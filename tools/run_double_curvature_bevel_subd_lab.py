"""Test explicit sharp-edge completeness on two double-curved SubD panels.

Each family uses one connected, closed, all-quad cage.  COMPLETE and
INCOMPLETE variants declare the same full physical rim intent; the negative
control deliberately omits eight declared perimeter segments during weight
assignment.  The lab exercises the typed decision path and keeps all
modifiers live.
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

import persistent_ids
from modeler_server import ModelerServer
from object_ops import hard_surface_shading_audit

OUT = ROOT / "runs" / "2026-08-16_double-curvature-bevel-subd"
BLEND = OUT / "double_curvature_bevel_subd.blend"
REPORT = OUT / "double_curvature_bevel_subd_report.json"
OVERVIEW = OUT / "double_curvature_bevel_subd_matcap.png"
BASE_WIRE = OUT / "double_curvature_base_cage_wire.png"

FAMILIES = {
    "CROWN": {"size": (3.2, 2.2), "amplitude": 0.42, "kind": "crown"},
    "SADDLE": {"size": (3.0, 2.4), "amplitude": 0.30, "kind": "saddle"},
}
NX = 7
NY = 7
THICKNESS = 0.34


def surface_height(u: float, v: float, family: dict) -> float:
    if family["kind"] == "crown":
        return family["amplitude"] * (1.0 - u * u) * (1.0 - v * v)
    return family["amplitude"] * (u * u - v * v)


def make_panel(name: str, family_name: str, family: dict, location) -> bpy.types.Object:
    width, depth = family["size"]
    vertices = []
    for layer in (0, 1):
        for j in range(NY):
            v = -1.0 + 2.0 * j / (NY - 1)
            for i in range(NX):
                u = -1.0 + 2.0 * i / (NX - 1)
                z = surface_height(u, v, family) - layer * THICKNESS
                vertices.append((0.5 * width * u, 0.5 * depth * v, z))

    def index(layer, i, j):
        return layer * NX * NY + j * NX + i

    faces = []
    for j in range(NY - 1):
        for i in range(NX - 1):
            faces.append((index(0, i, j), index(0, i + 1, j), index(0, i + 1, j + 1), index(0, i, j + 1)))
            faces.append((index(1, i, j + 1), index(1, i + 1, j + 1), index(1, i + 1, j), index(1, i, j)))
    perimeter = (
        [(i, 0) for i in range(NX)]
        + [(NX - 1, j) for j in range(1, NY)]
        + [(i, NY - 1) for i in range(NX - 2, -1, -1)]
        + [(0, j) for j in range(NY - 2, 0, -1)]
    )
    for current, following in zip(perimeter, perimeter[1:] + perimeter[:1]):
        i0, j0 = current
        i1, j1 = following
        faces.append((index(0, i0, j0), index(1, i0, j0), index(1, i1, j1), index(0, i1, j1)))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj["fixture_family"] = family_name
    obj["base_topology_contract"] = "one connected closed all-quad 7x7 top/bottom cage"
    persistent_ids.ensure_persistent_ids(name)
    return obj


def perimeter_edge_ids(obj: bpy.types.Object):
    edge_by_pair = {tuple(sorted(edge.vertices)): edge.index for edge in obj.data.edges}
    index_to_id = persistent_ids.get_id_maps(obj.name)["edges"]["index_to_id"]

    def vertex(layer, i, j):
        return layer * NX * NY + j * NX + i

    perimeter = (
        [(i, 0) for i in range(NX)]
        + [(NX - 1, j) for j in range(1, NY)]
        + [(i, NY - 1) for i in range(NX - 2, -1, -1)]
        + [(0, j) for j in range(NY - 2, 0, -1)]
    )
    ids = []
    pairs = []
    for layer in (0, 1):
        for current, following in zip(perimeter, perimeter[1:] + perimeter[:1]):
            pair = tuple(sorted((vertex(layer, *current), vertex(layer, *following))))
            pairs.append(pair)
            ids.append(int(index_to_id[edge_by_pair[pair]]))
    # Omit the middle segment of every side on both top and bottom.  These are
    # spread around the full object instead of manufacturing one local defect.
    side_length = NX - 1
    omitted_positions = []
    for layer in range(2):
        offset = layer * len(perimeter)
        omitted_positions.extend(offset + side * side_length + side_length // 2 for side in range(4))
    omitted = [ids[position] for position in omitted_positions]
    return ids, omitted


def configure(server: ModelerServer, obj: bpy.types.Object, complete: bool):
    intended, omitted = perimeter_edge_ids(obj)
    assigned = intended if complete else [agent_id for agent_id in intended if agent_id not in set(omitted)]
    bevel = obj.modifiers.new("Declared physical rim radius", "BEVEL")
    bevel.limit_method = "WEIGHT"
    bevel.width = 0.075
    bevel.segments = 2
    bevel.harden_normals = True
    subdivision = obj.modifiers.new("Double-curvature subdivision", "SUBSURF")
    subdivision.subdivision_type = "CATMULL_CLARK"
    subdivision.levels = subdivision.render_levels = 2

    transactions = []
    operations = (
        (
            "declare_bevel_edge_intent",
            {"edge_ids": intended, "rationale": "complete top and bottom manufactured panel rim"},
        ),
        (
            "set_bevel_weight_by_ids",
            {"edge_ids": assigned, "weight": 1.0, "clear_others": True},
        ),
        (
            "set_smooth_by_angle",
            {"angle": math.radians(30.0), "keep_sharp_edges": True},
        ),
    )
    for sequence, (operation, parameters) in enumerate(operations, start=1):
        begin = server.cmd_begin_decision(obj.name, operation)
        performed = server.cmd_perform_decision(
            begin["decision_id"], operation, parameters,
            command_id=f"{obj.name}_{sequence}_{operation}",
        )
        verified = server.cmd_verify_decision(begin["decision_id"])
        committed = server.cmd_commit_decision(begin["decision_id"])
        transactions.append({
            "operation": operation,
            "begin_revision": begin["observed_revision"],
            "result_revision": committed["result_revision"],
            "result": performed["result"],
            "verified_after_present": verified["after"] is not None,
        })
    return intended, omitted, assigned, transactions


def evaluated_metrics(obj: bpy.types.Object):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    coords = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
    result = {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "bounds_xyz": [
            round(max(co[axis] for co in coords) - min(co[axis] for co in coords), 6)
            for axis in range(3)
        ],
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def base_metrics(obj: bpy.types.Object):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    remaining = set(bm.verts)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "non_quads": sum(len(face.verts) != 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "connected_components": components,
    }
    bm.free()
    return result


def setup_render(path: Path):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    scene.display.shading.type = "SOLID"
    scene.display.shading.light = "MATCAP"
    scene.display.shading.studio_light = "hard_surface_grey.exr"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_specular_highlight = True
    scene.display.shading.background_type = "WORLD"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Double Curvature Review World")
    scene.world.color = (0.02, 0.025, 0.035)


def ensure_camera(location=(7.7, -10.5, 8.2), target=(0.0, 0.0, 0.0), scale=9.0):
    camera_data = bpy.data.cameras.get("DoubleCurvatureCamera") or bpy.data.cameras.new("DoubleCurvatureCamera")
    camera = bpy.data.objects.get("DoubleCurvatureCamera") or bpy.data.objects.new("DoubleCurvatureCamera", camera_data)
    if not camera.users_collection:
        bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = scale
    bpy.context.scene.camera = camera
    return camera


def render_overview(objects):
    setup_render(OVERVIEW)
    ensure_camera()
    colors = {
        "COMPLETE": (0.20, 0.52, 0.78, 1.0),
        "INCOMPLETE": (0.78, 0.31, 0.18, 1.0),
    }
    for obj in objects:
        obj.hide_render = False
        obj.color = colors[obj["selection_case"]]
    bpy.ops.render.render(write_still=True)


def render_base_wire(family_pairs, all_objects):
    visible = []
    wire_objects = []
    saved = {}
    for row, family_name in enumerate(FAMILIES):
        obj = family_pairs[family_name]["COMPLETE"]
        visible.append(obj)
        saved[obj.name] = {
            "location": obj.location.copy(),
            "color": tuple(obj.color),
            "modifier_render": [modifier.show_render for modifier in obj.modifiers],
        }
        obj.location = (0.0, 1.55 if row == 0 else -1.55, 0.0)
        obj.color = (0.20, 0.55, 0.82, 1.0)
        for modifier in obj.modifiers:
            modifier.show_render = False
        wire_mesh = obj.data.copy()
        wire_obj = bpy.data.objects.new(f"{obj.name}_EvidenceWire", wire_mesh)
        bpy.context.scene.collection.objects.link(wire_obj)
        wire_obj.location = obj.location.copy()
        wire_obj.color = (0.015, 0.025, 0.04, 1.0)
        wire = wire_obj.modifiers.new("Base cage evidence wire", "WIREFRAME")
        wire.thickness = 0.012
        wire.use_replace = True
        wire_objects.append(wire_obj)
    for obj in all_objects:
        obj.hide_render = obj not in visible
    setup_render(BASE_WIRE)
    bpy.context.scene.display.shading.light = "FLAT"
    ensure_camera(location=(6.6, -9.0, 7.0), scale=7.2)
    bpy.ops.render.render(write_still=True)
    for obj in visible:
        state = saved[obj.name]
        obj.location = state["location"]
        obj.color = state["color"]
        for modifier, show_render in zip(obj.modifiers, state["modifier_render"]):
            modifier.show_render = show_render
    for wire_obj in wire_objects:
        mesh = wire_obj.data
        bpy.data.objects.remove(wire_obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
    for obj in all_objects:
        obj.hide_render = False


def render_pair_difference(family_name: str, complete, incomplete, all_objects):
    pixels = {}
    paths = {}
    for label, obj in (("COMPLETE", complete), ("INCOMPLETE", incomplete)):
        for candidate in all_objects:
            candidate.hide_render = candidate != obj
        original_location = obj.location.copy()
        original_color = tuple(obj.color)
        obj.location = (0.0, 0.0, 0.0)
        obj.color = (0.48, 0.52, 0.58, 1.0)
        path = OUT / f"{family_name.lower()}_{label.lower()}_matcap.png"
        setup_render(path)
        ensure_camera(location=(5.2, -7.0, 5.5), scale=5.2)
        bpy.ops.render.render(write_still=True)
        image = bpy.data.images.load(str(path), check_existing=False)
        pixels[label] = list(image.pixels)
        bpy.data.images.remove(image)
        paths[label] = path.name
        obj.location = original_location
        obj.color = original_color
    changed = 0
    total = min(len(pixels["COMPLETE"]), len(pixels["INCOMPLETE"])) // 4
    for pixel in range(total):
        base = pixel * 4
        delta = max(abs(pixels["COMPLETE"][base + channel] - pixels["INCOMPLETE"][base + channel]) for channel in range(3))
        if delta > 0.035:
            changed += 1
    for candidate in all_objects:
        candidate.hide_render = False
    return {"images": paths, "changed_pixels": changed, "total_pixels": total, "changed_fraction": changed / total}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OUT.mkdir(parents=True, exist_ok=True)
    server = ModelerServer()
    objects = []
    records = {}
    family_pairs = {}
    for row, (family_name, family) in enumerate(FAMILIES.items()):
        y = 1.75 if row == 0 else -1.75
        pair = {}
        for label, x in (("COMPLETE", -2.1), ("INCOMPLETE", 2.1)):
            name = f"{family_name}_{label}"
            obj = make_panel(name, family_name, family, (x, y, 0.0))
            obj["selection_case"] = label
            intended, omitted, assigned, transactions = configure(server, obj, label == "COMPLETE")
            audit = hard_surface_shading_audit(name)
            records[name] = {
                "family": family_name,
                "selection_case": label,
                "base": base_metrics(obj),
                "intended_edge_count": len(intended),
                "assigned_edge_count": len(assigned),
                "omitted_edge_ids": omitted if label == "INCOMPLETE" else [],
                "modifier_types": [modifier.type for modifier in obj.modifiers],
                "audit": audit,
                "evaluated": evaluated_metrics(obj),
                "transactions": transactions,
            }
            objects.append(obj)
            pair[label] = obj
        family_pairs[family_name] = pair

    differences = {
        family_name: render_pair_difference(family_name, pair["COMPLETE"], pair["INCOMPLETE"], objects)
        for family_name, pair in family_pairs.items()
    }
    render_overview(objects)
    render_base_wire(family_pairs, objects)
    bpy.context.view_layer.update()
    assertions = {
        "four_variants_exist": len(records) == 4,
        "all_base_cages_connected_closed_all_quad": all(
            record["base"]["non_quads"] == 0 and record["base"]["vertices"] == 98
            and record["base"]["faces"] == 96
            and record["base"]["connected_components"] == 1
            and record["base"]["non_manifold_edges"] == 0
            and record["base"]["degenerate_faces"] == 0
            for record in records.values()
        ),
        "all_intent_declarations_are_explicit": all(
            record["audit"]["bevel_intent_source"] == "EXPLICIT_DECLARATION"
            for record in records.values()
        ),
        "complete_variants_pass_semantic_audit": all(
            records[f"{family}_COMPLETE"]["audit"]["status"] == "PASS"
            and not records[f"{family}_COMPLETE"]["audit"]["missing_weight_edge_ids"]
            for family in FAMILIES
        ),
        "incomplete_variants_fail_with_exact_omissions": all(
            records[f"{family}_INCOMPLETE"]["audit"]["status"] == "REVIEW_REQUIRED"
            and sorted(records[f"{family}_INCOMPLETE"]["audit"]["missing_weight_edge_ids"])
            == sorted(records[f"{family}_INCOMPLETE"]["omitted_edge_ids"])
            for family in FAMILIES
        ),
        "all_weighted_bevels_precede_subdivision": all(
            record["modifier_types"][:2] == ["BEVEL", "SUBSURF"] for record in records.values()
        ),
        "all_modifiers_remain_live": all(len(record["modifier_types"]) >= 2 for record in records.values()),
        "all_evaluated_meshes_closed_nondegenerate_quad": all(
            record["evaluated"]["non_manifold_edges"] == 0
            and record["evaluated"]["degenerate_faces"] == 0
            and record["evaluated"]["ngons"] == 0
            for record in records.values()
        ),
        "omissions_change_both_fixed_frame_results": all(
            difference["changed_pixels"] > 500 for difference in differences.values()
        ),
        "all_typed_decisions_committed_and_observed": all(
            transaction["result_revision"] == transaction["begin_revision"] + 1
            and transaction["verified_after_present"]
            for record in records.values() for transaction in record["transactions"]
        ),
    }
    report = {
        "lab": "double_curvature_explicit_bevel_intent_and_subd",
        "blender_version": bpy.app.version_string,
        "hypothesis": "A declared complete physical-rim edge set can detect distributed omissions that assignment-derived intent cannot; missing weighted segments remain visually consequential after Bevel-before-SubD on both positive and saddle double curvature.",
        "families": FAMILIES,
        "topology": {"grid": [NX, NY], "thickness": THICKNESS, "construction": "one connected closed all-quad cage per variant"},
        "records": records,
        "fixed_frame_differences": differences,
        "assertions": assertions,
        "renders": [OVERVIEW.name, BASE_WIRE.name] + [name for difference in differences.values() for name in difference["images"].values()],
        "pass": all(assertions.values()),
        "claim_boundary": "Controlled manufactured crown and saddle panels with predeclared rim intent. The run proves auditable edge-selection completeness and measurable evaluated visual consequences under a live Bevel->SubD stack; it does not identify sharp edges from arbitrary references or establish held-out asset quality.",
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print("DOUBLE_CURVATURE_BEVEL_SUBD_RESULT:" + json.dumps({"pass": report["pass"], "assertions": assertions, "differences": differences}))
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
