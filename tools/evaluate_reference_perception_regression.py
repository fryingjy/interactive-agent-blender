"""Evaluate a perception-lab report against the immutable per-metric anchor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def resolve_path(payload: dict[str, Any], dotted: str) -> Any:
    value: Any = payload
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"report does not contain metric path: {dotted}")
        value = value[part]
    return value


def evaluate(anchor: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    if anchor.get("record_type") != "REFERENCE_PERCEPTION_REGRESSION_ANCHOR":
        raise ValueError("wrong regression anchor type")
    if report.get("record_type") != "REFERENCE_PERCEPTION_VALIDATION_LAB":
        raise ValueError("wrong perception report type")
    results = []
    for rule in anchor.get("rules", []):
        value = resolve_path(report, rule["path"])
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"regression metric is not numeric: {rule['path']}")
        operator = rule["operator"]
        threshold = float(rule["threshold"])
        passed = float(value) >= threshold if operator == "min" else float(value) <= threshold if operator == "max" else None
        if passed is None:
            raise ValueError(f"unsupported regression operator: {operator}")
        results.append({**rule, "actual": float(value), "pass": passed})
    return {
        "schema_version": 1,
        "record_type": "REFERENCE_PERCEPTION_REGRESSION_RESULT",
        "anchor_frozen_at": anchor.get("frozen_at"),
        "results": results,
        "pass": bool(results) and all(item["pass"] for item in results),
        "claim_boundary": "This strict anchor protects the controlled perception fixture only; it is not a held-out real-photo or modeling-quality benchmark.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(
        json.loads(args.anchor.read_text(encoding="utf-8")),
        json.loads(args.report.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
