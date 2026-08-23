import unittest

from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.reference_analysis import (
    PropertyClaim,
    ReferenceResearchQuestion,
    ResearchCandidate,
    ReferenceConflict,
    ReferenceItem,
    ReferenceSet,
    audit_reference_set,
    build_reference_stage_evidence,
    reference_set_from_dict,
    validate_component_reference_coverage,
)


def item(reference_id, source_id, *, target="nailsea", variant="30.5cm", view="front",
         projection="PERSPECTIVE", purposes=("PRIMARY_FORM",), claims=(), anchors=(),
         component_ids=()):
    return ReferenceItem(
        reference_id=reference_id, source_id=source_id, target_id=target,
        target_variant=variant, purposes=purposes, view=view, projection=projection,
        source_tier="USEFUL_VERIFY", claims=claims, dimensional_anchors=anchors,
        component_ids=component_ids,
    )


class ReferenceAnalysisTests(unittest.TestCase):
    def test_open_high_impact_question_blocks_modeling_and_emits_exact_query(self):
        question = ReferenceResearchQuestion(
            question_id="rear-construction",
            property_id="rear_mount",
            question="How is the rear mount attached?",
            trigger="The target photograph occludes the rear face.",
            impact="HIGH",
            search_queries=("prop v1 rear mount teardown",),
            candidates=(),
        )
        audit = audit_reference_set(ReferenceSet(
            target_id="prop", target_variant="v1",
            items=(item("front", "source", target="prop", variant="v1"),),
            required_views=("front",), critical_properties=(),
            research_questions=(question,),
        ))
        self.assertFalse(audit["checks"]["question_driven_research_pass"])
        self.assertEqual(audit["disposition"], "TARGETED_RESEARCH")
        self.assertIn("prop v1 rear mount teardown", audit["targeted_research_queries"])

    def test_deferred_low_impact_question_requires_reversible_constraint(self):
        candidate = ResearchCandidate(
            candidate_id="different-variant",
            source_url="https://example.com/vintage",
            source_id="vintage-listing",
            observed_identity="prop",
            observed_variant="vintage",
            purpose="DETAIL",
            disposition="REJECTED",
            reason="Different variant cannot authorize target geometry.",
        )
        question = ReferenceResearchQuestion(
            question_id="underside-stamp",
            property_id="underside_stamp",
            question="What stamp is on the underside?",
            trigger="No supplied view exposes the base.",
            impact="LOW",
            search_queries=("prop v1 underside stamp",),
            candidates=(candidate,),
            status="DEFERRED",
            resolution="No matching evidence found.",
            modeling_constraint="Keep the underside unmarked and separately editable.",
        )
        audit = audit_reference_set(ReferenceSet(
            target_id="prop", target_variant="v1",
            items=(item("front", "source", target="prop", variant="v1"),),
            required_views=("front",), critical_properties=(),
            research_questions=(question,),
        ))
        self.assertTrue(audit["checks"]["question_driven_research_pass"])
        self.assertIn(
            "Keep the underside unmarked and separately editable.",
            audit["research_audit"]["modeling_constraints"],
        )

    def test_resolved_question_requires_accepted_reference_link(self):
        payload = {
            "target_id": "prop", "target_variant": "v1",
            "required_views": ["front"], "critical_properties": [],
            "items": [{
                "reference_id": "front", "source_id": "source", "target_id": "prop",
                "target_variant": "v1", "purposes": ["PRIMARY_FORM"], "view": "front",
                "projection": "PERSPECTIVE", "source_tier": "USEFUL_VERIFY",
            }],
            "research_questions": [{
                "question_id": "dimensions", "property_id": "width",
                "question": "What is the width?", "trigger": "No scale anchor.", "impact": "HIGH",
                "search_queries": ["prop v1 official width"], "status": "RESOLVED",
                "resolution": "Official page supplies width.", "candidates": [{
                    "candidate_id": "official", "source_url": "https://example.com/official",
                    "source_id": "official", "observed_identity": "prop",
                    "observed_variant": "v1", "purpose": "DIMENSION", "disposition": "ACCEPTED",
                    "reason": "Manufacturer specification.", "accepted_reference_id": "missing-item",
                }],
            }],
        }
        audit = audit_reference_set(reference_set_from_dict(payload))
        self.assertFalse(audit["checks"]["question_driven_research_pass"])
        self.assertIn("dimensions:missing-item", audit["research_audit"]["missing_reference_links"])

    def test_resolved_question_accepts_linked_reference_and_counts_rejection(self):
        accepted = ResearchCandidate(
            candidate_id="official", source_url="https://example.com/official",
            source_id="official", observed_identity="prop", observed_variant="v1",
            purpose="DIMENSION", disposition="ACCEPTED", reason="Manufacturer specification.",
            accepted_reference_id="front",
        )
        rejected = ResearchCandidate(
            candidate_id="retailer", source_url="https://example.com/retailer",
            source_id="retailer", observed_identity="prop", observed_variant="unknown",
            purpose="DIMENSION", disposition="REJECTED", reason="Variant is not established.",
        )
        question = ReferenceResearchQuestion(
            question_id="dimensions", property_id="width", question="What is the width?",
            trigger="No scale anchor.", impact="HIGH", search_queries=("prop v1 official width",),
            candidates=(accepted, rejected), status="RESOLVED",
            resolution="Use the manufacturer specification.",
        )
        audit = audit_reference_set(ReferenceSet(
            target_id="prop", target_variant="v1",
            items=(item("front", "source", target="prop", variant="v1"),),
            required_views=("front",), critical_properties=(), research_questions=(question,),
        ))
        self.assertTrue(audit["checks"]["question_driven_research_pass"])
        self.assertEqual(audit["research_audit"]["candidate_counts"]["REJECTED"], 1)

    def test_five_views_from_one_listing_are_not_five_independent_sources(self):
        refs = tuple(item(f"photo-{view}", "listing-1", view=view) for view in ("front", "side", "rear", "top", "bottom"))
        audit = audit_reference_set(ReferenceSet(
            target_id="nailsea", target_variant="30.5cm", items=refs,
            required_views=("front", "side", "top", "bottom"), critical_properties=(),
            minimum_independent_sources=2,
        ))
        self.assertEqual(audit["view_count"], 5)
        self.assertEqual(audit["independent_source_count"], 1)
        self.assertFalse(audit["checks"]["provenance_coverage_pass"])

    def test_mixed_variant_and_inspiration_claims_fail(self):
        refs = (
            item("photo-a", "listing-1", claims=(PropertyClaim("rim_profile", "PRIMARY_FORM", "flared"),)),
            item("concept", "artist-1", variant="fantasy", purposes=("INSPIRATION",),
                 claims=(PropertyClaim("base_diameter", "INSPIRATION", "9 cm"),)),
        )
        audit = audit_reference_set(ReferenceSet(
            target_id="nailsea", target_variant="30.5cm", items=refs,
            required_views=("front",), critical_properties=("rim_profile", "base_diameter"),
        ))
        self.assertFalse(audit["checks"]["same_target_identity_pass"])
        self.assertFalse(audit["checks"]["critical_property_coverage_pass"])

    def test_perspective_photo_cannot_satisfy_orthographic_requirement(self):
        audit = audit_reference_set(ReferenceSet(
            target_id="prop", target_variant="v1", items=(item("front", "source", target="prop", variant="v1"),),
            required_views=("front",), orthographic_required_views=("front",), critical_properties=(),
        ))
        self.assertFalse(audit["checks"]["orthographic_coverage_pass"])

    def test_unscoped_number_is_not_a_dimensional_anchor(self):
        audit = audit_reference_set(ReferenceSet(
            target_id="prop", target_variant="v1",
            items=(item("front", "source", target="prop", variant="v1", anchors=("height 20 cm",)),),
            required_views=("front",), critical_properties=(), require_dimensional_anchor=True,
        ))
        self.assertFalse(audit["checks"]["dimensional_anchor_pass"])

    def test_unresolved_conflict_forces_targeted_research(self):
        refs = (item("a", "source-a", claims=(PropertyClaim("base_diameter", "DIMENSION", "9 cm"),),
                     purposes=("DIMENSION",), anchors=("overall width 9 cm",)),)
        audit = audit_reference_set(ReferenceSet(
            target_id="nailsea", target_variant="30.5cm", items=refs,
            required_views=("front",), critical_properties=("base_diameter",),
            conflicts=(ReferenceConflict("base_diameter", ("a", "b"), "9 cm versus 8 cm"),),
        ))
        self.assertEqual(audit["disposition"], "TARGETED_RESEARCH")
        self.assertTrue(any("base diameter specification" in query for query in audit["targeted_research_queries"]))

    def test_complete_same_target_set_passes_without_promising_model_accuracy(self):
        refs = (
            item("front", "listing", view="front", claims=(
                PropertyClaim("outer_silhouette", "PRIMARY_FORM", "documented front contour"),
                PropertyClaim("rim_profile", "DETAIL", "rolled flared lip"),
            ), purposes=("PRIMARY_FORM", "DETAIL", "DIMENSION"), anchors=("overall height 30.5 cm", "maximum width 9 cm")),
            item("side", "listing", view="side", claims=(PropertyClaim("depth_profile", "PRIMARY_FORM", "documented side contour"),)),
            item("top", "listing", view="top", claims=(PropertyClaim("hollow_opening", "CONSTRUCTION", "open mouth"),), purposes=("CONSTRUCTION",)),
            item("bottom", "listing", view="bottom"),
        )
        audit = audit_reference_set(ReferenceSet(
            target_id="nailsea", target_variant="30.5cm", items=refs,
            required_views=("front", "side", "top", "bottom"),
            critical_properties=("outer_silhouette", "depth_profile", "rim_profile", "hollow_opening"),
            require_dimensional_anchor=True,
        ))
        self.assertTrue(audit["pass"])
        self.assertEqual(audit["disposition"], "READY_TO_MODEL")

    def test_planner_researches_instead_of_opening_blender_on_weak_references(self):
        decision = plan_next_decision(PlannerContext(
            task_id="task", asset_id="asset", stage="REFERENCE_ANALYSIS",
            session_id="session", scene_revision=0,
            stage_evidence={"targeted_research_queries": ["prop side view"]},
        ))
        self.assertEqual(decision.disposition, "RESEARCH")
        self.assertEqual(decision.action, "TARGETED_REFERENCE_RESEARCH")
        self.assertIsNone(decision.operation)

    def test_reference_gate_preempts_a_geometry_ticket(self):
        decision = plan_next_decision(PlannerContext(
            task_id="task", asset_id="asset", stage="REFERENCE_ANALYSIS",
            session_id="session", scene_revision=0,
            visual_tickets=[{
                "type": "missing_component", "target": "handle", "priority": 1,
                "severity": 1.0, "suggested_operation": "create_primitive",
            }],
        ))
        self.assertEqual(decision.action, "TARGETED_REFERENCE_RESEARCH")
        self.assertIsNone(decision.operation)

    def test_reference_gate_preempts_technical_geometry_repair(self):
        decision = plan_next_decision(PlannerContext(
            task_id="task", asset_id="asset", stage="REFERENCE_ANALYSIS",
            session_id="session", scene_revision=0, active_object="stale-blockout",
            evaluated_state={"mesh_health": {"non_manifold_edges": 12}},
        ))
        self.assertEqual(decision.action, "TARGETED_REFERENCE_RESEARCH")
        self.assertIsNone(decision.operation)

    def test_reference_stage_advances_only_with_full_evidence(self):
        evidence = {
            "component_graph_pass": True, "measured_ratio_count": 3,
            "uncertainty_recorded": True, "reference_set_audit_pass": True,
            "same_target_identity_pass": True, "view_coverage_pass": True,
            "critical_property_coverage_pass": True, "conflicts_resolved_pass": True,
            "question_driven_research_pass": True,
            "visual_reconstruction_audit_pass": {"record_type": "VISUAL_RECONSTRUCTION_AUDIT", "pass": True},
            "component_reference_coverage_pass": {"pass": True, "uncovered_component_ids": []},
        }
        decision = plan_next_decision(PlannerContext(
            task_id="task", asset_id="asset", stage="REFERENCE_ANALYSIS",
            session_id="session", scene_revision=0, stage_evidence=evidence,
        ))
        self.assertEqual(decision.next_stage, "PRIMARY_BLOCKOUT")

    def test_audit_maps_to_stage_evidence_without_manual_claims(self):
        audit = audit_reference_set(ReferenceSet(
            target_id="prop", target_variant="v1",
            items=(item("front", "source", target="prop", variant="v1"),),
            required_views=("front",), critical_properties=(),
        ))
        evidence = build_reference_stage_evidence(
            audit, component_graph_pass=True, measured_ratio_count=2,
            uncertainty_recorded=True,
        )
        self.assertTrue(evidence["reference_set_audit_pass"])
        self.assertTrue(evidence["question_driven_research_pass"])
        self.assertEqual(evidence["reference_audit"]["target_id"], "prop")

    def test_low_confidence_claim_cannot_authorize_a_critical_property(self):
        weak = item(
            "front", "source", target="prop", variant="v1",
            claims=(PropertyClaim("outer_silhouette", "PRIMARY_FORM", "uncertain contour", "LOW"),),
        )
        audit = audit_reference_set(ReferenceSet(
            target_id="prop", target_variant="v1", items=(weak,),
            required_views=("front",), critical_properties=("outer_silhouette",),
        ))
        self.assertFalse(audit["checks"]["critical_property_coverage_pass"])
        self.assertIn("front:outer_silhouette", " ".join(audit["issues"]))

    def test_resolved_conflict_requires_a_recorded_resolution(self):
        with self.assertRaisesRegex(ValueError, "recorded resolution"):
            audit_reference_set(ReferenceSet(
                target_id="prop", target_variant="v1",
                items=(item("front", "source", target="prop", variant="v1"),),
                required_views=("front",), critical_properties=(),
                conflicts=(ReferenceConflict(
                    "depth", ("front",), "two estimates", status="RESOLVED"
                ),),
            ))

    def test_component_reference_coverage_passes_when_every_component_is_covered(self):
        components = [{"id": "body"}, {"id": "handle"}]
        items = (
            item("front", "source", target="prop", variant="v1", component_ids=("body",)),
            item(
                "detail", "source", target="prop", variant="v1",
                claims=(PropertyClaim("handle_diameter", "DIMENSION", "measured off scale bar", "HIGH",
                                       component_id="handle"),),
            ),
        )
        result = validate_component_reference_coverage(components, items)
        self.assertTrue(result["pass"])
        self.assertEqual(result["uncovered_component_ids"], [])
        self.assertEqual(result["covered_component_ids"], ["body", "handle"])

    def test_component_reference_coverage_fails_on_uncovered_component(self):
        components = [{"id": "body"}, {"id": "handle"}, {"id": "foot"}]
        items = (item("front", "source", target="prop", variant="v1", component_ids=("body", "handle")),)
        result = validate_component_reference_coverage(components, items)
        self.assertFalse(result["pass"])
        self.assertEqual(result["uncovered_component_ids"], ["foot"])
        self.assertEqual(result["component_count"], 3)

    def test_component_reference_coverage_ignores_components_without_declared_ids(self):
        components = [{"id": "body"}, {"name": "no id field"}]
        items = (item("front", "source", target="prop", variant="v1", component_ids=("body",)),)
        result = validate_component_reference_coverage(components, items)
        self.assertTrue(result["pass"])
        self.assertEqual(result["component_count"], 1)


if __name__ == "__main__":
    unittest.main()
