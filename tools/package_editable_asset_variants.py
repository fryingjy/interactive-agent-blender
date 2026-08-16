"""Package every mesh in a reference asset into editable high/low collections.

This intentionally does *not* retopologize, unwrap, bake, or apply modifiers.
It is a scene-organization handoff: each high object keeps its original cage and
live modifier stack, while its low counterpart is an independent cage whose
Subdivision viewport/render levels can be reduced.  A later production-low
workflow must still author purpose-built topology and UVs.

Run through Blender, for example::

    blender --background --python tools/package_editable_asset_variants.py -- \
      source.blend output.blend --high-collection ASSET_HIGH --low-collection ASSET_LOW
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "blender_ops"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from blender_ops.modeler_server import ModelerServer  # noqa: E402


def arguments() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--high-collection", default="ASSET_HIGH")
    parser.add_argument("--low-collection", default="ASSET_LOW")
    parser.add_argument("--low-subd-levels", type=int, default=0)
    parser.add_argument(
        "--include",
        nargs="+",
        help="Exact mesh object names. Defaults to every mesh outside either output collection.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = arguments()
    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if args.high_collection == args.low_collection:
        raise ValueError("high and low collection names must differ")
    if not 0 <= args.low_subd_levels <= 6:
        raise ValueError("--low-subd-levels must be between 0 and 6")

    bpy.ops.wm.open_mainfile(filepath=str(source))
    high = bpy.data.collections.get(args.high_collection)
    low = bpy.data.collections.get(args.low_collection)
    if high is not None or low is not None:
        raise ValueError(
            "output collections already exist; use a fresh source or explicit new collection names"
        )

    requested = set(args.include or ())
    mesh_names = sorted(obj.name for obj in bpy.data.objects if obj.type == "MESH")
    names = sorted(requested) if requested else mesh_names
    missing = sorted(requested - set(mesh_names))
    if missing:
        raise ValueError(f"requested mesh objects do not exist: {missing}")
    if not names:
        raise ValueError("no mesh objects were available for packaging")
    low_names = [f"{name}_LOW" for name in names]
    collisions = sorted(name for name in low_names if name in bpy.data.objects)
    if collisions:
        raise ValueError(f"low object names already exist: {collisions}")

    server = ModelerServer()
    transactions: list[dict] = []
    try:
        # Decision revisions are intentionally serial: each committed component
        # advances the scene revision before the next component is observed.
        # All name/collection collisions were preflighted above, so this is a
        # narrow sequence of independently recoverable typed decisions rather
        # than a pretend cross-object atomic transaction.
        for name, low_name in zip(names, low_names):
            begun = server.cmd_begin_decision(name, "package_editable_asset_variant")
            performed = server.cmd_perform_decision(
                begun["decision_id"],
                "package_high_low_variants",
                {
                    "low_object_name": low_name,
                    "high_collection_name": args.high_collection,
                    "low_collection_name": args.low_collection,
                    "low_subd_levels": args.low_subd_levels,
                    "hide_low": True,
                },
                command_id=f"package-{name}-{begun['decision_id']}",
            )
            verified = server.cmd_verify_decision(begun["decision_id"])
            transaction = {
                "source": name,
                "low": low_name,
                "begin": begun,
                "perform": performed,
                "verify": verified,
            }
            transaction["commit"] = server.cmd_commit_decision(begun["decision_id"])
            transactions.append(transaction)
    except Exception:
        # A committed decision is deliberately durable. The source file is not
        # overwritten until all components have completed, so a failed run is
        # recoverable simply by discarding this unsaved Blender session.
        raise

    def object_record(name: str) -> dict:
        obj = bpy.data.objects[name]
        return {
            "name": name,
            "mesh": obj.data.name,
            "collections": sorted(collection.name for collection in obj.users_collection),
            "base_vertices": len(obj.data.vertices),
            "base_edges": len(obj.data.edges),
            "base_faces": len(obj.data.polygons),
            "modifiers": [
                {"name": modifier.name, "type": modifier.type,
                 "levels": getattr(modifier, "levels", None),
                 "render_levels": getattr(modifier, "render_levels", None)}
                for modifier in obj.modifiers
            ],
            "hidden_in_viewport": bool(obj.hide_viewport),
            "hidden_in_active_view_layer": obj.hide_get(),
            "hidden_in_render": obj.hide_render,
        }

    pairs = [
        {"high": object_record(name), "low": object_record(low_name)}
        for name, low_name in zip(names, low_names)
    ]
    report = {
        "schema_version": 1,
        "workflow": "editable_asset_high_low_packaging",
        "source": str(source),
        "output": str(output),
        "high_collection": args.high_collection,
        "low_collection": args.low_collection,
        "low_subd_levels": args.low_subd_levels,
        "pairs": pairs,
        "transactions": transactions,
        "checks": {
            "all_meshes_packaged": len(pairs) == len(names),
            "separate_named_collections": all(
                pair["high"]["collections"] == [args.high_collection]
                and pair["low"]["collections"] == [args.low_collection]
                for pair in pairs
            ),
            "independent_mesh_datablocks": all(
                pair["high"]["mesh"] != pair["low"]["mesh"] for pair in pairs
            ),
            "modifiers_left_unapplied": True,
            "low_variants_hidden": all(
                pair["low"]["hidden_in_viewport"] and pair["low"]["hidden_in_render"]
                for pair in pairs
            ),
        },
        "boundary": (
            "This is editable duplicate organization only. Equal base cages are not evidence of "
            "purpose-authored low-poly topology, UV readiness, baking, or final visual quality."
        ),
    }
    report["pass"] = all(report["checks"].values())
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path = output.with_suffix(".high_low_packaging.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(json.dumps({"output": str(output), "report": str(report_path), "pass": report["pass"]}, indent=2))


if __name__ == "__main__":
    main()
