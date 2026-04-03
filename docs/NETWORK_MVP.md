# Network MVP

## Goal

Run SecretFlow PSI between two real hosts without uploading either party's plaintext CSV to any centralized service or the other party.

The network layer should orchestrate:

- job creation
- metadata capture
- session configuration
- PSI execution
- receipt comparison

It should not redefine normalization or file formats.

## Recommended Shape

Use two party-local runners plus an optional metadata-only control plane.

Each party keeps its own normalized CSV locally and runs the same SecretFlow job code on its own host.

The shared session file contains only:

- job id
- protocol
- party network addresses
- per-party local input and output file paths
- per-party receipt file paths
- SPU node addresses

The plaintext CSV stays only on the host that owns it.

## Why This Shape

- keeps the PSI contract stable
- preserves the trust boundary the PSI workflow is supposed to protect
- avoids any centralized service becoming a plaintext data sink
- supports party-local receipts instead of centralized file staging

## Roles

- `party_a runner`: reads Party A local CSV, participates in PSI, writes Party A local result and receipt
- `party_b runner`: reads Party B local CSV, participates in PSI, writes Party B local result and receipt
- `metadata control plane` optional: stores the shared session manifest and the two receipts, but never stores plaintext CSVs

## Lifecycle

1. Create job.
2. Exchange or publish a shared session file with addresses and local file paths.
3. Party A validates only Party A's local normalized CSV.
4. Party B validates only Party B's local normalized CSV.
5. Each party starts `run_2party_psi_peer.py` on its own host.
6. SecretFlow runs PSI across the two parties.
7. Each party writes its own local receipt.
8. Compare the two receipts with `verify_peer_psi_receipts.py`.

## Minimal Security Model

For the first strict-trust networked version, assume:

- fixed peer identities
- TLS between peers
- IP allowlists or VPN
- no public internet exposure

The local demo uses plaintext localhost transport inside one machine for convenience only. Real deployments should configure SecretFlow TLS in the shared session.

## Hard Boundary

No service controlled by one party may receive the other party's plaintext CSV.
