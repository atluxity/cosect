# Deployment

## Positioning

Do not expose `coordinator.py` directly to the public internet.

Recommended shape:

- coordinator listens on localhost or a private interface
- a reverse proxy terminates TLS in front of it
- client identity is enforced at the reverse proxy or via mTLS

## Temporary Deployment

For a private test environment:

1. Run the coordinator on `127.0.0.1` or a private subnet.
2. Load API keys from environment variables.
3. Put nginx, Caddy, or another reverse proxy in front of it.
4. Restrict inbound access by firewall or VPN.

Example environment variables:

```bash
export PSI_COORDINATOR_ADMIN_API_KEY='replace-admin-key'
export PSI_COORDINATOR_PARTY_A_API_KEY='replace-party-a-key'
export PSI_COORDINATOR_PARTY_B_API_KEY='replace-party-b-key'
```

An example env file is provided at `.env.example`.

Start the coordinator:

```bash
python3 coordinator.py --env-file .env
```

Systemd unit examples are provided under `systemd/`.

## Reverse Proxy Expectations

The reverse proxy should:

- terminate TLS
- optionally enforce client certs or upstream auth
- cap request body size
- forward only the needed path prefixes
- preserve `X-API-Key` only from trusted clients
- log request metadata, not uploaded domain lists

A minimal Caddy example is provided in `CADDYFILE.example`.
A minimal nginx example is provided in `nginx.conf.example`.

## Runtime Controls

The coordinator now supports:

- env-based API keys
- validate timeout
- run timeout
- verify timeout
- archive timeout
- single-run concurrency guard
- configurable generous rate limiting
- admin-triggered cleanup endpoint

Override defaults if needed:

```bash
python3 coordinator.py \
  --host 127.0.0.1 \
  --port 8080 \
  --run-timeout-seconds 600 \
  --rate-limit-window-seconds 60 \
  --rate-limit-max-requests 300
```

## Production Direction

For production, replace API keys with stronger identity:

- mTLS between peers and proxy
- per-party authorization at the proxy or application layer
- explicit retention and deletion policy for runs and archives

For operations, schedule retention cleanup with cron or systemd, or call the admin cleanup endpoint from a trusted control path.
