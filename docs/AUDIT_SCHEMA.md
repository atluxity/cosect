# Audit Schema

## BLUF

`audit.json` is evidence for the standalone single-host path only.

It records what inputs were used, what output was produced, and what exact runner code generated the artifact. It does not prove anything about remote peer trust boundaries by itself.

For the strict-trust distributed mode, the relevant evidence is the pair of party-local receipts plus the receipt comparison step.

## Standalone Audit

`audit.json` is the minimum audit artifact for each single-host standalone PSI run.

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

This file supports a narrow claim:

- the standalone run used these specific inputs
- it produced this specific output
- the output matched a local plaintext recomputation of the intersection

## Distributed Strict-Trust Mode

The strict-trust distributed mode uses party-local receipts instead of any centralized verification receipt file.

Instead, each party writes its own local receipt and `verify_peer_psi_receipts.py` confirms that both sides:

- used the same session file
- produced the same output SHA-256
- produced the same output row count
