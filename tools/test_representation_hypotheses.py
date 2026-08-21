"""Test StrategyCandidate predicted_consequences against a reference manifest,
without Blender.

Meant to run BEFORE modeling commits to a representation: takes a scene JSON
(a list of StrategyCandidate-shaped dicts, each optionally carrying
predicted_consequences) and a reference manifest, and runs
knowledge_engine.representation_hypothesis.evaluate_predicted_consequence for
every consequence against the reference item it names. Mirrors
tools/verify_reference_set_gate.py's CLI shape.

Each predicted_consequences entry may additionally carry:
  reference_id: which manifest item to test against (required to run a test;
    consequences without one are reported UNDECIDABLE, not skipped silently)
  landmarks: optional list of [position_fraction, boundary_value] pairs,
    forwarded to evaluate_predicted_consequence for prediction_types that use
    them (currently boundary_linearity on an ORTHOGRAPHIC reference)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_engine.reference_analysis import reference_set_from_dict
from knowledge_engine.representation_hypothesis import evaluate_predicted_consequence


def _run(scene_payload: dict, reference_payload: dict) -> dict:
    reference_set = reference_set_from_dict(reference_payload)
    items_by_id = {item.reference_id: item for item in reference_set.items}

    candidate_reports = []
    for candidate in scene_payload.get("candidates", []):
        consequence_reports = []
        for consequence in candidate.get("predicted_consequences", []):
            reference_id = consequence.get("reference_id")
            reference_item = items_by_id.get(reference_id)
            if reference_item is None:
                consequence_reports.append({
                    "view": consequence.get("view"),
                    "property": consequence.get("property"),
                    "reference_id": reference_id,
                    "result": {
                        "status": "UNDECIDABLE",
                        "reason": f"no reference item '{reference_id}' in the manifest",
                        "prediction_type": consequence.get("prediction_type"),
                    },
                })
                continue
            landmarks = consequence.get("landmarks")
            if landmarks is not None:
                landmarks = [tuple(point) for point in landmarks]
            result = evaluate_predicted_consequence(consequence, reference_item, landmarks=landmarks)
            consequence_reports.append({
                "view": consequence.get("view"),
                "property": consequence.get("property"),
                "reference_id": reference_id,
                "result": result,
            })
        candidate_reports.append({
            "name": candidate.get("name"),
            "representation": candidate.get("representation"),
            "consequences": consequence_reports,
        })

    return {"schema_version": 1, "candidates": candidate_reports}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path, help="scene-decomposition JSON with candidates + predicted_consequences")
    parser.add_argument("reference_manifest", type=Path, help="structured reference-set manifest JSON")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    scene_payload = json.loads(args.scene.read_text(encoding="utf-8"))
    reference_payload = json.loads(args.reference_manifest.read_text(encoding="utf-8"))
    result = _run(scene_payload, reference_payload)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
