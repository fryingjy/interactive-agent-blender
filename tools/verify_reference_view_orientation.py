"""Pre-modeling orientation check: confirm which world plane a reference's
"wide/full-profile" view actually corresponds to, BEFORE building real
geometry in it.

Why this exists: the desk-lamp benchmark's second attempt
(runs/2026-08-12_heldout-desk-lamp-v2/) found that its first attempt built
the arm skeleton in Blender's X-Z plane, but render_silhouette's "side" view
looks along +X (exposing the Y-Z plane) and "front" looks along -Y (exposing
the X-Z plane) -- exactly backwards from what was built. That single mistake
alone produced a side-view IoU near zero (0.0045 at one point) and was only
caught after full construction, multiple failed candidates, and hours of
work. This tool generalizes the fix: build a trivial, cheap proxy shape
elongated along the *intended* in-plane axis, render it through the same
render_silhouette pipeline used for real evidence, and compare which view
comes out wide vs narrow against the reference's own measured aspect ratios
-- catching an axis mismatch in seconds, before any real construction time
is spent.

This does not replace measure_reference.py (which measures the reference
itself) or real modeling judgment -- it only confirms the *plane assignment*
is not inverted before landmark-based construction begins.

CORRECTION (found live, hand-plane benchmark, 2026-08-13): the original
version of this tool only checked that --in-plane-axis and --wide-view were
self-consistent with EACH OTHER -- it never compared the claimed --wide-view
against the reference's own measured aspect ratios (already printed in
reference_aspect_ratios, just never checked). That meant a wrong but
mutually-consistent pair could still report "orientation_consistent: true".
This happened for real: the hand plane's reference is wider in "front"
(aspect 1.67) than "side" (aspect 0.43), but this tool was first run with
--in-plane-axis Y --wide-view side, which is internally self-consistent and
passed, despite side being the WRONG view. main() now runs two independent
checks -- probe self-consistency (original) and claim-vs-reference (new) --
and both must agree for a pass.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from render_passes import render_silhouette  # noqa: E402


def mask_bbox_aspect(path: Path):
    """Reuses the same non-background bounding-box logic as measure_reference.py,
    via Blender's own image loading (no external dependency needed inside bpy)."""
    img = bpy.data.images.load(str(path))
    w, h = img.size
    pixels = list(img.pixels)  # RGBA flat, bottom-to-top rows
    channels = img.channels
    min_x, max_x, min_y, max_y = w, -1, h, -1
    found = False
    for y in range(h):
        row_has_content = False
        for x in range(w):
            idx = (y * w + x) * channels
            # Non-background: either has alpha and is opaque, or is dark
            # enough to be foreground on a light/transparent background.
            if channels == 4:
                is_fg = pixels[idx + 3] > 0.5
            else:
                luminance = pixels[idx]
                is_fg = luminance < 0.9
            if is_fg:
                found = True
                row_has_content = True
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
        if row_has_content:
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y
    bpy.data.images.remove(img)
    if not found:
        raise SystemExit(f"{path} appears to be entirely background")
    bw = max_x - min_x + 1
    bh = max_y - min_y + 1
    return bw / bh


