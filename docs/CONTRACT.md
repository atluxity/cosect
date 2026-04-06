# Local Contract

## Purpose

This contract defines the local, file-based interface for the PSI MVP, independent of backend.

The input and output file contract should remain stable even if the PSI engine changes.

## Input Files

Each party provides one normalized CSV file with exactly one required column:

```csv
domain
example.com
shared.example
```

Rules:

- header name must be exactly `domain`
- values must already be normalized
- file must be UTF-8 CSV
- duplicate domains are not allowed
- blank rows are not allowed

## Domain Canonicalization

Inputs must follow these rules before PSI:

- lowercase
- trim leading and trailing whitespace
- remove one trailing `.`
- convert IDNs to punycode
- preserve subdomains as distinct values

Examples:

- `Example.COM` -> `example.com`
- `www.Example.com.` -> `www.example.com`
- `münich.example` -> `xn--mnich-kva.example`

## Output Files

The runner writes:

- `party_a_intersection.csv`
- `party_b_intersection.csv`
- `audit.json` for standalone mode, or per-party receipts for distributed mode

Intersection CSV contract:

- one `domain` column
- sorted ascending
- identical content for both parties after the run completes

## Job Identity

Each run has a `job_id`. If not supplied, the runner generates one in UTC:

`psi-YYYYMMDDTHHMMSSZ`

## Validation Requirements

Before PSI runs:

- both input files must satisfy the CSV contract
- row counts must be greater than zero
- both input files must have unique `domain` values

After PSI runs:

- both output CSVs must exist
- both output CSVs must be byte-identical
- audit JSON must exist in standalone mode and record hashes and row counts
- per-party receipts must exist in distributed mode and agree on the same session and result
