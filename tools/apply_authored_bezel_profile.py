"""Replace the magnifier's torus ring placeholder with an authored, revolved bezel profile.

Why: the blockout used a torus primitive for the bezel. Two independent lines of evidence say
that is the wrong primary form:

  1. Patent literature on lens retention describes bezel cross-sections as channel/step profiles
     ("dihedral or of other kinds, such as half-round") that grip a lens edge -- not round tubes.
  2. Direct high-magnification inspection of this build's own primary reference
     (runs/2026-08-18_magnifying-glass-reference/ref_front_oblique_round_lens.jpg) shows a thin
     flat band with a stepped inner lip and a knurled outer edge. A torus reads as a fat rounded
     doughnut in silhouette; the reference plainly does not.

The frozen contract had already specified "a torus-LIKE revolved profile ... not a primitive torus
directly, so the rim bevel can be a deliberate, typed decision". The blockout took a shortcut to the
primitive. This restores the contract's intent rather than changing it.

Cross-section measured from the reference: the chrome band is ~4.7% of ring diameter in radial
thickness, i.e. ~0.42cm on the 9cm ring. Axial depth is read as slightly less than twice that.
The profile is deliberately left with square corners so the rim treatment stays an explicit later
decision, exactly as the contract requires.

Run:
    blender --background --factory-startup --python tools/apply_authored_bezel_profile.py -- IN.blend OUT_DIR
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "blender_ops"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import profile_mesh  # noqa: E402

RING_OUTER = 4.50   # cm, ring outer radius (9cm outer diameter, from the frozen contract)
BAND_RADIAL = 0.42  # cm, measured: ~4.7% of ring diameter
AXIAL_HALF = 0.35   # cm, half the band's axial depth
RING_CENTRE_Z = 16.25


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:]
    in_blend, out_dir = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(in_blend))

    removed = None
    for name in ("MagnifierRing", "MagnifierBezel"):
        obj = bpy.data.objects.get(name)
        if obj:
            removed = name
            bpy.data.objects.remove(obj, do_unlink=True)

    # Startup-scene hygiene. The live GUI session began from Blender's default startup file and
    # its default Cube was never deleted, so it sat at the origin inside the handle's base for the
    # whole blockout. It never reached any measurement or review render, because
    # render_diagnostic_pass renders only the object names it is given -- but it WAS in the saved
    # .blend, and a whole-scene render (render_blend_beauty) exposed it immediately. Caught by
    # visual inspection; mesh-health checks could never flag it, since a default cube is perfectly
    # manifold. Removed here, and named rather than quietly dropped.
    stray = [o.name for o in list(bpy.data.objects)
             if o.type == "MESH" and not o.name.startswith("Magnifier")]
    for name in stray:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    inner = RING_OUTER - BAND_RADIAL
    profile = [
        (inner,      -AXIAL_HALF),
        (RING_OUTER, -AXIAL_HALF),
        (RING_OUTER,  AXIAL_HALF),
        (inner,       AXIAL_HALF),
    ]
    bezel = profile_mesh.revolve_closed_profile("MagnifierBezel", profile, segments=48)
    # stand the ring into the handle's plane, then seat it above the neck
    bezel.rotation_euler = (math.pi / 2, 0, 0)
    bezel.location = (0, 0, RING_CENTRE_Z)
    bpy.context.view_layer.update()

    me = bezel.data
    sizes = [len(p.vertices) for p in me.polygons]
    report = {
        "replaced": removed,
        "stray_startup_objects_removed": stray,
        "profile_radius_axial": profile,
        "band_radial_thickness_cm": BAND_RADIAL,
        "ring_outer_radius_cm": RING_OUTER,
        "lens_aperture_radius_cm": inner,
        "bezel": {
            "vertices": len(me.vertices),
            "faces": len(me.polygons),
            "quads": sum(1 for s in sizes if s == 4),
            "triangles": sum(1 for s in sizes if s == 3),
            "ngons": sum(1 for s in sizes if s > 4),
        },
        "evidence": [
            "patent literature: lens bezels are channel/step profiles, not round tubes",
            "direct magnified inspection of ref_front_oblique_round_lens.jpg shows a flat band "
            "with a stepped inner lip and knurled outer edge",
        ],
        "claim_boundary": (
            "This corrects the bezel's PRIMARY FORM only. The knurled outer edge and the inner "
            "lens-retaining step are deliberately not modelled at blockout stage; the square rim "
            "corners are left for an explicit later bevel decision, per the frozen contract."
        ),
    }
    out = out_dir / "magnifier_authored_bezel.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    report["blend_path"] = str(out)
    (out_dir / "authored_bezel_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
