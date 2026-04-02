# Threat Model

## Scope

This threat model covers the first coordinator-based SecretFlow PSI MVP in this repository.

It assumes:

- two semi-trusted industry peers
- private network deployment
- no public internet exposure
- exact-domain PSI with mutual output

It does not assume malicious-security at the cryptographic protocol layer.

## Assets

- each party's full normalized domain list
- the overlap result
- `manifest.json`
- `audit.json`
- run logs
- archived run directories

## Main Threats

### Unauthorized Job Access

If an unauthorized client can reach the coordinator, it can create jobs, upload files, trigger runs, or download results.

Current mitigation:

- none in-process

Required external mitigation:

- mTLS or strong reverse-proxy authentication
- private network or VPN
- IP allowlists

### File Upload Abuse

An attacker can try oversized uploads, malformed manifests, or non-CSV inputs.

Current mitigation:

- request body size limits
- strict `job_id` validation
- manifest `job_id` must match path
- CSV upload must begin with `domain` header

### Job Mutation After Execution

An operator or attacker can try to swap inputs or manifests after validation or completion.

Current mitigation:

- coordinator rejects mutation in `running`, `verified`, and `archived`
- changing manifest or inputs clears stale output artifacts before re-run

### Result Leakage

Results, audit files, and logs are sensitive.

Current mitigation:

- none at the HTTP authorization layer

Required external mitigation:

- authenticated access
- party-scoped authorization for result endpoints
- retention and deletion policy

### Denial of Service

Repeated PSI runs or oversized inputs can consume CPU, memory, disk, and Docker capacity.

Current mitigation:

- upload size limits

Still needed:

- concurrency limits
- job quotas
- request rate limits
- execution timeouts

### Guessing and Repeated Probing

Domain names are from a guessable universe. A partner can run repeated PSI jobs to probe for overlap changes.

Current mitigation:

- audit trail

Still needed:

- governance between parties
- explicit run approval
- job frequency limits

## Security Position

This MVP is acceptable for controlled testing between trusted peers on a private network. It is not production-ready without transport security, authentication, authorization, rate limiting, and operational controls.
