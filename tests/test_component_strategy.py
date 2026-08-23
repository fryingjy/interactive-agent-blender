import unittest

from knowledge_engine.component_strategy import (
    ComponentStrategyEvidence,
    resolve_component_strategy,
)
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.strategy import ModelingBrief


def candidate(candidate_id, policy, front, top, *, objects, components):
    return ComponentStrategyEvidence(
        candidate_id=candidate_id,
        component_policy=policy,
        object_count=objects,
        connected_component_count=components,
        view_iou={"front": front, "top": top},
    )


class ComponentStrategyTests(unittest.TestCase):
    def setUp(self):
        self.continuous = candidate(
            "continuous", "CONTINUOUS_MESH", 1.0, 1.0, objects=1, components=1
        )
        self.separate = candidate(
            "front-plate", "SEPARATE_COMPONENTS", 1.0, 0.70, objects=2, components=2
        )

    def test_primary_tie_without_secondary_view_requires_research(self):
        resolution = resolve_component_strategy(
            [self.continuous, self.separate], primary_view="front", secondary_views=()
        )
        self.assertEqual(resolution["disposition"], "TARGETED_REFERENCE_RESEARCH")
        self.assertTrue(resolution["primary_ambiguous"])
        self.assertIsNone(resolution["chosen_policy"])

    def test_secondary_view_selects_continuous_strategy(self):
        resolution = resolve_component_strategy(
            [self.continuous, self.separate],
            primary_view="front",
            secondary_views=("top",),
            secondary_margin_min=0.15,
        )
        self.assertEqual(resolution["disposition"], "SELECT_STRATEGY")
        self.assertEqual(resolution["chosen_policy"], "CONTINUOUS_MESH")
        self.assertGreaterEqual(resolution["secondary_margin"], 0.15)

    def test_missing_secondary_candidate_evidence_fails_closed(self):
        incomplete = ComponentStrategyEvidence(
            "front-plate",
            "SEPARATE_COMPONENTS",
            2,
            2,
            {"front": 1.0},
        )
        resolution = resolve_component_strategy(
            [self.continuous, incomplete], primary_view="front", secondary_views=("top",)
        )
        self.assertEqual(resolution["disposition"], "TARGETED_REFERENCE_RESEARCH")
        self.assertEqual(resolution["missing_secondary_views"], {"front-plate": ["top"]})

    def test_policy_must_match_built_connectivity(self):
        invalid = ComponentStrategyEvidence(
            "joined-shells", "CONTINUOUS_MESH", 1, 2, {"front": 1.0, "top": 1.0}
        )
        with self.assertRaisesRegex(ValueError, "one connected component"):
            resolve_component_strategy(
                [invalid, self.separate], primary_view="front", secondary_views=("top",)
            )

    def test_planner_researches_before_reference_stage_advance(self):
        resolution = resolve_component_strategy(
            [self.continuous, self.separate], primary_view="front", secondary_views=()
        )
        decision = plan_next_decision(PlannerContext(
            task_id="secondary-view-test",
            asset_id="housing",
            stage="REFERENCE_ANALYSIS",
            session_id="test",
            scene_revision=1,
            stage_evidence={
                "component_graph_pass": True,
                "measured_ratio_count": 2,
                "uncertainty_recorded": True,
                "reference_set_audit_pass": True,
                "same_target_identity_pass": True,
                "view_coverage_pass": True,
                "critical_property_coverage_pass": True,
                "conflicts_resolved_pass": True,
                "question_driven_research_pass": True,
                "visual_reconstruction_audit_pass": {"record_type": "VISUAL_RECONSTRUCTION_AUDIT", "pass": True},
                "component_reference_coverage_pass": {"pass": True, "uncovered_component_ids": []},
            },
            component_strategy_resolution=resolution,
        ))
        self.assertEqual(decision.disposition, "RESEARCH")
        self.assertEqual(decision.action, "RESOLVE_SECONDARY_VIEW_STRATEGY")

    def test_measured_resolution_overrides_generic_component_prior(self):
        resolution = resolve_component_strategy(
            [self.continuous, self.separate],
            primary_view="front",
            secondary_views=("top",),
            secondary_margin_min=0.15,
        )
        decision = plan_next_decision(PlannerContext(
            task_id="secondary-view-test",
            asset_id="housing",
            stage="PROPORTION_SILHOUETTE",
            session_id="test",
            scene_revision=2,
            active_object="Housing",
            visual_tickets=[{
                "type": "missing_component",
                "target": "face-boundary",
                "priority": 1,
                "severity": 1.0,
            }],
            brief=ModelingBrief(independent_motion_or_material=True),
            component_strategy_resolution=resolution,
        ))
        self.assertEqual(decision.operation_params["component_policy"], "CONTINUOUS_MESH")
        self.assertEqual(decision.operation_params["component_strategy_candidate"], "continuous")


if __name__ == "__main__":
    unittest.main()
