#!/usr/bin/env python3
"""Normalize domain CSVs for SecretFlow PSI.

Input CSV must contain a `domain` column.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def normalize_domain(value: str) -> str:
    domain = value.strip().lower()
    if not domain:
        return ""
    if domain.endswith("."):
        domain = domain[:-1]
    return domain.encode("idna").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Source CSV with a domain column")
    parser.add_argument("--output", required=True, help="Normalized output CSV")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    rows: list[dict[str, str]] = []

    with input_path.open(newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if "domain" not in (reader.fieldnames or []):
            raise SystemExit("Input CSV must contain a 'domain' column")

        for row in reader:
            normalized = normalize_domain(row["domain"])
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            rows.append({"domain": normalized})

    rows.sort(key=lambda row: row["domain"])

    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=["domain"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} normalized domains to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
