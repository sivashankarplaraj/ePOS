from pathlib import Path
import shutil
import io
import sys
import zipfile
from typing import List, Tuple

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required

# Import mapping and runner from the insert script (safe now due to __main__ guard)
from User_details.Scripts.insert_sql import csv_to_table, downloaded_files_dir, main as run_insert


def _validate_source_dir(dir_path_str: str) -> Tuple[List[str], List[str]]:
    """Return (missing, present) lists for expected CSVs in a given directory."""
    src_dir = Path(dir_path_str)
    expected_files = list(csv_to_table.keys())
    present = []
    missing = []
    for fname in expected_files:
        if (src_dir / fname).exists():
            present.append(fname)
        else:
            missing.append(fname)
    return missing, present


def _extract_expected_from_zip(zf: zipfile.ZipFile, dest_dir: Path) -> Tuple[List[str], List[str]]:
    """Extract only expected CSVs from ZIP into dest_dir.

    Returns (missing, present) relative to csv_to_table keys.
    Matching is case-insensitive against each member's basename.
    """
    expected = list(csv_to_table.keys())
    # Build map of lowercase basename -> ZipInfo
    members_by_base = {}
    for info in zf.infolist():
        if info.is_dir():
            continue
        base = Path(info.filename).name.lower()
        members_by_base[base] = info

    dest_dir.mkdir(parents=True, exist_ok=True)
    present = []
    for fname in expected:
        match = members_by_base.get(fname.lower())
        if match:
            # Extract to the exact expected filename (overwrite)
            target = dest_dir / fname
            with zf.open(match) as src, open(target, 'wb') as out:
                shutil.copyfileobj(src, out)
            present.append(fname)
    missing = [f for f in expected if f not in present]
    return missing, present


@staff_member_required
@require_http_methods(["GET", "POST"])
def update_till_import(request: HttpRequest) -> HttpResponse:
    """Simple form to accept a directory path and run the Update Till import.

    - GET: show input form and current expected file list.
    - POST: validate all expected files exist in provided path; if any missing, show error.
            if all present, copy them into downloaded_files_dir (overwriting), run insert, and show output.
    """
    context = {
        'expected_files': list(csv_to_table.keys()),
        'output': None,
        'missing': None,
        'provided_dir': '',
        'download_target': str(downloaded_files_dir),
    }

    if request.method == 'POST':
        provided_dir = (request.POST.get('csv_dir') or '').strip()
        context['provided_dir'] = provided_dir

        # Ensure destination exists and clear old expected files to avoid stale data
        downloaded_files_dir.mkdir(parents=True, exist_ok=True)
        for fname in csv_to_table.keys():
            try:
                (downloaded_files_dir / fname).unlink(missing_ok=True)  # type: ignore[arg-type]
            except TypeError:
                # Python <3.8 compatibility: ignore if missing
                p = downloaded_files_dir / fname
                if p.exists():
                    p.unlink()

        missing = []
        present = []

        # Option A: ZIP upload
        upload = request.FILES.get('csv_zip')
        if upload and getattr(upload, 'size', 0) > 0:
            try:
                with zipfile.ZipFile(upload) as zf:
                    missing, present = _extract_expected_from_zip(zf, downloaded_files_dir)
            except zipfile.BadZipFile:
                context['missing'] = ['Uploaded file is not a valid ZIP']
                return render(request, 'update_till/import_form.html', context)
        else:
            # Option B: server directory
            if not provided_dir:
                context['missing'] = ['Provide a server directory path or upload a ZIP']
                return render(request, 'update_till/import_form.html', context)
            src = Path(provided_dir)
            if not src.exists() or not src.is_dir():
                context['missing'] = [f"Invalid directory: {provided_dir}"]
                return render(request, 'update_till/import_form.html', context)
            missing, present = _validate_source_dir(provided_dir)
            if missing:
                context['missing'] = missing
                return render(request, 'update_till/import_form.html', context)
            # Copy all expected files from source to destination
            for fname in present:
                shutil.copy2(src / fname, downloaded_files_dir / fname)

        if missing:
            context['missing'] = missing
            return render(request, 'update_till/import_form.html', context)

        # Capture stdout/stderr while running insert
        buf = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = buf
        try:
            run_insert()
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        context['output'] = buf.getvalue()
        return render(request, 'update_till/import_form.html', context)

    # GET: render form
    return render(request, 'update_till/import_form.html', context)