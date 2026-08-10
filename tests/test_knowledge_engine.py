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
from knowledge_engine.telemetry import SkillUsage, SkillUsageLog
from knowledge_engine.visual_compare import compare_component_masks, compare_landmarks, compare_masks, make_reference_tickets, negative_space_mask
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
    def test_stage_gate_rejects_global_only_visual_evidence(self):
        result = evaluate_stage_gate("PROPORTION_SILHOUETTE", {"view_count": 3, "worst_view_iou": 0.88, "multiview_regression_pass": True})
        self.assertFalse(result["pass"])
        self.assertIn("worst-view IoU below 0.9", result["failures"])

    def test_hard_failure_overrides_weighted_score(self):
        result = aggregate_professional_review([
            ReviewChannel("technical", 1.0, evidence="verify.json"),
            ReviewChannel("surface", 0.95, hard_pass=False, evidence="surface.json"),
        ])
        self.assertFalse(result["pass"])
        self.assertEqual(result["hard_failures"], ["surface"])


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


class CurriculumInventoryTests(unittest.TestCase):
    def test_every_mandatory_mesh_operator_is_in_inventory(self):
        inventory = (
            Path(__file__).parents[1]
            / "knowledge" / "foundation" / "operator_cards" / "mandatory_mesh_editing_inventory.md"
        ).read_text(encoding="utf-8")
        required = {
            "Selection", "Extrude", "Inset", "Bevel", "Loop Cut", "Subdivide", "Knife",
            "Bisect", "Bridge Edge Loops", "Spin", "Merge", "Merge by Distance", "Dissolve",
            "Delete", "Fill", "Grid Fill", "Edge Slide", "Vertex Slide", "Rip", "Split",
            "Separate", "Symmetrize", "Normals", "Shade Smooth", "Shade Flat",
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
