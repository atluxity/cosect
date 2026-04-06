# OpenMined Wire Traffic Notes

BLUF: the OpenMined distributed demo uses a much simpler wire format than the SecretFlow path in this repository. The transport is plain TCP carrying length-prefixed JSON messages from our wrapper. The final overlap is visibly returned on the wire in clear JSON. In the canary runs, the unique non-overlap values did not appear in the readable payloads we extracted.

## Test Setup

The first packet capture described here was taken during a distributed OpenMined run with the built-in fixture data:

- Party A: 200 domains
- Party B: 60 domains
- expected intersection: 10 domains

The capture was taken on loopback with `tcpdump` while [distributed_network_poc.py](/home/atluxity/git/cosect/distributed_network_poc.py) was running with `--engine openmined`.

## What Was Visible

The active connection was a plain TCP socket between the two local worker processes.

Unlike the SecretFlow path, the readable payload was our own wrapper protocol rather than a gRPC or SPU runtime layer.

Readable messages included:

- `{"type": "client_request", ...}`
- `{"type": "server_material", ...}`
- `{"type": "intersection_rows", ...}`

The most sensitive readable packet in the fixture run was:

```json
{"type": "intersection_rows", "rows": ["apple.com", "bbc.com", "ebay.com", "nih.gov", "paypal.com", "php.net", "stackoverflow.com", "support.google.com", "uk.com", "who.int"]}
```

So the current OpenMined distributed wrapper clearly sends the final overlap in plain JSON on the wire.

The capture also exposed:

- job and output paths
- session file paths
- party-local input and output paths

## What The Readable Messages Mean

| Message type | Plain-English meaning | What it leaks | What it does not leak |
|---|---|---|---|
| `client_request` | Party B sends the OpenMined PSI request to Party A | row count and the existence of an encoded client request blob | the client list in obvious plaintext |
| `server_material` | Party A returns server setup and response material | server row count and the existence of encoded setup/response blobs | the server list in obvious plaintext |
| `intersection_rows` | Party B sends the final intersection back to Party A | the final overlap values in clear JSON | the unique non-overlap values, at least not in this message |

## What This Capture Shows

- The OpenMined path is genuinely doing peer-to-peer network exchange.
- The transport is simpler and easier to inspect than the SecretFlow path.
- The final overlap is openly visible on the wire in the current non-TLS demo.
- The request and response containers are readable JSON envelopes with encoded cryptographic payload fields.

## What This Capture Does Not Show

- Packet inspection alone does not prove the OpenMined PSI math.
- It does not establish that the encoded `request_b64`, `setup_b64`, or `response_b64` fields contain no recoverable input information beyond the intended protocol design.
- It says nothing about host compromise or local inspection.
- It says nothing about transport confidentiality, because the current demo traffic is not TLS-protected.

## Canary Comparison

Two additional captures were taken with small canary inputs to see whether unique non-overlap values would appear in readable payloads.

Run 1 used:

- Party A only: `a-only-openmined-001.example`
- Party B only: `b-only-openmined-001.example`
- Shared value: `shared-openmined-001.example`

Run 2 used:

- Party A only: `a-only-openmined-002.example`
- Party B only: `b-only-openmined-002.example`
- Shared value: `shared-openmined-002.example`

Observed readable messages from run 1:

```json
{"type": "client_request", "protocol": "OPENMINED_ECDH", "client_row_count": 3, "request_b64": "..."}
{"type": "server_material", "server_row_count": 3, "setup_b64": "...", "response_b64": "..."}
{"type": "intersection_rows", "rows": ["shared-openmined-001.example"]}
```

Observed readable messages from run 2:

```json
{"type": "client_request", "protocol": "OPENMINED_ECDH", "client_row_count": 3, "request_b64": "..."}
{"type": "server_material", "server_row_count": 3, "setup_b64": "...", "response_b64": "..."}
{"type": "intersection_rows", "rows": ["shared-openmined-002.example"]}
```

The unique canaries did not appear in the readable payloads we extracted:

- `a-only-openmined-001.example`
- `b-only-openmined-001.example`
- `a-only-openmined-002.example`
- `b-only-openmined-002.example`

The shared canaries did appear exactly where expected:

- run 1: `shared-openmined-001.example`
- run 2: `shared-openmined-002.example`

## Practical Interpretation

For the current OpenMined demo, the wire picture is:

1. Party B connects directly to Party A over TCP.
2. Party B sends a JSON request envelope carrying an encoded PSI request.
3. Party A returns a JSON response envelope carrying encoded setup and response material.
4. Party B computes the overlap locally.
5. Party B sends the final overlap back to Party A in clear JSON.
6. Both sides write matching output files and receipts.

This is consistent with the current implementation in [openmined_backend.py](/home/atluxity/git/cosect/openmined_backend.py).

## Security Implication

The current non-TLS OpenMined distributed demo is easier to reason about than the SecretFlow wire format, but it is also more openly result-bearing.

The current capture supports these narrower claims:

- full lists were not visible in obvious plaintext in the readable payloads we extracted
- the final overlap was visible in obvious plaintext JSON
- unique non-overlap canaries did not appear in the readable payloads we extracted

It does not support a stronger claim that the encoded PSI blobs are free of any deeper recoverable leakage.
