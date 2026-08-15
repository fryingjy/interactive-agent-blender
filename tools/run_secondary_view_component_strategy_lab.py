"""Build two controlled Blender families whose front views hide a depth-strategy error."""

from __future__ import annotations

import json
import hashlib
import math
import sys
import tempfile
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_secondary-view-component-strategy"
BLENDER_OPS = ROOT / "blender_ops"
if str(BLENDER_OPS) not in sys.path:
    sys.path.insert(0, str(BLENDER_OPS))

from render_passes import render_diagnostic_pass, render_silhouette


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)


def collection(name: str):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def move_to(obj, target_collection) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    target_collection.objects.link(obj)


def annotate(obj, *, family: str, candidate: str, policy: str, role: str) -> None:
    obj["experiment_family"] = family
    obj["candidate_id"] = candidate
    obj["component_policy"] = policy
    obj["component_role"] = role


def cube(name: str, dimensions, target_collection, **metadata):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to(obj, target_collection)
    annotate(obj, **metadata)
    return obj


def cylinder(name: str, radius: float, depth: float, center_y: float, target_collection, **metadata):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=depth)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler.x = math.pi / 2.0
    obj.location.y = center_y
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    move_to(obj, target_collection)
    annotate(obj, **metadata)
    return obj


def build_box_family(targets, candidates):
    common = {"family": "box"}
    target = cube(
        "Box_Target_Truth", (4.4, 3.0, 3.0), targets,
        candidate="target", policy="CONTINUOUS_MESH", role="truth", **common,
    )
    continuous = cube(
        "Box_Continuous", (4.4, 3.0, 3.0), candidates,
        candidate="box-continuous", policy="CONTINUOUS_MESH", role="candidate", **common,
    )
    body = cube(
        "Box_Separate_Body", (3.0, 2.8, 3.0), candidates,
        candidate="box-separate", policy="SEPARATE_COMPONENTS", role="body", **common,
    )
    body.location.y = 0.1
    plate = cube(
        "Box_Separate_Plate", (4.4, 0.2, 3.0), candidates,
        candidate="box-separate", policy="SEPARATE_COMPONENTS", role="faceplate", **common,
    )
    plate.location.y = -1.4
    return {
        "target": [target.name],
        "continuous": [continuous.name],
        "separate": [body.name, plate.name],
    }


def build_radial_family(targets, candidates):
    common = {"family": "radial"}
    target = cylinder(
        "Radial_Target_Truth", 2.0, 3.0, 0.0, targets,
        candidate="target", policy="CONTINUOUS_MESH", role="truth", **common,
    )
    continuous = cylinder(
        "Radial_Continuous", 2.0, 3.0, 0.0, candidates,
        candidate="radial-continuous", policy="CONTINUOUS_MESH", role="candidate", **common,
    )
    body = cylinder(
        "Radial_Separate_Body", 1.35, 2.8, 0.1, candidates,
        candidate="radial-separate", policy="SEPARATE_COMPONENTS", role="body", **common,
    )
    plate = cylinder(
        "Radial_Separate_Plate", 2.0, 0.2, -1.4, candidates,
        candidate="radial-separate", policy="SEPARATE_COMPONENTS", role="faceplate", **common,
    )
    return {
        "target": [target.name],
        "continuous": [continuous.name],
        "separate": [body.name, plate.name],
    }


def mask_hash(path: Path) -> str:
    image = bpy.data.images.load(str(path))
    try:
        alpha = image.pixels[3::4]
        packed = bytes(1 if value > 0.5 else 0 for value in alpha)
        return hashlib.sha256(packed).hexdigest()
    finally:
        bpy.data.images.remove(image)


def render_family(
    family: str, objects: dict[str, list[str]], temp_dir: Path
) -> tuple[list[dict], dict]:
    records = []
    evidence = {}
    mask_dir = OUT / "masks"
    review_dir = OUT / "review"
    frame = objects["target"]
    for view in ("front", "top"):
        target_path = mask_dir / f"{family}_target_{view}.png"
        target_record = render_silhouette(
            objects["target"], str(target_path), view=view, resolution=384,
            margin=1.18, frame_name=frame,
        )
        records.append(target_record)
        target_hash = mask_hash(target_path)
        evidence.setdefault(view, {})["target"] = {
            "retained_path": str(target_path),
            "sha256": target_hash,
            "equals_target": True,
        }
        for label in ("continuous", "separate"):
            retained = label == "separate" and view == "top"
            path = (
                mask_dir / f"{family}_{label}_{view}.png"
                if retained else temp_dir / f"{family}_{label}_{view}.png"
            )
            record = render_silhouette(
                objects[label], str(path), view=view, resolution=384,
                margin=1.18, frame_name=frame,
            )
            record["retained"] = retained
            if not retained:
                record["output_path"] = None
            records.append(record)
            candidate_hash = mask_hash(path)
            evidence[view][label] = {
                "retained_path": str(path) if retained else None,
                "sha256": candidate_hash,
                "equals_target": candidate_hash == target_hash,
            }
        for label in ("continuous", "separate"):
            for pass_type in ("solid", "component_mask"):
                path = review_dir / f"{family}_{label}_{view}_{pass_type}.png"
                records.append(render_diagnostic_pass(
                    objects[label], str(path), pass_type, view=view, resolution=384,
                    margin=1.18, frame_name=frame,
                ))
    return records, evidence


def main() -> None:
    clear_scene()
    bpy.context.preferences.filepaths.save_version = 0
    targets = collection("REFERENCE_TRUTH")
    candidates = collection("STRATEGY_CANDIDATES")
    families = {
        "box": build_box_family(targets, candidates),
        "radial": build_radial_family(targets, candidates),
    }
    records = []
    mask_evidence = {}
    with tempfile.TemporaryDirectory(prefix="secondary-view-masks-", dir=OUT) as temp:
        temp_dir = Path(temp)
        for family, objects in families.items():
            family_records, family_evidence = render_family(family, objects, temp_dir)
            records.extend(family_records)
            mask_evidence[family] = family_evidence
    bpy.context.scene["experiment"] = "secondary-view-component-strategy"
    bpy.context.scene["experiment_contract"] = str(OUT / "experiment_contract.json")
    blend_path = OUT / "secondary_view_component_strategy.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report = {
        "blender_version": bpy.app.version_string,
        "blend_path": str(blend_path),
        "families": families,
        "mask_evidence": mask_evidence,
        "render_records": records,
        "pass": all("error" not in record for record in records),
        "claim_boundary": "Controlled fixture generation; strategy selection is analyzed separately.",
    }
    (OUT / "blender_build_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
