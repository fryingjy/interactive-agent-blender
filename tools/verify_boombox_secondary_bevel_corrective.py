"""Independent verifier for the boombox secondary-part bevel correction.

Deliberately separate from tools/run_boombox_secondary_bevel_corrective.py:
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

CORRECTED = ROOT / "runs/2026-08-12_boombox-secondary-bevel-corrective/heldout_boombox_corrected.blend"
ORIGINAL = ROOT / "runs/2026-08-11_heldout-boombox/final/heldout_boombox.blend"

TARGETS = [
    "Cassette reel", "Cassette reel.001", "Cassette reel.002", "Cassette reel.003",
    "Fascia fastener", "Fascia fastener.001", "Fascia fastener.002", "Fascia fastener.003",
    "Speaker cone L", "Speaker cone R", "Telescoping antenna",
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
    original_hash_before = sha256(ORIGINAL)
    bpy.ops.wm.open_mainfile(filepath=str(ORIGINAL))
    original_object_names = {obj.name for obj in bpy.data.objects}

    bpy.ops.wm.open_mainfile(filepath=str(CORRECTED))
    checks = {"original_source_file_unmodified": sha256(ORIGINAL) == original_hash_before}
    for name in TARGETS:
        audit = hard_surface_shading_audit(name)
        checks[f"{name}_audit_pass"] = audit["status"] == "PASS"
        checks[f"{name}_evaluated_clean"] = evaluated_clean(name)
    # Confirm no object was added or removed -- only the 11 targets' own modifier
    # stacks and weight attributes changed, not the scene's object roster.
    checks["object_roster_unchanged"] = {obj.name for obj in bpy.data.objects} == original_object_names
    passed = all(checks.values())
    print(checks)
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
