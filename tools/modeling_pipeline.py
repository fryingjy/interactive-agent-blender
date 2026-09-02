"""CLI for fit-before-Blender reference reconstruction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modeling_core import calibrate_perspective_view, compile_blender_command, fit_hypothesis, select_shape_family, validate_hypothesis


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_masks(values: list[str], parser: argparse.ArgumentParser) -> dict:
    masks = {}
    for value in values:
        if "=" not in value:
            parser.error("--mask values must be VIEW_ID=PATH")
        identifier, raw_path = value.split("=", 1)
        image = cv2.imread(str(Path(raw_path)), cv2.IMREAD_GRAYSCALE)
        if image is None:
            parser.error(f"could not read mask: {raw_path}")
        masks[identifier] = image > 127
    return masks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    validate = subparsers.add_parser("validate", help="validate a shape hypothesis")
    validate.add_argument("hypothesis", type=Path)
    camera = subparsers.add_parser("calibrate-camera", help="solve a perspective view from 3D/2D correspondences")
    camera.add_argument("correspondences", type=Path)
    camera.add_argument("--output", type=Path, required=True)
    fit = subparsers.add_parser("fit", help="fit declared parameters to materialized masks")
    fit.add_argument("hypothesis", type=Path)
    fit.add_argument("--mask", action="append", required=True, metavar="VIEW_ID=PATH")
    fit.add_argument("--output", type=Path, required=True)
    fit.add_argument("--seed", type=int, default=0)
    fit.add_argument("--maxiter", type=int, default=30)
    fit.add_argument("--allow-incompatible", action="store_true", help="return success for a rejected family during exploratory tests")
    select = subparsers.add_parser("select-family", help="fit and compete two or more generic shape hypotheses")
    select.add_argument("candidates", type=Path, nargs="+")
    select.add_argument("--mask", action="append", required=True, metavar="VIEW_ID=PATH")
    select.add_argument("--output", type=Path, required=True)
    select.add_argument("--seed", type=int, default=0)
    select.add_argument("--maxiter", type=int, default=20)
    compile_parser = subparsers.add_parser("compile", help="compile to a typed Blender command")
    compile_parser.add_argument("hypothesis", type=Path)
    compile_parser.add_argument("--name", default="FittedProxy")
    compile_parser.add_argument("--output", type=Path, required=True)
    compile_parser.add_argument("--allow-unfitted", action="store_true", help="compile a validated raw hypothesis for controlled fixtures")
    args = parser.parse_args()

    if args.action == "calibrate-camera":
        correspondences = _read_json(args.correspondences)
        _write_json(args.output, calibrate_perspective_view(
            correspondences["object_points"],
            correspondences["image_points"],
            image_size=tuple(correspondences["image_size"]),
            vertical_fov_degrees=correspondences["vertical_fov_degrees"],
            view_id=correspondences.get("view_id", "calibrated"),
        ))
        return 0

    if args.action == "select-family":
        result = select_shape_family(
            [_read_json(path) for path in args.candidates],
            _load_masks(args.mask, parser),
            seed=args.seed,
            maxiter=args.maxiter,
        )
        _write_json(args.output, result)
        return 0 if result["pass"] else 2

    payload = _read_json(args.hypothesis)
    if args.action == "validate":
        validate_hypothesis(payload)
        print("valid")
        return 0
    if args.action == "compile":
        if payload.get("record_type") == "FITTED_SHAPE_HYPOTHESIS":
            if payload.get("family_compatible") is not True:
                parser.error("refusing to compile a fitted hypothesis that failed family compatibility")
            payload = payload["hypothesis"]
        elif not args.allow_unfitted:
            parser.error("compile requires a compatible fitted result; use --allow-unfitted only for controlled fixtures")
        _write_json(args.output, compile_blender_command(payload, name=args.name))
        return 0
    masks = _load_masks(args.mask, parser)
    result = fit_hypothesis(payload, masks, seed=args.seed, maxiter=args.maxiter)
    _write_json(args.output, result)
    return 0 if result["family_compatible"] or args.allow_incompatible else 2


if __name__ == "__main__":
    raise SystemExit(main())
