# SecretFlow PSI POC

This repository is centered on a SecretFlow-based proof of concept for two organizations that want to learn only the overlap between their domain lists without exchanging full customer lists in plaintext.

Start with [START_HERE.md](START_HERE.md).

If you just want the fastest laptop demo with console output:

```bash
python3 standalone_poc.py --pull
```

## Repository Layout

- `START_HERE.md`: quickest path to a working test
- `README.md`: high-level overview
- `data/`: built-in test fixtures and raw CSV templates
- `docs/`: protocol, proof, and strict-trust network docs
- `standalone_poc.py`: simplest local demo
- `strict_network_poc.py`: two-container strict-trust demo with no centralized plaintext CSV upload
- `run_2party_psi_peer.py`: production-mode party-local PSI runner for real two-host execution
- `write_peer_psi_session.py`: shared session file generator for the strict-trust flow
- `verify_peer_psi_receipts.py`: compares the two party-local receipts for the same distributed run
- `run_2party_psi.py`: local single-host SecretFlow PSI runner for laptop demos

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

## Main Entry Points

For a laptop demo:

```bash
python3 standalone_poc.py --pull
```

For the strict-trust remote model where neither party may upload plaintext CSVs to the other side:

```bash
python3 strict_network_poc.py
```

That demo starts two separate SecretFlow containers. Each container mounts only its own party's plaintext CSV plus a shared session file. The two parties then run SecretFlow in production mode against each other over the network and produce matching receipts.

## Built-In Test Data

- `data/list_a_200_popular_domains.csv`: 200 popular domains
- `data/list_b_10_random_from_a.csv`: 10 guaranteed overlaps against A
- `data/list_b_50_not_in_a.csv`: 50 disjoint domains
- `data/list_b_60_mixed.csv`: 60 domains with exactly 10 overlaps against A

## Runtime Output

- `poc_output/`: default output location for the standalone demo
- `out/strict_network_poc/<job_id>/`: local demo output for the strict-trust network mode

## Proof Artifacts

The proof model depends on which execution shape you use.

Single-host standalone runs produce:

- `output/audit.json`: records input hashes, output hashes, execution timing, SecretFlow version, and the exact runner and validator script hashes used for the run

Strict-trust distributed runs produce:

- `party_a_receipt.json`: Party A's local receipt with its own input hash, output hash, session hash, execution metadata, and SecretFlow report counts
- `party_b_receipt.json`: Party B's local receipt with the same structure

`verify_peer_psi_receipts.py` checks that both receipts refer to the same session and agree on the same output hash and row count.

These files still do not create a cryptographic proof for a hostile third party, but they do give each operator a concrete receipt showing what local input they used and what shared output was produced.

## License

This repository is distributed under Apache License 2.0.

## Reference Docs

See [docs/STRICT_TRUST_MODE.md](docs/STRICT_TRUST_MODE.md), [docs/NETWORK_MVP.md](docs/NETWORK_MVP.md), [docs/AUDIT_SCHEMA.md](docs/AUDIT_SCHEMA.md), and [docs/MVP_SPEC.md](docs/MVP_SPEC.md) for the deeper operational material.
