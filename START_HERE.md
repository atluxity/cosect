# Start Here

Use this page if you want to test the POC quickly without reading the full reference docs first.

This repository includes sample CSV fixtures in `data/` and deeper operational docs in `docs/`.

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
- writes `poc_output/audit.json` with input and output hashes plus execution metadata

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

## Option 2: Strict-Trust Remote PSI

Use this when the parties are only semi-trusted and neither side may upload a plaintext CSV to the other side.

Requirements:

- Docker installed

Run:

```bash
python3 strict_network_poc.py
```

What it does:

- starts one SecretFlow container for Party A and one for Party B
- mounts Party A plaintext only into Party A's container
- mounts Party B plaintext only into Party B's container
- shares only a session file with addresses and file locations
- runs SecretFlow in production mode across the two parties
- writes one local receipt per party and verifies that the receipts agree on the same output

## Built-In Test Data

- `data/list_a_200_popular_domains.csv`: 200 popular domains
- `data/list_b_10_random_from_a.csv`: 10 guaranteed overlaps against A
- `data/list_b_50_not_in_a.csv`: 50 disjoint domains
- `data/list_b_60_mixed.csv`: 60 domains with exactly 10 overlaps against A

## Read Next

- [README.md](README.md): overview
- [docs/NETWORK_MVP.md](docs/NETWORK_MVP.md): network shape and trust boundary
- [docs/STRICT_TRUST_MODE.md](docs/STRICT_TRUST_MODE.md): architecture for semi-trusted remote peers
- [docs/AUDIT_SCHEMA.md](docs/AUDIT_SCHEMA.md): audit and verification receipt fields
- [docs/MVP_SPEC.md](docs/MVP_SPEC.md): acceptance criteria and deferred work
