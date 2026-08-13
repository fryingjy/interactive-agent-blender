# Operator card: high-poly/low-poly production collection pipeline

**Status:** OBSERVED ✓ (7/10 studied professional files) | TYPED SUPPORT partial | RUNTIME TRANSFER pending

## What it is

A collection-based organization pattern found consistently across 7 of the 10 professional `.blend`
files studied under `docs/BLEND_FILE_STUDY_PROTOCOL.md`
(`batarang.blend`, `alien force watch.blend`, `broken sword.blend`, `adventure time sword.blend`,
`ap15.blend`, `ak47.blend`, plus `battle axe.blend`'s simpler single-stage version), each using
slightly different names for the same underlying structure:

- **A working/editable collection** (`model`, `hp`, `highpoly`) -- the actual modeling happens here,
  with a full non-destructive modifier stack (Mirror, Bevel, Subdivision Surface, Smooth by Angle).
  This is the source of truth; every other collection is derived from it.
- **A genuinely separate, hand-retopologized low-poly collection** (`lowpoly`, `lp`) -- NOT simply
  the same mesh with modifiers disabled. Vertex counts confirm this directly: e.g. `alien force
  watch.blend` part 8's high-poly cage is 610 verts, its low-poly counterpart is a distinct 768-vert
  retopology, not a lower number as toggling SubD off would produce. The low-poly mesh sometimes
  carries a `TRIANGULATE` modifier (`broken sword.blend`) to pre-triangulate for a real-time engine
  export target, and is the actual UV/bake target.
- **Optionally, a dense sculpted collection** (`zbrush hp`, `zbrush cut`) holding untouched,
  unmodified meshes with very high vertex counts (`broken sword.blend`'s `wrap_high`: 1,126,023
  verts) -- these exist purely as bake sources for high-frequency surface detail (wear, cracks,
  tool marks), not as editable production geometry.
- A reference **Image Empty** (`batarang.blend`) is used for direct on-screen tracing, matching this
  project's own already-documented Image-Empty reference workflow.

The low-poly mesh's material carries real baked PBR textures (`batarang.blend`:
`batarang_low_uv_{BaseColor,Metallic,Normal,Roughness}.png`), confirming this is a genuine bake
pipeline (high-poly/sculpt -> low-poly, selected-to-active), not just an LOD convenience.

## Why this matters for this project

This project's `models/` folder convention (adopted 2026-08-13, first used for
`models/adjustable_wrench.blend` before that asset was rejected and removed) assumed a simpler
version of this pattern -- literally the same mesh with modifiers toggled off, per the user's own
initial description. The studied files show real professional practice goes further: a genuinely
separate, hand-authored low-poly retopology is the norm when production/export quality actually
matters, not merely a modifier-visibility toggle. The simpler toggle-based approach remains valid
for quick internal iteration; a true production deliverable should follow the fuller pattern
observed here.

This project already performs the equivalent bake step for real (Cycles selected-to-active tangent
bakes on the telephone and watering can, per `docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md`) -- these
studied files confirm that practice matches genuine professional convention rather than being an
invented substitute.

## What this does not establish

- No typed operation exists yet for "retopologize a low-poly target from a high-poly source" --
  this remains a manual/scripted step, same as before this study.
- Not yet applied within this project's own construction scripts; this is an observed, cross-file-
  confirmed pattern, not yet a `RUNTIME_VALIDATED` capability per `docs/KNOWLEDGE_SYSTEM.md`'s
  lifecycle.
- The exact retopology strategy (how the low-poly's edge flow is chosen) was not traced in this
  pass -- only vertex-count and collection-membership evidence was gathered, not a full topology
  comparison.

## Evidence

`runs/2026-08-13_blend-file-study/{batarang,alien_force_watch,broken_sword,adventure_time_sword,
ap15,ak47}/inspection.json` and `session_report.md`.
