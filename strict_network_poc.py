#!/usr/bin/env python3
"""Run a strict-trust two-party PSI demo with two Docker containers and no centralized plaintext upload."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_IMAGE = "secretflow/secretflow-anolis8:latest"
DEFAULT_PARTY_A = ROOT / "data" / "list_a_200_popular_domains.csv"
DEFAULT_PARTY_B = ROOT / "data" / "list_b_60_mixed.csv"
DEFAULT_OUT_ROOT = ROOT / "out" / "strict_network_poc"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def count_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as infile:
        return sum(1 for _ in csv.DictReader(infile))


def print_step(message: str) -> None:
    print(f"[strict-demo] {message}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", default="psi-strict-network-demo")
    parser.add_argument("--party-a", default=str(DEFAULT_PARTY_A))
    parser.add_argument("--party-b", default=str(DEFAULT_PARTY_B))
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    parser.add_argument("--pull", action="store_true")
    args = parser.parse_args()

    out_root = Path(args.out_root).resolve() / args.job_id
    shared_dir = out_root / "shared"
    party_a_dir = out_root / "party_a"
    party_b_dir = out_root / "party_b"
    for base in (shared_dir, party_a_dir, party_b_dir):
        (base / "input").mkdir(parents=True, exist_ok=True)
        (base / "output").mkdir(parents=True, exist_ok=True)

    party_a_input = party_a_dir / "input" / "party_a_domains.csv"
    party_b_input = party_b_dir / "input" / "party_b_domains.csv"
    shutil.copy2(Path(args.party_a).resolve(), party_a_input)
    shutil.copy2(Path(args.party_b).resolve(), party_b_input)

    session_path = shared_dir / "session.json"
    run(
        [
            "python3",
            str(ROOT / "write_peer_psi_session.py"),
            "--job-id",
            args.job_id,
            "--session-file",
            str(session_path),
            "--party-a-address",
            "127.0.0.1:43001",
            "--party-b-address",
            "127.0.0.1:43002",
            "--party-a-spu-address",
            "127.0.0.1:43101",
            "--party-b-spu-address",
            "127.0.0.1:43102",
            "--party-a-input-path",
            "/party_data/input/party_a_domains.csv",
            "--party-b-input-path",
            "/party_data/input/party_b_domains.csv",
            "--party-a-output-path",
            "/party_data/output/party_a_intersection.csv",
            "--party-b-output-path",
            "/party_data/output/party_b_intersection.csv",
            "--party-a-receipt-path",
            "/party_data/output/party_a_receipt.json",
            "--party-b-receipt-path",
            "/party_data/output/party_b_receipt.json",
        ]
    )

    if args.pull:
        print_step(f"pulling Docker image {args.image}")
        run(["docker", "pull", args.image])

    print_step(f"party_a input rows: {count_rows(party_a_input)}")
    print_step(f"party_b input rows: {count_rows(party_b_input)}")
    print_step("starting party_a container")
    party_a_proc = subprocess.Popen(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "host",
            "-v",
            f"{ROOT}:/workspace",
            "-v",
            f"{shared_dir}:/shared",
            "-v",
            f"{party_a_dir}:/party_data",
            "-w",
            "/workspace",
            "--entrypoint",
            "python3",
            args.image,
            "run_2party_psi_peer.py",
            "--party",
            "party_a",
            "--session-file",
            "/shared/session.json",
        ]
    )
    time.sleep(1.0)
    print_step("starting party_b container")
    party_b_proc = subprocess.Popen(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "host",
            "-v",
            f"{ROOT}:/workspace",
            "-v",
            f"{shared_dir}:/shared",
            "-v",
            f"{party_b_dir}:/party_data",
            "-w",
            "/workspace",
            "--entrypoint",
            "python3",
            args.image,
            "run_2party_psi_peer.py",
            "--party",
            "party_b",
            "--session-file",
            "/shared/session.json",
        ]
    )

    party_a_rc = party_a_proc.wait()
    party_b_rc = party_b_proc.wait()
    if party_a_rc != 0 or party_b_rc != 0:
        raise SystemExit(f"peer containers failed: party_a={party_a_rc}, party_b={party_b_rc}")

    print_step("verifying party receipts agree")
    summary_raw = subprocess.check_output(
        [
            "python3",
            str(ROOT / "verify_peer_psi_receipts.py"),
            "--party-a-receipt",
            str(party_a_dir / "output" / "party_a_receipt.json"),
            "--party-b-receipt",
            str(party_b_dir / "output" / "party_b_receipt.json"),
        ],
        text=True,
    )
    summary = json.loads(summary_raw)

    print()
    print("Strict-trust PSI demo")
    print(f"job id: {args.job_id}")
    print(f"party_a receipt: {party_a_dir / 'output' / 'party_a_receipt.json'}")
    print(f"party_b receipt: {party_b_dir / 'output' / 'party_b_receipt.json'}")
    print(f"output rows: {summary['output_rows']}")
    print(f"output sha256: {summary['output_sha256']}")
    print()
    print("What this demonstrates:")
    print("- party_a container mounted only party_a plaintext input")
    print("- party_b container mounted only party_b plaintext input")
    print("- no centralized service stored both plaintext CSVs")
    print("- both parties produced matching receipts for the same session and output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
