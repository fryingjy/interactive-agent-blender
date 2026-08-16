from knowledge_engine.component_layout import compare_component_layout


def test_component_layout_reports_localized_mismatch_without_global_pass_claim():
    report = compare_component_layout(
        {"body": {"left": 0.0, "top": 0.1, "right": 1.0, "bottom": 1.0}, "dial": {"left": 0.2, "top": 0.2, "right": 0.8, "bottom": 0.8}},
        {"body": {"left": 0.0, "top": 0.1, "right": 1.0, "bottom": 1.0}, "dial": {"left": 0.25, "top": 0.2, "right": 0.85, "bottom": 0.8}},
    )
    assert report["missing_components"] == []
    assert report["components"]["body"]["severity"] == 0.0
    assert report["tickets"][0]["target"] == "dial"
    assert report["tickets"][0]["type"] == "component_layout"


def test_component_layout_fails_closed_on_missing_component():
    report = compare_component_layout(
        {"body": {"left": 0.0, "top": 0.0, "right": 1.0, "bottom": 1.0}},
        {},
    )
    assert report["missing_components"] == ["body"]
    assert report["tickets"][0]["type"] == "missing_component"
