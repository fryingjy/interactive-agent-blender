# Correction: Shrinkwrap-conformed attachment is not connected topology

**What happened:** mid-way through building the second transfer test (Shrinkwrap + vertex-group
restricted attachment, the technique captured from CG Boost's 6-tricks video and confirmed by a
third independent source, The Gnomon Workshop's professional course), the user stopped the work
directly: "your approach is still wrong stop and watch me do it and learn." Control was ceded
(`set_control_mode("USER_CONTROL")`) immediately, and the user built the handle-attachment live in
their own Blender session while this was observed via `poll_events` and periodic screenshots.

## What the user built

A `Cylinder` object (mug body) and a `Torus` (handle), both edited extensively (the event log shows
sustained iterative editing with multiple undo/redo cycles on `Cylinder` -- normal live sculpting,
not a single clean operation), then the `Torus` was **joined** into `Cylinder`. Confirmed
afterward: `Torus` no longer exists as a separate object; `Cylinder` is a single mesh, 368 vertices,
736 edges, 368 faces, **0 non-manifold edges, 0 degenerate faces**, valence distribution mostly 4
(352) with a handful of 3-poles (8) and 5-poles (8) at what is almost certainly the join/bridge
seam. Screenshot and silhouette render saved alongside this brief; `.blend` file also saved.

## Why the abandoned Shrinkwrap approach was the wrong call, even though it "passed"

The Shrinkwrap+vertex-group technique (build `HandleTest_Handle` as a separate curve-derived tube,
restrict a Shrinkwrap modifier to the contact vertex group, target the body) does exactly what it
claims: it conforms the *position and orientation* of specific vertices onto a target surface. That
part of the claim, in isolation, is true and would still pass a transfer test if run to completion.

**But it was never going to produce the actual thing being asked for.** This project's very first
documented correction on handle-building (`blender_handle_connected_topology.md`, from earlier this
session) states it plainly: *a handle that reads as fused to the body must be grown from the body's
own mesh (extruded/loop-cut/bridge), not a separate touching object.* Shrinkwrap-restricted
attachment, however cleanly it snaps contact points, still leaves **two separate mesh objects** --
one shrinkwrapped onto the other, not merged into it. That is a real, useful technique for a
genuinely separate part meant to read as a distinct component (a bolt, a vent, a bracket, a decal --
exactly the use cases in the CG Boost and Gnomon Workshop sources it came from). It is not a
substitute for join+bridge when the goal is one continuous, structurally fused surface, which a mug
handle specifically is.

**The lesson: a transfer test can honestly confirm a narrow technical claim while the broader
choice to reach for that technique at all is still wrong for the actual goal.** Passing
`apply_transfer_test()` on "does Shrinkwrap conform vertex positions" would not have meant "this is
how to attach a mug handle" -- those are different claims, and conflating them is exactly the kind
of overclaiming this project's own knowledge discipline exists to prevent.

## What was corrected as a result

- The Shrinkwrap+Data-Transfer knowledge items in
  `runs/2026-08-14_video-study-cgboost-6-tricks/knowledge_items.json` and
  `runs/2026-08-14_video-study-gnomon-bryant-momo-koshu/knowledge_items.json` now carry an explicit
  scope caveat: valid for genuinely separate detail parts, not a substitute for join+bridge when
  the goal is a single fused surface.
- A new memory entry records this correction for future sessions.
- The `HandleTest_Body` / `HandleTest_Handle` / `HandleTest_Curve` objects from the abandoned
  Shrinkwrap attempt were left in the scene, mid-setup, not cleaned up further -- superseded by this
  correction, not deleted, so the abandoned attempt remains visible as a real record rather than
  quietly erased.

## Addendum (2026-08-17): re-inspected live instead of reproducing an unwatched video

This session independently attempted to reproduce a different curved-surface fusion technique
(McGlasham's "Connecting Cylinders," Shrinkwrap+Bridge on a T-junction) purely from a video whose
frames could never actually be watched (a real, documented environment limitation, not a shortcut).
After several iterations it still had a genuine, unresolved fold defect and was scrapped rather than
fixed. That failure prompted going back to re-examine this file's own already-successful result
in detail, which had only been summarized, never actually re-inspected, since it was first built.

Re-loaded `mug_handle_join.blend` live (`restore_checkpoint`) once a working live connection became
available this session, and checked it with tools that did not exist or were not applied to it back
on 2026-08-14: `get_evaluated_defect_regions` flags 280 candidate tickets on this mesh, but the top 20
by severity are **all at the mug's own rim** (z = +-1.0, an intentional sharp cap edge), not the
handle seam at all -- the seam itself doesn't rank as notably severe by the same metric that flagged
the cylinder-join fold as the single worst thing in that entire scene. A fresh `solid`-shaded render
(`live_reinspect_solid.png`) shows both seams blending smoothly into the body with no visible pinch
or crease, matching the mesh-health numbers (0 non-manifold, only 16 poles total across 368 vertices,
8 valence-3 and 8 valence-5, symmetric and paired at the seam -- not scattered).

**The actual lesson from comparing these two attempts directly:** the technique that worked was not
one reproduced from external tutorial description at all -- it was the user demonstrating, live, in
their own hands, exactly how to grow/join/bridge a secondary curved form into a primary one. The
technique that struggled was reconstructed secondhand from a source that could only ever be partially
observed. When this project already holds a verified-good example of the same class of problem, that
is better grounding for judgment than attempting a new secondhand reproduction of a different video
covering roughly the same territory. `live_reinspect_solid.png` and `live_reinspect_wireframe.png`
are retained alongside the original evidence in this directory.
