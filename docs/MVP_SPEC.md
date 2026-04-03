# SecretFlow PSI MVP Spec

## Objective

Build a two-party domain-sharing workflow where both parties learn only the exact overlapping domains, and neither side provides its full customer list to the other in plaintext.

## Parties

- Party A: larger list, usually a few thousand domains
- Party B: smaller list, often around 100 domains

Both parties are semi-trusted peers in the same industry.

## Inputs

Each party provides a local CSV with a single `domain` column after normalization.

## Outputs

Each party receives a local CSV containing only the intersecting `domain` values.

## Protocol

- SecretFlow 2-party PSI
- `key='domain'`
- `broadcast_result=True`
- default starting protocol: `KKRT_PSI_2PC`

`KKRT_PSI_2PC` is the default starting point because the dataset sizes are modest and the goal is a practical MVP, not protocol experimentation.

## Acceptance Criteria

- Both parties can run the workflow on local CSV inputs.
- Neither party transmits a plaintext full customer list to the other.
- Both parties receive the same intersection result.
- The run produces an audit trail with file hashes and row counts.
- The remote workflow can execute across two real party-local runners without a coordinator staging both plaintext inputs.
- The workflow is simple enough to explain to non-cryptographers.

## Deferred Work

- mTLS, pinned TLS, and firewall rules
- anti-abuse controls
- repeated-run policy
- production logging and key management
