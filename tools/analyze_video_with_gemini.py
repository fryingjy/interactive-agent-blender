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
    DEFAULT_MODEL,
    analyze_youtube_video,
    build_request,
    write_analysis,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract timestamped multimodal Blender-learning episodes without downloading video."
    )
    parser.add_argument("url", help="Public HTTPS YouTube watch URL")
    parser.add_argument("--output", type=Path, help="JSON evidence output path")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--focus", default="")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print a secret-free request summary without calling Gemini",
    )
    args = parser.parse_args()

    if args.dry_run:
        request = build_request(args.url, args.model, args.focus)
        summary = {
            "model": request["model"],
            "video_uri": request["input"][1]["uri"],
            "prompt_version": "blender-video-study-v1",
            "structured_output": True,
            "video_archived": False,
        }
        print(json.dumps(summary, indent=2))
        return 0

    if args.output is None:
        parser.error("--output is required unless --dry-run is used")
    result = analyze_youtube_video(
        args.url,
        model=args.model,
        focus=args.focus,
    )
    target = write_analysis(result, args.output)
    print(f"wrote unverified Gemini extraction: {target}")
    print("next gate: independently check representative timestamps before promotion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
