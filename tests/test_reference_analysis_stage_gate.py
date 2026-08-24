from blender_ops.stage_gates import evaluate_stage_gate


def _base_evidence():
    reference_audit = {
        "schema_version": 1,
        "record_type": "REFERENCE_SET_AUDIT",
        "target_id": "prop",
        "target_variant": "v1",
        "reference_count": 2,
        "matching_reference_count": 2,
        "checks": {
            "same_target_identity_pass": True,
            "view_coverage_pass": True,
            "orthographic_coverage_pass": True,
            "provenance_coverage_pass": True,
            "critical_property_coverage_pass": True,
            "dimensional_anchor_pass": True,
            "conflicts_resolved_pass": True,
            "question_driven_research_pass": True,
            "artifact_binding_pass": True,
        },
        "issues": [],
        "pass": True,
        "disposition": "READY_TO_MODEL",
        "authorized_reference_sha256": ["a" * 64],
    }
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
        "visual_reconstruction_audit_pass": {
            "schema_version": 1,
            "record_type": "VISUAL_RECONSTRUCTION_AUDIT",
            "target_id": "prop",
            "checks": {
                "identity_bound": True,
                "independent_observations": True,
                "property_specific_authority": True,
                "eleven_passes_recorded": True,
                "competing_interpretations_tested": True,
                "bad_interpretation_eliminated": True,
                "construction_bound_to_selected_interpretation": True,
                "uncertainty_kept_reversible": True,
                "every_component_has_construction_justification": True,
            },
            "region_reports": [{"region_id": "body"}],
            "selected_hypothesis_ids": ["box"],
            "contradiction_count": 1,
            "errors": [],
            "pass": True,
        },
        "component_reference_coverage_pass": {
            "schema_version": 1,
            "record_type": "COMPONENT_REFERENCE_COVERAGE",
            "component_count": 1,
            "covered_component_ids": ["body"],
            "uncovered_component_ids": [],
            "pass": True,
        },
        "depth_critical_reference_support_pass": {"schema_version": 1, "record_type": "DEPTH_CRITICAL_REFERENCE_SUPPORT", "depth_critical_component_ids": [], "component_reports": {}, "unsupported_component_ids": [], "pass": True},
        "modeling_spec_audit": {
            "schema_version": 1,
            "record_type": "REFERENCE_MODELING_SPEC_AUDIT",
            "target_id": "prop",
            "target_variant": "v1",
            "component_ids": ["body"],
            "identity_feature_ids": ["outer_arc"],
            "authorized_reference_sha256": ["a" * 64],
            "errors": [],
            "pass": True,
        },
        "reference_audit": reference_audit,
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


def test_front_only_depth_critical_component_blocks_advance():
    evidence = _base_evidence()
    evidence["depth_critical_reference_support_pass"] = {
        "record_type": "DEPTH_CRITICAL_REFERENCE_SUPPORT",
        "depth_critical_component_ids": ["head"],
        "component_reports": {"head": {"view_ids": ["front"], "reference_ids": ["front"], "view_count": 1, "pass": False}},
        "unsupported_component_ids": ["head"],
        "pass": False,
    }
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "depth-critical components lack multi-view structural evidence" in result["failures"]


def test_bare_true_does_not_satisfy_depth_support():
    evidence = _base_evidence()
    evidence["depth_critical_reference_support_pass"] = True
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False


def test_structured_depth_report_cannot_omit_declared_component_details():
    evidence = _base_evidence()
    evidence["depth_critical_reference_support_pass"] = {
        "record_type": "DEPTH_CRITICAL_REFERENCE_SUPPORT",
        "schema_version": 1,
        "depth_critical_component_ids": ["head"],
        "component_reports": {},
        "unsupported_component_ids": [],
        "pass": True,
    }
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False


def test_minimal_forged_structured_records_do_not_pass():
    evidence = _base_evidence()
    evidence["visual_reconstruction_audit_pass"] = {
        "schema_version": 1, "record_type": "VISUAL_RECONSTRUCTION_AUDIT", "pass": True
    }
    evidence["component_reference_coverage_pass"] = {
        "schema_version": 1, "record_type": "COMPONENT_REFERENCE_COVERAGE",
        "component_count": 0, "covered_component_ids": [], "uncovered_component_ids": [], "pass": True,
    }
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "visual reconstruction audit missing, invalid, or not passing" in result["failures"]
    assert "reference evidence does not cover every declared component" in result["failures"]


def test_flat_flags_cannot_contradict_reference_audit():
    evidence = _base_evidence()
    evidence["same_target_identity_pass"] = False
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "flattened reference flags contradict the structured reference_audit" in result["failures"]


def test_missing_modeling_spec_blocks_reference_authorization():
    evidence = _base_evidence()
    del evidence["modeling_spec_audit"]
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "modeling_spec_audit" in result["missing"]


def test_cross_target_visual_audit_cannot_be_replayed():
    evidence = _base_evidence()
    evidence["visual_reconstruction_audit_pass"]["target_id"] = "other_prop"
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "visual reconstruction audit targets a different asset" in result["failures"]


def test_cross_variant_modeling_spec_cannot_be_replayed():
    evidence = _base_evidence()
    evidence["modeling_spec_audit"]["target_variant"] = "other_variant"
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "modeling spec targets a different asset or variant" in result["failures"]


def test_modeling_spec_cannot_cite_unreviewed_reference_hash():
    evidence = _base_evidence()
    evidence["modeling_spec_audit"]["authorized_reference_sha256"] = ["b" * 64]
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "modeling spec cites reference artifacts outside the audited set" in result["failures"]


def test_non_hex_audit_fingerprint_is_rejected():
    evidence = _base_evidence()
    evidence["reference_audit"]["authorized_reference_sha256"] = ["z" * 64]
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "reference_audit is missing, malformed, or not ready to model" in result["failures"]
