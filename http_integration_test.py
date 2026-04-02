#!/usr/bin/env python3
"""Drive the coordinator end to end for a single PSI job."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib import request


def http_json(
    method: str,
    url: str,
    body: bytes | None = None,
    content_type: str = "application/json",
    api_key: str | None = None,
) -> dict:
    req = request.Request(url, data=body, method=method)
    req.add_header("Content-Type", content_type)
    if api_key:
        req.add_header("X-API-Key", api_key)
    with request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def http_bytes(
    method: str,
    url: str,
    body: bytes | None = None,
    content_type: str = "application/octet-stream",
    api_key: str | None = None,
) -> bytes:
    req = request.Request(url, data=body, method=method)
    req.add_header("Content-Type", content_type)
    if api_key:
        req.add_header("X-API-Key", api_key)
    with request.urlopen(req) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--party-a", required=True)
    parser.add_argument("--party-b", required=True)
    parser.add_argument("--admin-api-key", default=None)
    parser.add_argument("--party-a-api-key", default=None)
    parser.add_argument("--party-b-api-key", default=None)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    party_a_path = Path(args.party_a)
    party_b_path = Path(args.party_b)

    manifest = {
        "job_id": args.job_id,
        "purpose": "Coordinator HTTP integration test",
        "protocol": "KKRT_PSI_2PC",
        "broadcast_result": True,
        "parties": [
            {
                "name": "party_a",
                "organization": "Popular Domains A",
                "operator": "http_test",
                "source_export_date": "2026-03-31",
                "approved": True,
            },
            {
                "name": "party_b",
                "organization": "Mixed Domains B",
                "operator": "http_test",
                "source_export_date": "2026-03-31",
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

    print(
        http_json(
            "POST",
            f"{base_url}/jobs",
            json.dumps({"job_id": args.job_id, "protocol": "KKRT_PSI_2PC"}).encode("utf-8"),
            api_key=args.admin_api_key,
        )
    )
    print(
        http_json(
            "PUT",
            f"{base_url}/jobs/{args.job_id}/manifest",
            json.dumps(manifest).encode("utf-8"),
            api_key=args.admin_api_key,
        )
    )
    print(
        http_json(
            "PUT",
            f"{base_url}/jobs/{args.job_id}/inputs/party_a",
            party_a_path.read_bytes(),
            "text/csv",
            api_key=args.admin_api_key,
        )
    )
    print(
        http_json(
            "PUT",
            f"{base_url}/jobs/{args.job_id}/inputs/party_b",
            party_b_path.read_bytes(),
            "text/csv",
            api_key=args.admin_api_key,
        )
    )
    print(http_json("POST", f"{base_url}/jobs/{args.job_id}/validate", b"{}", "application/json", args.admin_api_key))
    print(http_json("POST", f"{base_url}/jobs/{args.job_id}/run", b"{}", "application/json", args.admin_api_key))
    print(http_json("POST", f"{base_url}/jobs/{args.job_id}/verify", b"{}", "application/json", args.admin_api_key))
    status = http_json("GET", f"{base_url}/jobs/{args.job_id}", api_key=args.admin_api_key)
    print(status)
    audit = http_json("GET", f"{base_url}/jobs/{args.job_id}/audit", api_key=args.admin_api_key)
    print({"intersection_rows": audit["intersection"]["rows"]})
    party_a_result = http_bytes(
        "GET",
        f"{base_url}/jobs/{args.job_id}/results/party_a",
        api_key=args.party_a_api_key or args.admin_api_key,
    ).decode("utf-8")
    print(party_a_result)
    party_b_result = http_bytes(
        "GET",
        f"{base_url}/jobs/{args.job_id}/results/party_b",
        api_key=args.party_b_api_key or args.admin_api_key,
    ).decode("utf-8")
    print(party_b_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
