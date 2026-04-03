# Coordinator

## Purpose

`coordinator.py` is the first network wrapper around the existing local SecretFlow workflow. It exposes a small HTTP job API and maps each action onto the current scripts and run-directory layout.

This coordinator stores uploaded plaintext CSV files on the coordinator host. That makes it unsuitable for the stricter semi-trusted-peer model where neither side may reveal its full plaintext list to infrastructure controlled by the other party.

Use [STRICT_TRUST_MODE.md](STRICT_TRUST_MODE.md) for that architecture.

## Start

```bash
python3 coordinator.py --host 127.0.0.1 --port 8080
```

With temporary API-key auth enabled:

```bash
python3 coordinator.py \
  --host 127.0.0.1 \
  --port 8080 \
  --admin-api-key admin-demo-key \
  --party-a-api-key party-a-demo-key \
  --party-b-api-key party-b-demo-key
```

Or load keys from environment variables:

```bash
export PSI_COORDINATOR_ADMIN_API_KEY=admin-demo-key
export PSI_COORDINATOR_PARTY_A_API_KEY=party-a-demo-key
export PSI_COORDINATOR_PARTY_B_API_KEY=party-b-demo-key
python3 coordinator.py --host 127.0.0.1 --port 8080
```

## Example Flow

Create a job:

```bash
curl -X POST http://127.0.0.1:8080/jobs \
  -H 'X-API-Key: admin-demo-key' \
  -H 'Content-Type: application/json' \
  -d '{"job_id":"psi-demo-1","protocol":"KKRT_PSI_2PC","party_a_org":"Company A","party_b_org":"Company B"}'
```

Upload the manifest:

```bash
curl -X PUT http://127.0.0.1:8080/jobs/psi-demo-1/manifest \
  -H 'X-API-Key: admin-demo-key' \
  -H 'Content-Type: application/json' \
  --data-binary @MANIFEST_TEMPLATE.json
```

Upload normalized inputs:

```bash
curl -X PUT http://127.0.0.1:8080/jobs/psi-demo-1/inputs/party_a \
  -H 'X-API-Key: admin-demo-key' \
  --data-binary @data/list_a_200_popular_domains.csv
curl -X PUT http://127.0.0.1:8080/jobs/psi-demo-1/inputs/party_b \
  -H 'X-API-Key: admin-demo-key' \
  --data-binary @data/list_b_10_random_from_a.csv
```

Validate, run, verify, and inspect status:

```bash
curl -X POST http://127.0.0.1:8080/jobs/psi-demo-1/validate -H 'X-API-Key: admin-demo-key'
curl -X POST http://127.0.0.1:8080/jobs/psi-demo-1/run -H 'X-API-Key: admin-demo-key'
curl -X POST http://127.0.0.1:8080/jobs/psi-demo-1/verify -H 'X-API-Key: admin-demo-key'
curl http://127.0.0.1:8080/jobs/psi-demo-1 -H 'X-API-Key: admin-demo-key'
```

Download artifacts:

```bash
curl http://127.0.0.1:8080/jobs/psi-demo-1/audit -H 'X-API-Key: admin-demo-key'
curl http://127.0.0.1:8080/jobs/psi-demo-1/results/party_a -H 'X-API-Key: party-a-demo-key'
curl http://127.0.0.1:8080/jobs/psi-demo-1/results/party_b -H 'X-API-Key: party-b-demo-key'
```

After the verify step, inspect `runs/<job_id>/output/verification.json`.

That receipt is written by `verify_run.py` and records:

- manifest SHA-256
- audit SHA-256
- input and output SHA-256 values
- recomputed plaintext intersection row count and SHA-256
- whether the produced output exactly matches the independently recomputed intersection

Archive the run:

```bash
curl -X POST http://127.0.0.1:8080/jobs/psi-demo-1/archive -H 'X-API-Key: admin-demo-key'
```

Apply retention cleanup:

```bash
curl -X POST http://127.0.0.1:8080/admin/cleanup \
  -H 'X-API-Key: admin-demo-key' \
  -H 'Content-Type: application/json' \
  -d '{"keep_mode":"metadata-only","older_than_hours":24}'
```

## Notes

- this service is intentionally synchronous
- it uses the existing scripts and Docker workflow directly
- it is meant for a private network or localhost testing, not public exposure
- API keys are a temporary control for testing; use TLS plus stronger client identity in production
- the verify step produces a concrete receipt, but not a cryptographic attestation against a malicious host
- see `docs/DEPLOYMENT.md` for reverse-proxy and TLS assumptions

## Integration Script

Use `http_integration_test.py` to drive the full flow in order with a fresh job id:

```bash
python3 http_integration_test.py \
  --base-url http://127.0.0.1:8080 \
  --job-id psi-http-demo-1 \
  --party-a data/list_a_200_popular_domains.csv \
  --party-b data/list_b_60_mixed.csv
```
