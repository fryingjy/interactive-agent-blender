"""Reconcile the Bevel-before/after-Subdivision source conflict in Blender 5.2.

The three fixtures share one moderately supported all-quad box cage and the
same semantic design edges.  They differ only in the intended workflow:

* PRE: weighted Bevel -> Subdivision (physical radius enters the smooth cage)
* POST_CREASE: crease + Subdivision -> weighted Bevel (protected line, final chamfer)
* POST_UNPROTECTED: Subdivision -> weighted Bevel without crease (negative control)

The lab records technical and surface signals and produces fixed-frame MatCap
renders.  It does not convert those signals into a universal artistic winner.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "blender_ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from evaluated_probe import evaluated_mesh_health, evaluated_surface_diagnostics, evaluated_surface_quality

OUT = ROOT / "runs" / "2026-08-15_bevel-subd-order"
NAMES = ("A_PreSubD_Bevel", "B_PostSubD_Bevel_Creased", "C_PostSubD_Bevel_Unprotected")


def base_cage(name: str, x: float):
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(x, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (1.25, 0.85, 0.62)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=2)
    bpy.ops.object.mode_set(mode="OBJECT")
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def design_edge_indices(obj):
    bounds = [max(abs(vertex.co[axis]) for vertex in obj.data.vertices) for axis in range(3)]
    result = []
    for edge in obj.data.edges:
        vertices = [obj.data.vertices[index].co for index in edge.vertices]
        fixed_extreme_axes = 0
        for axis in range(3):
            if all(abs(abs(vertex[axis]) - bounds[axis]) < 1e-5 for vertex in vertices):
                fixed_extreme_axes += 1
        if fixed_extreme_axes == 2:
            result.append(edge.index)
    return result


def write_edge_attribute(obj, name: str, indices, value: float):
    attribute = obj.data.attributes.get(name) or obj.data.attributes.new(name, "FLOAT", "EDGE")
    selected = set(indices)
    for edge in obj.data.edges:
        attribute.data[edge.index].value = value if edge.index in selected else 0.0


def add_subd(obj):
    modifier = obj.modifiers.new("Form subdivision", "SUBSURF")
    modifier.subdivision_type = "CATMULL_CLARK"
    modifier.levels = modifier.render_levels = 2
    return modifier


def add_bevel(obj):
    modifier = obj.modifiers.new("Semantic edge radius", "BEVEL")
    modifier.limit_method = "WEIGHT"
    modifier.width = 0.09
    modifier.segments = 2
    modifier.harden_normals = True
    return modifier


def evaluated_shape(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    coordinates = [vertex.co for vertex in bm.verts]
    bounds = {
        axis: round(max(vertex[axis] for vertex in coordinates) - min(vertex[axis] for vertex in coordinates), 6)
        for axis in range(3)
    }
    planar = sum(
        max(abs(face.normal.x), abs(face.normal.y), abs(face.normal.z)) >= 0.999
        for face in bm.faces
    )
    result = {
        "bounds_xyz": [bounds[0], bounds[1], bounds[2]],
        "axis_planar_face_ratio": round(planar / len(bm.faces), 6) if bm.faces else 0.0,
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def object_record(obj, edge_count):
    return {
        "base": {"vertices": len(obj.data.vertices), "edges": len(obj.data.edges), "faces": len(obj.data.polygons), "design_edges": edge_count},
        "modifier_order": [modifier.type for modifier in obj.modifiers],
        "health": evaluated_mesh_health(obj.name),
        "surface_quality": evaluated_surface_quality(obj.name),
        "surface_diagnostics": evaluated_surface_diagnostics(obj.name),
        "shape": evaluated_shape(obj),
    }


def render_comparison(path: Path, wire: bool):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT" if wire else "MATCAP"
    if not wire:
        scene.display.shading.studio_light = "hard_surface_grey.exr"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.type = "SOLID"
    scene.display.shading.wireframe_color_type = "OBJECT"
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_shadows = True
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 520
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Evidence World")
    scene.world.color = (0.025, 0.03, 0.04)
    wire_objects = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for index, name in enumerate(NAMES):
        obj = bpy.data.objects[name]
        obj.color = ((0.18, 0.45, 0.70, 1), (0.22, 0.62, 0.48, 1), (0.68, 0.31, 0.22, 1))[index]
        obj.show_wire = False
        obj.show_all_edges = False
        if wire:
            evaluated = obj.evaluated_get(depsgraph)
            wire_mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
            wire_obj = bpy.data.objects.new(f"{name}_EvaluatedWire", wire_mesh)
            wire_obj.matrix_world = obj.matrix_world.copy()
            wire_obj.color = ((0.28, 0.75, 1.0, 1), (0.30, 1.0, 0.66, 1), (1.0, 0.46, 0.28, 1))[index]
            bpy.context.scene.collection.objects.link(wire_obj)
            modifier = wire_obj.modifiers.new("Evidence wire", "WIREFRAME")
            modifier.thickness = 0.006
            modifier.use_replace = True
            obj.hide_render = True
            wire_objects.append(wire_obj)
    bpy.ops.object.camera_add(location=(8.6, -12.5, 8.2))
    camera = bpy.context.object
    camera.name = "EvidenceCamera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 9.4
    camera.rotation_euler = (Vector((0.0, 0.0, 0.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    for name in NAMES:
        bpy.data.objects[name].hide_render = False
    for wire_obj in wire_objects:
        mesh = wire_obj.data
        bpy.data.objects.remove(wire_obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    material = bpy.data.materials.new("Neutral review material")
    material.diffuse_color = (0.45, 0.48, 0.52, 1.0)

    pre = base_cage(NAMES[0], -3.2)
    pre_edges = design_edge_indices(pre)
    write_edge_attribute(pre, "bevel_weight_edge", pre_edges, 1.0)
    add_bevel(pre)
    add_subd(pre)

    post_crease = base_cage(NAMES[1], 0.0)
    post_crease_edges = design_edge_indices(post_crease)
    write_edge_attribute(post_crease, "bevel_weight_edge", post_crease_edges, 1.0)
    write_edge_attribute(post_crease, "crease_edge", post_crease_edges, 0.75)
    add_subd(post_crease)
    add_bevel(post_crease)

    post_unprotected = base_cage(NAMES[2], 3.2)
    post_unprotected_edges = design_edge_indices(post_unprotected)
    write_edge_attribute(post_unprotected, "bevel_weight_edge", post_unprotected_edges, 1.0)
    add_subd(post_unprotected)
    add_bevel(post_unprotected)

    for obj in (pre, post_crease, post_unprotected):
        obj.data.materials.append(material)

    records = {
        pre.name: object_record(pre, len(pre_edges)),
        post_crease.name: object_record(post_crease, len(post_crease_edges)),
        post_unprotected.name: object_record(post_unprotected, len(post_unprotected_edges)),
    }
    orders = {name: record["modifier_order"] for name, record in records.items()}
    assertions = {
        "identical_base_topology": len({(r["base"]["vertices"], r["base"]["edges"], r["base"]["faces"], r["base"]["design_edges"]) for r in records.values()}) == 1,
        "pre_subd_order_is_bevel_then_subsurf": orders[pre.name] == ["BEVEL", "SUBSURF"],
        "post_subd_orders_are_subsurf_then_bevel": orders[post_crease.name] == ["SUBSURF", "BEVEL"] and orders[post_unprotected.name] == ["SUBSURF", "BEVEL"],
        "all_evaluated_meshes_are_closed_quad_manifold": all(r["health"]["non_manifold_edges"] == 0 and r["health"]["degenerate_faces"] == 0 and r["health"]["ngons"] == 0 for r in records.values()),
        "all_strategies_add_evaluated_geometry": all(r["health"]["faces"] > r["base"]["faces"] for r in records.values()),
        "surface_strategies_produce_distinct_planarity_signals": len({r["shape"]["axis_planar_face_ratio"] for r in records.values()}) == 3,
        "creased_post_subd_fixture_concentrates_more_local_curvature_than_pre_subd": post_crease.name in records and records[post_crease.name]["surface_diagnostics"]["pinch_candidate_count"] > records[pre.name]["surface_diagnostics"]["pinch_candidate_count"],
    }
    solid_path = OUT / "bevel_subd_order_matcap.png"
    wire_path = OUT / "bevel_subd_order_wire.png"
    render_comparison(solid_path, wire=False)
    render_comparison(wire_path, wire=True)
    report = {
        "lab": "bevel_before_vs_after_subdivision",
        "blender_version": bpy.app.version_string,
        "source_conflict": {
            "standing_project_path": "semantic weighted Bevel before Subdivision",
            "captured_tutorial_path": "crease/weight base edges, Subdivision, then weighted Bevel with Harden Normals",
        },
        "fixture": "identical 3x3-supported all-quad rectangular box cages; 36 semantic outer design-edge segments",
        "records": records,
        "assertions": assertions,
        "interpretation_boundary": [
            "Technical health does not decide which edge character matches a reference.",
            "Pre-SubD Bevel makes the radius part of the smoothed form; post-SubD Bevel adds a final chamfer to an already evaluated form.",
            "Post-SubD Bevel without crease protection is a negative control because Subdivision can move the intended design line before Bevel evaluates.",
            "Choose by desired radius, silhouette, highlight flow, and topology cost on the actual asset; neither order is universal.",
        ],
        "rejected_check": "Evaluated face counts and bounding boxes did not distinguish the creased and unprotected post-SubD variants; those coarse checks were rejected in favor of fixed-frame visual review plus measured planarity/local-curvature signals.",
        "renders": [solid_path.name, wire_path.name],
        "pass": all(assertions.values()) and all(path.exists() and path.stat().st_size > 0 for path in (solid_path, wire_path)),
    }
    (OUT / "bevel_subd_order_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "bevel_subd_order.blend"))
    print("BEVEL_SUBD_ORDER_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
