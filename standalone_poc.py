#!/usr/bin/env python3
"""Standalone laptop-friendly PSI demo."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_PARTY_A = ROOT / "data" / "list_a_200_popular_domains.csv"
DEFAULT_PARTY_B = ROOT / "data" / "list_b_60_mixed.csv"
DEFAULT_OUT_DIR = ROOT / "poc_output"
DEFAULT_IMAGE = "secretflow/secretflow-anolis8:latest"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def count_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as infile:
        return sum(1 for _ in csv.DictReader(infile))


def read_domains(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as infile:
        return [row["domain"] for row in csv.DictReader(infile)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--party-a", default=str(DEFAULT_PARTY_A), help="CSV for party A")
    parser.add_argument("--party-b", default=str(DEFAULT_PARTY_B), help="CSV for party B")
    parser.add_argument("--job-id", default="psi-standalone-poc", help="Job id for the local run")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for local output")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="SecretFlow Docker image")
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pull the Docker image before running",
    )
    args = parser.parse_args()

    party_a = Path(args.party_a).resolve()
    party_b = Path(args.party_b).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.pull:
        run(["docker", "pull", args.image])

    run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "python",
            "-v",
            f"{ROOT}:/workspace",
            "-w",
            "/workspace",
            args.image,
            "run_2party_psi.py",
            "--party-a",
            str(party_a.relative_to(ROOT)),
            "--party-b",
            str(party_b.relative_to(ROOT)),
            "--out-dir",
            str(out_dir.relative_to(ROOT)),
            "--job-id",
            args.job_id,
        ]
    )

    audit_path = out_dir / "audit.json"
    result_path = out_dir / "party_a_intersection.csv"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    matches = read_domains(result_path)

    print()
    print("PSI standalone POC")
    print(f"party_a input rows: {count_rows(party_a)}")
    print(f"party_b input rows: {count_rows(party_b)}")
    print(f"intersection rows: {audit['intersection']['rows']}")
    print(f"audit file: {audit_path}")
    print(f"result file: {result_path}")
    print()
    print("Matching domains:")
    if matches:
        for domain in matches:
            print(domain)
    else:
        print("(none)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
