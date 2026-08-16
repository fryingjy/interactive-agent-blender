"""Reference-led Matteo sword interpretation with editable high/low variants.

Every visible component follows the supplied Matteo sword concept's front
silhouette; no source image is copied into the repository. Modifiers remain live.
"""
from __future__ import annotations
import json
from math import cos,pi,sin
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]; RUN=ROOT/'runs'/'2026-08-16_matteo-sword-interpretation'

def profile(name,pts,depth,coll,mat,bevel):
 n=len(pts); vs=[(x,-depth/2,z) for x,z in pts]+[(x,depth/2,z) for x,z in pts]
 fs=[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(vs,[],fs); me.materials.append(mat); ob=bpy.data.objects.new(name,me); coll.objects.link(ob)
 mod=ob.modifiers.new('Manual Bevel - Unapplied','BEVEL');mod.width=bevel;mod.segments=2;mod.limit_method='ANGLE';mod.show_viewport=True;mod.show_render=True;return ob
def wrapped_grip(name,coll,segments,mat):
 rings=[(-2.8,.26),(-2.58,.31),(-2.35,.26),(-2.12,.31),(-1.89,.26),(-1.66,.31),(-1.43,.26),(-1.20,.28)]
 vs=[(r*cos(2*pi*i/segments),r*sin(2*pi*i/segments),z) for z,r in rings for i in range(segments)]; fs=[tuple(range(segments)),tuple(range((len(rings)-1)*segments,len(rings)*segments))]
 for j in range(len(rings)-1):
  a=j*segments;b=a+segments;fs += [(a+i,a+(i+1)%segments,b+(i+1)%segments,b+i) for i in range(segments)]
 me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(vs,[],fs);me.materials.append(mat);ob=bpy.data.objects.new(name,me);coll.objects.link(ob);mod=ob.modifiers.new('Manual Bevel - Unapplied','BEVEL');mod.width=.025;mod.segments=2;mod.limit_method='ANGLE';mod.show_viewport=True;mod.show_render=True;return ob
def material(name,c):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
def variant(coll,prefix,segments):
 steel=material('Pale blade steel',(.34,.54,.58));gold=material('Antique gold',(.48,.32,.08));blue=material('Blue leather',(.04,.15,.42))
 blade=profile(prefix+'_Blade',[(-.72,0),(-1.05,.38),(-.74,1.12),(-.50,2.4),(-.60,4.2),(0,6.9),(.60,4.2),(.50,2.4),(.74,1.12),(1.05,.38),(.72,0)],.22,coll,steel,.035)
 fan=profile(prefix+'_FanGuard',[(-1.90,-.42),(-1.42,-.12),(-.94,.02),(0,.65),(.94,.02),(1.42,-.12),(1.90,-.42),(1.25,-.32),(0,-.72),(-1.25,-.32)],.30,coll,gold,.04)
 left=profile(prefix+'_LeftWing',[(-2.28,-.65),(-1.82,-.34),(-1.10,-.48),(-1.45,-.78),(-2.08,-1.04),(-1.65,-.57)],.24,coll,gold,.035)
 right=profile(prefix+'_RightWing',[(2.28,-.65),(1.82,-.34),(1.10,-.48),(1.45,-.78),(2.08,-1.04),(1.65,-.57)],.24,coll,gold,.035)
 grip=wrapped_grip(prefix+'_WrappedGrip',coll,segments,blue)
 pommel=profile(prefix+'_Pommel',[(-.52,-3.05),(-.62,-2.82),(-.42,-2.58),(-.26,-2.47),(.26,-2.47),(.42,-2.58),(.62,-2.82),(.52,-3.05),(0,-3.20)],.36,coll,gold,.04)
 return [blade,fan,left,right,grip,pommel]
def main():
 RUN.mkdir(parents=True,exist_ok=True);bpy.ops.wm.read_factory_settings(use_empty=True);high=bpy.data.collections.new('HIGH_POLY');low=bpy.data.collections.new('LOW_POLY');bpy.context.scene.collection.children.link(high);bpy.context.scene.collection.children.link(low)
 hs=variant(high,'High',16);ls=variant(low,'Low',12)
 for o in ls:o.hide_render=True;o.hide_viewport=True
 bpy.ops.object.camera_add(location=(8,-16,5));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.8))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.camera=cam
 s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.show_shadows=True;s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(RUN/'matteo_interpretation_solid.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'matteo_sword_interpretation.blend'))
 out={'disposition':'REFERENCE_INTERPRETATION_CANDIDATE','source':'supplied matteo-swordconcept244.jpg front view','high_collection':'HIGH_POLY','low_collection':'LOW_POLY','high_objects':[o.name for o in hs],'low_objects':[o.name for o in ls],'independent_meshes':all(a.data!=b.data for a,b in zip(hs,ls)),'live_unapplied_modifiers':all(m.show_viewport for o in hs+ls for m in o.modifiers),'modifier_apply_called':False,'topology_policy':'Blade, guard fan, wings, grip, and pommel are deliberately distinct physical/design components; each component is an editable contiguous mesh rather than accumulated detail primitives.','claim_boundary':'Front-view reference interpretation only. Requires human review and side/depth reference before production acceptance.'};(RUN/'matteo_interpretation_report.json').write_text(json.dumps(out,indent=2),encoding='utf8')
if __name__=='__main__':main()
