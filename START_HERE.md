# Start Here

Use this page if you want to test the POC quickly without reading the full reference docs first.

This repository includes sample CSV fixtures in `data/`, deeper operational docs in `docs/`, and example service units in `systemd/`.

## Option 1: Standalone Local Demo

Use this for the fastest one-laptop test with console output.

Requirements:

- Docker installed

Run:

```bash
python3 standalone_poc.py --pull
```

What it does:

- uses the built-in 200-vs-60 mixed fixture
- runs the SecretFlow PSI flow locally in Docker
- prints the intersection summary and matching domains

Use your own CSVs:

```bash
python3 standalone_poc.py \
  --party-a path/to/party_a.csv \
  --party-b path/to/party_b.csv \
  --job-id psi-demo-local
```

Validate normalized inputs before running PSI:

```bash
python3 validate_inputs.py path/to/party_a.csv path/to/party_b.csv
```

CSV format:

```csv
domain
example.com
shared.example
```

## Option 2: Local HTTP Coordinator

Use this if you want to test the networked job model on one machine first.

Requirements:

- Docker installed
- Python 3 available

Copy the env template and set temporary keys:

```bash
cp .env.example .env
```

The template uses the `PSI_COORDINATOR_*` environment variable names that `coordinator.py` reads at startup.

Start the coordinator:

```bash
python3 coordinator.py --env-file .env
```

Then run the authenticated integration test:

```bash
python3 http_integration_test.py \
  --base-url http://127.0.0.1:8080 \
  --job-id psi-http-demo-1 \
  --party-a data/list_a_200_popular_domains.csv \
  --party-b data/list_b_60_mixed.csv \
  --admin-api-key replace-admin-key \
  --party-a-api-key replace-party-a-key \
  --party-b-api-key replace-party-b-key
```

## Built-In Test Data

- `data/list_a_200_popular_domains.csv`: 200 popular domains
- `data/list_b_10_random_from_a.csv`: 10 guaranteed overlaps against A
- `data/list_b_50_not_in_a.csv`: 50 disjoint domains
- `data/list_b_60_mixed.csv`: 60 domains with exactly 10 overlaps against A

## Read Next

- [README.md](README.md): overview
- [docs/COORDINATOR.md](docs/COORDINATOR.md): coordinator usage
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): reverse-proxy and TLS assumptions
- [docs/SECURITY_CHECKLIST.md](docs/SECURITY_CHECKLIST.md): operational safety checks
- [docs/RETENTION.md](docs/RETENTION.md): retention modes
