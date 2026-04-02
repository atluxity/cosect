#!/usr/bin/env python3
"""Drive the coordinator end to end for a single PSI job."""

from __future__ import annotations

import argparse
import csv
import json
import time
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


def print_step(message: str) -> None:
    print(f"[http-test] {message}", flush=True)


def run_json_step(
    label: str,
    method: str,
    url: str,
    body: bytes | None = None,
    content_type: str = "application/json",
    api_key: str | None = None,
) -> dict:
    print_step(label)
    started = time.monotonic()
    payload = http_json(method, url, body, content_type, api_key)
    elapsed = time.monotonic() - started
    status = payload.get("status", "ok")
    print_step(f"{label} completed in {elapsed:.1f}s ({status})")
    return payload


def count_csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as infile:
        return sum(1 for _ in csv.DictReader(infile))


def preview_csv_rows(raw_csv: str, limit: int = 5) -> list[str]:
    rows = list(csv.DictReader(raw_csv.splitlines()))
    return [row["domain"] for row in rows[:limit]]


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
    party_a_path = Path(args.party_a).resolve()
    party_b_path = Path(args.party_b).resolve()
    started = time.monotonic()

    print_step(f"base URL: {base_url}")
    print_step(f"job id: {args.job_id}")
    print_step(f"party_a input: {party_a_path} ({count_csv_rows(party_a_path)} rows)")
    print_step(f"party_b input: {party_b_path} ({count_csv_rows(party_b_path)} rows)")

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

    run_json_step(
        "creating job",
        "POST",
        f"{base_url}/jobs",
        json.dumps({"job_id": args.job_id, "protocol": "KKRT_PSI_2PC"}).encode("utf-8"),
        api_key=args.admin_api_key,
    )
    run_json_step(
        "uploading manifest",
        "PUT",
        f"{base_url}/jobs/{args.job_id}/manifest",
        json.dumps(manifest).encode("utf-8"),
        api_key=args.admin_api_key,
    )
    run_json_step(
        "uploading party_a input",
        "PUT",
        f"{base_url}/jobs/{args.job_id}/inputs/party_a",
        party_a_path.read_bytes(),
        "text/csv",
        api_key=args.admin_api_key,
    )
    run_json_step(
        "uploading party_b input",
        "PUT",
        f"{base_url}/jobs/{args.job_id}/inputs/party_b",
        party_b_path.read_bytes(),
        "text/csv",
        api_key=args.admin_api_key,
    )
    run_json_step("validating uploaded inputs", "POST", f"{base_url}/jobs/{args.job_id}/validate", b"{}", "application/json", args.admin_api_key)
    run_json_step("running PSI job", "POST", f"{base_url}/jobs/{args.job_id}/run", b"{}", "application/json", args.admin_api_key)
    run_json_step("verifying outputs", "POST", f"{base_url}/jobs/{args.job_id}/verify", b"{}", "application/json", args.admin_api_key)
    status = run_json_step("fetching final job status", "GET", f"{base_url}/jobs/{args.job_id}", api_key=args.admin_api_key)
    audit = run_json_step("fetching audit record", "GET", f"{base_url}/jobs/{args.job_id}/audit", api_key=args.admin_api_key)
    print_step("downloading party results")
    party_a_result = http_bytes(
        "GET",
        f"{base_url}/jobs/{args.job_id}/results/party_a",
        api_key=args.party_a_api_key or args.admin_api_key,
    ).decode("utf-8")
    party_b_result = http_bytes(
        "GET",
        f"{base_url}/jobs/{args.job_id}/results/party_b",
        api_key=args.party_b_api_key or args.admin_api_key,
    ).decode("utf-8")
    elapsed = time.monotonic() - started

    print()
    print("HTTP integration test")
    print(f"job id: {args.job_id}")
    print(f"final status: {status['status']}")
    print(f"intersection rows: {audit['intersection']['rows']}")
    print(f"runtime: {elapsed:.1f}s")
    print()
    print("party_a result preview:")
    for domain in preview_csv_rows(party_a_result):
        print(domain)
    print()
    print("party_b result preview:")
    for domain in preview_csv_rows(party_b_result):
        print(domain)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
