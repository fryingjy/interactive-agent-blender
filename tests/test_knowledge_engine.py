import json
import tempfile
import unittest
from pathlib import Path

from knowledge_engine.ingest.document_ingest import crawl_local_documents, ingest_document
from knowledge_engine.ingest.transcript_ingest import parse_transcript
from knowledge_engine.ingest.speech_transcribe import write_webvtt
from knowledge_engine.reasoning import (
    Diagnosis,
    RegionRepairHistory,
    validate_component_graph,
    validate_multiview_metrics,
)
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore
from knowledge_engine.schemas import AccessRecord, SourceRecord
from knowledge_engine.scene_decomposition import (
    CLAIM_CATEGORIES,
    Component,
    ReferenceClaim,
    Relationship,
    SceneDecomposition,
    StrategyCandidate,
    scene_decomposition_from_dict,
)
from knowledge_engine.telemetry import SkillUsage, SkillUsageLog
from knowledge_engine.visual_compare import compare_component_masks, compare_landmarks, compare_masks, make_reference_tickets, negative_space_mask
from knowledge_engine.human_review import build_repair_record, review_to_repair_tickets, validate_external_visual_review
from knowledge_engine.strategy import ModelingBrief, choose_strategy
from knowledge_engine.quality_review import ReviewChannel, aggregate_professional_review, evaluate_stage_gate
from knowledge_engine.planner import PlannerContext, plan_next_decision
from knowledge_engine.session_learning import apply_replay_result, mine_session_events

import numpy as np


class SchemaTests(unittest.TestCase):
    def test_rejected_source_requires_reason(self):
        record = SourceRecord(
            id="bad",
            title="Unavailable",
            creator="unknown",
            source_type="video",
            trust_tier="D",
            version="n/a",
            topics=[],
            access=AccessRecord(),
            status="REJECTED",
            url="https://example.invalid",
        )
        with self.assertRaises(ValueError):
            record.to_dict()

    def test_repository_source_registry_is_normalized(self):
        registry = Path(__file__).resolve().parents[1] / "knowledge" / "foundation" / "source_registry.json"
        records = json.loads(registry.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(records), 1)
        for item in records:
            SourceRecord(**item).validate()


class DocumentIngestTests(unittest.TestCase):
    def test_approved_root_and_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            page = root / "manual.html"
            page.write_text(
                "<h1>Mirror</h1><h2>Options</h2><p>Parameter: Merge Distance.</p>"
                "<p>Warning: broad values can weld neighbors.</p><a href='/related'>Related</a>",
                encoding="utf-8",
            )
            result = ingest_document(
                page,
                approved_roots=[root],
                source_id="mirror",
                title="Mirror",
                creator="Blender",
                trust_tier="A",
                version="5.2",
                topics=["mirror"],
                canonical_url="https://docs.blender.org/manual/en/latest/mirror.html",
            )
            self.assertEqual(result.headings[1]["text"], "Options")
            self.assertIn("Parameter: Merge Distance.", result.operator_parameters)
            self.assertTrue(result.source.access.text)
            with self.assertRaises(PermissionError):
                ingest_document(
                    Path(temp).parent / "outside.md",
                    approved_roots=[root],
                    source_id="outside",
                    title="Outside",
                    creator="n/a",
                    trust_tier="D",
                    version="n/a",
                    topics=[],
                )

    def test_local_crawl_deduplicates_and_tracks_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.html").write_text("<h1>A</h1><a href='b.html'>B</a><a href='copy.html'>Copy</a>", encoding="utf-8")
            (root / "b.html").write_text("<h1>B</h1><p>Warning: test.</p>", encoding="utf-8")
            (root / "copy.html").write_text("<h1>B</h1><p>Warning: test.</p>", encoding="utf-8")
            result = crawl_local_documents([root / "a.html"], approved_roots=[root], creator="test", trust_tier="A", version="1", topics=["mesh"])
            self.assertTrue(result["completion"]["complete"])
            self.assertEqual(result["completion"]["unique_documents"], 2)
            self.assertIn("DUPLICATE_CONTENT", [item["reason"] for item in result["skipped"]])


