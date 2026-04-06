#!/usr/bin/env python3
"""Verify that two distributed PSI party receipts agree on the same session and result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--party-a-receipt", required=True)
    parser.add_argument("--party-b-receipt", required=True)
    args = parser.parse_args()

    party_a_path = Path(args.party_a_receipt).resolve()
    party_b_path = Path(args.party_b_receipt).resolve()
    party_a = read_json(party_a_path)
    party_b = read_json(party_b_path)

    expect(party_a["self_party"] == "party_a", "party_a receipt has wrong self_party")
    expect(party_b["self_party"] == "party_b", "party_b receipt has wrong self_party")
    expect(party_a["job_id"] == party_b["job_id"], "job_id mismatch between receipts")
    expect(party_a["engine"] == party_b["engine"], "engine mismatch between receipts")
    expect(party_a["protocol"] == party_b["protocol"], "protocol mismatch between receipts")
    expect(
        party_a["session_sha256"] == party_b["session_sha256"],
        "session file hash mismatch between receipts",
    )
    expect(
        party_a["local_output"]["sha256"] == party_b["local_output"]["sha256"],
        "output hash mismatch between receipts",
    )
    expect(
        party_a["local_output"]["rows"] == party_b["local_output"]["rows"],
        "output row count mismatch between receipts",
    )

    summary = {
        "job_id": party_a["job_id"],
        "engine": party_a["engine"],
        "protocol": party_a["protocol"],
        "session_sha256": party_a["session_sha256"],
        "output_rows": party_a["local_output"]["rows"],
        "output_sha256": party_a["local_output"]["sha256"],
        "party_a_input_sha256": party_a["local_input"]["sha256"],
        "party_b_input_sha256": party_b["local_input"]["sha256"],
        "status": "receipts_agree",
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
