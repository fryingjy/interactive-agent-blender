import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from knowledge_engine.gemini_video_study import (
    apply_independent_episode_reviews,
    analyze_youtube_video,
    build_request,
    build_generate_content_request,
    load_dotenv,
    load_expected_source_metadata,
    validate_analysis,
    normalize_model_confidences,
    normalize_model_timestamps,
    validate_expected_source,
    validate_time_range,
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
    def test_normalizes_numeric_percentage_confidence_with_provenance(self):
        data = _analysis()
        data["episodes"][0]["confidence"] = 85
        changes = normalize_model_confidences(data)
        self.assertEqual(data["episodes"][0]["confidence"], 0.85)
        self.assertEqual(changes[0]["original"], 85)
        validate_analysis(data, data["source"]["url"])

    def test_does_not_normalize_ambiguous_or_invalid_confidence(self):
        for value in ("85", -1, 101, float("inf")):
            data = _analysis()
            data["episodes"][0]["confidence"] = value
            with self.subTest(value=value):
                self.assertEqual(normalize_model_confidences(data), [])

    def test_normalizes_mmss_encoded_as_decimal_integer(self):
        data = _analysis()
        episode = data["episodes"][0]
        episode.update({
            "timestamp_label": "01:05 - 01:34",
            "start_seconds": 105,
            "end_seconds": 134,
        })
        changes = normalize_model_timestamps(data)
        self.assertEqual((episode["start_seconds"], episode["end_seconds"]), (65.0, 94.0))
        self.assertEqual(len(changes), 2)

    def test_does_not_override_valid_seconds_from_approximate_label(self):
        data = _analysis()
        episode = data["episodes"][0]
        episode.update({
            "timestamp_label": "01:05 - 01:34",
            "start_seconds": 64,
            "end_seconds": 95,
        })
        self.assertEqual(normalize_model_timestamps(data), [])
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
        self.assertIn("https://youtu.be/abc123", request["input"][0]["text"])
        self.assertEqual(request["response_format"]["mime_type"], "application/json")
        self.assertIn("observed_fact", request["response_format"]["schema"]["properties"]["episodes"]["items"]["required"])

    def test_generate_content_fallback_keeps_url_prompt_schema_and_identity(self):
        expected = {
            "url": "https://youtu.be/abc123",
            "title": "Exact Lesson",
            "creator": "Exact Artist",
            "duration_seconds": 100,
        }
        request = build_generate_content_request(
            "https://youtu.be/abc123", "gemini-test", expected_source=expected
        )
        self.assertEqual(request["model"], "gemini-test")
        self.assertEqual(request["contents"].parts[0].file_data.file_uri, "https://youtu.be/abc123")
        self.assertEqual(request["config"].response_mime_type, "application/json")
        self.assertIn("episodes", request["config"].response_json_schema["properties"])
        self.assertIn("Exact Lesson", request["contents"].parts[1].text)

    def test_range_scoped_generate_content_uses_video_metadata_and_absolute_time_prompt(self):
        expected = {
            "url": "https://youtu.be/abc123",
            "title": "Exact Lesson",
            "creator": "Exact Artist",
            "duration_seconds": 200,
        }
        request = build_generate_content_request(
            expected["url"],
            "gemini-test",
            expected_source=expected,
            start_seconds=24,
            end_seconds=124,
        )
        media = request["contents"].parts[0]
        self.assertEqual(media.video_metadata.start_offset, "24s")
        self.assertEqual(media.video_metadata.end_offset, "124s")
        prompt = request["contents"].parts[1].text
        self.assertIn("24 to 124 seconds", prompt)
        self.assertIn("absolute timestamp", prompt)

    def test_range_validation_requires_complete_bounded_pair(self):
        self.assertEqual(validate_time_range(24, 124, duration_seconds=200), (24.0, 124.0))
        for start, end in ((24, None), (None, 124), (-1, 20), (20, 20), (20, 201)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                validate_time_range(start, end, duration_seconds=200)

    def test_direct_source_metadata_requires_complete_matching_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "identity.json"
            path.write_text(json.dumps({
                "url": "https://youtu.be/abc123", "title": "Lesson", "creator": "Artist",
                "duration_seconds": 120,
            }), encoding="utf-8")
            record = load_expected_source_metadata(path, "https://www.youtube.com/watch?v=abc123")
            self.assertEqual(record["duration_seconds"], 120.0)
            path.write_text(json.dumps({
                "url": "https://youtu.be/other", "title": "", "creator": "Artist", "duration_seconds": 0
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "title"):
                load_expected_source_metadata(path)
            path.write_text(json.dumps({
                "url": "https://youtu.be/other", "title": "Lesson", "creator": "Artist",
                "duration_seconds": 120,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_expected_source_metadata(path, "https://youtu.be/abc123")

    def test_request_binds_discovery_identity_into_prompt(self):
        expected = {
            "url": "https://www.youtube.com/watch?v=abc123",
            "title": "Exact Lesson",
            "creator": "Exact Artist",
            "duration_seconds": 100,
        }
        request = build_request(expected["url"], expected_source=expected)
        prompt = request["input"][0]["text"]
        self.assertIn("Exact Lesson", prompt)
        self.assertIn("Untrusted public-source metadata", prompt)
        self.assertIn("Do not substitute", prompt)

    def test_validation_requires_visible_evidence(self):
        data = _analysis()
        data["episodes"][0]["evidence_modalities"] = ["CAPTIONS"]
        with self.assertRaisesRegex(ValueError, "visible video"):
            validate_analysis(data, data["source"]["url"])

    def test_validation_rejects_episodes_without_video_access(self):
        data = _analysis()
        data["access"]["video_inspected"] = False
        with self.assertRaisesRegex(ValueError, "video_inspected"):
            validate_analysis(data, data["source"]["url"])

    def test_validation_rejects_episode_beyond_reported_duration(self):
        data = _analysis()
        data["episodes"][0]["end_seconds"] = 101
        with self.assertRaisesRegex(ValueError, "exceeds the reported source duration"):
            validate_analysis(data, data["source"]["url"])

    def test_validation_rejects_url_substitution(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_analysis(_analysis(), "https://www.youtube.com/watch?v=different")

    def test_validation_accepts_canonical_short_url_for_same_video(self):
        data = _analysis("https://youtu.be/abc123")
        validate_analysis(data, "https://www.youtube.com/watch?v=abc123")

    def test_expected_source_rejects_title_creator_and_duration_substitution(self):
        expected = {"title": "Tutorial", "creator": "Artist", "duration_seconds": 100}
        validate_expected_source(_analysis(), expected)
        for field, value in (("title", "Other"), ("creator", "Other"), ("duration_seconds", 160)):
            data = _analysis()
            data["source"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "does not match"):
                validate_expected_source(data, expected)

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

    def test_rejects_unverifiable_model_reported_url(self):
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
            with self.assertRaisesRegex(ValueError, "cross-video attribution"):
                analyze_youtube_video(requested, client_factory=Client)

    def test_rejects_different_valid_model_reported_url(self):
        requested = "https://www.youtube.com/watch?v=abc123"
        payload = _analysis("https://www.youtube.com/watch?v=wrong456")

        class Interaction:
            output_text = json.dumps(payload)
            model = "gemini-test"
            id = "interaction-3"

        class Client:
            def __init__(self, api_key):
                self.interactions = self

            def create(self, **request):
                return Interaction()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret"}, clear=False):
            with self.assertRaisesRegex(ValueError, "cross-video attribution"):
                analyze_youtube_video(requested, client_factory=Client)

    def test_reports_permission_denial_without_exposing_credential(self):
        class Client:
            def __init__(self, api_key):
                self.interactions = self

            def create(self, **request):
                raise RuntimeError("403 The caller does not have permission")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-key"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "Gemini rejected the configured credential") as error:
                analyze_youtube_video(
                    "https://www.youtube.com/watch?v=abc123", client_factory=Client
                )
        self.assertNotIn("private-test-key", str(error.exception))

    def test_permission_denial_falls_back_to_generate_content(self):
        url = "https://www.youtube.com/watch?v=abc123"

        class InteractionClient:
            def create(self, **request):
                raise RuntimeError("403 The caller does not have permission")

        class Response:
            text = json.dumps(_analysis(url))
            model_version = "gemini-generate-test"

        class Models:
            def generate_content(self, **request):
                self.request = request
                return Response()

        class Client:
            def __init__(self, api_key):
                self.interactions = InteractionClient()
                self.models = Models()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret"}, clear=False):
            result = analyze_youtube_video(url, client_factory=Client)
        self.assertEqual(result["provenance"]["endpoint"], "generate_content")
        self.assertEqual(result["provenance"]["response_model"], "gemini-generate-test")

    def test_range_scoped_analysis_bypasses_whole_video_interaction(self):
        url = "https://www.youtube.com/watch?v=abc123"
        payload = _analysis(url)
        payload["episodes"][0]["start_seconds"] = 24.0
        payload["episodes"][0]["end_seconds"] = 40.0

        class Models:
            def generate_content(self, **request):
                self.request = request
                return type("Response", (), {"text": json.dumps(payload), "model_version": "range-test"})()

        class Interactions:
            def create(self, **request):
                raise AssertionError("whole-video interaction must not run for a scoped study")

        class Client:
            def __init__(self, api_key):
                self.models = Models()
                self.interactions = Interactions()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret"}, clear=False):
            result = analyze_youtube_video(
                url,
                start_seconds=24,
                end_seconds=124,
                client_factory=Client,
            )
        self.assertEqual(result["provenance"]["endpoint"], "generate_content_range")
        self.assertEqual(result["provenance"]["requested_time_range"], [24.0, 124.0])

    def test_range_scoped_analysis_rejects_out_of_range_episode(self):
        url = "https://www.youtube.com/watch?v=abc123"
        payload = _analysis(url)

        class Models:
            def generate_content(self, **request):
                return type("Response", (), {"text": json.dumps(payload), "model_version": "range-test"})()

        class Client:
            def __init__(self, api_key):
                self.models = Models()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret"}, clear=False):
            with self.assertRaisesRegex(ValueError, "outside the requested"):
                analyze_youtube_video(
                    url,
                    start_seconds=24,
                    end_seconds=80,
                    client_factory=Client,
                )

    def test_write_analysis_round_trips_utf8_json(self):
        with tempfile.TemporaryDirectory() as directory:
            target = write_analysis({"text": "topology → transfer"}, Path(directory) / "analysis.json")
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["text"], "topology → transfer")


    def test_independent_review_can_advance_matching_episode_only(self):
        result = {
            "provenance": {
                "requested_source_url": "https://www.youtube.com/watch?v=abc123",
                "verification_status": "MODEL_EXTRACTED_UNVERIFIED",
            },
            "analysis": _analysis(),
        }
        review = {
            "source_id": "abc123",
            "episode": [10.0, 20.0],
            "disposition": "VERIFIED",
            "pass": True,
        }
        updated = apply_independent_episode_reviews(result, {0: review})
        self.assertEqual(
            updated["provenance"]["verification_status"],
            "INDEPENDENTLY_FRAME_VERIFIED",
        )
        self.assertTrue(updated["provenance"]["knowledge_promotion_unchanged"])
        self.assertEqual(result["provenance"]["verification_status"], "MODEL_EXTRACTED_UNVERIFIED")

    def test_partial_or_rejected_review_cannot_become_verified(self):
        result = {
            "provenance": {"requested_source_url": "https://youtu.be/abc123"},
            "analysis": _analysis(),
        }
        for disposition, expected in (
            ("PENDING_REVIEW", "PARTIAL_INDEPENDENT_REVIEW"),
            ("REJECTED", "INDEPENDENT_REVIEW_REJECTED"),
        ):
            review = {
                "source_id": "abc123",
                "episode": [10.0, 20.0],
                "disposition": disposition,
                "pass": disposition == "VERIFIED",
            }
            with self.subTest(disposition=disposition):
                updated = apply_independent_episode_reviews(result, {0: review})
                self.assertEqual(updated["provenance"]["verification_status"], expected)

    def test_review_rejects_cross_video_or_wrong_timestamp(self):
        result = {
            "provenance": {"requested_source_url": "https://youtu.be/abc123"},
            "analysis": _analysis(),
        }
        base = {
            "source_id": "abc123",
            "episode": [10.0, 20.0],
            "disposition": "VERIFIED",
            "pass": True,
        }
        with self.assertRaisesRegex(ValueError, "source"):
            apply_independent_episode_reviews(result, {0: {**base, "source_id": "wrong"}})
        with self.assertRaisesRegex(ValueError, "timestamp"):
            apply_independent_episode_reviews(result, {0: {**base, "episode": [1.0, 2.0]}})


if __name__ == "__main__":
    unittest.main()
