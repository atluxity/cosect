#!/usr/bin/env python3
"""Archive a completed SecretFlow PSI run directory."""

from __future__ import annotations

import argparse
import tarfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Base directory for staged runs",
    )
    parser.add_argument(
        "--archive-dir",
        default="archives",
        help="Directory for compressed run archives",
    )
    args = parser.parse_args()

    run_dir = Path(args.runs_dir) / args.job_id
    archive_dir = Path(args.archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{args.job_id}.tar.gz"

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(run_dir, arcname=args.job_id)

    print(f"archived {run_dir} to {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
