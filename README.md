# SecretFlow PSI POC

This repository is now centered on a standalone SecretFlow-based proof of concept for two organizations that want to learn only the overlap between their domain lists without exchanging full customer lists in plaintext.

Start with [START_HERE.md](START_HERE.md).

If you just want the fastest laptop demo with console output, provide two normalized CSV files:

```bash
python3 standalone_poc.py \
  --party-a path/to/party_a.csv \
  --party-b path/to/party_b.csv \
  --pull
```

## Repository Layout

- `START_HERE.md`: quickest path to a working test
- `README.md`: high-level overview
- `SECURITY.md`: PSI caveats and protocol limitations
- `standalone_poc.py`: simplest local demo
- `coordinator.py`: local/private HTTP job wrapper
- `prepare_and_run.py`: normalize, validate, stage, and optionally run PSI
- `run_2party_psi.py`: local SecretFlow PSI runner used by the wrappers
- `stage_run.py`, `verify_run.py`, `archive_run.py`, `cleanup_runs.py`, `write_manifest.py`: job lifecycle helpers
- `CADDYFILE.example` and `nginx.conf.example`: reverse-proxy examples
- `runs/`, `archives/`, and `poc_output/`: generated at runtime and not stored in git

## Goal

The current POC is designed to prove four things:

- exact set intersection
- output to both parties
- auditable execution
- no plaintext full-list transfer between parties

## Input Format

Use a single CSV column named `domain`.

```csv
domain
example.com
shared.example
```

Normalize before PSI with:

```bash
python3 normalize_domains.py --input raw.csv --output normalized.csv
```

Validate the normalized CSVs with:

```bash
python3 validate_inputs.py path/to/party_a.csv path/to/party_b.csv
```

## Two Main Entry Points

For a laptop demo:

```bash
python3 standalone_poc.py \
  --party-a path/to/party_a.csv \
  --party-b path/to/party_b.csv \
  --pull
```

For the local HTTP job model:

```bash
cat > .env <<'EOF'
ADMIN_API_KEY=replace-admin-key
PARTY_A_API_KEY=replace-party-a-key
PARTY_B_API_KEY=replace-party-b-key
EOF

python3 coordinator.py --env-file .env

python3 http_integration_test.py \
  --base-url http://127.0.0.1:8080 \
  --job-id psi-http-demo-1 \
  --party-a path/to/party_a.csv \
  --party-b path/to/party_b.csv \
  --admin-api-key replace-admin-key \
  --party-a-api-key replace-party-a-key \
  --party-b-api-key replace-party-b-key
```

## Generated Layout

- `runs/<job_id>/`: staged inputs, status, logs, and output artifacts for active jobs
- `archives/<job_id>/`: archived job bundles produced by `archive_run.py`
- `poc_output/`: default output directory for the standalone demo

## License

This repository is distributed under Apache License 2.0.

## Additional Notes

- `coordinator.py` is the source of truth for the HTTP routes and artifact names.
- `SECURITY.md` captures protocol caveats and attack-surface assumptions.
- Reverse-proxy examples live in `CADDYFILE.example` and `nginx.conf.example`.
