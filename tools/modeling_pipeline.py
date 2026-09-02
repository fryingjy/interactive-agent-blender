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

from modeling_core import compile_blender_command, fit_hypothesis, validate_hypothesis


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    validate = subparsers.add_parser("validate", help="validate a shape hypothesis")
    validate.add_argument("hypothesis", type=Path)
    fit = subparsers.add_parser("fit", help="fit declared parameters to materialized masks")
    fit.add_argument("hypothesis", type=Path)
    fit.add_argument("--mask", action="append", required=True, metavar="VIEW_ID=PATH")
    fit.add_argument("--output", type=Path, required=True)
    fit.add_argument("--seed", type=int, default=0)
    fit.add_argument("--maxiter", type=int, default=30)
    compile_parser = subparsers.add_parser("compile", help="compile to a typed Blender command")
    compile_parser.add_argument("hypothesis", type=Path)
    compile_parser.add_argument("--name", default="FittedProxy")
    compile_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = _read_json(args.hypothesis)
    if args.action == "validate":
        validate_hypothesis(payload)
        print("valid")
        return 0
    if args.action == "compile":
        if payload.get("record_type") == "FITTED_SHAPE_HYPOTHESIS":
            payload = payload["hypothesis"]
        _write_json(args.output, compile_blender_command(payload, name=args.name))
        return 0
    masks = {}
    for value in args.mask:
        if "=" not in value:
            parser.error("--mask values must be VIEW_ID=PATH")
        identifier, raw_path = value.split("=", 1)
        image = cv2.imread(str(Path(raw_path)), cv2.IMREAD_GRAYSCALE)
        if image is None:
            parser.error(f"could not read mask: {raw_path}")
        masks[identifier] = image > 127
    _write_json(args.output, fit_hypothesis(payload, masks, seed=args.seed, maxiter=args.maxiter))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