class TranscriptTests(unittest.TestCase):
    def test_vtt_segments(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "lesson.vtt"
            path.write_text(
                "WEBVTT\n\n00:00:00.000 --> 00:00:01.500\nStep one: inspect the cage.\n\n"
                "00:00:01.500 --> 00:00:03.000\nCheck the evaluated surface.\n",
                encoding="utf-8",
            )
            segments = parse_transcript(path)
            self.assertEqual(len(segments), 2)
            self.assertEqual(segments[1]["start"], 1.5)

    def test_generated_vtt_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_webvtt([
                {"start": 0.0, "end": 1.234, "text": "Inspect the silhouette."},
                {"start": 61.5, "end": 63.0, "text": "Then inspect the surface."},
            ], Path(temp) / "generated.vtt")
            self.assertEqual(parse_transcript(path), [
                {"start": 0.0, "end": 1.234, "text": "Inspect the silhouette."},
                {"start": 61.5, "end": 63.0, "text": "Then inspect the surface."},
            ])


class RetrievalTests(unittest.TestCase):
    def test_question_driven_reference_unknown_retrieves_specific_skill(self):
        store = StructuredSkillStore(Path(__file__).resolve().parents[1] / "knowledge" / "skills")
        results = store.search(RetrievalContext(
            query="unknown boiler underside needs targeted evidence search and candidate rejection",
            modeling_stage="REFERENCE_ANALYSIS",
            workflow="question-driven evidence search",
            reference_issue="missing underside view and variant conflict",
        ))
        self.assertTrue(results)
        self.assertEqual(results[0]["skill_id"], "reference.question-driven-targeted-research")

    def test_structured_context_outranks_lexical_only_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "generic.json").write_text(json.dumps({
                "id": "generic",
                "title": "Mirror overview",
                "topic_tags": ["mirror"],
                "problem": "mirror",
                "symptom": "",
                "applicability": "general",
            }), encoding="utf-8")
            (root / "specific.json").write_text(json.dumps({
                "skill_id": "specific",
                "applicability": {
                    "workflow": "modifier-stack",
                    "defect": "non-manifold seam",
                    "modifiers_involved": ["MIRROR", "SUBSURF"],
                },
                "action_policy": ["test evaluated topology"],
                "runtime_usage": [{"success": True}],
                "status": "RUNTIME_VALIDATED",
            }), encoding="utf-8")
            results = StructuredSkillStore(root).search(RetrievalContext(
                query="mirror",
                workflow="modifier stack",
                defect="non manifold seam",
                modifiers=["mirror", "subsurf"],
            ))
            self.assertEqual(results[0]["skill_id"], "specific")
            self.assertGreater(results[0]["score_breakdown"]["defect"], 0)

    def test_weak_unrelated_overlap_abstains_by_default(self):
        store = StructuredSkillStore(Path(__file__).resolve().parents[1] / "knowledge" / "skills")
        cases = [
            RetrievalContext(
                query="camera focal length mismatch",
                workflow="reference modeling",
                defect="perspective distortion",
            ),
            RetrievalContext(
                query="UV islands overlap after pack",
                workflow="UV",
                defect="texel density",
            ),
            RetrievalContext(
                query="armature elbow collapses",
                workflow="rigging",
                defect="weight paint deformation",
            ),
        ]
        for context in cases:
            with self.subTest(query=context.query):
                self.assertEqual(store.search(context), [])

    def test_exploratory_search_can_lower_abstention_threshold(self):
        store = StructuredSkillStore(Path(__file__).resolve().parents[1] / "knowledge" / "skills")
        context = RetrievalContext(
            query="camera focal length mismatch",
            workflow="reference modeling",
            defect="perspective distortion",
        )
        self.assertNotEqual(store.search(context, min_score=0.0), [])
        with self.assertRaisesRegex(ValueError, "non-negative"):
            store.search(context, min_score=-0.1)

    def test_runtime_success_cannot_create_semantic_relevance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "weak.json").write_text(json.dumps({
                "skill_id": "weak",
                "title": "Reference candidate audit",
                "runtime_usage": [{"success": True}],
                "status": "RUNTIME_VALIDATED",
            }), encoding="utf-8")
            context = RetrievalContext(query="reference image color grade mismatch")
            self.assertEqual(StructuredSkillStore(root).search(context, min_score=4.0), [])

    def test_generic_workflow_cannot_create_relevance(self):
        store = StructuredSkillStore(Path(__file__).resolve().parents[1] / "knowledge" / "skills")
        context = RetrievalContext(
            query="reference image color grade mismatch",
            workflow="reference modeling",
            defect="white balance",
        )
        self.assertEqual(store.search(context), [])


class TelemetryTests(unittest.TestCase):
    def test_append_and_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            log = SkillUsageLog(Path(temp) / "usage.jsonl")
            log.append(SkillUsage(
                skill_id="s1",
                decision_id="d1",
                asset_id="a1",
                scene_revision_before=2,
                scene_revision_after=3,
                problem="open seam",
                action="raise threshold after measuring gap",
                success=True,
            ))
            self.assertEqual(log.summary("s1")["success_rate"], 1.0)
            with self.assertRaises(ValueError):
                log.append(SkillUsage("s1", "d2", "a1", 3, 3, "p", "a", False))


class ReasoningTests(unittest.TestCase):
    def test_uncertainty_and_rebuild(self):
        self.assertEqual(Diagnosis("pinch", 0.4, ["pole"]).next_action(), "INSPECT_OR_RESEARCH")
        decision = RegionRepairHistory("rim", 3, 0.8, 0.1, 1.0).decision()
        self.assertEqual(decision["decision"], "REBUILD_REGION")

    def test_multiview_and_component_graph(self):
        result = validate_multiview_metrics(
            {"front": 0.2, "side": 0.2, "top": 0.2},
            {"front": 0.1, "side": 0.3, "top": 0.2},
        )
        self.assertFalse(result["pass"])
        self.assertIn("side", result["regressions"])
        graph = validate_component_graph(
            [{"id": "body"}, {"id": "cap"}],
            [{"from": "cap", "to": "body", "type": "attached"}],
        )
        self.assertTrue(graph["pass"])


