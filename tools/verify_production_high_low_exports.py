"""Import each low-only GLB in a fresh Blender process and verify production payload basics."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_production-high-low-audit"


def clear() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def inspect_export(path: Path) -> dict:
    clear()
    images_before = {image.name for image in bpy.data.images}
    result = bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    materials = {material.name for obj in meshes for material in obj.data.materials if material}
    images = {
        image.name
        for image in bpy.data.images
        if image.source != "VIEWER" and image.name not in images_before
    }
    return {
        "path": str(path),
        "operator_result": sorted(result),
        "mesh_count": len(meshes),
        "mesh_names": [obj.name for obj in meshes],
        "face_count": sum(len(obj.data.polygons) for obj in meshes),
        "uv_layers": {obj.name: list(obj.data.uv_layers.keys()) for obj in meshes},
        "materials": sorted(materials),
        "images": sorted(images),
        "dimensions": {obj.name: list(obj.dimensions) for obj in meshes},
    }


def main() -> None:
    contract = json.loads((OUT / "experiment_contract.json").read_text(encoding="utf-8"))
    build = json.loads((OUT / "build_report.json").read_text(encoding="utf-8"))
    exports = {
        family: inspect_export(Path(path)) for family, path in build["exports"].items()
    }
    expected_meshes = contract["frozen_gates"]["glb_mesh_count"]
    checks = {
        family + "_imports": "FINISHED" in record["operator_result"]
        for family, record in exports.items()
    }
    checks.update({
        family + "_one_mesh": record["mesh_count"] == expected_meshes
        for family, record in exports.items()
    })
    checks.update({
        family + "_has_uv_material_and_normal_image": bool(
            record["face_count"] > 0
            and all(record["uv_layers"].values())
            and record["materials"]
            and record["images"]
        )
        for family, record in exports.items()
    })
    report = {
        "blender_version": bpy.app.version_string,
        "exports": exports,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": "GLB payload verification does not prove target-engine shading parity.",
    }
    (OUT / "fresh_export_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"checks": checks, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
