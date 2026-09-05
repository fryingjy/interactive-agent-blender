#!/usr/bin/env python3
"""Deterministic repository-hygiene audit for tracked project files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_FILES = {".gitignore", ".mcp.json", "README.md"}
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


def missing_document_links(path: Path, root: Path) -> list[dict[str, str]]:
    """Check file destinations in Markdown links, not prose/code example paths.

    Handles inline links and reference definitions; excludes fenced/inline code.
    Fragment existence and remote availability are deliberately outside this audit.
    """
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", content)
    content = re.sub(r"(`+).*?\1", "", content)
    destinations = re.findall(r"\]\(\s*(<[^>]+>|[^\s)]+)", content)
    destinations += re.findall(r"(?m)^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)", content)
    missing = []
    for destination in sorted(set(destinations)):
        destination = destination.strip("<>")
        parsed = urlsplit(destination)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        target = unquote(parsed.path)
        resolved = (root / target.lstrip("/") if target.startswith("/") else path.parent / target).resolve()
        if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
            missing.append({"document": path.relative_to(root).as_posix(), "destination": destination})
    return missing


def audit() -> dict:
    files = tracked_files()
    forbidden = []
    root_drift = []
    syntax_errors = []
    broken_links = []
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
        if path.suffix == ".md" and (relative.parts[0] == "docs" or relative_text == "README.md"):
            broken_links.extend(missing_document_links(path, ROOT))

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
        "current_document_file_links_resolve": not broken_links,
    }
    return {
        "tracked_file_count": len(files),
        "checks": checks,
        "forbidden_tracked_artifacts": forbidden,
        "unclassified_root_files": root_drift,
        "python_syntax_errors": syntax_errors,
        "exact_duplicate_groups": duplicate_groups,
        "broken_current_document_links": broken_links,
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
