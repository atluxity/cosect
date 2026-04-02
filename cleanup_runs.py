#!/usr/bin/env python3
"""Apply retention cleanup policy to run and archive artifacts."""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path


def older_than(path: Path, cutoff_epoch: float) -> bool:
    return path.stat().st_mtime < cutoff_epoch


def delete_if_exists(path: Path) -> None:
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--archive-dir", default="archives")
    parser.add_argument(
        "--keep-mode",
        choices=["everything", "metadata-only", "delete-all"],
        default="everything",
        help="What to retain for old completed runs",
    )
    parser.add_argument(
        "--older-than-hours",
        type=int,
        default=24,
        help="Apply cleanup only to runs and archives older than this age",
    )
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    archive_dir = Path(args.archive_dir)
    cutoff_epoch = time.time() - (args.older_than_hours * 3600)

    if runs_dir.exists():
        for run_dir in runs_dir.iterdir():
            if not run_dir.is_dir() or not older_than(run_dir, cutoff_epoch):
                continue
            if args.keep_mode == "everything":
                continue
            if args.keep_mode == "metadata-only":
                delete_if_exists(run_dir / "input")
                delete_if_exists(run_dir / "output" / "party_a_intersection.csv")
                delete_if_exists(run_dir / "output" / "party_b_intersection.csv")
                delete_if_exists(run_dir / "logs")
            elif args.keep_mode == "delete-all":
                delete_if_exists(run_dir)

    if archive_dir.exists():
        for archive in archive_dir.iterdir():
            if archive.is_file() and older_than(archive, cutoff_epoch) and args.keep_mode != "everything":
                archive.unlink()

    print(
        {
            "runs_dir": str(runs_dir),
            "archive_dir": str(archive_dir),
            "keep_mode": args.keep_mode,
            "older_than_hours": args.older_than_hours,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
