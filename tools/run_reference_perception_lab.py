"""Run a CPU-only camera-registration and segmentation-integrity validation fixture.

This is not an asset/modeling task. It uses synthetic masks with known ground truth to prove that
the evaluator can distinguish camera projection error from geometry error before new prop work.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.reference_overlay import overlay_pixels  # noqa: E402
from knowledge_engine.parameter_fitting import fit_bounded_parameters, silhouette_objective  # noqa: E402
from knowledge_engine.segmentation_audit import audit_segmentation_mask  # noqa: E402
from knowledge_engine.visual_compare import compare_masks  # noqa: E402


SIZE = 256


def fixture_mask(*, wrong_geometry: bool = False) -> np.ndarray:
    mask = np.zeros((SIZE, SIZE), dtype=np.uint8)
    cv2.rectangle(mask, (48, 58), (185, 210), 1, thickness=-1)
    cv2.rectangle(mask, (78, 90), (142, 154), 0, thickness=-1)
    if wrong_geometry:
        cv2.rectangle(mask, (78, 90), (142, 154), 1, thickness=-1)
        cv2.rectangle(mask, (185, 92), (238, 126), 1, thickness=-1)
    else:
        cv2.rectangle(mask, (185, 72), (228, 106), 1, thickness=-1)
    return mask.astype(bool)


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(mask.astype(np.uint8) * 255, "L").save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    source_frame = np.float32(((0, 0), (SIZE - 1, 0), (SIZE - 1, SIZE - 1), (0, SIZE - 1)))
    projected_frame = np.float32(((24, 15), (223, 4), (250, 239), (8, 250)))
    camera_homography = cv2.getPerspectiveTransform(source_frame, projected_frame)
    inverse_homography = cv2.getPerspectiveTransform(projected_frame, source_frame)

    canonical = fixture_mask()
    wrong = fixture_mask(wrong_geometry=True)
    reference = cv2.warpPerspective(
        canonical.astype(np.uint8), camera_homography, (SIZE, SIZE), flags=cv2.INTER_NEAREST
    ).astype(bool)
    strict_correct = compare_masks(reference, canonical)
    registered_reference = cv2.warpPerspective(
        reference.astype(np.uint8), inverse_homography, (SIZE, SIZE), flags=cv2.INTER_NEAREST
    ).astype(bool)
    registered_correct = compare_masks(registered_reference, canonical)
    registered_wrong = compare_masks(registered_reference, wrong)
    segmentation = audit_segmentation_mask(reference, expected_hole_range=(1, 1))
    wrong_segmentation = audit_segmentation_mask(wrong, expected_hole_range=(1, 1))

    def render_declared_parameters(parameters: np.ndarray) -> np.ndarray:
        body_width, hole_width = parameters
        generated = np.zeros((SIZE, SIZE), dtype=np.uint8)
        body_half = int(round(body_width * 0.5))
        hole_half = int(round(hole_width * 0.5))
        cv2.rectangle(generated, (116 - body_half, 58), (116 + body_half, 210), 1, -1)
        cv2.rectangle(generated, (110 - hole_half, 90), (110 + hole_half, 154), 0, -1)
        cv2.rectangle(generated, (185, 72), (228, 106), 1, -1)
        return generated.astype(bool)

    parameter_fit = fit_bounded_parameters(
        silhouette_objective(canonical, render_declared_parameters),
        [(90, 180), (20, 100)],
        initial=[175, 25],
        seed=19,
        maxiter=15,
        popsize=5,
    )

    save_mask(reference, args.output / "reference_projected.png")
    save_mask(canonical, args.output / "candidate_correct_unregistered.png")
    save_mask(registered_reference, args.output / "reference_registered.png")
    save_mask(wrong, args.output / "candidate_wrong_geometry.png")
    Image.fromarray(overlay_pixels(reference, canonical), "RGB").save(args.output / "overlay_unregistered.png")
    Image.fromarray(overlay_pixels(registered_reference, canonical), "RGB").save(args.output / "overlay_registered_correct.png")
    Image.fromarray(overlay_pixels(registered_reference, wrong), "RGB").save(args.output / "overlay_registered_wrong.png")

    checks = {
        "camera_mismatch_depresses_raw_iou": strict_correct["silhouette_iou"] < 0.90,
        "registration_recovers_correct_geometry": registered_correct["silhouette_iou"] > 0.97,
        "registration_does_not_hide_wrong_geometry": registered_wrong["silhouette_iou"] < registered_correct["silhouette_iou"] - 0.10,
        "reference_segmentation_integrity_passes": segmentation["pass"],
        "lost_negative_space_is_detected": not wrong_segmentation["pass"],
        "bounded_parameter_fit_improves_declared_shape": parameter_fit["retain_candidate"] and parameter_fit["improvement"] > 0.10,
    }
    report = {
        "schema_version": 1,
        "record_type": "REFERENCE_PERCEPTION_VALIDATION_LAB",
        "scope": "SYSTEM_VALIDATION_FIXTURE",
        "camera_transform": camera_homography.tolist(),
        "metrics": {
            "correct_geometry_unregistered": strict_correct,
            "correct_geometry_registered": registered_correct,
            "wrong_geometry_registered": registered_wrong,
        },
        "segmentation": {
            "reference": segmentation,
            "wrong_geometry_missing_expected_hole": wrong_segmentation,
        },
        "bounded_parameter_fit": parameter_fit,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": "This controlled fixture validates camera/shape disentanglement and mask integrity. It does not establish real-photo calibration or professional modeling readiness.",
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "checks": checks, "report": str(args.output / "report.json")}, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
