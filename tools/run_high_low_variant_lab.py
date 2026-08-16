"""Exercise typed, unapplied high/low variant packaging and rollback."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "blender_ops"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from blender_ops import object_ops, persistent_ids  # noqa: E402
from blender_ops.modeler_server import ModelerServer  # noqa: E402

OUT = ROOT / "runs" / "2026-08-15_typed-high-low-variants"


def transact(server, name, action, params, *, commit=True):
    begun = server.cmd_begin_decision(name, action)
    performed = server.cmd_perform_decision(
        begun["decision_id"],
        "package_high_low_variants",
        params,
        command_id=f"{action}-{begun['decision_id']}",
    )
    verified = server.cmd_verify_decision(begun["decision_id"])
    closed = (
        server.cmd_commit_decision(begun["decision_id"])
        if commit
        else server.cmd_reject_decision(begun["decision_id"], reason="rollback control")
    )
    return {"begin": begun, "perform": performed, "verify": verified, "close": closed}


def setup_source(server, name, primitive, dimensions):
    server.cmd_create_primitive(name, primitive, **dimensions)
    object_ops.add_modifier(name, "SUBSURF", "Editable_Subdivision")
    object_ops.set_modifier_parameter(name, "Editable_Subdivision", "levels", 2)
    object_ops.set_modifier_parameter(name, "Editable_Subdivision", "render_levels", 2)
    object_ops.add_modifier(name, "SOLIDIFY", "Editable_Thickness")
    object_ops.set_modifier_parameter(name, "Editable_Thickness", "thickness", 0.08)
    persistent_ids.ensure_persistent_ids(name)
    server.cmd_check_external_edit(name)


def object_record(name):
    obj = bpy.data.objects[name]
    return {
        "name": obj.name,
        "mesh": obj.data.name,
        "collections": sorted(collection.name for collection in obj.users_collection),
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
        "modifiers": [
            {
                "name": modifier.name,
                "type": modifier.type,
                "levels": getattr(modifier, "levels", None),
                "render_levels": getattr(modifier, "render_levels", None),
            }
            for modifier in obj.modifiers
        ],
        "variant": obj.get("production_variant"),
        "hidden": obj.hide_get(),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer()
    capabilities = server.cmd_get_capabilities()

    setup_source(server, "Fixture_HIGH", "cube", {"size": 2.0})
    committed = transact(
        server,
        "Fixture_HIGH",
        "package_committed_editable_variants",
        {
            "low_object_name": "Fixture_LOW",
            "high_collection_name": "HIGH_POLY",
            "low_collection_name": "LOW_POLY",
            "low_subd_levels": 0,
            "hide_low": True,
        },
    )
    committed_high = object_record("Fixture_HIGH")
    committed_low = object_record("Fixture_LOW")

    setup_source(server, "Fixture_Part_HIGH", "cube", {"size": 0.75})
    shared_collections = transact(
        server,
        "Fixture_Part_HIGH",
        "package_second_component_into_shared_variant_collections",
        {
            "low_object_name": "Fixture_Part_LOW",
            "high_collection_name": "HIGH_POLY",
            "low_collection_name": "LOW_POLY",
            "low_subd_levels": 0,
            "hide_low": True,
        },
    )
    shared_high = object_record("Fixture_Part_HIGH")
    shared_low = object_record("Fixture_Part_LOW")

    setup_source(server, "Shared_Rollback_HIGH", "cube", {"size": 0.5})
    shared_rollback_original = object_record("Shared_Rollback_HIGH")
    shared_collection_members_before = {
        "high": sorted(obj.name for obj in bpy.data.collections["HIGH_POLY"].objects),
        "low": sorted(obj.name for obj in bpy.data.collections["LOW_POLY"].objects),
    }
    shared_rollback_meshes_before = set(bpy.data.meshes.keys())
    shared_rejected = transact(
        server,
        "Shared_Rollback_HIGH",
        "package_into_shared_collections_then_reject",
        {
            "low_object_name": "Shared_Rollback_LOW",
            "high_collection_name": "HIGH_POLY",
            "low_collection_name": "LOW_POLY",
            "low_subd_levels": 0,
            "hide_low": True,
        },
        commit=False,
    )
    shared_rollback_after = object_record("Shared_Rollback_HIGH")
    shared_rollback_meshes_after = set(bpy.data.meshes.keys())
    shared_collection_members_after = {
        "high": sorted(obj.name for obj in bpy.data.collections["HIGH_POLY"].objects),
        "low": sorted(obj.name for obj in bpy.data.collections["LOW_POLY"].objects),
    }

    setup_source(
        server,
        "Rollback_HIGH",
        "cylinder",
        {"vertices": 12, "radius": 1.0, "depth": 2.0, "end_fill_type": "NGON"},
    )
    bpy.data.objects["Rollback_HIGH"]["array_property_control"] = [1, 2, 3]
    rollback_original_collections = sorted(
        collection.name for collection in bpy.data.objects["Rollback_HIGH"].users_collection
    )
    meshes_before_rollback = set(bpy.data.meshes.keys())
    revision_before_rollback = server.cmd_get_full_state("Rollback_HIGH")["revision"]
    rejected = transact(
        server,
        "Rollback_HIGH",
        "package_then_reject_variants",
        {
            "low_object_name": "Rollback_LOW",
            "high_collection_name": "ROLLBACK_HIGH_POLY",
            "low_collection_name": "ROLLBACK_LOW_POLY",
            "low_subd_levels": 0,
            "hide_low": False,
        },
        commit=False,
    )
    rollback_after = object_record("Rollback_HIGH")

    invalid_before = {
        "objects": sorted(bpy.data.objects.keys()),
        "collections": sorted(bpy.data.collections.keys()),
        "meshes": sorted(bpy.data.meshes.keys()),
    }
    begun = server.cmd_begin_decision("Rollback_HIGH", "reject_collection_name_collision")
    collision_error = None
    try:
        server.cmd_perform_decision(
            begun["decision_id"],
            "package_high_low_variants",
            {
                "low_object_name": "Collision_LOW",
                "high_collection_name": "HIGH_POLY",
                "low_collection_name": "COLLISION_LOW_POLY",
            },
        )
    except Exception as exc:  # expected control
        collision_error = str(exc)
    abandoned = server.cmd_abandon_decision(begun["decision_id"], reason="expected collision")
    invalid_after = {
        "objects": sorted(bpy.data.objects.keys()),
        "collections": sorted(bpy.data.collections.keys()),
        "meshes": sorted(bpy.data.meshes.keys()),
    }

    checks = {
        "capability_reported": "editable_high_low_variant_packaging" in capabilities["capabilities"],
        "operation_registered": "package_high_low_variants" in capabilities["available_operations"],
        "committed_separate_collections": (
            committed_high["collections"] == ["HIGH_POLY"]
            and committed_low["collections"] == ["LOW_POLY"]
        ),
        "committed_independent_meshes": committed_high["mesh"] != committed_low["mesh"],
        "shared_collections_accept_second_component": (
            shared_high["collections"] == ["HIGH_POLY"]
            and shared_low["collections"] == ["LOW_POLY"]
            and shared_collections["perform"]["result"]["collections_reused"] is True
        ),
        "shared_rejection_preserves_existing_members": shared_collection_members_after == shared_collection_members_before,
        "shared_rejection_removes_low_object": "Shared_Rollback_LOW" not in bpy.data.objects,
        "shared_rejection_restores_source": shared_rollback_after == shared_rollback_original,
        "shared_rejection_removes_mesh_snapshots": shared_rollback_meshes_after == shared_rollback_meshes_before,
        "committed_equal_base_counts": (
            committed_high["vertices"] == committed_low["vertices"]
            and committed_high["faces"] == committed_low["faces"]
        ),
        "committed_modifiers_retained_unapplied": (
            [item["type"] for item in committed_high["modifiers"]] == ["SUBSURF", "SOLIDIFY"]
            and [item["type"] for item in committed_low["modifiers"]] == ["SUBSURF", "SOLIDIFY"]
        ),
        "high_subd_preserved": committed_high["modifiers"][0]["levels"] == 2,
        "low_subd_zero_but_present": committed_low["modifiers"][0]["levels"] == 0,
        "variants_semantically_labeled": (
            committed_high["variant"] == "HIGH_POLY" and committed_low["variant"] == "LOW_POLY"
        ),
        "rollback_removed_created_object": "Rollback_LOW" not in bpy.data.objects,
        "rollback_removed_created_collections": (
            "ROLLBACK_HIGH_POLY" not in bpy.data.collections
            and "ROLLBACK_LOW_POLY" not in bpy.data.collections
        ),
        "rollback_restored_membership": rollback_after["collections"] == rollback_original_collections,
        "rollback_restored_modifiers": [item["type"] for item in rollback_after["modifiers"]] == ["SUBSURF", "SOLIDIFY"],
        "rollback_restored_array_custom_property": list(bpy.data.objects["Rollback_HIGH"]["array_property_control"]) == [1, 2, 3],
        "rollback_removed_snapshot_meshes": set(bpy.data.meshes.keys()) == meshes_before_rollback,
        "rollback_kept_revision": server.cmd_get_full_state("Rollback_HIGH")["revision"] == revision_before_rollback,
        "collision_failed_before_persistent_change": collision_error is not None and invalid_after == invalid_before,
        "collision_failure_auto_rolled_back": abandoned["failed_operation_rolled_back"] is True,
    }
    report = {
        "lab": "typed_editable_high_low_variant_packaging",
        "blender_version": bpy.app.version_string,
        "capabilities": capabilities,
        "committed_transaction": committed,
        "committed_high": committed_high,
        "committed_low": committed_low,
        "shared_collection_transaction": shared_collections,
        "shared_high": shared_high,
        "shared_low": shared_low,
        "shared_rejected_transaction": shared_rejected,
        "shared_rollback_original": shared_rollback_original,
        "shared_rollback_after": shared_rollback_after,
        "shared_collection_members_before": shared_collection_members_before,
        "shared_collection_members_after": shared_collection_members_after,
        "shared_meshes_before": sorted(shared_rollback_meshes_before),
        "shared_meshes_after": sorted(shared_rollback_meshes_after),
        "rejected_transaction": rejected,
        "rollback_after": rollback_after,
        "collision_error": collision_error,
        "collision_abandon": abandoned,
        "checks": checks,
        "pass": all(checks.values()),
        "boundary": (
            "This packages an independent editable duplicate with unapplied modifiers. "
            "It does not perform production retopology, UV authoring, baking, or export."
        ),
    }
    (OUT / "variant_packaging_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "typed_high_low_variants.blend"))
    print(json.dumps({"checks": checks, "pass": report["pass"]}, indent=2))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
