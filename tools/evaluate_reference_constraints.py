#!/usr/bin/env python3
"""Evaluate a compact local reference-constraint contract against observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from knowledge_engine.reference_constraints import evaluate_reference_constraints


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("observed", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate_reference_constraints(
        json.loads(args.contract.read_text(encoding="utf-8")),
        json.loads(args.observed.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "blocking": report["blocking_constraint_ids"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
