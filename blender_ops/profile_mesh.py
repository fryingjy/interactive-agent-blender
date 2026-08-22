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


def quad_shell_from_sections(name, section_grids, active_cells, *, collection=None):
    """Build one closed all-quad shell through authored depth sections.

    Each entry in ``section_grids`` is a matching X/Z control grid at a chosen
    depth.  Unlike a two-grid shell, intermediate sections explicitly control
    the side/top/bottom transitions, so a folded or rolled manufactured form
    can be matched without turning it into a stack of separate primitives.
    Active cells remain the sole description of material: false cells create
    real openings that are bridged around their boundary through every section.
    """
    if not isinstance(section_grids, (list, tuple)) or len(section_grids) < 2:
        raise ValueError("quad shell sections need at least two matching grids")

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

    sections = [validate_grid(f"section {index}", grid) for index, grid in enumerate(section_grids)]
    rows, columns = len(sections[0]), len(sections[0][0])
    if any(len(grid) != rows or len(grid[0]) != columns for grid in sections[1:]):
        raise ValueError("quad shell section grids must have matching row and column counts")
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
    edge_counts = {}
    active_rings = []
    for row in range(rows - 1):
        for column in range(columns - 1):
            if not cells[row][column]:
                continue
            ring = (node(row, column), node(row, column + 1), node(row + 1, column + 1), node(row + 1, column))
            active_rings.append(ring)
            used_nodes.update(ring)
            for first, second in zip(ring, ring[1:] + ring[:1]):
                edge = tuple(sorted((first, second)))
                edge_counts[edge] = edge_counts.get(edge, 0) + 1
    boundary_edges = sorted(edge for edge, count in edge_counts.items() if count == 1)
    boundary_nodes = {key for edge in boundary_edges for key in edge}
    # Only the outer surface boundary travels through intermediate sections.
    # Adding every grid point at every intermediate depth would create loose
    # interior vertices because those points have no surface face to own them.
    section_nodes = [
        sorted(used_nodes if index in {0, len(sections) - 1} else boundary_nodes)
        for index in range(len(sections))
    ]
    index_for = []
    vertices = []
    for section_index, nodes in enumerate(section_nodes):
        index_for.append({key: len(vertices) + index for index, key in enumerate(nodes)})
        for key in nodes:
            row, column = divmod(key, columns)
            vertices.append(sections[section_index][row][column])

    def vertex(section_index, key):
        return index_for[section_index][key]

    faces = []
    for ring in active_rings:
        faces.append(tuple(vertex(0, key) for key in ring))
        faces.append(tuple(vertex(len(sections) - 1, key) for key in reversed(ring)))
    for section_index in range(len(sections) - 1):
        for first, second in boundary_edges:
            faces.append((
                vertex(section_index, first), vertex(section_index, second),
                vertex(section_index + 1, second), vertex(section_index + 1, first),
            ))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.uv_layers.new(name="QuadShellSectionUV")
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def quad_open_surface_from_grids(name, front_grid, rear_grid, active_cells, bridge_edges, *, collection=None):
    """Create one connected, open all-quad surface from authored grids.

    ``bridge_edges`` contains only the physical boundaries that continue from
    front to rear, as ``[row_a, column_a, row_b, column_b]`` entries.  Other
    boundaries intentionally remain open for a later live Solidify modifier.
    This avoids falsely sealing folded products such as open A-frame shells.
    """
    def normalize(label, grid):
        if not isinstance(grid, (list, tuple)) or len(grid) < 2 or not isinstance(grid[0], (list, tuple)) or len(grid[0]) < 2:
            raise ValueError(f"{label} grid needs at least two rows and columns")
        columns = len(grid[0])
        if any(not isinstance(row, (list, tuple)) or len(row) != columns for row in grid):
            raise ValueError(f"{label} grid rows must share one width")
        return [[tuple(float(value) for value in point) for point in row] for row in grid]

    front, rear = normalize("front", front_grid), normalize("rear", rear_grid)
    rows, columns = len(front), len(front[0])
    if len(rear) != rows or len(rear[0]) != columns:
        raise ValueError("open surface grids must have matching dimensions")
    if len(active_cells) != rows - 1 or any(len(row) != columns - 1 for row in active_cells):
        raise ValueError("active_cells must be one row and column smaller than the grids")
    cells = [[bool(value) for value in row] for row in active_cells]
    if not any(value for row in cells for value in row):
        raise ValueError("open surface needs an active cell")

    def node(row, column): return row * columns + column
    used, rings = set(), []
    for row in range(rows - 1):
        for column in range(columns - 1):
            if cells[row][column]:
                ring = (node(row, column), node(row, column + 1), node(row + 1, column + 1), node(row + 1, column))
                rings.append(ring); used.update(ring)
    ordered = sorted(used)
    front_index = {key: index for index, key in enumerate(ordered)}
    rear_index = {key: index + len(ordered) for index, key in enumerate(ordered)}
    vertices = [front[row][column] for key in ordered for row, column in [divmod(key, columns)]] + [rear[row][column] for key in ordered for row, column in [divmod(key, columns)]]
    faces = [tuple(front_index[key] for key in ring) for ring in rings] + [tuple(rear_index[key] for key in reversed(ring)) for ring in rings]
    for edge in bridge_edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 4:
            raise ValueError("bridge_edges entries must be [row_a, column_a, row_b, column_b]")
        first, second = node(int(edge[0]), int(edge[1])), node(int(edge[2]), int(edge[3]))
        if first not in used or second not in used:
            raise ValueError("bridge edge must use active grid nodes")
        faces.append((front_index[first], front_index[second], rear_index[second], rear_index[first]))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces); mesh.update()
    mesh.uv_layers.new(name="QuadOpenSurfaceUV")
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def quad_annular_shell_from_loops(
    name,
    front_outer,
    front_inner,
    rear_outer,
    rear_inner,
    *,
    collection=None,
):
    """Bridge matched outer/inner loops into one closed all-quad annular shell.

    The four loops are authored 3D point sequences with identical count and
    correspondence.  This is the generic equivalent of bridging an opening
    into a curved host in Edit Mode: front and rear annuli provide the broad
    surfaces, while the outer and inner walls close both boundaries.  It is
    useful for bezels, trackpad recess patches, handle apertures, and other
    continuous surfaces where a separate ring primitive would destroy the
    construction relationship.
    """

    def normalize(label, loop):
        if not isinstance(loop, (list, tuple)) or len(loop) < 3:
            raise ValueError(f"{label} needs at least three points")
        points = []
        for point in loop:
            if not isinstance(point, (list, tuple)) or len(point) != 3:
                raise ValueError(f"{label} points must be [x, y, z]")
            points.append(tuple(float(value) for value in point))
        if len(set(points)) != len(points):
            raise ValueError(f"{label} points must be unique")
        return points

    loops = [
        normalize("front_outer", front_outer),
        normalize("front_inner", front_inner),
        normalize("rear_outer", rear_outer),
        normalize("rear_inner", rear_inner),
    ]
    count = len(loops[0])
    if any(len(loop) != count for loop in loops[1:]):
        raise ValueError("annular shell loops must have matching point counts")

    vertices = [point for loop in loops for point in loop]
    front_outer_offset = 0
    front_inner_offset = count
    rear_outer_offset = count * 2
    rear_inner_offset = count * 3
    faces = []
    for index in range(count):
        nxt = (index + 1) % count
        fo, fon = front_outer_offset + index, front_outer_offset + nxt
        fi, fin = front_inner_offset + index, front_inner_offset + nxt
        ro, ron = rear_outer_offset + index, rear_outer_offset + nxt
        ri, rin = rear_inner_offset + index, rear_inner_offset + nxt
        faces.extend((
            (fo, fon, fin, fi),
            (ro, ri, rin, ron),
            (fo, ro, ron, fon),
            (fi, fin, rin, ri),
        ))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.uv_layers.new(name="QuadAnnularShellUV")
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def quad_layered_annular_shell_from_loops(name, front_loops, rear_loops, *, collection=None):
    """Create a closed all-quad annular shell with authored radial support loops.

    Each side is an outer-to-inner sequence of matched loops. Additional
    radial loops localize SubD support without detaching the opening as a
    separate primitive or uniformly subdividing the whole host surface.
    """

    def normalize_side(label, side):
        if not isinstance(side, (list, tuple)) or len(side) < 2:
            raise ValueError(f"{label} needs at least outer and inner loops")
        normalized = []
        for loop_index, loop in enumerate(side):
            if not isinstance(loop, (list, tuple)) or len(loop) < 3:
                raise ValueError(f"{label}[{loop_index}] needs at least three points")
            points = []
            for point in loop:
                if not isinstance(point, (list, tuple)) or len(point) != 3:
                    raise ValueError(f"{label}[{loop_index}] points must be [x, y, z]")
                points.append(tuple(float(value) for value in point))
            if len(set(points)) != len(points):
                raise ValueError(f"{label}[{loop_index}] points must be unique")
            normalized.append(points)
        return normalized

    front = normalize_side("front_loops", front_loops)
    rear = normalize_side("rear_loops", rear_loops)
    if len(front) != len(rear):
        raise ValueError("front_loops and rear_loops must have the same radial loop count")
    point_count = len(front[0])
    if any(len(loop) != point_count for loop in front + rear):
        raise ValueError("all layered annular loops must have matching point counts")

    radial_count = len(front)
    loops = front + rear
    vertices = [point for loop in loops for point in loop]
    faces = []

    def vertex(side_offset, radial_index, point_index):
        return (side_offset + radial_index) * point_count + point_index

    for radial_index in range(radial_count - 1):
        for point_index in range(point_count):
            nxt = (point_index + 1) % point_count
            faces.append((
                vertex(0, radial_index, point_index), vertex(0, radial_index, nxt),
                vertex(0, radial_index + 1, nxt), vertex(0, radial_index + 1, point_index),
            ))
            faces.append((
                vertex(radial_count, radial_index, point_index), vertex(radial_count, radial_index + 1, point_index),
                vertex(radial_count, radial_index + 1, nxt), vertex(radial_count, radial_index, nxt),
            ))

    for radial_index in (0, radial_count - 1):
        for point_index in range(point_count):
            nxt = (point_index + 1) % point_count
            quad = (
                vertex(0, radial_index, point_index), vertex(radial_count, radial_index, point_index),
                vertex(radial_count, radial_index, nxt), vertex(0, radial_index, nxt),
            )
            faces.append(tuple(reversed(quad)) if radial_index == radial_count - 1 else quad)

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.uv_layers.new(name="QuadLayeredAnnularShellUV")
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
