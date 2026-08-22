"""Analyze a public YouTube Blender tutorial with Gemini video understanding."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.gemini_video_study import (
    AnalysisValidationError,
    DEFAULT_MODEL,
    analyze_youtube_video,
    build_request,
    load_expected_source_metadata,
    validate_time_range,
    write_analysis,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract timestamped multimodal Blender-learning episodes without downloading video."
    )
    parser.add_argument("url", nargs="?", help="Public HTTPS YouTube watch URL")
    parser.add_argument("--discovery-queue", type=Path, help="Use a ranked candidate from a discovery queue")
    parser.add_argument("--rank", type=int, default=1, help="Queue rank used with --discovery-queue")
    parser.add_argument(
        "--source-metadata",
        type=Path,
        help="Independent JSON identity record (url, title, creator, duration_seconds) for a direct URL",
    )
    parser.add_argument("--output", type=Path, help="JSON evidence output path")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--focus", default="")
    parser.add_argument("--start-seconds", type=float)
    parser.add_argument("--end-seconds", type=float)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print a secret-free request summary without calling Gemini",
    )
    args = parser.parse_args()

    expected_source = None
    source_url = args.url
    if args.discovery_queue:
        if args.url or args.source_metadata:
            parser.error("--discovery-queue cannot be combined with URL or --source-metadata")
        queue = json.loads(args.discovery_queue.read_text(encoding="utf-8"))
        expected_source = next(
            (item for item in queue.get("candidates", []) if item.get("queue_rank") == args.rank),
            None,
        )
        if expected_source is None:
            parser.error(f"queue has no candidate at rank {args.rank}")
        source_url = expected_source["url"]
    elif args.source_metadata:
        if not args.url:
            parser.error("--source-metadata requires a direct URL")
        try:
            expected_source = load_expected_source_metadata(args.source_metadata, args.url)
        except ValueError as exc:
            parser.error(str(exc))
    if not source_url:
        parser.error("URL or --discovery-queue is required")
    try:
        study_range = validate_time_range(
            args.start_seconds,
            args.end_seconds,
            duration_seconds=(expected_source or {}).get("duration_seconds"),
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.dry_run:
        request = build_request(source_url, args.model, args.focus, expected_source)
        summary = {
            "model": request["model"],
            "video_uri": request["input"][1]["uri"],
            "prompt_version": "blender-video-study-v1",
            "structured_output": True,
            "video_archived": False,
            "discovery_identity_bound": expected_source is not None,
            "identity_metadata_source": str(args.source_metadata) if args.source_metadata else None,
            "requested_time_range": (
                list(study_range) if study_range else None
            ),
        }
        print(json.dumps(summary, indent=2))
        return 0

    if args.output is None:
        parser.error("--output is required unless --dry-run is used")
    try:
        result = analyze_youtube_video(
            source_url,
            model=args.model,
            focus=args.focus,
            expected_source=expected_source,
            start_seconds=args.start_seconds,
            end_seconds=args.end_seconds,
        )
    except AnalysisValidationError as exc:
        rejected = args.output.with_suffix(args.output.suffix + ".rejected")
        write_analysis(
            {
                "verification_status": "MODEL_EXTRACTION_REJECTED",
                "validation_error": str(exc),
                "analysis": exc.analysis,
            },
            rejected,
        )
        print(f"rejected extraction retained for diagnosis: {rejected}", file=sys.stderr)
        raise
    target = write_analysis(result, args.output)
    print(f"wrote unverified Gemini extraction: {target}")
    print("next gate: independently check representative timestamps before promotion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
