"""Analyze one public YouTube reference-workflow lesson with Gemini video input.

This is a reproducible caller for the method previously documented only in run
notes.  It never downloads or archives the source video.  The output remains
CAPTURED evidence until separately reproduced and transfer-tested.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from google import genai


PROMPT = """Watch and listen to the entire supplied video as reference-workflow training for a
professional 3D modeling agent. Do not infer content from the title. Return JSON only with:
video_identity {title, creator, subject}; access_observation {audio_used, visuals_used};
episodes [{start, end, observed_visual_fact, instructor_claim, interpretation,
hypothesis, reference_workflow_stage, concrete_action, reason, failure_or_warning,
transferable_principle}]; reference_categories; acquisition_methods; organization_methods;
selection_and_rejection_criteria; contradiction_handling; iterative_research_triggers;
principles; limitations; claims_requiring_external_verification; proposed_experiments.

Use timestamps for every episode. Keep OBSERVED VISUAL FACT, INSTRUCTOR CLAIM,
INTERPRETATION, and HYPOTHESIS separate. Record what the artist actually does with references,
what they reject, why they group or retain an image, how they distinguish evidence from
inspiration, and when they return to research. Do not convert application shortcuts into universal
modeling rules. If a requested topic is absent, say so. Never claim this analysis proves transfer.
"""


def _load_key(env_path: Path) -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("GEMINI_API_KEY is not set")


def _oembed(url: str) -> dict:
    endpoint = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")
    with urllib.request.urlopen(endpoint, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def analyze(url: str, output: Path, *, model: str, env_path: Path) -> dict:
    metadata = _oembed(url)
    client = genai.Client(api_key=_load_key(env_path))
    interaction = client.interactions.create(
        model=model,
        input=[{"type": "video", "uri": url}, {"type": "text", "text": PROMPT}],
    )
    raw = interaction.output_text
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    try:
        analysis = json.loads(cleaned.strip())
        parse_status = "PARSED_JSON"
    except json.JSONDecodeError:
        analysis = {"raw_text": raw}
        parse_status = "RAW_TEXT"
    result = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": {"url": url, "title": metadata.get("title"), "author": metadata.get("author_name")},
        "access": {
            "method": "Gemini public YouTube URL video input",
            "model": model,
            "archived_source_video": False,
            "analysis_status": parse_status,
        },
        "knowledge_status": "CAPTURED",
        "promotion_warning": "Requires external corroboration, controlled reproduction, and different-target transfer.",
        "analysis": analysis,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default="gemini-3.6-flash")
    parser.add_argument("--env", type=Path, default=Path(__file__).resolve().parents[1] / ".env")
    args = parser.parse_args()
    result = analyze(args.url, args.output, model=args.model, env_path=args.env)
    print(json.dumps({"source": result["source"], "access": result["access"]}))


if __name__ == "__main__":
    main()
