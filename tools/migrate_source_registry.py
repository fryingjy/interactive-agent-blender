"""Normalize the historical source registry to the directive's v2 schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def creator_for(record: dict) -> str:
    source_id = record.get("source_id", "")
    if source_id.startswith("blender-manual") or source_id.startswith("blender-api"):
        return "Blender Foundation"
    if source_id.startswith("blenderguru"):
        return "Andrew Price / Blender Guru"
    if source_id.startswith("cgcookie"):
        return "CG Cookie"
    if source_id.startswith("blenderartists"):
        return "Blender Artists community"
    if source_id.startswith("youtube"):
        return "mixed creators"
    return record.get("creator", "unknown")


def access_for(record: dict) -> dict[str, bool]:
    modalities = " ".join(record.get("modalities_inspected", [])).lower()
    return {
        "text": "text" in modalities,
        "video": "video" in modalities or "video_frames" in modalities,
        "audio": "audio" in modalities,
        "captions": "caption" in modalities or "transcript" in modalities,
    }


def normalize(record: dict) -> dict:
    known = {
        "source_id", "title", "url", "type", "trust_tier", "version_scope",
        "topics", "modalities_inspected", "status", "rejection_reason", "creator",
    }
    return {
        "id": record.get("id") or record.get("source_id"),
        "url": record.get("url"),
        "local_path": record.get("local_path"),
        "title": record.get("title", "Untitled"),
        "creator": creator_for(record),
        "source_type": record.get("source_type") or record.get("type", "unknown"),
        "trust_tier": record.get("trust_tier", "D"),
        "version": record.get("version") or record.get("version_scope", "unknown"),
        "topics": record.get("topics", []),
        "access": record.get("access") or access_for(record),
        "status": record.get("status", "QUEUED"),
        "rejected_reason": record.get("rejected_reason") or record.get("rejection_reason"),
        "modalities_inspected": record.get("modalities_inspected", []),
        "metadata": {
            key: value for key, value in record.items()
            if key not in known and key not in {"id", "local_path", "source_type", "version", "access", "metadata"}
        } | record.get("metadata", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("registry")
    args = parser.parse_args()
    path = Path(args.registry)
    records = json.loads(path.read_text(encoding="utf-8"))
    normalized = [normalize(record) for record in records]
    path.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
    print(f"normalized {len(normalized)} sources")


if __name__ == "__main__":
    main()