class SceneDecompositionTests(unittest.TestCase):
    def _wrench_decomposition(self):
        return SceneDecomposition(
            object_name="adjustable pipe wrench",
            components=[
                Component("handle", "primary", "structural"),
                Component("fixed_jaw", "primary", "structural"),
                Component("movable_jaw", "primary", "structural"),
                Component("adjustment_wheel", "secondary", "structural"),
            ],
            relationships=[
                Relationship("movable_jaw", "fixed_jaw", "slides_relative_to"),
                Relationship("adjustment_wheel", "movable_jaw", "interacts_with"),
                Relationship("handle", "fixed_jaw", "transitions_into"),
            ],
        )

    def _strict_lantern_decomposition(self, extra_claims=None):
        claims = [
            ReferenceClaim(
                "body-form",
                "primary_forms",
                "The main body is a broad tapered shell.",
                "OBSERVED",
                0.95,
                evidence=["front reference: outer contour narrows toward the top"],
                modeling_consequence="Start from a proportion-controlled box cage.",
                impact="high",
                component_refs=["body"],
            ),
            ReferenceClaim(
                "handle-path",
                "continuous_surfaces",
                "The handle follows one continuous arch.",
                "STRONGLY_INFERRED",
                0.8,
                evidence=["front reference: uninterrupted handle silhouette"],
                modeling_consequence="Use an editable curve for the handle blockout.",
                impact="high",
                component_refs=["handle"],
                modeling_signals={"follows_path": True},
            ),
            ReferenceClaim(
                "separate-handle",
                "separate_parts",
                "The handle is manufactured separately from the shell.",
                "STRONGLY_INFERRED",
                0.78,
                evidence=["front reference: visible pivot gaps at both handle ends"],
                modeling_consequence="Keep the handle independently editable.",
                impact="high",
                component_refs=["body", "handle"],
                modeling_signals={"independent_motion_or_material": True},
            ),
            ReferenceClaim(
                "construction",
                "construction_hypotheses",
                "A box-modeled shell plus a curve handle preserves the visible boundaries.",
                "STRONGLY_INFERRED",
                0.82,
                evidence=["body-form", "handle-path", "separate-handle"],
                modeling_consequence="Keep shell and handle as separate editable components.",
                impact="high",
                component_refs=["body", "handle"],
            ),
        ]
        claims.extend(extra_claims or [])
        return SceneDecomposition(
            object_name="stylized lantern",
            object_class="portable light",
            reference_style="concept",
            components=[
                Component(
                    "body", "primary", "structural", False,
                    evidence_status="OBSERVED", confidence=0.95,
                    evidence=["front reference: dominant enclosing silhouette"],
                ),
                Component(
                    "handle", "primary", "structural", True,
                    evidence_status="OBSERVED", confidence=0.9,
                    evidence=["front reference: handle is separated by two negative-space gaps"],
                ),
            ],
            relationships=[
                Relationship(
                    "handle", "body", "attached_to",
                    evidence_status="STRONGLY_INFERRED", confidence=0.8,
                    evidence=["front reference: handle endpoints meet side pivots"],
                ),
            ],
            claims=claims,
            strategies=[
                StrategyCandidate(
                    "shell-plus-curve-handle",
                    "BOX_MESH + CURVE",
                    ["body-form", "handle-path", "separate-handle", "construction"],
                ),
                StrategyCandidate(
                    "single-monolithic-shell",
                    "CONTINUOUS_MESH",
                    ["separate-handle"],
                    status="rejected",
                    rejection_reason="Would erase the observed pivot gaps and component boundary.",
                ),
            ],
            require_evidence_bindings=True,
        )

    def test_valid_decomposition_passes(self):
        decomp = self._wrench_decomposition()
        decomp.validate()  # must not raise
        self.assertEqual(
            {c.name for c in decomp.primary_components()},
            {"handle", "fixed_jaw", "movable_jaw"},
        )

    def test_empty_decomposition_rejected(self):
        with self.assertRaises(ValueError):
            SceneDecomposition(object_name="thing", components=[]).validate()

    def test_invalid_relationship_type_rejected(self):
        decomp = self._wrench_decomposition()
        decomp.relationships.append(Relationship("handle", "movable_jaw", "not_a_real_type"))
        with self.assertRaises(ValueError):
            decomp.validate()

    def test_dangling_relationship_rejected_via_shared_graph_validator(self):
        decomp = self._wrench_decomposition()
        decomp.relationships.append(Relationship("handle", "teeth", "interacts_with"))
        with self.assertRaises(ValueError):
            decomp.validate()

    def test_coverage_check_passes_real_per_component_build(self):
        decomp = self._wrench_decomposition()
        result = decomp.check_object_coverage(["Handle", "Fixed_Jaw", "Movable_Jaw", "Adjustment_Wheel"])
        self.assertTrue(result["coverage_ok"])
        self.assertEqual(result["unmatched_primary_components"], [])

    def test_coverage_check_catches_the_actual_wrench_failure(self):
        """The real regression this module exists for: a single collapsed
        object passes silhouette/topology checks but is not a decomposed
        model. See knowledge/foundation/operator_cards/visual_reference_comparison.md."""
        decomp = self._wrench_decomposition()
        result = decomp.check_object_coverage(["Wrench_Body"])
        self.assertFalse(result["coverage_ok"])
        self.assertEqual(
            set(result["unmatched_primary_components"]),
            {"handle", "fixed_jaw", "movable_jaw"},
        )

    def test_coverage_check_does_not_reuse_one_shell_for_two_primary_components(self):
        decomp = SceneDecomposition(
            object_name="moka pot",
            components=[
                Component("boiler_lower_shell", "primary", "structural"),
                Component("collector_upper_shell", "primary", "structural"),
            ],
        )
        result = decomp.check_object_coverage(["Collector_Upper_Shell"])
        self.assertFalse(result["coverage_ok"])
        self.assertEqual(result["unmatched_primary_components"], ["boiler_lower_shell"])
        self.assertEqual(result["component_matches"], {"collector_upper_shell": "Collector_Upper_Shell"})

    def test_coverage_check_matches_distinct_explicit_components_one_to_one(self):
        decomp = SceneDecomposition(
            object_name="moka pot",
            components=[
                Component("boiler_lower_shell", "primary", "structural"),
                Component("collector_upper_shell", "primary", "structural"),
            ],
        )
        result = decomp.check_object_coverage(["Boiler_Lower_Shell", "Collector_Upper_Shell"])
        self.assertTrue(result["coverage_ok"])
        self.assertEqual(
            result["component_matches"],
            {
                "boiler_lower_shell": "Boiler_Lower_Shell",
                "collector_upper_shell": "Collector_Upper_Shell",
            },
        )

    def test_coverage_check_matches_pascal_case_blender_object_names(self):
        decomp = SceneDecomposition(
            object_name="stage gate fixture",
            components=[Component("stage_gate_asset", "primary", "structural")],
        )
        result = decomp.check_object_coverage(["StageGateAsset"])
        self.assertTrue(result["coverage_ok"])
        self.assertEqual(result["component_matches"], {"stage_gate_asset": "StageGateAsset"})

    def test_component_layout_requires_measured_primary_placement_and_proportion(self):
        decomp = SceneDecomposition(
            object_name="two-part housing",
            components=[
                Component("body", "primary", "structural", expected_region={
                    "normalized_centroid": {"x": [0.2, 0.3], "y": [0.5, 0.5], "z": [0.5, 0.5]},
                    "normalized_size": {"x": [0.45, 0.55], "y": [1.0, 1.0], "z": [1.0, 1.0]},
                }),
                Component("handle", "primary", "structural", expected_region={
                    "normalized_centroid": {"x": [0.7, 0.8], "y": [0.5, 0.5], "z": [0.5, 0.5]},
                    "normalized_size": {"x": [0.45, 0.55], "y": [1.0, 1.0], "z": [1.0, 1.0]},
                }),
            ],
        )
        result = decomp.check_component_layout({
            "Body": {"min": [0.0, 0.0, 0.0], "max": [1.0, 2.0, 2.0]},
            "Handle": {"min": [1.0, 0.0, 0.0], "max": [2.0, 2.0, 2.0]},
        })
        self.assertTrue(result["layout_expectations_present"])
        self.assertTrue(result["layout_ok"])
        self.assertEqual(result["component_reports"]["body"]["object_name"], "Body")

        displaced = decomp.check_component_layout({
            "Body": {"min": [0.0, 0.0, 0.0], "max": [1.6, 2.0, 2.0]},
            "Handle": {"min": [1.6, 0.0, 0.0], "max": [2.0, 2.0, 2.0]},
        })
        self.assertFalse(displaced["layout_ok"])
        self.assertFalse(displaced["component_reports"]["body"]["proportion_ok"])

    def test_component_layout_stays_not_applicable_without_aligned_reference_regions(self):
        result = self._wrench_decomposition().check_component_layout({
            "Handle": {"min": [0, 0, 0], "max": [1, 1, 1]},
            "Fixed_Jaw": {"min": [1, 0, 0], "max": [2, 1, 1]},
            "Movable_Jaw": {"min": [2, 0, 0], "max": [3, 1, 1]},
        })
        self.assertFalse(result["layout_expectations_present"])
        self.assertIsNone(result["layout_ok"])

    def test_invalid_component_expected_region_is_rejected(self):
        decomp = SceneDecomposition(
            object_name="invalid board",
            components=[Component("body", "primary", expected_region={"normalized_centroid": {"x": [0, 1]}})],
        )
        with self.assertRaisesRegex(ValueError, "invalid expected region keys"):
            decomp.validate()

    def test_reference_to_blockout_contract_preserves_unknowns_and_selected_strategy(self):
        decomp = self._strict_lantern_decomposition(extra_claims=[
            ReferenceClaim(
                "unseen-base", "unknowns", "The underside is not visible.", "UNKNOWN", 0.1,
                impact="low", component_refs=["body"],
            ),
        ])
        contract = decomp.to_reference_to_blockout_contract(reference_set_id="lantern-board-v1")
        self.assertEqual(contract["record_type"], "REFERENCE_TO_BLOCKOUT_CONTRACT")
        self.assertEqual(contract["selected_strategy"]["name"], "shell-plus-curve-handle")
        self.assertEqual([claim["claim_id"] for claim in contract["unknown"]], ["unseen-base"])
        self.assertEqual([item["name"] for item in contract["primary_components"]], ["body", "handle"])

    def test_reference_to_blockout_contract_requires_explicit_choice_for_multiple_candidates(self):
        decomp = self._strict_lantern_decomposition()
        decomp.strategies.append(StrategyCandidate(
            "alternate-shell", "BOX_MESH", ["body-form"],
        ))
        with self.assertRaisesRegex(ValueError, "selected_strategy_name"):
            decomp.to_reference_to_blockout_contract(reference_set_id="lantern-board-v1")

    def test_observed_claim_requires_concrete_evidence(self):
        decomp = self._strict_lantern_decomposition()
        decomp.claims[0].evidence = []
        with self.assertRaisesRegex(ValueError, "requires concrete evidence"):
            decomp.validate()

    def test_strict_decomposition_requires_supported_primary_components(self):
        decomp = self._strict_lantern_decomposition()
        decomp.components[0].evidence_status = "UNKNOWN"
        decomp.components[0].confidence = 0.1
        decomp.components[0].evidence = []
        with self.assertRaisesRegex(ValueError, "evidence-bound primary components"):
            decomp.validate()

    def test_high_impact_unknown_blocks_blockout_and_becomes_research_question(self):
        decomp = self._strict_lantern_decomposition(extra_claims=[
            ReferenceClaim(
                "rear-depth",
                "depth_order",
                "Whether the rear housing projects beyond the body is unknown.",
                "UNKNOWN",
                0.1,
                impact="high",
                component_refs=["body"],
            ),
        ])
        readiness = decomp.blockout_readiness()
        self.assertFalse(readiness["ready_for_blockout"])
        self.assertEqual(readiness["high_impact_unresolved_claims"], ["rear-depth"])
        self.assertIn("rear housing", readiness["research_questions"][0])

    def test_structured_artifact_contains_every_directive_field(self):
        artifact = self._strict_lantern_decomposition().to_dict()
        required = {
            "target", "object_class", "reference_style", "camera_assumptions",
            "primary_forms", "secondary_forms", "tertiary_forms", "components",
            "relationships", "continuous_surfaces", "separate_parts", "negative_spaces",
            "landmarks", "symmetry", "repetition", "thickness_hypotheses", "depth_order",
            "material_boundaries", "construction_hypotheses", "known_dimensions",
            "estimated_dimensions", "unknowns", "ambiguities", "confidence_by_claim",
            "candidate_modeling_strategies", "rejected_strategies",
        }
        self.assertTrue(required.issubset(artifact))
        self.assertEqual(tuple(CLAIM_CATEGORIES), tuple(dict.fromkeys(CLAIM_CATEGORIES)))

    def test_canonical_artifact_round_trips_through_strict_loader(self):
        source = self._strict_lantern_decomposition()
        loaded = scene_decomposition_from_dict({
            **source.to_dict(),
            "require_evidence_bindings": True,
        })
        self.assertEqual(loaded.object_name, source.object_name)
        self.assertTrue(loaded.blockout_readiness()["ready_for_blockout"])

    def test_loader_rejects_legacy_unbound_primary_when_strict(self):
        with self.assertRaisesRegex(ValueError, "evidence-bound primary components"):
            scene_decomposition_from_dict({
                "target": "legacy prop",
                "require_evidence_bindings": True,
                "components": [{"name": "body", "role": "primary"}],
                "relationships": [],
                "claims": [{
                    "claim_id": "form", "category": "primary_forms", "statement": "body visible",
                    "evidence_status": "OBSERVED", "confidence": 0.9, "evidence": ["front"],
                    "modeling_consequence": "block out body",
                }],
                "strategies": [{
                    "name": "box", "representation": "BOX_MESH", "rationale_claim_ids": ["form"],
                }],
            })

    def test_only_supported_claims_change_modeling_strategy(self):
        decomp = self._strict_lantern_decomposition(extra_claims=[
            ReferenceClaim(
                "weak-counterclaim",
                "ambiguities",
                "The handle may be a rigid polygonal extrusion.",
                "WEAKLY_INFERRED",
                0.35,
                evidence=["single blurred crop"],
                modeling_consequence="Do not harden this guess.",
                modeling_signals={"follows_path": False},
            ),
        ])
        brief = decomp.to_modeling_brief(ModelingBrief(follows_path=False))
        self.assertTrue(brief.follows_path)
        self.assertTrue(brief.independent_motion_or_material)
        self.assertIn("handle-path", " ".join(brief.notes))

    def test_conflicting_supported_signals_block_strategy(self):
        decomp = self._strict_lantern_decomposition(extra_claims=[
            ReferenceClaim(
                "supported-counterclaim",
                "ambiguities",
                "A second clear view shows the handle does not follow a path.",
                "OBSERVED",
                0.9,
                evidence=["side reference: straight segmented handle profile"],
                modeling_consequence="Resolve the conflicting representation evidence.",
                modeling_signals={"follows_path": False},
            ),
        ])
        self.assertEqual(decomp.blockout_readiness()["conflicting_modeling_signals"], ["follows_path"])
        with self.assertRaisesRegex(ValueError, "conflicting evidence-bound modeling signal"):
            decomp.to_modeling_brief()


