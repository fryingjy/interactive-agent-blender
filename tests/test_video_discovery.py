import json
import tempfile
import unittest
from pathlib import Path

from knowledge_engine.ingest.video_discovery import (
    DISCOVERY_STATUS,
    build_study_queue,
    discover_youtube_lessons,
    known_youtube_ids,
)


def _payload(*entries):
    return json.dumps({"entries": list(entries)})


class VideoDiscoveryTests(unittest.TestCase):
    def test_discovery_is_metadata_only_ranked_and_secret_free(self):
        captured = {}

        def runner(command, timeout):
            captured.update(command=command, timeout=timeout)
            return _payload(
                {
                    "id": "long1",
                    "title": "Hard Surface Reference Modeling and Clean Topology",
                    "description": "Reference blockout, topology decisions, and correction workflow.",
                    "duration": 1200,
                    "channel": "Teacher",
                    "view_count": 10000,
                    "channel_is_verified": True,
                },
                {
                    "id": "short1",
                    "title": "Fast Blender topology trick",
                    "description": "One shortcut.",
                    "duration": 30,
                    "channel": "Shorts",
                    "view_count": 1000000,
                },
            )

        report = discover_youtube_lessons(
            "Blender hard surface reference modeling topology workflow", limit=2, runner=runner
        )

        self.assertEqual(report["candidates"][0]["video_id"], "long1")
        self.assertEqual(report["candidates"][0]["status"], DISCOVERY_STATUS)
        self.assertFalse(report["media_downloaded"])
        self.assertFalse(report["candidates"][0]["knowledge_promoted"])
        self.assertIn("--flat-playlist", captured["command"])
        self.assertIn("--no-warnings", captured["command"])
        self.assertNotIn("--output", captured["command"])
        serialized = json.dumps(report)
        self.assertNotIn("googlevideo.com", serialized)
        self.assertNotIn("api_key", serialized.lower())

    def test_rejects_duplicates_and_heldout_target_contamination(self):
        report = discover_youtube_lessons(
            "subdivision topology",
            limit=3,
            excluded_video_ids=["seen"],
            heldout_target_terms=["bialetti moka pot"],
            runner=lambda *_: _payload(
                {"id": "seen", "title": "Subdivision topology", "duration": 500},
                {"id": "target", "title": "Model a Bialetti moka pot", "duration": 500},
                {"id": "safe", "title": "Subdivision topology on curved products", "duration": 500},
            ),
        )
        self.assertEqual([item["video_id"] for item in report["candidates"]], ["safe"])
        self.assertEqual({item["video_id"] for item in report["rejected"]}, {"seen", "target"})
        target = next(item for item in report["rejected"] if item["video_id"] == "target")
        self.assertEqual(target["reason"], "held-out target contamination risk")

    def test_rejects_explicitly_off_priority_topics(self):
        report = discover_youtube_lessons(
            "reference modeling blockout",
            excluded_topic_terms=["character sculpt animation"],
            runner=lambda *_: _payload(
                {"id": "organic", "title": "Characters sculpting blockout", "duration": 500},
                {"id": "prop", "title": "Product reference blockout", "duration": 500},
            ),
        )
        self.assertEqual([item["video_id"] for item in report["candidates"]], ["prop"])
        self.assertEqual(report["rejected"][0]["reason"], "current curriculum priority exclusion")

    def test_queue_deduplicates_cross_query_candidates(self):
        first = discover_youtube_lessons(
            "hard surface topology",
            runner=lambda *_: _payload({"id": "same", "title": "Hard surface topology", "duration": 600}),
        )
        second = discover_youtube_lessons(
            "reference modeling",
            runner=lambda *_: _payload({"id": "same", "title": "Reference modeling", "duration": 600}),
        )
        queue = build_study_queue([first, second])
        self.assertEqual(queue["candidate_count"], 1)
        self.assertEqual(queue["candidates"][0]["source_queries"], [
            "hard surface topology", "reference modeling"
        ])
        self.assertEqual(queue["candidates"][0]["next_gate"], "MULTIMODAL_EXTRACTION")
        self.assertEqual(queue["promotion_count"], 0)
        self.assertEqual(queue["discovery_summaries"][0]["candidate_video_ids"], ["same"])
        self.assertNotIn("candidates", queue["discovery_summaries"][0])

    def test_rejects_urls_ytsearch_expressions_and_bad_limits(self):
        for query in ("", "https://youtube.com/watch?v=x", "ytsearch5:topology"):
            with self.subTest(query=query), self.assertRaises(ValueError):
                discover_youtube_lessons(query, runner=lambda *_: _payload())
        with self.assertRaises(ValueError):
            discover_youtube_lessons("topology", limit=26, runner=lambda *_: _payload())

    def test_extracts_known_ids_from_explicit_registry_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "sources.json"
            registry.write_text(json.dumps([
                {"url": "https://www.youtube.com/watch?v=known_1&t=12"},
                {"url": "https://youtu.be/known-2"},
                {"url": "https://example.com/not-video"},
            ]), encoding="utf-8")
            self.assertEqual(known_youtube_ids([registry]), {"known_1", "known-2"})


if __name__ == "__main__":
    unittest.main()
