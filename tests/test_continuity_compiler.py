import pytest

from modeling_core import build_continuous_cage


def _loft(start, end, *, segments=12, width=0.4):
    return {
        "family": "section_loft",
        "segments": segments,
        "cross_section": "box",
        "scale_x": 1.0,
        "scale_y": 1.0,
        "scale_z": 1.0,
        "translate_x": 0.0,
        "translate_y": 0.0,
        "translate_z": 0.0,
        "stations": [
            {"z": start, "half_width": width, "half_depth": 0.25, "power": 4.0},
            {"z": end, "half_width": width, "half_depth": 0.25, "power": 4.0},
        ],
    }


def _relationship(first="a", second="b"):
    return {
        "pair_id": "::".join(sorted((first, second))),
        "components": [first, second],
        "construction_policy": "CONTINUOUS_MESH",
    }


def _interface(first_port="end", second_port="start", *, maximum=0.5, weld=1e-5):
    return {
        "ports": {"a": first_port, "b": second_port},
        "maximum_bridge_span": maximum,
        "weld_tolerance": weld,
    }


def test_coincident_equal_cardinality_ports_weld_into_one_quad_cage():
    result = build_continuous_cage(
        {"a": _loft(-1.0, 0.0), "b": _loft(0.0, 1.0)},
        [_relationship()],
        {"a::b": _interface()},
    )
    assert result["stats"] == {
        "vertices": 36,
        "faces": 24,
        "boundary_edges": 24,
        "manifold_edges": 36,
    }
    assert result["interfaces"][0]["mode"] == "WELD"
    assert all(len(face) == 4 for face in result["faces"])


def test_separated_equal_cardinality_ports_bridge_with_quads():
    result = build_continuous_cage(
        {"a": _loft(-1.0, 0.0), "b": _loft(0.2, 1.0)},
        [_relationship()],
        {"a::b": _interface(maximum=0.25)},
    )
    assert result["stats"]["vertices"] == 48
    assert result["stats"]["faces"] == 36
    assert result["stats"]["boundary_edges"] == 24
    assert result["interfaces"][0]["mode"] == "BRIDGE"
    assert result["interfaces"][0]["maximum_span"] == pytest.approx(0.2)


def test_mismatched_port_cardinality_fails_closed():
    with pytest.raises(ValueError, match="equal vertex counts"):
        build_continuous_cage(
            {"a": _loft(-1.0, 0.0), "b": _loft(0.1, 1.0, segments=16)},
            [_relationship()],
            {"a::b": _interface(maximum=0.2)},
        )


def test_bridge_span_must_stay_inside_measured_bound():
    with pytest.raises(ValueError, match="exceeds measured bound"):
        build_continuous_cage(
            {"a": _loft(-1.0, 0.0), "b": _loft(0.3, 1.0)},
            [_relationship()],
            {"a::b": _interface(maximum=0.1)},
        )


def test_a_boundary_port_cannot_be_reused_by_two_connections():
    relationships = [_relationship("a", "b"), _relationship("b", "c")]
    interfaces = {
        "a::b": _interface(),
        "b::c": {
            "ports": {"b": "start", "c": "start"},
            "maximum_bridge_span": 1.1,
        },
    }
    with pytest.raises(ValueError, match="is reused"):
        build_continuous_cage(
            {"a": _loft(-1.0, 0.0), "b": _loft(0.0, 1.0), "c": _loft(0.0, 1.0)},
            relationships,
            interfaces,
        )


def test_interface_records_must_exactly_match_relationships():
    with pytest.raises(ValueError, match="exactly match"):
        build_continuous_cage(
            {"a": _loft(-1.0, 0.0), "b": _loft(0.0, 1.0)},
            [_relationship()],
            {},
        )


@pytest.mark.parametrize("invalid_span", [0.0, -0.1, float("nan"), float("inf")])
def test_bridge_bound_must_be_positive_and_finite(invalid_span):
    with pytest.raises(ValueError, match="positive measured bound"):
        build_continuous_cage(
            {"a": _loft(-1.0, 0.0), "b": _loft(0.1, 1.0)},
            [_relationship()],
            {"a::b": _interface(maximum=invalid_span)},
        )


def test_weld_tolerance_must_be_finite_and_nonnegative():
    with pytest.raises(ValueError, match="finite nonnegative"):
        build_continuous_cage(
            {"a": _loft(-1.0, 0.0), "b": _loft(0.1, 1.0)},
            [_relationship()],
            {"a::b": _interface(weld=float("nan"))},
        )
