import copy

from modeling_core import (
    build_component_refit_tickets,
    build_section_loft,
    mask_diagnostics,
    render_silhouette,
)


def _hypothesis(translate_x):
    return {
        "schema_version": 1,
        "candidate_id": "offset-loft",
        "shape": {
            "family": "section_loft",
            "segments": 12,
            "cross_section": "box",
            "scale_x": 1.0,
            "scale_y": 1.0,
            "scale_z": 1.0,
            "translate_x": translate_x,
            "translate_y": 0.0,
            "translate_z": 0.0,
            "stations": [
                {"z": -0.7, "half_width": 0.3, "half_depth": 0.2, "power": 4.0},
                {"z": 0.7, "half_width": 0.3, "half_depth": 0.2, "power": 4.0},
            ],
        },
        "views": [{
            "id": "front",
            "projection": "orthographic",
            "image_size": [96, 96],
            "yaw_degrees": 0.0,
            "pitch_degrees": 0.0,
            "roll_degrees": 0.0,
            "world_scale": 2.4,
            "offset_x": 0.0,
            "offset_y": 0.0,
        }],
        "variables": [{"pointer": "/shape/translate_x", "bounds": [-0.5, 0.5]}],
        "acceptance": {
            "max_mean_view_loss": 0.2,
            "max_each_view_loss": 0.3,
            "require_hole_count_match": True,
        },
    }


def _render(hypothesis):
    vertices, faces = build_section_loft(hypothesis["shape"])
    return render_silhouette(vertices, faces, hypothesis["views"][0])


def test_refit_ticket_identifies_a_bounded_parameter_direction_without_mean_regression():
    retained = _hypothesis(-0.2)
    reference = _render(_hypothesis(0.0))
    diagnostics = mask_diagnostics(reference, _render(retained))
    fitted = {
        "record_type": "FITTED_SHAPE_HYPOTHESIS",
        "hypothesis": retained,
        "per_view": {"front": diagnostics},
    }
    tickets = build_component_refit_tickets(
        "body",
        fitted,
        {"front": reference},
        minimum_view_loss=0.0,
        probe_fraction=0.2,
    )
    residual = next(ticket for ticket in tickets if ticket["type"] == "component_view_residual")
    assert residual["target"] == "body"
    assert residual["view_id"] == "front"
    assert residual["root_cause"] == "DECLARED_PARAMETER_MISMATCH"
    assert residual["operation_params"]["parameter_pointer"] == "/shape/translate_x"
    assert residual["operation_params"]["probe_direction"] == "INCREASE"
    assert residual["operation_params"]["requires_multiview_refit"] is True


def test_negative_space_mismatch_requests_representation_change_not_fake_parameter_repair():
    retained = _hypothesis(0.0)
    reference = _render(retained)
    reference_with_hole = copy.deepcopy(reference)
    reference_with_hole[45:51, 45:51] = False
    diagnostics = mask_diagnostics(reference_with_hole, reference)
    fitted = {
        "record_type": "FITTED_SHAPE_HYPOTHESIS",
        "hypothesis": retained,
        "per_view": {"front": diagnostics},
    }
    tickets = build_component_refit_tickets("guard", fitted, {"front": reference_with_hole})
    topology = next(ticket for ticket in tickets if ticket["type"] == "component_negative_space_failure")
    assert topology["root_cause"] == "REPRESENTATION_FAILURE"
    assert topology["repair_scope"] == "CHANGE_FAMILY_OR_COMPONENT_GRAPH"
    assert topology["recommended_action"] == "CHANGE_REPRESENTATION"


def test_stale_residual_record_cannot_drive_a_refit_ticket():
    retained = _hypothesis(0.0)
    reference = _render(retained)
    diagnostics = mask_diagnostics(reference, reference)
    diagnostics["loss"] = 0.4
    fitted = {
        "record_type": "FITTED_SHAPE_HYPOTHESIS",
        "hypothesis": retained,
        "per_view": {"front": diagnostics},
    }
    try:
        build_component_refit_tickets("body", fitted, {"front": reference})
    except ValueError as error:
        assert "residual record is stale" in str(error)
    else:
        raise AssertionError("stale fit diagnostics were allowed to create repair instructions")
