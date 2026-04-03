# Repository Guidelines

## Project Structure & Module Organization
The active project is the SecretFlow proof of concept at the repo root. Start with `START_HERE.md`, then `README.md`. Runtime scripts such as `standalone_poc.py`, `run_2party_psi.py`, `run_2party_psi_peer.py`, and `strict_network_poc.py` live at the top level. Built-in fixtures and CSV templates are in `data/`. Reference material is in `docs/`. Generated runtime state is written under `poc_output/` and `out/strict_network_poc/`.

## Build, Test, and Development Commands
Pull the working SecretFlow image with `docker pull secretflow/secretflow-anolis8:latest`.

- `python3 standalone_poc.py --pull` runs the easiest laptop demo.
- `python3 normalize_domains.py --input raw.csv --output normalized.csv` canonicalizes domains before PSI.
- `python3 validate_inputs.py data/party_a_domains.csv data/party_b_domains.csv` validates the normalized CSV contract.
- `python3 strict_network_poc.py` runs the strict-trust two-container demo where each party keeps its plaintext input local.
- `python3 write_peer_psi_session.py ...` writes a shared session file for the strict-trust distributed mode.
- `python3 verify_peer_psi_receipts.py --party-a-receipt ... --party-b-receipt ...` verifies that both party-local receipts agree on the same run result.

## Coding Style & Naming Conventions
Use Python 3 with straightforward standard-library code where possible. Follow the existing style: UTF-8, LF line endings, spaces, and 4-space indentation in Python. Keep CSV contracts explicit, prefer descriptive `snake_case` names, and keep operator-facing console output concise and readable.

## Testing Guidelines
Use the built-in fixtures in `data/` first. Validate local changes with `python3 -m py_compile` on modified scripts, then run either `python3 standalone_poc.py --pull` or `python3 strict_network_poc.py` depending on whether the change affects the local or distributed strict-trust flow. Keep real customer data out of git and out of sample fixtures.

## Commit & Pull Request Guidelines
Use short, imperative commit subjects that describe the user-visible change, for example `Promote SecretFlow POC to repo root`. For pull requests, explain whether the change affects the standalone POC or the strict-trust distributed mode; list the commands you ran; and call out any security impact.
