from blender_ops.stage_gates import evaluate_stage_gate


def _base_evidence():
    return {
        "component_graph_pass": True,
        "measured_ratio_count": 3,
        "uncertainty_recorded": True,
        "reference_set_audit_pass": True,
        "same_target_identity_pass": True,
        "view_coverage_pass": True,
        "critical_property_coverage_pass": True,
        "conflicts_resolved_pass": True,
        "question_driven_research_pass": True,
        "visual_reconstruction_audit_pass": {"record_type": "VISUAL_RECONSTRUCTION_AUDIT", "pass": True},
        "component_reference_coverage_pass": {"pass": True, "uncovered_component_ids": []},
    }


def test_full_evidence_including_new_keys_passes():
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", _base_evidence())
    assert result["pass"] is True


def test_missing_visual_reconstruction_audit_key_blocks_advance():
    evidence = _base_evidence()
    del evidence["visual_reconstruction_audit_pass"]
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "visual_reconstruction_audit_pass" in result["missing"]


def test_self_asserted_true_does_not_satisfy_visual_reconstruction_audit():
    # A bare True is exactly the "self-reported flag" this gate must refuse --
    # only the real structured audit_visual_reconstruction() result counts.
    evidence = _base_evidence()
    evidence["visual_reconstruction_audit_pass"] = True
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "visual reconstruction audit missing, invalid, or not passing" in result["failures"]


def test_failing_visual_reconstruction_audit_blocks_advance():
    evidence = _base_evidence()
    evidence["visual_reconstruction_audit_pass"] = {"record_type": "VISUAL_RECONSTRUCTION_AUDIT", "pass": False}
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "visual reconstruction audit missing, invalid, or not passing" in result["failures"]


def test_uncovered_component_blocks_advance():
    evidence = _base_evidence()
    evidence["component_reference_coverage_pass"] = {"pass": False, "uncovered_component_ids": ["handle"]}
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "reference evidence does not cover every declared component" in result["failures"]


def test_self_asserted_true_does_not_satisfy_component_reference_coverage():
    evidence = _base_evidence()
    evidence["component_reference_coverage_pass"] = True
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "reference evidence does not cover every declared component" in result["failures"]
