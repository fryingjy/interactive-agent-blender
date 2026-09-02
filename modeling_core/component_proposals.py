"""Propose editable appearance regions and cross-view matches without claiming semantics."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

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
    if evidence.get("record_type") != "REFERENCE_IMAGE_EVIDENCE" or not evidence.get("accepted_for_fitting"):
        raise ValueError("component proposals require accepted REFERENCE_IMAGE_EVIDENCE")
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
    else:
        region_centers = np.asarray([region["mean_lab"] for region in regions])
        pairwise = np.linalg.norm(region_centers[:, None] - region_centers[None, :], axis=2)
        separation = float(np.min(pairwise[np.triu_indices(count, 1)]))
        dispersion = max(float(region["color_dispersion_lab"]) for region in regions)
        fragmentation = max(int(region["connected_fragment_count"]) for region in regions)
        confidence = float(np.clip((separation - dispersion) / 45.0, 0.0, 1.0) * (1.0 / max(1, fragmentation)))

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


def _proposal_descriptor(region: dict[str, Any]) -> np.ndarray:
    measurements = region["measurements"]
    return np.asarray([
        *region["mean_lab"],
        math.log(max(float(region["visible_area_fraction_of_object"]), 1e-8)),
        math.log(max(float(measurements["aspect_ratio_width_over_height"]), 1e-8)),
    ])


def propose_cross_view_correspondences(views: list[dict[str, Any]]) -> dict[str, Any]:
    """Match appearance proposals across views while preserving ambiguity and unmatched regions."""
    if not isinstance(views, list) or len(views) < 2:
        raise ValueError("cross-view proposal requires at least two views")
    loaded = []
    identifiers = []
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
        loaded.append((view_id, proposal))
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("proposal view ids must be unique")

    anchor_id, anchor = loaded[0]
    groups = [
        {
            "proposal_group_id": f"appearance-group-{index + 1:03d}",
            "matches": {anchor_id: region["proposal_region_id"]},
            "pair_confidence": {},
        }
        for index, region in enumerate(anchor["regions"])
    ]
    unmatched = {}
    ambiguous = []
    anchor_descriptors = np.asarray([_proposal_descriptor(region) for region in anchor["regions"]])
    for view_id, proposal in loaded[1:]:
        other_descriptors = np.asarray([_proposal_descriptor(region) for region in proposal["regions"]])
        color_cost = np.linalg.norm(anchor_descriptors[:, None, :3] - other_descriptors[None, :, :3], axis=2) / 80.0
        area_cost = np.abs(anchor_descriptors[:, None, 3] - other_descriptors[None, :, 3])
        aspect_cost = np.abs(anchor_descriptors[:, None, 4] - other_descriptors[None, :, 4])
        costs = 0.7 * color_cost + 0.18 * area_cost + 0.12 * aspect_cost
        anchor_rows, other_columns = linear_sum_assignment(costs)
        matched_other = set()
        for row, column in zip(anchor_rows.tolist(), other_columns.tolist()):
            matched_other.add(column)
            selected_cost = float(costs[row, column])
            alternatives = np.delete(costs[row], column)
            if len(alternatives):
                second = float(np.min(alternatives))
                margin = float(np.clip((second - selected_cost) / max(second, 1e-6), 0.0, 1.0))
            else:
                margin = 1.0
            confidence = float(math.exp(-selected_cost) * margin)
            groups[row]["matches"][view_id] = proposal["regions"][column]["proposal_region_id"]
            groups[row]["pair_confidence"][view_id] = confidence
            if confidence < 0.6:
                ambiguous.append({"view_id": view_id, "group_id": groups[row]["proposal_group_id"], "confidence": confidence})
        unmatched[view_id] = [
            region["proposal_region_id"]
            for index, region in enumerate(proposal["regions"])
            if index not in matched_other
        ]
    incomplete = [group["proposal_group_id"] for group in groups if len(group["matches"]) != len(loaded)]
    status = "CONFIDENT_PROPOSAL" if not ambiguous and not incomplete and not any(unmatched.values()) else "AMBIGUOUS_REVIEW_REQUIRED"
    return {
        "schema_version": 1,
        "record_type": "CROSS_VIEW_COMPONENT_CORRESPONDENCE_PROPOSAL",
        "anchor_view_id": anchor_id,
        "view_ids": identifiers,
        "groups": groups,
        "unmatched_regions": unmatched,
        "incomplete_groups": incomplete,
        "ambiguous_matches": ambiguous,
        "status": status,
        "accepted_as_semantic_identity": False,
        "review_required": True,
        "manual_correction": {
            "allowed": True,
            "instruction": "Edit group matches and assign semantic IDs before producing REFERENCE_COMPONENT_EVIDENCE records.",
        },
        "claim_boundary": "Matching compares visible appearance, area, and aspect descriptors. It does not prove that regions are the same physical component across views.",
    }
