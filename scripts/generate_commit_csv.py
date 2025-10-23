import argparse
import csv
import math
import os
import re
import subprocess
from datetime import datetime
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
            # Parse ISO date to datetime for time-gap based estimation
            try:
                current["date_dt"] = datetime.fromisoformat(parts[1])
            except Exception:
                current["date_dt"] = None
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

"""Heuristics for estimated_minutes:

Methods available via --method:
1) stat-log (default): Base 10 + 4 min per file + 10 * log10(1 + LOC)
   - Good for capping huge diffs, while acknowledging larger work.
2) time-delta: Minutes since previous commit by the same author (clamped 5..180),
   with resets for long gaps (>8h) falling back to a baseline (max(15, stat-log)).
3) stat-heavy: Base 24 + 9 per file + 10 per 20 LOC (previous heavier linear model).
"""

def estimate_minutes_stat_log(files_changed: int, insertions: int, deletions: int) -> int:
    loc = insertions + deletions
    minutes = 10 + 4 * files_changed + int(10 * math.log10(1 + max(0, loc)))
    return int(math.ceil(max(5, minutes) / 5.0) * 5)


def estimate_minutes_stat_heavy(files_changed: int, insertions: int, deletions: int) -> int:
    minutes = 24 + 9 * files_changed + math.ceil((insertions + deletions) / 20) * 10
    return int(math.ceil(minutes / 5.0) * 5)


def estimate_minutes_time_delta(commits: list[dict]) -> None:
    """In-place estimation using time gaps per author.

    For each author, walk commits oldest->newest and estimate:
    - First commit: max(15, stat-log) baseline
    - Subsequent: minutes = clamp(delta_minutes, 5..180)
      If delta > 8h (480 min) or missing dates: baseline = max(15, stat-log)
    Rounds to nearest 5 up. Writes 'estimated_minutes' into each commit dict.
    """
    from collections import defaultdict

    # Group by author with chronological order
    by_author: dict[str, list[dict]] = defaultdict(list)
    for c in reversed(commits):  # oldest first
        by_author[c.get("author", "?")].append(c)

    for author, lst in by_author.items():
        prev = None
        for c in lst:
            stat_baseline = estimate_minutes_stat_log(c.get("files_changed", 0), c.get("insertions", 0), c.get("deletions", 0))
            if prev is None:
                est = max(15, stat_baseline)
            else:
                t0 = prev.get("date_dt")
                t1 = c.get("date_dt")
                if not t0 or not t1:
                    est = max(15, stat_baseline)
                else:
                    delta = (t1 - t0).total_seconds() / 60.0
                    if delta > 480:  # >8 hours -> new session baseline
                        est = max(15, stat_baseline)
                    elif delta <= 0:
                        est = max(5, min(20, stat_baseline))
                    else:
                        est = max(5, min(180, int(delta)))
            c["estimated_minutes"] = int(math.ceil(est / 5.0) * 5)
            prev = c


def main():
    parser = argparse.ArgumentParser(description="Generate commit history CSV with estimated minutes per commit.")
    parser.add_argument("--method", choices=["stat-log", "time-delta", "stat-heavy"], default="stat-log", help="Estimation method to use")
    parser.add_argument("--outfile", default="commit_history.csv", help="Output CSV filename (relative to repo root)")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)
    raw = run(["git", "log", f"--pretty=format:{LOG_FORMAT}", "--date=iso-strict", "--shortstat"]).strip()
    commits = parse_log(raw)
    # Compute estimates
    if args.method == "time-delta":
        estimate_minutes_time_delta(commits)
    elif args.method == "stat-heavy":
        for c in commits:
            c["estimated_minutes"] = estimate_minutes_stat_heavy(c["files_changed"], c["insertions"], c["deletions"])
    else:  # stat-log
        for c in commits:
            c["estimated_minutes"] = estimate_minutes_stat_log(c["files_changed"], c["insertions"], c["deletions"])

    out_path = repo_root / args.outfile
    try:
        fobj = out_path.open("w", newline="", encoding="utf-8")
    except PermissionError:
        # Fallback to a method-specific file to avoid editor locks on Windows
        fallback = repo_root / f"commit_history.{args.method}.csv"
        print(f"Output file locked: {out_path}. Writing to {fallback} instead.")
        fobj = fallback.open("w", newline="", encoding="utf-8")
        out_path = fallback
    with fobj as f:
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
    print(f"Wrote {out_path} using method={args.method}")


if __name__ == "__main__":
    main()
