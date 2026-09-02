import hashlib
from pathlib import Path

import cv2
import numpy as np
import pytest

from modeling_core import analyze_reference_mask, extract_reference_evidence


def test_alpha_evidence_preserves_enclosed_negative_space(tmp_path: Path):
    image = np.zeros((80, 100, 4), dtype=np.uint8)
    image[12:68, 18:82, :3] = (80, 120, 190)
    image[12:68, 18:82, 3] = 255
    image[30:50, 38:62, 3] = 0
    source = tmp_path / "ring.png"
    cv2.imwrite(str(source), image)

    report = extract_reference_evidence(source, tmp_path / "evidence")

    assert report["accepted_for_fitting"] is True
    assert report["extraction"]["method"] == "alpha"
    assert report["measurements"]["enclosed_negative_space_count"] == 1
    assert Path(report["artifacts"]["editable_mask"]).is_file()
    assert report["source"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


def test_border_background_extracts_outline_and_normalized_crop(tmp_path: Path):
    image = np.full((120, 90, 3), 245, dtype=np.uint8)
    polygon = np.asarray([[45, 8], [68, 42], [61, 108], [29, 108], [22, 42]], dtype=np.int32)
    cv2.fillPoly(image, [polygon], (30, 45, 180))
    source = tmp_path / "blade.png"
    cv2.imwrite(str(source), image)

    report = extract_reference_evidence(source, tmp_path / "evidence")

    assert report["accepted_for_fitting"] is True
    assert report["extraction"]["method"] == "border_lab_distance"
    assert report["measurements"]["aspect_ratio_width_over_height"] < 0.6
    assert len(report["measurements"]["outline_landmarks_normalized"]) >= 5
    assert len(report["measurements"]["row_profile"]) == 33
    normalized = cv2.imread(report["artifacts"]["normalized_image"], cv2.IMREAD_UNCHANGED)
    assert normalized.shape[0] < image.shape[0]
    assert normalized.shape[1] < image.shape[1]


def test_empty_or_indistinguishable_reference_fails_closed(tmp_path: Path):
    source = tmp_path / "empty.png"
    cv2.imwrite(str(source), np.full((64, 64, 3), 127, dtype=np.uint8))
    with pytest.raises(ValueError, match="no usable foreground"):
        extract_reference_evidence(source, tmp_path / "evidence")


def test_manual_mask_override_is_remeasured_and_hashed(tmp_path: Path):
    image = np.full((50, 70, 3), 255, dtype=np.uint8)
    source = tmp_path / "photo.png"
    cv2.imwrite(str(source), image)
    override = np.zeros((50, 70), dtype=np.uint8)
    override[8:42, 20:50] = 255
    override_path = tmp_path / "edited-mask.png"
    cv2.imwrite(str(override_path), override)

    report = extract_reference_evidence(source, tmp_path / "evidence", mask_override=override_path)

    assert report["accepted_for_fitting"] is True
    assert report["manual_correction"]["applied"] is True
    assert report["extraction"]["method"] == "manual_mask_override"
    assert report["extraction"]["override_sha256"] == hashlib.sha256(override_path.read_bytes()).hexdigest()
    assert report["measurements"]["bbox_pixels"] == [20, 8, 50, 42]


def test_mask_analysis_uses_full_image_normalized_coordinates():
    mask = np.zeros((20, 40), dtype=bool)
    mask[5:15, 10:30] = True
    result = analyze_reference_mask(mask)
    assert result["bbox_normalized"] == [0.25, 0.25, 0.75, 0.75]
    assert result["centroid_normalized"] == pytest.approx([0.4875, 0.475])
