"""Reproduce Game Asset Factory's connected loop-cut/extrude chair exercise."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = REPO_ROOT / "runs" / "2026-08-22_tutorial-game-asset-factory-chair"


def reset_scene() -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def connected_chair_mesh() -> bpy.types.Object:
    # These three bins in X/Y are the result of four perimeter loop cuts on the seat cube.
    x_edges = (-1.50, -1.10, 1.10, 1.50)
    y_edges = (-1.50, -1.10, 1.10, 1.50)
    z_edges = (-2.55, -0.16, 0.16, 2.65)

    # Occupied cells are equivalent to extruding the four bottom corner faces into legs and the
    # complete rear top row into one backrest region. Shared faces are removed, so this is one
    # connected manifold shell—not joined overlapping boxes.
    occupied: set[tuple[int, int, int]] = set()
    occupied.update((ix, iy, 1) for ix in range(3) for iy in range(3))  # seat
    occupied.update((ix, 2, 2) for ix in range(3))  # backrest
    occupied.update((ix, iy, 0) for ix in (0, 2) for iy in (0, 2))  # legs

    vertex_ids: dict[tuple[float, float, float], int] = {}
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []

    def vertex(co: tuple[float, float, float]) -> int:
        if co not in vertex_ids:
            vertex_ids[co] = len(vertices)
            vertices.append(co)
        return vertex_ids[co]

    directions = (
        ((-1, 0, 0), lambda x0, x1, y0, y1, z0, z1: ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))),
        ((1, 0, 0), lambda x0, x1, y0, y1, z0, z1: ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))),
        ((0, -1, 0), lambda x0, x1, y0, y1, z0, z1: ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))),
        ((0, 1, 0), lambda x0, x1, y0, y1, z0, z1: ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0))),
        ((0, 0, -1), lambda x0, x1, y0, y1, z0, z1: ((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0))),
        ((0, 0, 1), lambda x0, x1, y0, y1, z0, z1: ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))),
    )
    for ix, iy, iz in sorted(occupied):
        bounds = (x_edges[ix], x_edges[ix + 1], y_edges[iy], y_edges[iy + 1], z_edges[iz], z_edges[iz + 1])
        for (dx, dy, dz), corners in directions:
            if (ix + dx, iy + dy, iz + dz) in occupied:
                continue
            faces.append(tuple(vertex(co) for co in corners(*bounds)))

    mesh = bpy.data.meshes.new("Chair_LoopExtrude_Cage")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new("Chair_Connected_LoopExtrude", mesh)
    bpy.context.collection.objects.link(obj)
    obj["tutorial_source"] = "https://www.youtube.com/watch?v=LyPPgW9GpKo"
    obj["construction"] = "single cube -> four perimeter loop cuts -> rear/leg face extrusions"
    obj["connected_component_intent"] = 1
    return obj


def add_material(obj: bpy.types.Object) -> None:
    material = bpy.data.materials.new("Tutorial_Chair_Warm_Wood")
    material.diffuse_color = (0.32, 0.105, 0.035, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.32, 0.105, 0.035, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.46
    obj.data.materials.append(material)


def mesh_audit(obj: bpy.types.Object) -> dict[str, object]:
    mesh = obj.data
    edge_face_counts = [0] * len(mesh.edges)
    edge_lookup = {tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges}
    for polygon in mesh.polygons:
        for key in polygon.edge_keys:
            edge_face_counts[edge_lookup[tuple(sorted(key))]] += 1
    components = 0
    pending = set(range(len(mesh.vertices)))
    adjacency = {index: set() for index in pending}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    while pending:
        components += 1
        stack = [pending.pop()]
        while stack:
            for neighbor in adjacency[stack.pop()]:
                if neighbor in pending:
                    pending.remove(neighbor)
                    stack.append(neighbor)
    return {
        "objects": 1,
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "triangles": sum(max(1, len(poly.vertices) - 2) for poly in mesh.polygons),
        "non_quad_faces": sum(len(poly.vertices) != 4 for poly in mesh.polygons),
        "boundary_edges": sum(count == 1 for count in edge_face_counts),
        "non_manifold_edges": sum(count != 2 for count in edge_face_counts),
        "connected_components": components,
        "modifiers": [],
    }


def point_camera(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def render_views(obj: bpy.types.Object) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.curvature_ridge_factor = 1.7
    scene.display.shading.curvature_valley_factor = 1.3
    scene.display.shading.color_type = "MATERIAL"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    camera_data = bpy.data.cameras.new("Tutorial_Diagnostic_Camera")
    camera = bpy.data.objects.new("Tutorial_Diagnostic_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 7.1
    scene.camera = camera
    target = Vector((0, 0, 0.05))
    views = {
        "front": Vector((0, -8, 0.15)),
        "side": Vector((8, 0, 0.15)),
        "isometric": Vector((6.5, -7.5, 5.2)),
    }
    for name, location in views.items():
        camera.location = location
        point_camera(camera, target)
        scene.render.filepath = str(RUN_DIR / f"chair_{name}_solid.png")
        bpy.ops.render.render(write_still=True)


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    reset_scene()
    obj = connected_chair_mesh()
    add_material(obj)
    audit = mesh_audit(obj)
    if audit["connected_components"] != 1 or audit["non_manifold_edges"] != 0 or audit["non_quad_faces"] != 0:
        raise RuntimeError(f"chair topology gate failed: {audit}")
    render_views(obj)
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN_DIR / "beginner_chair_connected.blend"))
    (RUN_DIR / "topology_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
