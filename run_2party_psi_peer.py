#!/usr/bin/env python3
"""Run a two-party SecretFlow PSI job with plaintext inputs kept on each party's own host."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from copy import deepcopy
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


def short_fingerprint(value: str, prefix: int = 16) -> str:
    return value[:prefix]


def normalize_session(session: dict) -> dict:
    required_top_level = {"job_id", "protocol", "parties", "spu"}
    missing = required_top_level - set(session)
    if missing:
        raise SystemExit(f"session file missing keys: {', '.join(sorted(missing))}")
    parties = session["parties"]
    if set(parties) != {"party_a", "party_b"}:
        raise SystemExit("session file must define exactly party_a and party_b")
    for party_name, party in parties.items():
        for field in ("address", "input_path", "output_path", "receipt_path"):
            if field not in party:
                raise SystemExit(f"session file missing parties.{party_name}.{field}")
    spu_nodes = session["spu"].get("nodes", {})
    if set(spu_nodes) != {"party_a", "party_b"}:
        raise SystemExit("session file must define spu.nodes for party_a and party_b")
    for party_name, node in spu_nodes.items():
        if "address" not in node:
            raise SystemExit(f"session file missing spu.nodes.{party_name}.address")
    return session


def cluster_config_for(session: dict, self_party: str) -> dict:
    parties = {}
    for party_name, party in session["parties"].items():
        entry = {"address": party["address"]}
        if "listen_addr" in party:
            entry["listen_addr"] = party["listen_addr"]
        parties[party_name] = entry
    return {"self_party": self_party, "parties": parties}


def spu_cluster_def(sf_module, session: dict) -> dict:
    runtime_config = deepcopy(sf_module.utils.testing.DEFAULT_SEMI2K_RUNTIME_CONFIG)
    return {
        "nodes": [
            {"party": "party_a", "address": session["spu"]["nodes"]["party_a"]["address"]},
            {"party": "party_b", "address": session["spu"]["nodes"]["party_b"]["address"]},
        ],
        "runtime_config": runtime_config,
    }


def maybe_tls_config(session: dict, self_party: str) -> dict | None:
    tls = session.get("tls")
    if not tls:
        return None
    if self_party not in tls:
        raise SystemExit(f"session file missing tls config for {self_party}")
    party_tls = tls[self_party]
    required = ("key_path", "cert_path", "ca_cert_path")
    missing = [field for field in required if field not in party_tls]
    if missing:
        raise SystemExit(f"tls config for {self_party} missing fields: {', '.join(missing)}")
    return {
        "key": Path(party_tls["key_path"]).read_text(encoding="utf-8"),
        "cert": Path(party_tls["cert_path"]).read_text(encoding="utf-8"),
        "ca_cert": Path(party_tls["ca_cert_path"]).read_text(encoding="utf-8"),
    }


def validate_local_input(input_path: Path) -> None:
    script_path = Path(__file__).with_name("validate_inputs.py")
    subprocess.run(["python3", str(script_path), str(input_path)], check=True)


def print_step(self_party: str, message: str) -> None:
    print(f"[peer:{self_party}] {message}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--party", required=True, choices=("party_a", "party_b"))
    parser.add_argument("--session-file", required=True, help="Shared JSON session file")
    parser.add_argument(
        "--ray-mode",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable Ray-backed production mode instead of thread-pool production mode",
    )
    parser.add_argument(
        "--print-receipt-json",
        action="store_true",
        help="Print the full local receipt JSON to stdout",
    )
    args = parser.parse_args()

    session_path = Path(args.session_file).resolve()
    session = normalize_session(json.loads(session_path.read_text(encoding="utf-8")))
    self_party = args.party
    self_config = session["parties"][self_party]
    local_input_path = Path(self_config["input_path"]).resolve()
    local_output_path = Path(self_config["output_path"]).resolve()
    receipt_path = Path(self_config["receipt_path"]).resolve()
    local_output_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    print_step(self_party, f"job id: {session['job_id']}")
    print_step(self_party, f"session file: {session_path}")
    print_step(self_party, f"local input: {local_input_path} ({count_rows(local_input_path)} rows)")
    print_step(self_party, f"local output will be written to: {local_output_path}")
    print_step(self_party, "validating local input")
    validate_local_input(local_input_path)

    try:
        import secretflow as sf
    except ImportError as exc:
        raise SystemExit(
            "SecretFlow is not installed. Run this inside the SecretFlow environment or container."
        ) from exc

    start_monotonic = time.monotonic()
    started_at = datetime.now(timezone.utc)
    print_step(self_party, "starting the local SecretFlow worker")
    sf.init(
        address=None,
        cluster_config=cluster_config_for(session, self_party),
        ray_mode=args.ray_mode,
        cross_silo_comm_backend=session.get("cross_silo_comm_backend", "grpc"),
        cross_silo_comm_options=session.get("cross_silo_comm_options"),
        enable_waiting_for_other_parties_ready=session.get("enable_waiting_for_other_parties_ready", True),
        tls_config=maybe_tls_config(session, self_party),
        job_name=session["job_id"],
    )

    party_a = sf.PYU("party_a")
    party_b = sf.PYU("party_b")
    spu = sf.SPU(spu_cluster_def(sf, session))
    input_path = {
        party_a: session["parties"]["party_a"]["input_path"],
        party_b: session["parties"]["party_b"]["input_path"],
    }
    output_path = {
        party_a: session["parties"]["party_a"]["output_path"],
        party_b: session["parties"]["party_b"]["output_path"],
    }

    print_step(self_party, "connecting to the other party and running PSI")
    print_step(self_party, "backend logs may appear while PSI is running")
    reports = spu.psi_csv(
        key="domain",
        input_path=input_path,
        output_path=output_path,
        receiver="party_a",
        protocol=session["protocol"],
        precheck_input=True,
        sort=True,
        broadcast_result=True,
    )
    completed_at = datetime.now(timezone.utc)
    elapsed_seconds = round(time.monotonic() - start_monotonic, 3)
    print_step(self_party, f"distributed PSI completed in {elapsed_seconds:.1f}s")

    if not local_output_path.exists():
        raise SystemExit(f"expected local output missing: {local_output_path}")

    local_output_rows = count_rows(local_output_path)
    local_output_sha256 = sha256_file(local_output_path)
    session_sha256 = sha256_file(session_path)
    receipt = {
        "job_id": session["job_id"],
        "self_party": self_party,
        "session_file": str(session_path),
        "session_sha256": session_sha256,
        "protocol": session["protocol"],
        "execution": {
            "started_at_utc": started_at.isoformat(),
            "completed_at_utc": completed_at.isoformat(),
            "duration_seconds": elapsed_seconds,
            "python_version": sys.version.split()[0],
            "secretflow_version": getattr(sf, "__version__", "unknown"),
            "runner_sha256": sha256_file(Path(__file__)),
            "validator_sha256": sha256_file(Path(__file__).with_name("validate_inputs.py")),
        },
        "local_input": {
            "path": str(local_input_path),
            "rows": count_rows(local_input_path),
            "sha256": sha256_file(local_input_path),
        },
        "local_output": {
            "path": str(local_output_path),
            "rows": local_output_rows,
            "sha256": local_output_sha256,
        },
        "reports": reports,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print_step(self_party, f"receipt written to {receipt_path}")
    if args.print_receipt_json:
        print(json.dumps(receipt, indent=2))
    else:
        print_step(self_party, f"local output written to {local_output_path}")
        print_step(
            self_party,
            f"local result: {local_output_rows} rows, fingerprint {short_fingerprint(local_output_sha256)}"
        )
        print_step(self_party, "status: success")

    sf.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
