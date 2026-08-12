"""Bake one authored normal-detail insert and export the held-out watering can."""
from __future__ import annotations
import json, sys
from pathlib import Path
import bpy

def quad(name, y, depth):
    vertices=[(-.42,y,-.15),(.42,y,-.15),(.42,y,.15),(-.42,y,.15)]
    faces=[(0,1,2,3)]
    if depth:
        # One continuous shallow four-sided relief, not overlapping boxes.
        vertices.append((0,y-depth,0)); faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4)]
    mesh=bpy.data.meshes.new(name+'Mesh'); mesh.from_pydata(vertices,[],faces); mesh.update(); obj=bpy.data.objects.new(name,mesh); bpy.context.scene.collection.objects.link(obj)
    uv=mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:
        co=mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=((co.x+.42)/.84,(co.z+.15)/.30)
    return obj

def activate(active, extra=()):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in extra: obj.select_set(True)
    active.select_set(True); bpy.context.view_layer.objects.active=active

def main():
    values=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if len(values)!=2: raise SystemExit('expected SOURCE_BLEND OUTPUT_DIR after --')
    source,out=map(lambda value:Path(value).resolve(),values);out.mkdir(parents=True,exist_ok=True); bpy.ops.wm.open_mainfile(filepath=str(source)); scene=bpy.context.scene
    low=quad('WateringCan_Baked_Badge',-1.575,0); high=quad('WateringCan_BadgeHigh',-1.575,.06)
    lowmat=bpy.data.materials.new('Watering Can Baked Detail');lowmat.use_nodes=True;low.data.materials.append(lowmat); nodes=lowmat.node_tree.nodes;links=lowmat.node_tree.links;principled=next(node for node in nodes if node.type=='BSDF_PRINCIPLED');principled.inputs['Metallic'].default_value=.7;principled.inputs['Roughness'].default_value=.3
    image=bpy.data.images.new('WateringCan_Badge_Tangent_Normal',128,128,alpha=False);image.generated_color=(.5,.5,1,1);image.colorspace_settings.name='Non-Color';tex=nodes.new('ShaderNodeTexImage');tex.image=image;nodes.active=tex
    scene.render.engine='CYCLES';scene.render.bake.use_selected_to_active=True;scene.render.bake.use_clear=True;scene.render.bake.margin=8;scene.render.bake.cage_extrusion=.12; activate(low, (high,));result=bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT');image.filepath_raw=str(out/'watering_can_badge_tangent_normal.png');image.save();image.pack();normal=nodes.new('ShaderNodeNormalMap');normal.space='TANGENT';links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],principled.inputs['Normal'])
    pixels=list(image.pixels);signal=sum(max(abs(pixels[i]-.5),abs(pixels[i+1]-.5),abs(pixels[i+2]-1))>.035 for i in range(0,len(pixels),4));bpy.data.objects.remove(high,do_unlink=True);low['assembly_reason']='replaceable badge; selected-to-active tangent normal bake'; bpy.ops.wm.save_as_mainfile(filepath=str(out/'heldout_watering_can_production.blend'))
    activate(low);bpy.ops.object.select_all(action='SELECT');glb=out/'heldout_watering_can.glb';export=bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_tangents=True,export_apply=True)
    assertions={'bake_finished':'FINISHED' in result,'normal_has_non_neutral_signal':signal>20,'normal_non_color':image.colorspace_settings.name=='Non-Color','normal_map_tangent':normal.space=='TANGENT','glb_export_finished':'FINISHED' in export and glb.stat().st_size>0}; report={'source':str(source),'bake_signal_pixels':signal,'glb':str(glb),'glb_bytes':glb.stat().st_size,'assertions':assertions,'pass':all(assertions.values())};(out/'production_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report));raise SystemExit(0 if report['pass'] else 2)
main()
