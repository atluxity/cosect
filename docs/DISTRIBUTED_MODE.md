# Distributed Mode

## BLUF

This is the only remote mode in this repository that is consistent with the stated semi-trusted-peer requirement.

Party A plaintext remains on Party A infrastructure.

Party B plaintext remains on Party B infrastructure.

Only PSI protocol traffic and shared session metadata cross the network.

This mode gives you a concrete record that both parties ran the same session and observed the same output. It does not answer questions about machine integrity or host tampering.

## Trust Boundary

Party A plaintext stays on Party A's host.

Party B plaintext stays on Party B's host.

Only PSI protocol traffic, result-sharing traffic, and session metadata may cross the network.

## Components

- `run_2party_psi_peer.py`: party-local PSI runner
- `write_peer_psi_session.py`: writes the shared session file
- `verify_peer_psi_receipts.py`: verifies the two party-local receipts agree on the same result
- `distributed_network_poc.py`: local two-container demo of the distributed model

## Session File

The shared session file contains:

- job id
- engine
- protocol
- Party A and Party B network addresses for the selected engine
- SPU node addresses when the engine is SecretFlow
- per-party local input path
- per-party local output path
- per-party local receipt path

The session file is metadata only. Plaintext domains are not stored in it.

## Execution Sequence

1. Party A normalizes and validates only Party A's local CSV.
2. Party B normalizes and validates only Party B's local CSV.
3. Both parties receive the same shared session file.
4. Party A runs `run_2party_psi_peer.py --party party_a --session-file ...`.
5. Party B runs `run_2party_psi_peer.py --party party_b --session-file ...`.
6. The selected PSI engine runs across the two hosts.
7. Each party writes its own local output CSV and local receipt.
8. Compare the two receipts with `verify_peer_psi_receipts.py`.

For the OpenMined backend, the distributed demo uses an asymmetric split:

- Party A acts as the OpenMined server
- Party B acts as the OpenMined client
- Party B learns the intersection first
- Party B then sends the final intersection back to Party A so both sides end with the same output file

## Records Produced

Each party-local receipt records:

- the shared session SHA-256
- the local input SHA-256
- the local output SHA-256
- the output row count
- engine-specific version information
- runner and validator script hashes
- engine-reported counts

`verify_peer_psi_receipts.py` confirms:

- both parties used the same session file
- both parties reported the same output hash
- both parties reported the same output row count

## What These Records Support

These records support these statements:

- no centralized service staged both plaintext CSVs
- each side retained its own plaintext locally
- both sides reported the same result for the same session

They are not enough to support stronger claims such as:

- the host runtime was non-malicious
- the operators did not collude
- a hostile third party can verify the result without adding stronger trust anchors

## Local Demo

Run:

```bash
python3 distributed_network_poc.py
```

With `engine=secretflow`, the demo starts two Docker containers:

- Party A container mounts only Party A's plaintext input
- Party B container mounts only Party B's plaintext input
- both mount the shared session file

With `engine=openmined`, the demo starts two local Python worker processes:

- Party A reads only Party A's plaintext input
- Party B reads only Party B's plaintext input
- both read the same session file

That is the recommended proof-of-concept shape for semi-trusted peers in this repository.

At the moment, the working backend is SecretFlow. See [ENGINE_OPTIONS.md](ENGINE_OPTIONS.md) for why that remains the default and which alternative is the most credible pivot target.