def build_axis_probe(in_plane_axis: str, name="AxisProbe"):
    """A single elongated, asymmetric box: long along `in_plane_axis`, short on
    the other two, so its silhouette is unambiguously wide in whichever view
    looks perpendicular to that axis and narrow in the view that looks along it."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name = name
    scale = {"X": (3.0, 0.05, 0.5), "Y": (0.05, 3.0, 0.5), "Z": (0.5, 0.5, 3.0)}[in_plane_axis]
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_dir", type=Path, help="directory containing reference_<view>_mask.png files")
    parser.add_argument("--in-plane-axis", choices=["X", "Y", "Z"], required=True,
                         help="the world axis the modeler intends to build the reference's 'wide' silhouette detail along")
    parser.add_argument("--wide-view", choices=["front", "side", "top"], required=True,
                         help="which reference view is measured to be the WIDE/full-detail one (higher aspect ratio, or visually the fuller silhouette)")
    parser.add_argument("--out", type=Path, default=None)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    args.reference_dir = args.reference_dir.resolve()

    out = args.out or (ROOT / "runs" / "_orientation_probe_scratch")
    out.mkdir(parents=True, exist_ok=True)

    ref_aspects = {}
    for view in ("front", "side", "top"):
        p = args.reference_dir / f"reference_{view}_mask.png"
        if p.exists():
            ref_aspects[view] = mask_bbox_aspect(p)

    build_axis_probe(args.in_plane_axis)
    probe_aspects = {}
    for view in ("front", "side", "top"):
        mask_path = out / f"probe_{view}_mask.png"
        render_silhouette("AxisProbe", str(mask_path), view=view, resolution=256)
        probe_aspects[view] = mask_bbox_aspect(mask_path)

    # Top view is deliberately excluded from the "which is widest" decision:
    # the probe's cross-section on the two non-elongated axes is not equal
    # (X/Y are both thin, but Z is a medium 0.5), so top's aspect ratio is
    # trivially extreme regardless of which axis was tested and would always
    # "win" a raw max() comparison -- it doesn't distinguish the actual
    # front-vs-side confusion this tool exists to catch (the desk lamp's
    # actual failure mode). Only compare front vs side directly.
    front_wider = probe_aspects["front"] > probe_aspects["side"]
    empirically_wide_view = "front" if front_wider else "side"
    if args.wide_view == "top":
        probe_ok = None  # not this tool's designed comparison; report data only
    else:
        probe_ok = empirically_wide_view == args.wide_view

    # CORRECTION (found live, hand-plane benchmark, 2026-08-13): the check
    # above only verifies that --in-plane-axis and --wide-view are SELF-
    # CONSISTENT with each other -- it says nothing about whether --wide-view
    # actually matches the reference. It is possible to pass a wrong but
    # mutually-consistent pair (e.g. claim "side" is wide when the reference
    # itself is wider in "front") and have probe_ok report True, because the
    # probe only checks its own geometry, never ref_aspects. That is exactly
    # what happened here: the reference's own reference_aspect_ratios (printed
    # below) showed front=1.6708 > side=0.4286 -- front is the reference's
    # real wide view -- but this tool was first run with --wide-view side and
    # reported "consistent: true" anyway, because axis Y and wide-view side
    # are indeed self-consistent, just both wrong for this reference. This
    # second check closes that gap: it compares the reference's OWN measured
    # front/side aspect ratios directly against the claimed --wide-view,
    # independent of the probe.
    if "front" in ref_aspects and "side" in ref_aspects and args.wide_view in ("front", "side"):
        ref_front_wider = ref_aspects["front"] > ref_aspects["side"]
        ref_empirically_wide_view = "front" if ref_front_wider else "side"
        reference_ok = ref_empirically_wide_view == args.wide_view
    else:
        ref_empirically_wide_view = None
        reference_ok = None

    ok = probe_ok if reference_ok is None else (bool(probe_ok) and reference_ok)

    report = {
        "reference_dir": str(args.reference_dir),
        "in_plane_axis_tested": args.in_plane_axis,
        "claimed_wide_view": args.wide_view,
        "reference_aspect_ratios": ref_aspects,
        "probe_aspect_ratios": probe_aspects,
        "probe_empirically_wider_of_front_vs_side": empirically_wide_view,
        "probe_self_consistent": probe_ok,
        "reference_empirically_wider_of_front_vs_side": ref_empirically_wide_view,
        "claim_matches_reference": reference_ok,
        "orientation_consistent": ok,
    }
    print(json.dumps(report, indent=2))
    if probe_ok is None:
        print("\n--wide-view top is informational only; this tool's empirical check compares front vs side.", file=sys.stderr)
    if probe_ok is False:
        print(
            f"\nORIENTATION MISMATCH (axis/claim self-consistency): building the reference's "
            f"detail along world axis {args.in_plane_axis!r} makes it wider in the "
            f"{empirically_wide_view!r} render, not {args.wide_view!r} as claimed. Do not proceed "
            f"with construction on this axis assignment -- this is the exact bug that produced "
            f"the desk lamp's near-zero side-view IoU.",
            file=sys.stderr,
        )
    if reference_ok is False:
        print(
            f"\nORIENTATION MISMATCH (claim vs. actual reference): the reference's own measured "
            f"aspect ratios show {ref_empirically_wide_view!r} is the wider view "
            f"(front={ref_aspects.get('front')!r}, side={ref_aspects.get('side')!r}), not "
            f"{args.wide_view!r} as claimed. A self-consistent axis/wide-view pair is not enough "
            f"if the claimed wide-view itself is wrong -- re-check reference_aspect_ratios above "
            f"before picking parameters.",
            file=sys.stderr,
        )
    raise SystemExit(0 if ok in (True, None) else 1)


if __name__ == "__main__":
    main()
