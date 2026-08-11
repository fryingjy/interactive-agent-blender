from knowledge_engine.surface_cause_classifier import (
    SurfaceCauseAblation,
    SurfaceCauseEvidence,
    classify_surface_cause,
    diagnose_mixed_surface_causes,
)


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


def test_mixed_cause_ablation_confirms_multiple_independent_repairs():
    causes = ("GEOMETRY", "NORMALS", "MATERIAL", "LIGHTING", "BEVEL_PROFILE")
    evidence = tuple(
        SurfaceCauseAblation(cause, True, True, True, 0.20, 0.15 - index * 0.01, 1000, 700 - index * 50)
        for index, cause in enumerate(causes)
    )
    diagnosis = diagnose_mixed_surface_causes(evidence)
    assert diagnosis.status == "MULTI_CAUSE_CONFIRMED"
    assert set(diagnosis.causes) == set(causes)
    assert diagnosis.rejected == ()


def test_mixed_cause_ablation_rejects_collateral_reset_and_weak_change():
    evidence = (
        SurfaceCauseAblation("GEOMETRY", True, True, False, 0.20, 0.01, 1000, 10),
        SurfaceCauseAblation("MATERIAL", True, True, True, 0.20, 0.199, 1000, 995),
    )
    diagnosis = diagnose_mixed_surface_causes(evidence)
    assert diagnosis.status == "UNRESOLVED"
    assert set(diagnosis.rejected) == {"GEOMETRY", "MATERIAL"}
