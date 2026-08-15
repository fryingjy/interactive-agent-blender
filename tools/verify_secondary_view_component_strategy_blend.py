"""Fresh Blender-process audit for the saved secondary-view strategy fixture."""

from __future__ import annotations

import json
import hashlib
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_secondary-view-component-strategy"
BLENDER_OPS = ROOT / "blender_ops"
if str(BLENDER_OPS) not in sys.path:
    sys.path.insert(0, str(BLENDER_OPS))

from render_passes import render_silhouette


FAMILIES = {
    "box": {
        "target": ["Box_Target_Truth"],
        "continuous": ["Box_Continuous"],
        "separate": ["Box_Separate_Body", "Box_Separate_Plate"],
    },
    "radial": {
        "target": ["Radial_Target_Truth"],
        "continuous": ["Radial_Continuous"],
        "separate": ["Radial_Separate_Body", "Radial_Separate_Plate"],
    },
}


def connected_components(obj) -> int:
    mesh = obj.data
    adjacency = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    unseen = set(adjacency)
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            current = stack.pop()
            neighbors = adjacency[current] & unseen
            unseen.difference_update(neighbors)
            stack.extend(neighbors)
    return count


def union_dimensions(names: list[str]) -> list[float]:
    points = []
    for name in names:
        obj = bpy.data.objects[name]
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    mins = [min(point[index] for point in points) for index in range(3)]
    maxs = [max(point[index] for point in points) for index in range(3)]
    return [maxs[index] - mins[index] for index in range(3)]


def candidate_record(names: list[str]) -> dict:
    objects = [bpy.data.objects[name] for name in names]
    return {
        "object_names": names,
        "object_count": len(objects),
        "connected_component_count": sum(connected_components(obj) for obj in objects),
        "vertex_count": sum(len(obj.data.vertices) for obj in objects),
        "face_count": sum(len(obj.data.polygons) for obj in objects),
        "modifier_count": sum(len(obj.modifiers) for obj in objects),
        "dimensions_xyz": union_dimensions(names),
        "component_policies": sorted({str(obj.get("component_policy", "")) for obj in objects}),
        "candidate_ids": sorted({str(obj.get("candidate_id", "")) for obj in objects}),
    }


def mask_hash(path: Path) -> str:
    image = bpy.data.images.load(str(path))
    try:
        alpha = image.pixels[3::4]
        packed = bytes(1 if value > 0.5 else 0 for value in alpha)
        return hashlib.sha256(packed).hexdigest()
    finally:
        bpy.data.images.remove(image)


def main() -> None:
    expected = {name for family in FAMILIES.values() for names in family.values() for name in names}
    actual = {obj.name for obj in bpy.data.objects if obj.type == "MESH"}
    build = json.loads((OUT / "blender_build_report.json").read_text(encoding="utf-8"))
    records = {}
    renders = []
    mask_hash_matches = {}
    with tempfile.TemporaryDirectory(prefix="secondary-view-verify-") as temp:
        temp_dir = Path(temp)
        for family, groups in FAMILIES.items():
            records[family] = {
                label: candidate_record(names) for label, names in groups.items()
            }
            mask_hash_matches[family] = {}
            for view in ("front", "top"):
                mask_hash_matches[family][view] = {}
                for label, names in groups.items():
                    output = temp_dir / f"{family}_{label}_{view}.png"
                    record = render_silhouette(
                        names, str(output), view=view, resolution=384, margin=1.18,
                        frame_name=groups["target"],
                    )
                    record["output_path"] = None
                    record["retained"] = False
                    renders.append(record)
                    expected_hash = build["mask_evidence"][family][view][label]["sha256"]
                    mask_hash_matches[family][view][label] = mask_hash(output) == expected_hash
    checks = {
        "exact_mesh_object_set": actual == expected,
        "expected_collections_present": {
            "REFERENCE_TRUTH", "STRATEGY_CANDIDATES"
        }.issubset(bpy.data.collections.keys()),
        "scene_contract_bound": bpy.context.scene.get("experiment") == "secondary-view-component-strategy",
        "continuous_candidates_one_object": all(
            records[family]["continuous"]["object_count"] == 1 for family in records
        ),
        "continuous_candidates_one_connected_component": all(
            records[family]["continuous"]["connected_component_count"] == 1 for family in records
        ),
        "separate_candidates_two_objects": all(
            records[family]["separate"]["object_count"] == 2 for family in records
        ),
        "separate_candidates_two_connected_components": all(
            records[family]["separate"]["connected_component_count"] == 2 for family in records
        ),
        "no_fixture_modifiers": all(
            candidate["modifier_count"] == 0
            for family in records.values() for candidate in family.values()
        ),
        "all_renders_completed": all("error" not in record for record in renders),
        "all_mask_hashes_reproduced": all(
            matches
            for family in mask_hash_matches.values()
            for view in family.values()
            for matches in view.values()
        ),
    }
    report = {
        "blender_version": bpy.app.version_string,
        "blend_file": bpy.data.filepath,
        "families": records,
        "renders": renders,
        "mask_hash_matches": mask_hash_matches,
        "checks": checks,
        "pass": all(checks.values()),
    }
    (OUT / "fresh_process_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
