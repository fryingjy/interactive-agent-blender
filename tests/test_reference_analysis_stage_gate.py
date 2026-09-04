from blender_ops.stage_gates import evaluate_stage_gate


def _base_evidence():
    reference_audit = {
        "schema_version": 1, "record_type": "REFERENCE_SET_AUDIT",
        "target_id": "prop", "target_variant": "v1",
        "reference_count": 2, "matching_reference_count": 2,
        "checks": {
            "same_target_identity_pass": True, "view_coverage_pass": True,
            "orthographic_coverage_pass": True, "provenance_coverage_pass": True,
            "critical_property_coverage_pass": True, "dimensional_anchor_pass": True,
            "conflicts_resolved_pass": True, "question_driven_research_pass": True,
            "artifact_binding_pass": True,
        },
        "issues": [], "pass": True, "disposition": "READY_TO_MODEL",
        "authorized_reference_sha256": ["a" * 64, "c" * 64],
    }
    return {
        "shape_pipeline_evidence": {
            "schema_version": 1, "record_type": "MULTIVIEW_REFERENCE_EVIDENCE_BUNDLE",
            "target_id": "prop", "target_variant": "v1",
            "views": [
                {"view_id": "front", "source_sha256": "a" * 64, "mask_sha256": "b" * 64, "issues": []},
                {"view_id": "side", "source_sha256": "c" * 64, "mask_sha256": "d" * 64, "issues": []},
            ],
            "missing_component_support": {}, "issues": [], "accepted_for_shape_solving": True,
        },
        "modeling_spec_audit": {
            "schema_version": 1, "record_type": "REFERENCE_MODELING_SPEC_AUDIT",
            "target_id": "prop", "target_variant": "v1", "component_ids": ["body"],
            "identity_feature_ids": ["outer_arc"], "authorized_reference_sha256": ["a" * 64],
            "errors": [], "pass": True,
        },
        "reference_audit": reference_audit,
    }


def test_structured_reference_and_shape_pipeline_evidence_passes():
    assert evaluate_stage_gate("REFERENCE_ANALYSIS", _base_evidence())["pass"] is True


def test_missing_shape_pipeline_evidence_blocks_advance():
    evidence = _base_evidence()
    del evidence["shape_pipeline_evidence"]
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "shape_pipeline_evidence" in result["missing"]


def test_self_asserted_shape_pipeline_flag_is_rejected():
    evidence = _base_evidence()
    evidence["shape_pipeline_evidence"] = True
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "shape_pipeline_evidence is missing, malformed, or not accepted" in result["failures"][0]


def test_rejected_or_cross_target_shape_bundle_blocks_advance():
    evidence = _base_evidence()
    evidence["shape_pipeline_evidence"]["target_id"] = "other_prop"
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "shape pipeline evidence targets a different asset or variant" in result["failures"]
    evidence = _base_evidence()
    evidence["shape_pipeline_evidence"]["accepted_for_shape_solving"] = False
    assert evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)["pass"] is False


def test_missing_modeling_spec_blocks_reference_authorization():
    evidence = _base_evidence()
    del evidence["modeling_spec_audit"]
    result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
    assert result["pass"] is False
    assert "modeling_spec_audit" in result["missing"]


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
