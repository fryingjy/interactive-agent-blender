"""Transfer Knife/Bisect and Loop Cut lessons to a rounded equipment housing.

This is a controlled mechanism experiment, not an asset builder or a claim of
professional prop quality. It exercises the repository's typed operations and
retains an interrupted-ring and an invalid fill request as failure evidence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "blender_ops") not in sys.path:
    sys.path.insert(0, str(REPO / "blender_ops"))

from blender_ops import mesh_ops


def output_dir() -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


SECTION = [
    (-1.35, -0.72), (-0.98, -1.08), (0.98, -1.08), (1.35, -0.72),
    (1.35, 0.72), (0.98, 1.08), (-0.98, 1.08), (-1.35, 0.72),
]


def housing(name: str, y: float, *, interrupt_ring: bool = False) -> bpy.types.Object:
    """Create a closed, non-primitive rounded rectangular enclosure along X."""
    xs = (-3.0, 3.0)
    verts = [(x, y + sy, sz) for x in xs for sy, sz in SECTION]
    verts.extend([(-3.0, y, 0.0), (3.0, y, 0.0)])
    faces: list[tuple[int, ...]] = []
    for i in range(8):
        q = (i, (i + 1) % 8, 8 + (i + 1) % 8, 8 + i)
        if interrupt_ring and i == 2:
            faces.extend([(q[0], q[1], q[2]), (q[0], q[2], q[3])])
        else:
            faces.append(q)
    for i in range(8):
        faces.append((16, (i + 1) % 8, i))
        faces.append((17, 8 + i, 8 + (i + 1) % 8))
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def select_longitudinal_ring(obj: bpy.types.Object) -> int:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for item in (*bm.verts, *bm.edges, *bm.faces):
        item.select = False
    selected = 0
    for edge in bm.edges:
        if abs(edge.verts[0].co.x - edge.verts[1].co.x) > 5.9:
            edge.select = True
            edge.verts[0].select = True
            edge.verts[1].select = True
            selected += 1
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return selected


def select_all(obj: bpy.types.Object) -> None:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for item in (*bm.verts, *bm.edges, *bm.faces):
        item.select = True
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def stats(obj: bpy.types.Object) -> dict:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    lengths = [edge.calc_length() for edge in bm.edges]
    result = {
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "minimum_edge_length": min(lengths),
    }
    bm.free()
    return result


def material(name: str, color: tuple[float, float, float, float], metallic=0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = 0.3
    return mat


def finish(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Review edge bevel", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 3
    for poly in obj.data.polygons:
        poly.use_smooth = True


def render(output: Path, objects: list[bpy.types.Object]) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 620
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.025, 0.03, 0.045)
    bpy.ops.object.camera_add(location=(12.8, -16.5, 10.8))
    camera = bpy.context.object
    scene.camera = camera
    target = Vector((0.0, 0.0, 0.0))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 56
    for location, energy, size in [((-4, -7, 10), 1400, 5.0), ((8, -2, 6), 900, 4.0), ((0, 8, 7), 1100, 3.0)]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(output / "knife_loop_transfer_beauty.png")
    bpy.ops.render.render(write_still=True)
    wire_material = material("Topology_Wire", (0.003, 0.003, 0.003, 1.0))
    temporary_wires = []
    disabled_bevels = []
    for obj in objects:
        for modifier in obj.modifiers:
            if modifier.type == "BEVEL":
                modifier.show_render = False
                disabled_bevels.append(modifier)
        obj.data.materials.append(wire_material)
        wire = obj.modifiers.new("Topology evidence wire", "WIREFRAME")
        wire.thickness = 0.018
        wire.use_replace = False
        wire.material_offset = 1
        temporary_wires.append((obj, wire))
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.filepath = str(output / "knife_loop_transfer_topology.png")
    bpy.ops.render.render(write_still=True)
    for obj, wire in temporary_wires:
        obj.modifiers.remove(wire)
        obj.data.materials.pop(index=len(obj.data.materials) - 1)
    for modifier in disabled_bevels:
        modifier.show_render = True


def main() -> None:
    output = output_dir()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    blue = material("Purposeful_Local_Loops", (0.05, 0.24, 0.58, 1.0), 0.65)
    red = material("Interrupted_Ring", (0.52, 0.055, 0.035, 1.0), 0.35)
    gold = material("Exact_Bisect", (0.62, 0.25, 0.045, 1.0), 0.75)

    good = housing("Purposeful_LoopCut_Housing", -4.0)
    good_selected = select_longitudinal_ring(good)
    good_before = stats(good)
    good_result = mesh_ops.loop_cut_selection(good.name, cuts=3)
    good_after = stats(good)
    finish(good, blue)

    interrupted = housing("Interrupted_Ring_Failure", 0.0, interrupt_ring=True)
    interrupted_selected = select_longitudinal_ring(interrupted)
    interrupted_before = stats(interrupted)
    interrupted_error = None
    interrupted_result = None
    try:
        interrupted_result = mesh_ops.loop_cut_selection(interrupted.name, cuts=3)
    except Exception as exc:  # retained expected topology-routing failure
        interrupted_error = f"{type(exc).__name__}: {exc}"
    interrupted_after = stats(interrupted)
    finish(interrupted, red)

    bisected = housing("Bisected_Capped_Housing", 4.0)
    select_all(bisected)
    invalid_fill_error = None
    try:
        mesh_ops.bisect_selection(bisected.name, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), fill=True)
    except Exception as exc:
        invalid_fill_error = f"{type(exc).__name__}: {exc}"
    select_all(bisected)
    bisect_result = mesh_ops.bisect_selection(
        bisected.name, (0.65, 0.0, 0.0), (1.0, 0.0, 0.0), clear_outer=True, fill=True
    )
    bisect_after = stats(bisected)
    finish(bisected, gold)

    expected_new_ring_vertices = good_selected * 3
    observed_good_new_vertices = good_after["vertices"] - good_before["vertices"]
    observed_interrupted_new_vertices = interrupted_after["vertices"] - interrupted_before["vertices"]
    assertions = {
        "purposeful_ring_selected": good_selected == 8,
        "three_complete_rings_created": observed_good_new_vertices == expected_new_ring_vertices,
        "purposeful_result_remains_closed": good_after["non_manifold_edges"] == 0,
        "interrupted_quad_flow_is_not_complete_ring": interrupted_error is not None or observed_interrupted_new_vertices < expected_new_ring_vertices,
        "fill_without_clear_is_rejected": invalid_fill_error is not None,
        "bisect_clear_and_fill_caps_boundary": bisect_result["filled_faces"] > 0 and bisect_after["non_manifold_edges"] == 0,
        "all_final_specimens_non_degenerate": all(stats(obj)["degenerate_faces"] == 0 for obj in (good, interrupted, bisected)),
    }
    report = {
        "lab": "knife_loop_cut_different_shape_transfer",
        "blender_version": bpy.app.version_string,
        "source_lessons": [
            "Knife Tool - Blender 2.80 Fundamentals",
            "Loop Cut - Blender 2.80 Fundamentals",
        ],
        "current_manual_corroboration": [
            "Blender 5.2 Knife Topology Tool",
            "Blender 5.2 Loop Cut and Slide",
            "Blender 5.2 Bisect",
        ],
        "specimens": {
            "purposeful_loop_cut": {"selected_ring_edges": good_selected, "before": good_before, "operation": good_result, "after": good_after},
            "interrupted_ring_failure": {"selected_edges": interrupted_selected, "before": interrupted_before, "operation": interrupted_result, "error": interrupted_error, "after": interrupted_after},
            "bisect": {"invalid_fill_error": invalid_fill_error, "operation": bisect_result, "after": bisect_after},
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
        "interpretation": "Loop Cut is efficient only when compatible quad flow carries the intended ring. Knife/Bisect is the deterministic choice for a deliberate planar cross-section; filling is meaningful only after one side is cleared.",
        "limitations": [
            "The lesson UI is Blender 2.80; mechanism and options were checked against the Blender 5.2 manual.",
            "This controlled housing test does not prove freehand modal Knife judgment or production asset quality.",
        ],
    }
    (output / "knife_loop_transfer_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    render(output, [good, interrupted, bisected])
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "knife_loop_transfer.blend"))
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit("knife/loop transfer assertions failed")


if __name__ == "__main__":
    main()
