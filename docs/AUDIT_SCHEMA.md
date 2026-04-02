# Audit Schema

`audit.json` is the minimum audit artifact for each local PSI run.

## Fields

```json
{
  "job_id": "psi-20260331T143023Z",
  "timestamp_utc": "2026-03-31T14:30:28.002395+00:00",
  "protocol": "KKRT_PSI_2PC",
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
  }
}
```

## Required Guarantees

- `job_id` uniquely identifies the run.
- `timestamp_utc` is ISO 8601 UTC.
- `input_sha256` is the SHA-256 of each normalized input CSV.
- `intersection.sha256` is the SHA-256 of the resulting intersection CSV.
- `reports` records the per-party counts returned by SecretFlow.

## Why It Matters

This file is the evidence for the claim that the run used local inputs, produced only the overlap, and did not require plaintext full-list exchange.
