import csv
import math
import os
import re
import subprocess
from pathlib import Path


LOG_FORMAT = "%H|%ad|%an|%s"


def run(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout


def parse_log(raw: str):
    commits = []
    current = None
    stat_re = re.compile(r"(?:(\d+) files? changed)?(?:,\s*(\d+) insertions?\(\+\))?(?:,\s*(\d+) deletions?\(-\))?")
    for line in raw.splitlines():
        line = line.rstrip("\n")
        if not line:
            continue
        if "|" in line and not line.lstrip().startswith(tuple(str(d) for d in range(10))):
            # Heuristic guard not reliable; rely on format: line starts with 40-hex hash
            pass
        if re.fullmatch(r"[0-9a-f]{40}\|.*", line):
            # Start a new commit entry
            if current:
                commits.append(current)
            parts = line.split("|", 3)
            current = {
                "hash": parts[0],
                "date": parts[1],
                "author": parts[2],
                "subject": parts[3] if len(parts) > 3 else "",
                "files_changed": 0,
                "insertions": 0,
                "deletions": 0,
            }
        else:
            m = stat_re.search(line)
            if m and current:
                fc = int(m.group(1) or 0)
                ins = int(m.group(2) or 0)
                dels = int(m.group(3) or 0)
                current["files_changed"] += fc
                current["insertions"] += ins
                current["deletions"] += dels
    if current:
        commits.append(current)
    return commits


def estimate_minutes(files_changed: int, insertions: int, deletions: int) -> int:
    # Simple heuristic: base 8 min + 3 min per file + 1 min per 20 LOC changed
    minutes = 8 + 3 * files_changed + math.ceil((insertions + deletions) / 20)
    # Round to nearest 5 minutes up
    minutes = int(math.ceil(minutes / 5.0) * 5)
    return minutes


def main():
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)
    raw = run(["git", "log", f"--pretty=format:{LOG_FORMAT}", "--date=iso-strict", "--shortstat"]).strip()
    commits = parse_log(raw)
    # Compute estimates
    for c in commits:
        c["estimated_minutes"] = estimate_minutes(c["files_changed"], c["insertions"], c["deletions"])

    out_path = repo_root / "commit_history.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "hash",
            "author",
            "date_iso",
            "subject",
            "files_changed",
            "insertions",
            "deletions",
            "estimated_minutes",
        ])
        for c in commits:
            writer.writerow([
                c["hash"],
                c["author"],
                c["date"],
                c["subject"],
                c["files_changed"],
                c["insertions"],
                c["deletions"],
                c["estimated_minutes"],
            ])
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
