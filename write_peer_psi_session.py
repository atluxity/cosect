#!/usr/bin/env python3
"""Write a shared session file for distributed two-party PSI execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def default_protocol_for(engine: str) -> str:
    if engine == "openmined":
        return "OPENMINED_ECDH"
    return "KKRT_PSI_2PC"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--session-file", required=True)
    parser.add_argument("--engine", default="secretflow")
    parser.add_argument("--protocol", default=None)
    parser.add_argument("--party-a-address", required=True)
    parser.add_argument("--party-b-address", required=True)
    parser.add_argument("--party-a-listen-addr", default=None)
    parser.add_argument("--party-b-listen-addr", default=None)
    parser.add_argument("--party-a-spu-address", default=None)
    parser.add_argument("--party-b-spu-address", default=None)
    parser.add_argument("--party-a-input-path", required=True)
    parser.add_argument("--party-b-input-path", required=True)
    parser.add_argument("--party-a-output-path", required=True)
    parser.add_argument("--party-b-output-path", required=True)
    parser.add_argument("--party-a-receipt-path", required=True)
    parser.add_argument("--party-b-receipt-path", required=True)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print a session-file confirmation line",
    )
    args = parser.parse_args()
    protocol = args.protocol or default_protocol_for(args.engine)

    session = {
        "job_id": args.job_id,
        "engine": args.engine,
        "protocol": protocol,
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
    }
    if args.engine == "secretflow":
        if not args.party_a_spu_address or not args.party_b_spu_address:
            raise SystemExit("secretflow sessions require both --party-a-spu-address and --party-b-spu-address")
        session["spu"] = {
            "nodes": {
                "party_a": {"address": args.party_a_spu_address},
                "party_b": {"address": args.party_b_spu_address},
            }
        }
    if args.party_a_listen_addr:
        session["parties"]["party_a"]["listen_addr"] = args.party_a_listen_addr
    if args.party_b_listen_addr:
        session["parties"]["party_b"]["listen_addr"] = args.party_b_listen_addr

    session_path = Path(args.session_file).resolve()
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    if not args.quiet:
        print(f"wrote session file to {session_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
