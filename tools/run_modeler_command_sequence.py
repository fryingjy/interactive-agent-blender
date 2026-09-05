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
from blender_ops.stage_gates import evaluate_stage_gate  # noqa: E402
from knowledge_engine.tutorial_reproduction import (  # noqa: E402
    asset_surface_gate_required,
    asset_mutation_gate_required,
    procedural_fixture_sequence,
    reference_modeling_gate_required,
    tutorial_modeling_gate_required,
    validate_tutorial_blockout_review,
    validate_tutorial_premodeling_evidence,
    validate_surface_diagnostic,
)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--load", type=Path)
    parser.add_argument("--save", type=Path)
    parser.add_argument("--tutorial-evidence", type=Path)
    parser.add_argument("--reference-stage-evidence", type=Path)
    parser.add_argument("--tutorial-blockout-review", type=Path)
    parser.add_argument("--surface-diagnostic-only", action="store_true",
                        help="Test live modifiers on a new .diagnostic.blend copy; never approve an asset")
    parser.add_argument("--allow-procedural-fixture", action="store_true")
    parser.add_argument("--allow-legacy-ungated-tutorial", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    sequence = json.loads(args.sequence.read_text(encoding="utf-8"))
    if not isinstance(sequence, list) or not sequence:
        raise ValueError("sequence must be a non-empty JSON list")
    fixture_path = procedural_fixture_sequence(args.sequence)
    fixture_exemption = args.allow_procedural_fixture or args.allow_legacy_ungated_tutorial
    mutation_required = asset_mutation_gate_required(args.sequence, sequence)
    tutorial_path = tutorial_modeling_gate_required(
        args.sequence, [{"command": "create_primitive"}]
    )
    if fixture_exemption and not fixture_path:
        raise ValueError("ungated construction is permitted only for an explicitly named lab/test fixture path")
    gate_results: dict[str, object] = {
        "procedural_fixture_path": fixture_path,
        "procedural_fixture_exemption": fixture_exemption,
        "asset_mutation_requires_authorization": mutation_required,
    }
    tutorial_evidence = None
    reference_evidence = None
    if args.surface_diagnostic_only:
        if fixture_exemption:
            raise ValueError("surface diagnostic cannot use fixture exemptions")
        gate_results["surface_diagnostic"] = validate_surface_diagnostic(sequence, args.load, args.save)
    if tutorial_modeling_gate_required(args.sequence, sequence) and not fixture_exemption:
        if args.tutorial_evidence is None:
            raise ValueError(
                "tutorial construction is blocked before Blender mutation: provide --tutorial-evidence "
                "with independently inspected geometry references and measured constraints"
            )
        tutorial_evidence = json.loads(args.tutorial_evidence.read_text(encoding="utf-8"))
        gate = validate_tutorial_premodeling_evidence(tutorial_evidence)
        gate_results["premodeling"] = gate
        if not gate["pass"]:
            raise ValueError(f"tutorial pre-modeling evidence gate failed: {gate['issues']}")
    if reference_modeling_gate_required(args.sequence, sequence) and not fixture_exemption:
        if args.reference_stage_evidence is None:
            raise ValueError(
                "reference-driven construction is blocked before Blender mutation: provide "
                "--reference-stage-evidence containing the audited multiview shape-pipeline bundle"
            )
        reference_evidence = json.loads(args.reference_stage_evidence.read_text(encoding="utf-8"))
        gate = evaluate_stage_gate("REFERENCE_ANALYSIS", reference_evidence)
        gate_results["reference_analysis"] = gate
        if not gate["pass"]:
            raise ValueError(f"reference-analysis gate failed: {gate['failures'] or gate['missing']}")
    if asset_surface_gate_required(args.sequence, sequence) and not fixture_exemption and not args.surface_diagnostic_only:
        if args.tutorial_blockout_review is None:
            raise ValueError(
                "asset surface treatment is blocked before Blender mutation: provide "
                "--tutorial-blockout-review with measured raw-cage comparisons"
            )
        review = json.loads(args.tutorial_blockout_review.read_text(encoding="utf-8"))
        gate = validate_tutorial_blockout_review(review)
        gate_results["blockout_review"] = gate
        if not gate["pass"]:
            raise ValueError(f"tutorial blockout review gate failed: {gate['issues']}")
    if mutation_required and not fixture_exemption:
        if tutorial_path and tutorial_evidence is None:
            if args.tutorial_evidence is None:
                raise ValueError("tutorial asset mutation requires --tutorial-evidence for runtime target authorization")
            tutorial_evidence = json.loads(args.tutorial_evidence.read_text(encoding="utf-8"))
            gate = validate_tutorial_premodeling_evidence(tutorial_evidence)
            gate_results["premodeling"] = gate
            if not gate["pass"]:
                raise ValueError(f"tutorial pre-modeling evidence gate failed: {gate['issues']}")
        if not tutorial_path and reference_evidence is None:
            if args.reference_stage_evidence is None:
                raise ValueError("reference asset mutation requires --reference-stage-evidence for runtime target authorization")
            reference_evidence = json.loads(args.reference_stage_evidence.read_text(encoding="utf-8"))
            gate = evaluate_stage_gate("REFERENCE_ANALYSIS", reference_evidence)
            gate_results["reference_analysis"] = gate
            if not gate["pass"]:
                raise ValueError(f"reference-analysis gate failed: {gate['failures'] or gate['missing']}")
    if asset_surface_gate_required(args.sequence, sequence) and not fixture_exemption and not args.surface_diagnostic_only:
        review_target = review.get("target_id")
        evidence_target = (
            tutorial_evidence.get("target_id") if tutorial_evidence is not None
            else reference_evidence.get("reference_audit", {}).get("target_id")
            if reference_evidence is not None else None
        )
        if review_target != evidence_target:
            raise ValueError("modeling authorization evidence and blockout review target_id values differ")
    if args.load:
        bpy.ops.wm.open_mainfile(filepath=str(args.load.resolve()))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    strict_runtime = mutation_required and not fixture_exemption
    server = ModelerServer(enforce_reference_authorization=strict_runtime)
    if strict_runtime:
        if tutorial_evidence is not None:
            server.cmd_authorize_tutorial_modeling(tutorial_evidence)
        elif reference_evidence is not None:
            server.cmd_authorize_reference_modeling(reference_evidence)
        else:
            raise ValueError("asset mutation reached runtime without target authorization evidence")
        existing_targets = set()
        for item in sequence:
            if not isinstance(item, dict):
                continue
            transaction = item.get("transaction")
            stage_advance = item.get("advance_with_component_coverage")
            if isinstance(transaction, dict) and isinstance(transaction.get("name"), str):
                existing_targets.add(transaction["name"])
            if isinstance(stage_advance, dict) and isinstance(stage_advance.get("name"), str):
                existing_targets.add(stage_advance["name"])
        for name in sorted(existing_targets):
            if name in bpy.data.objects:
                server.cmd_bind_existing_object_to_reference(name)
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
                begun = server.cmd_begin_decision(
                    name,
                    action_type,
                    allowed_vertex_ids=transaction.get("allowed_vertex_ids"),
                )
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
        "gate_results": gate_results,
        "results": results,
        "save_result": save_result,
        "pass": success,
        "artifact_role": "UNACCEPTED_SURFACE_DIAGNOSTIC" if args.surface_diagnostic_only else "MODELING_SEQUENCE_RESULT",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": success, "completed_steps": len(results), "report": str(args.report)}))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
