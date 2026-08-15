import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from knowledge_engine.gemini_video_study import (
    analyze_youtube_video,
    build_request,
    load_dotenv,
    validate_analysis,
    validate_youtube_url,
    youtube_video_id,
    write_analysis,
)


def _analysis(url="https://www.youtube.com/watch?v=abc123"):
    episode = {
        "start_seconds": 10.0,
        "end_seconds": 20.0,
        "timestamp_label": "00:10-00:20",
        "modeling_stage": "blockout",
        "problem": "choose the primary anchor",
        "observed_fact": "A rectangular base is visible in two reference views.",
        "instructor_claim": "The base is the least ambiguous form.",
        "interpretation": "Stable landmarks reduce early proportion drift.",
        "hypothesis": "The same rule may transfer to furniture.",
        "reference_evidence": "Two views agree on the rectangular footprint.",
        "modeling_decision": "Start from the base plane.",
        "visible_action": "The instructor adds and scales one plane.",
        "spoken_reason": "It is clearly rectangular.",
        "topology_surface_effect": "A minimal planar anchor is established.",
        "failure": "",
        "correction": "",
        "alternatives": "Starting from the curved horn.",
        "transferable_principle": "Begin with the least ambiguous primary landmark.",
        "confidence": 0.9,
        "evidence_modalities": ["VIDEO", "AUDIO"],
    }
    return {
        "source": {
            "title": "Tutorial",
            "creator": "Artist",
            "url": url,
            "duration_seconds": 100.0,
            "blender_version_mentions": [],
        },
        "access": {
            "video_inspected": True,
            "audio_inspected": True,
            "captions_used": False,
            "inaccessible_segments": [],
        },
        "study_scope": "reference interpretation",
        "episodes": [episode],
        "rejected_sections": ["intro"],
        "limitations": [],
    }


class GeminiVideoStudyTests(unittest.TestCase):
    def test_accepts_public_youtube_watch_url(self):
        url = "https://www.youtube.com/watch?v=abc123"
        self.assertEqual(validate_youtube_url(url), url)

    def test_rejects_non_youtube_or_non_watch_url(self):
        for url in ("https://example.com/video", "http://youtube.com/watch?v=x", "https://youtube.com/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_youtube_url(url)

    def test_equivalent_youtube_url_forms_share_video_id(self):
        self.assertEqual(
            youtube_video_id("https://youtu.be/abc123"),
            youtube_video_id("https://www.youtube.com/watch?v=abc123&t=10"),
        )

    def test_request_uses_direct_video_input_and_structured_output(self):
        request = build_request("https://youtu.be/abc123")
        self.assertEqual(request["input"][1]["type"], "video")
        self.assertEqual(request["input"][1]["uri"], "https://youtu.be/abc123")
        self.assertEqual(request["response_format"]["mime_type"], "application/json")
        self.assertIn("observed_fact", request["response_format"]["schema"]["properties"]["episodes"]["items"]["required"])

    def test_validation_requires_visible_evidence(self):
        data = _analysis()
        data["episodes"][0]["evidence_modalities"] = ["CAPTIONS"]
        with self.assertRaisesRegex(ValueError, "visible video"):
            validate_analysis(data, data["source"]["url"])

    def test_validation_rejects_url_substitution(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_analysis(_analysis(), "https://www.youtube.com/watch?v=different")

    def test_validation_accepts_canonical_short_url_for_same_video(self):
        data = _analysis("https://youtu.be/abc123")
        validate_analysis(data, "https://www.youtube.com/watch?v=abc123")

    def test_dotenv_does_not_overwrite_existing_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("GEMINI_API_KEY=file-key\n", encoding="utf-8")
            with patch.dict(os.environ, {"GEMINI_API_KEY": "existing-key"}, clear=False):
                self.assertTrue(load_dotenv(path))
                self.assertEqual(os.environ["GEMINI_API_KEY"], "existing-key")

    def test_client_is_injected_and_result_remains_unverified(self):
        url = "https://www.youtube.com/watch?v=abc123"

        class Interaction:
            output_text = json.dumps(_analysis(url))
            model = "gemini-test"
            id = "interaction-1"

        class Interactions:
            def create(self, **request):
                self.request = request
                return Interaction()

        class Client:
            def __init__(self, api_key):
                self.interactions = Interactions()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret"}, clear=False):
            result = analyze_youtube_video(url, client_factory=Client)
        self.assertEqual(result["provenance"]["verification_status"], "MODEL_EXTRACTED_UNVERIFIED")
        self.assertFalse(result["provenance"]["video_archived"])

    def test_request_owned_url_overrides_model_reported_url(self):
        requested = "https://www.youtube.com/watch?v=abc123"
        reported = "I inspected the supplied video input"
        payload = _analysis(requested)
        payload["source"]["url"] = reported

        class Interaction:
            output_text = json.dumps(payload)
            model = "gemini-test"
            id = "interaction-2"

        class Client:
            def __init__(self, api_key):
                self.interactions = self

            def create(self, **request):
                return Interaction()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret"}, clear=False):
            result = analyze_youtube_video(requested, client_factory=Client)
        self.assertEqual(result["analysis"]["source"]["url"], requested)
        self.assertEqual(result["provenance"]["reported_source_url"], reported)
        self.assertFalse(result["provenance"]["reported_source_matches_request"])

    def test_write_analysis_round_trips_utf8_json(self):
        with tempfile.TemporaryDirectory() as directory:
            target = write_analysis({"text": "topology → transfer"}, Path(directory) / "analysis.json")
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["text"], "topology → transfer")


if __name__ == "__main__":
    unittest.main()
