# Held-out fantasy ceremonial sword

**Date:** 2026-08-10

**Benchmark:** `heldout_b_fantasy_ceremonial_sword_001`

**Outcome:** technical PASS; visual gate FAIL

The user supplied the reference after the foundation/control implementation was complete. No
asset-specific builder existed. The selected reference was measured before modeling and the other
supplied references remained unused. Work stayed within fictional digital-prop art: no real-world
weapon construction or engineering was performed.

## Closed-loop execution

- Blender 5.2 remained in one persistent interactive process through revision 103.
- Geometry decisions used the typed `begin -> perform -> verify -> commit` protocol.
- The blade profile was observed by persistent vertex ID and adjusted ring-by-ring.
- Rendered mask tickets drove later blade-width, root-width, guard-mass, grip-width, and jewel
  proportion changes.
- Arbitrary Blender Python was used only for scene collections, materials, camera/lights, saving,
  and diagnostic rendering because those presentation operations are outside the typed modeling
  vocabulary. It is not counted as adaptive geometry evidence.

## Result

The editable source contains 15 named mesh components in `SWORD_PRIMARY` and `SWORD_SECONDARY`,
four named materials, typed bevel modifiers, a front/side/isometric presentation set, and a saved
`.blend` artifact. All 15 evaluated components passed a fresh-process independent verifier with:

- zero non-manifold edges;
- zero n-gons;
- zero loose vertices/edges;
- zero degenerate faces;
- positive signed volume.

The normalized front silhouette improved through the adaptive loop but finished at **0.725386**
against the predeclared **0.80** threshold. The visual gate therefore fails. The largest remaining
mismatches are the reference's longer curved tip transition and denser vertical guard silhouette.

## Artifacts

- `fantasy_sword_heldout.blend` — editable source
- `final_beauty.png`, `side_beauty.png`, `isometric_beauty.png` — review views
- `final_front_mask_alpha.png`, `final_front_mask_aligned.png` — comparison evidence
- `visual_comparison.json` — measured gate
- `independent_verify/` — 15 fresh-process evaluated-mesh reports

This run establishes real held-out control-loop and technical evidence. It does not establish a
visual pass, professional acceptance, or broad transfer across the seven reserved references.
