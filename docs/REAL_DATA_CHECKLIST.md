# Real Data Checklist

Use this checklist before the first non-sample PSI run.

## Business Agreement

- both parties agree on the purpose of the run
- both parties agree that only normalized domains are used
- both parties agree on the job id and execution date
- both parties agree that the result is the exact overlap only

## Data Preparation

- export domains from the source system to CSV
- keep one column only: `domain`
- remove internal notes, account ids, tags, or timestamps
- normalize with `normalize_domains.py`
- validate with `validate_inputs.py`

## Canonicalization Decisions

Confirm these choices before running:

- `example.com` and `www.example.com` are treated as different values
- subdomains are preserved
- IDNs are converted to punycode
- trailing dots are removed
- duplicates are removed

## Local Audit

Each party records:

- job id
- source export date
- normalized input row count
- normalized input SHA-256
- result row count
- result SHA-256

## Dry Run

Before using live customer data:

- run the workflow once with non-sensitive test data
- confirm both sides get the same intersection CSV
- confirm `audit.json` is produced for standalone mode, or party-local receipts are produced for distributed mode

## First Real Run

- create a dedicated run directory
- place each party input under that run directory
- run the containerized PSI command
- archive the run directory after completion
