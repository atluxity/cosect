# Strict-Trust Mode

## Goal

Run PSI between two semi-trusted peers without uploading either plaintext CSV to infrastructure controlled by the other party.

## Core Rule

Party A plaintext stays on Party A's host.

Party B plaintext stays on Party B's host.

Only SecretFlow protocol traffic and metadata may cross the network.

## Components

- `run_2party_psi_peer.py`: party-local PSI runner
- `write_peer_psi_session.py`: writes the shared session file
- `verify_peer_psi_receipts.py`: verifies the two party-local receipts agree on the same result
- `strict_network_poc.py`: local two-container demo of the strict-trust model

## Shared Session File

The shared session file contains:

- job id
- protocol
- Party A and Party B network addresses for SecretFlow production mode
- Party A and Party B SPU node addresses
- per-party local input path
- per-party local output path
- per-party local receipt path

This file does not contain plaintext domains.

## Execution Model

1. Party A normalizes and validates only Party A's local CSV.
2. Party B normalizes and validates only Party B's local CSV.
3. Both parties receive the same shared session file.
4. Party A runs `run_2party_psi_peer.py --party party_a --session-file ...`.
5. Party B runs `run_2party_psi_peer.py --party party_b --session-file ...`.
6. SecretFlow runs PSI in production mode across the two hosts.
7. Each party writes its own local output CSV and local receipt.
8. Compare the two receipts with `verify_peer_psi_receipts.py`.

## What The Receipt Proves

Each party-local receipt records:

- the shared session SHA-256
- the local input SHA-256
- the local output SHA-256
- the output row count
- SecretFlow version
- runner and validator script hashes
- SecretFlow-reported counts

`verify_peer_psi_receipts.py` proves:

- both parties used the same session file
- both parties reported the same output hash
- both parties reported the same output row count

## What It Does Not Prove

This mode does not produce a cryptographic attestation against a malicious host.

It proves a stronger operational statement than the coordinator-upload flow:

- no centralized service staged both plaintext CSVs
- each party retained its own plaintext locally
- the two parties reported the same result for the same session

## Local Demo

Run:

```bash
python3 strict_network_poc.py
```

The demo starts two Docker containers:

- Party A container mounts only Party A's plaintext input
- Party B container mounts only Party B's plaintext input
- both mount the shared session file

That is the recommended proof-of-concept shape for semi-trusted peers.
