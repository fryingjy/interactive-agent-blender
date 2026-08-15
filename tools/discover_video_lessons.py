"""Create a metadata-only Blender tutorial study queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.ingest.video_discovery import (
    build_study_queue,
    discover_youtube_lessons,
    known_youtube_ids,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover public tutorial metadata without downloading or claiming video understanding."
    )
    parser.add_argument("--query", action="append", required=True, help="Learning-gap search query; repeatable")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-query", type=int, default=8)
    parser.add_argument("--maximum", type=int, default=20)
    parser.add_argument("--exclude-video-id", action="append", default=[])
    parser.add_argument(
        "--exclude-source-file",
        action="append",
        default=[],
        type=Path,
        help="Registry/evidence file whose public YouTube URLs should be excluded",
    )
    parser.add_argument("--heldout-target-term", action="append", default=[])
    parser.add_argument(
        "--exclude-topic-term",
        action="append",
        default=[],
        help="Known off-priority topic term (for example character or sculpting)",
    )
    args = parser.parse_args()

    excluded_ids = set(args.exclude_video_id) | known_youtube_ids(args.exclude_source_file)
    discoveries = [
        discover_youtube_lessons(
            query,
            limit=args.per_query,
            excluded_video_ids=excluded_ids,
            heldout_target_terms=args.heldout_target_term,
            excluded_topic_terms=args.exclude_topic_term,
        )
        for query in args.query
    ]
    queue = build_study_queue(discoveries, maximum=args.maximum)
    queue["excluded_video_ids"] = sorted(excluded_ids)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "queries": len(queue["queries"]),
        "candidates": queue["candidate_count"],
        "excluded_known_video_ids": len(excluded_ids),
        "media_downloaded": queue["media_downloaded"],
        "promotion_count": queue["promotion_count"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
