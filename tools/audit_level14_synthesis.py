"""Audit the Level 14 synthesis against its 20 authoritative knowledge-item files.

The audit checks corpus identity, item counts, minimum schema, source ranges,
duplicate records, and the three count discrepancies found during takeover.
It does not use the prose synthesis as the source of item truth.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_level14-synthesis-audit"
RUN_SLUGS = (
    "blenderbros-subd-hardsurface",
    "blenderbros-subd-hardsurface-2",
    "blenderbros-subd-hive-controller",
    "blenderbros-tertiary-details",
    "blenderbros-decals-workflow",
    "blenderbros-curvy-organic",
    "blenderbros-5-best-tricks",
    "cgcookie-hardsurface-intro",
    "cgvoice-amateur-mistakes",
    "crnt-boolean-triangle",
    "elementza-clean-topology",
    "grant-abbitt-beginners",
    "gnomon-bryant-momo-koshu",
    "jl-mussi",
    "jl-mussi-5-tips",
    "jl-mussi-easy-once-you-learn",
    "mcglasham-subd",
    "pzthree-retopology",
    "rileyb3d-advanced-hardsurface",
    "subd-3dprint",
)
SYNTHESIS_CLAIMED_COUNTS = {
    "blenderbros-subd-hardsurface": 6,
    "blenderbros-subd-hardsurface-2": 4,
    "blenderbros-subd-hive-controller": 5,
    "blenderbros-tertiary-details": 5,
    "blenderbros-decals-workflow": 3,
    "blenderbros-curvy-organic": 7,
    "blenderbros-5-best-tricks": 5,
    "cgcookie-hardsurface-intro": 1,
    "cgvoice-amateur-mistakes": 5,
    "crnt-boolean-triangle": 2,
    "elementza-clean-topology": 4,
    "grant-abbitt-beginners": 1,
    "gnomon-bryant-momo-koshu": 6,
    "jl-mussi": 5,
    "jl-mussi-5-tips": 5,
    "jl-mussi-easy-once-you-learn": 5,
    "mcglasham-subd": 5,
    "pzthree-retopology": 5,
    "rileyb3d-advanced-hardsurface": 5,
    "subd-3dprint": 3,
}
ALLOWED_TYPES = {"PRINCIPLE", "PROCEDURE", "DECISION", "FAILURE", "VISUAL_CUE"}
REQUIRED_FIELDS = {
    "knowledge_type",
    "claim",
    "source",
    "confidence",
    "supporting_evidence",
    "status",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    runs: dict[str, dict] = {}
    schema_errors: list[str] = []
    fingerprints: list[tuple] = []
    type_counts: Counter[str] = Counter()

    for slug in RUN_SLUGS:
        run_dir = ROOT / "runs" / f"2026-08-14_video-study-{slug}"
        source_path = run_dir / "knowledge_items.json"
        if not source_path.is_file():
            schema_errors.append(f"missing knowledge_items.json: {slug}")
            continue
        items = json.loads(source_path.read_text(encoding="utf-8"))
        if not isinstance(items, list):
            schema_errors.append(f"top-level value is not a list: {slug}")
            continue
        for index, item in enumerate(items):
            label = f"{slug}[{index}]"
            missing = sorted(REQUIRED_FIELDS - set(item))
            if missing:
                schema_errors.append(f"{label} missing fields {missing}")
                continue
            if item["knowledge_type"] not in ALLOWED_TYPES:
                schema_errors.append(f"{label} invalid knowledge_type {item['knowledge_type']!r}")
            if not isinstance(item["claim"], str) or not item["claim"].strip():
                schema_errors.append(f"{label} has empty claim")
            if not isinstance(item["supporting_evidence"], str) or not item["supporting_evidence"].strip():
                schema_errors.append(f"{label} has empty supporting_evidence")
            confidence = item["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                schema_errors.append(f"{label} confidence is outside [0, 1]")
            source = item["source"]
            if not isinstance(source, dict) or not source.get("source_id"):
                schema_errors.append(f"{label} has invalid source")
                continue
            start = source.get("start_seconds")
            end = source.get("end_seconds")
            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or start < 0 or end < start:
                schema_errors.append(f"{label} has invalid source time range")
            fingerprints.append((source.get("source_id"), start, end, item["claim"].strip()))
            type_counts[item["knowledge_type"]] += 1
        runs[slug] = {
            "path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256(source_path),
            "actual_count": len(items),
            "synthesis_claimed_count": SYNTHESIS_CLAIMED_COUNTS[slug],
            "count_delta": len(items) - SYNTHESIS_CLAIMED_COUNTS[slug],
            "brief_md_present": (run_dir / "brief.md").is_file(),
        }

    duplicate_count = len(fingerprints) - len(set(fingerprints))
    actual_total = sum(item["actual_count"] for item in runs.values())
    claimed_total = sum(SYNTHESIS_CLAIMED_COUNTS.values())
    mismatches = {
        slug: item
        for slug, item in runs.items()
        if item["actual_count"] != item["synthesis_claimed_count"]
    }
    omitted_item_reconciliation = {
        "blenderbros-subd-hive-controller[5]": {
            "stage_effect": "blockout decision",
            "finding": "Already discussed in the prose; count was understated only.",
        },
        "jl-mussi-easy-once-you-learn[5]": {
            "stage_effect": "representation choice",
            "finding": "Previously absent from that section; explicitly favors a separate Solidify/SubD panel over carving one continuous curved shell.",
        },
        "rileyb3d-advanced-hardsurface[5]": {
            "stage_effect": "topology and surface acceptance",
            "finding": "Already discussed in the prose; count was understated only.",
        },
    }
    assertions = {
        "all_20_declared_run_directories_loaded": len(runs) == 20,
        "corpus_contains_90_items": actual_total == 90,
        "prior_synthesis_claimed_87_items": claimed_total == 87,
        "exactly_three_run_count_mismatches": set(mismatches) == {
            "blenderbros-subd-hive-controller",
            "jl-mussi-easy-once-you-learn",
            "rileyb3d-advanced-hardsurface",
        },
        "each_mismatch_is_plus_one": all(item["count_delta"] == 1 for item in mismatches.values()),
        "all_items_pass_minimum_schema": not schema_errors,
        "no_exact_duplicate_records": duplicate_count == 0,
        "no_brief_md_files_exist_in_batch": not any(item["brief_md_present"] for item in runs.values()),
        "all_allowed_knowledge_types_are_represented": set(type_counts) == ALLOWED_TYPES,
    }
    report = {
        "audit": "Level 14 synthesis against authoritative knowledge_items.json corpus",
        "synthesis_path": "runs/2026-08-15_synthesis-level14-professional-judgment/synthesis.md",
        "synthesis_sha256_at_audit": _sha256(
            ROOT / "runs" / "2026-08-15_synthesis-level14-professional-judgment" / "synthesis.md"
        ),
        "actual_total": actual_total,
        "prior_claimed_total": claimed_total,
        "type_counts": dict(sorted(type_counts.items())),
        "runs": runs,
        "count_mismatches": mismatches,
        "schema_errors": schema_errors,
        "exact_duplicate_record_count": duplicate_count,
        "omitted_item_reconciliation": omitted_item_reconciliation,
        "verdict_effect": {
            "reference_interpretation": "Still thin: none of the three reconciled items interprets an ambiguous visible cue into a target-specific geometric decision.",
            "blockout_decision": "Still moderate; the sixth hive-controller item was already discussed despite the count typo.",
            "representation_choice": "Still moderate but stronger: coverage is eight candidate items, with the separate-panel decision added as a second explicit alternative-based construction choice.",
            "strong_stages": "Unchanged; the Riley visual-cue item was already discussed despite the count typo.",
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "level14_synthesis_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "session_report.md").write_text(
        "# Level 14 synthesis corpus audit\n\n"
        f"Result: **{'PASS' if report['pass'] else 'FAIL'}** "
        f"({sum(assertions.values())}/{len(assertions)} assertions).\n\n"
        "The 20 authoritative `knowledge_items.json` files contain **90 items**, not 87. "
        "Three source runs were understated by one item each. Two omitted items were already "
        "discussed in the synthesis despite the count typo; the third adds an explicit "
        "continuous-vs-separate panel construction decision to representation-choice coverage. "
        "The overall strong/moderate/thin verdict remains, but representation choice is stronger "
        "than the original text reported.\n\n"
        "This audit verifies corpus identity, count, minimum schema, source ranges, duplicate "
        "absence, and the impact of the three reconciled items. It does not re-watch source videos "
        "or independently validate every extracted claim against frames/audio.\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(OUT), "actual_total": actual_total, "mismatches": list(mismatches), "assertions": assertions, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
