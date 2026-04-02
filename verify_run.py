#!/usr/bin/env python3
"""Verify a completed SecretFlow PSI run before archival."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as infile:
        for chunk in iter(lambda: infile.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as infile:
        return sum(1 for _ in csv.DictReader(infile))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Base directory for staged runs",
    )
    args = parser.parse_args()

    run_dir = Path(args.runs_dir) / args.job_id
    manifest_path = run_dir / "manifest.json"
    audit_path = run_dir / "output" / "audit.json"
    party_a_output = run_dir / "output" / "party_a_intersection.csv"
    party_b_output = run_dir / "output" / "party_b_intersection.csv"
    party_a_input = run_dir / "input" / "party_a_domains.csv"
    party_b_input = run_dir / "input" / "party_b_domains.csv"

    expect(run_dir.exists(), f"missing run directory: {run_dir}")
    expect(manifest_path.exists(), f"missing manifest: {manifest_path}")
    expect(audit_path.exists(), f"missing audit file: {audit_path}")
    expect(party_a_output.exists(), f"missing output: {party_a_output}")
    expect(party_b_output.exists(), f"missing output: {party_b_output}")
    expect(party_a_input.exists(), f"missing input: {party_a_input}")
    expect(party_b_input.exists(), f"missing input: {party_b_input}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    expect(manifest["job_id"] == args.job_id, "manifest job_id does not match requested job id")
    expect(audit["job_id"] == args.job_id, "audit job_id does not match requested job id")
    expect(manifest["protocol"] == audit["protocol"], "manifest/audit protocol mismatch")

    expect(
        party_a_output.read_bytes() == party_b_output.read_bytes(),
        "party output CSVs differ",
    )

    expect(
        sha256_file(party_a_input) == audit["party_a"]["input_sha256"],
        "party_a input SHA-256 mismatch",
    )
    expect(
        sha256_file(party_b_input) == audit["party_b"]["input_sha256"],
        "party_b input SHA-256 mismatch",
    )
    expect(
        count_rows(party_a_input) == audit["party_a"]["input_rows"],
        "party_a input row count mismatch",
    )
    expect(
        count_rows(party_b_input) == audit["party_b"]["input_rows"],
        "party_b input row count mismatch",
    )
    expect(
        count_rows(party_a_output) == audit["intersection"]["rows"],
        "intersection row count mismatch",
    )
    expect(
        sha256_file(party_a_output) == audit["intersection"]["sha256"],
        "intersection SHA-256 mismatch",
    )

    print(f"{run_dir}: verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
