#!/usr/bin/env python3
"""Create a manifest.json for a staged SecretFlow PSI run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--party-a-org", required=True)
    parser.add_argument("--party-b-org", required=True)
    parser.add_argument("--party-a-operator", required=True)
    parser.add_argument("--party-b-operator", required=True)
    parser.add_argument("--party-a-export-date", required=True)
    parser.add_argument("--party-b-export-date", required=True)
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Base directory for staged runs",
    )
    args = parser.parse_args()

    run_dir = Path(args.runs_dir) / args.job_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"

    manifest = {
        "job_id": args.job_id,
        "purpose": "Share exact overlapping domains between two industry peers",
        "protocol": "KKRT_PSI_2PC",
        "broadcast_result": True,
        "parties": [
            {
                "name": "party_a",
                "organization": args.party_a_org,
                "operator": args.party_a_operator,
                "source_export_date": args.party_a_export_date,
                "approved": True,
            },
            {
                "name": "party_b",
                "organization": args.party_b_org,
                "operator": args.party_b_operator,
                "source_export_date": args.party_b_export_date,
                "approved": True,
            },
        ],
        "canonicalization": {
            "lowercase": True,
            "trim_whitespace": True,
            "remove_trailing_dot": True,
            "convert_idn_to_punycode": True,
            "preserve_subdomains": True,
        },
    }

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
