#!/usr/bin/env python3
"""Compare interpreted carousel specs for conceptual and compositional distinctness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from render_carousel import compare_candidate_specs, load_json, validate_spec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two or more reference-driven carousel specs before full rendering."
    )
    parser.add_argument("specs", nargs="+", help="Two or more carousel JSON specs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if len(args.specs) < 2:
        print(json.dumps({"distinct": False, "errors": ["Provide at least two specs."]}, indent=2))
        return 1
    specs = []
    errors = []
    for raw_path in args.specs:
        path = Path(raw_path).expanduser().resolve()
        try:
            spec = load_json(path)
        except ValueError as exc:
            errors.append(f"{path}: {exc}")
            continue
        validation_errors = validate_spec(spec)
        if validation_errors:
            errors.extend(f"{path}: {message}" for message in validation_errors)
            continue
        if not spec.get("referenceDriven") or not isinstance(spec.get("designManifest"), dict):
            errors.append(f"{path}: candidate comparison requires referenceDriven and designManifest")
            continue
        specs.append(spec)
    if errors:
        print(json.dumps({"distinct": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    result = compare_candidate_specs(specs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["distinct"] else 2


if __name__ == "__main__":
    sys.exit(main())
