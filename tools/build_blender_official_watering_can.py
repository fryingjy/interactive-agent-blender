"""Independently reproduce the official Blender Fundamentals watering-can lesson.

The CC-BY lesson file is used only as a read-only comparison target. Geometry is
authored here from the published written workflow: a ring-built body, curve-like
tube paths converted conceptually to mesh rings, matching body openings, bridged
connections, one connected half cage, and a live Mirror modifier.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-22_tutorial-blender-official-watering-can"
BLEND = RUN / "watering_can_tutorial_v5.blend"


class MeshBuilder:
    def __init__(self) -> None:
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, ...]] = []

    def vertex(self, co) -> int:
        self.vertices.append(tuple(float(value) for value in co))
        return len(self.vertices) - 1

    def ring(self, points) -> list[int]:
        return [self.vertex(point) for point in points]

    def bridge(self, first: list[int], second: list[int]) -> None:
        if len(first) != len(second):
            raise ValueError("bridge loops require equal vertex counts")
        count = len(first)
        for index in range(count):
            self.faces.append((first[index], first[(index + 1) % count], second[(index + 1) % count], second[index]))


def body_point(radius: float, z: float, index: int, segments: int = 32) -> tuple[float, float, float]:
    angle = 2.0 * math.pi * index / segments
    return radius * math.sin(angle), radius * math.cos(angle), z


def hole_boundary(rings: list[list[int]], lower: int, center: int) -> list[int]:
    left = (center - 1) % 32
    right = (center + 1) % 32
    return [
        rings[lower][left], rings[lower][center], rings[lower][right],
        rings[lower + 1][right], rings[lower + 2][right],
        rings[lower + 2][center], rings[lower + 2][left], rings[lower + 1][left],
    ]


def catmull_rom(points: list[Vector], steps: int = 3) -> list[Vector]:
    if len(points) < 2:
        return points
    padded = [points[0], *points, points[-1]]
    result = [points[0]]
    for index in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[index - 1 : index + 3]
        for step in range(1, steps + 1):
            t = step / steps
            t2, t3 = t * t, t * t * t
            result.append(
                0.5
                * (
                    2 * p1
                    + (-p0 + p2) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
                )
            )
    return result


def tube_ring(center: Vector, tangent: Vector, radius: float, count: int = 8) -> list[Vector]:
    tangent = tangent.normalized()
    depth_axis = Vector((1.0, 0.0, 0.0))
    side_axis = tangent.cross(depth_axis).normalized()
    return [
        center
        + depth_axis * (math.cos(2 * math.pi * index / count) * radius)
        + side_axis * (math.sin(2 * math.pi * index / count) * radius)
        for index in range(count)
    ]


def ellipse_arc(center_y: float, center_z: float, radius_y: float, radius_z: float, start_deg: float, end_deg: float, count: int) -> list[tuple[float, float, float]]:
    return [
        (
            0.0,
            center_y + radius_y * math.cos(math.radians(start_deg + (end_deg - start_deg) * index / (count - 1))),
            center_z + radius_z * math.sin(math.radians(start_deg + (end_deg - start_deg) * index / (count - 1))),
        )
        for index in range(count)
    ]


def best_boundary_order(builder: MeshBuilder, boundary: list[int], target: list[Vector]) -> list[int]:
    candidates = []
    for source in (boundary, list(reversed(boundary))):
        for offset in range(len(source)):
            ordered = source[offset:] + source[:offset]
            score = sum((Vector(builder.vertices[index]) - target[i]).length_squared for i, index in enumerate(ordered))
            candidates.append((score, ordered))
    return min(candidates, key=lambda item: item[0])[1]


def bridge_with_transition(builder: MeshBuilder, first: list[int], second: list[int], steps: int = 2) -> None:
    start_points = [Vector(builder.vertices[index]) for index in first]
    end_points = [Vector(builder.vertices[index]) for index in second]
    current = first
    for step in range(1, steps + 1):
        factor = step / (steps + 1)
        ring = builder.ring(start.lerp(end, factor) for start, end in zip(start_points, end_points))
        builder.bridge(current, ring)
        current = ring
    builder.bridge(current, second)


def sweep_between(builder: MeshBuilder, start_boundary: list[int], end_boundary: list[int], controls, radius: float) -> None:
    path = catmull_rom([Vector(point) for point in controls], 3)
    generated: list[list[int]] = []
    for index in range(1, len(path) - 1):
        tangent = path[index + 1] - path[index - 1]
        generated.append(builder.ring(tube_ring(path[index], tangent, radius)))
    first_target = [Vector(builder.vertices[index]) for index in generated[0]]
    start = best_boundary_order(builder, start_boundary, first_target)
    bridge_with_transition(builder, start, generated[0])
    for first, second in zip(generated, generated[1:]):
        builder.bridge(first, second)
    last_target = [Vector(builder.vertices[index]) for index in generated[-1]]
    end = best_boundary_order(builder, end_boundary, last_target)
    bridge_with_transition(builder, generated[-1], end)


def sweep_open(builder: MeshBuilder, start_boundary: list[int], controls, start_radius: float, end_radius: float) -> None:
    path = catmull_rom([Vector(point) for point in controls], 3)
    generated: list[list[int]] = []
    for index in range(1, len(path)):
        prior = path[index - 1]
        following = path[min(index + 1, len(path) - 1)]
        tangent = following - prior
        factor = index / (len(path) - 1)
        radius = start_radius * (1.0 - factor) + end_radius * factor
        generated.append(builder.ring(tube_ring(path[index], tangent, radius)))
    first_target = [Vector(builder.vertices[index]) for index in generated[0]]
    start = best_boundary_order(builder, start_boundary, first_target)
    bridge_with_transition(builder, start, generated[0])
    for first, second in zip(generated, generated[1:]):
        builder.bridge(first, second)

    outer = generated[-1]
    tip_center = path[-1]
    tangent = (path[-1] - path[-2]).normalized()
    inner_points = tube_ring(tip_center - tangent * 0.012, tangent, end_radius * 0.64)
    inner = builder.ring(inner_points)
    builder.bridge(outer, list(reversed(inner)))


def component_sizes(mesh: bpy.types.Mesh) -> list[int]:
    adjacency = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    remaining = set(adjacency)
    sizes = []
    while remaining:
        size = 1
        stack = [remaining.pop()]
        while stack:
            for neighbor in adjacency[stack.pop()]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    size += 1
        sizes.append(size)
    return sorted(sizes, reverse=True)


def build_mesh() -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    builder = MeshBuilder()
    z_levels = [0.00, 0.028, 0.060, 0.104, 0.176, 0.272, 0.384, 0.512, 0.672, 0.832, 0.992, 1.144, 1.264, 1.360, 1.440, 1.504]
    radii = [0.50, 0.555, 0.535, 0.49, 0.48, 0.465, 0.45, 0.435, 0.42, 0.405, 0.39, 0.375, 0.39, 0.35, 0.255, 0.145]
    rings = [builder.ring(body_point(radius, z, index) for index in range(32)) for radius, z in zip(radii, z_levels)]

    # Published lesson: remove matching 2x2 face patches before bridging 8-vertex tubes.
    holes = {(4, 0), (12, 16), (4, 16)}
    skipped = {(band, face) for lower, center in holes for band in (lower, lower + 1) for face in ((center - 1) % 32, center)}
    for band in range(len(rings) - 1):
        for face in range(32):
            if (band, face) in skipped:
                continue
            nxt = (face + 1) % 32
            builder.faces.append((rings[band][face], rings[band][nxt], rings[band + 1][nxt], rings[band + 1][face]))

    bottom_center = builder.vertex((0.0, 0.0, 0.0))
    for face in range(32):
        builder.faces.append((bottom_center, rings[0][(face + 1) % 32], rings[0][face]))

    # A shallow inner neck gives the visible top opening thickness without hidden full-depth geometry.
    inner_top = builder.ring(body_point(0.11, 1.504, index) for index in range(32))
    inner_low = builder.ring(body_point(0.11, 1.424, index) for index in range(32))
    builder.bridge(rings[-1], list(reversed(inner_top)))
    builder.bridge(inner_top, inner_low)

    lower_handle = hole_boundary(rings, 4, 0)
    upper_handle = hole_boundary(rings, 12, 16)
    spout = hole_boundary(rings, 4, 16)

    sweep_between(
        builder,
        lower_handle,
        upper_handle,
        ellipse_arc(0.65, 1.48, 1.05, 1.18, -100.0, 178.0, 15)
        + [(0.0, -0.39, 1.42), (0.0, -0.355, 1.36)],
        0.105,
    )
    sweep_open(
        builder,
        spout,
        [
            (0.0, -0.48, 0.27), (0.0, -0.78, 0.27), (0.0, -1.03, 0.34),
            (0.0, -1.17, 0.55), (0.0, -1.18, 0.82), (0.0, -1.31, 1.05),
            (0.0, -1.58, 1.23), (0.0, -1.90, 1.30),
        ],
        0.105,
        0.072,
    )

    # Match the official lesson file's overall height/length ratio in cage space.
    builder.vertices = [(x, y, z * 0.862) for x, y, z in builder.vertices]

    # Retain the positive-X editable half cage. Every authored cross-section has
    # vertices on X=0, so the live Mirror can merge the seam without applying.
    keep = {index for index, vertex in enumerate(builder.vertices) if vertex[0] >= -1e-7}
    remap = {old: new for new, old in enumerate(sorted(keep))}
    vertices = [builder.vertices[old] for old in sorted(keep)]
    faces = [tuple(remap[index] for index in face) for face in builder.faces if all(index in keep for index in face)]
    return vertices, faces


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    vertices, faces = build_mesh()
    mesh = bpy.data.meshes.new("GEO-watering_can_Cage")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("GEO-watering_can", mesh)
    collection = bpy.data.collections.new("watering_can")
    bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    loose = [vertex for vertex in bm.verts if not vertex.link_edges]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    mirror = obj.modifiers.new("Mirror", "MIRROR")
    mirror.use_axis[0] = True
    mirror.use_clip = True
    mirror.use_mirror_merge = True
    mirror.merge_threshold = 0.001

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

    sizes = component_sizes(mesh)
    report = {
        "schema_version": 1,
        "record_type": "OFFICIAL_TUTORIAL_INDEPENDENT_REPRODUCTION",
        "source": "https://studio.blender.org/training/blender-fundamentals-45-lts/blender_4-5_lts_modeling-the-watering-can/",
        "blend": str(BLEND.relative_to(ROOT)),
        "object_count": 1,
        "connected_components_base_cage": len(sizes),
        "component_vertex_counts": sizes,
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "triangles": sum(len(poly.vertices) == 3 for poly in mesh.polygons),
        "quads": sum(len(poly.vertices) == 4 for poly in mesh.polygons),
        "ngons": sum(len(poly.vertices) > 4 for poly in mesh.polygons),
        "live_modifiers": [modifier.type for modifier in obj.modifiers],
        "modifiers_applied": False,
        "construction": "one connected positive-X half cage; body openings and 8-sided tube rings are bridged; live X Mirror merges the symmetry seam",
        "reference_mesh_copied": False,
    }
    (RUN / "modeling_report_v5.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
