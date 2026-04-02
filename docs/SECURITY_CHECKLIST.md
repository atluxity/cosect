# Security Checklist

Use this checklist before moving beyond localhost or private demo use.

## Transport

- terminate TLS in front of the coordinator
- require mTLS or equivalent strong client identity
- restrict exposure to private network paths only

## Authentication And Authorization

- require authenticated callers for all endpoints
- restrict result access per party
- restrict archive and run actions to approved operators
- if using temporary API keys, keep separate admin and party keys
- treat API keys as transitional controls, not final production auth

## Input Handling

- keep request size limits enabled
- reject malformed manifests
- reject malformed CSVs before writing to disk when possible
- enforce stable normalization rules

## State Integrity

- keep jobs immutable after `running`
- require explicit re-validation if inputs or manifest change
- do not allow archive before verify

## Logging And Retention

- avoid logging raw uploaded input bodies
- define archive retention windows
- define deletion workflow for completed runs
- protect `audit.json`, result CSVs, and archives

## Operational Controls

- add per-peer job quotas
- add request rate limiting
- add execution timeouts
- monitor Docker failures and disk usage

## Governance

- require run approval from both parties
- document acceptable use of repeated PSI runs
- document escalation if a partner probes abusively
