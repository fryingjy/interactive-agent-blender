"""Verify an editable high/low prop scene in a fresh Blender process.

Usage:
    blender --background PROP.blend --python tools/verify_editable_prop_variants.py -- \
        CONTRACT.json OUTPUT.json

The contract keeps this verifier prop-agnostic. It checks collection separation,
independent editable mesh datablocks, unapplied/live modifier policy, optional
crease requirements, and topology requirements for designated connected cages.
"""

from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path

import bpy


def arguments() -> tuple[Path, Path]:
    tail = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(tail) != 2:
        raise SystemExit("Expected CONTRACT.json OUTPUT.json after --")
    return Path(tail[0]).resolve(), Path(tail[1]).resolve()


def collection_names(obj: bpy.types.Object) -> list[str]:
    return sorted(collection.name for collection in obj.users_collection)


def modifier_records(obj: bpy.types.Object) -> list[dict]:
    return [
        {
            "name": modifier.name,
            "type": modifier.type,
            "show_viewport": modifier.show_viewport,
            "show_render": modifier.show_render,
            "levels": getattr(modifier, "levels", None),
            "render_levels": getattr(modifier, "render_levels", None),
        }
        for modifier in obj.modifiers
    ]


def connected_components(mesh: bpy.types.Mesh) -> int:
    if not mesh.vertices:
        return 0
    adjacency = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)
    unseen = set(range(len(mesh.vertices)))
    count = 0
    while unseen:
        count += 1
        start = unseen.pop()
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
    return count


def topology_record(obj: bpy.types.Object) -> dict:
    mesh = obj.data
    edge_face_counts = [0] * len(mesh.edges)
    edge_lookup = {tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges}
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for index, vertex in enumerate(vertices):
            key = tuple(sorted((vertex, vertices[(index + 1) % len(vertices)])))
            edge_face_counts[edge_lookup[key]] += 1
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "triangles": sum(len(face.vertices) == 3 for face in mesh.polygons),
        "quads": sum(len(face.vertices) == 4 for face in mesh.polygons),
        "ngons": sum(len(face.vertices) > 4 for face in mesh.polygons),
        "loose_edges": sum(count == 0 for count in edge_face_counts),
        "non_manifold_edges": sum(count not in (0, 2) for count in edge_face_counts),
        "connected_components": connected_components(mesh),
    }


def crease_record(obj: bpy.types.Object) -> dict:
    candidates = []
    for attribute in obj.data.attributes:
        if attribute.domain == "EDGE" and "crease" in attribute.name.lower():
            values = [float(item.value) for item in attribute.data]
            candidates.append(
                {
                    "name": attribute.name,
                    "count_above_zero": sum(value > 1e-6 for value in values),
                    "count_at_or_above_0_8": sum(value >= 0.8 for value in values),
                    "maximum": max(values, default=0.0),
                }
            )
    return {"attributes": candidates}


def find_modifier(obj: bpy.types.Object, modifier_type: str):
    return next((modifier for modifier in obj.modifiers if modifier.type == modifier_type), None)


def main() -> None:
    contract_path, output_path = arguments()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    objects: dict[str, dict] = {}

    high_collection = contract.get("high_collection", "HIGH_POLY")
    low_collection = contract.get("low_collection", "LOW_POLY")
    pairs = contract["pairs"]

    for pair in pairs:
        high = bpy.data.objects.get(pair["high"])
        low = bpy.data.objects.get(pair["low"])
        key = pair.get("component", pair["high"])
        checks[f"{key}:objects_present"] = high is not None and low is not None
        if high is None or low is None:
            continue
        checks[f"{key}:mesh_objects"] = high.type == "MESH" and low.type == "MESH"
        checks[f"{key}:collection_separation"] = (
            collection_names(high) == [high_collection]
            and collection_names(low) == [low_collection]
        )
        checks[f"{key}:independent_mesh_data"] = high.data != low.data
        checks[f"{key}:same_editable_cage_counts"] = (
            len(high.data.vertices) == len(low.data.vertices)
            and len(high.data.edges) == len(low.data.edges)
            and len(high.data.polygons) == len(low.data.polygons)
        )
        low_hidden = {
            "hide_render": low.hide_render,
            "hide_viewport": low.hide_viewport,
            "hidden_in_view_layer": low.hide_get(),
        }
        if pair.get("require_low_hidden"):
            checks[f"{key}:low_hidden"] = low.hide_render and (
                low.hide_viewport or low.hide_get()
            )

        high_modifiers = modifier_records(high)
        low_modifiers = modifier_records(low)
        if pair.get("require_subdivision"):
            high_subd = find_modifier(high, "SUBSURF")
            low_subd = find_modifier(low, "SUBSURF")
            checks[f"{key}:live_subdivision_both"] = high_subd is not None and low_subd is not None
            if high_subd is not None and low_subd is not None:
                checks[f"{key}:low_subdivision_zero"] = low_subd.levels == 0
        if pair.get("disabled_bevel"):
            bevel = find_modifier(high, "BEVEL")
            checks[f"{key}:broad_bevel_disabled"] = bool(
                bevel and not bevel.show_viewport and not bevel.show_render
            )
        if pair.get("live_bevel"):
            bevel = find_modifier(high, "BEVEL")
            checks[f"{key}:bevel_live_unapplied"] = bool(
                bevel and bevel.show_viewport and bevel.show_render
            )

        topology = topology_record(high)
        crease = crease_record(high)
        if pair.get("connected_all_quad_cage"):
            checks[f"{key}:single_connected_cage"] = topology["connected_components"] == 1
            checks[f"{key}:all_quad_cage"] = (
                topology["faces"] > 0
                and topology["quads"] == topology["faces"]
                and topology["triangles"] == 0
                and topology["ngons"] == 0
            )
            checks[f"{key}:no_loose_or_nonmanifold_edges"] = (
                topology["loose_edges"] == 0 and topology["non_manifold_edges"] == 0
            )
        minimum_creases = pair.get("minimum_creased_edges")
        if minimum_creases is not None:
            strong_creases = sum(
                item["count_at_or_above_0_8"] for item in crease["attributes"]
            )
            checks[f"{key}:semantic_creases_present"] = strong_creases >= minimum_creases

        objects[key] = {
            "high": pair["high"],
            "low": pair["low"],
            "high_collections": collection_names(high),
            "low_collections": collection_names(low),
            "low_visibility": low_hidden,
            "topology": topology,
            "creases": crease,
            "high_modifiers": high_modifiers,
            "low_modifiers": low_modifiers,
        }

    report = {
        "schema_version": 1,
        "record_type": "EDITABLE_PROP_VARIANT_VERIFICATION",
        "verification": "fresh_process_saved_blend_inspection",
        "blend_file": bpy.data.filepath,
        "contract": str(contract_path),
        "objects": objects,
        "checks": checks,
        "pass": bool(checks) and all(checks.values()),
        "boundary": (
            "This verifies saved editable structure and declared modifier policy. "
            "It does not claim final likeness, production retopology, UV, materials, or human acceptance."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "pass": report["pass"]}, indent=2))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
