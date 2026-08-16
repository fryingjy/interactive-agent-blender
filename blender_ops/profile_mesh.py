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
