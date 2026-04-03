# SecretFlow PSI POC

This project is for the case where two organizations want to find the customers or domains they have in common, but neither side wants to hand over its full list to the other.

## BLUF

This repository implements a two-party PSI proof of concept for semi-trusted peers.

In the remote setup, each side keeps its own CSV on its own machine. The two sides run the PSI process directly against each other. They do not send their full lists to a shared service, and no central system is allowed to hold both plaintext inputs.

What this repository does prove:

- the parties can compute an exact set intersection with SecretFlow
- the remote flow can run with party-local plaintext only
- both parties can retain receipts that bind the run to a specific session and output

What it does not prove:

- cryptographic attestation against a malicious host
- protection against repeated probing or abusive job frequency
- a production-ready transport and authentication posture by default

Start with [START_HERE.md](START_HERE.md).

If you just want the fastest laptop demo with console output:

```bash
python3 standalone_poc.py --pull
```

## Repository Layout

- `START_HERE.md`: quickest path to a working test
- `README.md`: high-level overview
- `data/`: built-in test fixtures and raw CSV templates
- `docs/`: protocol, proof, and distributed network docs
- `standalone_poc.py`: simplest local demo
- `distributed_network_poc.py`: two-container distributed demo with no centralized plaintext CSV upload
- `run_2party_psi_peer.py`: production-mode party-local PSI runner for real two-host execution
- `write_peer_psi_session.py`: shared session file generator for the distributed flow
- `verify_peer_psi_receipts.py`: compares the two party-local receipts for the same distributed run
- `run_2party_psi.py`: local single-host SecretFlow PSI runner for laptop demos

## Security Model

This codebase assumes:

- two semi-trusted peers
- exact-domain PSI
- mutual output of the intersection
- no plaintext full-list transfer to the other party

The distributed remote mode is the relevant one for that model. The standalone mode is retained as a local validation harness and developer test path.

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

## Entry Points

For a laptop demo:

```bash
python3 standalone_poc.py --pull
```

Use this only for local validation and operator orientation. It is not the remote trust-boundary story.

For the distributed remote model where neither party may upload plaintext CSVs to the other side:

```bash
python3 distributed_network_poc.py
```

That demo starts two separate SecretFlow containers. Each container mounts only its own party's plaintext CSV plus a shared session file. The parties then run SecretFlow in production mode against each other and produce matching receipts.

## Built-In Test Data

- `data/list_a_200_popular_domains.csv`: 200 popular domains
- `data/list_b_10_random_from_a.csv`: 10 guaranteed overlaps against A
- `data/list_b_50_not_in_a.csv`: 50 disjoint domains
- `data/list_b_60_mixed.csv`: 60 domains with exactly 10 overlaps against A

## Runtime Output

- `poc_output/`: default output location for the standalone demo
- `out/distributed_network_poc/<job_id>/`: local demo output for the distributed network mode

## Evidence

The repository emits evidence, not cryptographic proof.

Single-host standalone runs produce:

- `output/audit.json`: input hashes, output hash, execution timing, SecretFlow version, and runner/validator hashes

Distributed runs produce:

- `party_a_receipt.json`: Party A local receipt with input hash, output hash, session hash, execution metadata, and SecretFlow report counts
- `party_b_receipt.json`: Party B local receipt with the same structure

`verify_peer_psi_receipts.py` checks that both receipts refer to the same session and agree on the same output hash and row count.

These artifacts support a narrower claim:

- each operator can show which local input was used
- both operators can show they ran the same session
- both operators can show they observed the same output

## License

This repository is distributed under Apache License 2.0.

## Reference Docs

See [docs/DISTRIBUTED_MODE.md](docs/DISTRIBUTED_MODE.md), [docs/NETWORK_MVP.md](docs/NETWORK_MVP.md), [docs/AUDIT_SCHEMA.md](docs/AUDIT_SCHEMA.md), and [docs/MVP_SPEC.md](docs/MVP_SPEC.md) for the deeper operational material.
