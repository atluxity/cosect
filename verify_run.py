#!/usr/bin/env python3
"""Verify a completed SecretFlow PSI run before archival."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
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


def read_domains(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as infile:
        return [row["domain"] for row in csv.DictReader(infile)]


def csv_sha256_for_domains(domains: list[str]) -> str:
    body = "domain\n"
    if domains:
        body += "\n".join(domains) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


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

    expected_domains = sorted(set(read_domains(party_a_input)) & set(read_domains(party_b_input)))
    actual_party_a_domains = read_domains(party_a_output)
    actual_party_b_domains = read_domains(party_b_output)

    expect(
        actual_party_a_domains == expected_domains,
        "party_a output does not match independently recomputed plaintext intersection",
    )
    expect(
        actual_party_b_domains == expected_domains,
        "party_b output does not match independently recomputed plaintext intersection",
    )
    if "independent_verification" in audit:
        expect(
            audit["independent_verification"]["rows"] == len(expected_domains),
            "independent verification row count mismatch",
        )
        expect(
            audit["independent_verification"]["matches_secretflow_output"] is True,
            "audit does not record a successful independent verification",
        )

    verification = {
        "job_id": args.job_id,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha256_file(manifest_path),
        "audit_sha256": sha256_file(audit_path),
        "party_a_input_sha256": sha256_file(party_a_input),
        "party_b_input_sha256": sha256_file(party_b_input),
        "party_a_output_sha256": sha256_file(party_a_output),
        "party_b_output_sha256": sha256_file(party_b_output),
        "recomputed_plaintext_intersection_rows": len(expected_domains),
        "recomputed_plaintext_intersection_sha256": csv_sha256_for_domains(expected_domains),
        "output_matches_plaintext_intersection": True,
        "verification_script_sha256": sha256_file(Path(__file__)),
    }
    verification_path = run_dir / "output" / "verification.json"
    verification_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")

    print(f"{run_dir}: verification passed")
    print(f"verification receipt written to {verification_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
