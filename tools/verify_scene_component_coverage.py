"""Verify a saved Blender build against an evidence-bound component board.

Run from a fresh Blender process:

    blender --background --factory-startup --python-exit-code 1 --python \
      tools/verify_scene_component_coverage.py -- \
      ASSET.blend scene_decomposition.json COLLECTION_NAME report.json

Use ``ALL`` for COLLECTION_NAME when the board deliberately spans more than one
collection.  This is a component-presence gate only: it proves neither visual
likeness nor construction quality, and it never replaces human reference review.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.scene_decomposition import scene_decomposition_from_dict


def parse_args() -> tuple[Path, Path, str, Path]:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 4:
        raise SystemExit(
            "expected ASSET.blend scene_decomposition.json COLLECTION_NAME report.json after --"
        )
    blend, decomposition, collection, report = values
    return Path(blend).resolve(), Path(decomposition).resolve(), collection, Path(report).resolve()


def mesh_objects(collection_name: str):
    if collection_name == "ALL":
        objects = bpy.data.objects
    else:
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            raise SystemExit(f"missing collection: {collection_name}")
        objects = collection.all_objects
    return sorted((object for object in objects if object.type == "MESH"), key=lambda object: object.name)


def evaluated_bounds(objects) -> dict[str, dict[str, list[float]]]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    result = {}
    for object in objects:
        evaluated = object.evaluated_get(depsgraph)
        corners = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
        result[object.name] = {
            "min": [min(corner[axis] for corner in corners) for axis in range(3)],
            "max": [max(corner[axis] for corner in corners) for axis in range(3)],
        }
    return result


def semantic_region_records(objects) -> dict[str, dict[str, dict[str, object]]]:
    """Read persisted semantic regions and verify every referenced element ID.

    The live modeler performs the same validation through ``semantic_regions``.
    This independent verifier reads the saved datablocks directly so a region
    name alone cannot satisfy connected-component coverage after reload.
    """
    result: dict[str, dict[str, dict[str, object]]] = {}
    domain_attributes = {
        "vertex_ids": "agent_vertex_id",
        "edge_ids": "agent_edge_id",
        "face_ids": "agent_face_id",
    }
    for object in objects:
        records: dict[str, dict[str, object]] = {}
        try:
            regions = json.loads(object.get("agent_semantic_regions", "{}"))
        except (TypeError, json.JSONDecodeError):
            regions = {}
        available: dict[str, set[int]] = {}
        for key, attribute_name in domain_attributes.items():
            attribute = object.data.attributes.get(attribute_name)
            available[key] = (
                {int(item.value) for item in attribute.data}
                if attribute is not None else set()
            )
        for region_id, region in regions.items():
            missing = {
                key: sorted(set(region.get(key, [])) - available[key])
                for key in domain_attributes
            }
            element_count = sum(len(region.get(key, [])) for key in domain_attributes)
            records[region_id] = {
                "valid": not any(missing.values()),
                "element_count": element_count,
                "missing_ids": missing,
            }
        result[object.name] = records
    return result


def main() -> int:
    blend_path, decomposition_path, collection_name, report_path = parse_args()
    bpy.ops.wm.open_mainfile(filepath=str(blend_path), load_ui=False)
    decomposition = scene_decomposition_from_dict(
        json.loads(decomposition_path.read_text(encoding="utf-8"))
    )
    objects = mesh_objects(collection_name)
    object_names = [object.name for object in objects]
    semantic_records = semantic_region_records(objects)
    coverage = decomposition.check_object_coverage(object_names, semantic_records)
    component_layout = decomposition.check_component_layout(evaluated_bounds(objects), semantic_records)
    passed = coverage["coverage_ok"] and (
        not component_layout["layout_expectations_present"] or component_layout["layout_ok"]
    )
    report = {
        "schema_version": 3,
        "scope": (
            "Fresh-process component-presence plus optional coarse placement/proportion smoke test. "
            "Passing does not prove reference likeness, silhouette, topology, modifier quality, or human approval."
        ),
        "blend_path": str(blend_path),
        "decomposition_path": str(decomposition_path),
        "collection": collection_name,
        "mesh_object_names": object_names,
        "semantic_region_records": semantic_records,
        "coverage": coverage,
        "component_layout": component_layout,
        "pass": passed,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("COMPONENT_COVERAGE_RESULT:" + json.dumps(report))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
