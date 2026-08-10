import json
import tempfile
import unittest
from pathlib import Path

from knowledge_engine.ingest.document_ingest import ingest_document
from knowledge_engine.ingest.transcript_ingest import parse_transcript
from knowledge_engine.reasoning import (
    Diagnosis,
    RegionRepairHistory,
    validate_component_graph,
    validate_multiview_metrics,
)
from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore
from knowledge_engine.schemas import AccessRecord, SourceRecord
from knowledge_engine.telemetry import SkillUsage, SkillUsageLog
from knowledge_engine.visual_compare import compare_masks
from knowledge_engine.strategy import ModelingBrief, choose_strategy

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


if __name__ == "__main__":
    unittest.main()
