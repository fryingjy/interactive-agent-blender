import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from knowledge_engine.video_episode_review import (
    EpisodeReviewEvidence,
    FrameObservation,
    TranscriptEvidence,
    review_episode_alignment,
)
from tools.review_video_episode import load_evidence


class VideoEpisodeReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = []
        for name in ("before.png", "during.png", "after.png"):
            path = root / name
            path.write_bytes(b"fixture")
            self.paths.append(str(path))
        self.evidence = EpisodeReviewEvidence(
            source_id="fixture",
            start_seconds=2.0,
            end_seconds=4.0,
            visible_action_claim="base cage changes to evaluated rounded surface",
            spoken_reason_claim="inspect the evaluated surface",
            source_identity_verified=True,
            independent_reviewer=True,
            frame_observations=(
                FrameObservation(1.8, self.paths[0], "BEFORE", "angular base cage visible"),
                FrameObservation(2.2, self.paths[1], "DURING", "rounded surface becomes visible"),
                FrameObservation(4.1, self.paths[2], "AFTER", "next comparison stage visible"),
            ),
            transcript_segments=(
                TranscriptEvidence(2.0, 4.0, "inspect the evaluated surface"),
            ),
            visible_action_observed=True,
            speech_action_alignment="ALIGNED",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_independent_review_verifies(self):
        result = review_episode_alignment(self.evidence)
        self.assertEqual(result["disposition"], "VERIFIED")
        self.assertTrue(result["pass"])

    def test_model_only_claim_stays_pending(self):
        result = review_episode_alignment(replace(self.evidence, independent_reviewer=False))
        self.assertEqual(result["disposition"], "PENDING_REVIEW")

    def test_missing_after_frame_stays_pending(self):
        result = review_episode_alignment(
            replace(self.evidence, frame_observations=self.evidence.frame_observations[:2])
        )
        self.assertEqual(result["disposition"], "PENDING_REVIEW")
        self.assertFalse(result["checks"]["temporal_positions_bracket_episode"])

    def test_nonexistent_frame_path_stays_pending(self):
        missing = replace(self.evidence.frame_observations[1], path=self.paths[1] + ".missing")
        frames = (self.evidence.frame_observations[0], missing, self.evidence.frame_observations[2])
        result = review_episode_alignment(replace(self.evidence, frame_observations=frames))
        self.assertEqual(result["disposition"], "PENDING_REVIEW")

    def test_transcript_outside_episode_stays_pending(self):
        transcript = (TranscriptEvidence(8.0, 9.0, "unrelated speech"),)
        result = review_episode_alignment(replace(self.evidence, transcript_segments=transcript))
        self.assertEqual(result["disposition"], "PENDING_REVIEW")

    def test_explicit_visible_mismatch_is_rejected(self):
        result = review_episode_alignment(replace(self.evidence, visible_action_observed=False))
        self.assertEqual(result["disposition"], "REJECTED")
        self.assertIn("visible_action_mismatch", result["contradictions"])

    def test_unverified_source_stays_pending(self):
        result = review_episode_alignment(
            replace(self.evidence, source_identity_verified=False)
        )
        self.assertEqual(result["disposition"], "PENDING_REVIEW")

    def test_source_or_speech_mismatch_is_rejected(self):
        for changed in (
            replace(
                self.evidence,
                source_identity_verified=False,
                source_identity_mismatch=True,
            ),
            replace(self.evidence, speech_action_alignment="MISMATCH"),
        ):
            with self.subTest(changed=changed):
                self.assertEqual(review_episode_alignment(changed)["disposition"], "REJECTED")

    def test_loader_resolves_paths_relative_to_evidence_file(self):
        root = Path(self.temp.name)
        payload = {
            "source_id": "fixture",
            "start_seconds": 2.0,
            "end_seconds": 4.0,
            "visible_action_claim": "action",
            "spoken_reason_claim": "reason",
            "source_identity_verified": True,
            "independent_reviewer": True,
            "frame_observations": [
                {
                    "timestamp": 2.2,
                    "path": "during.png",
                    "temporal_position": "DURING",
                    "observed_fact": "visible change",
                }
            ],
            "transcript_segments": [],
            "visible_action_observed": None,
            "speech_action_alignment": "UNVERIFIED",
        }
        evidence_path = root / "evidence.json"
        evidence_path.write_text(json.dumps(payload), encoding="utf-8")
        loaded = load_evidence(evidence_path)
        self.assertEqual(Path(loaded.frame_observations[0].path), root / "during.png")


if __name__ == "__main__":
    unittest.main()
