#!/usr/bin/env python3
"""Deterministic repository-hygiene audit for tracked project files."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_FILES = {".gitignore", ".mcp.json", "README.md", "addon.py"}
FORBIDDEN_TRACKED_NAMES = {".env", "gh_auth.log"}
FORBIDDEN_TRACKED_PARTS = {"__pycache__", ".pytest_cache"}
FORBIDDEN_TRACKED_SUFFIXES = {".blend1", ".pyc"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = {ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item}
    return sorted(path for path in paths if path.is_file())


def audit() -> dict:
    files = tracked_files()
    forbidden = []
    root_drift = []
    syntax_errors = []
    hashes: dict[tuple[str, int], list[str]] = defaultdict(list)

    for path in files:
        relative = path.relative_to(ROOT)
        relative_text = relative.as_posix()
        if (
            path.name in FORBIDDEN_TRACKED_NAMES
            or any(part in FORBIDDEN_TRACKED_PARTS for part in relative.parts)
            or path.suffix.lower() in FORBIDDEN_TRACKED_SUFFIXES
        ):
            forbidden.append(relative_text)
        if len(relative.parts) == 1 and path.name not in ALLOWED_ROOT_FILES:
            root_drift.append(relative_text)
        content = path.read_bytes()
        if content:
            hashes[(hashlib.sha256(content).hexdigest(), len(content))].append(relative_text)
        if path.suffix == ".py":
            try:
                compile(content, relative_text, "exec")
            except (SyntaxError, UnicodeError) as exc:
                syntax_errors.append(f"{relative_text}: {exc}")

    duplicate_groups = [
        {"bytes": size, "paths": paths}
        for (_, size), paths in sorted(hashes.items())
        if len(paths) > 1
    ]
    checks = {
        "no_forbidden_tracked_artifacts": not forbidden,
        "no_unclassified_root_files": not root_drift,
        "python_syntax_clean": not syntax_errors,
        "no_exact_duplicate_tracked_files": not duplicate_groups,
    }
    return {
        "tracked_file_count": len(files),
        "checks": checks,
        "forbidden_tracked_artifacts": forbidden,
        "unclassified_root_files": root_drift,
        "python_syntax_errors": syntax_errors,
        "exact_duplicate_groups": duplicate_groups,
        "pass": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    rendered = json.dumps(report, indent=2)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
