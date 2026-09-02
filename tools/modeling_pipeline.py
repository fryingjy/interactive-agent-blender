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

from modeling_core import (
    build_multiview_evidence_bundle,
    calibrate_perspective_view,
    compile_component_assembly,
    compile_blender_command,
    extract_component_evidence,
    extract_reference_evidence,
    fit_hypothesis,
    fit_component_families,
    propose_assembly_hypotheses,
    resolve_assembly_hypotheses,
    select_shape_family,
    validate_hypothesis,
)


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
    evidence = subparsers.add_parser("extract-reference", help="extract auditable mask and landmark evidence from an isolated-object image")
    evidence.add_argument("image", type=Path)
    evidence.add_argument("--output-dir", type=Path, required=True)
    evidence.add_argument("--method", choices=("auto", "alpha", "border"), default="auto")
    evidence.add_argument("--background-tolerance", type=float)
    evidence.add_argument("--mask-override", type=Path, help="edited full-size binary mask to remeasure with explicit provenance")
    components = subparsers.add_parser("annotate-components", help="bind an editable grayscale component label map to reference evidence")
    components.add_argument("evidence", type=Path)
    components.add_argument("label_map", type=Path)
    components.add_argument("--component", action="append", required=True, metavar="ID=LABEL")
    components.add_argument("--output", type=Path, required=True)
    bundle = subparsers.add_parser("bundle-references", help="bind audited, registered per-view evidence for shape solving")
    bundle.add_argument("manifest", type=Path)
    bundle.add_argument("--output", type=Path, required=True)
    propose = subparsers.add_parser("propose-assembly", help="propose generic component representations and continuity alternatives")
    propose.add_argument("bundle", type=Path)
    propose.add_argument("component_specs", type=Path)
    propose.add_argument("--output", type=Path, required=True)
    resolve_assembly = subparsers.add_parser("resolve-assembly", help="resolve assembly alternatives from independent multiview observations")
    resolve_assembly.add_argument("hypotheses", type=Path)
    resolve_assembly.add_argument("observations", type=Path)
    resolve_assembly.add_argument("--output", type=Path, required=True)
    fit_components = subparsers.add_parser("fit-components", help="fit and compete shape families independently for every bundled component")
    fit_components.add_argument("bundle", type=Path)
    fit_components.add_argument("assembly_hypotheses", type=Path)
    fit_components.add_argument("candidates", type=Path)
    fit_components.add_argument("--resolved-assembly", type=Path)
    fit_components.add_argument("--output", type=Path, required=True)
    fit_components.add_argument("--seed", type=int, default=0)
    fit_components.add_argument("--maxiter", type=int, default=20)
    compile_assembly = subparsers.add_parser("compile-assembly", help="compile selected separate components to typed Blender commands")
    compile_assembly.add_argument("selection", type=Path)
    compile_assembly.add_argument("--output", type=Path, required=True)
    compile_assembly.add_argument("--sequence-output", type=Path)
    compile_assembly.add_argument("--object-prefix", default="Blockout_")
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

    if args.action == "extract-reference":
        result = extract_reference_evidence(
            args.image,
            args.output_dir,
            method=args.method,
            background_tolerance=args.background_tolerance,
            mask_override=args.mask_override,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["accepted_for_fitting"] else 2

    if args.action == "annotate-components":
        specifications = []
        for value in args.component:
            if "=" not in value:
                parser.error("--component values must be ID=LABEL")
            identifier, raw_label = value.split("=", 1)
            try:
                label = int(raw_label)
            except ValueError:
                parser.error("component labels must be integers")
            specifications.append({"id": identifier, "label": label})
        result = extract_component_evidence(args.evidence, args.label_map, specifications)
        _write_json(args.output, result)
        return 0 if result["accepted_for_bundle"] else 2

    if args.action == "bundle-references":
        manifest = _read_json(args.manifest)
        base = args.manifest.resolve().parent
        resolve = lambda value: (base / value).resolve() if isinstance(value, str) and not Path(value).is_absolute() else value
        views = []
        for view in manifest.get("views", []):
            normalized = dict(view)
            normalized["evidence"] = resolve(normalized.get("evidence"))
            if normalized.get("components") is not None:
                normalized["components"] = resolve(normalized["components"])
            views.append(normalized)
        result = build_multiview_evidence_bundle(
            resolve(manifest.get("reference_audit")),
            resolve(manifest.get("registration_gate")),
            views,
            required_component_support=manifest.get("required_component_support"),
        )
        _write_json(args.output, result)
        return 0 if result["accepted_for_shape_solving"] else 2

    if args.action == "propose-assembly":
        specifications = _read_json(args.component_specs)
        result = propose_assembly_hypotheses(
            _read_json(args.bundle),
            specifications.get("components", []),
        )
        _write_json(args.output, result)
        return 0

    if args.action == "resolve-assembly":
        observations = _read_json(args.observations)
        result = resolve_assembly_hypotheses(
            _read_json(args.hypotheses),
            observations.get("observations", []),
        )
        _write_json(args.output, result)
        return 0 if result["ready_for_component_graph"] else 2

    if args.action == "fit-components":
        candidates = _read_json(args.candidates)
        resolved = _read_json(args.resolved_assembly) if args.resolved_assembly else None
        result = fit_component_families(
            _read_json(args.bundle),
            _read_json(args.assembly_hypotheses),
            candidates.get("components", {}),
            resolved_assembly=resolved,
            seed=args.seed,
            maxiter=args.maxiter,
        )
        _write_json(args.output, result)
        return 0 if result["ready_for_compilation"] else 2

    if args.action == "compile-assembly":
        result = compile_component_assembly(
            _read_json(args.selection),
            object_prefix=args.object_prefix,
        )
        _write_json(args.output, result)
        if args.sequence_output:
            args.sequence_output.parent.mkdir(parents=True, exist_ok=True)
            args.sequence_output.write_text(json.dumps(result["command_sequence"], indent=2) + "\n", encoding="utf-8")
        return 0

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
