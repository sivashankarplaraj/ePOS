#!/usr/bin/env python3
"""
List git commits for a given ISO week.

- Prompts for week number (and optionally year; defaults to current year).
- Computes the Monday (00:00:00) to Sunday (23:59:59) window for that ISO week.
- Runs: git --no-pager log --since "YYYY-MM-DD 00:00:00" --until "YYYY-MM-DD 23:59:59" --pretty=format:%s

Usage examples:
  # Interactive (asks for week, year default is the current year)
  python git_week_commits.py

  # Non-interactive
  python git_week_commits.py --week 45 --year 2025

Optional flags:
  --format: git pretty format (default: %s to show only commit messages)
  --repo:   path to the git repo (default: current directory)
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from datetime import date, datetime, time


def iso_week_range(year: int, week: int) -> tuple[datetime, datetime]:
    """Return (start_dt, end_dt) for ISO week: Monday 00:00:00 to Sunday 23:59:59."""
    try:
        monday = date.fromisocalendar(year, week, 1)
    except ValueError as e:
        raise ValueError(f"Invalid ISO week/year: week={week} year={year}: {e}")
    sunday = date.fromisocalendar(year, week, 7)
    start_dt = datetime.combine(monday, time(0, 0, 0))
    end_dt = datetime.combine(sunday, time(23, 59, 59))
    return start_dt, end_dt


def run_git_log(repo_path: str, since: datetime, until: datetime, pretty_format: str) -> int:
    since_str = since.strftime("%Y-%m-%d %H:%M:%S")
    until_str = until.strftime("%Y-%m-%d %H:%M:%S")
    cmd = [
        "git", "--no-pager", "log",
        f"--since={since_str}",
        f"--until={until_str}",
        f"--pretty=format:{pretty_format}",
    ]
    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    try:
        proc = subprocess.run(cmd, cwd=repo_path, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: git not found on PATH.", file=sys.stderr)
        return 127
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return proc.returncode
    # Print each commit line
    output = proc.stdout.strip()
    if not output:
        print("(No commits found in this window)")
    else:
        print(output)
    return 0


def main(argv: list[str] | None = None) -> int:
    import os
    parser = argparse.ArgumentParser(description="List git commits for a given ISO week")
    parser.add_argument("--week", "-w", type=int, help="ISO week number (1-53)")
    parser.add_argument("--year", "-y", type=int, help="Year (defaults to current year)")
    parser.add_argument("--format", default="%s", help="git --pretty format (default: %s)")
    parser.add_argument("--repo", default=os.getcwd(), help="Path to git repository (default: current directory)")
    args = parser.parse_args(argv)

    # Prompt interactively if week not supplied
    week = args.week
    if week is None:
        while True:
            raw = input("Enter ISO week number (1-53): ").strip()
            try:
                week = int(raw)
            except ValueError:
                print("Please enter a valid number.")
                continue
            if 1 <= week <= 53:
                break
            print("Week must be in 1..53")
    year = args.year or date.today().year

    try:
        start_dt, end_dt = iso_week_range(year, week)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    print(f"Week {week} ({year}) -> {start_dt:%Y-%m-%d %H:%M:%S} to {end_dt:%Y-%m-%d %H:%M:%S}")
    return run_git_log(args.repo, start_dt, end_dt, args.format)


if __name__ == "__main__":
    raise SystemExit(main())
