# Reference: classic desk stapler (Swingline 747-style) -- HELD-OUT TEST OBJECT, RESTART

**Restart of the held-out reference-reconstruction test** (2026-08-15). The first attempt at this
test used a padlock; that build was abandoned mid-shackle (per direct user instruction: "poorly
done job scrap and try something else") after the shackle's curved-tube construction produced a
result that didn't track the intended geometry cleanly, on top of an earlier compromise (single
slot instead of two real shackle-leg holes, forced by a real T-junction ngon limitation in
`subdivide_selection`/`bisect_selection`). Rather than attempt a fourth curved-appendage build in a
row (teapot spout x3 attempts, teapot handle bridge-twist revert, padlock shackle) this object was
chosen specifically because its primary form has **no thin bent-tube appendage** -- it breaks the
failure pattern instead of repeating it. `Padlock_Body` was deleted from the live scene by the user
before this restart; `reference/padlock/notes.md` is left in place as an honest record, not deleted.

References were gathered from the user's own logged-in Chrome (Google Images, real product
listings) rather than the sandboxed in-app browser, per direct user instruction ("you can use my
actual browser this time") -- this got past the earlier Wikimedia-only restriction and reached
real dimensioned product data, not just estimated proportions.

## References collected

1. **Primary, side profile silhouette**: product photo, Swingline classic desk stapler (black),
   pure side view, plain white background, sourced via Google Images from shop.stinsons.com
   ("Swingline Durable Desk Stapler"). Shows: low elongated body, a distinct forward-sloping nose
   at the staple-exit end, a gently arched top surface (not flat -- highest toward the back/hinge
   end, sloping down toward the front nose), a visible seam/hinge split roughly 65-70% of the way
   forward from the back, and a thin flat base plate visible as a sliver beneath the main body,
   extending slightly past the body's silhouette at both ends.
2. **Mechanism reference, 3/4 open view**: Amazon listing photo (Marsrock heavy-duty stapler,
   modern design, not the classic body shape) showing the top lever hinged open, revealing the
   metal base rail/anvil track the staples form against, and loose staple sticks for scale context.
   Used only for mechanism understanding (how the top lever separates from the body, where the
   metal channel sits relative to the plastic/metal housing), not for body proportions -- this
   product's housing shape is a different (modern) style, explicitly not used as a shape reference.
3. **Real dimensioned reference, HIGH confidence**: Amazon product listing for the actual Swingline
   747 Classic Stapler, 30 Sheet Capacity, Metal, Black (model 74701, ASIN B0006HUQ9M) --
   `amazon.com/Swingline-SWI74701-Classic-Stapler-Sheets/dp/B0006HUQ9M`. Listed **Product
   Dimensions: 7.4"L x 1.7"W**; a separate product image's own dimension annotation gives **height
   2.6" (6 cm)**. This is real manufacturer-listed data, not an estimate -- a meaningfully stronger
   confidence basis than the padlock reference set had (which was proportion-estimated from photos
   only). Also confirmed from the listing text: metal construction, die-cast metal base, a
   button-latch on the bottom that lets the stapler "swing open" for tacking to vertical surfaces,
   a reversible anvil for pinning, and that it holds a full strip of up to 210 staples.

**What these do NOT establish (explicitly unresolved, not guessed):** exact corner-radius/fillet
values on the body; the exact profile curve of the top arch (approximated as a shallow arc, not
measured pointwise); interior mechanism detail beyond the general channel/spring/lever
relationship (not modeling functional interior parts, only the visible exterior + the open-lever
silhouette if attempted); the exact split-line position of the top lever hinge (estimated at ~65%
from photo proportion, not measured).

## Primary / secondary / tertiary decomposition

- **Primary** (defines identity/silhouette): a single elongated low body block, L:W:H derived
  directly from the real dimensions above -- 7.4 : 1.7 : 2.6 inches, i.e. normalizing to height=1:
  L≈2.85, W≈0.654, H=1. Top surface is gently arched (higher at back, sloping to a lower front
  nose), bottom is a flat thin base plate.
- **Secondary** (construction/recognizable design): the top-lever split line (~65% of the length
  from the back) where the striking mechanism hinges open; the forward-sloping nose at the front
  (staple-exit end) with a small step/overhang; the thin base plate reads as a distinct component
  from the main body, not flush with it, slightly wider than the body in side view.
- **Tertiary** (small realism/detail, explicitly deferred until primary+secondary are solid): the
  brand engraving on the top surface; the small pivot pin visible at the hinge; the metal staple
  channel visible through the front nose opening.

## Modeling plan (before opening Blender)

1. Body: single block, dimensions scaled from the real 7.4 x 1.7 x 2.6 ratio (e.g. 2.85 x 0.654 x
   1.0 local units, or scaled up for comfortable working size). Build via cube blockout.
2. Shape the top surface into a shallow arch (higher at back, lower at front) -- this is a curved
   SURFACE, not a curved TUBE, so it can be built by moving/scaling existing top-face geometry
   (subdivide the top face along its length, then raise the back verts / lower the front verts) or
   by a shallow bevel, not by the fragile extrude+rotate chain method that caused the last three
   failures. If a genuinely smooth arched curve is wanted, prefer the modeler's dedicated curve
   tools (`create_curve` / `set_curve_bevel_depth` / `convert_curve_to_mesh`) over hand-chained
   extrude+rotate -- those tools exist specifically for smooth curves and haven't been tried yet
   this project; hand-chaining was a self-imposed constraint, not a hard requirement.
3. Cut the front nose's forward slope via a bevel/loft on the front-top edge, not a boolean.
4. Add the top-lever split line as a visual seam (inset/loop cut at ~65% position), deferred until
   the primary block is confirmed against the reference silhouette. Whether to actually separate it
   into a hinged secondary object is a secondary-form decision, not primary.
5. Base plate: inset+extrude a thin plate slightly proud of the body's own footprint.
6. Bevel-weight policy applied per this project's standing convention once primary+secondary forms
   are confirmed against the reference silhouette.

## Honest confidence statement

HIGH on primary proportions (real manufacturer-listed L/W/H, not estimated from photos). MEDIUM on
the top arch's exact curve shape and the hinge split-line position (both read from a single photo's
proportions, not measured). LOW / explicitly deferred on interior mechanism detail.
