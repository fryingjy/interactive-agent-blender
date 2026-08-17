from blender_ops.stage_gates import evaluate_stage_gate


def _base_evidence():
    return {
        "view_count": 2,
        "worst_view_iou": 0.95,
        "multiview_regression_pass": True,
        "render_evidence_preflight": {"record_type": "MULTIVIEW_RENDER_EVIDENCE_PREFLIGHT", "pass": True, "blank_views": [], "duplicate_view_groups": []},
        "declared_view_ids": ["front", "side"],
        "constraint_report": {
            "record_type": "LOCAL_REFERENCE_CONSTRAINT_EVALUATION",
            "pass": True,
            "blocking_constraint_ids": [],
        },
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
