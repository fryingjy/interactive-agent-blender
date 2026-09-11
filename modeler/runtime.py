"""Small Blender-native mesh editor; run only inside Blender.

Indices are snapshot-local, never persistent identifiers. Each edit must name
the exact fingerprint returned by inspect(). Mesh edits own mesh-data rollback.
The separate subdivision operation owns one named modifier's settings. Arbitrary
object, collection, material, and modifier mutations are not exposed.
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
        'geometry': geometry, 'health': health,
        'topology': {'triangles': sum(len(f)==3 for f in geometry['faces']),
                     'quads': sum(len(f)==4 for f in geometry['faces']),
                     'ngons': sum(len(f)>4 for f in geometry['faces'])},
        'evaluated_counts': evaluated_counts,
        'quality_accepted': False}


def vector(value):
    if (not isinstance(value, list) or len(value) != 3 or
            any(type(x) not in (int, float) or not math.isfinite(x) for x in value)):
        raise ValueError('Expected three finite coordinates')
    return Vector(value)


def indices(value, count):
    if (not isinstance(value, list) or not value
            or any(type(i) is not int or not 0 <= i < count for i in value)
            or len(set(value)) != len(value)):
        raise ValueError('Invalid or duplicate snapshot indices')
    return value


def edit(request):
    name = request['object']
    before = inspect(name)
    if request.get('expected_fingerprint') != before['fingerprint']:
        raise ValueError('Stale or missing fingerprint; inspect before editing')
    action = request['action']
    allowed = {'extrude_face': {'face', 'delta'}, 'move_vertices': {'vertices', 'delta'},
               'subdivide_edges': {'edges', 'cuts'}, 'set_vertex_positions': {'positions'},
               'inset_region': {'faces', 'thickness', 'depth'},
               'set_edge_crease': {'edges', 'weight'},
               'set_vertex_crease': {'vertices', 'weight'},
               'set_face_smoothing': {'faces', 'smooth'}}
    if action not in allowed or set(request) != allowed[action] | {
            'object', 'action', 'expected_fingerprint'}:
        raise ValueError('Unknown action or unexpected request fields')
    delta = vector(request['delta']) if 'delta' in request else None
    obj = mesh_object(name)
    original = obj.data
    candidate = original.copy()
    bm = bmesh.new()
    try:
        bm.from_mesh(candidate)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        if action == 'extrude_face':
            face = bm.faces[indices([request['face']], len(bm.faces))[0]]
            result = bmesh.ops.extrude_face_region(bm, geom=[face], use_keep_orig=False)
            if face.is_valid:
                bmesh.ops.delete(bm, geom=[face], context='FACES_ONLY')
            verts = [element for element in result['geom'] if isinstance(element, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=verts, vec=delta)
        elif action == 'move_vertices':
            verts = [bm.verts[i] for i in indices(request['vertices'], len(bm.verts))]
            bmesh.ops.translate(bm, verts=verts, vec=delta)
        elif action == 'subdivide_edges':
            cuts = request['cuts']
            if type(cuts) is not int or not 1 <= cuts <= 16:
                raise ValueError('Cuts must be an integer from 1 to 16')
            edges = [bm.edges[i] for i in indices(request['edges'], len(bm.edges))]
            bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True)
        elif action == 'set_face_smoothing':
            if type(request['smooth']) is not bool:
                raise ValueError('Smoothing must be boolean')
            for i in indices(request['faces'], len(bm.faces)):
                bm.faces[i].smooth = request['smooth']
        elif action in {'set_edge_crease', 'set_vertex_crease'}:
            weight = request['weight']
            if type(weight) not in (int, float) or not 0 <= weight <= 1:
                raise ValueError('Crease weight must be between zero and one')
            elements = bm.edges if action == 'set_edge_crease' else bm.verts
            key, attribute = ('edges', 'crease_edge') if action == 'set_edge_crease' else ('vertices', 'crease_vert')
            layer = elements.layers.float.get(attribute) or elements.layers.float.new(attribute)
            elements.ensure_lookup_table()
            for i in indices(request[key], len(elements)):
                elements[i][layer] = weight
        elif action == 'inset_region':
            thickness, depth = request['thickness'], request['depth']
            if (type(thickness) not in (int, float) or type(depth) not in (int, float)
                    or not math.isfinite(thickness) or not math.isfinite(depth) or thickness <= 0):
                raise ValueError('Inset needs positive finite thickness and finite depth')
            faces = [bm.faces[i] for i in indices(request['faces'], len(bm.faces))]
            bmesh.ops.inset_region(bm, faces=faces, thickness=thickness, depth=depth,
                                  use_boundary=True, use_even_offset=True)
        else:
            positions = request['positions']
            if (not isinstance(positions, list) or not positions or
                    any(not isinstance(pair, list) or len(pair)!=2 for pair in positions)):
                raise ValueError('Expected vertex/position pairs')
            ids = indices([pair[0] for pair in positions], len(bm.verts))
            coords = [vector(pair[1]) for pair in positions]
            for index, position in zip(ids, coords):
                bm.verts[index].co = position
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
    warnings = []
    if after['topology']['ngons'] > before['topology']['ngons']:
        warnings.append('New n-gons: review topology suitability before continuing')
    return {'execution_succeeded': True, 'before': before, 'after': after, 'warnings': warnings,
            'quality_accepted': False}


def set_subdivision(request):
    """Own only one named live modifier; restore its settings on failure."""
    if (request.get('action') != 'set_subdivision' or
            set(request) != {'action', 'object', 'expected_fingerprint', 'levels'}):
        raise ValueError('Unexpected subdivision fields')
    levels = request['levels']
    if type(levels) is not int or not 0 <= levels <= 3:
        raise ValueError('Subdivision levels must be 0 through 3')
    obj = mesh_object(request['object'])
    before = inspect(obj.name)
    if request['expected_fingerprint'] != before['fingerprint']:
        raise ValueError('Stale fingerprint')
    modifier = obj.modifiers.get('Modeler_Subdivision')
    if modifier and modifier.type != 'SUBSURF':
        raise ValueError('Reserved modifier name has wrong type')
    old = (modifier.levels, modifier.render_levels) if modifier else None
    if modifier is None:
        modifier = obj.modifiers.new('Modeler_Subdivision', 'SUBSURF')
    try:
        modifier.levels = modifier.render_levels = levels
        after = inspect(obj.name)
    except Exception:
        if old is None:
            obj.modifiers.remove(modifier)
        else:
            modifier.levels, modifier.render_levels = old
        raise
    return {'execution_succeeded': True, 'before': before, 'after': after,
            'quality_accepted': False}
