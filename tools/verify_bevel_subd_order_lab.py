"""Fresh-process verification of the saved Bevel/SubD order experiment."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy

NAMES = ("A_PreSubD_Bevel", "B_PostSubD_Bevel_Creased", "C_PostSubD_Bevel_Unprotected")


def evaluated_health(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "degenerate_faces": sum(face.calc_area() < 1e-8 for face in bm.faces),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected RUN_DIR after --")
    run_dir = Path(args[0]).resolve()
    generator = json.loads((run_dir / "bevel_subd_order_report.json").read_text(encoding="utf-8"))
    objects = {name: bpy.data.objects.get(name) for name in NAMES}
    orders = {name: [modifier.type for modifier in obj.modifiers] if obj else None for name, obj in objects.items()}
    health = {name: evaluated_health(obj) if obj else None for name, obj in objects.items()}
    images = {}
    for filename in ("bevel_subd_order_matcap.png", "bevel_subd_order_wire.png"):
        image = bpy.data.images.load(str(run_dir / filename), check_existing=False)
        stride = max(4, (len(image.pixels) // 5000 // 4) * 4)
        samples = [image.pixels[index] for index in range(0, len(image.pixels), stride)]
        images[filename] = {
            "width": image.size[0],
            "height": image.size[1],
            "nonzero": (run_dir / filename).stat().st_size > 0,
            "sampled_channel_dynamic_range": round(max(samples) - min(samples), 6),
        }
        bpy.data.images.remove(image)
    assertions = {
        "generator_report_passes": generator.get("pass") is True,
        "all_named_objects_exist": all(objects.values()),
        "saved_modifier_orders_match": orders[NAMES[0]] == ["BEVEL", "SUBSURF"] and orders[NAMES[1]] == ["SUBSURF", "BEVEL"] and orders[NAMES[2]] == ["SUBSURF", "BEVEL"],
        "crease_exists_only_on_protected_post_variant": "crease_edge" in objects[NAMES[1]].data.attributes and "crease_edge" not in objects[NAMES[2]].data.attributes,
        "all_saved_evaluated_meshes_are_clean": all(item and item["non_manifold_edges"] == 0 and item["ngons"] == 0 and item["degenerate_faces"] == 0 for item in health.values()),
        "renders_are_full_resolution": all(item["width"] == 1200 and item["height"] == 520 and item["nonzero"] for item in images.values()),
        "renders_contain_visible_dynamic_range": all(item["sampled_channel_dynamic_range"] > 0.1 for item in images.values()),
        "temporary_wire_objects_not_saved": not any(obj.name.endswith("_EvaluatedWire") for obj in bpy.data.objects),
    }
    report = {"lab": "independent_bevel_subd_order_verification", "blender_version": bpy.app.version_string, "orders": orders, "health": health, "images": images, "assertions": assertions, "pass": all(assertions.values())}
    (run_dir / "bevel_subd_order_verify.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("BEVEL_SUBD_ORDER_VERIFY:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
