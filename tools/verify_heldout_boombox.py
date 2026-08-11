"""Fresh-process verifier for the held-out boombox production candidate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def run_dir():
    values=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(values)!=1: raise SystemExit("expected RUN_DIR after --")
    return Path(values[0]).resolve()


def health(obj,evaluated=False):
    owner=None; mesh=obj.data
    if evaluated:
        owner=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=owner.to_mesh()
    bm=bmesh.new(); bm.from_mesh(mesh)
    seen=set(); components=0
    for vertex in bm.verts:
        if vertex in seen: continue
        components+=1; stack=[vertex]; seen.add(vertex)
        while stack:
            current=stack.pop()
            for edge in current.link_edges:
                other=edge.other_vert(current)
                if other not in seen: seen.add(other); stack.append(other)
    result={"vertices":len(bm.verts),"faces":len(bm.faces),"non_manifold_edges":sum(not edge.is_manifold for edge in bm.edges),"degenerate_faces":sum(face.calc_area()<1e-10 for face in bm.faces),"loose_vertices":sum(not vertex.link_edges for vertex in bm.verts),"components":components}
    bm.free()
    if owner: owner.to_mesh_clear()
    return result


def main():
    run=run_dir(); final=run/"final"; bpy.ops.wm.open_mainfile(filepath=str(final/"heldout_boombox.blend"),load_ui=False)
    report=json.loads((final/"boombox_report.json").read_text(encoding="utf-8")); silhouette=json.loads((final/"normalized_silhouette_report.json").read_text(encoding="utf-8"))
    objects=sorted((obj for obj in bpy.data.objects if obj.type=="MESH"),key=lambda obj:obj.name)
    base={obj.name:health(obj) for obj in objects}; evaluated={obj.name:health(obj,True) for obj in objects}
    handle=bpy.data.objects.get("Connected carry handle"); left=bpy.data.objects.get("Speaker rim L"); right=bpy.data.objects.get("Speaker rim R")
    arrays=[(obj.name,modifier.count) for obj in objects for modifier in obj.modifiers if modifier.type=="ARRAY"]
    bevels=[(obj.name,modifier.width,modifier.segments) for obj in objects for modifier in obj.modifiers if modifier.type=="BEVEL"]
    uv_state={obj.name:{"layers":len(obj.data.uv_layers),"loops":len(obj.data.loops),"uv_loops":len(obj.data.uv_layers.active.data) if obj.data.uv_layers.active else 0,"nonzero_uv":any(abs(value)>1e-7 for loop in (obj.data.uv_layers.active.data if obj.data.uv_layers.active else []) for value in loop.uv)} for obj in objects}
    images={path.name:{"bytes":path.stat().st_size} for path in final.glob("candidate_*_beauty.png")}
    assertions={
        "generator_report_passes":report.get("pass") is True,
        "declared_silhouette_gates_pass":silhouette.get("pass") is True and silhouette.get("thresholds")=={"front":0.82,"side":0.72,"top":0.72,"mean":0.78},
        "exact_semantic_mesh_count":len(objects)==41,
        "base_meshes_closed_clean":all(item["non_manifold_edges"]==0 and item["degenerate_faces"]==0 and item["loose_vertices"]==0 for item in base.values()),
        "evaluated_meshes_closed_clean":all(item["non_manifold_edges"]==0 and item["degenerate_faces"]==0 and item["loose_vertices"]==0 for item in evaluated.values()),
        "connected_handle_is_single_component":handle is not None and base[handle.name]["components"]==1,
        "main_housing_is_one_connected_edited_cage":bpy.data.objects.get("Main integrated chassis") is not None and base["Main integrated chassis"]["components"]==1 and base["Main integrated chassis"]["faces"]>=70 and bpy.data.objects.get("Front fascia") is None and bpy.data.objects.get("Central recessed deck") is None,
        "housing_recess_bevel_is_region_scoped":bpy.data.objects.get("Main integrated chassis") is not None and [modifier.limit_method for modifier in bpy.data.objects["Main integrated chassis"].modifiers if modifier.type=="BEVEL"]==["VGROUP"],
        "speaker_pair_shares_editable_topology":left is not None and right is not None and left.data is right.data,
        "two_thirteen_slat_array_stacks":sorted(count for _,count in arrays)==[13,13],
        "purposeful_bevel_stacks_exist":len(bevels)>=12 and all(width>0 and segments>=2 for _,width,segments in bevels),
        "uvs_are_populated_not_empty_placeholders":all(state["layers"]>=1 and state["uv_loops"]==state["loops"] and state["nonzero_uv"] for state in uv_state.values()),
        "named_node_materials_on_every_mesh":all(obj.data.materials and obj.data.materials[0] and obj.data.materials[0].use_nodes for obj in objects),
        "four_final_beauty_views_exist":len(images)==4 and all(item["bytes"]>1000 for item in images.values()),
        "source_reference_mesh_not_present":all(obj.name.lower()!="boombox" for obj in objects),
    }
    result={"lab":"independent_heldout_boombox_verification","method":"fresh factory-startup Blender; saved scene inspected without generator import","blender_version":bpy.app.version_string,"objects":len(objects),"base_health":base,"evaluated_health":evaluated,"arrays":arrays,"bevel_count":len(bevels),"uv_state":uv_state,"silhouette":silhouette,"images":images,"assertions":assertions,"pass":all(assertions.values())}
    (final/"boombox_verify.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print("BOOMBOX_VERIFY_RESULT:"+json.dumps(result))
    if not result["pass"]: raise SystemExit(2)


main()
