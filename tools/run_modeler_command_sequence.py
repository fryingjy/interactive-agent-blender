"""Execute a JSON command sequence through ModelerServer in a fresh Blender process.

The sequence format is data, not executable Python. Every mutation therefore still
passes through the registered typed command surface and its transaction lifecycle.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender_ops.modeler_server import ModelerServer  # noqa: E402


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--load", type=Path)
    parser.add_argument("--save", type=Path)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    if args.load:
        bpy.ops.wm.open_mainfile(filepath=str(args.load.resolve()))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    sequence = json.loads(args.sequence.read_text(encoding="utf-8"))
    if not isinstance(sequence, list) or not sequence:
        raise ValueError("sequence must be a non-empty JSON list")
    server = ModelerServer()
    results = []
    success = True
    for index, item in enumerate(sequence):
        if not isinstance(item, dict):
            raise ValueError(f"sequence item {index} must be an object")
        transaction = item.get("transaction")
        stage_advance = item.get("advance_with_component_coverage")
        command = item.get("command")
        if transaction is None and stage_advance is None and not isinstance(command, str):
            raise ValueError(f"sequence item {index} requires command text, a transaction, or a component-coverage stage advance")
        params = item.get("params", {})
        label = item.get("label", f"step_{index:03d}")
        try:
            if stage_advance is not None:
                if not isinstance(stage_advance, dict):
                    raise ValueError("advance_with_component_coverage must be an object")
                decomposition = stage_advance["decomposition"]
                if isinstance(decomposition, str):
                    decomposition_path = Path(decomposition)
                    if not decomposition_path.is_absolute():
                        decomposition_path = (args.sequence.parent / decomposition_path).resolve()
                    decomposition = json.loads(decomposition_path.read_text(encoding="utf-8"))
                if not isinstance(decomposition, dict):
                    raise ValueError("advance_with_component_coverage.decomposition must be an object or JSON file path")
                coverage = server.cmd_check_scene_component_coverage(
                    decomposition,
                    collection_name=stage_advance.get("collection_name"),
                )
                evidence = {
                    "dimensions_checked": bool(stage_advance.get("dimensions_checked")),
                    "primary_components_present": bool(stage_advance.get("primary_components_present")),
                    "component_coverage": coverage,
                }
                advanced = server.cmd_set_modeling_stage(
                    stage_advance["name"],
                    stage_advance.get("stage", "PROPORTION_SILHOUETTE"),
                    evidence,
                )
                result = {"component_coverage": coverage, "stage_advance": advanced}
                command = "advance_with_component_coverage"
                params = stage_advance
            elif transaction is not None:
                if not isinstance(transaction, dict):
                    raise ValueError("transaction must be an object")
                name = transaction["name"]
                action_type = transaction["action_type"]
                operation = transaction["operation"]
                operation_params = transaction.get("params", {})
                begun = server.cmd_begin_decision(name, action_type)
                decision_id = begun["decision_id"]
                performed = server.cmd_perform_decision(
                    decision_id,
                    operation,
                    operation_params,
                    command_id=transaction.get("command_id", f"{label}-{decision_id}"),
                )
                verified = server.cmd_verify_decision(decision_id)
                if transaction.get("accept", True):
                    judged = server.cmd_commit_decision(decision_id)
                    judgment = "committed"
                else:
                    judged = server.cmd_reject_decision(decision_id, transaction.get("reason", "sequence rejection control"))
                    judgment = "rejected"
                result = {
                    "begin": begun,
                    "perform": performed,
                    "verify": verified,
                    "judgment": judgment,
                    "judge_result": judged,
                }
                command = "transaction"
                params = transaction
            else:
                result = server._dispatch(command, params)
            if isinstance(result, dict) and result.get("error"):
                raise RuntimeError(f"typed command returned an error: {result['error']}")
            results.append({"index": index, "label": label, "command": command, "params": params, "status": "ok", "result": result})
        except Exception as exc:
            success = False
            results.append({"index": index, "label": label, "command": command, "params": params, "status": "error", "error": str(exc), "traceback": traceback.format_exc()})
            break
    save_result = None
    if success and args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        save_result = server.cmd_save_file(str(args.save.resolve()))
    report = {
        "schema_version": 1,
        "record_type": "TYPED_MODELER_COMMAND_SEQUENCE",
        "sequence": str(args.sequence.resolve()),
        "loaded_file": str(args.load.resolve()) if args.load else None,
        "saved_file": str(args.save.resolve()) if args.save and success else None,
        "blender_version": bpy.app.version_string,
        "session_id": server.session_id,
        "results": results,
        "save_result": save_result,
        "pass": success,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": success, "completed_steps": len(results), "report": str(args.report)}))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
