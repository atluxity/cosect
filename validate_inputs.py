#!/usr/bin/env python3
"""Validate normalized CSV inputs for the SecretFlow PSI MVP."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def validate_csv(path: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    seen: set[str] = set()
    row_count = 0

    with path.open(newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if reader.fieldnames != ["domain"]:
            errors.append(f"{path}: expected exactly one header named 'domain'")
            return 0, errors

        for index, row in enumerate(reader, start=2):
            row_count += 1
            domain = row.get("domain", "")
            if domain != domain.strip():
                errors.append(f"{path}:{index}: domain has leading or trailing whitespace")
            if not domain:
                errors.append(f"{path}:{index}: blank domain")
                continue
            if domain.lower() != domain:
                errors.append(f"{path}:{index}: domain is not lowercase")
            if domain.endswith("."):
                errors.append(f"{path}:{index}: domain has trailing dot")
            if domain in seen:
                errors.append(f"{path}:{index}: duplicate domain '{domain}'")
            seen.add(domain)

    if row_count == 0:
        errors.append(f"{path}: file contains no data rows")

    return row_count, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Normalized CSV files to validate")
    args = parser.parse_args()

    all_errors: list[str] = []
    for raw_path in args.paths:
        path = Path(raw_path)
        row_count, errors = validate_csv(path)
        if errors:
            all_errors.extend(errors)
        else:
            print(f"{path}: ok ({row_count} rows)")

    if all_errors:
        for error in all_errors:
            print(error)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
