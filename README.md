# SecretFlow PSI POC

This repository is now centered on a standalone SecretFlow-based proof of concept for two organizations that want to learn only the overlap between their domain lists without exchanging full customer lists in plaintext.

Start with [START_HERE.md](START_HERE.md).

If you just want the fastest laptop demo with console output:

```bash
python3 standalone_poc.py --pull
```

## Repository Layout

- `START_HERE.md`: quickest path to a working test
- `README.md`: high-level overview
- `data/`: built-in test fixtures and raw CSV templates
- `docs/`: protocol, coordinator, security, deployment, and retention docs
- `systemd/`: example service and timer units
- `.env.example`: coordinator environment template
- `standalone_poc.py`: simplest local demo
- `strict_network_poc.py`: two-container strict-trust demo with no centralized plaintext CSV upload
- `run_2party_psi_peer.py`: production-mode party-local PSI runner for real two-host execution
- `write_peer_psi_session.py`: shared session file generator for the strict-trust flow
- `verify_peer_psi_receipts.py`: compares the two party-local receipts for the same distributed run
- `coordinator.py`: local/private HTTP job wrapper
- `prepare_and_run.py`: normalize, validate, stage, and optionally run PSI
- `run_2party_psi.py`: local SecretFlow PSI runner used by the wrappers
- `stage_run.py`, `verify_run.py`, `archive_run.py`, `cleanup_runs.py`: run lifecycle helpers

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

Validate normalized inputs with:

```bash
python3 validate_inputs.py data/party_a_domains.csv data/party_b_domains.csv
```

## Two Main Entry Points

For a laptop demo:

```bash
python3 standalone_poc.py --pull
```

For the strict-trust remote model where neither party may upload plaintext CSVs to the other side:

```bash
python3 strict_network_poc.py
```

That demo starts two separate SecretFlow containers. Each container mounts only its own party's plaintext CSV plus a shared session file. The two parties then run SecretFlow in production mode against each other over the network and produce matching receipts.

For the older local HTTP job model:

```bash
cp .env.example .env
python3 coordinator.py --env-file .env
python3 http_integration_test.py \
  --base-url http://127.0.0.1:8080 \
  --job-id psi-http-demo-1 \
  --party-a data/list_a_200_popular_domains.csv \
  --party-b data/list_b_60_mixed.csv \
  --admin-api-key replace-admin-key \
  --party-a-api-key replace-party-a-key \
  --party-b-api-key replace-party-b-key
```

That HTTP coordinator path is still useful for a trusted local workflow wrapper, but it is not acceptable when one semi-trusted party must never receive the other party's plaintext CSV.

## Built-In Test Data

- `data/list_a_200_popular_domains.csv`: 200 popular domains
- `data/list_b_10_random_from_a.csv`: 10 guaranteed overlaps against A
- `data/list_b_50_not_in_a.csv`: 50 disjoint domains
- `data/list_b_60_mixed.csv`: 60 domains with exactly 10 overlaps against A

## Runtime Output

- `runs/<job_id>/`: active job state, inputs, logs, and results
- `archives/<job_id>/`: archived runs created by `archive_run.py`
- `poc_output/`: default output location for the standalone demo

## Proof Artifacts

The proof model depends on which execution shape you use.

Single-host or coordinator-staged runs produce:

- `output/audit.json`: records input hashes, output hashes, execution timing, SecretFlow version, and the exact runner and validator script hashes used for the run
- `output/verification.json`: written by `verify_run.py`; independently recomputes the plaintext intersection from the staged inputs and records whether the produced output matches it exactly

Strict-trust distributed runs produce:

- `party_a_receipt.json`: Party A's local receipt with its own input hash, output hash, session hash, execution metadata, and SecretFlow report counts
- `party_b_receipt.json`: Party B's local receipt with the same structure

`verify_peer_psi_receipts.py` checks that both receipts refer to the same session and agree on the same output hash and row count.

These files still do not create a cryptographic proof for a hostile third party, but they do give each operator a concrete receipt showing what local input they used and what shared output was produced.

## License

This repository is distributed under Apache License 2.0.

## Reference Docs

See [docs/STRICT_TRUST_MODE.md](docs/STRICT_TRUST_MODE.md), [docs/COORDINATOR.md](docs/COORDINATOR.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/SECURITY_CHECKLIST.md](docs/SECURITY_CHECKLIST.md), and [docs/RETENTION.md](docs/RETENTION.md) for the deeper operational material.
