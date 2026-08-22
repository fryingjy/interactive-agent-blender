"""Fresh-process verification for the Stage-7 medical-case GLB delivery."""

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-22_tutorial-cgthoughts-game-asset"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT / "medical_case_low.glb"))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
images = sorted({
    node.image.name
    for material in bpy.data.materials
    if material and material.use_nodes
    for node in material.node_tree.nodes
    if node.type == "TEX_IMAGE" and node.image
})
report = {
    "schema_version": 1,
    "record_type": "FRESH_GLTF_IMPORT_VERIFICATION",
    "mesh_count": len(meshes),
    "mesh_names": sorted(obj.name for obj in meshes),
    "all_meshes_have_uvs": all(obj.data.uv_layers.active and len(obj.data.uv_layers.active.data) > 0 for obj in meshes),
    "material_count": len([material for material in bpy.data.materials if material]),
    "image_names": images,
    "total_faces": sum(len(obj.data.polygons) for obj in meshes),
}
report["pass"] = (
    report["mesh_count"] == 6
    and report["all_meshes_have_uvs"]
    and report["material_count"] >= 3
    and report["total_faces"] > 0
)
(OUT / "fresh_import_verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["pass"] else 2)
