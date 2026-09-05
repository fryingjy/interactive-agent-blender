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
    mask_path = Path(report["artifacts"]["editable_mask"])
    assert report["artifact_sha256"]["editable_mask"] == hashlib.sha256(mask_path.read_bytes()).hexdigest()
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


def test_uint16_product_png_is_normalized_before_lab_extraction(tmp_path: Path):
    image = np.full((90, 120, 3), 65535, dtype=np.uint16)
    image[15:75, 20:100] = (7000, 9000, 11000)
    source = tmp_path / "catalog-16-bit.png"
    assert cv2.imwrite(str(source), image)

    report = extract_reference_evidence(source, tmp_path / "catalog-evidence")

    assert report["accepted_for_fitting"] is True
    assert report["extraction"]["decode"] == {
        "source_dtype": "uint16",
        "working_dtype": "uint8",
        "bit_depth_normalization": "UINT16_FULL_RANGE_TO_UINT8",
    }
    normalized = cv2.imread(report["artifacts"]["normalized_image"], cv2.IMREAD_UNCHANGED)
    assert normalized.dtype == np.uint8


def test_edge_cropped_product_detail_can_segment_but_cannot_fit_full_silhouette(tmp_path: Path):
    image = np.full((100, 140, 3), 250, dtype=np.uint8)
    cv2.rectangle(image, (35, 15), (139, 85), (25, 30, 35), thickness=-1)
    source = tmp_path / "edge-cropped-detail.png"
    assert cv2.imwrite(str(source), image)

    report = extract_reference_evidence(source, tmp_path / "detail-evidence")

    assert report["accepted_for_component_segmentation"] is True
    assert report["accepted_for_fitting"] is False
    assert report["segmentation_issues"] == []
    assert any("crop-truncated" in issue for issue in report["issues"])
    assert report["extraction"]["border_background_inlier_fraction"] > 0.55


def test_unsupported_float_decode_fails_with_explicit_dtype_error(monkeypatch, tmp_path: Path):
    source = tmp_path / "unsupported.exr"
    source.write_bytes(b"fixture")
    monkeypatch.setattr(cv2, "imread", lambda *_args, **_kwargs: np.ones((8, 8, 3), dtype=np.float32))

    with pytest.raises(ValueError, match="dtype float32 is unsupported"):
        extract_reference_evidence(source, tmp_path / "unused")


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


def test_negative_space_inventory_localizes_without_filling_or_inventing_semantics():
    mask = np.zeros((40, 50), dtype=bool)
    mask[3:37, 3:47] = True
    mask[8:18, 10:22] = False
    mask[25, 30] = False  # Could be a tiny real aperture or noise: do not decide.
    before = mask.copy()
    result = analyze_reference_mask(mask)
    review = result['negative_space_review']
    assert result['enclosed_negative_space_count'] == 2
    assert [r['area_pixels'] for r in review['regions']] == [120, 1]
    assert review['regions'][0]['bbox_pixels'] == [10, 8, 22, 18]
    assert review['regions'][0]['seed_pixel'] == [10, 8]
    assert review['geometric_hole_count'] is None
    assert not review['truncated']
    assert np.array_equal(mask, before)
    assert review['mask_pixels_sha256'] == hashlib.sha256(mask.astype(np.uint8).tobytes()).hexdigest()


def test_negative_space_inventory_is_bounded_but_counts_are_not_truncated():
    mask = np.zeros((44, 44), dtype=bool)
    mask[2:42, 2:42] = True
    mask[5:35:3, 5:35:3] = False
    result = analyze_reference_mask(mask)
    assert result['enclosed_negative_space_count'] == 100
    assert len(result['negative_space_review']['regions']) == 64
    assert result['negative_space_review']['truncated'] is True
    assert result['enclosed_negative_space_fraction'] == pytest.approx(100 / mask.size)


def test_negative_space_inventory_excludes_exterior_connected_notches():
    mask = np.zeros((30, 30), dtype=bool)
    mask[5:25, 5:25] = True
    mask[5:15, 12:16] = False
    result = analyze_reference_mask(mask)
    assert result['enclosed_negative_space_count'] == 0
    assert result['negative_space_review']['regions'] == []
