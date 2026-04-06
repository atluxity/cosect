#!/usr/bin/env python3
"""Standalone laptop-friendly PSI demo."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_PARTY_A = ROOT / "data" / "list_a_200_popular_domains.csv"
DEFAULT_PARTY_B = ROOT / "data" / "list_b_60_mixed.csv"
DEFAULT_OUT_DIR = ROOT / "poc_output"
DEFAULT_OPENMINED_OUT_DIR = ROOT / "poc_output_openmined"
DEFAULT_IMAGE = "secretflow/secretflow-anolis8:latest"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def print_step(message: str) -> None:
    print(f"[standalone] {message}", flush=True)


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
    parser.add_argument("--engine", default="secretflow", help="PSI engine")
    parser.add_argument("--protocol", default=None, help="Engine-specific protocol override")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="SecretFlow Docker image")
    parser.add_argument(
        "--show-results",
        action="store_true",
        help="Print the matching domains after the run completes",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pull the Docker image before running",
    )
    args = parser.parse_args()
    if args.protocol is None:
        args.protocol = "OPENMINED_ECDH" if args.engine == "openmined" else "KKRT_PSI_2PC"

    party_a = Path(args.party_a).resolve()
    party_b = Path(args.party_b).resolve()
    out_dir = Path(args.out_dir).resolve()
    if args.engine == "openmined" and args.out_dir == str(DEFAULT_OUT_DIR):
        out_dir = DEFAULT_OPENMINED_OUT_DIR.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    party_a_rows = count_rows(party_a)
    party_b_rows = count_rows(party_b)
    start_time = time.monotonic()

    print_step(f"job id: {args.job_id}")
    print_step(f"engine: {args.engine}")
    print_step(f"party_a input: {party_a} ({party_a_rows} rows)")
    print_step(f"party_b input: {party_b} ({party_b_rows} rows)")
    print_step(f"output directory: {out_dir}")

    if args.pull:
        print_step(f"pulling Docker image {args.image}")
        run(["docker", "pull", args.image])

    if args.engine == "secretflow":
        print_step("checking the two local input files and starting SecretFlow in Docker")
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
                "--engine",
                args.engine,
                "--protocol",
                args.protocol,
                "--quiet",
            ]
        )
    elif args.engine == "openmined":
        openmined_python = ROOT / ".venv-openmined" / "bin" / "python"
        if not openmined_python.exists():
            raise SystemExit(
                "OpenMined virtualenv is missing. Create .venv-openmined and install openmined-psi."
            )
        print_step("checking the two local input files and starting OpenMined PSI locally")
        run(
            [
                str(openmined_python),
                str(ROOT / "run_2party_psi.py"),
                "--party-a",
                str(party_a),
                "--party-b",
                str(party_b),
                "--out-dir",
                str(out_dir),
                "--job-id",
                args.job_id,
                "--engine",
                args.engine,
                "--protocol",
                args.protocol,
                "--quiet",
            ]
        )
    else:
        raise SystemExit(f"unsupported engine: {args.engine}")
    elapsed_seconds = time.monotonic() - start_time
    print_step(f"PSI run completed in {elapsed_seconds:.1f}s")

    audit_path = out_dir / "audit.json"
    result_path = out_dir / "party_a_intersection.csv"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    matches = read_domains(result_path)

    print_step(f"audit file written to {audit_path}")
    print_step(f"result file written to {result_path}")

    print()
    print("Standalone PSI demo")
    print(f"engine: {args.engine}")
    print(f"protocol: {args.protocol}")
    print(f"party_a input rows: {party_a_rows}")
    print(f"party_b input rows: {party_b_rows}")
    print(f"intersection rows: {audit['intersection']['rows']}")
    print(f"audit file: {audit_path}")
    print(f"result file: {result_path}")
    print("status: success")
    if args.show_results:
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
