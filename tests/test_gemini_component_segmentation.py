import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

from knowledge_engine import run_gemini_component_segmentation
from modeling_core import extract_reference_evidence, import_component_region_proposal


def _evidence(tmp_path: Path):
    image = np.full((100, 100, 3), 245, dtype=np.uint8)
    image[20:80, 20:80] = (45, 50, 60)
    source = tmp_path / "fixture.png"
    cv2.imwrite(str(source), image)
    return extract_reference_evidence(source, tmp_path / "evidence")


def _edge_evidence(tmp_path: Path):
    image = np.full((100, 100, 3), 245, dtype=np.uint8)
    image[20:80, 20:50] = (35, 40, 50)
    image[20:80, 50:80] = (150, 155, 165)
    source = tmp_path / "edge-fixture.png"
    cv2.imwrite(str(source), image)
    return extract_reference_evidence(source, tmp_path / "edge-evidence")


def _analysis(*, incomplete=False):
    right_start = 700 if incomplete else 500
    return {
        "components": [
            {
                "label": "head",
                "role": "PRIMARY_VOLUME",
                "box_2d": [200, 200, 800, 500],
                "mask_polygon": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]],
                "confidence": 0.93,
                "evidence": "A visible vertical seam separates the left shell.",
            },
            {
                "label": "handle",
                "role": "ATTACHED_ASSEMBLY",
                "box_2d": [200, right_start, 800, 800],
                "mask_polygon": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]],
                "confidence": 0.9,
                "evidence": "A visible attachment boundary separates the right shell.",
            },
        ],
        "limitations": ["The fixture has no depth evidence."],
    }


def _generate(analysis):
    def generate(**_kwargs):
        return SimpleNamespace(text=json.dumps(analysis))
    return generate


def test_gemini_polygons_are_audited_and_emit_secret_free_adapter_artifacts(tmp_path: Path):
    result = run_gemini_component_segmentation(
        _evidence(tmp_path),
        tmp_path / "gemini",
        generate=_generate(_analysis()),
    )
    assert result["ready_for_external_adapter"] is True
    assert result["raw_coverage"] >= 0.99
    assert result["raw_overlap"] < 0.03
    assert result["model"] == "gemini-3.8-flash"
    assert "api" not in json.dumps(result).lower()
    labels = cv2.imread(result["artifacts"]["label_map"], cv2.IMREAD_GRAYSCALE)
    assert set(np.unique(labels)) == {0, 1, 2}
    provider = json.loads(Path(result["artifacts"]["provider_report"]).read_text(encoding="utf-8"))
    assert provider["provider"] == "Google Gemini"
    assert provider["model_version"] == "blender-component-segmentation-v3-box-local"
    assert set(provider["region_confidence"]) == {"1", "2"}
    assert provider["region_semantic_proposals"]["1"]["label"] == "head"
    assert provider["segmentation_gate_pass"] is True
    assert provider["final_quality_factor"] >= provider["raw_quality_factor"]
    assert result["request_image"]["request_image_size"] == [100, 100]
    assert result["artifact_sha256"]["request_image"] == provider["request_image"]["request_image_sha256"]


def test_gemini_upload_is_bounded_and_normalized_without_changing_aspect(tmp_path: Path):
    evidence = _evidence(tmp_path)
    source = Path(evidence["source"]["path"])
    large = np.full((1000, 2000, 3), 65535, dtype=np.uint16)
    large[200:800, 400:1600] = (9000, 11000, 13000)
    assert cv2.imwrite(str(source), large)
    evidence = extract_reference_evidence(source, tmp_path / "large-evidence")

    result = run_gemini_component_segmentation(
        evidence,
        tmp_path / "large-gemini",
        generate=_generate(_analysis()),
        request_maximum_dimension=1000,
    )

    assert result["request_image"]["source_image_size"] == [2000, 1000]
    assert result["request_image"]["request_image_size"] == [1000, 500]
    assert result["request_image"]["source_dtype"] == "uint16"
    request_image = cv2.imread(result["artifacts"]["request_image"], cv2.IMREAD_UNCHANGED)
    assert request_image.dtype == np.uint8


def test_saved_response_can_be_hash_bound_and_reaudited(tmp_path: Path):
    replay = tmp_path / "saved-response.json"
    replay.write_text(json.dumps(_analysis()), encoding="utf-8")

    result = run_gemini_component_segmentation(
        _evidence(tmp_path), tmp_path / "replayed", response_replay=replay
    )

    assert result["response_acquisition"]["mode"] == "HASH_BOUND_RESPONSE_REPLAY"
    assert result["response_acquisition"]["replay_source_sha256"] == hashlib.sha256(replay.read_bytes()).hexdigest()


