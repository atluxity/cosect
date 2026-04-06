#!/usr/bin/env python3
"""Helpers for the OpenMined PSI backend."""

from __future__ import annotations

import base64
import csv
import json
import socket
import struct
import time
from pathlib import Path


DEFAULT_PROTOCOL = "OPENMINED_ECDH"
DEFAULT_FALSE_POSITIVE_RATE = 1e-9


def require_supported_protocol(protocol: str) -> None:
    if protocol != DEFAULT_PROTOCOL:
        raise SystemExit(
            f"unsupported OpenMined protocol: {protocol}. "
            f"Use {DEFAULT_PROTOCOL} for the openmined engine."
        )


def import_openmined():
    try:
        from private_set_intersection.python import (
            Request,
            Response,
            ServerSetup,
            __version__,
            client,
            server,
        )
    except ImportError as exc:
        raise SystemExit(
            "OpenMined PSI is not installed. "
            "Create .venv-openmined and install openmined-psi before using engine=openmined."
        ) from exc
    return {
        "Request": Request,
        "Response": Response,
        "ServerSetup": ServerSetup,
        "client": client,
        "server": server,
        "version": __version__,
    }


def read_domains(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as infile:
        return [row["domain"] for row in csv.DictReader(infile)]


def write_domains(path: Path, domains: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=["domain"])
        writer.writeheader()
        for domain in domains:
            writer.writerow({"domain": domain})


def build_reports(
    client_party: str,
    client_rows: int,
    server_party: str,
    server_rows: int,
    intersection_rows: int,
) -> list[dict]:
    counts = {
        client_party: client_rows,
        server_party: server_rows,
    }
    return [
        {
            "party": "party_a",
            "original_count": counts["party_a"],
            "intersection_count": intersection_rows,
        },
        {
            "party": "party_b",
            "original_count": counts["party_b"],
            "intersection_count": intersection_rows,
        },
    ]


def compute_local_intersection(
    party_a_domains: list[str],
    party_b_domains: list[str],
    protocol: str,
) -> tuple[list[str], list[dict], str]:
    require_supported_protocol(protocol)
    api = import_openmined()
    client_runner = api["client"].CreateWithNewKey(True)
    server_runner = api["server"].CreateWithNewKey(True)
    request = client_runner.CreateRequest(party_a_domains)
    setup = server_runner.CreateSetupMessage(
        DEFAULT_FALSE_POSITIVE_RATE,
        len(party_a_domains),
        party_b_domains,
    )
    response = server_runner.ProcessRequest(request)
    intersection_indices = client_runner.GetIntersection(setup, response)
    intersection = sorted(party_a_domains[index] for index in intersection_indices)
    reports = build_reports("party_a", len(party_a_domains), "party_b", len(party_b_domains), len(intersection))
    return intersection, reports, api["version"]


def _encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _decode_bytes(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def send_message(sock: socket.socket, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    sock.sendall(struct.pack("!I", len(data)) + data)


def recv_message(sock: socket.socket) -> dict:
    raw_size = _recv_exact(sock, 4)
    size = struct.unpack("!I", raw_size)[0]
    return json.loads(_recv_exact(sock, size).decode("utf-8"))


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    parts: list[bytes] = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise SystemExit("unexpected EOF while reading OpenMined peer message")
        parts.append(chunk)
        remaining -= len(chunk)
    return b"".join(parts)


def connect_with_retry(address: str, attempts: int = 50, delay_seconds: float = 0.2) -> socket.socket:
    host, port_str = address.rsplit(":", 1)
    port = int(port_str)
    last_error = None
    for _ in range(attempts):
        try:
            sock = socket.create_connection((host, port), timeout=5.0)
            sock.settimeout(5.0)
            return sock
        except OSError as exc:
            last_error = exc
            time.sleep(delay_seconds)
    raise SystemExit(f"unable to connect to OpenMined peer at {address}: {last_error}")


def openmined_client_exchange(
    local_domains: list[str],
    server_address: str,
    protocol: str,
    client_party: str,
    server_party: str,
) -> tuple[list[str], list[dict], str]:
    require_supported_protocol(protocol)
    api = import_openmined()
    client_runner = api["client"].CreateWithNewKey(True)
    request = client_runner.CreateRequest(local_domains)

    with connect_with_retry(server_address) as sock:
        send_message(
            sock,
            {
                "type": "client_request",
                "protocol": protocol,
                "client_row_count": len(local_domains),
                "request_b64": _encode_bytes(request.SerializeToString()),
            },
        )
        server_material = recv_message(sock)
        if server_material.get("type") != "server_material":
            raise SystemExit("unexpected OpenMined server reply")

        setup = api["ServerSetup"]()
        setup.ParseFromString(_decode_bytes(server_material["setup_b64"]))
        response = api["Response"]()
        response.ParseFromString(_decode_bytes(server_material["response_b64"]))
        intersection_indices = client_runner.GetIntersection(setup, response)
        intersection = sorted(local_domains[index] for index in intersection_indices)
        send_message(
            sock,
            {
                "type": "intersection_rows",
                "rows": intersection,
            },
        )
        reports = build_reports(
            client_party,
            len(local_domains),
            server_party,
            int(server_material["server_row_count"]),
            len(intersection),
        )
        return intersection, reports, api["version"]


def openmined_server_exchange(
    local_domains: list[str],
    listen_address: str,
    protocol: str,
    client_party: str,
    server_party: str,
) -> tuple[list[str], list[dict], str]:
    require_supported_protocol(protocol)
    api = import_openmined()
    server_runner = api["server"].CreateWithNewKey(True)
    host, port_str = listen_address.rsplit(":", 1)
    port = int(port_str)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen(1)
        conn, _ = listener.accept()
        with conn:
            conn.settimeout(5.0)
            client_message = recv_message(conn)
            if client_message.get("type") != "client_request":
                raise SystemExit("unexpected OpenMined client message")
            if client_message.get("protocol") != protocol:
                raise SystemExit("OpenMined client/server protocol mismatch")

            request = api["Request"]()
            request.ParseFromString(_decode_bytes(client_message["request_b64"]))
            setup = server_runner.CreateSetupMessage(
                DEFAULT_FALSE_POSITIVE_RATE,
                int(client_message["client_row_count"]),
                local_domains,
            )
            response = server_runner.ProcessRequest(request)
            send_message(
                conn,
                {
                    "type": "server_material",
                    "server_row_count": len(local_domains),
                    "setup_b64": _encode_bytes(setup.SerializeToString()),
                    "response_b64": _encode_bytes(response.SerializeToString()),
                },
            )
            result_message = recv_message(conn)
            if result_message.get("type") != "intersection_rows":
                raise SystemExit("OpenMined client did not return final intersection rows")
            intersection = sorted(result_message["rows"])
            reports = build_reports(
                client_party,
                int(client_message["client_row_count"]),
                server_party,
                len(local_domains),
                len(intersection),
            )
            return intersection, reports, api["version"]
