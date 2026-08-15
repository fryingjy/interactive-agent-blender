"""Independent saved-scene verification for scoped Shrinkwrap Project transfer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy

NAMES = ("A_Sphere_Scoped", "B_Sphere_Unscoped", "C_Sphere_WrongDirection", "D_Cylinder_Scoped_Transfer")


def evaluated_health(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {"vertices": len(bm.verts), "faces": len(bm.faces), "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges), "ngons": sum(len(face.verts) > 4 for face in bm.faces), "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces)}
    bm.free()
    evaluated.to_mesh_clear()
    return result


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected RUN_DIR after --")
    run_dir = Path(args[0]).resolve()
    generator = json.loads((run_dir / "shrinkwrap_footprint_report.json").read_text(encoding="utf-8"))
    objects = {name: bpy.data.objects.get(name) for name in NAMES}
    modifiers = {name: obj.modifiers.get("Project mounting footprint") if obj else None for name, obj in objects.items()}
    health = {name: evaluated_health(obj) if obj else None for name, obj in objects.items()}
    image = bpy.data.images.load(str(run_dir / "shrinkwrap_footprint_matcap.png"), check_existing=False)
    stride = max(4, (len(image.pixels) // 5000 // 4) * 4)
    pixels = [image.pixels[index] for index in range(0, len(image.pixels), stride)]
    image_record = {"width": image.size[0], "height": image.size[1], "dynamic_range": max(pixels) - min(pixels)}
    bpy.data.images.remove(image)
    assertions = {
        "generator_report_passes": generator.get("pass") is True,
        "all_mounts_exist": all(objects.values()),
        "all_modifiers_are_project_z": all(modifier and modifier.wrap_method == "PROJECT" and modifier.use_project_z for modifier in modifiers.values()),
        "only_unscoped_control_has_empty_vertex_group": modifiers[NAMES[0]].vertex_group == "MountFootprint" and modifiers[NAMES[1]].vertex_group == "" and modifiers[NAMES[2]].vertex_group == "MountFootprint" and modifiers[NAMES[3]].vertex_group == "MountFootprint",
        "wrong_direction_is_saved": modifiers[NAMES[2]].use_positive_direction and not modifiers[NAMES[2]].use_negative_direction,
        "scoped_and_wrong_direction_saved_mounts_are_clean": all(health[name] and health[name]["vertices"] == 50 and health[name]["faces"] == 48 and health[name]["non_manifold_edges"] == 0 and health[name]["ngons"] == 0 and health[name]["degenerate_faces"] == 0 for name in (NAMES[0], NAMES[2], NAMES[3])),
        "unscoped_saved_control_retains_expected_failure": health[NAMES[1]]["degenerate_faces"] > 0,
        "evidence_render_is_visible": image_record["width"] == 1400 and image_record["height"] == 520 and image_record["dynamic_range"] > 0.1,
    }
    report = {"lab": "independent_shrinkwrap_footprint_transfer_verification", "blender_version": bpy.app.version_string, "health": health, "image": image_record, "assertions": assertions, "pass": all(assertions.values())}
    (run_dir / "shrinkwrap_footprint_verify.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SHRINKWRAP_FOOTPRINT_VERIFY:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
