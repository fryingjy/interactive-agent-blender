# Stylized longsword — first blockout pass (SHELVED)

**Status update, 2026-08-23:** the user reviewed overall repo direction and made two decisions
that apply to this run: (1) weapon-related subject matter is being removed from the active
modeling curriculum in favor of neutral manufactured props (lamps, tools, appliances, cameras,
containers, furniture, mechanical objects) — not because anything unsafe happened here (the
fictional-prop-only constraint below was honored throughout), but because a weapon doesn't help
prove anything the neutral-prop ladder can't already prove, and (2) the project is pausing new
prop starts for a phase to rebuild the reference-analysis/interpretation layer (see
`docs/FAILURE_TAXONOMY.md` and the in-progress representation-hypothesis work) before resuming
modeling. This run is intentionally left as-is (not deleted, not "finished") as real evidence of
where the reference-driven-correction pattern was working (see the correction-pass section below)
and where it wasn't yet (still-unsourced blade thickness and pommel size at time of shelving). The
project's next modeling target will be a fresh neutral prop, not a resumption of this one.

Original task: model a game-ready medieval longsword as a stylized fictional prop, per the user's
explicit STEP 6 directive. Per the project's own evidence/claim rules and the user's explicit
instruction, this is treated as **fictional prop art using general modeling principles only** —
no real weapon-construction or engineering content (blade metallurgy, edge geometry for cutting
performance, structural load specs) was used or is present anywhere in this build. All
proportions below come from silhouette/dimension references, not functional-weapon sources.

## Reference basis (WebSearch, not memorized defaults)

- Total length, blade length, and grip length: corroborated across two independent source
  clusters (overlap ranges 116-140cm total, 100-110cm blade, 20-30cm grip; grip length is a
  well-corroborated single Wikipedia figure).
- Guard/crossguard width: **no reliable longsword-specific figure was found.** Only single-handed
  sword data (~20-25cm) turned up, which the sources themselves don't treat as transferable to
  longswords. The 0.22m guard width used below is therefore an explicitly low-confidence estimate,
  not a sourced figure, and is the first thing to revise if the human visual review flags the
  guard as under/over-scaled.
- A Wikimedia Commons SVG (`Long_sword.svg`) was downloaded and inspected directly, then
  **rejected** as reference: it is a small decorative/heraldic icon, not a proportionally accurate
  diagram.
- Pinterest access was attempted per the user's suggestion; the search page returned no content
  in this environment (likely login-gated) and was not used.

## Construction

Four distinct, separately-authored connected components (profile/section-authored, not primitive
stacking), built via the repo's typed modeler MCP surface (port 9878), then assembled by object
transform only — no boolean operations:

| Component | Tool | Method | Verts / Edges / Faces |
| --- | --- | --- | --- |
| Blade | `create_quad_shell_sections` | 5 authored cross-sections (base -> tip) along Y, each a 2x5 diamond profile with a fuller dip, so width and thickness taper are real authored geometry, not a single extrusion | 50 / 96 / 48 |
| Guard | `create_profile_loft` | One 10-point X/Z outline (diamond quillons tapering to points) lofted along Y | 20 / 30 / 12 |
| Grip | `create_quad_radial_surface` | 4-ring oval radial cage, then reoriented from its native local-Z build axis onto the blade's Y axis | 48 / 84 / 36 |
| Pommel | `create_quad_radial_surface` | 6-ring circular radial cage (neck -> disc bulge -> near-point taper), same reorientation | 72 / 132 / 60 |

Total: 190 vertices / 342 edges / 156 faces across the 4 components.

Grip and Pommel were built along their native local Z axis (how `create_quad_radial_surface`
authors rings), then moved onto the blade's Y axis using two **separate**, single-operation
decision transactions each (`rotate_object` then `translate_object`) — the server rejected an
attempt to chain both mutations inside one transaction as a stale/external-edit, which is the
typed surface correctly enforcing this project's one-operation-per-decision rule, not a bug.
Every transaction was begin -> perform -> verify -> commit; none were rejected or rolled back
except the one chained attempt above, which was cleanly `reject_decision`-ed and redone correctly.

Final layout along world Y (blade tip at +Y):
- Blade: Y = 0.00 (base, at guard) to Y = 1.05 (tip)
- Guard: centered on Y = 0.00, +/-0.011 thick
- Grip: Y = -0.011 to Y = -0.261
- Pommel: Y = -0.261 to Y = -0.327 (tapers to a near-point)

## Evidence

