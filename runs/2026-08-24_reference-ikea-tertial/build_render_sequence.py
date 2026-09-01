"""Generate deterministic diagnostic passes for the current TERTIAL blockout."""

from __future__ import annotations

import json
from pathlib import Path


OUT = Path(__file__).resolve().parent
REVISION = "v15"
OBJECTS = [
    "ShadeShell", "SocketHousing", "HeadYoke", "UpperArmBar_A", "UpperArmBar_B",
    "ElbowPlate", "LowerArmBar_A", "LowerArmBar_B", "BaseClamp", "BaseBushing",
    "BaseClampLowerJaw", "UpperSpring_Front", "UpperSpring_Rear", "LowerSpring_Front",
    "LowerSpring_Rear", "BasePivot", "ElbowPivot", "HeadPivot", "ClampScrew", "ClampHandle",
    "PowerCable",
]


def diagnostic(label: str, suffix: str, pass_type: str, view: str, margin: float, **extra: object) -> dict:
    params = {
        "name": OBJECTS,
        "frame_name": OBJECTS,
        "output_path": str((OUT / f"blockout_{REVISION}_{suffix}.png").resolve()),
        "pass_type": pass_type,
        "view": view,
        "resolution": 768,
        "margin": margin,
        **extra,
    }
    return {"label": label, "command": "render_diagnostic_pass", "params": params}


sequence = [
    diagnostic("render_front_solid", "front_solid", "solid", "front", 1.08),
    diagnostic("render_front_wireframe", "front_wireframe", "wireframe", "front", 1.08),
    diagnostic("render_isometric_solid", "isometric_solid", "solid", "isometric", 1.12),
    {
        "label": "render_front_silhouette",
        "command": "render_silhouette",
        "params": {
            "name": OBJECTS,
            "frame_name": OBJECTS,
            "output_path": str((OUT / f"blockout_{REVISION}_front_silhouette.png").resolve()),
            "view": "front",
            "resolution": 768,
            "margin": 1.08,
        },
    },
    diagnostic(
        "render_front_semantic_smooth_preview",
        "front_semantic_preview",
        "solid",
        "front",
        1.08,
        preview_smooth_names=[
            "ShadeShell", "SocketHousing", "BasePivot", "ElbowPivot", "HeadPivot",
            "ClampScrew", "ClampHandle", "PowerCable",
        ],
    ),
]

(OUT / "render_blockout_sequence.json").write_text(json.dumps(sequence, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"revision": REVISION, "passes": len(sequence), "objects": len(OBJECTS)}, indent=2))
