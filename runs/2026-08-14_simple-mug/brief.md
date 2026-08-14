**Note (2026-08-14, second write):** this file and its reference photo were lost once already --
built earlier the same session, never committed to git, then deleted along with every other `runs/`
folder during a blanket "wipe all historical runs except the blend-file study" cleanup that didn't
account for this one still being active work. Recreated from conversation context; the reference
photo was re-downloaded (same file, same public-domain source, already-approved earlier this
session). Lesson for future broad cleanups: check for in-progress work before wiping a whole
directory tree, not just already-completed/committed folders.

**Final status (2026-08-14, third write): SCRAPPED per direct user instruction** ("ok scrap this
and all the other models for the time being you still have no clue how to model things"). Third
attempt was mid-build (body + hole-cutting + torus arc all clean and verified) when an unexplained
duplicate object appeared right as the live connection dropped again -- a fourth technical surprise
across three attempts on one asset, on top of an earlier real correction (disconnected-topology
handle) and real data loss (two full attempts lost to unexplained session resets). No `.blend`
survives; none should be recreated without explicit direction to resume. All active modeling work
is paused in favor of the video-learning curriculum. The reference photo, decomposition record, and
the lessons below remain as the durable record of this asset.

# Skill-building build #3: simple diner mug (revolved body + one justified handle)

**Purpose (2026-08-14):** third entry in the bottom-up curriculum. The crate tested a box-primitive
multi-part assembly (16 repeated parts, one component *type*); the tumbler tested a single revolved
shell with zero secondary parts. Neither tested real component-decomposition judgment -- deciding
what stays one connected surface versus what is a genuinely separate, justified secondary part. A
mug does: one revolved primary body plus exactly one handle.

## Reference

`reference/coffee_cup.jpg` -- a public-domain photo ("Coffee cup (1).jpg", Wikimedia Commons,
author Jon Sullivan / PDPhoto.org, released into the public domain, free for any use including
commercial), downloaded 2026-08-14 with explicit user permission.

## What the reference actually shows, and a disclosed limitation

A dark blue ceramic diner-style mug, photographed close up and at a steep downward angle, filled
with coffee. Visible construction: straight-sided cylindrical body, thick ceramic wall; a distinctly
thicker, lighter-colored rolled rim band; a thick, round-cross-section, C-shaped handle attached to
the side in roughly the lower two-thirds of the body height, with a visible gap between the handle's
top attachment and the rim. The base is not visible -- the photo is cropped close and shot from
above.

**Disclosed limitation:** the crop and angle prevent measuring exact height, diameter, wall
thickness, or handle placement directly. Proceeding from generic, reasonable diner-mug proportions
(body diameter ~8cm, height ~9.5cm, wall ~4mm) informed by what *is* visible. MEDIUM confidence.

## Construction history (this is the second full attempt within the same session)

**First attempt:** built the handle as a standalone curve-swept tube, a separate object merely
touching the body. Corrected directly by the user: a handle that reads as fused to the body must be
grown from the body's own mesh (extrude/loop-cut/bridge), not a separate object -- see
`blender_handle_connected_topology.md` in memory. That attempt was abandoned.

**Second attempt:** tried building the handle as connected topology via manual face-ID selection,
loop cuts, and `inset_selection` on a curved wall patch. `inset_selection` repeatedly produced
degenerate zero-area faces on the segmented cylindrical boundary regardless of thickness -- a real,
documented limitation now in `transaction_recovery.md`. Also lost twice to unexplained live
Blender/session resets before either technique could finish, costing significant time. Abandoned.

**Third attempt (informed by the user's own live demonstration):** the user built a working handle
directly in Blender while being observed -- a torus, bisected to keep only the outer arc, joined
into the body, bridged into two holes cut in the wall, finished with a Subdivision Surface modifier
(not Bevel) plus Smooth by Angle. This is the technically correct approach for a genuinely round,
continuous form: a bevel fakes roundness with a small chamfer, SubD actually rounds a shell. This
build (the one in `mug.blend` alongside this brief) follows that demonstrated technique on the real,
correctly-scaled `Mug_Body`, and additionally applies a transfer test of two knowledge items
extracted from `runs/2026-08-14_video-study-jl-mussi/` (JL Mussi's hard-surface tutorial):
divisible-by-four cylindrical segment counts, and watching for vert-pinching under SubD near tight
transitions.

## Success bar

1. Direct visual comparison against the reference before declaring complete.
2. Fresh-process verification: 0 non-manifold edges, 0 degenerate faces.
3. Reads as a mug with a correctly placed, correctly proportioned, properly connected handle.
4. Record the transfer-test result for the two applied knowledge items in
   `runs/2026-08-14_video-study-jl-mussi/knowledge_items.json`, pass or fail, honestly.
