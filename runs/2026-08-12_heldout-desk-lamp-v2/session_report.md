# Held-out articulated desk-lamp benchmark — second attempt, still rejected

## Status: REJECTED, but a real and measured improvement over the first attempt

The first attempt (`runs/2026-08-12_heldout-desk-lamp/`) never approached its frozen gates (best
mean IoU 0.4058) and its own conclusion named the fix: *"the next attempt must begin with explicit
side-view rail/frame landmarks and component proportions rather than broad manual span
adjustments."* This attempt does exactly that, and finds -- then fixes -- the actual root cause of
the first attempt's worst failure, but still does not pass.

## What was measured before building anything

`tools/measure_reference.py` was run against both `reference_side_mask.png` and
`reference_front_mask.png` (both already saved from the first attempt; the source GLTF was not
re-inspected). The row-by-row width profile gives precise pixel landmarks for every joint: shade
tip, shade rim, shade neck, upper-arm-to-shade mount, elbow, base joint, clamp. The front-view
profile's bounding box is only 117px wide against a 519px-tall silhouette (aspect ratio 0.225) --
confirming the whole mechanism is nearly planar, which is the fact the first attempt's "paired arm
rails placed across depth" mistake violated.

## The root-cause bug this attempt found and fixed

The first candidate script built the arm's zigzag skeleton in Blender's X-Z plane. That is *not*
the plane `render_silhouette`'s "side" view exposes -- "side" looks along +X (the YZ plane); "front"
looks along -Y (the XZ plane). Building in X-Z therefore made the full zigzag profile show up in
the **front** render and collapse to a nearly straight line in the **side** render -- the exact
inverse of the reference, where "side" is the full-profile view and "front" is the compressed one.
This is verifiable directly: the first draft of this script's own `candidate_side_mask.png` was a
thin vertical line and `candidate_front_mask.png` had the full zigzag, before the axis was swapped.

Rebuilding the same measured landmarks in the Y-Z plane instead (X reserved for the small
cross-axis thickness of twin rails and the damper cylinder) immediately produced the correct
front/side assignment and measurably improved the score:

| View | First attempt (best, v5) | This attempt (final) |
| --- | ---: | ---: |
| Front | 0.446008 | 0.328311 |
| Side | 0.222600 | 0.336009 |
| Top | 0.548928 | 0.586857 |
| Mean | 0.405845 | 0.417059 |

Side view improved from a near-total failure to a real (if still failing) score. Front view
regressed from the first attempt's landmark-tuned value, likely because that value came from five
rounds of direct row-landmark correction on a specific pose while this attempt's front-view
proportions (member thickness in particular) were only corrected once, by eye, against the
reference silhouette, not measured the same way the side-view skeleton was.

## Construction

All-quad `path_loft`/`ring_loft` continuous members (matching this repo's established pattern from
the watering can and other props) for: clamp post/foot, lower-arm main rail, a funnel piece
representing the scissor mechanism spreading toward the damper cylinder, the damper cylinder itself,
the elbow joint, upper-arm twin rail, the shade-mount joint, and a revolved frustum shade. No
primitive-assembly shortcuts; every part is a continuous authored member sized from the measured
landmarks, widened once after the first render showed low front-view recall (0.385) with decent
precision (0.599) -- meaning the whole candidate was too thin, not misplaced.

One real defect was found and fixed during this pass: the elbow and shade-mount joints were first
built with `ring_loft`, which assumes Z-axis stacking; used for an X-axis joint pin, its cap
triangulation produced 2 degenerate faces on each joint. Switched both to `path_loft`, which builds
tube frames from the actual path tangent regardless of axis. Independent fresh-process verification
now shows 0/10 objects with any non-manifold edges, degenerate faces, or loose vertices.

## What this does not establish

- Still fails all four frozen gates (front 0.68, side 0.70, top 0.58, mean 0.66) -- this is not a
  held-out pass and is not claimed as one.
- The scissor/tension mechanism is represented by one funnel + one damper cylinder, not the
  reference's actual crossed twin-rail lazy-tongs linkage; this is a genuine, disclosed
  simplification, not a hidden one.
- No UV/bake/export/named-engine production work was attempted, since the geometry itself has not
  cleared its visual gate yet.
- Component thickness was corrected by eye against the rendered silhouette, not by the same
  landmark-measurement rigor used for the joint positions; a further pass should measure member
  widths directly from the reference's row-profile data the same way the joint positions were.

## Why this is being published despite still failing

Every other correction in this session that mattered was published as real evidence whether or not
it fully passed -- the rejected desk lamp itself is one of those. This attempt's value is the
diagnosed and fixed root-cause bug (the front/side axis inversion), which is exactly the kind of
concrete, reproducible finding this project's evidence trail exists to preserve, not a status
upgrade to claim.
