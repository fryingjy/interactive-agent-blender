"""CLI for one-view or manifest-driven silhouette comparison."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.visual_compare import compare_image_files, compare_views


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", nargs="?")
    parser.add_argument("candidate", nargs="?")
    parser.add_argument("--manifest")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        report = compare_views({name: (pair["reference"], pair["candidate"]) for name, pair in manifest.items()})
    elif args.reference and args.candidate:
        report = compare_image_files(args.reference, args.candidate)
    else:
        parser.error("provide reference/candidate or --manifest")
    text = json.dumps(report, indent=2)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
