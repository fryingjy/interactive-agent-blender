"""Independent verifier for the telephone trim bevel correction.

Deliberately separate from tools/run_telephone_trim_bevel_corrective.py:
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

CORRECTED = ROOT / "runs/2026-08-12_telephone-trim-bevel-corrective/heldout_vintage_telephone_production_trim_corrected.blend"
HANDSET_CORRECTED = ROOT / "runs/2026-08-12_telephone-handset-bevel-corrective/heldout_vintage_telephone_production_corrected.blend"
ORIGINAL_PUBLISHED = ROOT / "runs/2026-08-11_heldout-vintage-telephone/production/heldout_vintage_telephone_production.blend"

TARGETS = ["Clock_Face", "Lower_Panel_Trim", "Upper_Face_Trim", "Dial_Aperture"] + [
    f"Dial_Aperture_{i:02d}" for i in range(1, 12)
]


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
    handset_hash_before = sha256(HANDSET_CORRECTED)
    original_hash_before = sha256(ORIGINAL_PUBLISHED)
    bpy.ops.wm.open_mainfile(filepath=str(CORRECTED))
    checks = {
        "handset_source_file_unmodified": sha256(HANDSET_CORRECTED) == handset_hash_before,
        "original_published_file_unmodified": sha256(ORIGINAL_PUBLISHED) == original_hash_before,
        "housing_weight_bevel_undisturbed": "WEIGHT" in hard_surface_shading_audit("Main_Housing")["bevel_limit_methods_present"],
        "handset_correction_undisturbed": hard_surface_shading_audit("Handset")["status"] == "PASS",
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
