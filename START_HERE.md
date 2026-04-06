# Start Here

## BLUF

If the trust boundary matters, use the distributed remote path.

In the distributed path, Party A keeps its plaintext on Party A's host and Party B keeps its plaintext on Party B's host. The standalone path is for quick local validation on one machine.

This repository includes sample CSV fixtures in `data/` and deeper operational docs in `docs/`.

The repository currently supports `secretflow` and `openmined`.

## Option 1: Standalone Local Demo

Use this for the fastest one-host sanity check.

Requirements:

- Docker installed for `engine=secretflow`
- `.venv-openmined` with `openmined-psi` installed for `engine=openmined`

Run:

```bash
python3 standalone_poc.py --pull
```

Or:

```bash
python3 standalone_poc.py --engine openmined
```

What it does:

- uses the built-in 200-vs-60 mixed fixture
- runs the selected PSI engine locally
- prints the intersection summary and matching domains
- writes an `audit.json` file with input and output hashes plus execution metadata

What it leaves out:

- the remote trust boundary
- party-local plaintext retention
- the absence of centralized plaintext staging

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

## Option 2: Distributed Remote PSI

Use this when the parties are semi-trusted and neither side may upload a plaintext CSV to the other side.

Requirements:

- Docker installed for `engine=secretflow`
- `.venv-openmined` with `openmined-psi` installed for `engine=openmined`

Run:

```bash
python3 distributed_network_poc.py
```

Or:

```bash
python3 distributed_network_poc.py --engine openmined
```

What it does:

- starts one worker for Party A and one for Party B
- keeps Party A plaintext local to Party A's side
- keeps Party B plaintext local to Party B's side
- shares only a session file with addresses and file locations
- runs the selected PSI engine across the two parties
- writes one local receipt per party and verifies that the receipts agree on the same output

What to inspect after the run:

- Party A receipt
- Party B receipt
- matching output hash and row count from `verify_peer_psi_receipts.py`

## Built-In Test Data

- `data/list_a_200_popular_domains.csv`: 200 popular domains
- `data/list_b_10_random_from_a.csv`: 10 guaranteed overlaps against A
- `data/list_b_50_not_in_a.csv`: 50 disjoint domains
- `data/list_b_60_mixed.csv`: 60 domains with exactly 10 overlaps against A

## Read Next

- [README.md](README.md): overview
- [docs/NETWORK_MVP.md](docs/NETWORK_MVP.md): network shape and trust boundary
- [docs/DISTRIBUTED_MODE.md](docs/DISTRIBUTED_MODE.md): architecture for semi-trusted remote peers
- [docs/AUDIT_SCHEMA.md](docs/AUDIT_SCHEMA.md): audit and verification receipt fields
- [docs/MVP_SPEC.md](docs/MVP_SPEC.md): acceptance criteria and deferred work
- [docs/ENGINE_OPTIONS.md](docs/ENGINE_OPTIONS.md): current backend choices and tradeoffs
- [docs/SECRETFLOW_DUE_DILIGENCE.md](docs/SECRETFLOW_DUE_DILIGENCE.md): due-diligence notes on the SecretFlow backend
- [docs/OPENMINED_DUE_DILIGENCE.md](docs/OPENMINED_DUE_DILIGENCE.md): due-diligence notes on the OpenMined backend
