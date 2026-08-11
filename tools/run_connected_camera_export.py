"""Export the accepted connected camera to GLB and verify a fresh reimport."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def arguments():
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 3:
        raise SystemExit("expected BLEND_FILE GLB_FILE REPORT_FILE after --")
    return tuple(Path(value).resolve() for value in values)


def dimensions(obj):
    return [round(value, 6) for value in obj.dimensions]


def evaluated_dimensions(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    coordinates = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    values = [round(max(point[axis] for point in coordinates) - min(point[axis] for point in coordinates), 6) for axis in range(3)]
    evaluated.to_mesh_clear()
    return values


def main():
    blend_file, glb_file, report_file = arguments()
    bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError(f"expected one source mesh, found {len(meshes)}")
    source = meshes[0]
    source_dimensions = evaluated_dimensions(source)
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    glb_file.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(glb_file),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
        export_texcoords=True,
    )

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb_file))
    imported = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    imported_dimensions = dimensions(imported[0]) if len(imported) == 1 else []
    dimension_error = max((abs(a - b) for a, b in zip(source_dimensions, imported_dimensions)), default=999.0)
    assertions = {
        "glb_is_nonempty": glb_file.is_file() and glb_file.stat().st_size > 1000,
        "one_mesh_round_trips": len(imported) == 1,
        "dimensions_round_trip": dimension_error < 0.001,
        "uvs_round_trip": len(imported) == 1 and bool(imported[0].data.uv_layers),
        "four_material_regions_round_trip": len(imported) == 1 and len(imported[0].data.materials) == 4,
        "evaluated_geometry_exported": len(imported) == 1 and len(imported[0].data.vertices) > 1000,
    }
    report = {
        "lab": "connected_camera_glb_roundtrip",
        "source": str(blend_file),
        "glb": str(glb_file),
        "glb_bytes": glb_file.stat().st_size if glb_file.is_file() else 0,
        "source_dimensions": source_dimensions,
        "imported_dimensions": imported_dimensions,
        "dimension_max_error": round(dimension_error, 8),
        "imported_meshes": len(imported),
        "imported_vertices": len(imported[0].data.vertices) if len(imported) == 1 else 0,
        "imported_polygons": len(imported[0].data.polygons) if len(imported) == 1 else 0,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CONNECTED_CAMERA_EXPORT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


main()
