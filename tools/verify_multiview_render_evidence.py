"""Fail closed on blank or duplicated render evidence before visual review.

This checks only capture integrity (visible signal and distinct declared views),
not whether a model resembles its reference.  A nonblank render is necessary
but never sufficient visual evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def inspect_view(view_id: str, path: Path, *, foreground_threshold: int = 8) -> dict:
    if not path.is_file():
        return {"view_id": view_id, "path": str(path), "exists": False}
    image = Image.open(path).convert("RGBA")
    pixels = list(image.get_flattened_data())
    # Workbench references in this repository commonly use a black background;
    # transparent silhouette renders are recognized through alpha as well.
    foreground = sum(
        1 for red, green, blue, alpha in pixels
        if alpha > foreground_threshold and max(red, green, blue) > foreground_threshold
    )
    total = max(len(pixels), 1)
    digest = hashlib.sha256(image.tobytes()).hexdigest()
    return {
        "view_id": view_id,
        "path": str(path),
        "exists": True,
        "resolution": list(image.size),
        "foreground_pixels": foreground,
        "foreground_ratio": foreground / total,
        "pixel_sha256": digest,
    }


def evaluate(views: list[tuple[str, Path]], *, minimum_ratio: float = 0.001) -> dict:
    inspected = [inspect_view(view_id, path) for view_id, path in views]
    missing = [item["view_id"] for item in inspected if not item["exists"]]
    blank = [item["view_id"] for item in inspected if item.get("exists") and item["foreground_ratio"] < minimum_ratio]
    digests: dict[str, list[str]] = {}
    for item in inspected:
        if item.get("exists"):
            digests.setdefault(item["pixel_sha256"], []).append(item["view_id"])
    duplicate_groups = [ids for ids in digests.values() if len(ids) > 1]
    return {
        "schema_version": 1,
        "record_type": "MULTIVIEW_RENDER_EVIDENCE_PREFLIGHT",
        "claim_boundary": "Validates nonblank, distinct capture evidence only; it does not measure visual fidelity or approve a modeling stage.",
        "minimum_foreground_ratio": minimum_ratio,
        "views": inspected,
        "missing_views": missing,
        "blank_views": blank,
        "duplicate_view_groups": duplicate_groups,
        "pass": not missing and not blank and not duplicate_groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", action="append", required=True, metavar="ID=PATH")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-ratio", type=float, default=0.001)
    args = parser.parse_args()
    views = []
    for value in args.view:
        if "=" not in value:
            raise ValueError("each --view must be ID=PATH")
        view_id, raw_path = value.split("=", 1)
        views.append((view_id, Path(raw_path)))
    report = evaluate(views, minimum_ratio=args.minimum_ratio)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "blank_views": report["blank_views"], "output": str(args.output)}))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
