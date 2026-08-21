# Mug with handle — the real join test the mallet avoided

The mallet ([[interactive-agent-blender-project]] memory, `runs/2026-08-20_mallet-build/`) proved
clean all-quad SubD technique but was a single revolved profile — no join between separate forms,
which is exactly what broke on the magnifying glass. This build tests that directly.

## Technique

No boolean anywhere. The handle is a literal authored bridge:
1. Cut two small rectangular holes in the mug wall (same angular width, at two different heights),
   each leaving a real boundary loop that is still part of the body mesh.
2. Canonicalize each hole's boundary into a matched vertex order (top row by ascending angle, then
   bottom row by descending angle) — an undirected boundary-walk's start point and direction are
   arbitrary and will NOT line up between two independently-walked loops.
3. Sweep new rings between the two loops along a D-shaped arc, ending exactly at the second hole's
   *existing* vertices — so the weld is by construction, not a merge-by-distance or `bridge_loops`
   call that could fail like it did repeatedly on the magnifying glass.

Result: 584 faces, 0 non-manifold except the intentional open rim (z=9.15), 100% quads.

## Two real bugs found under actual material/lighting, not flat shading

1. **Cross-section shear.** First version moved each of the handle's boundary vertices along its own
   independent lerp+radial-bulge path. Looked fine in flat solid shading; under real material
   lighting it showed heavy creasing, and just adding more rings didn't fix it. Root cause: nearby
   vertices' individually-computed radial directions diverge slightly along the curve, so the
   cross-section shears as it sweeps instead of moving as a rigid shape. Fix: compute one shared path
   for the cross-section's *centroid*, and carry each vertex's local offset from that centroid along
   rigidly — the shape's size and orientation stay constant through the sweep. Should generalize to
   any authored-bridge sweep in this project, not just this handle.
2. **Sparse-geometry rim faceting.** Same underlying issue as the mallet's shading artifact
   ([[blender-modeling-technique-corrections]] §4) — the rim flare had too few intermediate loops
   for a tight radius change. Fixed the same way: added support loops.

Neither defect was visible in flat grey Workbench solid shading — both only showed up once rendered
under `render_blend_beauty.py`'s `material` mode. Checked every delivered image personally before
sending, per [[feedback_verification_before_claiming_done]].

## Status

**Human visual review (2026-08-20): accepted, no repair tickets.** Recorded via
`tools/record_external_visual_review.py` against `human_review.json` at scene_revision 0; see
`human_review_repair_handoff.json`. This build satisfies the join test the mallet deliberately
avoided; per `docs/CURRENT_STATE_GAP_MATRIX.md` the still-open gap is a genuine unfamiliar-reference
build, which neither this nor the mallet is.
