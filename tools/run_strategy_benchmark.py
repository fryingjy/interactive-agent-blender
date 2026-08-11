"""Run context-diverse strategy choices with cases kept outside the policy module."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.strategy import ModelingBrief, choose_strategy


CASES = [
    ("mechanical_enclosure", ModelingBrief(shape_family="mechanical", symmetric=True), {"representation": "BOX_MESH", "editing": "NONDESTRUCTIVE_MODIFIERS"}),
    ("organic_shell", ModelingBrief(shape_family="organic", smooth_continuous_surface=True, deformation_expected=True), {"representation": "SUBD_CAGE", "components": "CONTINUOUS_MESH"}),
    ("cable", ModelingBrief(shape_family="organic", follows_path=True), {"representation": "CURVE", "editing": "NONDESTRUCTIVE_MODIFIERS"}),
    ("hinged_lid", ModelingBrief(shape_family="mechanical", independent_motion_or_material=True), {"components": "SEPARATE_COMPONENTS"}),
    ("single_print_shell", ModelingBrief(shape_family="mechanical", watertight_union_required=True), {"components": "CONTINUOUS_MESH"}),
    ("vent_array", ModelingBrief(shape_family="mechanical", repeated_elements=True), {"components": "SEPARATE_COMPONENTS", "editing": "NONDESTRUCTIVE_MODIFIERS"}),
    ("export_bake", ModelingBrief(shape_family="mechanical", destructive_required=True), {"editing": "DESTRUCTIVE_EDIT"}),
    ("tiny_local_defect", ModelingBrief(local_damage_fraction=0.05), {"repair": "PATCH_REGION"}),
    ("failed_unstable_region", ModelingBrief(local_damage_fraction=0.55, failed_repairs=3, modifier_instability=0.8), {"repair": "REBUILD_REGION"}),
    ("smooth_watertight_body", ModelingBrief(shape_family="organic", smooth_continuous_surface=True, watertight_union_required=True), {"representation": "SUBD_CAGE", "components": "CONTINUOUS_MESH"}),
]


def main() -> None:
    records = []
    passed = 0
    for case_id, brief, expected in CASES:
        result = choose_strategy(brief)
        observed = {axis: result[axis]["choice"] for axis in expected}
        ok = observed == expected
        passed += int(ok)
        records.append({"case_id": case_id, "brief": asdict(brief), "expected": expected, "observed": observed, "pass": ok, "full_result": result})
    report = {"benchmark": "strategy_choice_context_cases", "case_count": len(records), "passed": passed, "pass_rate": passed / len(records), "all_pass": passed == len(records), "records": records}
    out = Path("runs/2026-08-10_strategy-choice")
    out.mkdir(parents=True, exist_ok=True)
    (out / "strategy_benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("case_count", "passed", "pass_rate", "all_pass")}, indent=2))


if __name__ == "__main__":
    main()
