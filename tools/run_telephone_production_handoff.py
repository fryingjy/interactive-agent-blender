"""Add an asset-specific baked badge, wire tangent normals, and export the telephone."""
from __future__ import annotations
import json,sys,math
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]

def args():
 v=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if len(v)!=2: raise SystemExit('expected SOURCE_BLEND OUTPUT_DIR after --')
 o=Path(v[1]).resolve(); o.mkdir(parents=True,exist_ok=True); return Path(v[0]).resolve(),o

def box(name,cx,cy,cz,sx,sy,sz):
 x0,x1=cx-sx/2,cx+sx/2; y0,y1=cy-sy/2,cy+sy/2; z0,z1=cz-sz/2,cz+sz/2
 v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
 f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(v,[],f); me.update(calc_edges=True); ob=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(ob); return ob

def high_badge_relief():
 nx,nz=33,17; verts=[]; faces=[]
 for j in range(nz):
  z=-1.92+.28*j/(nz-1)
  for i in range(nx):
   x=-.55+1.10*i/(nx-1)
   bar=max(0.0,1.0-abs(x)/.065)*max(0.0,1.0-abs(z+1.78)/.105)
   side=max(0.0,1.0-abs(abs(x)-.28)/.055)*max(0.0,1.0-abs(z+1.78)/.075)
   riv=max(max(0.0,1.0-math.hypot(x+.46,z+1.78)/.07),max(0.0,1.0-math.hypot(x-.46,z+1.78)/.07))
   disp=.070*max(bar,side,.8*riv)
   verts.append((x,-.844-disp,z))
 for j in range(nz-1):
  for i in range(nx-1):
   a=j*nx+i; faces.append((a,a+1,a+1+nx,a+nx))
 me=bpy.data.meshes.new('BadgeHigh_ReliefMesh'); me.from_pydata(verts,[],faces); me.update(calc_edges=True); ob=bpy.data.objects.new('BadgeHigh_Relief',me); bpy.context.scene.collection.objects.link(ob)
 for p in me.polygons: p.use_smooth=True
 return ob

def activate(active,include=()):
 bpy.ops.object.select_all(action='DESELECT')
 for o in include: o.hide_set(False); o.select_set(True)
 active.hide_set(False); active.select_set(True); bpy.context.view_layer.objects.active=active

def metrics(image):
 px=list(image.pixels); samples=[px[i:i+4] for i in range(0,len(px),4)]; neutral=(.5,.5,1.0)
 return {'size':list(image.size),'non_neutral_pixels':sum(max(abs(p[k]-neutral[k]) for k in range(3))>.035 for p in samples),'channel_min':[min(p[k] for p in samples) for k in range(3)],'channel_max':[max(p[k] for p in samples) for k in range(3)]}

def main():
 source,out=args(); bpy.ops.wm.open_mainfile(filepath=str(source)); scene=bpy.context.scene
 low=box('Telephone_Baked_Badge',0,-.815,-1.78,1.10,.055,.28)
 # Authored UVs through deterministic projection on this production insert.
 activate(low); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.04); bpy.ops.object.mode_set(mode='OBJECT')
 lowmat=bpy.data.materials.new('Telephone Badge Baked Material'); lowmat.use_nodes=True; low.data.materials.append(lowmat)
 image=bpy.data.images.new('Telephone_Badge_Tangent_Normal',width=256,height=256,alpha=False,float_buffer=False); image.generated_color=(.5,.5,1,1); image.colorspace_settings.name='Non-Color'
 nodes=lowmat.node_tree.nodes; links=lowmat.node_tree.links; principled=next(n for n in nodes if n.type=='BSDF_PRINCIPLED'); principled.inputs['Base Color'].default_value=(.20,.12,.035,1); principled.inputs['Metallic'].default_value=.72; principled.inputs['Roughness'].default_value=.30
 tex=nodes.new('ShaderNodeTexImage'); tex.name='Telephone Badge Tangent Bake'; tex.image=image; nodes.active=tex
 # High source: plate plus three raised bars and two fasteners, authored as a coherent badge relief.
 high=[high_badge_relief()]
 for o in high:
  for p in o.data.polygons: p.use_smooth=False
 scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.render.bake.use_selected_to_active=True; scene.render.bake.use_clear=True; scene.render.bake.margin=12; scene.render.bake.cage_extrusion=.10; scene.render.bake.max_ray_distance=.18; scene.render.image_settings.file_format='PNG'
 activate(low); failure={'rejected':False,'error':None}
 try: bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT')
 except RuntimeError as exc: failure={'rejected':True,'error':str(exc)}
 activate(low,include=high); result=bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT'); image.filepath_raw=str(out/'telephone_badge_tangent_normal.png'); image.save(); image.pack(); signal=metrics(image)
 normal=nodes.new('ShaderNodeNormalMap'); normal.name='Telephone Badge Tangent Decode'; normal.space='TANGENT'; links.new(tex.outputs['Color'],normal.inputs['Color']); links.new(normal.outputs['Normal'],principled.inputs['Normal'])
 for o in high: bpy.data.objects.remove(o,do_unlink=True)
 low['assembly_reason']='replaceable manufacturer badge with authored high-low tangent bake'; low['bake_image']='Telephone_Badge_Tangent_Normal'
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'heldout_vintage_telephone_production.blend'))
 # Preserve linked/mirrored editability in the saved source; normalize transforms only for the package.
 applied_export_scales=[]
 for ob in list(bpy.context.scene.objects):
  if ob.type in {'MESH','CURVE'} and any(abs(abs(v)-1.0)>1e-8 or v<0 for v in ob.scale):
   if hasattr(ob.data,'users') and ob.data.users>1: ob.data=ob.data.copy()
   bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); applied_export_scales.append(ob.name)
 bpy.ops.object.select_all(action='DESELECT')
 for o in bpy.context.scene.objects:
  if o.type in {'MESH','CURVE'} and not o.name.startswith('BadgeHigh_'): o.select_set(True)
 glb=out/'heldout_vintage_telephone.glb'; export=bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True)
 assertions={'missing_high_source_rejected':failure['rejected'],'selected_to_active_bake_finished':'FINISHED' in result,'normal_bake_has_signal':signal['non_neutral_pixels']>300,'normal_image_non_color':image.colorspace_settings.name=='Non-Color','normal_map_node_tangent':normal.space=='TANGENT','glb_export_finished':'FINISHED' in export and glb.stat().st_size>0}
 report={'lab':'heldout_vintage_telephone_production_handoff','blender_version':bpy.app.version_string,'source_blend':str(source),'failure_control':failure,'bake':{'operator_result':sorted(result),'image':signal,'path':str(out/'telephone_badge_tangent_normal.png')},'export':{'operator_result':sorted(export),'path':str(glb),'bytes':glb.stat().st_size,'applied_export_scales':applied_export_scales},'assertions':assertions,'pass':all(assertions.values())}; (out/'production_report.json').write_text(json.dumps(report,indent=2),encoding='utf8'); print('TELEPHONE_PRODUCTION:'+json.dumps(report));
 if not report['pass']: raise SystemExit(2)
main()