class VisualComparisonTests(unittest.TestCase):
    def test_identical_masks_are_exact(self):
        mask = np.zeros((64, 64), dtype=bool)
        mask[16:48, 20:44] = True
        result = compare_masks(mask, mask.copy())
        self.assertEqual(result["silhouette_iou"], 1.0)
        self.assertEqual(result["centroid_error_normalized"], 0.0)

    def test_shift_is_detected(self):
        reference = np.zeros((64, 64), dtype=bool)
        candidate = np.zeros((64, 64), dtype=bool)
        reference[16:48, 16:48] = True
        candidate[16:48, 20:52] = True
        result = compare_masks(reference, candidate)
        self.assertLess(result["silhouette_iou"], 1.0)
        self.assertGreater(result["centroid_error_normalized"], 0.0)
        self.assertGreater(result["symmetric_contour_error_normalized"], 0.0)

    def test_negative_space_landmarks_and_components(self):
        ring = np.ones((32, 32), dtype=bool)
        ring[8:24, 8:24] = False
        solid = np.ones((32, 32), dtype=bool)
        self.assertEqual(int(negative_space_mask(ring).sum()), 256)
        self.assertEqual(compare_masks(ring, solid)["negative_space_iou"], 0.0)
        landmarks = compare_landmarks({"port": (8, 8)}, {"port": (9, 8)}, (32, 32))
        self.assertGreater(landmarks["mean_error_normalized"], 0.0)
        components = compare_component_masks({"body": ring}, {"body": ring.copy()})
        self.assertEqual(components["mean_component_iou"], 1.0)
        tickets = make_reference_tickets(
            compare_masks(ring, solid),
            {"errors_normalized": {"port": 0.1}, "missing_landmarks": ["button"]},
            {"components": {}, "missing_components": ["handle"]},
            view="front",
        )
        self.assertEqual(tickets[0]["severity"], 1.0)
        self.assertEqual([item["priority"] for item in tickets], list(range(1, len(tickets) + 1)))


