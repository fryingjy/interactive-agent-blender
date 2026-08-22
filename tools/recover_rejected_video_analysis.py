"""Revalidate a retained Gemini extraction after deterministic normalization fixes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.gemini_video_study import (
    normalize_model_confidences,
    normalize_model_timestamps,
    validate_analysis,
    write_analysis,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rejected", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-url", required=True)
    args = parser.parse_args()

    retained = json.loads(args.rejected.read_text(encoding="utf-8"))
    if retained.get("verification_status") != "MODEL_EXTRACTION_REJECTED":
        raise ValueError("input is not a retained rejected extraction")
    analysis = retained["analysis"]
    normalizations = normalize_model_timestamps(analysis)
    normalizations.extend(normalize_model_confidences(analysis))
    if not normalizations:
        raise ValueError("no deterministic normalization applies")
    validate_analysis(analysis, args.expected_url)
    write_analysis(
        {
            "provenance": {
                "extractor": "Google Gemini video understanding",
                "requested_source_url": args.expected_url,
                "verification_status": "MODEL_EXTRACTED_UNVERIFIED",
                "recovered_from_rejected_payload": str(args.rejected),
                "normalizations": normalizations,
                "video_archived": False,
            },
            "analysis": analysis,
        },
        args.output,
    )
    print(f"revalidated normalized extraction: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
