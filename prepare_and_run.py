#!/usr/bin/env python3
"""Normalize, validate, stage, and optionally run a SecretFlow PSI job."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run_step(command: list[str]) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True, help="Run identifier, for example psi-20260401T090000Z")
    parser.add_argument("--party-a-raw", required=True, help="Raw CSV for party A")
    parser.add_argument("--party-b-raw", required=True, help="Raw CSV for party B")
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Base directory for staged runs",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Prepare inputs and stage the run without executing SecretFlow",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    run_dir = (Path(args.runs_dir) / args.job_id).resolve()
    normalized_dir = run_dir / "normalized"
    input_dir = run_dir / "input"
    output_dir = run_dir / "output"
    normalized_dir.mkdir(parents=True, exist_ok=False)

    party_a_normalized = normalized_dir / "party_a_normalized.csv"
    party_b_normalized = normalized_dir / "party_b_normalized.csv"

    run_step(
        [
            "python3",
            str(root / "normalize_domains.py"),
            "--input",
            str(Path(args.party_a_raw).resolve()),
            "--output",
            str(party_a_normalized),
        ]
    )
    run_step(
        [
            "python3",
            str(root / "normalize_domains.py"),
            "--input",
            str(Path(args.party_b_raw).resolve()),
            "--output",
            str(party_b_normalized),
        ]
    )
    run_step(
        [
            "python3",
            str(root / "validate_inputs.py"),
            str(party_a_normalized),
            str(party_b_normalized),
        ]
    )
    run_step(
        [
            "python3",
            str(root / "stage_run.py"),
            "--job-id",
            args.job_id,
            "--party-a",
            str(party_a_normalized),
            "--party-b",
            str(party_b_normalized),
            "--runs-dir",
            str(Path(args.runs_dir)),
        ]
    )

    print(f"staged input dir: {input_dir}")
    print(f"staged output dir: {output_dir}")

    if args.skip_run:
        print("SecretFlow execution skipped")
        return 0

    run_step(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "python",
            "-v",
            f"{Path.cwd()}:/workspace",
            "-w",
            "/workspace",
            "secretflow/secretflow-anolis8:latest",
            "run_2party_psi.py",
            "--party-a",
            str((input_dir / "party_a_domains.csv").relative_to(Path.cwd())),
            "--party-b",
            str((input_dir / "party_b_domains.csv").relative_to(Path.cwd())),
            "--out-dir",
            str(output_dir.relative_to(Path.cwd())),
            "--job-id",
            args.job_id,
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