class QualityReviewTests(unittest.TestCase):
    def test_primary_blockout_requires_structured_one_to_one_component_coverage(self):
        base = {
            "dimensions_checked": True,
            "primary_components_present": True,
        }
        rejected = evaluate_stage_gate("PRIMARY_BLOCKOUT", base)
        self.assertFalse(rejected["pass"])
        self.assertIn("component_coverage", rejected["missing"])

        stale_or_collapsed = evaluate_stage_gate("PRIMARY_BLOCKOUT", {
            **base,
            "component_coverage": {
                "capture_type": "LIVE_MODELER_RUNTIME", "session_id": "test", "scene_revision": 0,
                "mesh_object_names": ["Collector_Upper_Shell"], "pass": False,
                "coverage": {"declared_primary_components": ["boiler_lower_shell", "collector_upper_shell"],
                    "built_object_names": ["Collector_Upper_Shell"],
                    "component_matches": {"collector_upper_shell": "Collector_Upper_Shell"},
                    "unmatched_primary_components": ["boiler_lower_shell"], "coverage_ok": False},
            },
        })
        self.assertFalse(stale_or_collapsed["pass"])
        self.assertIn("structured one-to-one component coverage is missing or invalid", stale_or_collapsed["failures"])

        accepted = evaluate_stage_gate("PRIMARY_BLOCKOUT", {
            **base,
            "component_coverage": {
                "capture_type": "LIVE_MODELER_RUNTIME", "session_id": "test", "scene_revision": 0,
                "mesh_object_names": ["Body", "Handle"], "pass": True,
                "coverage": {"declared_primary_components": ["body", "handle"],
                    "built_object_names": ["Body", "Handle"],
                    "component_matches": {"body": "Body", "handle": "Handle"},
                    "unmatched_primary_components": [], "coverage_ok": True},
            },
        })
        self.assertTrue(accepted["pass"])

    def test_primary_blockout_rejects_failed_required_component_layout(self):
        result = evaluate_stage_gate("PRIMARY_BLOCKOUT", {
            "dimensions_checked": True,
            "primary_components_present": True,
            "component_coverage": {
                "capture_type": "LIVE_MODELER_RUNTIME", "session_id": "test", "scene_revision": 0,
                "mesh_object_names": ["Body"], "pass": False,
                "coverage": {"declared_primary_components": ["body"], "built_object_names": ["Body"],
                    "component_matches": {"body": "Body"}, "unmatched_primary_components": [], "coverage_ok": True},
                "component_layout": {
                    "layout_expectations_present": True, "layout_ok": False, "status": "fail",
                    "component_reports": {"body": {"object_name": "Body", "presence_ok": True, "placement_ok": False, "proportion_ok": True}},
                },
            },
        })
        self.assertFalse(result["pass"])
        self.assertIn("structured one-to-one component coverage is missing or invalid", result["failures"])

    def test_stage_gate_rejects_global_only_visual_evidence(self):
        result = evaluate_stage_gate("PROPORTION_SILHOUETTE", {"view_count": 3, "worst_view_iou": 0.88, "multiview_regression_pass": True})
        self.assertFalse(result["pass"])
        self.assertIn("worst-view IoU below 0.9", result["failures"])

    def test_stage_gate_reports_malformed_numeric_evidence_without_crashing(self):
        result = evaluate_stage_gate("PROPORTION_SILHOUETTE", {
            "view_count": "three", "worst_view_iou": "high",
            "multiview_regression_pass": True,
        })
        self.assertFalse(result["pass"])
        self.assertIn("view_count must describe at least two relevant views", result["failures"])
        self.assertIn("worst_view_iou must be a number in [0, 1]", result["failures"])

    def test_hard_failure_overrides_weighted_score(self):
        result = aggregate_professional_review([
            ReviewChannel("technical", 1.0, evidence="verify.json"),
            ReviewChannel("surface", 0.95, hard_pass=False, evidence="surface.json"),
        ])
        self.assertFalse(result["pass"])
        self.assertEqual(result["hard_failures"], ["surface"])

    def test_human_rejection_becomes_revision_bound_localized_repair_tickets(self):
        review = {
            "review_result": "reject", "reviewer_type": "human", "reviewer_id": "reviewer-01",
            "asset_id": "unfamiliar-prop", "scene_revision": 7,
            "failure_types": ["proportion", "negative_space"],
            "regions": [
                {"target": "body", "failure_type": "proportion", "view": "front", "severity": 0.9},
                {"target": "handle_gap", "failure_type": "negative_space", "view": "side", "severity": 0.8},
            ],
            "severity": {"proportion": 0.9, "negative_space": 0.8},
            "notes": "The body is too tall and the handle clearance is too narrow.",
        }
        tickets = review_to_repair_tickets(review, current_scene_revision=7)
        self.assertEqual([ticket["target"] for ticket in tickets], ["body", "handle_gap"])
        self.assertTrue(all(ticket["source"] == "EXTERNAL_HUMAN_REVIEW" for ticket in tickets))
        with self.assertRaisesRegex(ValueError, "not current revision"):
            review_to_repair_tickets(review, current_scene_revision=8)
        agent_review = {**review, "reviewer_type": "agent"}
        with self.assertRaisesRegex(ValueError, "only a human"):
            validate_external_visual_review(agent_review)
        handoff = build_repair_record(review, current_scene_revision=7)
        self.assertEqual(handoff["disposition"], "INSPECT_BEFORE_REPAIR")
        self.assertEqual(handoff["repair_tickets"], tickets)


