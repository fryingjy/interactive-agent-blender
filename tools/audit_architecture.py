#!/usr/bin/env python3
"""Inventory the active tree and expose local Python dependency evidence.

The report is deliberately descriptive.  A zero-incoming module is not called
dead code automatically: command-line programs and Blender's sibling-import
bootstrap are modeled explicitly, and deletion decisions live in the human
reviewed consolidation report.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import subprocess
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
CLASSIFICATIONS = {
    "CORE_RUNTIME",
    "TEST_SUPPORT",
    "TOOL",
    "CURRENT_DOC",
    "CURRENT_KNOWLEDGE",
    "HISTORICAL",
    "DUPLICATED",
    "UNREFERENCED",
    "SUPERSEDED",
}
AUTHORITATIVE_ROOTS = {
    "blender_ops/modeler_server.py",
    "tools/modeler_mcp_server.py",
    "tools/modeling_pipeline.py",
    "tools/run_modeler_command_sequence.py",
    "tools/start_modeler_in_blender.py",
}
CLASSIFICATION_OVERRIDES = {
    "knowledge/skills/boolean-groove-cut-topology-cleanup.json": "HISTORICAL",
}


def git_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return sorted(
        Path(item.decode("utf-8")).as_posix()
        for item in result.stdout.split(b"\0")
        if item and (ROOT / Path(item.decode("utf-8"))).is_file()
    )


def module_name(path: str) -> str | None:
    candidate = Path(path)
    if candidate.suffix != ".py":
        return None
    parts = list(candidate.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _candidate_modules(node: ast.ImportFrom, current: str) -> Iterable[str]:
    package = current.split(".")[:-1]
    if node.level:
        base = package[: max(0, len(package) - node.level + 1)]
        if node.module:
            base.extend(node.module.split("."))
        yield ".".join(base)
    elif node.module:
        yield node.module


def import_graph(paths: list[str]) -> tuple[dict[str, list[str]], list[dict[str, str]]]:
    module_to_path = {
        name: path for path in paths if (name := module_name(path)) is not None
    }
    graph: dict[str, set[str]] = defaultdict(set)
    errors: list[dict[str, str]] = []
    for path in paths:
        current = module_name(path)
        if current is None:
            continue
        try:
            tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
        except (SyntaxError, UnicodeError) as exc:
            errors.append({"path": path, "error": str(exc)})
            continue
        raw: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                raw.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                raw.update(_candidate_modules(node, current))
        current_dir = Path(path).parent.as_posix().replace("/", ".")
        for imported in raw:
            choices = [imported]
            # blender_ops/modeler_server.py intentionally adds its own directory
            # to sys.path before importing sibling modules by their bare names.
            if "." not in imported and current_dir != ".":
                choices.insert(0, f"{current_dir}.{imported}")
            for choice in choices:
                if choice in module_to_path:
                    graph[path].add(module_to_path[choice])
                    break
                package_init = choice + ".__init__"
                if package_init in module_to_path:
                    graph[path].add(module_to_path[package_init])
                    break
    return {key: sorted(value) for key, value in sorted(graph.items())}, errors


def reachable(graph: dict[str, list[str]], roots: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    queue = deque(root for root in roots if (ROOT / root).exists())
    while queue:
        path = queue.popleft()
        if path in seen:
            continue
        seen.add(path)
        queue.extend(graph.get(path, []))
    return seen


def default_classification(path: str) -> str:
    if path in CLASSIFICATION_OVERRIDES:
        return CLASSIFICATION_OVERRIDES[path]
    parts = Path(path).parts
    suffix = Path(path).suffix.lower()
    if parts[0] in {"modeling_core", "blender_ops"}:
        return "CORE_RUNTIME"
    if parts[0] == "tests" or parts[0] == "reference":
        return "TEST_SUPPORT"
    if parts[0] == "tools" or parts[0] == "requirements":
        return "TOOL"
    if parts[0] == "knowledge_engine" or parts[0] == "knowledge":
        return "CURRENT_KNOWLEDGE"
    if parts[0] == "docs" or suffix == ".md":
        return "CURRENT_DOC"
    if path in {".mcp.json", ".gitignore"}:
        return "CORE_RUNTIME"
    return "CURRENT_DOC"


def classification_reason(path: str, classification: str) -> str:
    if path in CLASSIFICATION_OVERRIDES:
        return {
            "knowledge/skills/boolean-groove-cut-topology-cleanup.json": "negative evidence retained but status-gated out of runtime retrieval",
        }[path]
    return {
        "CORE_RUNTIME": "member of the authoritative shape-solving or typed Blender execution path",
        "TEST_SUPPORT": "test, deterministic fixture, or redistributable neutral reference",
        "TOOL": "CLI, verifier, audit, launcher, or optional dependency declaration",
        "CURRENT_DOC": "current repository or architecture documentation",
        "CURRENT_KNOWLEDGE": "research, review, retrieval, learning policy, or curated knowledge",
        "HISTORICAL": "retained negative evidence outside runtime retrieval",
    }[classification]


def audit() -> dict[str, object]:
    paths = git_paths()
    graph, parse_errors = import_graph(paths)
    production_graph = {
        source: [target for target in targets if not target.startswith("tests/")]
        for source, targets in graph.items()
        if not source.startswith("tests/")
    }
    authority_reachable = reachable(production_graph, AUTHORITATIVE_ROOTS)
    incoming_production: dict[str, list[str]] = defaultdict(list)
    incoming_tests: dict[str, list[str]] = defaultdict(list)
    for source, targets in graph.items():
        for target in targets:
            destination = incoming_tests if source.startswith("tests/") else incoming_production
            destination[target].append(source)
    records = []
    for path in paths:
        classification = default_classification(path)
        if classification not in CLASSIFICATIONS:
            raise AssertionError(classification)
        records.append(
            {
                "path": path,
                "classification": classification,
                "classification_reason": classification_reason(path, classification),
                "python_module": module_name(path),
                "imports": graph.get(path, []),
                "production_importers": sorted(incoming_production.get(path, [])),
                "test_importers": sorted(incoming_tests.get(path, [])),
                "reachable_from_authoritative_roots": path in authority_reachable,
                "entrypoint": path in AUTHORITATIVE_ROOTS
                or (Path(path).suffix == ".py" and path.startswith("tools/")),
            }
        )
    counts = Counter(record["classification"] for record in records)
    return {
        "schema_version": 1,
        "record_type": "ACTIVE_TREE_ARCHITECTURE_AUDIT",
        "authoritative_pipeline": [
            "reference",
            "evidence",
            "components/correspondence",
            "cameras",
            "competing shape hypotheses",
            "fit",
            "compile",
            "typed Blender",
            "inspect",
            "diagnose/refit/rebuild",
        ],
        "authoritative_roots": sorted(AUTHORITATIVE_ROOTS),
        "tracked_file_count": len(paths),
        "python_file_count": sum(Path(path).suffix == ".py" for path in paths),
        "classification_counts": dict(sorted(counts.items())),
        "parse_errors": parse_errors,
        "files": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not report["parse_errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
