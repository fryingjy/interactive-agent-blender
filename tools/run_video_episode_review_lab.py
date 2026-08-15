"""Exercise the video episode review gate with pass, pending, and rejection controls."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-15_video-episode-review-gate"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.video_episode_review import TranscriptEvidence, review_episode_alignment
from tools.review_video_episode import load_evidence


def main() -> None:
    baseline_evidence = load_evidence(OUT / "fixture_episode_evidence.json")
    baseline = review_episode_alignment(baseline_evidence)
    controls = {
        "model_only_no_independent_reviewer": review_episode_alignment(
            replace(baseline_evidence, independent_reviewer=False)
        ),
        "missing_after_frame": review_episode_alignment(
            replace(
                baseline_evidence,
                frame_observations=baseline_evidence.frame_observations[:2],
            )
        ),
        "speech_outside_episode": review_episode_alignment(
            replace(
                baseline_evidence,
                transcript_segments=(TranscriptEvidence(8.0, 9.0, "unrelated speech"),),
            )
        ),
        "source_identity_mismatch": review_episode_alignment(
            replace(
                baseline_evidence,
                source_identity_verified=False,
                source_identity_mismatch=True,
            )
        ),
        "explicit_visible_action_mismatch": review_episode_alignment(
            replace(baseline_evidence, visible_action_observed=False)
        ),
        "public_browser_identity_without_frames": review_episode_alignment(
            replace(
                baseline_evidence,
                source_id="yi87Dap_WOc",
                start_seconds=307.0,
                end_seconds=400.0,
                frame_observations=(),
                transcript_segments=(),
                visible_action_observed=None,
                speech_action_alignment="UNVERIFIED",
            )
        ),
    }
    assertions = {
        "fixture_episode_verified": baseline["disposition"] == "VERIFIED",
        "model_only_pending": (
            controls["model_only_no_independent_reviewer"]["disposition"] == "PENDING_REVIEW"
        ),
        "missing_after_pending": controls["missing_after_frame"]["disposition"] == "PENDING_REVIEW",
        "speech_outside_pending": controls["speech_outside_episode"]["disposition"] == "PENDING_REVIEW",
        "source_mismatch_rejected": controls["source_identity_mismatch"]["disposition"] == "REJECTED",
        "visible_mismatch_rejected": (
            controls["explicit_visible_action_mismatch"]["disposition"] == "REJECTED"
        ),
        "public_browser_attempt_pending": (
            controls["public_browser_identity_without_frames"]["disposition"] == "PENDING_REVIEW"
        ),
    }
    report = {
        "baseline": baseline,
        "controls": controls,
        "assertions": assertions,
        "pass": all(assertions.values()),
        "claim_boundary": json.loads(
            (OUT / "experiment_contract.json").read_text(encoding="utf-8")
        )["claim_boundary"],
    }
    (OUT / "episode_review_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({"assertions": assertions, "pass": report["pass"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
