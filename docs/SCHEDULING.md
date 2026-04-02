# Scheduling

## Purpose

Retention is more reliable if cleanup runs on a schedule instead of waiting for a manual operator action.

Use one of these patterns:

- admin calls `POST /admin/cleanup`
- cron runs `cleanup_runs.py`
- a systemd timer runs `cleanup_runs.py`

## Cron Example

Run cleanup every night at 02:15 and keep metadata only for 24 hours:

```cron
15 2 * * * cd /path/to/repo && /usr/bin/python3 cleanup_runs.py --keep-mode metadata-only --older-than-hours 24
```

## Systemd Timer Idea

Use a one-shot service that runs:

```bash
python3 cleanup_runs.py --keep-mode metadata-only --older-than-hours 24
```

Trigger it daily with a timer.

Example unit files are provided in `systemd/psi-cleanup.service` and `systemd/psi-cleanup.timer`.

## Recommended Start

- test/demo: `delete-all` after 24 hours
- pilot: `metadata-only` after 24 or 72 hours
- only keep `everything` when there is a concrete dispute or audit requirement
