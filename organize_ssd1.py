#!/usr/bin/env python3
"""Organize ssd1/results/ into per-run and per-experiment subfolders.

ssd1/results/ currently holds a flat mix of files following the patterns:
    fv_shot_sweep_<task>_<timestamp>.<csv|png>            -- one sweep run's output for a task
    fv_shot_sweep_all_tasks_<timestamp>.png               -- that run's combined summary plot
    nla_mistake_attribution_<task>_<timestamp>.<csv|png>  -- one run's output for a task
    nla_mistake_attribution_all_tasks_<timestamp>.png     -- that run's combined summary plot
    nla_mistake_attribution_mistakes_<task>_<timestamp>.json -- that run's raw mistakes
    tense_flip_edit_sweep.<png|json>                      -- a separate one-off experiment
    <task>_edit_sweep.png                                 -- threshold-flip sweep plot for
                                                               <task> in {tense, capitalize_allcaps,
                                                               en_fr_es}
    <task>_flip_thresholds.json                           -- that run's flip thresholds
    <task>_results.json                                   -- that run's full results

This script reorganizes them into:
    ssd1/results/fv_shot_sweep/<timestamp>/...            -- all files from one sweep run
    ssd1/results/nla_mistake_attribution/<timestamp>/...  -- all files from one run
    ssd1/results/tense_flip_edit_sweep/...                -- the one-off experiment's files
    ssd1/results/<task>/<task>_edit_sweep.png             -- one task's threshold-flip sweep
    ssd1/results/<task>/flip_thresholds.json
    ssd1/results/<task>/results.json

It only moves files matching these naming conventions, is safe to re-run, and
leaves anything it doesn't recognize untouched.
"""

import re
import shutil
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "ssd1" / "results"
TIMESTAMPED_PREFIXES = ["fv_shot_sweep", "nla_mistake_attribution"]
TENSE_FLIP_PREFIX = "tense_flip_edit_sweep"
FLIP_SWEEP_TASKS = ["tense", "capitalize_allcaps", "en_fr_es"]


def organize(results_dir: Path, dry_run: bool = False) -> None:
    if not results_dir.is_dir():
        raise SystemExit(f"No such directory: {results_dir}")

    timestamped_res = [
        (prefix, re.compile(rf"^{re.escape(prefix)}_.+_(?P<timestamp>\d{{8}}_\d{{6}})\.\w+$"))
        for prefix in TIMESTAMPED_PREFIXES
    ]
    tense_flip_dir = results_dir / TENSE_FLIP_PREFIX
    flip_sweep_re = re.compile(
        rf"^(?P<task>{'|'.join(re.escape(t) for t in FLIP_SWEEP_TASKS)})"
        rf"_(?P<rest>edit_sweep\.\w+|flip_thresholds\.json|results\.json)$"
    )

    for path in sorted(results_dir.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue

        dest = None
        for prefix, pattern in timestamped_res:
            match = pattern.match(path.name)
            if match:
                dest = results_dir / prefix / match["timestamp"] / path.name
                break

        if dest is None and path.name.startswith(TENSE_FLIP_PREFIX):
            dest = tense_flip_dir / path.name

        if dest is None:
            match = flip_sweep_re.match(path.name)
            if match:
                task, rest = match["task"], match["rest"]
                filename = path.name if rest.startswith("edit_sweep") else rest
                dest = results_dir / task / filename

        if dest is None:
            continue

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
