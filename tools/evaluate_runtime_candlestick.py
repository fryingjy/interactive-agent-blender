"""Normalize and score the runtime candlestick against its frozen reference proxy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.visual_compare import compare_masks  # noqa: E402


def bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError("empty mask")
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def load_reference(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L")) > 0


def load_candidate(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))[..., 3] > 0


def align(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    rx0, ry0, rx1, ry1 = bbox(reference)
    cx0, cy0, cx1, cy1 = bbox(candidate)
    crop = Image.fromarray((candidate[cy0 : cy1 + 1, cx0 : cx1 + 1] * 255).astype(np.uint8), "L")
    resized = np.asarray(crop.resize((rx1 - rx0 + 1, ry1 - ry0 + 1), Image.Resampling.NEAREST)) > 0
    result = np.zeros_like(reference)
    result[ry0 : ry1 + 1, rx0 : rx1 + 1] = resized
    return result


def row_width_profile(mask: np.ndarray, samples: int = 241) -> np.ndarray:
    x0, y0, x1, y1 = bbox(mask)
    height = y1 - y0
    width = max(1, x1 - x0)
    rows = np.linspace(y0, y1, samples).round().astype(int)
    values = []
    for row in rows:
        xs = np.where(mask[row] > 0)[0]
        values.append((xs.max() - xs.min()) / width if len(xs) else 0.0)
    return np.asarray(values, dtype=float)


def save_overlay(reference: np.ndarray, candidate: np.ndarray, path: Path) -> None:
    overlay = np.full((*reference.shape, 3), 18, dtype=np.uint8)
    overlay[reference & ~candidate] = (235, 70, 70)
    overlay[candidate & ~reference] = (55, 210, 235)
    overlay[reference & candidate] = (240, 240, 240)
    Image.fromarray(overlay, "RGB").save(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    contract = json.loads((run / "experiment_contract.json").read_text(encoding="utf-8"))
    blender_report = json.loads((run / "blender_runtime_report.json").read_text(encoding="utf-8"))
    planner = json.loads((run / "retrieval_and_planner.json").read_text(encoding="utf-8"))
    reference = load_reference(run / "reference_silhouette.png")
    control = align(reference, load_candidate(run / "unshaped_cylinder_mask.png"))
    candidate = align(reference, load_candidate(run / "final_candidate_mask.png"))
    control_metrics = compare_masks(reference, control)
    candidate_metrics = compare_masks(reference, candidate)
    ref_profile = row_width_profile(reference)
    control_profile = row_width_profile(control)
    candidate_profile = row_width_profile(candidate)
    control_rmse = float(np.sqrt(np.mean((control_profile - ref_profile) ** 2)))
    candidate_rmse = float(np.sqrt(np.mean((candidate_profile - ref_profile) ** 2)))
    rmse_reduction = 100.0 * (control_rmse - candidate_rmse) / control_rmse
    iou_gain = candidate_metrics["silhouette_iou"] - control_metrics["silhouette_iou"]
    expected = contract["frozen_acceptance_gates"]["base_mesh"]
    audit = blender_report["base_cage_audit"]
    checks = {
        "retrieval_and_planner": planner["pass"] is True,
        "one_object": len(blender_report["scene_mesh_objects"]) == expected["objects"],
        "connected_components": audit["connected_components"] == expected["connected_components"],
        "vertices": audit["vertices"] == expected["vertices"],
        "faces": audit["faces"] == expected["faces"],
        "quads": audit["quads"] == expected["quads"],
        "non_quad_faces": audit["non_quad_faces"] == expected["non_quad_faces"],
        "intentional_boundary_edges": audit["boundary_edges"] == expected["intentional_boundary_edges"],
        "loose_vertices": audit["loose_vertices"] == expected["loose_vertices"],
        "degenerate_faces": audit["degenerate_faces"] == expected["degenerate_faces"],
        "final_profile_rmse": candidate_rmse <= contract["frozen_acceptance_gates"]["profile"]["final_normalized_width_rmse_max"],
        "profile_rmse_reduction": rmse_reduction >= contract["frozen_acceptance_gates"]["profile"]["rmse_reduction_vs_unshaped_cylinder_min_percent"],
        "final_silhouette_iou": candidate_metrics["silhouette_iou"] >= contract["frozen_acceptance_gates"]["silhouette"]["final_iou_min"],
        "silhouette_iou_gain": iou_gain >= contract["frozen_acceptance_gates"]["silhouette"]["iou_gain_vs_unshaped_cylinder_min"],
    }
    report = {
        "method": "foreground-bbox normalization removes scale/translation, then compares masks and 241-sample normalized row-width profiles",
        "control": {"metrics": control_metrics, "profile_rmse": control_rmse},
        "candidate": {"metrics": candidate_metrics, "profile_rmse": candidate_rmse},
        "improvement": {"profile_rmse_reduction_percent": rmse_reduction, "silhouette_iou_gain": iou_gain},
        "checks": checks,
        "pass_before_independent_verifier": all(checks.values()),
    }
    save_overlay(reference, control, run / "control_overlay.png")
    save_overlay(reference, candidate, run / "candidate_overlay.png")
    (run / "runtime_evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass_before_independent_verifier"] else 2
if __name__ == "__main__":
    raise SystemExit(main())
