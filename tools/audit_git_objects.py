#!/usr/bin/env python3
"""Measure reachable Git blobs without changing repository history."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        input=input_bytes,
        capture_output=True,
    ).stdout


def object_paths() -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for line in run("rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines():
        oid, separator, path = line.partition(" ")
        if separator and path:
            result[oid].add(Path(path).as_posix())
    return result


def object_sizes(oids: list[str]) -> dict[str, int]:
    request = "".join(f"{oid}\n" for oid in oids).encode("ascii")
    response = run("cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)", input_bytes=request)
    result = {}
    for line in response.decode("ascii", "replace").splitlines():
        oid, kind, raw_size = line.split()
        if kind == "blob":
            result[oid] = int(raw_size)
    return result


def current_blob_ids() -> set[str]:
    return {
        line.split()[2]
        for line in run("ls-tree", "-r", "HEAD").decode("utf-8", "replace").splitlines()
        if len(line.split()) >= 3 and line.split()[1] == "blob"
    }


def audit() -> dict[str, object]:
    paths = object_paths()
    sizes = object_sizes(sorted(paths))
    current = current_blob_ids()
    total = sum(sizes.values())
    current_bytes = sum(size for oid, size in sizes.items() if oid in current)
    deleted_only = total - current_bytes
    path_group_bytes: Counter[str] = Counter()
    extension_bytes: Counter[str] = Counter()
    historical_media_bytes = 0
    media_suffixes = {".blend", ".blend1", ".png", ".jpg", ".jpeg", ".webp", ".avif", ".mp4", ".mov", ".mkv", ".glb", ".gltf", ".html"}
    for oid, size in sizes.items():
        representative = sorted(paths[oid])[0]
        top = representative.split("/", 1)[0]
        path_group_bytes[top] += size
        suffix = Path(representative).suffix.lower() or "[none]"
        extension_bytes[suffix] += size
        if oid not in current and (top == "runs" or suffix in media_suffixes):
            historical_media_bytes += size
    largest = [
        {
            "oid": oid,
            "bytes": sizes[oid],
            "current": oid in current,
            "paths": sorted(paths[oid]),
        }
        for oid in sorted(sizes, key=sizes.get, reverse=True)[:75]
    ]
    return {
        "schema_version": 1,
        "record_type": "GIT_OBJECT_SIZE_AUDIT",
        "audited_head": run("rev-parse", "HEAD").decode("ascii").strip(),
        "reachable_blob_count": len(sizes),
        "reachable_blob_bytes": total,
        "current_blob_bytes": current_bytes,
        "deleted_only_blob_bytes": deleted_only,
        "deleted_only_fraction": deleted_only / total if total else 0.0,
        "deleted_historical_media_bytes": historical_media_bytes,
        "deleted_historical_media_fraction": historical_media_bytes / total if total else 0.0,
        "bytes_by_first_path_component": dict(path_group_bytes.most_common()),
        "bytes_by_representative_extension": dict(extension_bytes.most_common()),
        "largest_blobs": largest,
        "history_rewrite_performed": False,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
