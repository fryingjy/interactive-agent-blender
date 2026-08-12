"""Fresh-process verifier for the held-out metal watering-can candidate."""
from __future__ import annotations
import json, sys
from pathlib import Path
import bmesh, bpy

def health(ob, evaluated=False):
    owner=None; mesh=ob.data
    if evaluated: owner=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=owner.to_mesh()
    bm=bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table(); unseen=set(bm.verts); components=0
    while unseen:
        components+=1; stack=[unseen.pop()]
        while stack:
            vertex=stack.pop()
            for edge in vertex.link_edges:
                other=edge.other_vert(vertex)
                if other in unseen: unseen.remove(other); stack.append(other)
    result={'vertices':len(bm.verts),'faces':len(bm.faces),'quads':sum(len(face.verts)==4 for face in bm.faces),'components':components,'non_manifold':sum(not edge.is_manifold for edge in bm.edges),'degenerate':sum(face.calc_area()<1e-10 for face in bm.faces)}
    bm.free()
    if owner: owner.to_mesh_clear()
    return result

def main():
    values=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(values)!=2: raise SystemExit('expected BLEND REPORT after --')
    blend, report=map(lambda value: Path(value).resolve(),values); bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes={obj.name:obj for obj in bpy.data.objects if obj.type=='MESH'}; required=('Connected_Vessel','Connected_Tapered_Spout','Rose_Head','Arched_Handle','Opening_Rim','Opening_Shadow')
    states={name:{'base':health(meshes[name]),'evaluated':health(meshes[name],True)} for name in required if name in meshes}; body=meshes.get('Connected_Vessel'); spout=meshes.get('Connected_Tapered_Spout'); handle=meshes.get('Arched_Handle')
    assertions={'required_meshes_exist':all(name in meshes for name in required),'source_geometry_absent':not any('watering_can_metal_01' in obj.name.lower() for obj in bpy.data.objects),'body_one_component_all_quad_closed':bool(body) and states[body.name]['base']['components']==1 and states[body.name]['base']['faces']==states[body.name]['base']['quads'] and states[body.name]['base']['non_manifold']==0,'spout_one_component_all_quad_closed':bool(spout) and states[spout.name]['base']['components']==1 and states[spout.name]['base']['faces']==states[spout.name]['base']['quads'] and states[spout.name]['base']['non_manifold']==0,'handle_one_component_all_quad_closed':bool(handle) and states[handle.name]['base']['components']==1 and states[handle.name]['base']['faces']==states[handle.name]['base']['quads'] and states[handle.name]['base']['non_manifold']==0,'sparse_radial_cages':bool(body and spout) and body.get('radial_vertices')==16 and spout.get('radial_vertices')==12,'weighted_body_bevel_complete':bool(body) and body.get('intended_sharp_edge_count')==body.get('weighted_bevel_edges')>0,'all_meshes_uv_material':all(obj.data.uv_layers and obj.data.materials and all(material and material.use_nodes for material in obj.data.materials) for obj in meshes.values()),'evaluated_meshes_closed_nondegenerate':all(state['evaluated']['non_manifold']==0 and state['evaluated']['degenerate']==0 for state in states.values())}
    result={'blend':str(blend),'blender_version':bpy.app.version_string,'states':states,'assertions':assertions,'pass':all(assertions.values())}; report.parent.mkdir(parents=True,exist_ok=True); report.write_text(json.dumps(result,indent=2),encoding='utf8'); print(json.dumps(result)); raise SystemExit(0 if result['pass'] else 2)
main()
