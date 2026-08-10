from knowledge_engine.surface_cause_classifier import SurfaceCauseEvidence, classify_surface_cause


def test_classifies_each_controlled_cause():
    cases = {
        "GEOMETRY": SurfaceCauseEvidence(
            base_geometry_changed=True,
            evaluated_geometry_changed=True,
            silhouette_or_depth_changed=True,
        ),
        "NORMALS": SurfaceCauseEvidence(
            face_orientation_or_split_normals_changed=True,
            normal_repair_neutralizes=True,
        ),
        "MATERIAL": SurfaceCauseEvidence(
            material_state_changed=True,
            neutral_material_neutralizes=True,
        ),
        "LIGHTING": SurfaceCauseEvidence(
            lighting_state_changed=True,
            neutral_lighting_neutralizes=True,
        ),
        "BEVEL_PROFILE": SurfaceCauseEvidence(
            evaluated_geometry_changed=True,
            bevel_parameters_changed=True,
            bevel_repair_neutralizes=True,
        ),
    }
    assert {name: classify_surface_cause(case).cause for name, case in cases.items()} == {
        name: name for name in cases
    }


def test_conflicting_and_unresolved_are_not_overclaimed():
    conflicting = SurfaceCauseEvidence(
        base_geometry_changed=True,
        evaluated_geometry_changed=True,
        silhouette_or_depth_changed=True,
        bevel_parameters_changed=True,
        bevel_repair_neutralizes=True,
    )
    assert classify_surface_cause(conflicting).cause == "CONFLICTING"
    assert classify_surface_cause(SurfaceCauseEvidence()).cause == "UNRESOLVED"
