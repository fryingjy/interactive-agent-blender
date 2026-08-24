from types import SimpleNamespace

from knowledge_engine.gemini_reference_critic import analyze_reference_candidate
from knowledge_engine.stage_checkpoint import build_visual_stage_checkpoint
from tests.test_gemini_reference_critic import valid_analysis


def _record(manifest):
    return analyze_reference_candidate(
        manifest,
        model="test-model",
        generate=lambda **_kwargs: SimpleNamespace(text=__import__("json").dumps(valid_analysis())),
    )


def test_checkpoint_preserves_one_dominant_focus_and_artifact_binding(tmp_path):
    from PIL import Image
    from knowledge_engine.gemini_reference_critic import load_critic_manifest
    import json

    Image.new("RGB", (8, 8), "red").save(tmp_path / "reference.png")
    Image.new("RGB", (8, 8), "blue").save(tmp_path / "candidate.png")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "target_id": "test_prop", "component_ids": ["body"],
        "views": [{"view": "front", "reference": "reference.png", "candidate": "candidate.png"}],
    }))
    manifest = load_critic_manifest(tmp_path / "manifest.json")
    record = _record(manifest)
    checkpoint = build_visual_stage_checkpoint(
        record,
        target_id="test_prop",
        stage="PRIMARY_BLOCKOUT",
        scene_revision=4,
        candidate_views={"front": manifest["views"][0]["candidate_sha256"]},
        authorized_reference_hashes={manifest["views"][0]["reference_sha256"]},
        recent_decisions=[],
    )
    assert checkpoint["decision"] == "CORRECT_ONE_DOMINANT_MISMATCH"
    assert checkpoint["correction_focus"]["component_id"] == "body"
    assert checkpoint["parallel_repairs_allowed"] is False
    assert checkpoint["pass"] is False


def test_checkpoint_changes_strategy_after_stagnation(tmp_path):
    from PIL import Image
    from knowledge_engine.gemini_reference_critic import load_critic_manifest
    import json

    Image.new("RGB", (8, 8), "red").save(tmp_path / "reference.png")
    Image.new("RGB", (8, 8), "blue").save(tmp_path / "candidate.png")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "target_id": "test_prop", "component_ids": ["body"],
        "views": [{"view": "front", "reference": "reference.png", "candidate": "candidate.png"}],
    }))
    manifest = load_critic_manifest(tmp_path / "manifest.json")
    attempts = [
        {"stage": "PRIMARY_BLOCKOUT", "target_region": "body", "status": "committed", "before_score": 0.5, "after_score": 0.505},
        {"stage": "PRIMARY_BLOCKOUT", "target_region": "body", "status": "committed", "before_score": 0.505, "after_score": 0.506},
    ]
    checkpoint = build_visual_stage_checkpoint(
        _record(manifest), target_id="test_prop", stage="PRIMARY_BLOCKOUT", scene_revision=5,
        candidate_views={"front": manifest["views"][0]["candidate_sha256"]},
        authorized_reference_hashes={manifest["views"][0]["reference_sha256"]},
        recent_decisions=attempts,
    )
    assert checkpoint["decision"] == "CHANGE_STRATEGY"


def test_checkpoint_rejects_replayed_candidate_hash(tmp_path):
    from PIL import Image
    from knowledge_engine.gemini_reference_critic import load_critic_manifest
    import json
    import pytest

    Image.new("RGB", (8, 8), "red").save(tmp_path / "reference.png")
    Image.new("RGB", (8, 8), "blue").save(tmp_path / "candidate.png")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "target_id": "test_prop", "component_ids": ["body"],
        "views": [{"view": "front", "reference": "reference.png", "candidate": "candidate.png"}],
    }))
    manifest = load_critic_manifest(tmp_path / "manifest.json")
    with pytest.raises(ValueError, match="candidate views"):
        build_visual_stage_checkpoint(
            _record(manifest), target_id="test_prop", stage="PRIMARY_BLOCKOUT", scene_revision=5,
            candidate_views={"front": "0" * 64},
            authorized_reference_hashes={manifest["views"][0]["reference_sha256"]},
            recent_decisions=[],
        )
