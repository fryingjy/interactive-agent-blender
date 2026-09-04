from blender_ops.stage_gates import evaluate_stage_gate


def _base_evidence():
    return {
        "fitted_shape_evidence": {
            "schema_version": 1,
            "record_type": "SHAPE_FAMILY_SELECTION",
            "pass": True,
            "candidates": [{"candidate_id": "a"}, {"candidate_id": "b"}],
            "selected_result": {
                "record_type": "FITTED_SHAPE_HYPOTHESIS",
                "family_compatible": True,
                "compatibility_issues": [],
                "per_view": {"front": {"loss": 0.02}, "side": {"loss": 0.04}},
            },
        },
        "render_evidence_preflight": {"record_type": "MULTIVIEW_RENDER_EVIDENCE_PREFLIGHT", "pass": True, "blank_views": [], "duplicate_view_groups": []},
        "visual_mismatch_ledger": [
            {"view_id": "front", "status": "accepted", "salience": "high", "observation": "outer contour and dial opening reviewed"},
            {"view_id": "side", "status": "accepted", "salience": "high", "observation": "body depth and attachment order reviewed"},
        ],
    }


def test_high_salience_unresolved_visual_mismatch_blocks_advance():
    evidence = _base_evidence()
    evidence["visual_mismatch_ledger"][1]["status"] = "repair"
    result = evaluate_stage_gate("PROPORTION_SILHOUETTE", evidence)
    assert result["pass"] is False
    assert "an unresolved high-salience visual mismatch blocks proportion advance" in result["failures"]


def test_every_declared_view_requires_a_written_review():
    evidence = _base_evidence()
    evidence["visual_mismatch_ledger"].pop()
    result = evaluate_stage_gate("PROPORTION_SILHOUETTE", evidence)
    assert result["pass"] is False
    assert "visual_mismatch_ledger is missing declared views: side" in result["failures"]


def test_bare_or_single_candidate_fit_evidence_is_rejected():
    evidence = _base_evidence()
    evidence["fitted_shape_evidence"] = True
    assert evaluate_stage_gate("PROPORTION_SILHOUETTE", evidence)["pass"] is False
    evidence = _base_evidence()
    evidence["fitted_shape_evidence"]["candidates"].pop()
    assert evaluate_stage_gate("PROPORTION_SILHOUETTE", evidence)["pass"] is False
