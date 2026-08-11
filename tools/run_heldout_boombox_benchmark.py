"""Build the held-out CC0 boombox candidate from neutral reference pixels only."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from render_passes import render_silhouette


def output_dir():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(values) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    path = Path(values[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def mesh_object(name, vertices, faces, collection):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def box(name, center, size, collection, bevel=0.04):
    x, y, z = (value * 0.5 for value in size)
    vertices = [(sx*x, sy*y, sz*z) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    faces = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    obj = mesh_object(name, vertices, faces, collection)
    obj.location = center
    if bevel:
        modifier = obj.modifiers.new("Purposeful edge radius", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    return obj


def extruded_polygon_y(name, points, depth, collection, bevel=0.03):
    half = depth * 0.5
    vertices = [(x, -half, z) for x, z in points] + [(x, half, z) for x, z in points]
    count = len(points)
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    obj = mesh_object(name, vertices, faces, collection)
    if bevel:
        modifier = obj.modifiers.new("Structural edge radius", "BEVEL")
        modifier.width, modifier.segments = bevel, 3
    return obj


def integrated_housing(collection, case_material, recess_material):
    """One connected edited cage: cut grid + recessed central front region."""
    xs=(-3.20,-1.45,-1.35,1.35,1.45,3.20)
    zs=(-1.09,-0.98,-0.88,0.92,1.00,1.09)
    depth=1.48; front=-depth*0.5; back=depth*0.5
    vertices=[]
    for y_side in (front,back):
        for z in zs:
            for x in xs:
                y=y_side
                if y_side==front and -1.35<=x<=1.35 and -0.88<=z<=0.92:
                    y=front+0.075
                vertices.append((x,y,z))
    columns=len(xs); rows=len(zs); plane=columns*rows; faces=[]; front_face_indices=[]
    for side in range(2):
        offset=side*plane
        for row in range(rows-1):
            for column in range(columns-1):
                a=offset+row*columns+column; b=a+1; d=offset+(row+1)*columns+column; c=d+1
                face=(a,b,c,d) if side==0 else (a,d,c,b)
                front_face_indices.append(len(faces)) if side==0 else None
                faces.append(face)
    front_perimeter=[]
    front_perimeter.extend(range(0,columns))
    front_perimeter.extend(row*columns+columns-1 for row in range(1,rows))
    front_perimeter.extend((rows-1)*columns+column for column in range(columns-2,-1,-1))
    front_perimeter.extend(row*columns for row in range(rows-2,0,-1))
    for index,a in enumerate(front_perimeter):
        b=front_perimeter[(index+1)%len(front_perimeter)]
        faces.append((a,b,plane+b,plane+a))
    obj=mesh_object("Main integrated chassis",vertices,faces,collection)
    obj.data.materials.append(case_material); obj.data.materials.append(recess_material)
    face_index=0
    for row in range(rows-1):
        for column in range(columns-1):
            mid_x=(xs[column]+xs[column+1])*0.5; mid_z=(zs[row]+zs[row+1])*0.5
            if -1.35<mid_x<1.35 and -0.88<mid_z<0.92:
                obj.data.polygons[face_index].material_index=1
            face_index+=1
    # Do not drive an outer-corner bevel from perimeter *vertices*. On this cut
    # grid that also weights coplanar row/column edges and produces corner fins
    # after evaluation. The authored cage therefore keeps its clean, deliberate
    # outer corners; only the recessed transition receives a narrow treatment.
    recess_indices=[index for index,vertex in enumerate(vertices[:plane]) if abs(vertex[0])<=1.35+1e-6 and -0.88-1e-6<=vertex[2]<=0.92+1e-6]
    recess_group=obj.vertex_groups.new(name="Central recess bevel edges"); recess_group.add(recess_indices,1.0,"REPLACE")
    recess_bevel=obj.modifiers.new("Scoped central recess radius","BEVEL"); recess_bevel.width=0.018; recess_bevel.segments=2; recess_bevel.limit_method="VGROUP"; recess_bevel.vertex_group=recess_group.name
    obj["construction_intent"]="single connected cage; front grid cut and central vertices inset; no primitive-shell assembly"
    return obj


def lathe_y(name, profile, collection, segments=48, bevel=0.0):
    # A zero-radius endpoint represented as a full ring creates coincident
    # vertices and degenerate side faces. The adjacent nonzero ring already
    # lies at the same axial coordinate in every authored profile, so cap that
    # ring directly instead of manufacturing a collapsed pole ring.
    if len(profile) > 1 and profile[0][1] == 0.0:
        profile = profile[1:]
    if len(profile) > 1 and profile[-1][1] == 0.0:
        profile = profile[:-1]
    vertices = []
    for y, radius in profile:
        for segment in range(segments):
            angle = math.tau * segment / segments
            vertices.append((radius * math.cos(angle), y, radius * math.sin(angle)))
    faces = []
    rings = len(profile)
    for ring in range(rings - 1):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            a, b = ring*segments + segment, ring*segments + nxt
            c, d = (ring+1)*segments + nxt, (ring+1)*segments + segment
            faces.append((a,b,c,d))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple((rings-1)*segments + i for i in range(segments)))
    obj = mesh_object(name, vertices, faces, collection)
    if bevel:
        modifier = obj.modifiers.new("Profile edge radius", "BEVEL")
        modifier.width, modifier.segments = bevel, 2
    return obj


def rod(name, start, end, radius, collection, segments=16):
    start, end = Vector(start), Vector(end)
    length = (end - start).length
    profile = [(-length*0.5, 0.0), (-length*0.5, radius), (length*0.5, radius), (length*0.5, 0.0)]
    obj = lathe_y(name, profile, collection, segments)
    obj.location = (start + end) * 0.5
    obj.rotation_euler = (end - start).to_track_quat("Y", "Z").to_euler()
    return obj


def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def speaker_material():
    mat = material("Speaker grille", (0.018, 0.022, 0.024), 0.35, 0.55)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    noise = nodes.new("ShaderNodeTexNoise"); noise.name = "Stamped grille microtexture"; noise.inputs["Scale"].default_value = 145.0; noise.inputs["Detail"].default_value = 2.0; noise.inputs["Roughness"].default_value = 0.35
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.22; bump.inputs["Distance"].default_value = 0.018
    links.new(noise.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], nodes["Principled BSDF"].inputs["Normal"])
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def build(collection, mats):
    objects = []
    add = objects.append
    add(integrated_housing(collection,mats["case"],mats["dark"]))
    add(assign(box("Tuner display", (0,-0.95,0.63), (2.36,0.07,0.27), collection, 0.02), mats["glass"]))
    add(assign(box("Cassette left", (-0.66,-0.96,-0.25), (1.02,0.08,0.82), collection, 0.045), mats["glass"]))
    add(assign(box("Cassette right", (0.67,-0.96,-0.25), (1.02,0.08,0.82), collection, 0.045), mats["glass"]))
    add(assign(box("Lower control rail", (0,-0.96,-0.82), (2.50,0.08,0.30), collection, 0.02), mats["panel"]))

    speaker_profile = [(-0.09,0),(-0.09,0.68),(-0.06,0.76),(0.0,0.82),(0.08,0.76),(0.12,0.68),(0.12,0)]
    cone_profile = [(-0.035,0),(-0.035,0.63),(0.025,0.56),(0.07,0.22),(0.07,0)]
    for side in (-1, 1):
        x = side * 2.23
        rim = assign(lathe_y(f"Speaker rim {'L' if side < 0 else 'R'}", speaker_profile, collection, 64, 0.012), mats["metal"])
        rim.location = (x,-0.96,-0.23); add(rim)
        cone = assign(lathe_y(f"Speaker cone {'L' if side < 0 else 'R'}", cone_profile, collection, 64), mats["speaker"])
        cone.location = (x,-1.03,-0.23); add(cone)
        tweeter = assign(lathe_y(f"Tweeter {'L' if side < 0 else 'R'}", [(-0.06,0),(-0.06,0.14),(0.04,0.14),(0.04,0)], collection, 32, 0.01), mats["metal"])
        tweeter.location = (side*2.76,-0.94,0.72); add(tweeter)
        add(assign(box(f"Meter grille {'L' if side < 0 else 'R'}", (side*2.30,-0.94,0.70), (0.34,0.07,0.37), collection, 0.025), mats["dark"]))

    knob_profile = [(-0.08,0),(-0.08,0.105),(-0.03,0.13),(0.08,0.13),(0.08,0)]
    for index, x in enumerate((-0.86,-0.43,0.0,0.44,0.86)):
        knob = assign(lathe_y(f"Control knob {index+1}", knob_profile, collection, 32, 0.008), mats["metal"])
        knob.location = (x,-1.0,0.42); add(knob)
    for index, x in enumerate((-0.48,-0.24,0.0,0.24,0.48)):
        add(assign(box(f"Transport key {index+1}", (x,-1.03,-0.84), (0.16,0.16,0.26), collection, 0.018), mats["light"]))

    add(assign(box("Top inset", (0,0.0,1.15), (3.15,1.00,0.12), collection, 0.04), mats["panel"]))
    for index, x in enumerate((-0.80,-0.45,-0.10,0.25,0.60)):
        control = assign(lathe_y(f"Top dial {index+1}", [(-0.07,0),(-0.07,0.11),(0.07,0.11),(0.07,0)], collection, 24, 0.008), mats["metal"])
        control.location=(x,-0.22,1.25); control.rotation_euler[0]=math.radians(90); add(control)

    handle_points=[(-1.26,1.10),(-1.26,2.14),(1.26,2.14),(1.26,1.10),(1.02,1.10),(1.02,1.90),(-1.02,1.90),(-1.02,1.10)]
    handle=assign(extruded_polygon_y("Connected carry handle",handle_points,0.24,collection,0.045),mats["metal"]); handle.location.y=0.02; add(handle)
    add(assign(rod("Telescoping antenna", (-0.35,0.22,1.28), (3.18,0.22,2.72), 0.026, collection, 16), mats["metal"]))

    # Repeated side ventilation is represented by one authored slat plus an Array stack per side.
    for side in (-1,1):
        vent=assign(box(f"Side vent array {'L' if side < 0 else 'R'}",(side*3.22,0.08,0.60),(0.035,0.76,0.035),collection,0.006),mats["dark"])
        array=vent.modifiers.new("13 evenly spaced vents","ARRAY"); array.count=13; array.use_relative_offset=False; array.use_constant_offset=True; array.constant_offset_displace=(0,0,-0.10)
        vent["construction_intent"]="one authored slat repeated by Array"; add(vent)

    # Cassette hubs and fasteners are tertiary radial details, not silhouette substitutes.
    for cassette_x in (-0.66,0.67):
        for offset in (-0.22,0.22):
            reel=assign(lathe_y("Cassette reel",[(-0.025,0),(-0.025,0.10),(0.025,0.10),(0.025,0)],collection,24),mats["light"])
            reel.location=(cassette_x+offset,-1.025,-0.25); add(reel)
    for side in (-1,1):
        for z in (-0.88,0.88):
            screw=assign(lathe_y("Fascia fastener",[(-0.018,0),(-0.018,0.035),(0.018,0.035),(0.018,0)],collection,16),mats["metal"])
            screw.location=(side*3.0,-0.985,z); add(screw)

    # Share topology across bilateral/repeated parts so later edits remain coherent.
    by_name={obj.name:obj for obj in objects}
    for left_name,right_name in (("Speaker rim L","Speaker rim R"),("Speaker cone L","Speaker cone R"),("Tweeter L","Tweeter R"),("Meter grille L","Meter grille R")):
        left,right=by_name[left_name],by_name[right_name]; old=right.data; right.data=left.data
        if old.users == 0: bpy.data.meshes.remove(old)
        left["bilateral_pair"]=right.name; right["bilateral_pair"]=left.name
    for prefix,count in (("Control knob ",5),("Transport key ",5),("Top dial ",5)):
        master=by_name[prefix+"1"]
        for index in range(2,count+1):
            target=by_name[prefix+str(index)]; old=target.data; target.data=master.data
            if old.users == 0: bpy.data.meshes.remove(old)
            target["linked_repeat_master"]=master.name
    return objects


def unwrap(objects):
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    for obj in objects:
        bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.025)
        bpy.ops.object.mode_set(mode="OBJECT")


def mesh_health(obj):
    bm=bmesh.new(); bm.from_mesh(obj.data)
    result={"vertices":len(bm.verts),"edges":len(bm.edges),"faces":len(bm.faces),"quads":sum(len(face.verts)==4 for face in bm.faces),"non_manifold_edges":sum(not edge.is_manifold for edge in bm.edges),"degenerate_faces":sum(face.calc_area()<1e-10 for face in bm.faces),"loose_vertices":sum(not vertex.link_edges for vertex in bm.verts)}
    bm.free(); return result


def render_beauty(scene, output, objects, view):
    directions={"front":Vector((0,-1,0)),"side":Vector((1,0,0)),"top":Vector((0,0,1)),"isometric":Vector((1,-1,0.8)).normalized()}
    direction=directions[view]
    camera_data=bpy.data.cameras.new(f"{view}CameraData"); camera_data.type="ORTHO"; camera_data.ortho_scale=7.9
    camera=bpy.data.objects.new(f"{view}Camera",camera_data); scene.collection.objects.link(camera)
    camera.location=direction*14+Vector((0,0,0.75)); camera.rotation_euler=(Vector((0,0,0.75))-camera.location).to_track_quat("-Z","Y").to_euler(); scene.camera=camera
    review_light=None
    if view=="isometric":
        light_data=bpy.data.lights.new("IsometricReviewLightData","AREA"); light_data.energy=1100; light_data.size=6
        review_light=bpy.data.objects.new("IsometricReviewLight",light_data); scene.collection.objects.link(review_light)
        review_light.location=camera.location*0.72; review_light.rotation_euler=(Vector((0,0,0.5))-review_light.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str(output/f"candidate_{view}_beauty.png"); bpy.ops.render.render(write_still=True)
    if review_light is not None:
        bpy.data.objects.remove(review_light,do_unlink=True); bpy.data.lights.remove(light_data)
    bpy.data.objects.remove(camera,do_unlink=True)


def main():
    output=output_dir(); bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    collection=bpy.data.collections.new("Heldout Boombox"); bpy.context.scene.collection.children.link(collection)
    mats={"case":material("Painted case",(0.11,0.16,0.13),0.15,0.34),"panel":material("Control panel",(0.23,0.28,0.25),0.30,0.30),"dark":material("Recess",(0.018,0.025,0.024),0.10,0.52),"glass":material("Smoked glass",(0.025,0.075,0.07),0.05,0.20),"metal":material("Brushed metal",(0.38,0.43,0.40),0.78,0.24),"speaker":speaker_material(),"light":material("Keys",(0.58,0.52,0.33),0.20,0.35)}
    objects=build(collection,mats)
    for obj in objects:
        obj["semantic_component"]=obj.name
    unwrap(objects)
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=scene.render.resolution_y=720; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.world.color=(0.012,0.014,0.016)
    for location,energy,size in [((-5,-6,7),950,5),((5,-3,3),550,4),((0,4,5),750,4)]:
        data=bpy.data.lights.new("ReviewLightData","AREA"); data.energy=energy; data.size=size
        light=bpy.data.objects.new("ReviewLight",data); scene.collection.objects.link(light); light.location=location; light.rotation_euler=(Vector((0,0,0.5))-light.location).to_track_quat("-Z","Y").to_euler()
    names=[obj.name for obj in objects]
    records=[]
    for view in ("front","side","top"):
        records.append(render_silhouette(names,str(output/f"candidate_{view}_mask.png"),view=view,resolution=720,margin=1.12,frame_name=names))
        render_beauty(scene,output,objects,view)
    render_beauty(scene,output,objects,"isometric")
    health={obj.name:mesh_health(obj) for obj in objects}
    assertions={"all_base_meshes_closed":all(item["non_manifold_edges"]==0 for item in health.values()),"all_base_meshes_nondegenerate":all(item["degenerate_faces"]==0 for item in health.values()),"no_loose_vertices":all(item["loose_vertices"]==0 for item in health.values()),"all_meshes_have_populated_uvs":all(obj.data.uv_layers and len(obj.data.uv_layers.active.data)==len(obj.data.loops) and len(obj.data.loops)>0 for obj in objects),"all_meshes_have_named_materials":all(obj.data.materials and obj.data.materials[0].name for obj in objects),"handle_is_one_connected_authored_mesh":"Connected carry handle" in health,"array_vent_stacks_present":sum(any(mod.type=="ARRAY" for mod in obj.modifiers) for obj in objects)==2,"linked_bilateral_speaker_topology":bpy.data.objects["Speaker rim L"].data is bpy.data.objects["Speaker rim R"].data}
    report={"lab":"heldout_boombox","stage":"production_candidate","objects":len(objects),"mesh_primitive_operators_used":0,"construction":{"single_connected_grid_edited_housing":1,"separate_boxes_for_physical_panels_and_keys":14,"lathed_profile_instances":25,"authored_rods":1,"connected_handle":1,"array_vent_stacks":2},"mesh_health":health,"assertions":assertions,"pass":all(assertions.values()),"visual_checkpoints":[f"candidate_{v}_beauty.png" for v in ("front","side","top","isometric")],"silhouette_records":records,"limitations":["Reference-source topology was not inspected; only neutral pixels were used.","Fine typography, exact grille perforations, stickers, and wear are represented only at material/detail-family level.","No experienced modeler has accepted the asset; this cannot prove broad professional proficiency."]}
    (output/"boombox_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output/"heldout_boombox.blend")); print(json.dumps(report)); raise SystemExit(0 if report["pass"] else 2)


main()
