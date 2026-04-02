# MVP Runbook

## Operating Model

Party A and Party B each prepare their own local `domain` CSV. Neither side sends the raw CSV to the other. Both sides run the same PSI job configuration and receive only the intersection result.

## Workflow

1. Export raw domains from the local source system.
2. Normalize the CSV with `normalize_domains.py`.
3. Validate the normalized CSVs with `validate_inputs.py`.
4. Record the SHA-256 of the normalized file and the row count.
5. Write `manifest.json` for the job.
6. Run `run_2party_psi.py`.
7. Record the output file SHA-256 and intersection count.
8. Review the resulting intersection CSV.
9. Run `verify_run.py`.
10. Archive the completed run directory.

## Audit Fields

Capture these values for each run:

- job id
- timestamp
- party name
- normalized input path
- normalized input row count
- normalized input SHA-256
- output path
- output row count
- output SHA-256
- manifest path

## Trust Statement

This MVP supports the statement: neither party transmitted its full customer list to the other in plaintext. Each party supplied only its own local input into the PSI protocol and received only the overlap.

## Known Limits

- SecretFlow PSI is generally documented in the semi-honest model.
- Domains are from a guessable universe, so repeated probing and abusive usage still matter operationally.
- This MVP proves the workflow, not the final production deployment.

## Sequence Discipline

Do not build transport or remote orchestration until the local file contract, normalization rules, and audit output are accepted by both parties. Local correctness comes first.
