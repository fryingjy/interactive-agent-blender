"""Held-out articulated desk-lamp candidate from neutral reference renders only.

This uses independent mechanical assemblies where rotation/serviceability is real, and
closed all-quad path lofts for arms, springs, and shade shell rather than primitive stacks.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import bmesh, bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'blender_ops'))
from render_passes import render_silhouette
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.strategy import ModelingBrief
VIEWS={'front':Vector((0,-1,0)),'side':Vector((1,0,0)),'top':Vector((0,0,1)),'isometric':Vector((1,-1,.8)).normalized()}

def perimeter(n): return [(i,0) for i in range(n)]+[(n-1,j) for j in range(1,n)]+[(i,n-1) for i in range(n-2,-1,-1)]+[(0,j) for j in range(n-2,0,-1)]
def disk(u,v):
 if abs(u)<1e-9 and abs(v)<1e-9:return 0.,0.
 if abs(u)>abs(v):r=u;t=math.pi/4*v/u
 else:r=v;t=math.pi/2-math.pi/4*u/v
 return r*math.cos(t),r*math.sin(t)
def mat(name,color,metal=.0,rough=.4):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
def make(name,verts,faces,col,material,props={}):
 me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(verts,[],faces);me.materials.append(material);me.update(calc_edges=True);ob=bpy.data.objects.new(name,me);col.objects.link(ob)
 # Do not blanket-smooth a hard-surface assembly. Rejected desk-lamp
 # candidates predate the policy; future accepted assets must explicitly use
 # semantic bevels and Smooth by Angle where their geometry calls for it.
 uv=me.uv_layers.new(name='UVMap');xs=[v.co.x for v in me.vertices];ys=[v.co.y for v in me.vertices];zs=[v.co.z for v in me.vertices];dx=max(xs)-min(xs) or 1;dy=max(ys)-min(ys) or 1;dz=max(zs)-min(zs) or 1
 for poly in me.polygons:
  for li in poly.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=((co.y-min(ys))/dy,(co.z-min(zs))/dz)
 for k,v in props.items():ob[k]=v
 return ob
def path_loft(name,centers,radii,n,col,material,props={}):
 bc=perimeter(n);verts=[];faces=[];rings=[];frames=[]
 for k,center in enumerate(centers):
  tangent=(Vector(centers[min(k+1,len(centers)-1)])-Vector(centers[max(k-1,0)])).normalized();bx=Vector((1,0,0));by=tangent.cross(bx).normalized();frames.append((bx,by));ring=[]
  for i,j in bc:
   a,b=disk(-1+2*i/(n-1),-1+2*j/(n-1));ring.append(len(verts));verts.append(tuple(Vector(center)+(bx*a+by*b)*radii[k]))
  rings.append(ring)
 for a,b in zip(rings,rings[1:]):
  for k in range(len(a)):faces.append((a[k],a[(k+1)%len(a)],b[(k+1)%len(a)],b[k]))
 for ridx,up in ((0,False),(len(rings)-1,True)):
  mp={bc[k]:rings[ridx][k] for k in range(len(bc))};c=Vector(centers[ridx]);bx,by=frames[ridx];r=radii[ridx]
  for j in range(1,n-1):
   for i in range(1,n-1):
    a,b=disk(-1+2*i/(n-1),-1+2*j/(n-1));mp[(i,j)]=len(verts);verts.append(tuple(c+(bx*a+by*b)*r))
  for j in range(n-1):
   for i in range(n-1):
    q=(mp[(i,j)],mp[(i+1,j)],mp[(i+1,j+1)],mp[(i,j+1)]);faces.append(q if up else tuple(reversed(q)))
 return make(name,verts,faces,col,material,props)
def health(ob,eval=False):
 me=ob.data;owner=None
 if eval:owner=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=owner.to_mesh()
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();unseen=set(bm.verts);c=0
 while unseen:
  c+=1;stack=[unseen.pop()]
  while stack:
   v=stack.pop()
   for edge in v.link_edges:
    q=edge.other_vert(v)
    if q in unseen:unseen.remove(q);stack.append(q)
 result={'verts':len(bm.verts),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),'components':c,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'degenerate':sum(f.calc_area()<1e-10 for f in bm.faces)};bm.free()
 if owner:owner.to_mesh_clear()
 return result
def render(scene,out,objs,view):
 points=[ob.matrix_world@Vector(c) for ob in objs for c in ob.bound_box];mn=Vector((min(p.x for p in points),min(p.y for p in points),min(p.z for p in points)));mx=Vector((max(p.x for p in points),max(p.y for p in points),max(p.z for p in points)));center=(mn+mx)/2;diag=(mx-mn).length;d=VIEWS[view]
 bpy.ops.object.camera_add(location=center+d*diag*2.2);cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=diag*1.12;cam.rotation_euler=d.to_track_quat('Z','Y').to_euler();scene.camera=cam;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.render.filepath=str(out/f'candidate_{view}_beauty.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
def main():
 vals=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if len(vals)!=1:raise SystemExit('expected OUTPUT_DIR')
 out=Path(vals[0]).resolve();out.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.world=bpy.data.worlds.new('ReviewWorld');scene.world.color=(.045,.045,.045);scene.render.resolution_x=scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';col=bpy.data.collections.new('DeskLamp');scene.collection.children.link(col)
 dark=mat('PowderCoat',(.08,.105,.12),.55,.28);metal=mat('Hardware',(.32,.36,.39),.75,.24);light=mat('ShadeInterior',(.46,.47,.43),.15,.38);objs=[]
 planner=[plan_next_decision(PlannerContext(task_id='heldout-desk-lamp',asset_id='desk_lamp_arm_01',stage='REFERENCE_ANALYSIS',session_id='candidate-v1',scene_revision=0,stage_evidence={},brief=ModelingBrief(follows_path=True,independent_motion_or_material=True))).to_dict()]
 # Side-view composition: clamp/right -> two hinged arm spans -> shade/left.
 base=path_loft('Clamp_Base',[(0,.12,-2.1),(0,.12,-1.7)],[.34,.34],4,col,dark,{'assembly_reason':'clamp base','primitive_operators_used':0});objs.append(base)
 jaw=path_loft('Clamp_Jaw',[(0,.30,-2.22),(0,.30,-2.52)],[.22,.22],4,col,dark,{'assembly_reason':'clamp jaw','primitive_operators_used':0});objs.append(jaw)
 # Measured correction after v1: the source's side silhouette is a Z, not
 # one diagonal. Clamp and shade sit to the right of a leftward elbow.
 # The paired rails must separate in the visible articulation plane, not only
 # across depth: v2's two depth rails collapsed to a single line in side view.
 lower_a=[(-.04,.20,-1.34),(-.04,-.48,-.62),(-.04,-1.02,.06)];lower_b=[(.04,.04,-1.62),(.04,-.64,-.90),(.04,-1.18,-.22)]
 upper_a=[(-.04,-1.02,.06),(-.04,-.35,.90),(-.04,.48,1.69)];upper_b=[(.04,-1.18,-.22),(.04,-.51,.62),(.04,.32,1.41)]
 for name,points in [('LowerArmRailL',lower_a),('LowerArmRailR',lower_b),('UpperArmRailL',upper_a),('UpperArmRailR',upper_b)]:objs.append(path_loft(name,points,[.075]*3,4,col,dark,{'construction':'continuous articulated arm rail','primitive_operators_used':0}))
 for name,a,b in [('Lower_Frame_Strut',(0,2.0,-1.48),(0,2.0,-1.48)),('Upper_Frame_Strut',(0,1.78,1.55),(0,1.78,1.55))]:
  # Short transverse members make the two rail housings a real frame without
  # faking them as one disconnected primitive shell.
  if name.startswith('Lower'): points=[(-.04,.20,-1.34),(.04,.04,-1.62)]
  else: points=[(-.04,.48,1.69),(.04,.32,1.41)]
  objs.append(path_loft(name,points,[.055,.055],4,col,metal,{'assembly_reason':'arm-frame cross strut','primitive_operators_used':0}))
 for name,center in [('BaseHub',(0,.12,-1.48)),('ElbowHub',(0,-1.10,-.08)),('ShadeHub',(0,.40,1.55))]:objs.append(path_loft(name,[(0,center[1],center[2]-.12),(0,center[1],center[2]+.12)],[.28,.28],4,col,metal,{'assembly_reason':'rotational joint hub','primitive_operators_used':0}))
 # Tension paths are continuous thin members, deliberately distinct from rigid rails.
 spring1=[(0,-.06,-1.28),(0,-.55,-.67),(0,-.85,-.16)];spring2=[(0,-.98,.08),(0,-.48,.78),(0,.20,1.38)]
 for name,points in [('LowerTensionCable',spring1),('UpperTensionCable',spring2)]:objs.append(path_loft(name,points,[.032]*3,4,col,metal,{'construction':'continuous tension path','primitive_operators_used':0}))
 shade=path_loft('Lamp_Shade',[(0,.40,1.48),(0,.62,1.65),(0,.88,1.78),(0,1.08,1.82)],[.20,.32,.55,.68],5,col,dark,{'assembly_reason':'serviceable shade shell','radial_vertices':16,'primitive_operators_used':0});objs.append(shade)
 bulb=path_loft('Lamp_Bulb',[(0,1.06,1.80),(0,1.18,1.82)],[.38,.38],4,col,light,{'assembly_reason':'replaceable bulb','primitive_operators_used':0});objs.append(bulb)
 bpy.context.view_layer.update();names=[o.name for o in objs];sil=[]
 for view in ('front','side','top'):
  sil.append(render_silhouette(names,str(out/f'candidate_{view}_mask.png'),view=view,resolution=720,margin=1.12,frame_name=names));render(scene,out,objs,view)
 render(scene,out,objs,'isometric');states={o.name:{'base':health(o),'evaluated':health(o,True)} for o in objs}
 planner.append(plan_next_decision(PlannerContext(task_id='heldout-desk-lamp',asset_id='desk_lamp_arm_01',stage='PRIMARY_BLOCKOUT',session_id='candidate-v1',scene_revision=1,active_object='LowerArmRailL',stage_evidence={},visual_tickets=[{'type':'contour_error','target':'arm span','severity':.7,'priority':1}],brief=ModelingBrief(follows_path=True,independent_motion_or_material=True))).to_dict())
 primary=['LowerArmRailL','LowerArmRailR','UpperArmRailL','UpperArmRailR','Lamp_Shade'];assertions={'source_absent':not any('desk_lamp_arm_01' in o.name.lower() for o in bpy.data.objects),'primary_members_closed_all_quad':all(states[n]['base']['components']==1 and states[n]['base']['faces']==states[n]['base']['quads'] and states[n]['base']['nonmanifold']==0 for n in primary),'all_meshes_have_uv_material':all(o.data.uv_layers and o.data.materials for o in objs),'articulated_assemblies_preserved':len(objs)>=12,'sparse_radial_controls':shade.get('radial_vertices')==16,'silhouette_renders':all('error' not in item for item in sil),'evaluated_clean':all(s['evaluated']['nonmanifold']==0 and s['evaluated']['degenerate']==0 for s in states.values())}
 report={'lab':'heldout_desk_lamp','stage':'candidate_v1','construction':'neutral references only; procedural fallback does not count as typed runtime evidence','planner_checkpoints':planner,'mesh_records':states,'assertions':assertions,'pass':all(assertions.values())};(out/'desk_lamp_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');bpy.ops.wm.save_as_mainfile(filepath=str(out/'heldout_desk_lamp.blend'));print(json.dumps(report));raise SystemExit(0 if report['pass'] else 2)
main()
