# Skill-building build #2: simple drinking glass (tumbler)

**Purpose (2026-08-14):** second entry in the bottom-up modeling curriculum started with the
slatted crate (`runs/2026-08-14_simple-crate/`). Deliberately chosen to be structurally different
from the crate -- a single revolved (curved) shell instead of a box-primitive multi-part assembly --
to test whether the "start simple, verify visually, don't trust automated checks alone" discipline
actually transfers, per `docs/MASTER_DIRECTIVE.md` Section 19a and this project's own repeated
"one successful asset is not generalization" lesson.

## Reference

`reference/cooler_glass_tumbler.svg` -- a CC0 vector illustration ("Cooler Glass (Tumbler)") from
Wikimedia Commons (`en.wikipedia.org/wiki/Tumbler_(glass)`), downloaded 2026-08-14 with explicit
user permission. License confirmed directly from the Commons file page: CC0 1.0 Universal Public
Domain Dedication.

## What the reference actually shows, and a disclosed extraction limitation

Wikipedia's own caption: "an oversized tumbler for serving chilled beverages, depicted as a
flat-bottomed drinking glass." The SVG's outer canvas is 247.317 x 477 px, confirmed by importing
it into Blender as curves and reading back real coordinate bounds (0.0697m x 0.1346m at Blender's
default SVG import scale) -- a width:height ratio of roughly 1:1.93, i.e. notably taller than wide,
consistent with a tall cooler-style tumbler rather than a squat rocks glass.

Attempted to extract the precise wall-taper profile directly from the SVG's vector path
coordinates (the same measured-reference discipline used elsewhere in this project) by importing
the file into a fresh headless Blender process and sampling curve point coordinates per path. This
did not work cleanly: the illustration is built from many overlapping near-white tonal fill regions
(hex colors like `#fcfcfc` and `#f2f2f2`, differing by only a few percent in lightness) representing
soft glass-highlight shading rather than a single stroked outline, so no single path in the file
corresponds cleanly to "the outer silhouette." A rendered flat-shaded preview of the imported curves
was also uninformative (the tonal differences are too subtle to read at normal preview brightness).
This is a **recorded, deliberate limitation**, not a skipped step: rather than force a false-precision
reading out of a shading illustration that was never meant for exact silhouette extraction, this
build proceeds from the reliably-confirmed canvas aspect ratio (~1:1.93) and the caption's own
"flat-bottomed" description, at MEDIUM confidence on exact wall taper -- the same confidence tier
already used for this project's stylized single-illustration benchmarks.

## Construction plan

- **Tumbler_Shell x1**: one connected, thin-walled revolved shell -- a genuinely different technique
  from the crate's box-primitive assembly. Built via `blender_ops/profile_mesh.py`'s
  `revolve_closed_profile`, this project's own validated profile-revolution helper (evidence:
  `runs/2026-08-11_multiview-barrel/`, 5,376/5,376 quads, one connected component, zero non-manifold
  edges). This is a disclosed direct-script call (not the typed decision-transaction path, since
  `create_primitive` only offers basic primitives, not custom revolved profiles) for the one-time
  starting mesh; any subsequent shaping decisions (edge treatment, shading) go through the typed
  `mcp__modeler__*` path exactly as for the crate.
- Profile (radius, z) in meters, a closed lathe cross-section: flat outer base, a gentle outward
  taper up the wall (flare toward the rim, matching a "cooler glass" silhouette rather than a
  straight cylinder), a thin rim lip (2mm wall), and a symmetric inner wall back down to a solid
  4mm-thick base. Target overall height 0.13m, base outer radius 0.0275m, rim outer radius 0.0325m
  -- proportions chosen to match the confirmed ~1:1.93 canvas aspect ratio, not an arbitrary guess.
- No secondary components. This is intentionally a single-object, single-technique build -- the
  minimal possible Level-1 test per the continuation directive's benchmark ladder
  (`docs/MASTER_DIRECTIVE.md` Section 19a).

## Success bar

1. Direct visual comparison against the reference before declaring the build complete.
2. Fresh-process verification: 0 non-manifold edges, 0 degenerate faces, one connected component.
3. Reads as a tall, flat-bottomed drinking glass with a thin wall -- proportions matching the
   confirmed aspect ratio, not pixel-precision against a shading illustration that was never
   suitable for that.

## Checkpoint result (2026-08-14)

Built `Tumbler_Shell` via `revolve_closed_profile` (64 segments, 6-point closed lathe profile: flat
outer base -> outward-tapering outer wall -> thin rim lip -> inner wall back down -> solid base
underside). Fresh headless verification immediately after creation: 384/384 quad faces, 0
non-manifold edges, 0 degenerate faces, 0 ngons, one connected component, exact intended dimensions
(0.065 x 0.065 x 0.13m). `checkpoint_v1.png` already read clearly as a tall drinking glass on first
look, though the wall showed a faint vertical facet stripe under studio lighting.

Applied this project's established edge policy through the typed decision-transaction path
(`set_bevel_scoping(method="ANGLE", angle_deg=45, width=0.0008, segments=2)` then
`set_smooth_by_angle()`), same as the crate. The 45-degree angle threshold correctly isolated the
genuine profile folds (base edge, rim lip, inner-base transition) while leaving the smooth
circumferential wall edges alone (adjacent-segment angle ~5.6 degrees at 64 segments, well under
threshold) -- confirmed by re-running `get_evaluated_state` rather than assumed: still 0
non-manifold/degenerate/ngons after bevel, 1152/1152 quads, dimensions barely changed
(0.0649 vs 0.065m, as expected for a sub-millimeter bevel). The evaluated-state pinch detector
flagged 256 "candidate" vertices, all clustered exactly at the rim (z~0.1292m) -- inspected and
attributed to the intentional bevel fold itself, not a defect, per this project's own standing
caveat that boundaries/intentional transitions can resemble candidate defects.
`get_hard_surface_shading_audit` returns `PASS`. `checkpoint_v2_beveled.png` shows the faceting
from v1 resolved by the smooth-by-angle pass, plus a soft rounded highlight at the rim -- a
genuine, visually confirmed improvement, not just a passing technical check.

Structurally, this is the most convincing single build of the session: a mostly-curved,
single-connected, single-technique object matched its reference on first visual read, in contrast
to every multi-part assembly this project has attempted. That is itself useful evidence, not a
coincidence to ignore: profile-revolution of a *correctly measured or well-reasoned* cross-section
appears to transfer cleanly, while box-primitive assemblies of manufactured products have
repeatedly not, regardless of technical cleanliness.

## Live-session note

The live Blender GUI process (and its typed modeler server) had been closed since the crate work
finished. Restarted Blender and `blender_ops/modeler_server.py` directly for this build --
confirmed via a fresh `heartbeat` call (`session_id`, `revision: 0`) that this is a new session,
not a stale reconnect.
