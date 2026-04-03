#!/usr/bin/env python3
"""Write a shared session file for strict-trust two-party PSI execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--session-file", required=True)
    parser.add_argument("--protocol", default="KKRT_PSI_2PC")
    parser.add_argument("--party-a-address", required=True)
    parser.add_argument("--party-b-address", required=True)
    parser.add_argument("--party-a-listen-addr", default=None)
    parser.add_argument("--party-b-listen-addr", default=None)
    parser.add_argument("--party-a-spu-address", required=True)
    parser.add_argument("--party-b-spu-address", required=True)
    parser.add_argument("--party-a-input-path", required=True)
    parser.add_argument("--party-b-input-path", required=True)
    parser.add_argument("--party-a-output-path", required=True)
    parser.add_argument("--party-b-output-path", required=True)
    parser.add_argument("--party-a-receipt-path", required=True)
    parser.add_argument("--party-b-receipt-path", required=True)
    args = parser.parse_args()

    session = {
        "job_id": args.job_id,
        "protocol": args.protocol,
        "cross_silo_comm_backend": "grpc",
        "enable_waiting_for_other_parties_ready": True,
        "parties": {
            "party_a": {
                "address": args.party_a_address,
                "input_path": args.party_a_input_path,
                "output_path": args.party_a_output_path,
                "receipt_path": args.party_a_receipt_path,
            },
            "party_b": {
                "address": args.party_b_address,
                "input_path": args.party_b_input_path,
                "output_path": args.party_b_output_path,
                "receipt_path": args.party_b_receipt_path,
            },
        },
        "spu": {
            "nodes": {
                "party_a": {"address": args.party_a_spu_address},
                "party_b": {"address": args.party_b_spu_address},
            }
        },
    }
    if args.party_a_listen_addr:
        session["parties"]["party_a"]["listen_addr"] = args.party_a_listen_addr
    if args.party_b_listen_addr:
        session["parties"]["party_b"]["listen_addr"] = args.party_b_listen_addr

    session_path = Path(args.session_file).resolve()
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    print(f"wrote session file to {session_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
