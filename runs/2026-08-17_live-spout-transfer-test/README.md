# Live transfer test: growing a spout from a body, using the validated technique

Direct follow-on to the re-inspection in
`runs/2026-08-14_shrinkwrap-vs-join-handle-correction/brief.md`. That correction concluded that
this project's own live-demonstrated technique (grow/join/bridge a secondary curved form directly
from the primary body's own mesh) was a better foundation for judgment than reproducing an
externally-sourced video technique from partial observation -- which is exactly what the scrapped
cylinder-join experiment (`4de7745`, deleted `b37f609`) had tried and failed to do cleanly.

This is the direct test of that conclusion: build a new curved-fusion case -- a spout growing out of
a cylindrical body at an angle, the same general class of shape the cylinder-join attempt struggled
with -- but via inset-then-extrude growth from the body's own faces (the validated pattern), done
live with a real decision-transaction per step and a render/geometry check before committing each
one, not a headless batch script computing parameters in advance.

## What was built

`FlaskBody`: a 32-segment, radius-1, ngon-capped cylinder. Two horizontal loop cuts split the side
wall into three height bands. A face on the middle band was inset (thickness sized to the face's
actual ~0.196x0.867 dimensions, not guessed), then extruded outward, rotated upward twice, extruded
twice more with a taper, producing a bent, tapered spout stub grown directly out of the body -- one
continuous mesh, no join/bridge needed at all since nothing was ever a separate object.

Final state: 144 vertices, 256 edges, 114 faces, **0 non-manifold edges** throughout every single
step (never once went non-zero, including immediately after every individual operation). Valence
distribution 3:68 (64 of these are the two ngon end caps' boundary rings, a known non-defect
pattern; the remainder is the actual join), 4:72, 5:4. `get_evaluated_defect_regions` flags 38
candidate tickets total, and **the join area does not appear anywhere in the 15 most severe** --
every one of those is `angle_degrees: 11.25`, which is exactly 360/32, the body's own inherent
low-poly circumferential faceting, not a defect. The join is invisible to the same diagnostic that
flagged the cylinder-join fold as the single worst thing in that entire scene.

`progress_02_final_iso.png`: clean, coherent bent spout, no visible fold or pinch.

## Two real mistakes made and caught mid-build, not glossed over

**Mistake 1: inset thickness sized without checking the face's actual dimensions.** First attempt
used `thickness=0.15` on a face roughly 0.196 units wide -- geometrically impossible (0.15 on each
of two opposite sides needs 0.3 of a 0.196-wide face) and produced a twisted, wrong-normal quad
instead of a valid ring. This wasn't caught by mesh-health metrics (non_manifold_edges stayed 0
throughout, `verify_decision` reported clean deltas at every step) -- it was only caught by directly
querying the resulting vertex coordinates and finding the "extruded" tip had moved *inward*
(X ~0.48-0.81) instead of outward from a radius-1 body, the opposite of what an outward extrude
should do.

**Recovery, done properly instead of using `undo`** (documented elsewhere in this project as
unreliable -- it does not reliably target "the last decision" and can jump past committed
transactions unpredictably): explicitly selected and deleted the malformed geometry by persistent
ID, filled the resulting hole, then found and deleted a second, disconnected stray remnant face
(`agent_id 399`, `link_faces` on its boundary edges all equal to 1, `agent_id: None` on the edges
themselves -- genuinely untracked debris from the failed inset) that the first cleanup pass missed.
Confirmed the object was back to a byte-for-byte-equivalent clean state (same vertex/edge/face
counts as immediately after the loop cut, 0 non-manifold edges) before starting over with a
correctly-sized `thickness=0.04`.

**Mistake 2 (methodological, not geometric): front/side orthographic renders don't reveal a bump
near the silhouette's own tangent line.** The first (broken) attempt's `front`-view render looked
identical to the clean body -- not because the geometry was fine, but because the defect sat too
close to the viewing angle's own silhouette edge for an axis-aligned camera to show it. Switched to
`render_diagnostic_pass`'s `isometric` view for every subsequent check, which does reveal off-axis
features properly. Recorded here so future checks default to an oblique view, not front/side, when
looking for a feature growing off a curved surface's front-facing area.

## What this confirms, and its limits

This is `EXPERIMENTALLY_TESTED`: one clean build, verified two ways (mesh-health deltas at every
step, `get_evaluated_defect_regions` on the finished result), with real mistakes caught by direct
evidence rather than assumed away. It is not yet `TRANSFER_VALIDATED` -- that requires a second,
different target (a different body shape, a different attachment angle) using the same technique,
which is the natural next step. It also does not by itself prove the technique is *better* than
Shrinkwrap+Bridge in general -- only that, on this shape, built carefully with real verification at
each step, it produced a clean result where the reproduced-from-video technique did not.
