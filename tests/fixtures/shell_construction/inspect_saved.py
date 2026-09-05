"""Read-only neutral shell-drill inspection in fresh Blender.

Arguments after --: saved.blend object_name output.json
No runtime imports; never modifies or saves the source asset.
"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend, name, output = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()), load_ui=False)
obj = bpy.data.objects[name]
evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
bm = bmesh.new()
bm.from_mesh(mesh)
bvh = BVHTree.FromBMesh(bm)


def ray(origin, direction):
    location, normal, face, distance = bvh.ray_cast(Vector(origin), Vector(direction))
    return list(location) if location is not None else None


floor = ray((0, 0, 2), (0, 0, -1))
bottom = ray((0, 0, -2), (0, 0, 1))
radii = []
for degrees in range(360):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    hit = ray((3*c, 3*s, 0), (-c, -s, 0))
    if hit:
        radii.append(math.hypot(hit[0], hit[1]))
coords = [v.co for v in mesh.vertices]
dimensions = [max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3)]
base_bm = bmesh.new()
base_bm.from_mesh(obj.data)
remaining = set(base_bm.verts)
components = 0
while remaining:
    components += 1
    pending = [remaining.pop()]
    while pending:
        for edge in pending.pop().link_edges:
            for vertex in edge.verts:
                if vertex in remaining:
                    remaining.remove(vertex)
                    pending.append(vertex)
record = {
    'scope': 'Neutral construction drill, not reference fidelity or independent visual review',
    'blender_version': bpy.app.version_string,
    'blend': str(Path(blend).resolve()), 'object': name,
    'base': {'vertices': len(obj.data.vertices), 'faces': len(obj.data.polygons),
             'ngons': sum(len(p.vertices)>4 for p in obj.data.polygons),
             'connected_components': components},
    'evaluated': {'vertices': len(mesh.vertices), 'faces': len(mesh.polygons),
                  'non_manifold_edges': sum(not e.is_manifold for e in bm.edges),
                  'dimensions': dimensions},
    'floor_hit': floor, 'underside_hit': bottom,
    'center_floor_thickness': floor[2]-bottom[2] if floor and bottom else None,
    'center_cavity_depth': max(v.z for v in coords)-floor[2] if floor else None,
    'radial_midheight': {'samples': len(radii), 'min': min(radii) if radii else None,
                         'max': max(radii) if radii else None,
                         'peak_to_peak': max(radii)-min(radii) if radii else None},
    'modifiers': [{'name': m.name, 'type': m.type, 'viewport': m.show_viewport,
                   'render': m.show_render} for m in obj.modifiers],
    'collections': [c.name for c in obj.users_collection],
}
base_bm.free()
bm.free()
evaluated.to_mesh_clear()
Path(output).parent.mkdir(parents=True, exist_ok=True)
Path(output).write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record))