class SessionLearningTests(unittest.TestCase):
    def test_candidates_require_separate_replay(self):
        events = [
            {"evaluation": "accepted", "asset_id": "a", "chosen_action": {"op": "bevel"}},
            {"evaluation": "accepted", "asset_id": "b", "chosen_action": {"op": "bevel"}},
            {"evaluation": "repaired", "asset_id": "b", "chosen_action": {"op": "bevel"}},
        ]
        candidate = mine_session_events(events)["candidates"][0]
        self.assertEqual(candidate["status"], "CANDIDATE_REQUIRES_REPLAY")
        result = apply_replay_result(candidate, {"replay_id": "r1", "different_asset": True, "expected": "clean", "observed": "clean", "pass": True, "evidence_path": "run.json"})
        self.assertEqual(result["status"], "REPLAY_VALIDATED")
        richer = apply_replay_result(candidate, {"replay_id": "r2", "different_asset": True, "expected": "clean", "observed": {"clean": True, "faces": 30}, "pass": True, "evidence_path": "verify.json"})
        self.assertEqual(richer["status"], "REPLAY_VALIDATED")


class StrategyTests(unittest.TestCase):
    def test_curve_and_separate_component_choice(self):
        result = choose_strategy(ModelingBrief(follows_path=True, independent_motion_or_material=True))
        self.assertEqual(result["representation"]["choice"], "CURVE")
        self.assertEqual(result["components"]["choice"], "SEPARATE_COMPONENTS")

    def test_rebuild_requires_accumulated_evidence(self):
        patch = choose_strategy(ModelingBrief(local_damage_fraction=0.05))["repair"]
        rebuild = choose_strategy(ModelingBrief(local_damage_fraction=0.6, failed_repairs=3, modifier_instability=0.8))["repair"]
        self.assertEqual(patch["choice"], "PATCH_REGION")
        self.assertEqual(rebuild["choice"], "REBUILD_REGION")


