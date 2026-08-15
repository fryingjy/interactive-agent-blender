"""Independent structural verification for the retained video-discovery run."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-15_video-discovery-queue"
OLD = ROOT / "runs" / "2026-08-15_gemini-pipeline-validation" / "gemini_structured_analysis.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    queue_path = RUN / "discovery_queue.json"
    queue_text = queue_path.read_text(encoding="utf-8")
    queue = json.loads(queue_text)
    failed = load(RUN / "top_candidate_gemini_analysis.json")
    strict = load(RUN / "strict_top_candidate_analysis.json")
    review = load(RUN / "independent_review.json")
    old = load(OLD)
    candidates = queue["candidates"]
    top = candidates[0]
    strict_source = strict["analysis"]["source"]
    known_at_discovery = set(queue["excluded_video_ids"])
    blocked = ("bialetti", "moka", "camera", "telephone", "watering", "lamp", "boombox", "wrench")
    candidate_text = " ".join(f"{item['title']} {item['description']}" for item in candidates).casefold()
    checks = {
        "queue_has_three_gap_queries": len(queue["queries"]) == 3,
        "queue_has_15_unique_candidates": len(candidates) == 15 == len({item["video_id"] for item in candidates}),
        "known_registry_sources_are_excluded": not (known_at_discovery & {item["video_id"] for item in candidates}),
        "heldout_target_terms_are_absent": not any(term in candidate_text for term in blocked),
        "discovery_downloaded_no_media": queue["media_downloaded"] is False,
        "queue_contains_no_ephemeral_media_urls": "googlevideo.com" not in queue_text and '"formats"' not in queue_text,
        "discovery_promoted_no_knowledge": queue["promotion_count"] == 0 and all(not item["knowledge_promoted"] for item in candidates),
        "failed_call_is_retained_as_identity_rejection": failed["provenance"]["reported_source_matches_request"] is False and failed["provenance"]["verification_status"] == "REJECTED_SOURCE_IDENTITY_MISMATCH",
        "old_mismatched_validation_is_rejected": old["provenance"]["reported_source_matches_request"] is False and old["provenance"]["verification_status"] == "REJECTED_SOURCE_IDENTITY_MISMATCH",
        "strict_call_matches_requested_video": strict["provenance"]["reported_source_matches_request"] is True and strict_source["url"] == top["url"],
        "strict_call_matches_discovery_metadata": strict_source["title"] == top["title"] and strict_source["creator"] == top["creator"] and abs(strict_source["duration_seconds"] - top["duration_seconds"]) <= 2,
        "independent_review_preserves_timestamp_defect": review["disposition"] == "INDEPENDENT_REVIEW_PARTIAL_TIMESTAMP_DEFECT" and any(item["result"] == "TIMESTAMP_DEFECT" for item in review["checks"]),
        "nothing_was_promoted_after_partial_review": review["knowledge_promoted"] is False and review["speech_action_alignment_proven"] is False,
    }
    report = {"checks": checks, "pass": all(checks.values())}
    (RUN / "independent_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
