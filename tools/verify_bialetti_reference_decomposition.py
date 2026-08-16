"""Verify that the Bialetti board has an evidence-bound, blockout-ready decomposition.

This is deliberately reference-only: it does not authorize modeling or replace the
separate human review gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.scene_decomposition import scene_decomposition_from_dict


RUN = ROOT / "runs" / "2026-08-15_reference-gathering-bialetti"
SOURCE = RUN / "scene_decomposition_evidence_bound.json"
OUTPUT = RUN / "scene_decomposition_verification.json"


def main() -> int:
    decomposition = scene_decomposition_from_dict(json.loads(SOURCE.read_text(encoding="utf-8")))
    readiness = decomposition.blockout_readiness()
    artifact = decomposition.to_dict()
    checks = {
        "strict_evidence_bindings": decomposition.require_evidence_bindings,
        "four_primary_components_evidence_bound": len(decomposition.primary_components()) == 4,
        "all_primary_components_supported": all(
            item.evidence_status in {"OBSERVED", "STRONGLY_INFERRED"}
            for item in decomposition.primary_components()
        ),
        "high_impact_claims_have_consequences": all(
            claim.impact != "high" or bool(claim.modeling_consequence)
            for claim in decomposition.claims
        ),
        "unknown_underside_is_preserved": any(
            claim["claim_id"] == "underside-unknown"
            for claim in artifact["unknowns"]
        ),
        "blockout_readiness_from_evidence": readiness["ready_for_blockout"],
        "rejected_primitive_strategy_retained": len(artifact["rejected_strategies"]) == 1,
    }
    report = {
        "schema_version": 1,
        "scope": "agent visual/reference cross-check; not human approval or Blender-model authorization",
        "source": str(SOURCE),
        "contact_sheet": "media/same_object_contact_sheet.png",
        "canonical_decomposition": artifact,
        "readiness": readiness,
        "checks": checks,
        "pass": all(checks.values()),
        "human_gate_unchanged": "PENDING_USER_REVIEW",
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "pass": report["pass"]}, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
