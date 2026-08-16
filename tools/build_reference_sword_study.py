"""Build an editable sword study from the supplied straight-sword references.

The blade is a single profile-extruded mesh (not stacked primitives). Guard,
grip and pommel are distinct manufactured components. HIGH_POLY and LOW_POLY
contain independent meshes and all modifiers remain unapplied.
"""
from __future__ import annotations
import json
from math import cos, pi, sin
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/"runs"/"2026-08-16_reference-sword-study"

def profile(name, points, depth, collection):
    verts=[(x,-depth/2,z) for x,z in points]+[(x,depth/2,z) for x,z in points]; n=len(points)
    faces=[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); collection.objects.link(obj); return obj

def cylinder(name,radius,depth,z,collection,segments=12):
    pts=[(radius*cos(2*pi*i/segments),radius*sin(2*pi*i/segments)) for i in range(segments)]
    verts=[(x,y,z-depth/2) for x,y in pts]+[(x,y,z+depth/2) for x,y in pts]; n=segments
    faces=[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); collection.objects.link(obj); return obj

def ridged_blade(name,collection,detail):
    # Six-sided rings form one continuous diamond-section blade: the centerline
    # is actual geometry, not a floating "fuller" primitive.
    sections=[(0,.48),(.35,.55),(4.85,.54),(5.35,.58),(6.45,.22)]
    verts=[]
    for z,w in sections:
        verts += [(-w,-.075,z),(0,-.18,z),(w,-.075,z),(w,.075,z),(0,.18,z),(-w,.075,z)]
    faces=[tuple(range(6))]
    for ring in range(len(sections)-1):
        a=ring*6; b=a+6
        faces += [(a+i,a+(i+1)%6,b+(i+1)%6,b+i) for i in range(6)]
    tip=len(verts); verts.append((0,0,7.2))
    a=(len(sections)-1)*6; faces += [(a+i,a+(i+1)%6,tip) for i in range(6)]
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); collection.objects.link(obj); return obj

def ringed_grip(name,collection,segments):
    rings=[(-2.18,.23),(-1.95,.27),(-1.68,.235),(-1.40,.27),(-1.12,.235),(-.83,.27),(-.55,.23)]
    verts=[]
    for z,r in rings: verts += [(r*cos(2*pi*i/segments),r*sin(2*pi*i/segments),z) for i in range(segments)]
    faces=[tuple(range(segments)),tuple(range((len(rings)-1)*segments,len(rings)*segments))]
    for ring in range(len(rings)-1):
        a=ring*segments; b=a+segments
        faces += [(a+i,a+(i+1)%segments,b+(i+1)%segments,b+i) for i in range(segments)]
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); collection.objects.link(obj); return obj

def bevel(obj,width,segments):
    mod=obj.modifiers.new("Manual Bevel - Unapplied","BEVEL"); mod.width=width; mod.segments=segments; mod.limit_method="ANGLE"; mod.show_viewport=True; mod.show_render=True

def material(name,color):
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name); mat.diffuse_color=(*color,1); return mat

def make_variant(collection, prefix, segments):
    # One profile-extruded blade retains a wide ricasso, taper, and diamond-like point silhouette.
    blade=ridged_blade(prefix+"_Blade",collection,segments)
    guard=profile(prefix+"_Guard",[(-2.20,.16),(-2.34,.06),(-2.22,-.12),(-1.62,-.14),(-1.20,-.06),(-.58,.10),(-.22,.22),(0,.14),(.22,.22),(.58,.10),(1.20,-.06),(1.62,-.14),(2.22,-.12),(2.34,.06),(2.20,.16)],.34,collection)
    grip=ringed_grip(prefix+"_Grip",collection,16 if prefix=="High" else 12)
    pommel=profile(prefix+"_Pommel",[(-.28,-2.34),(-.48,-2.04),(-.37,-1.75),(-.18,-1.56),(.18,-1.56),(.37,-1.75),(.48,-2.04),(.28,-2.34)],.44,collection)
    steel=material("Steel",(.18,.24,.30)); leather=material("Crimson leather",(.28,.025,.04))
    for obj in (blade,guard,pommel): obj.data.materials.append(steel); bevel(obj,.035 if prefix=="Low" else .055,segments)
    grip.data.materials.append(leather); bevel(grip,.035 if prefix=="Low" else .055,segments)
    return [blade,guard,grip,pommel]

def main():
    RUN.mkdir(parents=True,exist_ok=True); bpy.ops.wm.read_factory_settings(use_empty=True)
    high=bpy.data.collections.new("HIGH_POLY"); low=bpy.data.collections.new("LOW_POLY"); bpy.context.scene.collection.children.link(high); bpy.context.scene.collection.children.link(low)
    high_objs=make_variant(high,"High",3); low_objs=make_variant(low,"Low",1)
    # Low and high are separate editable meshes; neither stack is applied.
    for obj in high_objs: obj.location.x=-3.0
    for obj in low_objs: obj.location.x=3.0
    for obj in high_objs+low_objs:
        obj.select_set(True)
        for poly in obj.data.polygons: poly.use_smooth=False
    bpy.ops.object.camera_add(location=(11,-16,9)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,1.6))-cam.location).to_track_quat("-Z","Y").to_euler(); bpy.context.scene.camera=cam
    scene=bpy.context.scene; scene.render.engine="BLENDER_WORKBENCH"; scene.display.shading.light="STUDIO"; scene.display.shading.color_type="MATERIAL"; scene.display.shading.show_cavity=True; scene.display.shading.show_shadows=True; scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.render.filepath=str(RUN/"sword_study_solid.png"); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN/"reference_sword_study.blend"))
    report={"disposition":"IMPROVED_REJECTED", "reference_direction":"supplied straight medieval/fantasy sword sheets; no claim of exact reproduction", "collections":{"high":"HIGH_POLY","low":"LOW_POLY"}, "high_objects":[o.name for o in high_objs], "low_objects":[o.name for o in low_objs], "independent_meshes":all(a.data!=b.data for a,b in zip(high_objs,low_objs)), "all_modifiers_live":all(m.show_viewport and m.show_render for o in high_objs+low_objs for m in o.modifiers), "modifier_apply_called":False, "topology_note":"Blade is a continuous diamond-section ridged mesh; guard, ringed grip, and pommel are intentionally distinct physical components, not touching detail primitives.", "visual_review":{"accepted":False,"improvements":["real diamond cross-section ridge geometry replaces the flat blade","one continuous ringed grip replaces the plain cylinder","guard and pommel silhouettes now carry secondary tapered geometry"],"remaining_defects":["the design remains a generic interpretation, not a measured reconstruction of one reference","guard/pommel ornament and material breakup are below the supplied concept sheets","high/low remain editable variant cages rather than purpose-authored baking topology"]}, "claim_boundary":"Editable reference-informed improved but rejected blockout, not a finished production sword or purpose-authored retopology pair."}
    (RUN/"sword_study_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if __name__=="__main__": main()
