"""Review one timestamped episode against independent local frame and transcript evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.video_episode_review import (
    EpisodeReviewEvidence,
    FrameObservation,
    TranscriptEvidence,
    review_episode_alignment,
)


def load_evidence(path: Path) -> EpisodeReviewEvidence:
    data = json.loads(path.read_text(encoding="utf-8"))
    frame_items = []
    for item in data["frame_observations"]:
        frame_path = Path(item["path"])
        if not frame_path.is_absolute():
            repo_candidate = ROOT / frame_path
            frame_path = repo_candidate if repo_candidate.exists() else path.parent / frame_path
        frame_items.append({**item, "path": str(frame_path.resolve())})
    return EpisodeReviewEvidence(
        source_id=data["source_id"],
        start_seconds=data["start_seconds"],
        end_seconds=data["end_seconds"],
        visible_action_claim=data["visible_action_claim"],
        spoken_reason_claim=data["spoken_reason_claim"],
        source_identity_verified=data["source_identity_verified"],
        independent_reviewer=data["independent_reviewer"],
        frame_observations=tuple(FrameObservation(**item) for item in frame_items),
        transcript_segments=tuple(TranscriptEvidence(**item) for item in data["transcript_segments"]),
        visible_action_observed=data.get("visible_action_observed"),
        speech_action_alignment=data.get("speech_action_alignment", "UNVERIFIED"),
        source_identity_mismatch=data.get("source_identity_mismatch", False),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = review_episode_alignment(load_evidence(args.evidence))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