def test_gemini_incomplete_polygons_fail_adapter_gate(tmp_path: Path):
    result = run_gemini_component_segmentation(
        _evidence(tmp_path),
        tmp_path / "incomplete",
        generate=_generate(_analysis(incomplete=True)),
    )
    assert result["ready_for_external_adapter"] is False
    assert result["raw_coverage"] < 0.92
    assert any("covered only" in warning for warning in result["warnings"])
    assert any("weak image-edge support" in issue for issue in result["issues"])
    assert result["watershed_refinement_applied"] is True
    assert result["interior_edge_mean"] < 1.0


def test_gemini_duplicate_component_labels_are_rejected(tmp_path: Path):
    analysis = _analysis()
    analysis["components"][1]["label"] = "HEAD"
    try:
        run_gemini_component_segmentation(
            _evidence(tmp_path),
            tmp_path / "duplicate",
            generate=_generate(analysis),
        )
    except ValueError as error:
        assert "labels must be unique" in str(error)
    else:
        raise AssertionError("duplicate Gemini component labels were accepted")


def test_box_local_polygon_is_mapped_through_documented_full_image_box(tmp_path: Path):
    analysis = {"components": [{
        "label": "boxed host",
        "role": "PRIMARY_VOLUME",
        "box_2d": [200, 300, 800, 700],
        "mask_polygon": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]],
        "confidence": 0.95,
        "evidence": "The visible object fills the declared component box.",
    }], "limitations": []}
    image = np.full((100, 100, 3), 245, dtype=np.uint8)
    image[20:80, 30:70] = (40, 45, 50)
    source = tmp_path / "boxed.png"
    assert cv2.imwrite(str(source), image)
    evidence = extract_reference_evidence(source, tmp_path / "boxed-evidence")

    result = run_gemini_component_segmentation(
        evidence, tmp_path / "boxed-gemini", generate=_generate(analysis)
    )

    assert result["polygon_coordinate_conventions"] == ["XY_BOX_LOCAL_TO_FULL_IMAGE"]
    diagnostics = result["polygon_coordinate_diagnostics"][0]
    assert diagnostics["verified_object_precision"] > 0.95
    labels = cv2.imread(result["artifacts"]["label_map"], cv2.IMREAD_GRAYSCALE)
    assert labels[50, 50] == 1
    assert labels[50, 20] == 0


def test_gemini_semantic_seeds_refine_to_supported_complete_partition(tmp_path: Path):
    analysis = _analysis()
    analysis["components"][0]["box_2d"] = [200, 200, 800, 550]
    analysis["components"][0]["mask_polygon"] = [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]
    analysis["components"][1]["box_2d"] = [200, 450, 800, 770]
    analysis["components"][1]["mask_polygon"] = [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]
    result = run_gemini_component_segmentation(
        _edge_evidence(tmp_path),
        tmp_path / "refined",
        generate=_generate(analysis),
    )
    assert result["bounded_nearest_fill_applied"] is True
    assert result["raw_overlap"] > result["visible_overlap_after_role_resolution"]
    assert result["ready_for_external_adapter"] is True
    labels = cv2.imread(result["artifacts"]["label_map"], cv2.IMREAD_GRAYSCALE)
    source_mask = cv2.imread(str(tmp_path / "edge-evidence" / "reference_mask.png"), cv2.IMREAD_GRAYSCALE) >= 128
    assert np.all(labels[source_mask] > 0)
    proposal = import_component_region_proposal(
        tmp_path / "edge-evidence" / "reference_evidence.json",
        result["artifacts"]["label_map"],
        result["artifacts"]["provider_report"],
        tmp_path / "imported",
    )
    assert proposal["proposal_status"] == "REVIEWABLE_PROPOSAL"
    assert proposal["accepted_as_semantic_evidence"] is False


def test_overlap_between_peer_visible_assemblies_is_not_hidden_by_role_resolution(tmp_path: Path):
    analysis = _analysis()
    analysis["components"][0]["role"] = "ATTACHED_ASSEMBLY"
    analysis["components"][0]["box_2d"] = [200, 200, 800, 650]
    analysis["components"][1]["box_2d"] = [200, 350, 800, 800]
    result = run_gemini_component_segmentation(
        _edge_evidence(tmp_path),
        tmp_path / "peer-overlap",
        generate=_generate(analysis),
    )
    assert result["raw_overlap"] == result["visible_overlap_after_role_resolution"]
    assert result["ready_for_external_adapter"] is False
    assert any("overlap after role-aware" in issue for issue in result["issues"])
