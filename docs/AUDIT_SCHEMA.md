# Audit Schema

`audit.json` is the minimum audit artifact for each local PSI run.

## Fields

```json
{
  "job_id": "psi-20260331T143023Z",
  "timestamp_utc": "2026-03-31T14:30:28.002395+00:00",
  "protocol": "KKRT_PSI_2PC",
  "execution": {
    "started_at_utc": "2026-03-31T14:30:23.102395+00:00",
    "completed_at_utc": "2026-03-31T14:30:28.002395+00:00",
    "duration_seconds": 4.9,
    "python_version": "3.10.12",
    "secretflow_version": "x.y.z",
    "runner_sha256": "...",
    "validator_sha256": "..."
  },
  "reports": [
    {
      "party": "party_a",
      "original_count": 10,
      "intersection_count": 4
    },
    {
      "party": "party_b",
      "original_count": 6,
      "intersection_count": 4
    }
  ],
  "party_a": {
    "input_path": "...",
    "input_rows": 10,
    "input_sha256": "...",
    "output_path": "..."
  },
  "party_b": {
    "input_path": "...",
    "input_rows": 6,
    "input_sha256": "...",
    "output_path": "..."
  },
  "intersection": {
    "rows": 4,
    "sha256": "..."
  },
  "independent_verification": {
    "method": "sorted set intersection over normalized CSV inputs",
    "rows": 4,
    "matches_secretflow_output": true
  }
}
```

## Required Guarantees

- `job_id` uniquely identifies the run.
- `timestamp_utc` is ISO 8601 UTC.
- `input_sha256` is the SHA-256 of each normalized input CSV.
- `intersection.sha256` is the SHA-256 of the resulting intersection CSV.
- `reports` records the per-party counts returned by SecretFlow.
- `execution` binds the audit to the exact runner and validator script content used for the run.
- `independent_verification` records that the result was also checked against a plaintext recomputation of the intersection.

## Why It Matters

This file is the evidence for the claim that the run used local inputs, produced only the overlap, and did not require plaintext full-list exchange.

## Verification Receipt

`verify_run.py` also writes `output/verification.json`.

That receipt independently recomputes the plaintext intersection from the staged inputs and records:

- manifest SHA-256
- audit SHA-256
- input and output SHA-256 values
- recomputed intersection row count and SHA-256
- whether the output matches the independently recomputed intersection
