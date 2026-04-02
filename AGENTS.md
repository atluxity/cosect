# Repository Guidelines

## Project Structure & Module Organization
The active project is the SecretFlow proof of concept at the repo root. Start with `START_HERE.md`, then `README.md`. Runtime scripts such as `standalone_poc.py`, `coordinator.py`, and `run_2party_psi.py` live at the top level. Supporting helpers such as `stage_run.py`, `verify_run.py`, `archive_run.py`, and `cleanup_runs.py` also live at the top level. `SECURITY.md` captures protocol caveats, and `CADDYFILE.example` plus `nginx.conf.example` contain reverse-proxy examples. Generated runtime state is written under `runs/`, `archives/`, and `poc_output/`.

## Build, Test, and Development Commands
Pull the working SecretFlow image with `docker pull secretflow/secretflow-anolis8:latest`.

- `python3 standalone_poc.py --party-a path/to/party_a.csv --party-b path/to/party_b.csv --pull` runs the easiest laptop demo.
- `python3 normalize_domains.py --input raw.csv --output normalized.csv` canonicalizes domains before PSI.
- `python3 validate_inputs.py party_a.csv party_b.csv` validates the normalized CSV contract.
- `python3 prepare_and_run.py --job-id psi-demo --party-a-raw party_a.csv --party-b-raw party_b.csv` runs the local workflow wrapper.
- `python3 coordinator.py --env-file .env` starts the local/private coordinator.
- `python3 http_integration_test.py --base-url http://127.0.0.1:8080 ...` exercises the coordinator end to end.

## Coding Style & Naming Conventions
Use Python 3 with straightforward standard-library code where possible. Follow the existing style: UTF-8, LF line endings, spaces, and 4-space indentation in Python. Keep CSV contracts explicit, prefer descriptive `snake_case` names, and keep operator-facing console output concise and readable.

## Testing Guidelines
Use small local CSV fixtures with a single `domain` header. Validate local changes with `python3 -m py_compile` on modified scripts, then run either `python3 standalone_poc.py --party-a ... --party-b ... --pull` or `python3 http_integration_test.py ...` depending on whether the change affects the coordinator. Keep real customer data out of git and out of any sample fixtures you create locally.

## Commit & Pull Request Guidelines
Use short, imperative commit subjects that describe the user-visible change, for example `Promote SecretFlow POC to repo root`. For pull requests, explain whether the change affects the standalone POC, the coordinator, or deployment docs; list the commands you ran; and call out any security or retention impact.
