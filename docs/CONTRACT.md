# Local Contract

## Purpose

This contract defines the local, file-based interface for the SecretFlow PSI MVP. It must remain stable before any network wrapper is built.

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
- `audit.json`

Intersection CSV contract:

- one `domain` column
- sorted ascending
- identical content for both parties in the local MVP

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
- audit JSON must exist and record hashes and row counts
