#!/usr/bin/env python3
"""Run a local two-party SecretFlow PSI job with mutual output."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
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
        reader = csv.DictReader(infile)
        return sum(1 for _ in reader)


def ensure_identical_outputs(path_a: Path, path_b: Path) -> None:
    if path_a.read_bytes() != path_b.read_bytes():
        raise SystemExit("Intersection outputs differ between parties; local contract violated")


def validate_inputs(party_a_path: Path, party_b_path: Path) -> None:
    script_path = Path(__file__).with_name("validate_inputs.py")
    subprocess.run(
        ["python", str(script_path), str(party_a_path), str(party_b_path)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--party-a", required=True, help="Normalized CSV for party A")
    parser.add_argument("--party-b", required=True, help="Normalized CSV for party B")
    parser.add_argument("--out-dir", required=True, help="Directory for PSI outputs")
    parser.add_argument("--job-id", default=None, help="Optional audit job id")
    parser.add_argument(
        "--protocol",
        default="KKRT_PSI_2PC",
        help="SecretFlow protocol, for example KKRT_PSI_2PC or ECDH_PSI_2PC",
    )
    args = parser.parse_args()

    party_a_path = Path(args.party_a).resolve()
    party_b_path = Path(args.party_b).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    job_id = args.job_id or datetime.now(timezone.utc).strftime("psi-%Y%m%dT%H%M%SZ")

    validate_inputs(party_a_path, party_b_path)

    try:
        import secretflow as sf
    except ImportError as exc:
        raise SystemExit(
            "SecretFlow is not installed. Install it in a dedicated environment before running this script."
        ) from exc

    sf.init(parties=["party_a", "party_b"], address="local")

    party_a = sf.PYU("party_a")
    party_b = sf.PYU("party_b")
    spu = sf.SPU(sf.utils.testing.cluster_def(["party_a", "party_b"]))

    input_path = {
        party_a: str(party_a_path),
        party_b: str(party_b_path),
    }
    output_path = {
        party_a: str(out_dir / "party_a_intersection.csv"),
        party_b: str(out_dir / "party_b_intersection.csv"),
    }

    reports = spu.psi_csv(
        key="domain",
        input_path=input_path,
        output_path=output_path,
        receiver="party_a",
        protocol=args.protocol,
        precheck_input=True,
        sort=True,
        broadcast_result=True,
    )

    audit = {
        "job_id": job_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": args.protocol,
        "reports": reports,
        "party_a": {
            "input_path": str(party_a_path),
            "input_rows": count_rows(party_a_path),
            "input_sha256": sha256_file(party_a_path),
            "output_path": output_path[party_a],
        },
        "party_b": {
            "input_path": str(party_b_path),
            "input_rows": count_rows(party_b_path),
            "input_sha256": sha256_file(party_b_path),
            "output_path": output_path[party_b],
        },
        "intersection": {
            "rows": count_rows(Path(output_path[party_a])),
            "sha256": sha256_file(Path(output_path[party_a])),
        },
    }

    ensure_identical_outputs(
        Path(output_path[party_a]),
        Path(output_path[party_b]),
    )

    audit_path = out_dir / "audit.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(json.dumps(audit, indent=2))
    print(f"audit written to {audit_path}")

    sf.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
