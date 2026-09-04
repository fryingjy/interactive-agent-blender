"""Propose editable appearance regions and cross-view matches without claiming semantics."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

from .component_evidence import extract_component_evidence
from .reference_evidence import analyze_reference_mask


def _read(value: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _current_file(record: dict[str, Any], *, label: str) -> Path:
    path = Path(record.get("path", ""))
    expected = record.get("sha256")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"{label} is stale or missing")
    return path


def _kmeans(features: np.ndarray, count: int, *, seed: int) -> tuple[np.ndarray, np.ndarray, float]:
    """Small deterministic k-means used to avoid a heavyweight perception dependency."""
    if count < 1 or count > len(features):
        raise ValueError("cluster count must fit the available pixels")
    generator = np.random.default_rng(seed)
    centers = [features[int(generator.integers(len(features)))]]
    for _index in range(1, count):
        distances = np.min(np.sum((features[:, None] - np.asarray(centers)[None, :]) ** 2, axis=2), axis=1)
        total = float(distances.sum())
        if total <= 1e-12:
            centers.append(features[len(centers) % len(features)])
        else:
            centers.append(features[int(generator.choice(len(features), p=distances / total))])
    centers_array = np.asarray(centers, dtype=float)
    labels = np.zeros(len(features), dtype=np.int32)
    for _iteration in range(60):
        distances = np.sum((features[:, None] - centers_array[None, :]) ** 2, axis=2)
        updated_labels = np.argmin(distances, axis=1).astype(np.int32)
        updated_centers = centers_array.copy()
        for index in range(count):
            members = features[updated_labels == index]
            if len(members):
                updated_centers[index] = members.mean(axis=0)
            else:
                farthest = int(np.argmax(np.min(distances, axis=1)))
                updated_centers[index] = features[farthest]
        if np.array_equal(updated_labels, labels) and np.allclose(updated_centers, centers_array):
            labels, centers_array = updated_labels, updated_centers
            break
        labels, centers_array = updated_labels, updated_centers
    residual = features - centers_array[labels]
    return labels, centers_array, float(np.sum(residual * residual))


def _select_color_clusters(
    colors: np.ndarray,
    *,
    maximum_regions: int,
    minimum_region_fraction: float,
    seed: int,
) -> tuple[int, dict[str, Any]]:
    sample = colors
    if len(sample) > 20_000:
        sample = sample[np.linspace(0, len(sample) - 1, 20_000).round().astype(int)]
    _labels, _centers, base_sse = _kmeans(sample, 1, seed=seed)
    variance_per_pixel = base_sse / max(1, len(sample))
    diagnostics = {"1": {"sse": base_sse, "score": 0.0, "accepted": True}}
    if variance_per_pixel < 9.0:
        return 1, diagnostics
    best_count, best_score = 1, 0.0
    for count in range(2, min(maximum_regions, len(sample)) + 1):
        labels, centers, sse = _kmeans(sample, count, seed=seed + count)
        fractions = np.bincount(labels, minlength=count) / len(sample)
        separations = np.linalg.norm(centers[:, None] - centers[None, :], axis=2)
        minimum_separation = float(np.min(separations[np.triu_indices(count, 1)]))
        explained = 1.0 - sse / max(base_sse, 1e-12)
        score = explained - 0.11 * (count - 1)
        accepted = bool(float(fractions.min()) >= minimum_region_fraction and minimum_separation >= 10.0)
        diagnostics[str(count)] = {
            "sse": sse,
            "explained_color_variance": explained,
            "minimum_region_fraction": float(fractions.min()),
            "minimum_center_distance_lab": minimum_separation,
            "score": score,
            "accepted": accepted,
        }
        if accepted and score > best_score + 0.04:
            best_count, best_score = count, score
    return best_count, diagnostics


def propose_component_regions(
    reference_evidence: dict[str, Any] | str | Path,
    output_directory: str | Path,
    *,
    maximum_regions: int = 6,
    minimum_region_fraction: float = 0.03,
    seed: int = 0,
) -> dict[str, Any]:
    """Create an editable appearance-region label proposal for one accepted object mask."""
    if not 1 <= maximum_regions <= 12:
        raise ValueError("maximum_regions must be from 1 through 12")
    if not 0.005 <= minimum_region_fraction <= 0.25:
        raise ValueError("minimum_region_fraction must be in [0.005, 0.25]")
    evidence = _read(reference_evidence)
    segmentation_ready = evidence.get(
        "accepted_for_component_segmentation", evidence.get("accepted_for_fitting")
    )
    if evidence.get("record_type") != "REFERENCE_IMAGE_EVIDENCE" or not segmentation_ready:
        raise ValueError("component proposals require REFERENCE_IMAGE_EVIDENCE accepted for component segmentation")
    source_path = _current_file(evidence.get("source", {}), label="source image")
    mask_path = _current_file(
        {
            "path": evidence.get("artifacts", {}).get("editable_mask"),
            "sha256": evidence.get("artifact_sha256", {}).get("editable_mask"),
        },
        label="editable source mask",
    )
    image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    source_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if image is None or source_mask is None or image.shape[:2] != source_mask.shape:
        raise ValueError("source image and editable mask must be decodable at matching dimensions")
    foreground = source_mask >= 128
    lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(float)
    colors = lab_image[foreground]
    count, model_selection = _select_color_clusters(
        colors,
        maximum_regions=maximum_regions,
        minimum_region_fraction=minimum_region_fraction,
        seed=seed,
    )
    labels, centers, _sse = _kmeans(colors, count, seed=seed + 101)
    order = sorted(range(count), key=lambda index: tuple(float(value) for value in centers[index]))
    remap = np.zeros(count, dtype=np.uint8)
    for new_label, old_index in enumerate(order, 1):
        remap[old_index] = new_label
    label_map = np.zeros(foreground.shape, dtype=np.uint8)
    label_map[foreground] = remap[labels]

    regions = []
    for label in range(1, count + 1):
        region_mask = label_map == label
        region_colors = lab_image[region_mask]
        connected_count, _connected = cv2.connectedComponents(region_mask.astype(np.uint8), connectivity=8)
        measurement = analyze_reference_mask(region_mask)
        distances = np.linalg.norm(region_colors - region_colors.mean(axis=0), axis=1)
        regions.append({
            "proposal_region_id": f"appearance-region-{label:03d}",
            "label": label,
            "visible_area_fraction_of_object": float(region_mask.sum() / foreground.sum()),
            "mean_lab": region_colors.mean(axis=0).tolist(),
            "color_dispersion_lab": float(np.mean(distances)),
            "connected_fragment_count": connected_count - 1,
            "measurements": measurement,
        })

    if count == 1:
        confidence = 1.0
        maximum_fragmentation = max(int(region["connected_fragment_count"]) for region in regions)
    else:
        region_centers = np.asarray([region["mean_lab"] for region in regions])
        pairwise = np.linalg.norm(region_centers[:, None] - region_centers[None, :], axis=2)
        separation = float(np.min(pairwise[np.triu_indices(count, 1)]))
        dispersion = max(float(region["color_dispersion_lab"]) for region in regions)
        fragmentation = max(int(region["connected_fragment_count"]) for region in regions)
        confidence = float(np.clip((separation - dispersion) / 45.0, 0.0, 1.0) * (1.0 / max(1, fragmentation)))
        maximum_fragmentation = fragmentation
    quality_issues = []
    if count > 1 and confidence < 0.6:
        quality_issues.append(f"appearance-region confidence is only {confidence:.4f}")
    if maximum_fragmentation > 4:
        quality_issues.append(f"a proposed region is fragmented into {maximum_fragmentation} islands")
    proposal_status = (
        "SINGLE_REGION_NO_DECOMPOSITION" if count == 1
        else "REVIEW_REQUIRED_LOW_CONFIDENCE" if quality_issues
        else "REVIEWABLE_PROPOSAL"
    )

    destination = Path(output_directory).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    label_path = destination / "component_proposal_labels.png"
    preview_path = destination / "component_proposal_preview.png"
    cv2.imwrite(str(label_path), label_map)
    preview = image.copy()
    boundaries = np.zeros_like(foreground)
    boundaries[1:, :] |= label_map[1:, :] != label_map[:-1, :]
    boundaries[:, 1:] |= label_map[:, 1:] != label_map[:, :-1]
    preview[boundaries & foreground] = (0, 255, 255)
    cv2.imwrite(str(preview_path), preview)
    result = {
        "schema_version": 1,
        "record_type": "COMPONENT_REGION_PROPOSAL",
        "source_reference_sha256": evidence["source"]["sha256"],
        "source_mask_sha256": evidence["artifact_sha256"]["editable_mask"],
        "proposal_method": "DETERMINISTIC_LAB_KMEANS",
        "seed": seed,
        "region_count": count,
        "regions": regions,
        "model_selection": model_selection,
        "proposal_confidence": confidence,
        "proposal_status": proposal_status,
        "quality_issues": quality_issues,
        "artifacts": {
            "editable_label_map": str(label_path),
            "preview": str(preview_path),
        },
        "artifact_sha256": {
            "editable_label_map": hashlib.sha256(label_path.read_bytes()).hexdigest(),
            "preview": hashlib.sha256(preview_path.read_bytes()).hexdigest(),
        },
        "accepted_as_semantic_evidence": False,
        "review_required": True,
        "manual_correction": {
            "allowed": True,
            "instruction": "Edit component_proposal_labels.png, assign semantic component IDs, then run annotate-components. Appearance labels never authorize geometry directly.",
        },
        "claim_boundary": "Regions are appearance clusters inside a verified object mask. They may split one part, merge same-colored parts, or follow lighting; they are not semantic components or cross-view identity.",
    }
    report_path = destination / "component_proposal.json"
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def import_component_region_proposal(
    reference_evidence: dict[str, Any] | str | Path,
    label_map_path: str | Path,
    provider_report: dict[str, Any] | str | Path,
    output_directory: str | Path,
) -> dict[str, Any]:
    """Normalize an external segmenter's labels into the same review-only proposal contract."""
    evidence = _read(reference_evidence)
    provider = _read(provider_report)
    segmentation_ready = evidence.get(
        "accepted_for_component_segmentation", evidence.get("accepted_for_fitting")
    )
    if evidence.get("record_type") != "REFERENCE_IMAGE_EVIDENCE" or not segmentation_ready:
        raise ValueError("external component proposals require REFERENCE_IMAGE_EVIDENCE accepted for component segmentation")
    for key in ("provider", "model_id", "model_version"):
        if not str(provider.get(key) or "").strip():
            raise ValueError(f"external provider report requires {key}")
    if provider.get("provider") == "Google Gemini" and provider.get("segmentation_gate_pass") is not True:
        raise ValueError("Gemini provider report did not pass its segmentation gate")
    source_path = _current_file(evidence.get("source", {}), label="source image")
    source_mask_path = _current_file(
        {
            "path": evidence.get("artifacts", {}).get("editable_mask"),
            "sha256": evidence.get("artifact_sha256", {}).get("editable_mask"),
        },
        label="editable source mask",
    )
    external_path = Path(label_map_path).resolve()
    image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    source_mask = cv2.imread(str(source_mask_path), cv2.IMREAD_GRAYSCALE)
    external = cv2.imread(str(external_path), cv2.IMREAD_GRAYSCALE)
    if image is None or source_mask is None or external is None or image.shape[:2] != source_mask.shape or external.shape != source_mask.shape:
        raise ValueError("external labels, source image, and source mask must be decodable at matching dimensions")
    foreground = source_mask >= 128
    if np.any((external > 0) & ~foreground):
        raise ValueError("external component labels leak outside the verified object mask")
    if np.any(foreground & (external == 0)):
        raise ValueError("external component labels must cover the complete verified object mask")
    observed = [int(value) for value in np.unique(external) if value]
    if not observed:
        raise ValueError("external component proposal contains no regions")
    confidence_record = provider.get("region_confidence", {})
    occlusion_record = provider.get("region_occlusion_expected", {})
    semantic_record = provider.get("region_semantic_proposals", {})
    if semantic_record and not isinstance(semantic_record, dict):
        raise ValueError("external region semantic proposals must be a label-keyed object")
    confidences = []
    normalized = np.zeros_like(external)
    for new_label, old_label in enumerate(observed, 1):
        value = confidence_record.get(str(old_label), confidence_record.get(old_label))
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"external region {old_label} requires confidence in [0, 1]")
        confidences.append(float(value))
        normalized[external == old_label] = new_label

    lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(float)
    regions = []
    maximum_unexpected_fragmentation = 1
    for label, (old_label, provider_confidence) in enumerate(zip(observed, confidences), 1):
        region_mask = normalized == label
        region_colors = lab_image[region_mask]
        connected_count, _connected = cv2.connectedComponents(region_mask.astype(np.uint8), connectivity=8)
        fragmentation = connected_count - 1
        occlusion_expected = occlusion_record.get(str(old_label), occlusion_record.get(old_label, False))
        if not isinstance(occlusion_expected, bool):
            raise ValueError(f"external region {label} occlusion expectation must be boolean")
        semantic = semantic_record.get(str(old_label), semantic_record.get(old_label))
        if semantic is not None:
            if not isinstance(semantic, dict):
                raise ValueError(f"external region {label} semantic proposal must be an object")
            if not str(semantic.get("label") or "").strip():
                raise ValueError(f"external region {label} semantic proposal requires a label")
            if semantic.get("role") not in {
                "PRIMARY_VOLUME", "ATTACHED_ASSEMBLY", "FASTENER", "INSERT", "OTHER"
            }:
                raise ValueError(f"external region {label} semantic proposal has an invalid role")
            if not str(semantic.get("evidence") or "").strip():
                raise ValueError(f"external region {label} semantic proposal requires visible evidence")
        if not occlusion_expected:
            maximum_unexpected_fragmentation = max(maximum_unexpected_fragmentation, fragmentation)
        regions.append({
            "proposal_region_id": f"appearance-region-{label:03d}",
            "label": label,
            "provider_confidence": provider_confidence,
            "occlusion_expected": occlusion_expected,
            "provider_semantic_proposal": dict(semantic) if semantic is not None else None,
            "visible_area_fraction_of_object": float(region_mask.sum() / foreground.sum()),
            "mean_lab": region_colors.mean(axis=0).tolist(),
            "color_dispersion_lab": float(np.mean(np.linalg.norm(region_colors - region_colors.mean(axis=0), axis=1))),
            "connected_fragment_count": fragmentation,
            "measurements": analyze_reference_mask(region_mask),
        })
    confidence = min(confidences) / max(1, maximum_unexpected_fragmentation)
    quality_issues = []
    if confidence < 0.6:
        quality_issues.append(f"external proposal confidence is only {confidence:.4f} after fragmentation penalty")
    if maximum_unexpected_fragmentation > 4:
        quality_issues.append(f"an external region is unexpectedly fragmented into {maximum_unexpected_fragmentation} islands")
    status = "REVIEW_REQUIRED_LOW_CONFIDENCE" if quality_issues else "REVIEWABLE_PROPOSAL"

    destination = Path(output_directory).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    output_label_path = destination / "component_proposal_labels.png"
    preview_path = destination / "component_proposal_preview.png"
    cv2.imwrite(str(output_label_path), normalized)
    preview = image.copy()
    boundaries = np.zeros_like(foreground)
    boundaries[1:, :] |= normalized[1:, :] != normalized[:-1, :]
    boundaries[:, 1:] |= normalized[:, 1:] != normalized[:, :-1]
    preview[boundaries & foreground] = (0, 255, 255)
    cv2.imwrite(str(preview_path), preview)
    result = {
        "schema_version": 1,
        "record_type": "COMPONENT_REGION_PROPOSAL",
        "source_reference_sha256": evidence["source"]["sha256"],
        "source_mask_sha256": evidence["artifact_sha256"]["editable_mask"],
        "proposal_method": "EXTERNAL_LABEL_IMPORT",
        "provider": dict(provider),
        "provider_label_map": {
            "path": str(external_path),
            "sha256": hashlib.sha256(external_path.read_bytes()).hexdigest(),
        },
        "region_count": len(regions),
        "regions": regions,
        "model_selection": {"authority": "EXTERNAL_PROVIDER_REVIEW_REQUIRED"},
        "proposal_confidence": confidence,
        "proposal_status": status,
        "quality_issues": quality_issues,
        "artifacts": {"editable_label_map": str(output_label_path), "preview": str(preview_path)},
        "artifact_sha256": {
            "editable_label_map": hashlib.sha256(output_label_path.read_bytes()).hexdigest(),
            "preview": hashlib.sha256(preview_path.read_bytes()).hexdigest(),
        },
        "accepted_as_semantic_evidence": False,
        "review_required": True,
        "manual_correction": {
            "allowed": True,
            "instruction": "Review or edit component_proposal_labels.png before correspondence confirmation. Provider confidence does not authorize geometry.",
        },
        "claim_boundary": "External labels are hash-bound proposals from the declared provider. Model output is not semantic truth, physical continuity, or final topology.",
    }
    (destination / "component_proposal.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _proposal_descriptor(region: dict[str, Any]) -> np.ndarray:
    measurements = region["measurements"]
    return np.asarray([
        *region["mean_lab"],
        math.log(max(float(region["visible_area_fraction_of_object"]), 1e-8)),
        math.log(max(float(measurements["aspect_ratio_width_over_height"]), 1e-8)),
    ])


_SEMANTIC_TOKEN_ALIASES = {
    "bolts": "fastener", "bolt": "fastener", "screws": "fastener", "screw": "fastener",
    "rivets": "fastener", "rivet": "fastener", "fasteners": "fastener",
    "scales": "scale", "grips": "grip", "assemblies": "assembly",
}
_SEMANTIC_GENERIC_TOKENS = {
    "and", "body", "component", "assembly", "primary", "volume", "visible",
    "metal", "steel", "composite", "g", "material",
}


def _semantic_tokens(region: dict[str, Any]) -> set[str]:
    semantic = region.get("provider_semantic_proposal")
    if not isinstance(semantic, dict):
        return set()
    tokens = re.findall(r"[a-z]+", str(semantic.get("label") or "").lower())
    normalized = {_SEMANTIC_TOKEN_ALIASES.get(token, token) for token in tokens}
    return normalized - _SEMANTIC_GENERIC_TOKENS


def _pair_cost(
    first: dict[str, Any],
    second: dict[str, Any],
    *,
    first_scope: str,
    second_scope: str,
) -> tuple[float, dict[str, Any]]:
    left, right = _proposal_descriptor(first), _proposal_descriptor(second)
    feature_costs: dict[str, float] = {
        "color_lab": min(float(np.linalg.norm(left[:3] - right[:3]) / 80.0), 2.0),
        "visible_area": min(float(abs(left[3] - right[3])), 2.0),
        "aspect_ratio": min(float(abs(left[4] - right[4])), 2.0),
    }
    weights = {"color_lab": 0.70, "visible_area": 0.18, "aspect_ratio": 0.12}
    first_tokens, second_tokens = _semantic_tokens(first), _semantic_tokens(second)
    first_semantic, second_semantic = (
        first.get("provider_semantic_proposal"), second.get("provider_semantic_proposal")
    )
    if first_tokens and second_tokens and isinstance(first_semantic, dict) and isinstance(second_semantic, dict):
        # A detail view often uses a shorter compatible phrase ("axe head") than a full
        # view ("axe head and tang steel body"). Overlap coefficient preserves that subset
        # relation while role and visual features keep words from authorizing identity.
        semantic_overlap = len(first_tokens & second_tokens) / min(len(first_tokens), len(second_tokens))
        feature_costs["semantic_label"] = 1.0 - semantic_overlap
        feature_costs["semantic_role"] = float(first_semantic.get("role") != second_semantic.get("role"))
        weights = {
            "color_lab": 0.30,
            "visible_area": 0.12,
            "aspect_ratio": 0.08,
            "semantic_label": 0.35,
            "semantic_role": 0.15,
        }
    scope_reliability = {
        "FULL_OBJECT": 1.0,
        "OCCLUDED_OBJECT": 0.45,
        "PARTIAL_OBJECT": 0.25,
        "COMPONENT_DETAIL": 0.20,
    }
    reliability = min(scope_reliability[first_scope], scope_reliability[second_scope])
    weights["visible_area"] *= reliability
    weights["aspect_ratio"] *= reliability
    weight_total = sum(weights.values())
    normalized_weights = {name: value / weight_total for name, value in weights.items()}
    cost = float(sum(feature_costs[name] * normalized_weights[name] for name in normalized_weights))
    return cost, {
        "feature_costs": feature_costs,
        "normalized_weights": normalized_weights,
        "scope_reliability": reliability,
    }


def propose_cross_view_correspondences(views: list[dict[str, Any]]) -> dict[str, Any]:
    """Match review-only regions without forcing absent or unrelated components together."""
    if not isinstance(views, list) or len(views) < 2:
        raise ValueError("cross-view proposal requires at least two views")
    loaded = []
    identifiers = []
    allowed_scopes = {"FULL_OBJECT", "OCCLUDED_OBJECT", "PARTIAL_OBJECT", "COMPONENT_DETAIL"}
    declared_identities = set()
    for item in views:
        view_id = str(item.get("view_id") or "").strip().lower()
        if not view_id:
            raise ValueError("proposal view ids must be non-empty")
        identifiers.append(view_id)
        proposal = _read(item.get("proposal"))
        if proposal.get("record_type") != "COMPONENT_REGION_PROPOSAL":
            raise ValueError(f"{view_id}: invalid component region proposal")
        _current_file(
            {
                "path": proposal.get("artifacts", {}).get("editable_label_map"),
                "sha256": proposal.get("artifact_sha256", {}).get("editable_label_map"),
            },
            label=f"{view_id} editable proposal label map",
        )
        scope = str(item.get("geometry_scope") or "FULL_OBJECT").strip().upper()
        if scope not in allowed_scopes:
            raise ValueError(f"{view_id}: unknown geometry_scope")
        target_id = str(item.get("target_id") or "").strip()
        target_variant = str(item.get("target_variant") or "").strip()
        if bool(target_id) != bool(target_variant):
            raise ValueError(f"{view_id}: target_id and target_variant must be declared together")
        if target_id:
            declared_identities.add((target_id, target_variant))
        loaded.append({"view_id": view_id, "proposal": proposal, "scope": scope})
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("proposal view ids must be unique")
    if len(declared_identities) > 1:
        raise ValueError("cross-view proposals contain mixed target identity or variant")
    if declared_identities and len(declared_identities) == 1 and any(
        not str(item.get("target_id") or "").strip() for item in views
    ):
        raise ValueError("identity-bound correspondence requires target identity on every view")

    anchor_id, anchor = loaded[0]["view_id"], loaded[0]["proposal"]
    groups = [
        {
            "proposal_group_id": f"component-group-{index + 1:03d}",
            "matches": {anchor_id: region["proposal_region_id"]},
            "pair_confidence": {},
            "match_diagnostics": {},
            "_members": [(region, loaded[0]["scope"])],
            "_qualities": [float(anchor.get("proposal_confidence", 0.0))],
        }
        for index, region in enumerate(anchor["regions"])
    ]
    unmatched = {anchor_id: []}
    ambiguous = []
    maximum_match_cost = 0.85
    for loaded_view in loaded[1:]:
        view_id, proposal, scope = (
            loaded_view["view_id"], loaded_view["proposal"], loaded_view["scope"]
        )
        pair_details: list[list[dict[str, Any]]] = []
        costs = np.zeros((len(groups), len(proposal["regions"])), dtype=float)
        for group_index, group in enumerate(groups):
            detail_row = []
            for region_index, region in enumerate(proposal["regions"]):
                member_results = [
                    _pair_cost(member, region, first_scope=member_scope, second_scope=scope)
                    for member, member_scope in group["_members"]
                ]
                member_costs = np.asarray([result[0] for result in member_results], dtype=float)
                representative = int(np.argmin(member_costs))
                costs[group_index, region_index] = float(np.median(member_costs))
                detail_row.append({
                    **member_results[representative][1],
                    "aggregate_cost": float(costs[group_index, region_index]),
                    "representative_prior_view_count": len(member_results),
                })
            pair_details.append(detail_row)
        group_rows, other_columns = linear_sum_assignment(costs)
        matched_other = set()
        rejected_other = set()
        for row, column in zip(group_rows.tolist(), other_columns.tolist()):
            selected_cost = float(costs[row, column])
            alternatives = np.delete(costs[row], column).tolist()
            alternatives.append(maximum_match_cost)
            second = float(min(alternatives))
            margin = float(np.clip((second - selected_cost) / max(second, 1e-6), 0.0, 1.0))
            if selected_cost >= maximum_match_cost:
                rejected_other.add(column)
                continue
            matched_other.add(column)
            proposal_quality = min(
                min(groups[row]["_qualities"]),
                float(proposal.get("proposal_confidence", 0.0)),
            )
            confidence = float(math.exp(-selected_cost) * margin * proposal_quality)
            groups[row]["matches"][view_id] = proposal["regions"][column]["proposal_region_id"]
            groups[row]["pair_confidence"][view_id] = confidence
            groups[row]["match_diagnostics"][view_id] = {
                **pair_details[row][column],
                "selected_cost": selected_cost,
                "no_match_cost": maximum_match_cost,
                "assignment_margin": margin,
            }
            groups[row]["_members"].append((proposal["regions"][column], scope))
            groups[row]["_qualities"].append(float(proposal.get("proposal_confidence", 0.0)))
            if confidence < 0.6:
                ambiguous.append({"view_id": view_id, "group_id": groups[row]["proposal_group_id"], "confidence": confidence})
        unmatched_indices = [index for index in range(len(proposal["regions"])) if index not in matched_other]
        unmatched[view_id] = [proposal["regions"][index]["proposal_region_id"] for index in unmatched_indices]
        for index in unmatched_indices:
            region = proposal["regions"][index]
            groups.append({
                "proposal_group_id": f"component-group-{len(groups) + 1:03d}",
                "matches": {view_id: region["proposal_region_id"]},
                "pair_confidence": {},
                "match_diagnostics": {view_id: {
                    "created_from_unmatched_region": True,
                    "rejected_by_cost_gate": index in rejected_other,
                    "no_match_cost": maximum_match_cost,
                }},
                "_members": [(region, scope)],
                "_qualities": [float(proposal.get("proposal_confidence", 0.0))],
            })
    incomplete = [group["proposal_group_id"] for group in groups if len(group["matches"]) != len(loaded)]
    status = "CONFIDENT_PROPOSAL" if not ambiguous and not incomplete and not any(unmatched.values()) else "AMBIGUOUS_REVIEW_REQUIRED"
    public_groups = [
        {key: value for key, value in group.items() if not key.startswith("_")}
        for group in groups
    ]
    return {
        "schema_version": 1,
        "record_type": "CROSS_VIEW_COMPONENT_CORRESPONDENCE_PROPOSAL",
        "anchor_view_id": anchor_id,
        "view_ids": identifiers,
        "target_identity": (
            {"target_id": next(iter(declared_identities))[0], "target_variant": next(iter(declared_identities))[1]}
            if declared_identities else None
        ),
        "view_geometry_scope": {item["view_id"]: item["scope"] for item in loaded},
        "proposal_bindings": {
            item["view_id"]: {
                "source_reference_sha256": proposal["source_reference_sha256"],
                "source_mask_sha256": proposal["source_mask_sha256"],
                "editable_label_map_sha256": proposal["artifact_sha256"]["editable_label_map"],
            }
            for item in loaded for proposal in [item["proposal"]]
        },
        "groups": public_groups,
        "unmatched_regions": unmatched,
        "incomplete_groups": incomplete,
        "ambiguous_matches": ambiguous,
        "matching_model": {
            "method": "INCREMENTAL_GLOBAL_ASSIGNMENT_WITH_EXPLICIT_NO_MATCH",
            "maximum_match_cost": maximum_match_cost,
            "features": ["color_lab", "visible_area", "aspect_ratio", "provider_semantic_label_if_available", "provider_semantic_role_if_available"],
            "partial_view_area_aspect_downweighting": True,
        },
        "status": status,
        "accepted_as_semantic_identity": False,
        "review_required": True,
        "manual_correction": {
            "allowed": True,
            "instruction": "Edit group matches and assign semantic IDs before producing REFERENCE_COMPONENT_EVIDENCE records.",
        },
        "claim_boundary": "Matching combines appearance, bounded geometry descriptors, and optional provider semantic proposals with an explicit no-match gate. Provider words remain proposal features, not identity truth or geometry authorization.",
    }


def materialize_confirmed_component_evidence(
    correspondence: dict[str, Any] | str | Path,
    views: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
    confirmation: dict[str, Any],
    output_directory: str | Path,
) -> dict[str, Any]:
    """Convert explicitly reviewed proposal groups into bundle-ready semantic label evidence."""
    proposal = _read(correspondence)
    if proposal.get("record_type") != "CROSS_VIEW_COMPONENT_CORRESPONDENCE_PROPOSAL":
        raise ValueError("confirmation requires a cross-view component correspondence proposal")
    if confirmation.get("decision") != "CONFIRM_COMPONENT_IDENTITY":
        raise ValueError("confirmation decision must be CONFIRM_COMPONENT_IDENTITY")
    if confirmation.get("reviewer_type") not in {"HUMAN", "AGENT_EVIDENCE_REVIEW"}:
        raise ValueError("confirmation reviewer_type must be HUMAN or AGENT_EVIDENCE_REVIEW")
    if not str(confirmation.get("reviewer_id") or "").strip() or not str(confirmation.get("reviewed_at") or "").strip():
        raise ValueError("confirmation requires reviewer_id and reviewed_at")
    if not isinstance(assignments, list) or not assignments:
        raise ValueError("at least one confirmed semantic assignment is required")

    group_ids = [group["proposal_group_id"] for group in proposal.get("groups", [])]
    assigned_groups = [str(item.get("proposal_group_id") or "") for item in assignments]
    component_ids = [str(item.get("component_id") or "").strip() for item in assignments]
    if set(assigned_groups) != set(group_ids) or len(assigned_groups) != len(set(assigned_groups)):
        raise ValueError("confirmed assignments must cover every proposal group exactly once")
    if any(not identifier for identifier in component_ids) or len(component_ids) != len(set(component_ids)):
        raise ValueError("confirmed component ids must be unique and non-empty")
    if len(assignments) > 255:
        raise ValueError("confirmed component labels exceed the grayscale label-map limit")

    view_ids = [str(item.get("view_id") or "").strip().lower() for item in views]
    if set(view_ids) != set(proposal.get("view_ids", [])) or len(view_ids) != len(set(view_ids)):
        raise ValueError("confirmation views must exactly match the correspondence proposal")
    proposal_hash = hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    group_map = {group["proposal_group_id"]: group for group in proposal["groups"]}
    assignment_map = {item["proposal_group_id"]: item for item in assignments}
    destination = Path(output_directory).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    records = {}
    issues = []
    for item in views:
        view_id = str(item["view_id"]).strip().lower()
        region_proposal = _read(item.get("proposal"))
        evidence = _read(item.get("evidence"))
        if region_proposal.get("record_type") != "COMPONENT_REGION_PROPOSAL":
            raise ValueError(f"{view_id}: invalid component region proposal")
        binding = proposal.get("proposal_bindings", {}).get(view_id)
        actual_binding = {
            "source_reference_sha256": region_proposal.get("source_reference_sha256"),
            "source_mask_sha256": region_proposal.get("source_mask_sha256"),
            "editable_label_map_sha256": region_proposal.get("artifact_sha256", {}).get("editable_label_map"),
        }
        if binding != actual_binding:
            raise ValueError(f"{view_id}: proposal no longer matches its correspondence binding")
        if evidence.get("source", {}).get("sha256") != binding["source_reference_sha256"]:
            raise ValueError(f"{view_id}: reference evidence belongs to another source")
        if evidence.get("artifact_sha256", {}).get("editable_mask") != binding["source_mask_sha256"]:
            raise ValueError(f"{view_id}: reference mask revision differs from the proposal")
        label_path = _current_file(
            {
                "path": region_proposal.get("artifacts", {}).get("editable_label_map"),
                "sha256": binding["editable_label_map_sha256"],
            },
            label=f"{view_id} editable proposal label map",
        )
        source_labels = cv2.imread(str(label_path), cv2.IMREAD_GRAYSCALE)
        if source_labels is None:
            raise ValueError(f"{view_id}: proposal label map cannot be decoded")
        region_labels = {
            region["proposal_region_id"]: int(region["label"])
            for region in region_proposal.get("regions", [])
        }
        confirmed_labels = np.zeros_like(source_labels)
        component_specs = []
        for semantic_label, assignment in enumerate(assignments, 1):
            group = group_map[assignment["proposal_group_id"]]
            region_id = group.get("matches", {}).get(view_id)
            if region_id not in region_labels:
                raise ValueError(f"{view_id}: confirmed group {group['proposal_group_id']} has no bound region")
            confirmed_labels[source_labels == region_labels[region_id]] = semantic_label
            component_specs.append({
                "id": assignment["component_id"],
                "label": semantic_label,
                "role": assignment.get("role", "UNSPECIFIED"),
                "continuity_policy": assignment.get("continuity_policy", "UNRESOLVED"),
            })
        if np.any((source_labels > 0) & (confirmed_labels == 0)):
            raise ValueError(f"{view_id}: confirmed groups leave proposal pixels unmapped")
        view_directory = destination / view_id
        view_directory.mkdir(parents=True, exist_ok=True)
        confirmed_path = view_directory / "confirmed_component_labels.png"
        cv2.imwrite(str(confirmed_path), confirmed_labels)
        component_evidence = extract_component_evidence(evidence, confirmed_path, component_specs)
        component_evidence["proposal_confirmation"] = {
            "correspondence_sha256": proposal_hash,
            "confirmation": dict(confirmation),
            "assignments": [dict(assignment_map[group_id]) for group_id in group_ids],
        }
        component_evidence["claim_boundary"] = (
            "Semantic IDs were explicitly confirmed from hash-bound appearance proposals. "
            "Confirmation establishes reviewed cross-view naming, not hidden extent, continuity, or geometry."
        )
        record_path = view_directory / "component_evidence.json"
        record_path.write_text(json.dumps(component_evidence, indent=2) + "\n", encoding="utf-8")
        if not component_evidence["accepted_for_bundle"]:
            issues.extend(f"{view_id}: {issue}" for issue in component_evidence["issues"])
        records[view_id] = {
            "path": str(record_path),
            "sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
            "component_ids": component_evidence["component_ids"],
            "accepted_for_bundle": component_evidence["accepted_for_bundle"],
        }
    return {
        "schema_version": 1,
        "record_type": "CONFIRMED_CROSS_VIEW_COMPONENT_SET",
        "correspondence_sha256": proposal_hash,
        "confirmation": dict(confirmation),
        "assignments": [dict(assignment_map[group_id]) for group_id in group_ids],
        "views": records,
        "ready_for_bundle": not issues and len(records) == len(views),
        "issues": issues,
        "claim_boundary": "This record materializes reviewed semantic labels. It does not prove physical continuity, hidden structure, or final shape.",
    }
