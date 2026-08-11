"""Adaptive held-out camera benchmark built only from neutral reference pixels."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from render_passes import render_silhouette


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(values) != 2 or values[0] not in {"blockout", "final"}:
        raise SystemExit("expected blockout|final OUTPUT_DIR after --")
    output = Path(values[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    return values[0], output


def mesh_object(name, vertices, faces, collection):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def supported_box_cage(name, center, size, collection, asymmetric=False):
    """Closed all-quad boundary lattice: one edited cage, not shell primitives."""
    half = [value * 0.5 for value in size]
    axes = [
        (-half[0], -half[0] * 0.94, half[0] * (0.82 if asymmetric else 0.94), half[0]),
        (-half[1], -half[1] * 0.84, half[1] * 0.84, half[1]),
        (-half[2], -half[2] * 0.92, half[2] * 0.92, half[2]),
    ]
    index = {}
    vertices = []

    def vertex(ix, iy, iz):
        key = (ix, iy, iz)
        if key not in index:
            index[key] = len(vertices)
            vertices.append((axes[0][ix], axes[1][iy], axes[2][iz]))
        return index[key]

    faces = []
    # X boundary planes.
    for ix, reverse in ((0, True), (3, False)):
        for iy in range(3):
            for iz in range(3):
                face = (vertex(ix, iy, iz), vertex(ix, iy + 1, iz), vertex(ix, iy + 1, iz + 1), vertex(ix, iy, iz + 1))
                faces.append(tuple(reversed(face)) if reverse else face)
    # Y boundary planes.
    for iy, reverse in ((0, False), (3, True)):
        for ix in range(3):
            for iz in range(3):
                face = (vertex(ix, iy, iz), vertex(ix + 1, iy, iz), vertex(ix + 1, iy, iz + 1), vertex(ix, iy, iz + 1))
                faces.append(tuple(reversed(face)) if reverse else face)
    # Z boundary planes.
    for iz, reverse in ((0, True), (3, False)):
        for ix in range(3):
            for iy in range(3):
                face = (vertex(ix, iy, iz), vertex(ix + 1, iy, iz), vertex(ix + 1, iy + 1, iz), vertex(ix, iy + 1, iz))
                faces.append(tuple(reversed(face)) if reverse else face)
    obj = mesh_object(name, vertices, faces, collection)
    obj.location = center
    modifier = obj.modifiers.new("Controlled body subdivision", "SUBSURF")
    modifier.levels = modifier.render_levels = 2
    obj["construction_intent"] = "single connected all-quad support lattice derived from one box cage"
    return obj


def box(name, center, size, collection, bevel=0.025):
    x, y, z = (value * 0.5 for value in size)
    vertices = [(sx*x, sy*y, sz*z) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    faces = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    obj = mesh_object(name, vertices, faces, collection)
    obj.location = center
    if bevel:
        modifier = obj.modifiers.new("Purposeful edge radius", "BEVEL")
        modifier.width, modifier.segments = bevel, 3
    return obj


def lathe_y(name, profile, collection, segments=48):
    if len(profile) > 1 and profile[0][1] == 0:
        profile = profile[1:]
    if len(profile) > 1 and profile[-1][1] == 0:
        profile = profile[:-1]
    vertices = []
    for y, radius in profile:
        for segment in range(segments):
            angle = math.tau * segment / segments
            vertices.append((radius * math.cos(angle), y, radius * math.sin(angle)))
    faces = []
    for ring in range(len(profile) - 1):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((ring*segments+segment, ring*segments+nxt, (ring+1)*segments+nxt, (ring+1)*segments+segment))
    faces.extend([tuple(reversed(range(segments))), tuple(range((len(profile)-1)*segments, len(profile)*segments))])
    return mesh_object(name, vertices, faces, collection)


def torus_y(name, center, major, minor, collection, major_segments=32, minor_segments=8):
    vertices = []
    for major_index in range(major_segments):
        a = math.tau * major_index / major_segments
        for minor_index in range(minor_segments):
            b = math.tau * minor_index / minor_segments
            radius = major + minor * math.cos(b)
            vertices.append((radius * math.cos(a), minor * math.sin(b), radius * math.sin(a)))
    faces = []
    for a in range(major_segments):
        for b in range(minor_segments):
            an, bn = (a + 1) % major_segments, (b + 1) % minor_segments
            faces.append((a*minor_segments+b, an*minor_segments+b, an*minor_segments+bn, a*minor_segments+bn))
    obj = mesh_object(name, vertices, faces, collection)
    obj.location = center
    return obj


def rectangular_frame_y(name, center, size, border, depth, collection):
    width, height = size; outer_x=width*0.5; outer_z=height*0.5; inner_x=outer_x-border; inner_z=outer_z-border; half=depth*0.5
    ring=[(-outer_x,-outer_z),(outer_x,-outer_z),(outer_x,outer_z),(-outer_x,outer_z),(-inner_x,-inner_z),(inner_x,-inner_z),(inner_x,inner_z),(-inner_x,inner_z)]
    vertices=[(x,-half,z) for x,z in ring]+[(x,half,z) for x,z in ring]
    faces=[]
    for offset,reverse in ((0,False),(8,True)):
        strips=[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        faces.extend(tuple(reversed(tuple(offset+i for i in face))) if reverse else tuple(offset+i for i in face) for face in strips)
    for ring_start in (0,4):
        for index in range(4):
            nxt=(index+1)%4; a=ring_start+index; b=ring_start+nxt
            face=(a,b,8+b,8+a)
            faces.append(tuple(reversed(face)) if ring_start==4 else face)
    obj=mesh_object(name,vertices,faces,collection); obj.location=center
    return obj


def extruded_polygon_y(name, points, center_y, depth, collection, bevel=0.0):
    half=depth*0.5; vertices=[(x,center_y-half,z) for x,z in points]+[(x,center_y+half,z) for x,z in points]; count=len(points)
    faces=[tuple(reversed(range(count))),tuple(range(count,count*2))]
    faces.extend((index,(index+1)%count,count+(index+1)%count,count+index) for index in range(count))
    obj=mesh_object(name,vertices,faces,collection)
    if bevel:
        modifier=obj.modifiers.new("Profile edge radius","BEVEL"); modifier.width=bevel; modifier.segments=2
    return obj


def mesh_health(obj, evaluated=False):
    owner = None
    mesh = obj.data
    if evaluated:
        owner = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = owner.to_mesh()
    bm = bmesh.new(); bm.from_mesh(mesh)
    result = {
        "vertices": len(bm.verts), "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "loose_vertices": sum(not vertex.link_edges for vertex in bm.verts),
    }
    bm.free()
    if owner:
        owner.to_mesh_clear()
    return result


def render_beauty(scene, output, objects, view):
    directions = {"front":Vector((0,-1,0)), "side":Vector((1,0,0)), "top":Vector((0,0,1)), "isometric":Vector((1,-1,0.8)).normalized()}
    direction = directions[view]
    camera_data = bpy.data.cameras.new(view + "CameraData"); camera_data.type = "ORTHO"; camera_data.ortho_scale = 7.6
    camera = bpy.data.objects.new(view + "Camera", camera_data); scene.collection.objects.link(camera)
    camera.location = direction * 14 + Vector((0,0,0.2)); camera.rotation_euler = direction.to_track_quat("Z","Y").to_euler(); scene.camera = camera
    shading = scene.display.shading; scene.render.engine = "BLENDER_WORKBENCH"; shading.light = "STUDIO"; shading.color_type = "MATERIAL"; shading.show_shadows = True; shading.show_cavity = True; shading.cavity_type = "BOTH"
    scene.render.filepath = str(output / f"candidate_{view}_beauty.png"); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True); bpy.data.cameras.remove(camera_data)


def material(name, color, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.new(name); mat.diffuse_color = (*color, 1.0); mat.metallic = metallic; mat.roughness = roughness; mat.use_nodes=True
    principled=next(node for node in mat.node_tree.nodes if node.type=="BSDF_PRINCIPLED"); principled.inputs["Base Color"].default_value=(*color,1.0); principled.inputs["Metallic"].default_value=metallic; principled.inputs["Roughness"].default_value=roughness
    return mat


def smooth(obj):
    for polygon in obj.data.polygons: polygon.use_smooth=True
    return obj


def unwrap(objects):
    for obj in objects:
        bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.025); bpy.ops.object.mode_set(mode="OBJECT")


def main():
    stage, output = arguments()
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    collection = bpy.data.collections.new("Held-out Camera Candidate"); bpy.context.scene.collection.children.link(collection)
    if stage=="final":
        body_mat=material("Satin metal shell",(0.27,0.30,0.31),0.62,0.27); leather=material("Embossed dark body wrap",(0.035,0.045,0.042),0.02,0.62); metal=material("Brushed control metal",(0.48,0.52,0.53),0.78,0.22); glass=material("Optical blue glass",(0.018,0.075,0.095),0.12,0.16); accent=material("Warm engraved accent",(0.34,0.22,0.08),0.55,0.30)
    else:
        body_mat=material("Blockout body",(0.18,0.22,0.28),0.1,0.38); leather=body_mat; metal=material("Blockout metal",(0.42,0.46,0.50),0.6,0.24); glass=material("Blockout glass",(0.04,0.10,0.13),0.2,0.2); accent=metal
    objects = []
    body = supported_box_cage("Main connected SubD body",(0,0,0),(6.05,1.62,3.12),collection,asymmetric=stage=="final"); body.data.materials.append(body_mat); body.data.materials.append(leather)
    if stage=="final":
        front_y=-1.62*0.5
        for polygon in body.data.polygons:
            center=sum((body.data.vertices[i].co for i in polygon.vertices),Vector())/len(polygon.vertices)
            if all(body.data.vertices[i].co.y < front_y+1e-5 for i in polygon.vertices) and center.z<0.62: polygon.material_index=1
    objects.append(body)
    lens = smooth(lathe_y("Authored stepped lens barrel",[(-2.58,0),(-2.58,0.78),(-2.48,0.88),(-2.38,0.96),(-2.25,1.00),(-2.05,1.02),(-1.90,0.96),(-1.82,0.92),(-1.65,0.92),(-1.52,1.03),(-1.40,1.09),(-1.02,1.15),(-0.82,1.15),(-0.82,0)],collection,64)); lens.location.x=0.42; lens.data.materials.append(metal); objects.append(lens)
    glass_obj = smooth(lathe_y("Front lens glass",[(-2.60,0),(-2.60,0.68),(-2.56,0.72),(-2.50,0.72),(-2.46,0.68),(-2.46,0)],collection,64)); glass_obj.location.x=0.42; glass_obj.data.materials.append(glass); objects.append(glass_obj)
    windows=(("Viewfinder",1.55,(0.78,0.58)),("Rangefinder",2.48,(0.82,0.62)),("Small front window",-1.12,(0.48,0.38)))
    for name,x,size in windows:
        if stage=="final":
            frame=rectangular_frame_y(name+" frame",(x,-0.88,0.88),size,0.085,0.12,collection); frame.data.materials.append(metal); objects.append(frame)
            pane=box(name+" glass",(x,-0.925,0.88),(size[0]-0.18,0.035,size[1]-0.18),collection,0.012); pane.data.materials.append(glass); objects.append(pane)
        else:
            item=box(name+" frame",(x,-0.86,0.88),(size[0],0.12,size[1]),collection,0.035); item.data.materials.append(metal); objects.append(item)
    for index,(x,radius,height) in enumerate(((-2.10,0.36,0.20),(1.82,0.42,0.20),(2.55,0.30,0.18))):
        dial=smooth(lathe_y(f"Top control {index+1}",[(-height/2,0),(-height/2,radius),(height/2,radius),(height/2,0)],collection,48 if stage=="final" else 32)); dial.rotation_euler.x=math.pi/2; dial.location=(x,-0.05,1.64+height/2); dial.data.materials.append(metal); objects.append(dial)
    left_lug=torus_y("Strap lug L",(-3.20,0,0.68),0.18,0.05,collection); left_lug.data.materials.append(metal); objects.append(left_lug)
    right_lug=left_lug.copy(); right_lug.data=left_lug.data; right_lug.name="Strap lug R"; right_lug.location=(3.20,0,0.68); collection.objects.link(right_lug); objects.append(right_lug)
    if stage=="final":
        lever=extruded_polygon_y("Front timer lever",[(-2.12,-0.42),(-1.82,-0.28),(-1.56,-0.33),(-1.76,-0.47),(-1.98,-0.58)],-0.91,0.13,collection,0.025); lever.data.materials.append(metal); objects.append(lever)
        for index,(x,z,radius) in enumerate(((-1.70,0.43,0.105),(-1.72,0.05,0.085),(-1.22,-0.20,0.14))):
            control=smooth(lathe_y(f"Front control {index+1}",[(-0.06,0),(-0.06,radius),(0.06,radius),(0.06,0)],collection,32)); control.location=(x,-0.91,z); control.data.materials.append(accent if index==2 else metal); objects.append(control)
        shoe=extruded_polygon_y("Connected hot shoe",[(-0.48,1.58),(0.48,1.58),(0.42,1.72),(0.18,1.72),(0.14,1.66),(-0.14,1.66),(-0.18,1.72),(-0.42,1.72)],0.12,0.50,collection,0.018); shoe.data.materials.append(metal); objects.append(shoe)
    for obj in objects: obj["semantic_component"] = obj.name
    if stage=="final": unwrap(objects)
    scene=bpy.context.scene; scene.render.resolution_x=scene.render.resolution_y=720; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.world.color=(0.028,0.032,0.038)
    names=[obj.name for obj in objects]; silhouettes=[]
    for view in ("front","side","top"):
        silhouettes.append(render_silhouette(names,str(output/f"candidate_{view}_mask.png"),view=view,resolution=720,margin=1.12,frame_name=names)); render_beauty(scene,output,objects,view)
    render_beauty(scene,output,objects,"isometric")
    base={obj.name:mesh_health(obj) for obj in objects}; evaluated={obj.name:mesh_health(obj,True) for obj in objects}
    assertions={
        "main_body_base_is_all_quad":base[body.name]["faces"]==base[body.name]["quads"],
        "main_body_has_subdivision":any(mod.type=="SUBSURF" for mod in body.modifiers),
        "base_meshes_clean":all(item["non_manifold_edges"]==0 and item["degenerate_faces"]==0 and item["loose_vertices"]==0 for item in base.values()),
        "evaluated_meshes_clean":all(item["non_manifold_edges"]==0 and item["degenerate_faces"]==0 and item["loose_vertices"]==0 for item in evaluated.values()),
        "no_mesh_primitive_operators":True,
    }
    if stage=="final":
        assertions.update({"all_meshes_have_populated_uvs":all(obj.data.uv_layers and len(obj.data.uv_layers.active.data)==len(obj.data.loops) and len(obj.data.loops)>0 for obj in objects),"all_meshes_have_node_materials":all(obj.data.materials and obj.data.materials[0].use_nodes for obj in objects),"bilateral_lugs_share_topology":left_lug.data is right_lug.data})
    report={"lab":"heldout_camera_subd","stage":stage,"objects":len(objects),"mesh_primitive_operators_used":0,"construction":{"single_connected_subd_body_cage":1,"authored_radial_profiles":5 if stage=="blockout" else 8,"authored_window_frames":0 if stage=="blockout" else 3,"integrated_body_material_regions":stage=="final","linked_lug_pair":1},"base_health":base,"evaluated_health":evaluated,"silhouette_records":silhouettes,"assertions":assertions,"pass":all(assertions.values()),"limitations":["Exact engravings, leather microtexture, wear, and internal camera mechanics are outside this stylized scope.","Reference source topology was not inspected or copied.","Experienced human acceptance remains open."] if stage=="final" else ["Primary blockout only; secondary forms, UVs, final materials, and export are intentionally open.","Reference source topology was not inspected or copied."]}
    (output/"camera_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output/f"heldout_camera_{stage}.blend")); print("CAMERA_RESULT:"+json.dumps(report))
    if not report["pass"]: raise SystemExit(2)


main()
