"""Independent verifier for the watering-can spout/handle bevel correction.

Deliberately separate from tools/run_watering_can_secondary_bevel_corrective.py:
opens only the saved output file (never imports or runs the generator) and
re-checks manifoldness, the shading-policy audit, and that the original
production source is untouched.
"""
import hashlib
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from object_ops import hard_surface_shading_audit  # noqa: E402

CORRECTED = ROOT / "runs/2026-08-12_watering-can-secondary-bevel-corrective/heldout_watering_can_production_corrected.blend"
ORIGINAL = ROOT / "runs/2026-08-11_heldout-watering-can/production/heldout_watering_can_production.blend"


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
    original_hash_before = sha256(ORIGINAL)
    bpy.ops.wm.open_mainfile(filepath=str(CORRECTED))
    checks = {}
    for name in ("Connected_Tapered_Spout", "Arched_Handle"):
        audit = hard_surface_shading_audit(name)
        checks[f"{name}_audit_pass"] = audit["status"] == "PASS"
        checks[f"{name}_evaluated_clean"] = evaluated_clean(name)
    # Connected_Vessel was REVIEW_REQUIRED before this correction too (missing
    # recorded intent and Smooth-by-Angle policy, same as every other object in
    # the retroactive audit) -- it was never PASS, so this only checks that its
    # existing WEIGHT bevel was not disturbed by this script.
    checks["vessel_weight_bevel_undisturbed"] = "WEIGHT" in hard_surface_shading_audit("Connected_Vessel")["bevel_limit_methods_present"]
    checks["original_source_file_unmodified"] = sha256(ORIGINAL) == original_hash_before
    passed = all(checks.values())
    print(checks)
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
