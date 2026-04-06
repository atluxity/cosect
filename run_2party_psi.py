#!/usr/bin/env python3
"""Run a local two-party PSI job with mutual output."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from openmined_backend import compute_local_intersection, read_domains, write_domains


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


def expected_intersection(party_a_path: Path, party_b_path: Path) -> list[str]:
    return sorted(set(read_domains(party_a_path)) & set(read_domains(party_b_path)))


def ensure_identical_outputs(path_a: Path, path_b: Path) -> None:
    if path_a.read_bytes() != path_b.read_bytes():
        raise SystemExit("Intersection outputs differ between parties; local contract violated")


def validate_inputs(party_a_path: Path, party_b_path: Path) -> None:
    script_path = Path(__file__).with_name("validate_inputs.py")
    subprocess.run(
        ["python3", str(script_path), str(party_a_path), str(party_b_path)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--party-a", required=True, help="Normalized CSV for party A")
    parser.add_argument("--party-b", required=True, help="Normalized CSV for party B")
    parser.add_argument("--out-dir", required=True, help="Directory for PSI outputs")
    parser.add_argument("--job-id", default=None, help="Optional audit job id")
    parser.add_argument("--engine", default="secretflow", help="PSI engine")
    parser.add_argument(
        "--protocol",
        default=None,
        help="Engine-specific protocol, for example KKRT_PSI_2PC or ECDH_PSI_2PC",
    )
    parser.add_argument(
        "--print-audit-json",
        action="store_true",
        help="Print the full audit JSON to stdout",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the normal completion summary",
    )
    args = parser.parse_args()
    if args.protocol is None:
        args.protocol = "OPENMINED_ECDH" if args.engine == "openmined" else "KKRT_PSI_2PC"

    party_a_path = Path(args.party_a).resolve()
    party_b_path = Path(args.party_b).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    job_id = args.job_id or datetime.now(timezone.utc).strftime("psi-%Y%m%dT%H%M%SZ")
    started_at = datetime.now(timezone.utc)

    validate_inputs(party_a_path, party_b_path)

    party_a_output_path = out_dir / "party_a_intersection.csv"
    party_b_output_path = out_dir / "party_b_intersection.csv"

    if args.engine == "secretflow":
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
            party_a: str(party_a_output_path),
            party_b: str(party_b_output_path),
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
        engine_version = getattr(sf, "__version__", "unknown")
    elif args.engine == "openmined":
        intersection, reports, engine_version = compute_local_intersection(
            read_domains(party_a_path),
            read_domains(party_b_path),
            args.protocol,
        )
        write_domains(party_a_output_path, intersection)
        write_domains(party_b_output_path, intersection)
    else:
        raise SystemExit(
            f"unsupported engine: {args.engine}. "
            "Supported engines: secretflow, openmined."
        )

    expected_rows = expected_intersection(party_a_path, party_b_path)
    actual_rows = read_domains(party_a_output_path)
    if actual_rows != expected_rows:
        raise SystemExit(
            f"{args.engine} output does not match the independently recomputed set intersection"
        )
    completed_at = datetime.now(timezone.utc)

    audit = {
        "job_id": job_id,
        "timestamp_utc": completed_at.isoformat(),
        "engine": args.engine,
        "protocol": args.protocol,
        "execution": {
            "started_at_utc": started_at.isoformat(),
            "completed_at_utc": completed_at.isoformat(),
            "duration_seconds": round((completed_at - started_at).total_seconds(), 3),
            "python_version": sys.version.split()[0],
            "engine_version": engine_version,
            "runner_sha256": sha256_file(Path(__file__)),
            "validator_sha256": sha256_file(Path(__file__).with_name("validate_inputs.py")),
        },
        "reports": reports,
        "party_a": {
            "input_path": str(party_a_path),
            "input_rows": count_rows(party_a_path),
            "input_sha256": sha256_file(party_a_path),
            "output_path": str(party_a_output_path),
        },
        "party_b": {
            "input_path": str(party_b_path),
            "input_rows": count_rows(party_b_path),
            "input_sha256": sha256_file(party_b_path),
            "output_path": str(party_b_output_path),
        },
        "intersection": {
            "rows": count_rows(party_a_output_path),
            "sha256": sha256_file(party_a_output_path),
        },
        "independent_verification": {
            "method": "sorted set intersection over normalized CSV inputs",
            "rows": len(expected_rows),
            "matches_engine_output": True,
        }
    }

    ensure_identical_outputs(
        party_a_output_path,
        party_b_output_path,
    )

    audit_path = out_dir / "audit.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    if args.print_audit_json:
        print(json.dumps(audit, indent=2))
    elif not args.quiet:
        print("PSI run completed")
        print(f"job id: {job_id}")
        print(f"engine: {args.engine}")
        print(f"protocol: {args.protocol}")
        print(f"party_a rows: {audit['party_a']['input_rows']}")
        print(f"party_b rows: {audit['party_b']['input_rows']}")
        print(f"intersection rows: {audit['intersection']['rows']}")
        print(f"audit written to {audit_path}")

    if args.engine == "secretflow":
        sf.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
