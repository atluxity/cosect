# Network MVP

## Goal

Wrap the existing local SecretFlow workflow in a minimal networked job model without changing the underlying PSI contract.

The network layer should orchestrate:

- job creation
- metadata capture
- normalized input upload
- PSI execution
- result retrieval
- archival

It should not redefine normalization, audit, or output formats.

## Recommended Shape

Use a coordinator-style batch service, not a generic online API.

Each party interacts with one coordinator that stores files under the existing run layout:

- `runs/<job_id>/manifest.json`
- `runs/<job_id>/input/party_a_domains.csv`
- `runs/<job_id>/input/party_b_domains.csv`
- `runs/<job_id>/output/audit.json`
- `runs/<job_id>/output/party_a_intersection.csv`
- `runs/<job_id>/output/party_b_intersection.csv`

The coordinator is only a workflow wrapper around the existing scripts.

## Why This Shape

- keeps the PSI contract stable
- avoids exposing SecretFlow internals directly
- supports audit and archival naturally
- fits a cooperative two-party model better than a public-facing API

## Roles

- `coordinator`: accepts job metadata, stores files, runs the workflow, exposes status and results
- `party_a operator`: uploads Party A normalized input and retrieves Party A result
- `party_b operator`: uploads Party B normalized input and retrieves Party B result

## Lifecycle

1. Create job.
2. Write manifest metadata.
3. Upload Party A normalized CSV.
4. Upload Party B normalized CSV.
5. Validate both inputs.
6. Run PSI.
7. Verify run.
8. Download results.
9. Archive run.

## Minimal Security Model

For the first networked version, assume:

- fixed peer identities
- mutual TLS or pinned TLS later
- IP allowlists later
- no public internet exposure

The first network wrapper should live on a controlled private link or VPN.

## Hard Boundary

The coordinator must not transform data beyond:

- saving uploaded files
- invoking the existing scripts
- returning stored artifacts

Any future change to normalization or file formats must happen in the local workflow first, then flow upward into the network wrapper.