class PlannerTests(unittest.TestCase):
    def context(self, **changes):
        values = dict(
            task_id="test",
            asset_id="asset",
            stage="PROPORTION_SILHOUETTE",
            session_id="session",
            scene_revision=4,
            active_object="Asset",
            base_state={"mesh_health": {}},
            evaluated_state={"mesh_health": {}},
        )
        values.update(changes)
        return PlannerContext(**values)

    def test_planner_does_not_apply_a_stale_human_review_ticket(self):
        decision = plan_next_decision(self.context(visual_tickets=[{
            "type": "human_review_proportion", "target": "body", "severity": 1.0,
            "source": "EXTERNAL_HUMAN_REVIEW", "scene_revision": 3,
        }]))
        self.assertEqual(decision.action, "RECAPTURE_STALE_HUMAN_REVIEW")
        self.assertEqual(decision.disposition, "INSPECT")

    def test_authority_and_external_edit_preempt_mutation(self):
        wait = plan_next_decision(self.context(control_mode="USER_CONTROL"))
        self.assertEqual(wait.disposition, "WAIT")
        self.assertIsNone(wait.operation)
        stale = plan_next_decision(self.context(external_edit_detected=True))
        self.assertEqual(stale.action, "REOBSERVE_AFTER_EXTERNAL_EDIT")

    def test_technical_failure_preempts_visual_ticket_and_can_rebuild(self):
        repair = plan_next_decision(self.context(
            evaluated_state={"mesh_health": {"non_manifold_edges": 4}},
            visual_tickets=[{"type": "contour_error", "priority": 1, "severity": 1.0}],
        ))
        self.assertEqual(repair.action, "LOCALIZE_NON_MANIFOLD_REGION")
        rebuild = plan_next_decision(self.context(
            evaluated_state={"mesh_health": {"non_manifold_edges": 4}},
            repair_history=RegionRepairHistory("seam", 3, 0.8, 0.0, 1.0),
        ))
        self.assertEqual(rebuild.action, "REBUILD_OPEN_REGION")

    def test_explicit_intentional_boundary_allowlist_does_not_hide_excess_breakage(self):
        ticket = {
            "type": "contour_error", "target": "open_glass_lip", "priority": 1,
            "severity": 0.8, "suggested_operation": "scale_selection",
            "operation_params": {"factor": [1.05, 1.05, 1.0]},
        }
        allowed = plan_next_decision(self.context(
            evaluated_state={"mesh_health": {"non_manifold_edges": 4}},
            intentional_non_manifold_edge_ids=(101, 102, 103, 104),
            visual_tickets=[ticket],
        ))
        self.assertEqual(allowed.operation, "scale_selection")
        excess = plan_next_decision(self.context(
            evaluated_state={"mesh_health": {"non_manifold_edges": 5}},
            intentional_non_manifold_edge_ids=(101, 102, 103, 104),
            visual_tickets=[ticket],
        ))
        self.assertEqual(excess.action, "LOCALIZE_NON_MANIFOLD_REGION")
        self.assertIn("1 non-manifold edges remain unexplained", excess.rationale)

    def test_uncertainty_visual_action_and_stage_advance(self):
        research = plan_next_decision(self.context(diagnosis=Diagnosis("pinch", 0.3, ["healthy curvature"])))
        self.assertEqual(research.disposition, "RESEARCH")
        visual = plan_next_decision(self.context(visual_tickets=[{
            "type": "contour_error", "target": "rim", "priority": 1, "severity": 0.8,
            "suggested_operation": "scale_selection", "operation_params": {"factor": [1.05, 1, 1]},
        }]))
        self.assertEqual(visual.operation, "scale_selection")
        self.assertEqual(visual.target_region, "rim")
        advance = plan_next_decision(self.context(stage_evidence={
            "view_count": 3, "worst_view_iou": 0.95, "multiview_regression_pass": True,
        }))
        self.assertEqual(advance.next_stage, "SECONDARY_FORMS")
        self.assertEqual(advance.observed_revision, 4)

    def test_primary_blockout_plans_live_component_capture_before_geometry(self):
        decomp = SceneDecompositionTests()._strict_lantern_decomposition()
        decision = plan_next_decision(self.context(
            stage="PRIMARY_BLOCKOUT",
            reference_decomposition=decomp,
            visual_tickets=[{
                "type": "missing_component", "target": "handle", "priority": 1, "severity": 1.0,
            }],
        ))
        self.assertEqual(decision.disposition, "INSPECT")
        self.assertEqual(decision.action, "CAPTURE_LIVE_COMPONENT_COVERAGE")
        self.assertEqual(decision.operation, "check_scene_component_coverage")
        self.assertEqual(
            decision.operation_params["decomposition"]["object_name"], "stylized lantern"
        )

    def test_primary_blockout_recaptures_stale_component_coverage(self):
        decomp = SceneDecompositionTests()._strict_lantern_decomposition()
        decision = plan_next_decision(self.context(
            stage="PRIMARY_BLOCKOUT",
            scene_revision=4,
            reference_decomposition=decomp,
            stage_evidence={
                "component_coverage": {
                    "capture_type": "LIVE_MODELER_RUNTIME", "session_id": "prior", "scene_revision": 3,
                    "mesh_object_names": ["Body", "Handle"], "pass": True,
                    "coverage": {
                        "declared_primary_components": ["body", "handle"],
                        "built_object_names": ["Body", "Handle"],
                        "component_matches": {"body": "Body", "handle": "Handle"},
                        "unmatched_primary_components": [], "coverage_ok": True,
                    },
                },
            },
        ))
        self.assertEqual(decision.action, "CAPTURE_LIVE_COMPONENT_COVERAGE")
        self.assertTrue(any("differs from observed revision 4" in item for item in decision.rationale))

    def test_passing_final_review_completes_instead_of_requesting_more_evidence(self):
        complete = plan_next_decision(self.context(
            stage="FINAL_REVIEW",
            stage_evidence={
                "independent_verification_pass": True,
                "reference_review_pass": True,
                "editable_source_saved": True,
            },
        ))
        self.assertEqual(complete.disposition, "COMPLETE")
        self.assertEqual(complete.action, "ACCEPT_FINAL_REVIEW")
        self.assertIsNone(complete.operation)

    def test_transfer_validated_skill_changes_matching_ticket_to_scoped_action(self):
        ticket = {
            "type": "uneven_deformation_density",
            "target": "pedestal_waist",
            "priority": 1,
            "severity": 0.7,
            "operation_params": {"cuts": 6, "edge_ids": [11, 12]},
        }
        without_skill = plan_next_decision(self.context(visual_tickets=[ticket]))
        self.assertEqual(without_skill.disposition, "INSPECT")

        captured_skill = {
            "skill_id": "uniform-rings",
            "status": "CAPTURED",
            "skill": {
                "planner_hint": {
                    "trigger_ticket_types": ["uneven_deformation_density"],
                    "modeling_stages": ["PROPORTION_SILHOUETTE"],
                    "required_ticket_fields": ["target", "operation_params"],
                    "action": "ESTABLISH_UNIFORM_DEFORMATION_RINGS",
                    "operation": "loop_cut_selection",
                }
            },
        }
        still_inspect = plan_next_decision(self.context(
            visual_tickets=[ticket], retrieved_skills=[captured_skill]
        ))
        self.assertEqual(still_inspect.disposition, "INSPECT")

        validated_skill = {**captured_skill, "status": "TRANSFER_VALIDATED"}
        acted = plan_next_decision(self.context(
            visual_tickets=[ticket], retrieved_skills=[validated_skill]
        ))
        self.assertEqual(acted.disposition, "ACT")
        self.assertEqual(acted.action, "ESTABLISH_UNIFORM_DEFORMATION_RINGS")
        self.assertEqual(acted.operation, "loop_cut_selection")
        self.assertEqual(acted.operation_params, ticket["operation_params"])
        self.assertEqual(acted.target_region, "pedestal_waist")
        self.assertEqual(acted.retrieved_skill_ids, ("uniform-rings",))

    def test_reference_uncertainty_blocks_blockout_with_a_research_contract(self):
        decomp = SceneDecompositionTests()._strict_lantern_decomposition(extra_claims=[
            ReferenceClaim(
                "rear-depth", "depth_order",
                "Whether the rear housing projects beyond the body is unknown.",
                "UNKNOWN", 0.1, impact="high", component_refs=["body"],
            ),
        ])
        decision = plan_next_decision(self.context(
            stage="REFERENCE_ANALYSIS",
            stage_evidence={
                "component_graph_pass": True,
                "measured_ratio_count": 3,
                "uncertainty_recorded": True,
                "reference_set_audit_pass": True,
                "same_target_identity_pass": True,
                "view_coverage_pass": True,
                "critical_property_coverage_pass": True,
                "conflicts_resolved_pass": True,
                "question_driven_research_pass": True,
            },
            reference_decomposition=decomp,
        ))
        self.assertEqual(decision.disposition, "RESEARCH")
        self.assertEqual(decision.action, "RESOLVE_REFERENCE_UNCERTAINTY")
        self.assertEqual(decision.operation_params["claim_ids"], ["rear-depth"])
        self.assertIn("rear housing", decision.operation_params["research_questions"][0])

    def test_technical_breakage_still_preempts_reference_uncertainty(self):
        decomp = SceneDecompositionTests()._strict_lantern_decomposition(extra_claims=[
            ReferenceClaim(
                "rear-depth", "depth_order", "Rear depth is unknown.",
                "UNKNOWN", 0.1, impact="high", component_refs=["body"],
            ),
        ])
        decision = plan_next_decision(self.context(
            stage="PRIMARY_BLOCKOUT",
            evaluated_state={"mesh_health": {"non_manifold_edges": 4}},
            reference_decomposition=decomp,
        ))
        self.assertEqual(decision.action, "LOCALIZE_NON_MANIFOLD_REGION")

    def test_evidence_bound_claims_change_representation_and_component_policy(self):
        decomp = SceneDecompositionTests()._strict_lantern_decomposition()
        decision = plan_next_decision(self.context(
            visual_tickets=[{
                "type": "missing_component", "target": "handle", "priority": 1, "severity": 1.0,
            }],
            brief=ModelingBrief(follows_path=False, independent_motion_or_material=False),
            reference_decomposition=decomp,
        ))
        self.assertEqual(decision.operation, "create_curve")
        self.assertEqual(decision.operation_params["representation"], "CURVE")
        self.assertEqual(decision.operation_params["component_policy"], "SEPARATE_COMPONENTS")
        self.assertTrue(any("handle-path" in note for note in decision.operation_params["reference_claim_notes"]))


class CurriculumInventoryTests(unittest.TestCase):
    def test_every_mandatory_mesh_operator_is_in_inventory(self):
        inventory = (
            Path(__file__).parents[1]
            / "knowledge" / "foundation" / "operator_cards" / "mandatory_mesh_editing_inventory.md"
        ).read_text(encoding="utf-8")
        required = {
            "Selection", "Extrude", "Inset", "Bevel", "Loop Cut", "Connect Vertex Path", "Subdivide", "Knife",
            "Bisect", "Bridge Edge Loops", "Spin", "Merge", "Merge by Distance", "Dissolve",
            "Delete", "Fill", "Grid Fill", "Edge Slide", "Vertex Slide", "Rip", "Split",
            "Separate", "Symmetrize", "Normals", "Shade Smooth", "Shade Flat",
            "Smooth by Angle", "Crease",
        }
        present = {
            line.split("|")[1].strip()
            for line in inventory.splitlines()
            if line.startswith("|") and not line.startswith("| ---") and "Operator" not in line
        }
        self.assertEqual(present, required)
        self.assertIn("API and typed support", inventory)
        self.assertIn("Topology effects and common failures", inventory)


if __name__ == "__main__":
    unittest.main()
