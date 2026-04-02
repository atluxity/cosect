# Job State

## State Transitions

```text
created
  -> manifest_written
  -> inputs_uploaded
  -> validated
  -> running
  -> completed
  -> verified
  -> archived
```

Any step may move to `failed`.

## Rules

- `run` is not allowed before both inputs and `manifest.json` exist.
- `verify` is not allowed before `audit.json` and both output CSVs exist.
- `archive` is not allowed before `verify` succeeds.

## Failure Handling

If a step fails:

- preserve the run directory
- preserve stderr/stdout logs if available
- keep the job in `failed`
- require explicit operator action before retry

## Retry Policy

For the first networked version:

- allow retry of `validate`
- allow retry of `run`
- allow retry of `verify`
- do not allow changing `job_id`

If inputs are replaced after validation, move the job back to `inputs_uploaded`.
