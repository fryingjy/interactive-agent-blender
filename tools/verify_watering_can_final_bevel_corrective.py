"""Independent verifier for the watering can's final bevel correction
(Opening_Rim, Opening_Shadow, Rose_Head).

Deliberately separate from tools/run_watering_can_final_bevel_corrective.py:
opens only the saved output file, never imports or runs the generator.
"""
import hashlib
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from object_ops import hard_surface_shading_audit  # noqa: E402

CORRECTED = ROOT / "runs/2026-08-12_watering-can-final-bevel-corrective/heldout_watering_can_production_fully_corrected.blend"
SPOUT_HANDLE_CORRECTED = ROOT / "runs/2026-08-12_watering-can-secondary-bevel-corrective/heldout_watering_can_production_corrected.blend"
ORIGINAL_PUBLISHED = ROOT / "runs/2026-08-11_heldout-watering-can/production/heldout_watering_can_production.blend"

TARGETS = ["Opening_Rim", "Opening_Shadow", "Rose_Head"]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluated_clean(obj_name):
    obj = bpy.data.objects[obj_name]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    bm.free()
    eval_obj.to_mesh_clear()
    return non_manifold == 0 and degenerate == 0


def main():
    spout_handle_hash_before = sha256(SPOUT_HANDLE_CORRECTED)
    original_hash_before = sha256(ORIGINAL_PUBLISHED)
    bpy.ops.wm.open_mainfile(filepath=str(CORRECTED))
    checks = {
        "spout_handle_source_file_unmodified": sha256(SPOUT_HANDLE_CORRECTED) == spout_handle_hash_before,
        "original_published_file_unmodified": sha256(ORIGINAL_PUBLISHED) == original_hash_before,
        "vessel_weight_bevel_undisturbed": "WEIGHT" in hard_surface_shading_audit("Connected_Vessel")["bevel_limit_methods_present"],
        "spout_correction_undisturbed": hard_surface_shading_audit("Connected_Tapered_Spout")["status"] == "PASS",
        "handle_correction_undisturbed": hard_surface_shading_audit("Arched_Handle")["status"] == "PASS",
    }
    for name in TARGETS:
        audit = hard_surface_shading_audit(name)
        checks[f"{name}_audit_pass"] = audit["status"] == "PASS"
        checks[f"{name}_evaluated_clean"] = evaluated_clean(name)
    passed = all(checks.values())
    print(checks)
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
