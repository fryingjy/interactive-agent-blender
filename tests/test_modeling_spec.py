from knowledge_engine.modeling_spec import validate_reference_modeling_spec


HASH = "a" * 64


def valid_spec():
    return {
        "record_type": "REFERENCE_MODELING_SPEC",
        "target": {
            "target_id": "prop", "target_variant": "v1", "complexity": "MODERATE",
            "authorized_reference_sha256": [HASH],
        },
        "components": [{
            "id": "body", "role": "PRIMARY", "continuity_policy": "CONTINUOUS",
            "high_salience": True, "representation": "SUBD_CAGE",
            "construction_justification": "One continuous molded housing.",
            "evidence_sha256": [HASH], "depth_critical": True,
            "reversible_until_multiview_pass": True,
        }],
        "identity_features": [{
            "id": "outer_arc", "component_id": "body", "salience": "HIGH",
            "description": "The upper silhouette forms one shallow asymmetric arc.",
            "evidence_sha256": HASH,
            "measurement": {"type": "SILHOUETTE", "tolerance": 0.03},
        }],
        "passes": [{
            "stage": stage,
            "criteria": [{"feature_id": "outer_arc", "observable": "Arc error is within tolerance.", "channel": "VISUAL"}],
        } for stage in ("REFERENCE_ANALYSIS", "PRIMARY_BLOCKOUT", "PROPORTION_SILHOUETTE")],
        "repair_policy": {"max_attempts_per_region_stage": 3, "stagnation_limit": 2},
    }


def test_valid_spec_passes_without_object_count_quota():
    result = validate_reference_modeling_spec(valid_spec())
    assert result["pass"] is True
    assert result["component_ids"] == ["body"]
    assert result["authorized_reference_sha256"] == [HASH]


def test_primary_component_needs_measured_identity_feature():
    spec = valid_spec()
    spec["identity_features"][0]["salience"] = "LOW"
    result = validate_reference_modeling_spec(spec)
    assert result["pass"] is False
    assert any("lack HIGH identity" in error for error in result["errors"])


def test_unresolved_high_salience_continuity_blocks():
    spec = valid_spec()
    spec["components"][0]["continuity_policy"] = "UNRESOLVED"
    assert validate_reference_modeling_spec(spec)["pass"] is False


def test_depth_critical_component_must_remain_reversible():
    spec = valid_spec()
    spec["components"][0]["reversible_until_multiview_pass"] = False
    assert validate_reference_modeling_spec(spec)["pass"] is False


def test_repair_budget_cannot_be_silently_expanded():
    spec = valid_spec()
    spec["repair_policy"]["max_attempts_per_region_stage"] = 99
    assert validate_reference_modeling_spec(spec)["pass"] is False


def test_non_hex_reference_fingerprint_is_rejected():
    spec = valid_spec()
    spec["target"]["authorized_reference_sha256"] = ["z" * 64]
    assert validate_reference_modeling_spec(spec)["pass"] is False
