# API Contract

## Scope

This is the first network contract for the coordinator wrapper. It is a job API, not a generic PSI computation API.

## Endpoints

### `POST /jobs`

Create a new job and reserve a `job_id`.

Request:

```json
{
  "job_id": "psi-20260401T090000Z",
  "protocol": "KKRT_PSI_2PC",
  "party_a_org": "Company A",
  "party_b_org": "Company B"
}
```

Response:

```json
{
  "job_id": "psi-20260401T090000Z",
  "status": "created"
}
```

### `PUT /jobs/{job_id}/manifest`

Upload or replace `manifest.json`.

### `PUT /jobs/{job_id}/inputs/party_a`

Upload normalized Party A CSV with header `domain`.

### `PUT /jobs/{job_id}/inputs/party_b`

Upload normalized Party B CSV with header `domain`.

### `POST /jobs/{job_id}/validate`

Run the existing local validation step against both uploaded files.

Response:

```json
{
  "job_id": "psi-20260401T090000Z",
  "status": "validated"
}
```

### `POST /jobs/{job_id}/run`

Execute the existing SecretFlow container workflow.

Response:

```json
{
  "job_id": "psi-20260401T090000Z",
  "status": "running"
}
```

### `POST /jobs/{job_id}/verify`

Run the existing `verify_run.py` step.

### `GET /jobs/{job_id}`

Return job status and artifact presence.

Example response:

```json
{
  "job_id": "psi-20260401T090000Z",
  "status": "verified",
  "artifacts": {
    "manifest": true,
    "party_a_input": true,
    "party_b_input": true,
    "audit": true,
    "party_a_result": true,
    "party_b_result": true
  }
}
```

### `GET /jobs/{job_id}/results/party_a`

Download Party A intersection CSV.

### `GET /jobs/{job_id}/results/party_b`

Download Party B intersection CSV.

### `GET /jobs/{job_id}/audit`

Download `audit.json`.

### `POST /jobs/{job_id}/archive`

Archive the completed run directory.

### `POST /admin/cleanup`

Apply the configured retention policy to old runs and archives.

Request:

```json
{
  "keep_mode": "metadata-only",
  "older_than_hours": 24
}
```

Response:

```json
{
  "status": "cleanup_completed",
  "keep_mode": "metadata-only",
  "older_than_hours": 24
}
```

## Status Model

Allowed statuses:

- `created`
- `manifest_written`
- `inputs_uploaded`
- `validated`
- `running`
- `completed`
- `verified`
- `archived`
- `failed`

## Mapping To Current Scripts

- `PUT /manifest` -> `write_manifest.py` or direct file write
- `POST /validate` -> `validate_inputs.py`
- `POST /run` -> `run_2party_psi.py`
- `POST /verify` -> `verify_run.py`
- `POST /archive` -> `archive_run.py`
- `POST /admin/cleanup` -> `cleanup_runs.py`
