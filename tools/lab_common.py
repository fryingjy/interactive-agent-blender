"""Shared sys.path setup for tools/run_*.py Blender lab scripts.

Every lab script needs the repo root and blender_ops importable before it can
`import mesh_ops`, `import object_ops`, etc. That boilerplate was previously
duplicated by hand in each script with several slightly different forms.
"""

from __future__ import annotations

import sys
from pathlib import Path


def add_repo_paths(script_file: str) -> tuple[Path, Path]:
    """Ensure the repo root and blender_ops are importable; return (root, ops)."""
    root = Path(script_file).resolve().parents[1]
    ops = root / "blender_ops"
    for path in (root, ops):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    return root, ops
