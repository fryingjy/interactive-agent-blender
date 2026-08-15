"""Independent structural verifier for the reference-interpretation lab report.

This verifier reads the serialized artifact only; it does not import the lab or
the policy modules that generated it.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-15_reference-interpretation-contract"
SOURCE = RUN / "reference_interpretation_report.json"
OUTPUT = RUN / "reference_interpretation_verify.json"


def main() -> None:
    report = json.loads(SOURCE.read_text(encoding="utf-8"))
    cases = report["cases"]
    checks = {
        "generator_report_passed": report.get("pass") is True,
        "two_different_object_families_present": len(set(report.get("object_families", []))) == 2,
        "lamp_plan_uses_curve": cases["path_lamp"]["decision"]["operation"] == "create_curve",
        "lamp_plan_is_separate": cases["path_lamp"]["decision"]["operation_params"]["component_policy"] == "SEPARATE_COMPONENTS",
        "panel_plan_uses_box_mesh": cases["control_panel"]["decision"]["operation_params"]["representation"] == "BOX_MESH",
        "weak_panel_claim_was_not_hardened": cases["control_panel"]["derived_brief"]["follows_path"] is False,
        "unknown_claim_ids_are_actionable": cases["unresolved_depth"]["decision"]["operation_params"]["claim_ids"] == ["socket-depth"],
        "conflict_is_explicit": cases["conflicting_supported_claims"]["readiness"]["conflicting_modeling_signals"] == ["follows_path"],
        "technical_preemption_is_preserved": cases["technical_preemption"]["action"] == "LOCALIZE_NON_MANIFOLD_REGION",
        "scope_disclaims_blender_and_heldout_proof": "no Blender" in report.get("scope", "") and "held-out" in report.get("scope", ""),
    }
    result = {
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "independent_from_generator_imports": True,
        "checks": checks,
        "pass": all(checks.values()),
    }
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
