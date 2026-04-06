# PSI MVP Spec

## BLUF

The acceptance target is:

- exact intersection
- mutual output
- party-local plaintext retention in the remote path
- evidence sufficient for post-run review

Any design that stages both plaintext CSVs on infrastructure controlled by one party is out of scope.

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

## Engines

The repository currently supports:

- `secretflow`
- `openmined`

Current engine defaults:

- `secretflow`: `KKRT_PSI_2PC`
- `openmined`: `OPENMINED_ECDH`

The two engines have different shapes:

- SecretFlow uses a mutual-output distributed PSI flow
- OpenMined uses an asymmetric client/server PSI flow, then sends the final result back so both parties end with the same output file

Protocol experimentation beyond those working defaults is outside the scope of this repo.

## Acceptance Criteria

- Both parties can run the workflow on local CSV inputs.
- Both supported engines can produce the same exact intersection on the built-in fixtures.
- Neither party transmits a plaintext full customer list to the other.
- Both parties receive the same intersection result.
- The run produces an audit trail with file hashes and row counts.
- The remote workflow can execute across two real party-local runners without any centralized service staging both plaintext inputs.
- The workflow is simple enough to explain to non-cryptographers.

## Deferred Work

- mTLS, pinned TLS, and firewall rules
- anti-abuse controls
- repeated-run policy
- production logging and key management
