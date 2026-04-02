# Start Here

Use this page if you want to test the POC quickly without reading through every script first.

This repository was moved to the root as a compact SecretFlow PSI proof of concept. The top-level Python files are the active entry points. Generated state such as `runs/`, `archives/`, and `poc_output/` is created on demand.

## Option 1: Standalone Local Demo

Use this for the fastest one-laptop test with console output.

Requirements:

- Docker installed
- Two normalized CSV files with a single header named `domain`

Run:

```bash
python3 standalone_poc.py \
  --party-a path/to/party_a.csv \
  --party-b path/to/party_b.csv \
  --pull
```

What it does:

- mounts this repository into the SecretFlow container
- runs the SecretFlow PSI flow locally in Docker
- prints the intersection summary and matching domains

Optional flags:

- `--job-id psi-demo-local`
- `--out-dir poc_output`
- `--image secretflow/secretflow-anolis8:latest`

CSV format:

```csv
domain
example.com
shared.example
```

Validate normalized inputs before running PSI:

```bash
python3 validate_inputs.py path/to/party_a.csv path/to/party_b.csv
```

## Option 2: Local HTTP Coordinator

Use this if you want to test the networked job model on one machine first.

Requirements:

- Docker installed
- Python 3 available
- An env file containing temporary API keys, for example:

```dotenv
ADMIN_API_KEY=replace-admin-key
PARTY_A_API_KEY=replace-party-a-key
PARTY_B_API_KEY=replace-party-b-key
```

Start the coordinator:

```bash
python3 coordinator.py --env-file .env
```

Then run the authenticated integration test:

```bash
python3 http_integration_test.py \
  --base-url http://127.0.0.1:8080 \
  --job-id psi-http-demo-1 \
  --party-a path/to/party_a.csv \
  --party-b path/to/party_b.csv \
  --admin-api-key replace-admin-key \
  --party-a-api-key replace-party-a-key \
  --party-b-api-key replace-party-b-key
```

## Read Next

- [README.md](README.md): repository overview and command map
- [SECURITY.md](SECURITY.md): PSI caveats and security limitations
- `coordinator.py`: HTTP API implementation and job storage layout
- `standalone_poc.py`: simplest local Docker-backed PSI run
