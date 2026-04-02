# Retention

## Why Retain Anything

Retention exists for three reasons:

- dispute resolution between parties
- debugging failed runs
- auditability of what result was produced

But retained artifacts are sensitive, so retention must be intentional.

## Retention Modes

Use one of these modes:

- `everything`
  - keep run directories and archives intact
- `metadata-only`
  - keep `manifest.json`, `status.json`, and `audit.json`
  - remove uploaded inputs, result CSVs, and logs after the retention window
- `delete-all`
  - remove the whole run directory and old archives after the retention window

## Recommended Defaults

- test/demo environments: `delete-all`
- short review workflows: `metadata-only`
- dispute-heavy workflows: `everything` for a short window only

## Cleanup Helper

Use `cleanup_runs.py` to enforce the retention policy:

```bash
python3 cleanup_runs.py \
  --keep-mode metadata-only \
  --older-than-hours 24
```

## What Metadata-Only Keeps

- `manifest.json`
- `status.json`
- `output/audit.json`

## What Metadata-Only Removes

- `input/`
- result CSVs
- `logs/`
- old archives
