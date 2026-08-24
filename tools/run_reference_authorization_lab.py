"""Exercise the strict reference-authorization boundary inside real Blender."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender_ops.modeler_server import ModelerServer  # noqa: E402


def _args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def _valid_reference_evidence() -> dict:
    target_id = "authorization_lab_prop"
    target_variant = "v1"
    checks = {
        "same_target_identity_pass": True,
        "view_coverage_pass": True,
        "orthographic_coverage_pass": True,
        "provenance_coverage_pass": True,
        "critical_property_coverage_pass": True,
        "dimensional_anchor_pass": True,
        "conflicts_resolved_pass": True,
        "question_driven_research_pass": True,
        "artifact_binding_pass": True,
    }
    return {
        "component_graph_pass": True,
        "measured_ratio_count": 3,
        "uncertainty_recorded": True,
        "reference_set_audit_pass": True,
        "same_target_identity_pass": True,
        "view_coverage_pass": True,
        "critical_property_coverage_pass": True,
        "conflicts_resolved_pass": True,
        "question_driven_research_pass": True,
        "visual_reconstruction_audit_pass": {
            "schema_version": 1,
            "record_type": "VISUAL_RECONSTRUCTION_AUDIT",
            "target_id": target_id,
            "checks": {
                "identity_bound": True,
                "independent_observations": True,
                "property_specific_authority": True,
                "eleven_passes_recorded": True,
                "competing_interpretations_tested": True,
                "bad_interpretation_eliminated": True,
                "construction_bound_to_selected_interpretation": True,
                "uncertainty_kept_reversible": True,
                "every_component_has_construction_justification": True,
            },
            "region_reports": [{"region_id": "body"}],
            "selected_hypothesis_ids": ["connected_box_cage"],
            "contradiction_count": 1,
            "errors": [],
            "pass": True,
        },
        "component_reference_coverage_pass": {
            "schema_version": 1,
            "record_type": "COMPONENT_REFERENCE_COVERAGE",
            "component_count": 1,
            "covered_component_ids": ["body"],
            "uncovered_component_ids": [],
            "pass": True,
        },
        "depth_critical_reference_support_pass": {
            "schema_version": 1,
            "record_type": "DEPTH_CRITICAL_REFERENCE_SUPPORT",
            "depth_critical_component_ids": [],
            "component_reports": {},
            "unsupported_component_ids": [],
            "pass": True,
        },
        "modeling_spec_audit": {
            "schema_version": 1,
            "record_type": "REFERENCE_MODELING_SPEC_AUDIT",
            "target_id": target_id,
            "target_variant": target_variant,
            "component_ids": ["body"],
            "identity_feature_ids": ["outer_silhouette"],
            "authorized_reference_sha256": ["a" * 64],
            "errors": [],
            "pass": True,
        },
        "reference_audit": {
            "schema_version": 1,
            "record_type": "REFERENCE_SET_AUDIT",
            "target_id": target_id,
            "target_variant": target_variant,
            "reference_count": 2,
            "matching_reference_count": 2,
            "checks": checks,
            "issues": [],
            "pass": True,
            "disposition": "READY_TO_MODEL",
            "authorized_reference_sha256": ["a" * 64],
        },
    }


def _expect_failure(label: str, operation, results: list[dict]) -> None:
    try:
        operation()
    except Exception as exc:  # Blender exposes several exception types across versions.
        results.append({"check": label, "pass": True, "error": str(exc)})
    else:
        results.append({"check": label, "pass": False, "error": "operation unexpectedly succeeded"})


def main() -> int:
    args = _args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    server = ModelerServer(enforce_reference_authorization=True)
    results: list[dict] = []

    _expect_failure(
        "construction_before_authorization_is_blocked",
        lambda: server.cmd_create_primitive("Premature", "cube"),
        results,
    )
    _expect_failure(
        "malformed_authorization_is_blocked",
        lambda: server.cmd_authorize_reference_modeling({"reference_audit": {"pass": True}}),
        results,
    )

    authorization = server.cmd_authorize_reference_modeling(_valid_reference_evidence())
    results.append({"check": "structured_authorization_passes", "pass": authorization["authorized"] is True})
    server.cmd_create_primitive("AuthorizedBody", "cube")
    body = bpy.data.objects["AuthorizedBody"]
    state = server.cmd_get_reference_authorization()["authorization"]
    binding_ok = all(
        body.get(key) == state[state_key]
        for key, state_key in (
            ("reference_target_id", "target_id"),
            ("reference_target_variant", "target_variant"),
            ("reference_authorization_sha256", "evidence_sha256"),
        )
    )
    results.append({"check": "created_object_is_hash_bound", "pass": binding_ok})

    bpy.ops.mesh.primitive_cube_add()
    unbound = bpy.context.active_object
    unbound.name = "ManualUnbound"
    _expect_failure(
        "unbound_existing_object_mutation_is_blocked",
        lambda: server.cmd_begin_decision(unbound.name, "MOVE_VERTEX"),
        results,
    )
    server.cmd_bind_existing_object_to_reference(unbound.name)
    begun = server.cmd_begin_decision(unbound.name, "MOVE_VERTEX")
    _expect_failure(
        "authorization_cannot_change_during_pending_decision",
        lambda: server.cmd_authorize_reference_modeling(_valid_reference_evidence()),
        results,
    )
    server.cmd_abandon_decision(begun["decision_id"], "authorization lab")
    results.append({"check": "explicit_binding_enables_transaction", "pass": True})

    packaged = server.cmd_begin_decision("AuthorizedBody", "PACKAGE_HIGH_LOW")
    server.cmd_perform_decision(
        packaged["decision_id"],
        "package_high_low_variants",
        {"low_object_name": "AuthorizedBody_LOW", "hide_low": False},
    )
    server.cmd_verify_decision(packaged["decision_id"])
    committed = server.cmd_commit_decision(packaged["decision_id"])
    low = bpy.data.objects["AuthorizedBody_LOW"]
    derived_binding_ok = (
        "AuthorizedBody_LOW" in committed["authorized_created_objects"]
        and low.get("reference_authorization_sha256") == state["evidence_sha256"]
    )
    results.append({"check": "transaction_created_object_inherits_binding", "pass": derived_binding_ok})

    _expect_failure("global_undo_is_blocked", server.cmd_undo, results)
    _expect_failure(
        "full_scene_restore_is_blocked",
        lambda: server.cmd_restore_checkpoint("does-not-matter.blend"),
        results,
    )

    region = server.cmd_create_region("AuthorizedBody", "body", "PRIMARY", face_ids=[])
    results.append({"check": "bound_semantic_region_write_passes", "pass": region["region_id"] == "body"})
    _expect_failure(
        "unbound_semantic_region_write_is_blocked",
        lambda: server.cmd_create_region("NotPresent", "body", "PRIMARY", face_ids=[]),
        results,
    )

    report = {
        "schema_version": 1,
        "record_type": "REFERENCE_AUTHORIZATION_LAB",
        "blender_version": bpy.app.version_string,
        "checks": results,
        "pass": all(item["pass"] for item in results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
