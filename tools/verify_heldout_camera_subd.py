"""Independent saved-scene verifier for the held-out camera SubD benchmark."""

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
    bm=bmesh.new(); bm.from_mesh(mesh); seen=set(); components=0
    for vertex in bm.verts:
        if vertex in seen: continue
        components+=1; stack=[vertex]; seen.add(vertex)
        while stack:
            current=stack.pop()
            for edge in current.link_edges:
                other=edge.other_vert(current)
                if other not in seen: seen.add(other); stack.append(other)
    result={"vertices":len(bm.verts),"faces":len(bm.faces),"quads":sum(len(face.verts)==4 for face in bm.faces),"non_manifold_edges":sum(not edge.is_manifold for edge in bm.edges),"degenerate_faces":sum(face.calc_area()<1e-10 for face in bm.faces),"loose_vertices":sum(not vertex.link_edges for vertex in bm.verts),"components":components}
    bm.free()
    if owner: owner.to_mesh_clear()
    return result


def main():
    run=run_dir(); final=run/"final"; bpy.ops.wm.open_mainfile(filepath=str(final/"heldout_camera_final.blend"),load_ui=False)
    generator=json.loads((final/"camera_report.json").read_text(encoding="utf-8")); silhouette=json.loads((final/"normalized_silhouette_report.json").read_text(encoding="utf-8"))
    objects=sorted((obj for obj in bpy.data.objects if obj.type=="MESH"),key=lambda obj:obj.name); base={obj.name:health(obj) for obj in objects}; evaluated={obj.name:health(obj,True) for obj in objects}
    body=bpy.data.objects.get("Main connected SubD body"); left=bpy.data.objects.get("Strap lug L"); right=bpy.data.objects.get("Strap lug R"); frames=[bpy.data.objects.get(name) for name in ("Viewfinder frame","Rangefinder frame","Small front window frame")]
    uv={obj.name:{"loops":len(obj.data.loops),"uv_loops":len(obj.data.uv_layers.active.data) if obj.data.uv_layers.active else 0,"nonzero":any(abs(value)>1e-7 for loop in (obj.data.uv_layers.active.data if obj.data.uv_layers.active else []) for value in loop.uv)} for obj in objects}
    images={path.name:path.stat().st_size for path in final.glob("candidate_*_beauty.png")}
    assertions={
        "generator_report_passes":generator.get("pass") is True,
        "declared_silhouette_gates_pass":silhouette.get("pass") is True and silhouette.get("thresholds")=={"front":0.8,"side":0.68,"top":0.7,"mean":0.76},
        "exact_semantic_mesh_count":len(objects)==19,
        "all_base_meshes_closed_clean":all(item["non_manifold_edges"]==0 and item["degenerate_faces"]==0 and item["loose_vertices"]==0 for item in base.values()),
        "all_evaluated_meshes_closed_clean":all(item["non_manifold_edges"]==0 and item["degenerate_faces"]==0 and item["loose_vertices"]==0 for item in evaluated.values()),
        "body_is_one_connected_all_quad_cage":body is not None and base[body.name]["components"]==1 and base[body.name]["faces"]==base[body.name]["quads"]==54,
        "body_has_controlled_subdivision":body is not None and [(mod.type,mod.levels,mod.render_levels) for mod in body.modifiers]==[("SUBSURF",2,2)],
        "body_records_single_cage_intent":body is not None and "single connected all-quad" in body.get("construction_intent",""),
        "aperture_frames_are_authored_clean_quads":all(frame is not None and base[frame.name]["faces"]==base[frame.name]["quads"]==16 and not frame.modifiers for frame in frames),
        "bilateral_lugs_share_editable_topology":left is not None and right is not None and left.data is right.data,
        "uvs_are_populated":all(state["loops"]>0 and state["uv_loops"]==state["loops"] and state["nonzero"] for state in uv.values()),
        "named_node_materials_on_every_mesh":all(obj.data.materials and obj.data.materials[0] and obj.data.materials[0].use_nodes for obj in objects),
        "four_solid_mode_review_views_exist":len(images)==4 and all(size>1000 for size in images.values()),
        "source_reference_objects_absent":all(not obj.name.startswith("Camera_01") for obj in objects),
    }
    report={"lab":"independent_heldout_camera_subd_verification","method":"fresh factory-startup Blender saved-scene inspection without generator import","blender_version":bpy.app.version_string,"objects":len(objects),"base_health":base,"evaluated_health":evaluated,"uv_state":uv,"silhouette":silhouette,"images":images,"assertions":assertions,"pass":all(assertions.values())}
    (final/"camera_verify.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); print("CAMERA_VERIFY_RESULT:"+json.dumps(report))
    if not report["pass"]: raise SystemExit(2)


main()
