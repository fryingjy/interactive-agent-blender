# Reference: standard laminated brass padlock -- HELD-OUT TEST OBJECT

**This is the project's first held-out reference-reconstruction test** (2026-08-14), per direct
user instruction to pivot from curriculum accumulation to an unseen-reference build: no
prewritten recipe, no target-specific coordinates, no manually-prepared topology going in. This
document is being written AS the reference-analysis step, not before the object was chosen.
Confirmed via repo-wide grep before starting that no file anywhere in this project previously
referenced a padlock, pepper grinder, or desk stapler -- padlock was picked as genuinely fresh,
common enough to have reliable references, and a reasonable hard-surface complexity match for
this project's current priority allocation (hard-surface/SubD/topology).

## References collected

Real photographs only, no invented proportions. Per `docs/REFERENCE_COLLECTION_PROTOCOL.md`'s own
confidence levels, this is **MEDIUM confidence**: two independent photographs agree on primary
proportions, but neither is a true orthographic/dimensioned source, so depth (front-to-back
thickness) is inferred from general padlock construction knowledge, not measured -- flagged
explicitly as the weakest part of this reference set rather than silently treated as solid.

1. **Primary, closed/locked state**: Wikimedia Commons, "Solex 99 30 padlock with keys
   (DSCF2659).jpg" (`commons.wikimedia.org/wiki/File:Solex_99_30_padlock_with_keys_(DSCF2659).jpg`).
   Slight 3/4 angle, not pure orthographic. Shows: rounded-top rectangular brass body, symmetric
   U-shaped steel shackle in the closed/locked position, small vertical keyhole slot on the front
   face below the brand engraving, keys on a ring through the shackle for scale context.
2. **Secondary, open/mechanism state**: Wikimedia Commons, "Padlock klódka ubt.JPG"
   (`commons.wikimedia.org/wiki/File:Padlock_kl%C3%B3dka_ubt.JPG`). Near-front angle. Shows the
   shackle in the OPEN position -- one leg stays pivoted/captured in the body (the hinge side),
   the other leg is the free/locking side that inserts into a second body hole when closed. This
   is real evidence for the mechanism (why the shackle has two functionally different legs even
   though it looks symmetric when closed), not just the closed silhouette.

**What these do NOT establish (explicitly unresolved, not guessed):** true orthographic side
profile / exact depth-to-width ratio; exact keyhole internal geometry (pin tumbler detail is
occluded/irrelevant at this modeling scale); exact corner-radius values; whether the body is a
single brass shell or laminated steel plates (real padlocks vary by construction type -- this
build will treat it as a single solid shell, which is a real simplification, stated as one, not
hidden).

## Primary / secondary / tertiary decomposition

- **Primary** (defines identity/silhouette): the body -- a rounded-top-corner rectangular block,
  taller than wide, most likely near-square in front elevation based on both photos (estimating
  body width:height around 1:1.15-1.25); the shackle -- a U-shaped bent cylindrical rod, symmetric
  when closed, extending above the body by roughly 45-55% of the body's own height based on both
  photos' proportions.
- **Secondary** (construction/recognizable design): the two shackle-leg holes in the top of the
  body (one hinge/pivot side, one free/locking side -- visible directly in reference photo 2); the
  keyhole slot on the front face, small, vertical, positioned centered horizontally, roughly in
  the lower-middle third of the front face height.
  Also secondary: a shackle diameter that reads as noticeably thinner than the body width (roughly
  10-15% of body width in both photos) -- this is a real proportion, not an assumption, since both
  references agree on it independently.
- **Tertiary** (small realism/detail, explicitly deferred until primary+secondary are solid):
  branding engraving on the body face, a subtle bevel/chamfer on the body's edges, any visible
  seam line if treating the body as laminated plates rather than a single shell.

## Negative space

The gap between the shackle's inner curve and the body's top face -- the space a padlock is
actually meant to hook through (a hasp, a chain link) -- is real functional geometry, not empty
space to ignore. Getting the shackle's arc height/width wrong changes what the padlock could
plausibly hook onto, so this negative space is being treated as a real proportion target, per the
reference protocol's explicit warning that negative space is data, not the wrong lesson to have
learned from the earlier adjustable-wrench rejection this project's own docs already record.

## Modeling plan (before opening Blender)

1. Body: rounded-top-corner rectangular block. Build via cube blockout, then bevel/fillet the top
   two corners (not the bottom -- padlocks sit flat), matching the reference's rounded-top /
   flat-bottom silhouette.
2. Two holes through the top face for the shackle legs (through-holes into the body, matching
   photo 2's visible construction), positioned symmetrically.
3. Shackle: grown as a single continuous curved tube through the typed decision-transaction
   protocol -- same category of problem as the teapot's spout/handle (a curved cylindrical
   appendage), but this time driven by proportions read directly off a real reference rather than
   invented numbers, and this time using what was actually learned from the teapot's two real bugs
   (always re-verify extrude direction empirically; expect bridge_selection issues on any loop
   closure and plan around them, e.g. keep both ends' loop vertex counts equal from the start
   rather than mismatched).
4. Keyhole: a small inset+extrude/bore into the front face, positioned per the reference's
   observed proportions.
5. Bevel-weight policy applied per this project's standing convention once primary+secondary forms
   are confirmed against the reference silhouette.

## Honest confidence statement

MEDIUM overall. Primary silhouette and proportions: reasonably confident (two independent sources
agree). Depth/thickness: LOW confidence, inferred from general construction knowledge, not
measured -- will be checked against the model's own silhouette from a side render once built,
rather than assumed correct going in. Mechanism understanding (two functionally different shackle
legs): confirmed directly from reference photo 2, not assumed.
