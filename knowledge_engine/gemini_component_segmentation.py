"""Hash-bound Gemini component polygons for the reviewed segmentation-proposal path."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt


DEFAULT_MODEL = "gemini-3.8-flash"
PROMPT_VERSION = "blender-component-segmentation-v3-box-local"


def _read(value: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare_request_image(source: Path, destination: Path, maximum_dimension: int) -> tuple[bytes, dict[str, Any]]:
    """Materialize a bounded 8-bit provider image without changing normalized coordinates."""
    if not 512 <= maximum_dimension <= 4096:
        raise ValueError("Gemini request maximum dimension must be in [512, 4096]")
    image = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Gemini segmentation source image cannot be decoded for upload")
    source_dtype = str(image.dtype)
    if image.dtype == np.uint16:
        image = ((image.astype(np.uint32) + 128) // 257).astype(np.uint8)
    elif image.dtype != np.uint8:
        raise ValueError(f"Gemini request image dtype {image.dtype} is unsupported")
    height, width = image.shape[:2]
    scale = min(1.0, maximum_dimension / max(width, height))
    if scale < 1.0:
        image = cv2.resize(
            image,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    success, encoded = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Gemini request image could not be encoded")
    payload = encoded.tobytes()
    destination.write_bytes(payload)
    return payload, {
        "source_image_size": [width, height],
        "request_image_size": [int(image.shape[1]), int(image.shape[0])],
        "source_dtype": source_dtype,
        "request_dtype": "uint8",
        "scale": scale,
        "coordinate_transform": "ASPECT_PRESERVING_NORMALIZED_COORDINATES",
        "request_image_path": str(destination),
        "request_image_sha256": hashlib.sha256(payload).hexdigest(),
    }


def component_segmentation_schema() -> dict[str, Any]:
    point = {
        "type": "array",
        "items": {"type": "integer", "minimum": 0, "maximum": 1000},
        "minItems": 2,
        "maxItems": 2,
    }
    return {
        "type": "object",
        "properties": {
            "components": {
                "type": "array",
                "minItems": 1,
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "role": {
                            "type": "string",
                            "enum": ["PRIMARY_VOLUME", "ATTACHED_ASSEMBLY", "FASTENER", "INSERT", "OTHER"],
                        },
                        "box_2d": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 0, "maximum": 1000},
                            "minItems": 4,
                            "maxItems": 4,
                            "description": "Full-image [ymin, xmin, ymax, xmax], normalized 0-1000.",
                        },
                        "mask_polygon": {
                            "type": "array",
                            "items": point,
                            "minItems": 3,
                            "description": "[x, y] points normalized 0-1000 inside this component's box_2d.",
                        },
                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "evidence": {"type": "string"},
                    },
                    "required": ["label", "role", "box_2d", "mask_polygon", "confidence", "evidence"],
                },
            },
            "limitations": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["components", "limitations"],
    }


def _validate_analysis(analysis: dict[str, Any]) -> None:
    if not isinstance(analysis, dict) or not isinstance(analysis.get("components"), list) or not analysis["components"]:
        raise ValueError("Gemini segmentation requires a non-empty components list")
    if not isinstance(analysis.get("limitations"), list):
        raise ValueError("Gemini segmentation limitations must be a list")
    labels = []
    for component in analysis["components"]:
        label = str(component.get("label") or "").strip()
        labels.append(label)
        if not label or not str(component.get("evidence") or "").strip():
            raise ValueError("Gemini components require labels and visible evidence")
        if component.get("role") not in {"PRIMARY_VOLUME", "ATTACHED_ASSEMBLY", "FASTENER", "INSERT", "OTHER"}:
            raise ValueError("Gemini component has an invalid role")
        confidence = component.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("Gemini component confidence must be in [0, 1]")
        box = component.get("box_2d")
        if not isinstance(box, list) or len(box) != 4 or any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1000 for value in box):
            raise ValueError("Gemini component box_2d must contain four normalized integers")
        if box[0] >= box[2] or box[1] >= box[3]:
            raise ValueError("Gemini component box_2d is degenerate")
        polygon = component.get("mask_polygon")
        if not isinstance(polygon, list) or len(polygon) < 3:
            raise ValueError("Gemini component mask_polygon needs at least three points")
        if any(not isinstance(point, list) or len(point) != 2 or any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1000 for value in point) for point in polygon):
            raise ValueError("Gemini mask polygon points must be normalized integer coordinate pairs")
    if len(labels) != len(set(label.lower() for label in labels)):
        raise ValueError("Gemini component labels must be unique")


def _box_local_polygon_xy(
    component: dict[str, Any], foreground: np.ndarray
) -> tuple[list[list[float]], str, dict[str, Any]]:
    """Map Gemini's documented box-local ``[x, y]`` polygon to the full image."""
    y0, x0, y1, x1 = component["box_2d"]
    points = component["mask_polygon"]
    full_image_points = [
        [x0 + point[0] / 1000.0 * (x1 - x0), y0 + point[1] / 1000.0 * (y1 - y0)]
        for point in points
    ]
    height, width = foreground.shape
    pixels = np.asarray([
        [round(point[0] / 1000.0 * (width - 1)), round(point[1] / 1000.0 * (height - 1))]
        for point in full_image_points
    ], dtype=np.int32)
    mask = np.zeros(foreground.shape, dtype=np.uint8)
    cv2.fillPoly(mask, [pixels], 1)
    proposed = mask.astype(bool)
    verified_precision = float(np.logical_and(proposed, foreground).sum() / max(1, proposed.sum()))
    diagnostics = {
        "box_2d_ymin_xmin_ymax_xmax": list(component["box_2d"]),
        "box_local_polygon_x_range": [min(point[0] for point in points), max(point[0] for point in points)],
        "box_local_polygon_y_range": [min(point[1] for point in points), max(point[1] for point in points)],
        "verified_object_precision": verified_precision,
    }
    return full_image_points, "XY_BOX_LOCAL_TO_FULL_IMAGE", diagnostics


