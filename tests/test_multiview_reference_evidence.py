from pathlib import Path

import cv2
import numpy as np

from modeling_core import (
    build_multiview_evidence_bundle,
    extract_component_evidence,
    extract_reference_evidence,
)


def _view(tmp_path: Path, name: str, *, shift: int = 0):
    image = np.full((80, 100, 3), 250, dtype=np.uint8)
    image[12:68, 24 + shift:72 + shift] = (40, 60, 180)
    image[30:50, 72 + shift:84 + shift] = (40, 60, 180)
    source = tmp_path / f"{name}.png"
    cv2.imwrite(str(source), image)
    evidence = extract_reference_evidence(source, tmp_path / f"{name}-evidence")
    labels = np.zeros((80, 100), dtype=np.uint8)
    labels[12:68, 24 + shift:72 + shift] = 1
    labels[30:50, 72 + shift:84 + shift] = 2
    label_path = tmp_path / f"{name}-labels.png"
    cv2.imwrite(str(label_path), labels)
    components = extract_component_evidence(
        evidence,
        label_path,
        [
            {"id": "body", "label": 1, "continuity_policy": "CONTINUOUS_MESH"},
            {"id": "handle", "label": 2, "continuity_policy": "SEPARATE_ASSEMBLY"},
        ],
    )
    return evidence, components


def _gates(first, second):
    hashes = [first["source"]["sha256"], second["source"]["sha256"]]
    audit = {
        "schema_version": 1,
        "record_type": "REFERENCE_SET_AUDIT",
        "target_id": "fixture",
        "target_variant": "v1",
        "authorized_reference_sha256": hashes,
        "pass": True,
    }
    registration = {
        "schema_version": 1,
        "record_type": "REFERENCE_REGISTRATION_GATE",
        "target_id": "fixture",
        "authoritative_views": ["front", "side"],
        "pass": True,
    }
    return audit, registration


def test_component_labels_measure_regions_and_visible_adjacency(tmp_path: Path):
    _evidence, components = _view(tmp_path, "front")
    assert components["accepted_for_bundle"] is True
    assert components["foreground_coverage"] == 1.0
    assert components["background_leakage"] == 0.0
    assert components["visible_adjacency"] == [["body", "handle"]]
    assert components["observations"]["handle"]["continuity_policy"] == "SEPARATE_ASSEMBLY"


def test_multiview_bundle_requires_audits_hashes_and_component_support(tmp_path: Path):
    front = _view(tmp_path, "front")
    side = _view(tmp_path, "side", shift=2)
    audit, registration = _gates(front[0], side[0])
    result = build_multiview_evidence_bundle(
        audit,
        registration,
        [
            {"view_id": "front", "source_id": "set-a", "evidence": front[0], "components": front[1]},
            {"view_id": "side", "source_id": "set-a", "evidence": side[0], "components": side[1]},
        ],
        required_component_support={"body": 2, "handle": 2},
    )
    assert result["accepted_for_shape_solving"] is True
    assert result["component_support"] == {"body": ["front", "side"], "handle": ["front", "side"]}


def test_bundle_rejects_duplicate_image_and_missing_component_support(tmp_path: Path):
    front = _view(tmp_path, "front")
    second = _view(tmp_path, "side", shift=2)
    audit, registration = _gates(front[0], second[0])
    result = build_multiview_evidence_bundle(
        audit,
        registration,
        [
            {"view_id": "front", "source_id": "set-a", "evidence": front[0], "components": front[1]},
            {"view_id": "side", "source_id": "set-a", "evidence": front[0], "components": front[1]},
        ],
        required_component_support={"hidden-fastener": 2},
    )
    assert result["accepted_for_shape_solving"] is False
    assert any("same source image" in issue for issue in result["issues"])
    assert result["missing_component_support"]["hidden-fastener"] == {"required": 2, "observed": 0}


def test_component_evidence_rejects_unlabeled_object_area(tmp_path: Path):
    evidence, _components = _view(tmp_path, "front")
    labels = np.zeros((80, 100), dtype=np.uint8)
    labels[12:40, 24:72] = 1
    label_path = tmp_path / "partial.png"
    cv2.imwrite(str(label_path), labels)
    result = extract_component_evidence(evidence, label_path, [{"id": "body", "label": 1}])
    assert result["accepted_for_bundle"] is False
    assert result["foreground_coverage"] < 0.95


def test_component_evidence_rejects_a_mask_edited_without_remeasurement(tmp_path: Path):
    evidence, _components = _view(tmp_path, "front")
    mask_path = Path(evidence["artifacts"]["editable_mask"])
    cv2.imwrite(str(mask_path), np.zeros((80, 100), dtype=np.uint8))
    labels = np.zeros((80, 100), dtype=np.uint8)
    label_path = tmp_path / "labels.png"
    cv2.imwrite(str(label_path), labels)
    try:
        extract_component_evidence(evidence, label_path, [{"id": "body", "label": 1}])
    except ValueError as error:
        assert "mask no longer matches" in str(error)
    else:
        raise AssertionError("tampered mask was accepted")
