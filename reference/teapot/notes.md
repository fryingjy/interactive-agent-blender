# Reference: simple teapot (mug's replacement transfer-test candidate)

Written proportions spec (no image download requested), deliberately picked as the mug's successor
for connected-topology transfer testing -- a genuinely harder version of the same skill (TWO grown
appendages instead of one: a spout and a handle, both required to read as fused to the body via
join+bridge, per `blender_handle_connected_topology.md`'s now-twice-reinforced correction), not a
repeat of the same failure.

- Body: revolved profile, rotationally symmetric around the vertical (Z) axis -- squat, rounded
  form. Base diameter ~4 units, widest point (~4.6 units) around 1/3 up the height, tapering back
  in toward a narrower shoulder near the lid opening. Overall body height ~3.2 units.
- Lid opening: circular, diameter ~1.8 units, centered on top, with a small rim/lip bevel.
- Lid: a separate, simple domed disc sitting in the opening -- genuinely a distinct removable part,
  the one place on this object where a separate (not joined) object is the correct call, unlike the
  handle and spout.
- Spout: grown from the body's own mesh (extrude/loop-cut/bridge, not a separate primitive),
  tapering outward and slightly upward from roughly the body's widest point, curving up and out to
  an open tip. Length from body to tip ~2.2 units, hollow bore at the tip (not solid) so it reads
  as a genuine pour spout.
- Handle: grown from the body's own mesh on the side opposite the spout, C-shaped, spanning
  roughly the body's mid-to-upper height, standing proud of the body by ~1.0 unit at its outermost
  point -- same category of problem the mug's handle posed, now with a second, independently
  correct solution required (spout) alongside it.
- Wall thickness: solid for this milestone, matching the bottle/mug precedent.
- Why this replaces the mug as the active candidate: the mug was scrapped after three failed
  attempts (see `runs/2026-08-14_simple-mug/brief.md`, kept as historical failure evidence, not
  deleted) and a live user correction reinforcing that Shrinkwrap-conformed attachment is not a
  substitute for genuine connected topology. This object tests the corrected understanding
  directly, on a harder case, rather than repeating the same single-appendage build.
