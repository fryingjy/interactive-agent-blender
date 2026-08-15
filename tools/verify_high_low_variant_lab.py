"""Independently verify the saved typed high/low packaging lab."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_typed-high-low-variants"


def collection_names(obj):
    return sorted(collection.name for collection in obj.users_collection)


def modifier_record(obj):
    return [
        {
            "name": modifier.name,
            "type": modifier.type,
            "levels": getattr(modifier, "levels", None),
            "render_levels": getattr(modifier, "render_levels", None),
        }
        for modifier in obj.modifiers
    ]


def evaluated_counts(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return {"vertices": len(mesh.vertices), "faces": len(mesh.polygons)}
    finally:
        evaluated.to_mesh_clear()


def persistent_id_summary(obj):
    point = obj.data.attributes.get("agent_vertex_id")
    face = obj.data.attributes.get("agent_face_id")
    point_values = [item.value for item in point.data] if point else []
    face_values = [item.value for item in face.data] if face else []
    return {
        "point_count": len(point_values),
        "point_unique": len(set(point_values)),
        "point_nonzero": all(value > 0 for value in point_values),
        "face_count": len(face_values),
        "face_unique": len(set(face_values)),
        "face_nonzero": all(value > 0 for value in face_values),
    }


def main():
    report_path = OUT / "variant_packaging_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    high = bpy.data.objects.get("Fixture_HIGH")
    low = bpy.data.objects.get("Fixture_LOW")
    rollback = bpy.data.objects.get("Rollback_HIGH")

    high_modifiers = modifier_record(high) if high else []
    low_modifiers = modifier_record(low) if low else []
    high_evaluated = evaluated_counts(high) if high else {}
    low_evaluated = evaluated_counts(low) if low else {}
    high_ids = persistent_id_summary(high) if high else {}
    low_ids = persistent_id_summary(low) if low else {}

    checks = {
        "generator_report_passed": report.get("pass") is True,
        "expected_objects_present": all(item is not None for item in (high, low, rollback)),
        "rollback_duplicate_absent": bpy.data.objects.get("Rollback_LOW") is None,
        "rollback_collections_absent": (
            bpy.data.collections.get("ROLLBACK_HIGH_POLY") is None
            and bpy.data.collections.get("ROLLBACK_LOW_POLY") is None
        ),
        "separate_variant_collections": (
            high is not None
            and low is not None
            and collection_names(high) == ["HIGH_POLY"]
            and collection_names(low) == ["LOW_POLY"]
        ),
        "independent_mesh_datablocks": high is not None and low is not None and high.data != low.data,
        "equal_editable_base_topology": (
            high is not None
            and low is not None
            and len(high.data.vertices) == len(low.data.vertices)
            and len(high.data.edges) == len(low.data.edges)
            and len(high.data.polygons) == len(low.data.polygons)
        ),
        "modifiers_live_on_both": (
            [item["type"] for item in high_modifiers] == ["SUBSURF", "SOLIDIFY"]
            and [item["type"] for item in low_modifiers] == ["SUBSURF", "SOLIDIFY"]
        ),
        "high_subdivision_two": bool(high_modifiers) and high_modifiers[0]["levels"] == 2,
        "low_subdivision_zero": bool(low_modifiers) and low_modifiers[0]["levels"] == 0,
        "evaluated_geometry_differs_without_apply": (
            bool(high_evaluated)
            and bool(low_evaluated)
            and high_evaluated["vertices"] > low_evaluated["vertices"]
            and high_evaluated["faces"] > low_evaluated["faces"]
        ),
        "semantic_labels_present": (
            high is not None
            and low is not None
            and high.get("production_variant") == "HIGH_POLY"
            and low.get("production_variant") == "LOW_POLY"
        ),
        "persistent_ids_complete": (
            bool(high_ids)
            and bool(low_ids)
            and high_ids["point_count"] == len(high.data.vertices)
            and high_ids["face_count"] == len(high.data.polygons)
            and low_ids["point_count"] == len(low.data.vertices)
            and low_ids["face_count"] == len(low.data.polygons)
            and high_ids["point_unique"] == high_ids["point_count"]
            and high_ids["face_unique"] == high_ids["face_count"]
            and low_ids["point_unique"] == low_ids["point_count"]
            and low_ids["face_unique"] == low_ids["face_count"]
            and high_ids["point_nonzero"]
            and high_ids["face_nonzero"]
            and low_ids["point_nonzero"]
            and low_ids["face_nonzero"]
        ),
    }
    verification = {
        "verification": "fresh_process_saved_blend_inspection",
        "blend_file": bpy.data.filepath,
        "high": {
            "collections": collection_names(high) if high else [],
            "base": {
                "vertices": len(high.data.vertices),
                "edges": len(high.data.edges),
                "faces": len(high.data.polygons),
            }
            if high
            else {},
            "evaluated": high_evaluated,
            "modifiers": high_modifiers,
            "persistent_ids": high_ids,
        },
        "low": {
            "collections": collection_names(low) if low else [],
            "base": {
                "vertices": len(low.data.vertices),
                "edges": len(low.data.edges),
                "faces": len(low.data.polygons),
            }
            if low
            else {},
            "evaluated": low_evaluated,
            "modifiers": low_modifiers,
            "persistent_ids": low_ids,
        },
        "checks": checks,
        "pass": all(checks.values()),
        "boundary": report.get("boundary"),
    }
    (OUT / "independent_verification.json").write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"checks": checks, "pass": verification["pass"]}, indent=2))
    if not verification["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
