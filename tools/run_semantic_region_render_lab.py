"""Create, validate, render, and stale-reject a persistent semantic face region."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]; OPS=ROOT/"blender_ops"
if str(OPS) not in sys.path: sys.path.insert(0,str(OPS))

import decision_state
import persistent_ids
import render_passes
import semantic_regions


def main():
    out=ROOT/"runs"/"2026-08-10_semantic-region-render"; out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add(); obj=bpy.context.object; obj.name="RegionRenderCube"
    bpy.context.scene["scene_revision"]=77
    persistent_ids.ensure_persistent_ids(obj.name)
    maps=persistent_ids.get_id_maps(obj.name)
    top_face=max(obj.data.polygons,key=lambda face:face.center.z)
    face_id=maps["faces"]["index_to_id"][str(top_face.index)] if isinstance(next(iter(maps["faces"]["index_to_id"])),str) else maps["faces"]["index_to_id"][top_face.index]
    created=semantic_regions.create_region(obj.name,"top_panel","flat_panel",face_ids=[face_id])
    rendered=render_passes.render_semantic_region(obj.name,"top_panel",str(out/"top_panel_isometric.png"),view="isometric",resolution=256,margin=1.2)
    region=json.loads(obj["agent_semantic_regions"]); region["top_panel"]["face_ids"].append(999999999); obj["agent_semantic_regions"]=json.dumps(region)
    stale=render_passes.render_semantic_region(obj.name,"top_panel",str(out/"must_not_render.png"),view="front",resolution=128)
    assertions={
        "region_created_and_role_recognized":"error" not in created and created["role_recognized"],
        "render_nonblank":rendered.get("foreground_fill_ratio",0)>0,
        "region_and_context_colored":rendered.get("dominant_channel_pixel_counts",{}).get("red",0)>100 and rendered.get("dominant_channel_pixel_counts",{}).get("green",0)>100,
        "metadata_complete":rendered.get("geometry_source")=="BASE_CAGE" and rendered.get("scene_revision")==77 and rendered.get("region_face_count")==1,
        "stale_region_rejected":stale.get("error")=="semantic region is stale" and 999999999 in stale.get("missing_face_ids",[]),
        "stale_file_not_created":not (out/"must_not_render.png").exists(),
    }
    report={"lab":"semantic_selected_region_render","created":created,"rendered":rendered,"stale_attempt":stale,"assertions":assertions,"pass":all(assertions.values())}
    (out/"semantic_region_render_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    # Restore valid persisted region before saving the evidence scene.
    region["top_panel"]["face_ids"]=[face_id]; obj["agent_semantic_regions"]=json.dumps(region)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"semantic_region_render_lab.blend"))
    print("SEMANTIC_REGION_RESULT:"+json.dumps(report))
    if not report["pass"]: raise SystemExit(2)


if __name__=="__main__": main()
