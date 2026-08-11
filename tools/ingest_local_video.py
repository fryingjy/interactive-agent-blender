"""CLI for permitted local video ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.ingest.video_ingest import ingest_video


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--approved-root", action="append", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--coarse-interval", type=float, default=30.0)
    parser.add_argument("--fine-timestamp", type=float, action="append", default=[])
    parser.add_argument("--transcribe-model", help="Optional faster-whisper model, e.g. tiny.en")
    parser.add_argument("--transcript-language", default="en")
    parser.add_argument("--machine-transcript-file")
    parser.add_argument(
        "--include-transcript-text",
        action="store_true",
        help="Embed transcript wording in the public ingest report (off by default)",
    )
    args = parser.parse_args()
    result = ingest_video(
        args.video,
        approved_roots=args.approved_root,
        output_dir=args.output_dir,
        source_id=args.source_id,
        coarse_interval=args.coarse_interval,
        fine_timestamps=args.fine_timestamp,
        transcribe_model=args.transcribe_model,
        transcript_language=args.transcript_language,
        include_transcript_text=args.include_transcript_text,
        machine_transcript_path=args.machine_transcript_file,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
