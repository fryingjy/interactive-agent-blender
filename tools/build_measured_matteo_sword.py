"""Build editable high/low sword silhouettes from the supplied measured reference.

This is deliberately silhouette-first: the source profile determines the
outline, rather than an arbitrary generic-sword builder. Each variant is one
continuous extruded mesh and its bevel remains live.
"""
from __future__ import annotations
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(r"C:\Users\odane\Downloads\blender\ref\matteo-swordconcept244_measurement.json")
RUN=ROOT/"runs"/"2026-08-16_measured-matteo-sword"

def outline_rows(step):
    data=json.loads(SOURCE.read_text(encoding="utf-8")); rows=data["row_profile"]
    # Include the end row and retain rows whose width proves a real silhouette.
    chosen=[row for i,row in enumerate(rows) if i%step==0 or i==len(rows)-1]
    chosen=[row for row in chosen if row["width_px"]>0]
    cx=(data["silhouette_bbox_px"]["x"][0]+data["silhouette_bbox_px"]["x"][1])/2
    height=data["silhouette_size_px"]["height"]
    # Image y grows down; model z grows up. Normalize to source silhouette height.
    left=[((row["x_min_px"]-cx)/height,(data["silhouette_bbox_px"]["y"][1]-row["y_px"])/height*10) for row in chosen]
    right=[((row["x_max_px"]-cx)/height,(data["silhouette_bbox_px"]["y"][1]-row["y_px"])/height*10) for row in reversed(chosen)]
    return left+right, data

def build(name,collection,step,depth,bevel_width,bevel_segments):
    points,data=outline_rows(step); n=len(points)
    verts=[(x,-depth/2,z) for x,z in points]+[(x,depth/2,z) for x,z in points]
    faces=[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); collection.objects.link(obj)
    bevel=obj.modifiers.new("Manual Bevel - Unapplied","BEVEL"); bevel.width=bevel_width; bevel.segments=bevel_segments; bevel.limit_method="ANGLE"; bevel.show_viewport=True; bevel.show_render=True
    return obj, data, len(points)

def main():
    RUN.mkdir(parents=True,exist_ok=True); bpy.ops.wm.read_factory_settings(use_empty=True)
    high=bpy.data.collections.new("HIGH_POLY"); low=bpy.data.collections.new("LOW_POLY"); bpy.context.scene.collection.children.link(high); bpy.context.scene.collection.children.link(low)
    high_obj,measurement,high_points=build("MatteoSword_High",high,8,.25,.025,3)
    low_obj,_,low_points=build("MatteoSword_Low",low,32,.25,.02,1)
    high_obj.location.x=-1.3; low_obj.location.x=1.3
    steel=bpy.data.materials.new("Reference Steel"); steel.diffuse_color=(.22,.28,.34,1)
    for obj in (high_obj,low_obj): obj.data.materials.append(steel)
    bpy.ops.object.camera_add(location=(0,-15,5)); camera=bpy.context.object; camera.rotation_euler=(Vector((0,0,5))-camera.location).to_track_quat("-Z","Y").to_euler(); bpy.context.scene.camera=camera
    scene=bpy.context.scene; scene.render.engine="BLENDER_WORKBENCH"; scene.display.shading.light="STUDIO"; scene.display.shading.color_type="MATERIAL"; scene.display.shading.show_cavity=True; scene.display.shading.show_shadows=True; scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.render.filepath=str(RUN/"measured_silhouette_study.png"); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN/"measured_matteo_sword.blend"))
    report={"disposition":"REJECTED_PARTIAL_MEASUREMENT","reference_measurement":str(SOURCE),"source_image_size_px":measurement["image_size_px"],"source_silhouette_aspect_ratio":measurement["aspect_ratio_w_over_h"],"collections":{"high":"HIGH_POLY","low":"LOW_POLY"},"high_outline_points":high_points,"low_outline_points":low_points,"one_continuous_mesh_each":True,"independent_meshes":high_obj.data!=low_obj.data,"all_modifiers_live":all(o.modifiers[0].show_viewport for o in (high_obj,low_obj)),"modifier_apply_called":False,"visible_review":{"accepted":False,"reason":"The supplied measurement mask excludes the guard, grip, and pommel, so it is blade/tang-only evidence rather than the full reference silhouette."},"claim_boundary":"This verifies only that the measurement JSON can drive editable variants. It is rejected as a full-sword reference profile and does not establish hidden depth, blade ridge/fuller, material response, or production-ready retopology."}
    (RUN/"measured_sword_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if __name__=="__main__": main()
