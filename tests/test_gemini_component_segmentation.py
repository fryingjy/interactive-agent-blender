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
                "mask_polygon": [[200, 200], [500, 200], [500, 800], [200, 800]],
                "confidence": 0.93,
                "evidence": "A visible vertical seam separates the left shell.",
            },
            {
                "label": "handle",
                "role": "ATTACHED_ASSEMBLY",
                "box_2d": [200, right_start, 800, 800],
                "mask_polygon": [[right_start, 200], [800, 200], [800, 800], [right_start, 800]],
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
    assert result["model"] == "gemini-3.7-flash"
    assert "api" not in json.dumps(result).lower()
    labels = cv2.imread(result["artifacts"]["label_map"], cv2.IMREAD_GRAYSCALE)
    assert set(np.unique(labels)) == {0, 1, 2}
    provider = json.loads(Path(result["artifacts"]["provider_report"]).read_text(encoding="utf-8"))
    assert provider["provider"] == "Google Gemini"
    assert provider["model_version"] == "blender-component-segmentation-v1"
    assert set(provider["region_confidence"]) == {"1", "2"}


def test_gemini_incomplete_polygons_fail_adapter_gate(tmp_path: Path):
    result = run_gemini_component_segmentation(
        _evidence(tmp_path),
        tmp_path / "incomplete",
        generate=_generate(_analysis(incomplete=True)),
    )
    assert result["ready_for_external_adapter"] is False
    assert result["raw_coverage"] < 0.92
    assert any("cover only" in issue for issue in result["issues"])


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


def test_gemini_semantic_seeds_refine_to_supported_complete_partition(tmp_path: Path):
    analysis = _analysis()
    analysis["components"][0]["box_2d"] = [200, 200, 800, 550]
    analysis["components"][0]["mask_polygon"] = [[200, 200], [550, 200], [550, 800], [200, 800]]
    analysis["components"][1]["box_2d"] = [200, 450, 800, 770]
    analysis["components"][1]["mask_polygon"] = [[450, 200], [770, 200], [770, 800], [450, 800]]
    result = run_gemini_component_segmentation(
        _edge_evidence(tmp_path),
        tmp_path / "refined",
        generate=_generate(analysis),
    )
    assert result["watershed_refinement_applied"] is True
    assert result["boundary_edge_support_ratio"] >= 0.7
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
