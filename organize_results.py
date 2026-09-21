#!/usr/bin/env python3
"""Organize results/ into per-run, latest, and summary-plot subfolders.

results/ currently holds a flat mix of files following the pattern:
    fv_shot_sweep_<task>_<timestamp>.<csv|png>   -- one run's output for a task
    fv_shot_sweep_<task>.<png>                   -- "current" copy (no timestamp)
    fv_shot_sweep_results.json                   -- current aggregate results
    fv_sweep_plots/                              -- cross-run summary plots

This script reorganizes them into:
    results/runs/<timestamp>/fv_shot_sweep_<task>.<csv|png>
    results/latest/...                           -- the un-timestamped "current" files
    results/summary_plots/...                    -- (renamed from fv_sweep_plots/)

It only moves files matching the fv_shot_sweep_* naming convention, is safe
to re-run, and leaves anything it doesn't recognize untouched.
"""

import re
import shutil
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"
TIMESTAMPED_RE = re.compile(r"^(?P<stem>.+)_(?P<timestamp>\d{8}_\d{6})\.(?P<ext>\w+)$")


def organize(results_dir: Path, dry_run: bool = False) -> None:
    if not results_dir.is_dir():
        raise SystemExit(f"No such directory: {results_dir}")

    runs_dir = results_dir / "runs"
    latest_dir = results_dir / "latest"
    summary_dir = results_dir / "summary_plots"

    old_summary = results_dir / "fv_sweep_plots"
    if old_summary.is_dir():
        _move(old_summary, summary_dir, dry_run)

    for path in sorted(results_dir.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if not path.name.startswith("fv_shot_sweep"):
            continue

        match = TIMESTAMPED_RE.match(path.name)
        if match:
            dest = runs_dir / match["timestamp"] / f"{match['stem']}.{match['ext']}"
        else:
            dest = latest_dir / path.name

        _move(path, dest, dry_run)


def _move(src: Path, dest: Path, dry_run: bool) -> None:
    if dest.exists():
        print(f"skip (exists): {dest.relative_to(RESULTS_DIR.parent)}")
        return
    print(f"{src.relative_to(RESULTS_DIR.parent)} -> {dest.relative_to(RESULTS_DIR.parent)}")
    if dry_run:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the planned moves without doing them"
    )
    args = parser.parse_args()
    organize(RESULTS_DIR, dry_run=args.dry_run)