def run_gemini_component_segmentation(
    reference_evidence: dict[str, Any] | str | Path,
    output_directory: str | Path,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    generate: Callable[..., Any] | None = None,
    minimum_raw_coverage: float = 0.92,
    maximum_raw_overlap: float = 0.08,
    minimum_watershed_seed_coverage: float = 0.55,
    request_timeout_ms: int = 60_000,
    request_maximum_dimension: int = 1536,
    response_replay: str | Path | None = None,
) -> dict[str, Any]:
    """Request physical-part polygons, audit them, and emit an external-adapter payload."""
    evidence = _read(reference_evidence)
    segmentation_ready = evidence.get(
        "accepted_for_component_segmentation", evidence.get("accepted_for_fitting")
    )
    if evidence.get("record_type") != "REFERENCE_IMAGE_EVIDENCE" or not segmentation_ready:
        raise ValueError("Gemini component segmentation requires reference evidence accepted for component segmentation")
    source = Path(evidence.get("source", {}).get("path", ""))
    source_hash = evidence.get("source", {}).get("sha256")
    mask_path = Path(evidence.get("artifacts", {}).get("editable_mask", ""))
    mask_hash = evidence.get("artifact_sha256", {}).get("editable_mask")
    if not source.is_file() or _sha256(source) != source_hash:
        raise ValueError("Gemini segmentation source image is stale or missing")
    if not mask_path.is_file() or _sha256(mask_path) != mask_hash:
        raise ValueError("Gemini segmentation object mask is stale or missing")
    mime = mimetypes.guess_type(source.name)[0]
    if mime not in {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"}:
        raise ValueError("Gemini segmentation source has an unsupported image type")
    if not 5_000 <= request_timeout_ms <= 300_000:
        raise ValueError("Gemini request timeout must be in [5000, 300000] milliseconds")
    if not 0.50 <= minimum_watershed_seed_coverage <= minimum_raw_coverage:
        raise ValueError("minimum watershed seed coverage must be between 0.50 and the raw-coverage threshold")
    destination = Path(output_directory).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    request_path = destination / "gemini_request_image.png"
    request_bytes, request_image = _prepare_request_image(
        source, request_path, request_maximum_dimension
    )
    if response_replay is not None and generate is not None:
        raise ValueError("response replay and live/mock generation are mutually exclusive")
    key = api_key or os.environ.get("GEMINI_API_KEY")
    from google import genai
    from google.genai import types

    replay_path = Path(response_replay).resolve() if response_replay is not None else None
    if replay_path is not None:
        if not replay_path.is_file():
            raise ValueError("Gemini response replay file is missing")
        response_text = replay_path.read_text(encoding="utf-8")
        acquisition = {
            "mode": "HASH_BOUND_RESPONSE_REPLAY",
            "replay_source_path": str(replay_path),
            "replay_source_sha256": _sha256(replay_path),
        }
    else:
        if generate is None:
            if not key:
                raise RuntimeError("GEMINI_API_KEY is not configured")
            client = genai.Client(
                api_key=key,
                http_options=types.HttpOptions(
                    timeout=request_timeout_ms,
                    retry_options=types.HttpRetryOptions(
                        attempts=2,
                        initial_delay=1.0,
                        max_delay=4.0,
                        exp_base=2.0,
                        jitter=0.25,
                        http_status_codes=[408, 429, 500, 502, 503, 504],
                    ),
                ),
            )
            generate = client.models.generate_content
        acquisition = {"mode": "LIVE_OR_INJECTED_GENERATION"}
    prompt = """
Segment the visible manufactured object into its main physically meaningful modeling components.
Use one component for each continuous manufactured shell or substantial visibly attached assembly.
Do not emit screws, bolts, rivets, pins, or other small repeated hardware as component masks; those
are detail landmarks handled separately. Do not segment highlights, shadows, printed texture,
bevels, holes, or color patches as parts. If the object is cropped, cover only visible object pixels
and never infer an unseen continuation. Cover the complete visible object silhouette exactly once. Follow
Gemini's standard segmentation coordinate contract exactly: box_2d is [ymin, xmin, ymax, xmax]
normalized over the full image, while every mask_polygon point is [x, y] normalized from 0 to 1000
inside that component's box. Do not return full-image mask-polygon coordinates.
Keep visible component masks mutually exclusive: an attached cover owns the pixels it visibly
occludes, while the hidden host surface must not also claim those pixels.
For each component, state concrete visible seam/form evidence and calibrated uncertainty.
""".strip()
    if replay_path is None:
        response = generate(
            model=model,
            contents=[types.Part.from_bytes(data=request_bytes, mime_type="image/png"), prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=component_segmentation_schema(),
                # The current GenerateContent endpoint rejects MINIMAL for Gemini 3.8 Flash,
                # despite the Interactions segmentation example recommending it. LOW is the
                # lowest operational level on this SDK path (verified 2026-09-04).
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                temperature=0.0,
            ),
        )
        response_text = response.text
    try:
        analysis = json.loads(response_text)
    except (AttributeError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Gemini component segmentation returned unreadable JSON") from exc
    _validate_analysis(analysis)
    response_path = destination / "gemini_component_response.json"
    response_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    object_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if object_mask is None:
        raise ValueError("Gemini segmentation object mask cannot be decoded")
    foreground = object_mask >= 128
    height, width = foreground.shape
    component_masks = []
    coordinate_conventions = []
    coordinate_diagnostics = []
    for component in analysis["components"]:
        polygon_xy, convention, diagnostics = _box_local_polygon_xy(component, foreground)
        coordinate_conventions.append(convention)
        coordinate_diagnostics.append(diagnostics)
        points = np.asarray([
            [round(point[0] / 1000.0 * (width - 1)), round(point[1] / 1000.0 * (height - 1))]
            for point in polygon_xy
        ], dtype=np.int32)
        mask = np.zeros_like(object_mask)
        cv2.fillPoly(mask, [points], 1)
        component_masks.append(mask.astype(bool) & foreground)
    raw_component_masks = component_masks
    raw_stack = np.stack(raw_component_masks)
    union = np.any(raw_stack, axis=0)
    raw_coverage = float(np.logical_and(union, foreground).sum() / foreground.sum())
    raw_overlap = float(np.logical_and(raw_stack.sum(axis=0) > 1, foreground).sum() / foreground.sum())

    # Gemini commonly describes a continuous host through an attached cover. That is useful
    # construction evidence, but the visible label map must still be mutually exclusive. Resolve
    # only the explicit, physically meaningful PRIMARY_VOLUME -> ATTACHED_ASSEMBLY/INSERT
    # occlusion relationship. All other overlaps remain visible and fail the gate.
    component_masks = [mask.copy() for mask in raw_component_masks]
    occluder_roles = {"ATTACHED_ASSEMBLY", "INSERT"}
    for host_index, component in enumerate(analysis["components"]):
        if component["role"] != "PRIMARY_VOLUME":
            continue
        visible_occluders = np.zeros_like(foreground)
        for other_index, other in enumerate(analysis["components"]):
            if other_index != host_index and other["role"] in occluder_roles:
                visible_occluders |= raw_component_masks[other_index]
        component_masks[host_index] &= ~visible_occluders
    stack = np.stack(component_masks)
    visible_overlap = float(
        np.logical_and(stack.sum(axis=0) > 1, foreground).sum() / foreground.sum()
    )
    role_occlusion_resolved_fraction = max(0.0, raw_overlap - visible_overlap)
    confidence_order = sorted(range(len(component_masks)), key=lambda index: float(analysis["components"][index]["confidence"]))
    labels = np.zeros_like(object_mask)
    for index in confidence_order:
        labels[component_masks[index]] = index + 1
    bounded_fill_applied = False
    watershed_refinement_applied = False
    boundary_edge_support_ratio = 0.0
    boundary_edge_mean = 0.0
    interior_edge_mean = 0.0
    boundary_edge_supported_fraction = 0.0
    ready = raw_coverage >= minimum_raw_coverage and visible_overlap <= maximum_raw_overlap and np.all(labels[foreground] > 0)
    if raw_coverage >= minimum_raw_coverage and visible_overlap <= maximum_raw_overlap and np.any(foreground & (labels == 0)):
        _distance, nearest = distance_transform_edt(labels == 0, return_indices=True)
        missing = foreground & (labels == 0)
        labels[missing] = labels[tuple(axis[missing] for axis in nearest)]
        bounded_fill_applied = True
        ready = bool(np.all(labels[foreground] > 0))
    elif not ready and raw_coverage >= minimum_watershed_seed_coverage and visible_overlap <= 0.25:
        overlap_count = stack.sum(axis=0)
        markers = np.zeros(foreground.shape, dtype=np.int32)
        markers[~foreground] = len(component_masks) + 1
        kernel_size = max(3, int(round(min(width, height) * 0.008)) | 1)
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        seeds_valid = True
        for index, mask in enumerate(component_masks):
            exclusive = (mask & (overlap_count == 1)).astype(np.uint8)
            seed = cv2.erode(exclusive, kernel, iterations=1).astype(bool)
            if int(seed.sum()) < max(8, int(foreground.sum() * 0.0002)):
                seeds_valid = False
                break
            markers[seed] = index + 1
        if seeds_valid:
            image_for_watershed = cv2.imread(str(source), cv2.IMREAD_COLOR)
            cv2.watershed(image_for_watershed, markers)
            refined = np.where(
                foreground & (markers >= 1) & (markers <= len(component_masks)),
                markers,
                0,
            ).astype(np.uint8)
            missing = foreground & (refined == 0)
            if np.any(missing):
                _distance, nearest = distance_transform_edt(refined == 0, return_indices=True)
                refined[missing] = refined[tuple(axis[missing] for axis in nearest)]
            labels = refined
            watershed_refinement_applied = True
            gray = cv2.cvtColor(image_for_watershed, cv2.COLOR_BGR2GRAY).astype(float)
            gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient = np.hypot(gradient_x, gradient_y)
            internal_boundary = np.zeros_like(foreground)
            internal_boundary[1:, :] |= foreground[1:, :] & foreground[:-1, :] & (labels[1:, :] != labels[:-1, :])
            internal_boundary[:, 1:] |= foreground[:, 1:] & foreground[:, :-1] & (labels[:, 1:] != labels[:, :-1])
            interior = cv2.erode(foreground.astype(np.uint8), np.ones((3, 3), dtype=np.uint8), iterations=1).astype(bool)
            if internal_boundary.any() and interior.any():
                boundary_edge_mean = float(gradient[internal_boundary].mean())
                interior_edge_mean = float(gradient[interior].mean())
                boundary_edge_support_ratio = boundary_edge_mean / max(interior_edge_mean, 1e-8)
                boundary_edge_supported_fraction = float(
                    np.mean(gradient[internal_boundary] >= 10.0)
                )
            ready = bool(
                np.all(labels[foreground] > 0)
                and boundary_edge_support_ratio >= 0.7
                and boundary_edge_mean >= 5.0
                and interior_edge_mean >= 1.0
            )
    retained = [int((labels == index + 1).sum()) for index in range(len(component_masks))]
    if any(count == 0 for count in retained):
        ready = False

    label_path = destination / "gemini_component_labels.png"
    preview_path = destination / "gemini_component_preview.png"
    provider_path = destination / "gemini_provider_report.json"
    cv2.imwrite(str(label_path), labels)
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    preview = image.copy()
    boundaries = np.zeros_like(foreground)
    boundaries[1:, :] |= labels[1:, :] != labels[:-1, :]
    boundaries[:, 1:] |= labels[:, 1:] != labels[:, :-1]
    preview[boundaries & foreground] = (0, 255, 255)
    cv2.imwrite(str(preview_path), preview)
    raw_quality_factor = float(np.clip(raw_coverage - visible_overlap, 0.0, 1.0))
    refinement_quality = 0.0
    if watershed_refinement_applied and ready:
        refinement_quality = float(
            min(boundary_edge_support_ratio / 2.0, 1.0)
            * min(boundary_edge_mean / 25.0, 1.0)
            * boundary_edge_supported_fraction
        )
    # A successful deterministic partition can recover some—but never all—of
    # the confidence lost to sparse model polygons. Failed refinement earns no
    # credit and remains non-importable below.
    quality_factor = float(
        raw_quality_factor
        + (1.0 - raw_quality_factor) * 0.5 * refinement_quality
    )
    provider_report = {
        "provider": "Google Gemini",
        "model_id": model,
        "model_version": PROMPT_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "source_sha256": source_hash,
        "request_image": request_image,
        "response_acquisition": acquisition,
        "response_sha256": _sha256(response_path),
        "region_confidence": {
            str(index + 1): float(component["confidence"]) * quality_factor
            for index, component in enumerate(analysis["components"])
        },
        "region_semantic_proposals": {
            str(index + 1): {
                "label": component["label"],
                "role": component["role"],
                "evidence": component["evidence"],
            }
            for index, component in enumerate(analysis["components"])
        },
        "region_occlusion_expected": {
            str(index + 1): bool(
                component["role"] == "PRIMARY_VOLUME"
                and any(
                    other_index != index
                    and analysis["components"][other_index]["role"] in {"ATTACHED_ASSEMBLY", "INSERT"}
                    and np.logical_and(raw_component_masks[index], raw_component_masks[other_index]).any()
                    for other_index in range(len(component_masks))
                )
            )
            for index, component in enumerate(analysis["components"])
        },
        "raw_coverage": raw_coverage,
        "raw_overlap": raw_overlap,
        "visible_overlap_after_role_resolution": visible_overlap,
        "role_occlusion_resolved_fraction": role_occlusion_resolved_fraction,
        "bounded_nearest_fill_applied": bounded_fill_applied,
        "watershed_refinement_applied": watershed_refinement_applied,
        "boundary_edge_support_ratio": boundary_edge_support_ratio,
        "boundary_edge_mean": boundary_edge_mean,
        "interior_edge_mean": interior_edge_mean,
        "boundary_edge_supported_fraction": boundary_edge_supported_fraction,
        "minimum_watershed_seed_coverage": minimum_watershed_seed_coverage,
        "raw_quality_factor": raw_quality_factor,
        "refinement_quality_credit": refinement_quality,
        "final_quality_factor": quality_factor,
        "segmentation_gate_pass": bool(ready),
        "model_limitations": analysis["limitations"],
        "claim_boundary": "Confidence is model-reported and penalized by deterministic mask coverage/overlap. It is not calibrated semantic truth.",
    }
    provider_path.write_text(json.dumps(provider_report, indent=2) + "\n", encoding="utf-8")
    issues = []
    warnings = []
    if raw_coverage < minimum_raw_coverage and not watershed_refinement_applied:
        issues.append(f"Gemini polygons cover only {raw_coverage:.4f} of the verified object mask")
    elif raw_coverage < minimum_raw_coverage:
        warnings.append(f"raw Gemini polygons covered only {raw_coverage:.4f}; watershed refinement was required")
    if role_occlusion_resolved_fraction > 0:
        warnings.append(
            "resolved declared attached-assembly/insert occlusion over "
            f"{role_occlusion_resolved_fraction:.4f} of the verified object mask"
        )
    if visible_overlap > maximum_raw_overlap and not watershed_refinement_applied:
        issues.append(
            "Gemini visible polygons overlap after role-aware occlusion resolution on "
            f"{visible_overlap:.4f} of the verified object mask"
        )
    elif visible_overlap > maximum_raw_overlap:
        warnings.append(
            "Gemini visible polygons overlapped after role-aware occlusion resolution on "
            f"{visible_overlap:.4f}; watershed refinement was required"
        )
    if any(count == 0 for count in retained):
        issues.append("at least one Gemini component has no retained verified-mask pixels")
    if watershed_refinement_applied and (
        boundary_edge_support_ratio < 0.7
        or boundary_edge_mean < 5.0
        or interior_edge_mean < 1.0
    ):
        issues.append(
            "refined internal boundaries have weak image-edge support "
            f"(ratio={boundary_edge_support_ratio:.4f}, mean={boundary_edge_mean:.4f}, "
            f"supported_fraction={boundary_edge_supported_fraction:.4f})"
        )
    return {
        "schema_version": 1,
        "record_type": "GEMINI_COMPONENT_SEGMENTATION",
        "source_sha256": source_hash,
        "source_mask_sha256": mask_hash,
        "request_image": request_image,
        "response_acquisition": acquisition,
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "components": analysis["components"],
        "polygon_coordinate_conventions": coordinate_conventions,
        "polygon_coordinate_diagnostics": coordinate_diagnostics,
        "raw_coverage": raw_coverage,
        "raw_overlap": raw_overlap,
        "visible_overlap_after_role_resolution": visible_overlap,
        "role_occlusion_resolved_fraction": role_occlusion_resolved_fraction,
        "bounded_nearest_fill_applied": bounded_fill_applied,
        "watershed_refinement_applied": watershed_refinement_applied,
        "boundary_edge_support_ratio": boundary_edge_support_ratio,
        "boundary_edge_mean": boundary_edge_mean,
        "interior_edge_mean": interior_edge_mean,
        "boundary_edge_supported_fraction": boundary_edge_supported_fraction,
        "retained_pixel_counts": retained,
        "artifacts": {
            "label_map": str(label_path),
            "preview": str(preview_path),
            "request_image": str(request_path),
            "response": str(response_path),
            "provider_report": str(provider_path),
        },
        "artifact_sha256": {
            "label_map": _sha256(label_path),
            "preview": _sha256(preview_path),
            "request_image": _sha256(request_path),
            "response": _sha256(response_path),
            "provider_report": _sha256(provider_path),
        },
        "ready_for_external_adapter": ready and not issues,
        "issues": issues,
        "warnings": warnings,
        "claim_boundary": "Gemini polygons are a reviewed segmentation proposal. They cannot authorize semantic identity, continuity, hidden geometry, or Blender construction.",
    }
