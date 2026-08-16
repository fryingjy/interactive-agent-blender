"""Fresh-process verifier for the current Blender hard-surface shading policy lab."""
from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-12_hard-surface-shading-policy"


def main() -> None:
    auto = bpy.data.objects.get("Shade_Auto_Smooth_Current_UI_Box")
    semantic = bpy.data.objects.get("Semantic_Hard_Surface_Box")
    auto_modifiers = list(auto.modifiers) if auto else []
    semantic_types = [modifier.type for modifier in semantic.modifiers] if semantic else []
    checks = {
        "auto_smooth_fixture_exists": auto is not None,
        "auto_smooth_modifier_is_live_nodes_last": (
            bool(auto_modifiers)
            and auto_modifiers[-1].type == "NODES"
            and auto_modifiers[-1].show_viewport
            and auto_modifiers[-1].show_render
            and "smooth by angle" in auto_modifiers[-1].name.casefold()
        ),
        "auto_smooth_fixture_faces_are_smooth": bool(auto) and all(poly.use_smooth for poly in auto.data.polygons),
        "semantic_weighted_bevel_precedes_subsurf": semantic_types[:2] == ["BEVEL", "SUBSURF"],
        "semantic_weight_attribute_exists": bool(semantic) and "bevel_weight_edge" in semantic.data.attributes,
    }
    result = {
        "blender_version": bpy.app.version_string,
        "pass": all(checks.values()),
        "checks": checks,
        "boundary": "Confirms live Blender data and modifier ordering only; it does not judge whether a particular reference calls for a sharp edge or a bevel.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fresh_source_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
