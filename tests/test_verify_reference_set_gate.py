import json

from tools.verify_reference_set_gate import audit_manifest


def test_manifest_audit_reports_failure_instead_of_crashing(tmp_path):
    manifest = tmp_path / "reference_manifest.json"
    manifest.write_text(json.dumps({
        "target_id": "prop", "target_variant": "v1",
        "required_views": ["front"], "critical_properties": [],
        "items": [{
            "reference_id": "front", "source_id": "source", "target_id": "prop",
            "target_variant": "v1", "purposes": ["PRIMARY_FORM"], "view": "front",
            "projection": "PERSPECTIVE", "source_tier": "HIGH",
        }],
    }))
    report = audit_manifest(manifest)
    assert report["pass"] is False
    assert "source_url or local_file" in report["error"]