Renders (Blender-native, modifier-evaluated, not GUI screenshots) in this directory:
- `silhouette_top.png` — flat silhouette, top view (fill ratio 1.94%, consistent by hand-calc
  with the sword's actual long/thin bounding-box aspect ratio)
- `silhouette_front.png` — end-on silhouette (tiny fill ratio expected/correct: this view looks
  straight down the blade's length axis)
- `shaded_top.png`, `shaded_side.png` — solid-shaded diagnostic passes
- `wireframe_top.png` — base-cage wireframe, showing the authored section lines on the blade and
  the radial structure on grip/pommel (confirms this is profile-authored geometry, not a
  primitive stack)

**Note:** `silhouette_top.png`/`shaded_top.png`/`shaded_side.png`/`wireframe_top.png` above show
the original (pre-correction) `Blade`, kept intentionally for before/after comparison rather than
deleted. `silhouette_top_v2.png` and `shaded_top_v2.png` (see the correction section below) show
the current `BladeV2`, which is the geometry actually assembled with Guard/Grip/Pommel now.

## Status: MODELED / HUMAN VISUAL REVIEW PENDING

This is a first blockout pass, not a self-declared finished asset. Per the project's review
protocol, human visual review overrides any automated pass, and I have not run or claimed one.
Known open items, honestly flagged rather than hidden:
- Guard width (0.22m) is the lowest-confidence dimension in the build (see Reference basis above).
- Only 5 lengthwise sections author the blade's taper; if the human review calls the taper too
  faceted/straight-sided at this stage, that's a legitimate topology gap, not a rendering artifact.
- End caps on Grip/Pommel are open n-gon-free boundary loops by design (each component stays a
  connected open cage per its build tool), relying on the adjoining component to visually cover
  the seam; this has not yet been checked at close range for gaps.
- No bevels, edge-weighting, or SubD pass has been applied yet — this is the base cage only.

Waiting on the user's own visual review before any further stage advancement or claim of
completion.

## Correction pass: real dimensioned references, not just human eyeballing

Per explicit user feedback ("less review from me, more review via references and tutorials
online"), the next check on this build was a real evidence pass, not another request for the
user to eyeball a render. Sources actually fetched and read (not just searched):

- [Longsword](https://en.wikipedia.org/wiki/Longsword) (Wikipedia) — confirms total 100-140cm,
  blade 80-110cm, grip 20-30cm. This build's blade (105cm) and total length (~137.7cm) sit at the
  long end of these ranges but inside them; grip (25cm) is centered in range.
- [Albion Armorers Munich](https://myarmoury.com/bill_swor_alb_munich.html) (myArmoury.com
  review of a specific, precisely-measured historical-reproduction longsword) — the single
  strongest source found: overall 125.7cm, blade 94.6cm, **blade width at base 3.8cm, tapering to
  1.1cm at the point (not a knife-edge zero)**, **guard width 21.6cm**, grip 25.1cm.
- [myArmoury "Cross-guard width" forum thread](http://myarmoury.com/talk/viewtopic.29211.html)
  and [myArmoury "quillon length" thread](http://myarmoury.com/talk/viewtopic.14596.html) —
  independent corroboration for longsword-specific guard widths clustering ~19-30cm (Albion
  Castellan 18.7cm, Liechtenauer-type 23.5cm, a longsword-with-12in-handle at 29.8cm), confirming
  this build's 22cm guard is well inside the real range, not a low-confidence guess as originally
  flagged.
- Grant Abbitt, ["Make a Detailed Sword in Blender: Topology Tips & Hard Surface
  Techniques"](https://www.youtube.com/watch?v=f320TtEpGYQ) (full transcript read, not just the
  title) — a real Blender sword-modeling tutorial, checked for construction technique rather than
  dimensions. Notable findings: the tutorial's grip/guard/pommel are modeled as separate
  box-modeled pieces that are explicitly allowed to overlap without welding ("You can overlap
  them, that's absolutely fine") -- this independently validates the separate-overlapping-object
  approach already used here for Guard/Grip/Pommel. The tutorial's blade has no fuller at all (a
  flat hard-surface ridge study using bevel-supported creases instead), so it offered no
  transferable fuller-construction technique, and it does not address crossguard construction or
  give any numeric proportions -- everything there is sized by eye against a traced reference
  image.

**What changed as a result**: the original Blade (base half-width 2.5cm, tapering to a near-zero
point) was measurably too wide at the base (5cm vs. the Munich's 3.8cm) and too sharply pointed
(tapering to ~0.2cm vs. the Munich's 1.1cm blunt tip) compared to the one precisely-measured real
longsword found. The original Blade object was archived (not deleted -- moved to a
`REJECTED_COMPONENTS` collection, fully recoverable) via one `archive_object` decision
transaction, and replaced with `BladeV2`: the same 5-section authored construction, with all five
cross-sections' widths rescaled to match the base-3.8cm/tip-1.1cm anchors, thickness values left
unchanged (no independently sourced thickness data was found, so those stayed as originally
authored rather than being adjusted on a guess). New renders: `silhouette_top_v2.png`,
`shaded_top_v2.png`. Guard, Grip, and Pommel proportions were left unchanged -- they are now
corroborated by real longsword-specific data (guard) or already matched it closely (grip), rather
than needing correction.

Still not independently sourced: blade thickness/cross-section profile (spine vs. edge
thickness), and pommel size/shape (no numeric pommel reference was found in this pass). These
remain the most likely next things to revisit if a further reference pass turns up better data.
