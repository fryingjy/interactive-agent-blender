"""CLI for fit-before-Blender reference reconstruction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import cv2
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modeling_core import (
    build_multiview_evidence_bundle,
    build_component_refit_tickets,
    calibrate_perspective_view,
    compile_component_assembly,
    compile_blender_command,
    extract_component_evidence,
    extract_reference_evidence,
    fit_hypothesis,
    fit_component_families,
    initialize_component_candidates,
    import_component_region_proposal,
    materialize_confirmed_component_evidence,
    propose_assembly_hypotheses,
    propose_component_regions,
    propose_cross_view_correspondences,
    resolve_assembly_hypotheses,
    select_shape_family,
    validate_hypothesis,
)
from knowledge_engine import run_gemini_component_segmentation
from knowledge_engine.component_mask_observations import extract_component_mask_observations
from knowledge_engine.reference_overlay import compare_reference_render, save_mask


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
    propose_components = subparsers.add_parser("propose-components", help="create editable appearance-region labels without claiming semantic identity")
    propose_components.add_argument("evidence", type=Path)
    propose_components.add_argument("--output-dir", type=Path, required=True)
    propose_components.add_argument("--max-regions", type=int, default=6)
    propose_components.add_argument("--minimum-region-fraction", type=float, default=0.03)
    propose_components.add_argument("--seed", type=int, default=0)
    import_components = subparsers.add_parser("import-component-proposal", help="normalize external segmenter labels into the review-only proposal contract")
    import_components.add_argument("evidence", type=Path)
    import_components.add_argument("label_map", type=Path)
    import_components.add_argument("provider_report", type=Path)
    import_components.add_argument("--output-dir", type=Path, required=True)
    gemini_components = subparsers.add_parser("segment-components-gemini", help="request and audit Gemini physical-component polygons")
    gemini_components.add_argument("evidence", type=Path)
    gemini_components.add_argument("--output-dir", type=Path, required=True)
    gemini_components.add_argument("--output", type=Path, required=True)
    gemini_components.add_argument("--model", default="gemini-3.8-flash")
    gemini_components.add_argument("--request-timeout-ms", type=int, default=60_000)
    gemini_components.add_argument("--request-max-dimension", type=int, default=1536)
    gemini_components.add_argument("--response-replay", type=Path, help="re-audit a saved raw Gemini JSON response without another API call")
    propose_correspondences = subparsers.add_parser("propose-correspondences", help="match appearance-region proposals across views for review")
    propose_correspondences.add_argument("manifest", type=Path)
    propose_correspondences.add_argument("--output", type=Path, required=True)
    confirm_components = subparsers.add_parser("confirm-components", help="materialize reviewed cross-view proposal groups as semantic component evidence")
    confirm_components.add_argument("manifest", type=Path)
    confirm_components.add_argument("--output-dir", type=Path, required=True)
    confirm_components.add_argument("--output", type=Path, required=True)
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
    initialize_components = subparsers.add_parser("initialize-components", help="derive generic family candidates and bounds from registered component masks")
    initialize_components.add_argument("bundle", type=Path)
    initialize_components.add_argument("assembly_hypotheses", type=Path)
    initialize_components.add_argument("--output", type=Path, required=True)
    diagnose_fit = subparsers.add_parser("diagnose-fit", help="convert per-view fitted residuals into scoped refit tickets")
    diagnose_fit.add_argument("fitted", type=Path)
    diagnose_fit.add_argument("--component-id", required=True)
    diagnose_fit.add_argument("--mask", action="append", required=True, metavar="VIEW_ID=PATH")
    diagnose_fit.add_argument("--output", type=Path, required=True)
    compile_assembly = subparsers.add_parser("compile-assembly", help="compile resolved continuous groups and separate components to typed Blender commands")
    compile_assembly.add_argument("selection", type=Path)
    compile_assembly.add_argument("--output", type=Path, required=True)
    compile_assembly.add_argument("--sequence-output", type=Path)
    compile_assembly.add_argument("--object-prefix", default="Blockout_")
    compile_assembly.add_argument("--continuity-interfaces", type=Path, help="explicit port bindings and measured bridge bounds")
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
    compare = subparsers.add_parser("compare-reference", help="inspect a render against a reference in a declared alignment frame")
    compare.add_argument("reference", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--output-dir", type=Path, required=True)
    compare.add_argument("--alignment", choices=("strict", "uniform-bbox", "bbox", "landmarks"), default="strict")
    compare.add_argument("--landmark-pairs", type=Path)
    compare.add_argument("--reference-mask-mode", choices=("auto", "alpha", "light-background", "luminance-range"), default="auto")
    compare.add_argument("--candidate-mask-mode", choices=("auto", "alpha", "light-background", "luminance-range"), default="auto")
    compare.add_argument("--background-threshold", type=int, default=240)
    compare.add_argument("--reference-luminance-min", type=int, default=0)
    compare.add_argument("--reference-luminance-max", type=int, default=255)
    compare.add_argument("--candidate-luminance-min", type=int, default=0)
    compare.add_argument("--candidate-luminance-max", type=int, default=255)
    compare.add_argument("--reference-roi", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    compare.add_argument("--candidate-roi", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    compare.add_argument("--view", default="unknown")
    inspect_components = subparsers.add_parser("inspect-component-mask", help="measure normalized component bounds in a Blender diagnostic mask")
    inspect_components.add_argument("image", type=Path)
    inspect_components.add_argument("--components", nargs="+", required=True)
    inspect_components.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.action == "inspect-component-mask":
        report = extract_component_mask_observations(args.image, args.components)
        _write_json(args.output, report)
        print(json.dumps({"observed": sorted(report["observations"]), "missing": report["missing_component_ids"], "output": str(args.output)}, indent=2))
        return 0 if not report["missing_component_ids"] else 2

    if args.action == "compare-reference":
        landmark_pairs = None
        if args.landmark_pairs:
            payload = _read_json(args.landmark_pairs)
            landmark_pairs = payload.get("pairs", payload)
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=True)
        report, images = compare_reference_render(
            args.reference,
            args.candidate,
            alignment=args.alignment,
            reference_mask_mode=args.reference_mask_mode,
            candidate_mask_mode=args.candidate_mask_mode,
            light_background_threshold=args.background_threshold,
            reference_luminance_min=args.reference_luminance_min,
            reference_luminance_max=args.reference_luminance_max,
            candidate_luminance_min=args.candidate_luminance_min,
            candidate_luminance_max=args.candidate_luminance_max,
            reference_roi=tuple(args.reference_roi) if args.reference_roi else None,
            candidate_roi=tuple(args.candidate_roi) if args.candidate_roi else None,
            landmark_pairs=landmark_pairs,
            view=args.view,
        )
        save_mask(images["reference_mask"], output / "reference_mask.png")
        save_mask(images["candidate_mask_aligned"], output / "candidate_mask_aligned.png")
        Image.fromarray(images["overlay"], "RGB").save(output / "overlay.png")
        Image.fromarray(images["contour_error_heatmap"], "RGB").save(output / "contour_error_heatmap.png")
        _write_json(output / "comparison.json", report)
        print(json.dumps({"report": str(output / "comparison.json"), "metrics": report["metrics"], "alignment": report["alignment"]}, indent=2))
        return 0

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

    if args.action == "propose-components":
        result = propose_component_regions(
            args.evidence,
            args.output_dir,
            maximum_regions=args.max_regions,
            minimum_region_fraction=args.minimum_region_fraction,
            seed=args.seed,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.action == "import-component-proposal":
        result = import_component_region_proposal(
            args.evidence,
            args.label_map,
            args.provider_report,
            args.output_dir,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.action == "segment-components-gemini":
        result = run_gemini_component_segmentation(
            args.evidence,
            args.output_dir,
            model=args.model,
            request_timeout_ms=args.request_timeout_ms,
            request_maximum_dimension=args.request_max_dimension,
            response_replay=args.response_replay,
        )
        _write_json(args.output, result)
        return 0 if result["ready_for_external_adapter"] else 2

    if args.action == "propose-correspondences":
        manifest = _read_json(args.manifest)
        base = args.manifest.resolve().parent
        views = []
        for view in manifest.get("views", []):
            normalized = dict(view)
            proposal = normalized.get("proposal")
            if isinstance(proposal, str) and not Path(proposal).is_absolute():
                normalized["proposal"] = (base / proposal).resolve()
            views.append(normalized)
        result = propose_cross_view_correspondences(views)
        _write_json(args.output, result)
        return 0

    if args.action == "confirm-components":
        manifest = _read_json(args.manifest)
        base = args.manifest.resolve().parent
        resolve = lambda value: (base / value).resolve() if isinstance(value, str) and not Path(value).is_absolute() else value
        views = []
        for view in manifest.get("views", []):
            normalized = dict(view)
            normalized["proposal"] = resolve(normalized.get("proposal"))
            normalized["evidence"] = resolve(normalized.get("evidence"))
            views.append(normalized)
        result = materialize_confirmed_component_evidence(
            resolve(manifest.get("correspondence")),
            views,
            manifest.get("assignments", []),
            manifest.get("confirmation", {}),
            args.output_dir,
        )
        _write_json(args.output, result)
        return 0 if result["ready_for_bundle"] else 2

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
        if candidates.get("record_type") == "INITIALIZED_COMPONENT_CANDIDATE_SET" and not candidates.get("ready_for_component_fitting"):
            parser.error("initialized candidate set is underconstrained or lacks two executable families per component")
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

    if args.action == "initialize-components":
        result = initialize_component_candidates(
            _read_json(args.bundle),
            _read_json(args.assembly_hypotheses),
        )
        _write_json(args.output, result)
        return 0 if result["ready_for_component_fitting"] else 2

    if args.action == "compile-assembly":
        interface_payload = _read_json(args.continuity_interfaces) if args.continuity_interfaces else {}
        interfaces = interface_payload.get("interfaces", interface_payload)
        if not isinstance(interfaces, dict):
            parser.error("--continuity-interfaces must contain a JSON object or an interfaces object")
        result = compile_component_assembly(
            _read_json(args.selection),
            object_prefix=args.object_prefix,
            continuity_interfaces=interfaces,
        )
        _write_json(args.output, result)
        if args.sequence_output:
            args.sequence_output.parent.mkdir(parents=True, exist_ok=True)
            args.sequence_output.write_text(json.dumps(result["command_sequence"], indent=2) + "\n", encoding="utf-8")
        return 0

    if args.action == "diagnose-fit":
        tickets = build_component_refit_tickets(
            args.component_id,
            _read_json(args.fitted),
            _load_masks(args.mask, parser),
        )
        _write_json(args.output, {
            "schema_version": 1,
            "record_type": "COMPONENT_REFIT_TICKET_SET",
            "component_id": args.component_id,
            "tickets": tickets,
            "claim_boundary": "Parameter probes are diagnostic and never mutate geometry. Any suggested direction still requires a bounded all-view refit and regression check.",
        })
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
