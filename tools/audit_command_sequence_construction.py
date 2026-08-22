"""Fail closed when a primary prop form has not progressed beyond primitive placement.

This audits the *typed command sequence* rather than guessing artistic intent from
the final mesh.  A cylinder, sphere, or cube may be a valid starting cage, but it
is not evidence of the connected edit-mode construction required for a continuous
manufactured form.  Promotion requires either an authored connected-profile cage
or a committed topology-changing decision on every declared primary form.

Usage:
    python tools/audit_command_sequence_construction.py SEQUENCE.json \
        --primary ClockShell_BLOCKOUT --output audit.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TOPOLOGY_OPERATIONS = {
    "extrude_selection",
    "inset_selection",
    "subdivide_selection",
    "bevel_selection",
    "delete_selection",
    "dissolve_selection",
    "merge_selection",
    "fill_selection",
    "bridge_selection",
    "spin_selection",
    "loop_cut_selection",
    "connect_vertex_path",
    "bisect_selection",
    "symmetrize_selection",
    "split_selection",
    "separate_selection",
    "replace_mesh_from_object",
}


def audit_sequence(sequence: list[dict[str, Any]], primary_names: list[str]) -> dict[str, Any]:
    """Return evidence and failures for declared continuous primary forms."""
    created_by: dict[str, str] = {}
    edited_by: dict[str, list[str]] = {}
    for step in sequence:
        command = step.get("command")
        params = step.get("params", {})
        if command in {"create_primitive", "create_curve", "create_revolved_profile", "create_profile_extrusion", "create_profile_loft", "create_quad_shell_grid", "create_quad_shell_sections", "create_quad_open_surface", "create_quad_annular_shell", "create_quad_layered_annular_shell", "create_authored_quad_mesh"}:
            name = params.get("name")
            if isinstance(name, str):
                created_by[name] = command
        transaction = step.get("transaction")
        if isinstance(transaction, dict):
            name = transaction.get("name")
            operation = transaction.get("operation")
            if isinstance(name, str) and operation in TOPOLOGY_OPERATIONS and transaction.get("accept", True):
                edited_by.setdefault(name, []).append(operation)

    forms = []
    failures = []
    for name in primary_names:
        origin = created_by.get(name)
        operations = edited_by.get(name, [])
        connected_profile = origin in {"create_revolved_profile", "create_profile_extrusion", "create_profile_loft", "create_quad_shell_grid", "create_quad_shell_sections", "create_quad_open_surface", "create_quad_annular_shell", "create_quad_layered_annular_shell", "create_authored_quad_mesh"}
        passed = connected_profile or bool(operations)
        entry = {
            "name": name,
            "origin": origin,
            "topology_operations": operations,
            "connected_profile_origin": connected_profile,
            "pass": passed,
        }
        forms.append(entry)
        if not passed:
            failures.append(
                f"{name}: no committed topology edit after {origin or 'an unknown origin'}"
            )
    return {
        "schema_version": 1,
        "record_type": "PRIMARY_FORM_CONSTRUCTION_AUDIT",
        "claim_boundary": "This verifies recorded construction evidence only; it does not judge visual resemblance or topology quality.",
        "primary_forms": forms,
        "pass": not failures,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequence", type=Path)
    parser.add_argument("--primary", action="append", required=True, dest="primary_names")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sequence = json.loads(args.sequence.read_text(encoding="utf-8"))
    if not isinstance(sequence, list):
        raise ValueError("sequence must be a JSON array")
    result = audit_sequence(sequence, args.primary_names)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "output": str(args.output)}))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
