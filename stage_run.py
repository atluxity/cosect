#!/usr/bin/env python3
"""Stage normalized inputs into a dedicated run directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True, help="Run identifier, for example psi-20260401T090000Z")
    parser.add_argument("--party-a", required=True, help="Normalized CSV for party A")
    parser.add_argument("--party-b", required=True, help="Normalized CSV for party B")
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Base directory for staged runs",
    )
    args = parser.parse_args()

    run_dir = Path(args.runs_dir) / args.job_id
    input_dir = run_dir / "input"
    output_dir = run_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=False)
    output_dir.mkdir(parents=True, exist_ok=False)

    party_a_src = Path(args.party_a).resolve()
    party_b_src = Path(args.party_b).resolve()
    party_a_dst = input_dir / "party_a_domains.csv"
    party_b_dst = input_dir / "party_b_domains.csv"

    shutil.copy2(party_a_src, party_a_dst)
    shutil.copy2(party_b_src, party_b_dst)

    print(f"staged run at {run_dir}")
    print(f"party_a input: {party_a_dst}")
    print(f"party_b input: {party_b_dst}")
    print(f"output dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
