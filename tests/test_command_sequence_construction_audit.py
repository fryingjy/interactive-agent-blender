from tools.audit_command_sequence_construction import audit_sequence


def test_primitive_only_primary_form_fails_closed():
    result = audit_sequence(
        [{"command": "create_primitive", "params": {"name": "Body", "primitive_type": "cube"}}],
        ["Body"],
    )
    assert result["pass"] is False
    assert "no committed topology edit" in result["failures"][0]


def test_committed_topology_edit_promotes_primitive_starting_cage():
    result = audit_sequence(
        [
            {"command": "create_primitive", "params": {"name": "Body", "primitive_type": "cube"}},
            {"transaction": {"name": "Body", "operation": "loop_cut_selection", "accept": True}},
        ],
        ["Body"],
    )
    assert result["pass"] is True
    assert result["primary_forms"][0]["topology_operations"] == ["loop_cut_selection"]


def test_rejected_edit_and_shading_do_not_promote_form():
    result = audit_sequence(
        [
            {"command": "create_primitive", "params": {"name": "Body", "primitive_type": "cube"}},
            {"transaction": {"name": "Body", "operation": "bevel_selection", "accept": False}},
            {"transaction": {"name": "Body", "operation": "set_smooth_by_angle", "accept": True}},
        ],
        ["Body"],
    )
    assert result["pass"] is False


def test_connected_revolved_profile_is_valid_authored_starting_cage():
    result = audit_sequence(
        [{"command": "create_revolved_profile", "params": {"name": "Shell"}}], ["Shell"]
    )
    assert result["pass"] is True


def test_connected_profile_extrusion_is_valid_authored_starting_cage():
    result = audit_sequence(
        [{"command": "create_profile_extrusion", "params": {"name": "Shell"}}], ["Shell"]
    )
    assert result["pass"] is True


def test_connected_profile_loft_is_valid_authored_starting_cage():
    result = audit_sequence(
        [{"command": "create_profile_loft", "params": {"name": "Shell"}}], ["Shell"]
    )
    assert result["pass"] is True


def test_connected_quad_shell_grid_is_valid_authored_starting_cage():
    result = audit_sequence(
        [{"command": "create_quad_shell_grid", "params": {"name": "Shell"}}], ["Shell"]
    )
    assert result["pass"] is True


def test_connected_quad_shell_sections_is_valid_authored_starting_cage():
    result = audit_sequence(
        [{"command": "create_quad_shell_sections", "params": {"name": "Shell"}}], ["Shell"]
    )
    assert result["pass"] is True


def test_connected_quad_open_surface_is_valid_authored_starting_cage():
    result = audit_sequence(
        [{"command": "create_quad_open_surface", "params": {"name": "Shell"}}], ["Shell"]
    )
    assert result["pass"] is True


def test_connected_quad_annular_shell_is_valid_authored_starting_cage():
    result = audit_sequence(
        [{"command": "create_quad_annular_shell", "params": {"name": "Shell"}}], ["Shell"]
    )
    assert result["pass"] is True


def test_connected_layered_quad_annular_shell_is_valid_authored_starting_cage():
    result = audit_sequence(
        [{"command": "create_quad_layered_annular_shell", "params": {"name": "Shell"}}], ["Shell"]
    )
    assert result["pass"] is True


def test_connected_authored_quad_mesh_is_valid_starting_cage():
    result = audit_sequence(
        [{"command": "create_authored_quad_mesh", "params": {"name": "TerminationPatch"}}],
        ["TerminationPatch"],
    )
    assert result["pass"] is True


def test_connected_quad_radial_surface_is_valid_starting_cage():
    result = audit_sequence(
        [{"command": "create_quad_radial_surface", "params": {"name": "CurvedHost"}}],
        ["CurvedHost"],
    )
    assert result["pass"] is True
