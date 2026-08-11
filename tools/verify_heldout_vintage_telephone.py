"""Fresh-process verifier for the held-out vintage telephone candidate."""
from __future__ import annotations
import json,sys
from pathlib import Path
import bmesh,bpy

def args():
 v=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if len(v)!=2: raise SystemExit('expected BLEND REPORT after --')
 return Path(v[0]).resolve(),Path(v[1]).resolve()

def health(ob,evaluated=False):
 owner=None; me=ob.data
 if evaluated: owner=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=owner.to_mesh()
 bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); unseen=set(bm.verts); comps=0
 while unseen:
  comps+=1; stack=[unseen.pop()]
  while stack:
   x=stack.pop()
   for e in x.link_edges:
    y=e.other_vert(x)
    if y in unseen: unseen.remove(y); stack.append(y)
 d={'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),'triangles':sum(len(f.verts)==3 for f in bm.faces),'ngons':sum(len(f.verts)>4 for f in bm.faces),'components':comps,'non_manifold':sum(not e.is_manifold for e in bm.edges),'degenerate':sum(f.calc_area()<1e-10 for f in bm.faces),'loose':sum(not v.link_edges for v in bm.verts)}
 bm.free()
 if owner: owner.to_mesh_clear()
 return d

def main():
 blend,report=args(); bpy.ops.wm.open_mainfile(filepath=str(blend)); meshes=[o for o in bpy.data.objects if o.type=='MESH']; curves=[o for o in bpy.data.objects if o.type=='CURVE']; by={o.name:o for o in meshes}; required=('Main_Housing','Handset','Upper_Face_Trim','Lower_Panel_Trim','Dial_Bezel','Clock_Face','Hour_Hand','Minute_Hand','Cradle_Left','Cradle_Right','Top_Latch')
 states={o.name:{'base':health(o),'evaluated':health(o,True)} for o in meshes}; body=by['Main_Housing']; handset=by['Handset']; apertures=[o for o in meshes if o.name.startswith('Dial_Aperture')]
 assertions={
  'all_required_objects_exist':all(n in by for n in required),
  'source_geometry_absent':not any('vintage_telephone_wall_clock' in o.name.lower() for o in bpy.data.objects),
  'housing_base_one_component_all_quad_closed':states['Main_Housing']['base']['components']==1 and states['Main_Housing']['base']['faces']==states['Main_Housing']['base']['quads'] and states['Main_Housing']['base']['non_manifold']==0,
  'housing_evaluated_one_component_all_quad_closed':states['Main_Housing']['evaluated']['components']==1 and states['Main_Housing']['evaluated']['faces']==states['Main_Housing']['evaluated']['quads'] and states['Main_Housing']['evaluated']['non_manifold']==0,
  'handset_base_one_component_all_quad_closed':states['Handset']['base']['components']==1 and states['Handset']['base']['faces']==states['Handset']['base']['quads'] and states['Handset']['base']['non_manifold']==0,
  'handset_evaluated_one_component_all_quad_closed':states['Handset']['evaluated']['components']==1 and states['Handset']['evaluated']['faces']==states['Handset']['evaluated']['quads'] and states['Handset']['evaluated']['non_manifold']==0,
  'all_meshes_closed_nondegenerate':all(s['base']['non_manifold']==0 and s['base']['degenerate']==0 and s['base']['loose']==0 and s['evaluated']['non_manifold']==0 and s['evaluated']['degenerate']==0 for s in states.values()),
  'housing_modifier_order_bevel_then_subd':[m.type for m in body.modifiers][:2]==['BEVEL','SUBSURF'],
  'housing_weight_map_complete':body.get('intended_sharp_edge_count',0)==body.get('weighted_bevel_edges',-1)>0 and sum(x.value>.999 for x in body.data.attributes['bevel_weight_edge'].data)==body['weighted_bevel_edges'],
  'handset_one_subd_cage':[m.type for m in handset.modifiers]==['SUBSURF'] and handset.get('radial_vertices')==12,
  'twelve_linked_apertures':len(apertures)==12 and len({o.data.as_pointer() for o in apertures})==1 and len({tuple(round(v,5) for v in o.location) for o in apertures})==12,
  'mirrored_cradles_share_data':by['Cradle_Left'].data==by['Cradle_Right'].data and by['Cradle_Right'].scale.x==-1,
  'all_meshes_have_uv_and_node_material':all(o.data.uv_layers and o.data.materials and all(m and m.use_nodes for m in o.data.materials) for o in meshes),
  'three_editable_curve_assemblies':len(curves)==3 and {o.name for o in curves}=={'Handset_Cord','Cradle_Rod_Left','Cradle_Rod_Right'},
  'no_primary_primitive_operator_claim':body.get('primitive_operators_used')==0 and handset.get('primitive_operators_used')==0,
 }
 result={'blend':str(blend),'blender_version':bpy.app.version_string,'mesh_count':len(meshes),'curve_count':len(curves),'states':states,'assertions':assertions,'pass':all(assertions.values())}; report.parent.mkdir(parents=True,exist_ok=True); report.write_text(json.dumps(result,indent=2),encoding='utf8'); print('VERIFY_TELEPHONE:'+json.dumps(result));
 if not result['pass']: raise SystemExit(2)
main()
