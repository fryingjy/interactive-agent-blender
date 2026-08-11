"""Fresh-process GLB re-import and package verifier for the held-out boombox."""

from __future__ import annotations

import json
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-11_heldout-boombox"
EXPORT = RUN / "export"


def glb_json(path: Path) -> dict:
    with path.open("rb") as handle:
        magic, version, total_length = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF" or version != 2 or total_length != path.stat().st_size:
            raise ValueError("invalid GLB 2.0 header")
        chunk_length, chunk_type = struct.unpack("<II", handle.read(8))
        if chunk_type != 0x4E4F534A:
            raise ValueError("GLB first chunk is not JSON")
        return json.loads(handle.read(chunk_length).decode("utf-8").rstrip(" \x00"))


def imported_state(objects: list[bpy.types.Object]) -> dict:
    triangles = 0
    points = []
    for obj in objects:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    return {
        "mesh_objects": len(objects),
        "triangles": triangles,
        "bounds": {axis: [min(point[index] for point in points), max(point[index] for point in points)] for index, axis in enumerate("xyz")},
        "all_have_uvs": all(obj.data.uv_layers and len(obj.data.uv_layers.active.data) == len(obj.data.loops) for obj in objects),
        "all_have_materials": all(obj.data.materials and obj.data.materials[0] for obj in objects),
        "material_names": sorted({material.name for obj in objects for material in obj.data.materials if material}),
    }


def main() -> None:
    source_report = json.loads((EXPORT / "boombox_export_report.json").read_text(encoding="utf-8"))
    glb_path = EXPORT / "heldout_boombox.glb"
    document = glb_json(glb_path)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    result = bpy.ops.import_scene.gltf(filepath=str(glb_path))
    objects = sorted((obj for obj in bpy.context.scene.objects if obj.type == "MESH"), key=lambda obj: obj.name)
    imported = imported_state(objects)
    source = source_report["source"]
    # The exporter writes Y-up glTF, but Blender's importer converts it back to
    # Blender Z-up. A Blender-to-Blender round trip must therefore recover the
    # original XYZ dimensions rather than expose the package's axis ordering.
    expected_dimensions = [
        source["bounds"]["x"][1] - source["bounds"]["x"][0],
        source["bounds"]["y"][1] - source["bounds"]["y"][0],
        source["bounds"]["z"][1] - source["bounds"]["z"][0],
    ]
    actual_dimensions = [imported["bounds"][axis][1] - imported["bounds"][axis][0] for axis in "xyz"]
    attributes = [set(primitive.get("attributes", {})) for mesh in document.get("meshes", []) for primitive in mesh.get("primitives", [])]
    required = {"POSITION", "NORMAL", "TEXCOORD_0"}
    assertions = {
        "export_report_passes": source_report.get("pass") is True,
        "import_finished": "FINISHED" in result,
        "semantic_mesh_count_preserved": imported["mesh_objects"] == source["mesh_objects"] == 41,
        "evaluated_triangle_count_preserved": imported["triangles"] == source["triangles"],
        "roundtrip_dimensions_preserved": all(abs(a - b) < 1e-4 for a, b in zip(actual_dimensions, expected_dimensions)),
        "uvs_present_after_roundtrip": imported["all_have_uvs"],
        "materials_present_after_roundtrip": imported["all_have_materials"],
        "material_family_count_preserved": len(imported["material_names"]) == len(source["material_names"]),
        "every_glb_primitive_declares_position_normal_uv": bool(attributes) and all(required.issubset(item) for item in attributes),
        "glb_contains_tangents": any("TANGENT" in item for item in attributes),
    }
    report = {
        "lab": "independent_heldout_boombox_glb_roundtrip",
        "method": "fresh factory-startup Blender re-import plus direct GLB 2.0 JSON inspection",
        "blender_version": bpy.app.version_string,
        "source": source,
        "imported": imported,
        "expected_blender_roundtrip_dimensions": expected_dimensions,
        "actual_imported_dimensions": actual_dimensions,
        "primitive_attribute_sets": [sorted(item) for item in attributes],
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (EXPORT / "boombox_export_verify.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("BOOMBOX_EXPORT_VERIFY_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


main()
