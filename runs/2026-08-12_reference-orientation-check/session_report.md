# Pre-modeling reference view-orientation check

## Why

The desk lamp's first attempt (`runs/2026-08-12_heldout-desk-lamp/`) built its full arm skeleton in
Blender's X-Z plane. `render_silhouette`'s "side" view looks along +X (exposing the Y-Z plane) and
"front" looks along -Y (exposing the X-Z plane) -- the opposite of what the candidate assumed. The
result was a side-view IoU as low as 0.0045, indistinguishable from a genuine proportion failure
until the axes were checked directly, and only discovered after the entire candidate was built,
rendered, and measured.

This is not a desk-lamp-specific bug. Per the takeover directive's own framing (`Bad: hard-code the
desk lamp's correct axis. Good: improve reference/view analysis so the agent determines the
orientation relationship between reference views and Blender cameras before modeling.`), the general
capability gap is: nothing in this repository checked the plane assignment *before* investing in
full construction. This closes that gap with a reusable, cheap, empirical check rather than a
one-off fix.

## What was built

`tools/verify_reference_view_orientation.py`. Given a reference mask directory and a claimed
`--in-plane-axis` / `--wide-view` pairing, it:

1. Builds a trivial, cheap proxy (a single elongated box, not the real asset) scaled long along the
   claimed axis.
2. Renders it through the same `render_silhouette` pipeline real evidence uses, at low resolution
   (256px) for speed.
3. Compares the proxy's front-vs-side silhouette aspect ratio (top is excluded from this specific
   comparison -- see the tool's own comments for why a thin proxy's top-view ratio is trivially
   extreme regardless of the tested axis, and doesn't distinguish the front/side confusion this tool
   targets).
4. Fails loudly, before any real geometry exists, if the claimed wide view doesn't match what the
   proxy actually renders as wider.

## Validation: does it actually catch the real bug?

Run twice against `runs/2026-08-12_heldout-desk-lamp/reference/`, once with each candidate's actual
axis choice:

| Run | `--in-plane-axis` | `--wide-view` | Result |
| --- | --- | --- | --- |
| `x_axis_mismatch_output.log` | X (first candidate's actual choice) | side | **FAILS** (exit 1) -- probe reads wider in `front`, not `side` |
| `y_axis_consistent_output.log` | Y (second candidate's actual, corrected choice) | side | **PASSES** (exit 0) -- probe reads wider in `side`, matching |

This is direct empirical proof, not a claim: the exact bug that cost the first desk-lamp attempt a
full failed construction cycle is caught by this tool in about 5-8 seconds, before any real geometry
is built. `knowledge/foundation/operator_cards/visual_reference_comparison.md` now documents this as
step 0 of the reference-analysis procedure for any future asymmetric or articulated asset.

## What this does not establish

- This only checks plane assignment (which axis is "in-plane" vs "compressed"). It does not check
  sign/handedness (whether the detail should face +X or -X within the correct plane), scale, or any
  other proportion property -- those remain the job of the existing landmark-measurement workflow
  (`tools/measure_reference.py`) and multi-view IoU comparison.
- It has only been run retroactively against one already-known case (the desk lamp) so far. Its
  first prospective use, on a genuinely new asset before construction begins, is the real test of
  whether it changes runtime behavior rather than just documenting a lesson.
