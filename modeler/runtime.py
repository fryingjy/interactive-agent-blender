"""Small Blender-native mesh editor; run only inside Blender.

Indices are snapshot-local, never persistent identifiers. Each edit must name
the exact fingerprint returned by inspect(). Rollback owns only mesh data;
operations that mutate modifiers, objects, or collections are not exposed yet.
"""
import hashlib
import json
import math

import bmesh
import bpy
from mathutils import Vector


def mesh_object(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != 'MESH':
        raise ValueError('Expected a named mesh object')
    if obj.mode != 'OBJECT' or obj.data.users != 1 or obj.data.shape_keys:
        raise ValueError('Requires object mode, single-user mesh, no shape keys')
    return obj


def inspect(name):
    bpy.context.view_layer.update()
    obj = mesh_object(name)
    mesh = obj.data
    geometry = {
        'vertices': [list(v.co) for v in mesh.vertices],
        'edges': [list(e.vertices) for e in mesh.edges],
        'faces': [list(p.vertices) for p in mesh.polygons],
        'matrix_world': [list(row) for row in obj.matrix_world],
        'attributes': {},
    }
    # Include numerical mesh attributes, including crease/bevel weights and UVs.
    for attr in mesh.attributes:
        values = []
        for item in attr.data:
            value = next((getattr(item, key) for key in
                          ('value', 'vector', 'color') if hasattr(item, key)), None)
            values.append(value if value is None or isinstance(value, (str, int, float, bool))
                          else list(value))
        geometry['attributes'][attr.name] = [attr.domain, attr.data_type, values]
    modifiers = []
    for modifier in obj.modifiers:
        fields = {'type': modifier.type}
        for prop in modifier.bl_rna.properties:
            if not prop.is_readonly and prop.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
                value = getattr(modifier, prop.identifier)
                fields[prop.identifier] = (sorted(value) if isinstance(value, set) else
                                           list(value) if getattr(prop, 'is_array', False) else value)
        modifiers.append(fields)
    geometry['modifiers'] = modifiers
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        unseen = set(bm.verts)
        components = 0
        while unseen:
            components += 1
            queue = [unseen.pop()]
            while queue:
                for edge in queue.pop().link_edges:
                    for vertex in edge.verts:
                        if vertex in unseen:
                            unseen.remove(vertex)
                            queue.append(vertex)
        health = {'components': components,
                  'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
                  'degenerate_faces': sum(f.calc_area() < 1e-12 for f in bm.faces)}
    finally:
        bm.free()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    result = evaluated.to_mesh()
    try:
        evaluated_counts = {'vertices': len(result.vertices), 'faces': len(result.polygons)}
    finally:
        evaluated.to_mesh_clear()
    return {'object': name, 'fingerprint': hashlib.sha256(json.dumps(
        geometry, sort_keys=True, allow_nan=False).encode()).hexdigest(),
        'geometry': geometry, 'health': health, 'evaluated_counts': evaluated_counts,
        'quality_accepted': False}


def vector(value):
    if (not isinstance(value, list) or len(value) != 3 or
            any(type(x) not in (int, float) or not math.isfinite(x) for x in value)):
        raise ValueError('Expected three finite coordinates')
    return Vector(value)


def indices(value, count):
    if (not isinstance(value, list) or not value or len(set(value)) != len(value)
            or any(type(i) is not int or not 0 <= i < count for i in value)):
        raise ValueError('Invalid or duplicate snapshot indices')
    return value


def edit(request):
    name = request['object']
    before = inspect(name)
    if request.get('expected_fingerprint') != before['fingerprint']:
        raise ValueError('Stale or missing fingerprint; inspect before editing')
    action = request['action']
    allowed = {'extrude_face': {'face', 'delta'}, 'move_vertices': {'vertices', 'delta'}}
    if action not in allowed or set(request) != allowed[action] | {
            'object', 'action', 'expected_fingerprint'}:
        raise ValueError('Unknown action or unexpected request fields')
    delta = vector(request['delta'])
    obj = mesh_object(name)
    original = obj.data
    candidate = original.copy()
    bm = bmesh.new()
    try:
        bm.from_mesh(candidate)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        if action == 'extrude_face':
            face = bm.faces[indices([request['face']], len(bm.faces))[0]]
            result = bmesh.ops.extrude_face_region(bm, geom=[face], use_keep_orig=False)
            if face.is_valid:
                bmesh.ops.delete(bm, geom=[face], context='FACES_ONLY')
            verts = [element for element in result['geom'] if isinstance(element, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=verts, vec=delta)
        else:
            verts = [bm.verts[i] for i in indices(request['vertices'], len(bm.verts))]
            bmesh.ops.translate(bm, verts=verts, vec=delta)
        bm.normal_update()
        bm.to_mesh(candidate)
        candidate.update()
        obj.data = candidate
        bpy.context.view_layer.update()
        after = inspect(name)
        # Local safety checks, not a general intersection or artistic validator.
        if (after['health']['components'] != before['health']['components'] or
                after['health']['nonmanifold_edges'] > before['health']['nonmanifold_edges'] or
                after['health']['degenerate_faces'] > before['health']['degenerate_faces']):
            raise ValueError('Edit introduced a connectivity or degeneracy defect')
    except Exception:
        obj.data = original
        bpy.data.meshes.remove(candidate)
        bpy.context.view_layer.update()
        raise
    finally:
        bm.free()
    bpy.data.meshes.remove(original)
    candidate.name = name + '_Mesh'
    return {'execution_succeeded': True, 'before': before, 'after': after,
            'quality_accepted': False}
