# Skill-building build: simple slatted wooden crate

**Purpose (2026-08-14):** not a held-out benchmark. Per direct user feedback ("you were horribly
inaccurate... start with simpler shapes/props/models and work your way up because you genuinely
dont know what you're doing in terms of modelling it"), this is the first entry in a bottom-up
modeling-skill curriculum, replacing an immediate return to complex assets. See
[[feedback_start_simple_build_modeling_skill]]. The katana benchmark is paused, not resumed
(`runs/2026-08-14_heldout-katana/benchmark_brief.md`).

## Reference

`reference/wooden_apple_crate.jpg` — a public-domain photo (photos-public-domain.com, "All Photos
on this site have been released into the Public Domain... Free Photos for any use including
Commercial"), downloaded 2026-08-14 with explicit user permission. Real, un-stylized, photographed
object — the opposite of the illustrated/stylized single-image sources this project's complex
benchmarks kept relying on.

## What the reference actually shows

A rectangular slatted wooden fruit/produce crate, photographed at a three-quarter angle, resting
on rough ground. Visible construction:

- Four vertical corner posts (thicker battens), one at each corner, running the full height of the
  crate.
- The long sides are built from horizontal slats nailed to the corner posts, with visible gaps
  between slats (not solid panels) — three slats visible on the near long side, evenly spaced with
  roughly slat-width gaps between them.
- The top (visible in the photo as the near-horizontal face closest to camera, since the crate is
  photographed tilted toward the viewer) is also slatted, same construction as the sides, with one
  slat sitting slightly askew (real, weathered, second-hand crate — this specific asymmetry is not
  a target to reproduce, the overall structure is).
- Visible nail heads at each slat/post intersection — a texture-level detail, not a modeling
  target.
- No curved surfaces anywhere. No compound joinery. This is deliberately about as low a
  construction-complexity object as exists.

## Construction plan

- **Corner_Post × 4**: the typed modeler's `create_primitive` has no join/boolean operation, so a
  single fused frame mesh isn't buildable through it anyway -- and four separate posts is actually
  the more accurate decomposition of a real crate, which is assembled from genuinely separate
  boards nailed together, not one continuous casting.
- **Slat × 12**: 3 slats per long side (×2) + 3 top + 3 bottom, each its own object at its own
  transform via `create_primitive`, matching the visible even spacing and gap ratio from the
  reference. Short ends are left open, framed only by the posts, for this first pass -- checkpoint
  against the reference before deciding whether that needs correction.
- Sharp-edge policy: a rough-sawn wooden crate reads with soft, slightly worn arrises, not a crisp
  machined chamfer — decide the actual bevel/crease choice from the reference at construction time,
  per this project's own edge_crease.md lesson, not assumed in advance.

## Success bar (deliberately not a formal IoU-gated benchmark)

1. Direct visual comparison against the reference photo, from the same three-quarter-ish framing,
   before declaring any stage complete — this is the one check every prior complex asset in this
   project failed to apply rigorously enough.
2. Fresh-process verification: 0 non-manifold edges, 0 degenerate faces, correct evaluated signed
   volume.
3. Proportions read as a crate (roughly square-ish cross-section, longer than it is tall) without
   needing pixel-precise measurement — this build is about topology and construction judgment, not
   chasing a silhouette-IoU number.

## Checkpoint result (2026-08-14, blockout v1)

Built entirely through the typed-modeler decision-transaction path (`create_primitive` +
`scale_selection` per object, 16 objects: 4 `Corner_Post`, 12 `Slat`), saved to
`wooden_crate.blend`. Fresh **headless** verification (`blender --background`, not the live GUI
session's own self-report): 16/16 objects, 0 non-manifold edges, 0 degenerate faces, 0 ngons, exact
intended dimensions on every object. `checkpoint_blockout_v1.png` rendered from that same fresh
process (Workbench, studio lighting) for an unbiased comparison.

Direct visual comparison against `reference/wooden_apple_crate.jpg`: the structure reads
correctly as a slatted crate on first look — four corner posts, evenly gapped horizontal slats on
two long sides and the top, proportions longer than tall. This is a genuinely closer visual match,
achieved with far less construction complexity, than any of the complex held-out assets attempted
earlier this session (boombox, camera, wrench, watering can, telephone, katana), which all had
clean technical checks but failed direct visual review. Known, disclosed simplifications not yet
addressed: short ends are open (framed only by posts, no end panel), no bottom-facing slats were
rendered in this checkpoint framing, and no bevel/wear detail has been added yet -- next passes
should address whichever of these the reference makes clearly necessary, one at a time, checkpointing
visually after each.

## Checkpoint result (2026-08-14, blockout v2 — edge treatment)

Re-examined the reference before assuming the open short ends were a defect: zoomed into the
crate's visible right-hand end and confirmed it genuinely is open (interior debris visible through
the gap) — not a simplification to fix, the original read was already correct.

Applied this project's established hard-surface edge policy (`bevel_modifier.md`,
`transaction_recovery.md`): `set_bevel_scoping(method="ANGLE", angle_deg=30, width=0.0015,
segments=1)` then `set_smooth_by_angle()` on all 16 objects, matching the reference's worn,
non-machined arrises rather than leaving razor-sharp CAD edges. `get_hard_surface_shading_audit`
returns `PASS` on every spot-checked object (`angle_or_vgroup_intent_matches_actual: true`,
`smooth_by_angle_recorded: true`). Fresh headless verification after: still 16/16 clean, every
object now carrying exactly one `BEVEL` modifier. `checkpoint_blockout_v2_beveled.png` shows soft
highlight lines along the previously razor-sharp edges — a small but genuine improvement toward
the reference's worn-lumber look, not just a technical checkbox.

Also discovered while batching this pass: `set_smooth_by_angle` does not add a persistent modifier
(unlike `set_bevel_scoping`), so `check_external_edit`'s modifier-list diff never flags it as an
external change on re-observation — confirmed via `get_hard_surface_shading_audit` directly rather
than assumed, before abandoning the redundant re-adoption decisions.
