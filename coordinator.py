#!/usr/bin/env python3
"""Minimal coordinator service for the SecretFlow PSI MVP."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR
RUNS_DIR = SCRIPT_DIR / "runs"
ARCHIVES_DIR = SCRIPT_DIR / "archives"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_INPUT_BYTES = 2 * 1024 * 1024
JOB_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
ADMIN_API_KEY: str | None = None
PARTY_A_API_KEY: str | None = None
PARTY_B_API_KEY: str | None = None
VALIDATE_TIMEOUT_SECONDS = 30
RUN_TIMEOUT_SECONDS = 300
VERIFY_TIMEOUT_SECONDS = 30
ARCHIVE_TIMEOUT_SECONDS = 30
RUN_LOCK = threading.Lock()
RATE_LIMIT_LOCK = threading.Lock()
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 120
RATE_LIMIT_STATE: dict[str, list[float]] = {}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def job_dir(job_id: str) -> Path:
    return RUNS_DIR / job_id


def status_path(job_id: str) -> Path:
    return job_dir(job_id) / "status.json"


def load_status(job_id: str) -> dict:
    path = status_path(job_id)
    if path.exists():
        return read_json(path)
    return {"job_id": job_id, "status": "created"}


def save_status(job_id: str, status: str, detail: str | None = None) -> dict:
    payload = {"job_id": job_id, "status": status}
    if detail:
        payload["detail"] = detail
    write_json(status_path(job_id), payload)
    return payload


def artifact_presence(job_id: str) -> dict:
    run_dir = job_dir(job_id)
    return {
        "manifest": (run_dir / "manifest.json").exists(),
        "party_a_input": (run_dir / "input" / "party_a_domains.csv").exists(),
        "party_b_input": (run_dir / "input" / "party_b_domains.csv").exists(),
        "audit": (run_dir / "output" / "audit.json").exists(),
        "party_a_result": (run_dir / "output" / "party_a_intersection.csv").exists(),
        "party_b_result": (run_dir / "output" / "party_b_intersection.csv").exists(),
    }


def current_status_name(job_id: str) -> str:
    return load_status(job_id)["status"]


def clear_run_outputs(job_id: str) -> None:
    run_dir = job_dir(job_id)
    for path in [
        run_dir / "output" / "audit.json",
        run_dir / "output" / "party_a_intersection.csv",
        run_dir / "output" / "party_b_intersection.csv",
        run_dir / "logs" / "run.log",
        run_dir / "logs" / "verify.log",
        run_dir / "logs" / "archive.log",
    ]:
        if path.exists():
            path.unlink()


def run_command(command: list[str], log_path: Path, timeout_seconds: int) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as logfile:
        subprocess.run(
            command,
            check=True,
            cwd=REPO_ROOT,
            stdout=logfile,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
        )


def validate_job_id(job_id: str) -> None:
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError(
            "invalid job_id: use 3-80 chars of lowercase letters, digits, dot, underscore, or hyphen"
        )


def ensure_mutable(job_id: str) -> None:
    status = current_status_name(job_id)
    if status in {"running", "verified", "archived"}:
        raise ValueError(f"job is immutable in status '{status}'")


def auth_enabled() -> bool:
    return any([ADMIN_API_KEY, PARTY_A_API_KEY, PARTY_B_API_KEY])


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def rate_limit_identity(api_key: str | None) -> str:
    return api_key or "anonymous"


def enforce_rate_limit(api_key: str | None) -> None:
    identity = rate_limit_identity(api_key)
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    with RATE_LIMIT_LOCK:
        bucket = [ts for ts in RATE_LIMIT_STATE.get(identity, []) if ts >= cutoff]
        if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
            raise PermissionError("rate limit exceeded")
        bucket.append(now)
        RATE_LIMIT_STATE[identity] = bucket


class CoordinatorHandler(BaseHTTPRequestHandler):
    server_version = "SecretFlowCoordinator/0.1"

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            raise ValueError("request body required")
        return self.rfile.read(length)

    def _read_limited_body(self, max_bytes: int) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            raise ValueError("request body required")
        if length > max_bytes:
            raise ValueError(f"request body exceeds {max_bytes} bytes")
        return self.rfile.read(length)

    def _json_body(self) -> dict:
        return json.loads(self._read_limited_body(MAX_MANIFEST_BYTES).decode("utf-8"))

    def _route(self) -> list[str]:
        return [part for part in urlparse(self.path).path.split("/") if part]

    def _api_key(self) -> str | None:
        return self.headers.get("X-API-Key")

    def _require_admin(self) -> None:
        if not auth_enabled():
            return
        if not ADMIN_API_KEY:
            raise PermissionError("admin API key not configured")
        if self._api_key() != ADMIN_API_KEY:
            raise PermissionError("admin API key required")

    def _require_party(self, party: str) -> None:
        if not auth_enabled():
            return
        key = self._api_key()
        party_key = PARTY_A_API_KEY if party == "party_a" else PARTY_B_API_KEY
        if key == ADMIN_API_KEY:
            return
        if not party_key or key != party_key:
            raise PermissionError(f"{party} API key required")

    def do_POST(self) -> None:
        try:
            enforce_rate_limit(self._api_key())
            route = self._route()
            if route == ["jobs"]:
                self._create_job()
                return
            if route == ["admin", "cleanup"]:
                self._cleanup()
                return
            if len(route) == 3 and route[0] == "jobs":
                job_id = route[1]
                action = route[2]
                if action == "validate":
                    self._validate(job_id)
                    return
                if action == "run":
                    self._run_job(job_id)
                    return
                if action == "verify":
                    self._verify(job_id)
                    return
                if action == "archive":
                    self._archive(job_id)
                    return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except subprocess.CalledProcessError as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "command failed", "returncode": exc.returncode},
            )
        except subprocess.TimeoutExpired:
            self._send_json(HTTPStatus.REQUEST_TIMEOUT, {"error": "command timed out"})
        except PermissionError as exc:
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def do_PUT(self) -> None:
        try:
            enforce_rate_limit(self._api_key())
            route = self._route()
            if len(route) == 4 and route[0] == "jobs" and route[2] == "inputs":
                self._upload_input(route[1], route[3])
                return
            if len(route) == 3 and route[0] == "jobs" and route[2] == "manifest":
                self._upload_manifest(route[1])
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except PermissionError as exc:
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def do_GET(self) -> None:
        try:
            enforce_rate_limit(self._api_key())
            route = self._route()
            if len(route) == 2 and route[0] == "jobs":
                self._get_job(route[1])
                return
            if len(route) == 4 and route[0] == "jobs" and route[2] == "results":
                self._get_result(route[1], route[3])
                return
            if len(route) == 3 and route[0] == "jobs" and route[2] == "audit":
                self._get_audit(route[1])
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except PermissionError as exc:
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def _create_job(self) -> None:
        self._require_admin()
        payload = self._json_body()
        job_id = payload["job_id"]
        validate_job_id(job_id)
        run_dir = job_dir(job_id)
        if run_dir.exists():
            self._send_json(HTTPStatus.CONFLICT, {"error": "job already exists"})
            return
        (run_dir / "input").mkdir(parents=True, exist_ok=False)
        (run_dir / "output").mkdir(parents=True, exist_ok=False)
        (run_dir / "logs").mkdir(parents=True, exist_ok=False)
        status = save_status(job_id, "created")
        self._send_json(HTTPStatus.CREATED, status)

    def _cleanup(self) -> None:
        self._require_admin()
        payload = self._json_body()
        keep_mode = payload.get("keep_mode", "everything")
        older_than_hours = int(payload.get("older_than_hours", 24))
        if keep_mode not in {"everything", "metadata-only", "delete-all"}:
            raise ValueError("invalid keep_mode")
        run_command(
            [
                "python3",
                str(SCRIPT_DIR / "cleanup_runs.py"),
                "--runs-dir",
                str(RUNS_DIR),
                "--archive-dir",
                str(ARCHIVES_DIR),
                "--keep-mode",
                keep_mode,
                "--older-than-hours",
                str(older_than_hours),
            ],
            SCRIPT_DIR / "cleanup.log",
            ARCHIVE_TIMEOUT_SECONDS,
        )
        self._send_json(
            HTTPStatus.OK,
            {
                "status": "cleanup_completed",
                "keep_mode": keep_mode,
                "older_than_hours": older_than_hours,
            },
        )

    def _upload_manifest(self, job_id: str) -> None:
        self._require_admin()
        validate_job_id(job_id)
        run_dir = job_dir(job_id)
        if not run_dir.exists():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "job not found"})
            return
        ensure_mutable(job_id)
        manifest = self._json_body()
        if manifest.get("job_id") != job_id:
            raise ValueError("manifest job_id must match path job_id")
        write_json(run_dir / "manifest.json", manifest)
        if artifact_presence(job_id)["audit"]:
            clear_run_outputs(job_id)
        next_status = "manifest_written"
        status = save_status(job_id, next_status)
        self._send_json(HTTPStatus.OK, status)

    def _upload_input(self, job_id: str, party: str) -> None:
        self._require_admin()
        validate_job_id(job_id)
        if party not in {"party_a", "party_b"}:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown party"})
            return
        run_dir = job_dir(job_id)
        if not run_dir.exists():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "job not found"})
            return
        ensure_mutable(job_id)
        path = run_dir / "input" / f"{party}_domains.csv"
        body = self._read_limited_body(MAX_INPUT_BYTES)
        if not body.startswith(b"domain\n"):
            raise ValueError("CSV must start with a 'domain' header")
        path.write_bytes(body)
        if artifact_presence(job_id)["audit"]:
            clear_run_outputs(job_id)
        artifacts = artifact_presence(job_id)
        status_name = (
            "inputs_uploaded"
            if artifacts["party_a_input"] and artifacts["party_b_input"]
            else current_status_name(job_id)
        )
        status = save_status(job_id, status_name)
        self._send_json(HTTPStatus.OK, status)

    def _validate(self, job_id: str) -> None:
        self._require_admin()
        validate_job_id(job_id)
        run_dir = job_dir(job_id)
        ensure_mutable(job_id)
        if not (run_dir / "manifest.json").exists():
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "manifest missing"})
            return
        if not all((run_dir / "input" / f"{party}_domains.csv").exists() for party in ("party_a", "party_b")):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "inputs missing"})
            return
        save_status(job_id, "inputs_uploaded")
        run_command(
            [
                "python3",
                str(SCRIPT_DIR / "validate_inputs.py"),
                str(run_dir / "input" / "party_a_domains.csv"),
                str(run_dir / "input" / "party_b_domains.csv"),
            ],
            run_dir / "logs" / "validate.log",
            VALIDATE_TIMEOUT_SECONDS,
        )
        status = save_status(job_id, "validated")
        self._send_json(HTTPStatus.OK, status)

    def _run_job(self, job_id: str) -> None:
        self._require_admin()
        validate_job_id(job_id)
        run_dir = job_dir(job_id)
        if current_status_name(job_id) != "validated":
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "job must be validated before run"})
            return
        if not (run_dir / "manifest.json").exists():
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "manifest missing"})
            return
        if not all((run_dir / "input" / f"{party}_domains.csv").exists() for party in ("party_a", "party_b")):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "inputs missing"})
            return
        if not RUN_LOCK.acquire(blocking=False):
            self._send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "another PSI run is already in progress"})
            return
        save_status(job_id, "running")
        try:
            run_command(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--entrypoint",
                    "python",
                    "-v",
                    f"{REPO_ROOT}:/workspace",
                    "-w",
                    "/workspace",
                    "secretflow/secretflow-anolis8:latest",
                    "run_2party_psi.py",
                    "--party-a",
                    str((run_dir / "input" / "party_a_domains.csv").relative_to(REPO_ROOT)),
                    "--party-b",
                    str((run_dir / "input" / "party_b_domains.csv").relative_to(REPO_ROOT)),
                    "--out-dir",
                    str((run_dir / "output").relative_to(REPO_ROOT)),
                    "--job-id",
                    job_id,
                ],
                run_dir / "logs" / "run.log",
                RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            self._send_json(
                HTTPStatus.REQUEST_TIMEOUT,
                save_status(job_id, "failed", f"run timed out after {RUN_TIMEOUT_SECONDS} seconds"),
            )
            return
        except subprocess.CalledProcessError as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                save_status(job_id, "failed", f"run failed with code {exc.returncode}"),
            )
            return
        finally:
            RUN_LOCK.release()
        status = save_status(job_id, "completed")
        self._send_json(HTTPStatus.OK, status)

    def _verify(self, job_id: str) -> None:
        self._require_admin()
        validate_job_id(job_id)
        run_dir = job_dir(job_id)
        artifacts = artifact_presence(job_id)
        if not (artifacts["audit"] and artifacts["party_a_result"] and artifacts["party_b_result"]):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "job must have completed artifacts before verify"})
            return
        try:
            run_command(
                [
                    "python3",
                    str(SCRIPT_DIR / "verify_run.py"),
                    "--job-id",
                    job_id,
                ],
                run_dir / "logs" / "verify.log",
                VERIFY_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            self._send_json(
                HTTPStatus.REQUEST_TIMEOUT,
                save_status(job_id, "failed", f"verify timed out after {VERIFY_TIMEOUT_SECONDS} seconds"),
            )
            return
        except subprocess.CalledProcessError as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                save_status(job_id, "failed", f"verify failed with code {exc.returncode}"),
            )
            return
        status = save_status(job_id, "verified")
        self._send_json(HTTPStatus.OK, status)

    def _archive(self, job_id: str) -> None:
        self._require_admin()
        validate_job_id(job_id)
        if current_status_name(job_id) != "verified":
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "job must be verified before archive"})
            return
        try:
            run_command(
                [
                    "python3",
                    str(SCRIPT_DIR / "archive_run.py"),
                    "--job-id",
                    job_id,
                    "--archive-dir",
                    str(ARCHIVES_DIR),
                ],
                job_dir(job_id) / "logs" / "archive.log",
                ARCHIVE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            self._send_json(
                HTTPStatus.REQUEST_TIMEOUT,
                save_status(job_id, "failed", f"archive timed out after {ARCHIVE_TIMEOUT_SECONDS} seconds"),
            )
            return
        except subprocess.CalledProcessError as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                save_status(job_id, "failed", f"archive failed with code {exc.returncode}"),
            )
            return
        status = save_status(job_id, "archived")
        self._send_json(HTTPStatus.OK, status)

    def _get_job(self, job_id: str) -> None:
        self._require_admin()
        validate_job_id(job_id)
        if not job_dir(job_id).exists():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "job not found"})
            return
        payload = load_status(job_id)
        payload["artifacts"] = artifact_presence(job_id)
        self._send_json(HTTPStatus.OK, payload)

    def _get_result(self, job_id: str, party: str) -> None:
        validate_job_id(job_id)
        if party not in {"party_a", "party_b"}:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown party"})
            return
        self._require_party(party)
        path = job_dir(job_id) / "output" / f"{party}_intersection.csv"
        if not path.exists():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "result not found"})
            return
        self._send_bytes(HTTPStatus.OK, path.read_bytes(), "text/csv; charset=utf-8")

    def _get_audit(self, job_id: str) -> None:
        self._require_admin()
        validate_job_id(job_id)
        path = job_dir(job_id) / "output" / "audit.json"
        if not path.exists():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "audit not found"})
            return
        self._send_bytes(HTTPStatus.OK, path.read_bytes(), "application/json")


def main() -> int:
    global ADMIN_API_KEY, PARTY_A_API_KEY, PARTY_B_API_KEY
    global VALIDATE_TIMEOUT_SECONDS, RUN_TIMEOUT_SECONDS, VERIFY_TIMEOUT_SECONDS, ARCHIVE_TIMEOUT_SECONDS
    global RATE_LIMIT_WINDOW_SECONDS, RATE_LIMIT_MAX_REQUESTS
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=str(SCRIPT_DIR / ".env"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--admin-api-key", default=None)
    parser.add_argument("--party-a-api-key", default=None)
    parser.add_argument("--party-b-api-key", default=None)
    parser.add_argument("--validate-timeout-seconds", type=int, default=VALIDATE_TIMEOUT_SECONDS)
    parser.add_argument("--run-timeout-seconds", type=int, default=RUN_TIMEOUT_SECONDS)
    parser.add_argument("--verify-timeout-seconds", type=int, default=VERIFY_TIMEOUT_SECONDS)
    parser.add_argument("--archive-timeout-seconds", type=int, default=ARCHIVE_TIMEOUT_SECONDS)
    parser.add_argument("--rate-limit-window-seconds", type=int, default=RATE_LIMIT_WINDOW_SECONDS)
    parser.add_argument("--rate-limit-max-requests", type=int, default=RATE_LIMIT_MAX_REQUESTS)
    args = parser.parse_args()

    load_env_file(Path(args.env_file))

    host = os.environ.get("PSI_COORDINATOR_HOST", args.host)
    port = int(os.environ.get("PSI_COORDINATOR_PORT", str(args.port)))

    ADMIN_API_KEY = args.admin_api_key or os.environ.get("PSI_COORDINATOR_ADMIN_API_KEY")
    PARTY_A_API_KEY = args.party_a_api_key or os.environ.get("PSI_COORDINATOR_PARTY_A_API_KEY")
    PARTY_B_API_KEY = args.party_b_api_key or os.environ.get("PSI_COORDINATOR_PARTY_B_API_KEY")
    VALIDATE_TIMEOUT_SECONDS = int(os.environ.get("PSI_COORDINATOR_VALIDATE_TIMEOUT_SECONDS", str(args.validate_timeout_seconds)))
    RUN_TIMEOUT_SECONDS = int(os.environ.get("PSI_COORDINATOR_RUN_TIMEOUT_SECONDS", str(args.run_timeout_seconds)))
    VERIFY_TIMEOUT_SECONDS = int(os.environ.get("PSI_COORDINATOR_VERIFY_TIMEOUT_SECONDS", str(args.verify_timeout_seconds)))
    ARCHIVE_TIMEOUT_SECONDS = int(os.environ.get("PSI_COORDINATOR_ARCHIVE_TIMEOUT_SECONDS", str(args.archive_timeout_seconds)))
    RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("PSI_COORDINATOR_RATE_LIMIT_WINDOW_SECONDS", str(args.rate_limit_window_seconds)))
    RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("PSI_COORDINATOR_RATE_LIMIT_MAX_REQUESTS", str(args.rate_limit_max_requests)))

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer((host, port), CoordinatorHandler)
    print(f"listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
