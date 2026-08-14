"""Independent verifier for the rounded-part bevel revert.

Deliberately separate from tools/run_revert_incorrect_rounded_part_bevels.py:
opens only the saved output files, never imports or runs the generator.
"""
import hashlib
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))

CAN_CORRECTED = ROOT / "runs/2026-08-12_watering-can-rounded-parts-bevel-reverted/heldout_watering_can_production_rounded_parts_reverted.blend"
CAN_SOURCE = ROOT / "runs/2026-08-12_watering-can-final-bevel-corrective/heldout_watering_can_production_fully_corrected.blend"
CAN_TARGETS = ["Rose_Head", "Connected_Tapered_Spout", "Arched_Handle"]

TELEPHONE_CORRECTED = ROOT / "runs/2026-08-12_telephone-handset-bevel-reverted/heldout_vintage_telephone_production_handset_reverted.blend"
TELEPHONE_SOURCE = ROOT / "runs/2026-08-12_telephone-trim-bevel-corrective/heldout_vintage_telephone_production_trim_corrected.blend"


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


def no_weight_bevel(obj_name):
    obj = bpy.data.objects[obj_name]
    return not any(m.type == "BEVEL" and m.limit_method == "WEIGHT" for m in obj.modifiers)


def main():
    can_source_hash_before = sha256(CAN_SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(CAN_CORRECTED))
    checks = {"can_source_file_unmodified": sha256(CAN_SOURCE) == can_source_hash_before}
    for name in CAN_TARGETS:
        checks[f"{name}_weight_bevel_removed"] = no_weight_bevel(name)
        checks[f"{name}_evaluated_clean"] = evaluated_clean(name)
    checks["vessel_weight_bevel_still_present"] = not no_weight_bevel("Connected_Vessel")

    telephone_source_hash_before = sha256(TELEPHONE_SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(TELEPHONE_CORRECTED))
    checks["telephone_source_file_unmodified"] = sha256(TELEPHONE_SOURCE) == telephone_source_hash_before
    checks["handset_weight_bevel_removed"] = no_weight_bevel("Handset")
    checks["handset_evaluated_clean"] = evaluated_clean("Handset")
    checks["handset_subd_still_present"] = any(m.type == "SUBSURF" for m in bpy.data.objects["Handset"].modifiers)
    checks["housing_weight_bevel_still_present"] = not no_weight_bevel("Main_Housing")

    passed = all(checks.values())
    print(checks)
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
