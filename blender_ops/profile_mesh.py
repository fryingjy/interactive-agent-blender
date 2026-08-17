"""Explicit profile-revolution mesh construction for authored lathed forms.

The functions in this module create vertices and faces directly.  They do not
call Blender mesh primitive operators, which keeps the authored radial profile
visible and reusable for measured-reference work.
"""

from __future__ import annotations

import math

import bpy


def revolve_closed_profile(name, profile, *, segments=96, collection=None):
    """Revolve a closed ``(radius, z)`` profile around world Z.

    All radii must be positive.  This is ideal for closed shells, rolled seams,
    and annular details.  The returned object has a seam-aware UV map.
    """
    if int(segments) < 3:
        raise ValueError("closed revolution profile needs at least 3 radial segments")
    if len(profile) < 3 or any(len(point) != 2 for point in profile) or any(radius <= 0 for radius, _z in profile):
        raise ValueError("closed revolution profile needs >=3 positive-radius points")
    vertices = []
    uvs = []
    count = len(profile)
    z_values = [point[1] for point in profile]
    z_min, z_max = min(z_values), max(z_values)
    z_span = max(z_max - z_min, 1e-8)
    for segment in range(segments):
        angle = 2.0 * math.pi * segment / segments
        cosine, sine = math.cos(angle), math.sin(angle)
        for radius, z_value in profile:
            vertices.append((radius * cosine, radius * sine, z_value))
            uvs.append((segment / segments, (z_value - z_min) / z_span))
    faces = []
    for segment in range(segments):
        nxt = (segment + 1) % segments
        for profile_index in range(count):
            profile_next = (profile_index + 1) % count
            faces.append((
                segment * count + profile_index,
                nxt * count + profile_index,
                nxt * count + profile_next,
                segment * count + profile_next,
            ))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="ProfileUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def extrude_closed_profile(name, profile, *, depth, collection=None):
    """Create one editable prism from an authored closed X/Z outline.

    This is the non-radial counterpart to :func:`revolve_closed_profile` and
    corresponds to tracing a measured outline in Edit Mode and extruding it
    along local Y.  It is deliberately generic: callers supply only their own
    measured profile points and depth; it contains no asset-specific shape
    knowledge or source topology.

    Side walls are quads.  The two planar caps are n-gons when a profile has
    more than four sides, which is an explicit starting-cage trade-off rather
    than a claim of all-quad SubD-ready topology.  A caller that needs a
    subdivided cap must add its own local loops/insets before surface work.
    """
    if len(profile) < 3 or any(not isinstance(point, (list, tuple)) or len(point) != 2 for point in profile):
        raise ValueError("closed extrusion profile needs at least three [x, z] points")
    if not isinstance(depth, (int, float)) or isinstance(depth, bool) or float(depth) <= 0:
        raise ValueError("profile extrusion depth must be positive")
    points = [(float(point[0]), float(point[1])) for point in profile]
    if len(set(points)) != len(points):
        raise ValueError("closed extrusion profile points must be unique")

    half_depth = float(depth) / 2.0
    count = len(points)
    vertices = [(x, -half_depth, z) for x, z in points] + [(x, half_depth, z) for x, z in points]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, count + next_index, count + index))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="ProfileUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            x, _, z = vertices[vertex_index]
            uv_layer.data[loop_index].uv = (x, z)
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def loft_closed_profiles(name, front_profile, rear_profile, *, depth, collection=None):
    """Create a connected shell between two authored X/Z outline loops.

    The two loops have matching vertex order and are placed at opposite Y
    positions.  This is the generic Edit Mode equivalent of creating a second
    profile and bridging corresponding boundary loops; it supports an A-frame,
    taper, or changing front/rear silhouette without fragmenting the asset into
    object primitives.  It does not choose either profile for the caller.

    The bridge wall is all quads.  The front/rear caps retain the same explicit
    n-gon caveat as :func:`extrude_closed_profile` and must be locally resolved
    before a SubD surface workflow where those caps matter.
    """
    if not isinstance(depth, (int, float)) or isinstance(depth, bool) or float(depth) <= 0:
        raise ValueError("profile loft depth must be positive")
    if len(front_profile) < 3 or len(front_profile) != len(rear_profile):
        raise ValueError("profile loft needs equal-length front and rear profiles with at least three points")
    profiles = []
    for label, raw_profile in (("front", front_profile), ("rear", rear_profile)):
        if any(not isinstance(point, (list, tuple)) or len(point) != 2 for point in raw_profile):
            raise ValueError(f"{label} loft profile points must be [x, z] pairs")
        profile = [(float(point[0]), float(point[1])) for point in raw_profile]
        if len(set(profile)) != len(profile):
            raise ValueError(f"{label} loft profile points must be unique")
        profiles.append(profile)
    front, rear = profiles
    count = len(front)
    half_depth = float(depth) / 2.0
    vertices = [(x, -half_depth, z) for x, z in front] + [(x, half_depth, z) for x, z in rear]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, count + next_index, count + index))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.uv_layers.new(name="ProfileLoftUV")
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def quad_shell_from_grids(name, front_grid, rear_grid, active_cells, *, collection=None):
    """Build one closed all-quad shell from two authored control grids.

    ``front_grid`` and ``rear_grid`` are matching row-major 3D point grids;
    ``active_cells`` says which grid cells are material.  Omitted cells become
    genuine openings and their boundary is bridged between the grids, so a
    U-opening, vent, or handle aperture remains part of one manifold cage.
    This is a typed, general representation of a modeler's manual quad layout,
    not an asset-specific generator and not a source-mesh import path.
    """
    def validate_grid(label, grid):
        if not isinstance(grid, (list, tuple)) or len(grid) < 2:
            raise ValueError(f"{label} grid needs at least two rows")
        width = len(grid[0]) if isinstance(grid[0], (list, tuple)) else 0
        if width < 2 or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
            raise ValueError(f"{label} grid rows must have one shared width of at least two")
        normalized = []
        for row in grid:
            normalized_row = []
            for point in row:
                if not isinstance(point, (list, tuple)) or len(point) != 3:
                    raise ValueError(f"{label} grid points must be [x, y, z] values")
                normalized_row.append(tuple(float(value) for value in point))
            normalized.append(normalized_row)
        return normalized

    front = validate_grid("front", front_grid)
    rear = validate_grid("rear", rear_grid)
    rows, columns = len(front), len(front[0])
    if len(rear) != rows or len(rear[0]) != columns:
        raise ValueError("front and rear quad grids must have matching row and column counts")
    if (
        not isinstance(active_cells, (list, tuple))
        or len(active_cells) != rows - 1
        or any(not isinstance(row, (list, tuple)) or len(row) != columns - 1 for row in active_cells)
    ):
        raise ValueError("active_cells must have one boolean row/column less than the point grids")
    cells = [[bool(value) for value in row] for row in active_cells]
    if not any(value for row in cells for value in row):
        raise ValueError("quad shell needs at least one active cell")

    def node(row, column):
        return row * columns + column

    used_nodes = set()
    for row in range(rows - 1):
        for column in range(columns - 1):
            if cells[row][column]:
                used_nodes.update((node(row, column), node(row, column + 1), node(row + 1, column + 1), node(row + 1, column)))
    ordered_nodes = sorted(used_nodes)
    front_index = {key: index for index, key in enumerate(ordered_nodes)}
    rear_index = {key: index + len(ordered_nodes) for index, key in enumerate(ordered_nodes)}
    vertices = []
    for key in ordered_nodes:
        row, column = divmod(key, columns)
        vertices.append(front[row][column])
    for key in ordered_nodes:
        row, column = divmod(key, columns)
        vertices.append(rear[row][column])

    faces = []
    edge_counts = {}
    for row in range(rows - 1):
        for column in range(columns - 1):
            if not cells[row][column]:
                continue
            ring = (node(row, column), node(row, column + 1), node(row + 1, column + 1), node(row + 1, column))
            faces.append(tuple(front_index[key] for key in ring))
            faces.append(tuple(rear_index[key] for key in reversed(ring)))
            for first, second in zip(ring, ring[1:] + ring[:1]):
                edge = tuple(sorted((first, second)))
                edge_counts[edge] = edge_counts.get(edge, 0) + 1
    for first, second in sorted(edge for edge, count in edge_counts.items() if count == 1):
        faces.append((front_index[first], front_index[second], rear_index[second], rear_index[first]))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.uv_layers.new(name="QuadShellUV")
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def capped_cylinder(name, *, radius, z_bottom, z_top, segments=64, collection=None):
    """Create a manifold capped cylinder from explicit vertices and triangles."""
    if radius <= 0 or z_top <= z_bottom:
        raise ValueError("cylinder needs positive radius and z_top > z_bottom")
    vertices = []
    for z_value in (z_bottom, z_top):
        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z_value))
    vertices.extend(((0.0, 0.0, z_bottom), (0.0, 0.0, z_top)))
    bottom_center, top_center = 2 * segments, 2 * segments + 1
    faces = []
    for segment in range(segments):
        nxt = (segment + 1) % segments
        faces.append((segment, nxt, segments + nxt, segments + segment))
        faces.append((bottom_center, nxt, segment))
        faces.append((top_center, segments + segment, segments + nxt))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.uv_layers.new(name="GeneratedUV")
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj
