# Tutorial rebuild: Blender Guru "Beginner Blender Tutorial" (donut + mug)

> **REJECTED / SUPERSEDED:** this run stopped after Part 6 and its latest render has poor object
> placement, a visibly faceted coffee surface, no sprinkle-scattering stage, and weak final
> composition. It remains as failure evidence only. Continuation moved to
> `runs/2026-08-22_tutorial-blenderguru-beginner-rebuild-v2/` under the strict apprenticeship gate.

## Why this exists

Direct instruction: scrap every prop model this project has ever attempted (see the deletion commit
on `main`, all six prop-build run directories removed) and restart from beginner Blender tutorials,
building exactly what each tutorial shows with maximum accuracy, before working back up toward
original commercial-product modeling.

## What's being followed

Blender Guru's "Beginner Blender Tutorial (2026)" (YouTube `z-Xl9tGqH14`, ~4h19m, the current version
of the long-running "donut tutorial" -- confirmed via `youtube_video_get`, not assumed from the
title alone). Two earlier sessions on this project already pulled and lightly analyzed portions of
this same video (`runs/2026-08-14_video-study-blenderguru-beginner-course/`, `-part2/`) but never
actually built anything from it -- this run is the first to actually construct the tutorial's own
objects, not just extract technique notes.

Chapters, per the video's own timestamps:
0:00 Part 1 (Basics) -- 28:16 Part 2 (Basic Modelling) -- 59:05 Part 3 (Organic Modelling) --
1:30:13 Part 4 (Materials) -- 2:03:46 Part 5 (Texturing) -- 2:35:40 Part 6 (UV Unwrapping) --
3:09:26 Part 7 (Scattering) -- 3:46:11 Part 8 (Lighting and Rendering).

Working through this from the beginning, one part at a time, actually building in Blender at each
step rather than reading ahead -- matching "start at beginner tutorials and work your way up."

## Part 1: donut base + mug base (transcript reviewed directly, paraphrased below -- not reproduced)

Two objects get started in Part 1, in parallel:

**Donut**: `Add > Mesh > Torus`, scaled down to a real-world-plausible size (major radius ~0.1m,
minor radius roughly half that, tuned by eye), major segments left near default (48), minor segments
increased somewhat (18) for a rounder cross-section, then Shade Smooth. This is the whole of Part 1's
donut work -- shaping/icing/sprinkles come in later parts (Organic Modelling, Scattering).

**Mug base**: `Add > Mesh > Cylinder`, sized roughly like a real mug, with a deliberately LOW vertex
count (the tutorial explicitly picks a low base resolution because a Subdivision Surface modifier
will double geometry on top of it later -- starting high would compound into an unnecessarily heavy
mesh). The top face gets deleted (face-select, delete faces only, not vertices) to open the cup.
Wall thickness comes from a Solidify modifier (non-destructive -- the real mesh underneath stays a
single open-ended tube). A Subdivision Surface modifier then rounds the whole thing, and two loop
cuts (near the rim and near the base) tighten the smoothing so it doesn't over-round those edges --
without them, the SubD interpolates across too wide a span and rounds the rim/base further than
intended, exactly the geometric behavior a SubD modifier is defined by (averaging toward
increasingly distant existing points without an edge loop to stop it early). An inset (not a plain
loop cut) closes off the bottom face cleanly, avoiding the n-gon/"starfish" pattern a single loop cut
would leave on a face with more than 4 sides.

## Part 2: mug handle (reviewed directly -- this is what the earlier `knowledge_items.json` notes
already described accurately)

Before extruding the handle, the Solidify modifier must be applied (baked into real geometry) --
otherwise the still-live modifier re-applies wall thickness to the newly-extruded handle too,
breaking it. The handle is built as a sequence of real extrusions from one face on the mug body
(Ctrl+right-click extrudes and auto-aligns each segment to the curve), looped back around to meet
the body again, then joined to the body by creating real faces between matching vertex pairs (not a
boolean, not overlapping/intersecting geometry) -- and any interior face left over from the join
must be deleted, or smooth shading reads as broken across that seam even though the outer surface
looks joined.

## Part 2 built: mug handle, a genuinely subtle bug chain

Baked the Solidify modifier into real geometry first (`bpy.ops.object.modifier_apply`), matching the
tutorial's own instruction. Building the actual handle loop took four attempts, each caught by a real
structural health check rather than assumed clean:

1. **Repeated `extrude_face_region` calls, feeding all returned faces back into the next
   extrusion.** `extrude_face_region` on one quad returns the new cap face *and* the connecting
   side-wall faces -- feeding all of them back in compounds into self-intersecting geometry. Caught
   by a direct vertex/edge dump (20 non-manifold edges, 2 degenerate faces), not by eyeballing a
   render.
2. **Selecting the cap face by matching its normal direction to the original face's normal**, then
   continuing to extrude from just that one. Diagnostic prints showed this actually worked correctly
   in isolation (each step's own candidate list only ever held one face) -- so this wasn't the real
   remaining bug, just a correct fix for a problem that turned out to have a second, separate cause.
3. **Switched to the swept-cross-section + `bridge_loops` technique** already proven this session on
   the KUPONG arch and Swingline throat (build each ring's vertices directly at each path position,
   bridge consecutive rings) -- fixed the non-manifold edges (0), but 2 degenerate faces persisted at
   the exact same location. Matches this project's own documented `bridge_loops` twist/ambiguous-
   pairing bug class, so the next attempt removed all automatic pairing.
4. **Fully explicit, by-index face construction** (no `bridge_loops` at all) still produced the same
   2 degenerate faces -- proving the twist-bug hypothesis wrong. Traced by hand: the handle's
   semicircular arc path samples parameter values that are mirror-symmetric around its peak (with
   5 segments, t=0.4 and t=0.6 give the identical sine value, hence the identical X position), and
   those two mirror-symmetric rings land *directly adjacent* to each other in the walk. Every vertex
   in the connecting face between them then shares both X and Y (the cross-section's own local
   coordinate only varies in Y and Z, not X), leaving a face collinear in Z alone -- genuinely
   zero-area, not a winding-order bug. Fixed by using 4 segments instead of 5: t=0.25 and t=0.75 are
   still a mirror pair, but t=0.5 sits between them in the walk, so no two *adjacent* rings ever share
   an X position.

Final state: 0 non-manifold edges, 0 degenerate faces (2 remaining n-gons are the pre-existing flat
bottom-cap faces from Part 1's cylinder base, not curved surfaces, not a defect per this project's
own SubD topology guidance). Verified two ways: the structural health check, and a render from the
handle's own side (`part2_handle_side.png`) rather than the first isometric angle tried
(`part1_iso.png`'s camera direction mostly occluded the handle behind the mug body -- rendering from
the wrong side would have looked like nothing changed). Reads as a real, smoothly-blended handle with
no visible seam.

## Part 3 built: donut icing, another real bug caught before it got saved silently

Followed the tutorial's actual technique rather than a fluid simulation (which the video explicitly
rejects as unreliable and uncontrollable): duplicate the donut, delete the bottom half (faces only,
keeping the boundary), Solidify with an inverted offset (thickness goes outward, not into the donut),
a proportional-editing-equivalent random height nudge along the boundary (smoothed across neighbors
so it reads as an organic ripple, not per-vertex noise), several drip tendrils extruded from
boundary edges at varied depths, Subdivision Surface to round the drips, a Shrinkwrap modifier
targeting the donut moved to the *top* of the modifier stack (the tutorial is explicit that order
matters -- shrinkwrap has to re-snap the shape before thickness/subdivision build on top of it, not
after), and edge crease on the original seam so the icing reads as clinging to the donut rather than
merging into an overly-rounded blob.

**A real bug this time, caught by a sanity check before it could save silently, not by a render
glance.** After building the drips, `state_probe.mesh_health` on the result showed 926 non-manifold
edges against only 1749 total -- far more than a normal open-boundary shell should ever show. First
hypothesis: stale `BMEdge` references reused across the drip loop's repeated topology-changing
extrusions (a bmesh gotcha this project has hit before). Rewrote to re-query boundary edges fresh, by
position, before every single extrusion -- **identical result, 816 loose edges and 384 loose verts,
proving that hypothesis wrong.** Isolated it properly instead of guessing again: checked topology
right after each individual step, and found the corruption was already present immediately after
deleting the bottom half, before any drip or boundary edit ever ran. Root cause:
`bmesh.ops.delete(..., context="FACES_ONLY")` deletes only the face records and deliberately leaves
every edge and vertex behind regardless of whether anything still uses them -- not the same as the
tutorial's own "delete faces" (which cleans up whatever becomes genuinely orphaned as a result).
Fixed by using `context="FACES"` instead. Added an explicit loose-edge/loose-vert check that raises
before `bm.to_mesh()` can ever write a broken result to the file, rather than relying on a later,
separate health-check pass to catch it after the fact.

Final state: 0 loose edges, 0 loose verts, 0 degenerate faces, 110 non-manifold edges -- exactly
matching the seam edge count, the same legitimate open-boundary pattern the mug had before its own
Solidify modifier was baked. Verified visually too (`part3_final_iso.png`): a real icing layer with
visible drip tendrils, correctly clinging to the donut via the (correctly-ordered) shrinkwrap and
crease.

## Part 4, first piece: the plate

Part 4 opens by finally showing the "homework" object teased at the end of Part 3 (a plate), before
moving into materials, camera setup, and a lattice-deform pass on the donut. Built the plate first,
as its own real object: a circle (ngon fill) extruded up and capped open, boundary scaled out for a
lip, a second extrusion (no vertical move, scaled out) for a flat rim shelf, a third extrusion
straight up (Z-locked) for the rim wall, Subdivision Surface, and Solidify moved to the top of the
stack -- the same "modifier order matters" pattern as the mug and icing.

**First attempt was structurally clean but a real design failure, caught by actually looking at an
isolated render, not just the health check.** The initial wall height (0.01) against the plate's
~0.18 radius read as almost perfectly flat from a proper side view -- barely distinguishable from a
coaster, not a plate with the rim the tutorial explicitly calls a hard requirement ("you can't just
have a plate, it's always got to have a rim on"). This is the same category of lesson as the
Swingline stapler's rejected construction earlier this project: a health check proves the geometry is
valid, never that the design reads correctly. Reverted (not git-committed yet) and rebuilt with a
taller cap extrusion (0.012) and rim wall (0.022, roughly double) -- now clearly reads as a plate
with a real, visible rim and a flat well, confirmed with the same isolated side-view render technique
used to verify the Swingline hinge throat and mug handle.

Structurally: 0 loose/degenerate, 32 non-manifold edges matching the open top boundary (32-segment
circle, same legitimate open-shell-before-Solidify pattern as every other part), 1 ngon (the
intentional flat bottom cap, matching the tutorial's own ngon fill choice for the base circle).

## Part 4 finished: materials, lattice-deform lumpiness, camera, ray tracing

Principled BSDF materials for every object, matching the tutorial's real values: pink icing and
brown donut both with Subsurface weight=1 and a neutral (not the reddish character-skin default)
scatter color for a milky food-like look; a dark, near-black (not pure black -- true black rarely
occurs on a real surface) glossy mug; a lighter glossy plate; a simple plane as a table backdrop
(matching the tutorial's own point that a full table model is unnecessary fakery when the camera only
ever sees its top surface).

Lattice Deform Selected on the donut+icing pair: a 3x3x3 lattice, the middle W-row scaled inward
(the real detail the tutorial gives a reason for -- a donut fries on both sides but not at its
equator, so the middle band is genuinely less puffy on a real one), plus two asymmetric bumps for
handmade-looking irregularity, applied to bake the deformation into both meshes. Blender warned the
modifier "was not first" when applied (Icing already had Shrinkwrap/Solidify/Subdivision on it) --
structural health stayed clean afterward (0 non-manifold/degenerate beyond the same legitimate seam
count as before), and the render shows the intended irregularity, so left as-is rather than chasing a
warning that didn't correspond to an actual defect.

Camera positioned for a 3/4 view of the group, a simple area light added, EEVEE with ray tracing
enabled (the tutorial calls the default-off setting a mistake -- it's what produces bounce lighting
and real reflections instead of flat, plasticky shading). First render composition was too tight
(cropped the group); repositioned the camera and enlarged the table plane to fix it.

## Part 5: UV unwrapping done for real; PBR texturing substituted honestly, not skipped silently

Part 5's real technique is downloading photo-scanned PBR texture maps (base color, normal, roughness)
from Poliigon and wiring them through shader nodes (Image Texture -> Normal Map node for
color-to-vector conversion, correct non-color data space for anything but base color). That first
step needs a real account and an internet download from a specific commercial vendor -- outside this
project's own established restriction on autonomous web-fetching, and a copyright concern for
downloading proprietary texture assets even under a free tier. Substituted Blender's own procedural
textures (Noise Texture nodes) for the table's material, keeping the actual reusable skill intact:
the same node graph shape (a Bump/Normal Map node between a grayscale source and the Normal input,
non-color data space, a separate roughness variation source) rather than skipping shader-node
texturing entirely.

The UV unwrapping step has no such dependency and was done for real: marked seams around the icing's
outer boundary (reusing the same edge loop that already carries the crease) and one more seam around
the donut's inner hole, then unwrapped angle-based -- necessary because the icing's UVs, inherited
from the base torus, no longer match the mesh after all the drip extrusions and lattice deformation.

Also caught and fixed a real exposure problem, not a broken material: the table looked blown-out
white at the original 40W area light energy (fine for a much larger scene, way too strong this
close), then overcorrected to near-black at 1.2W. Settled on 5.0W/0.5 size as a reasonable middle
ground -- confirmed the base color/normal/roughness node graph itself was correctly linked the whole
time by checking `is_linked` directly rather than guessing from the render alone.

## Part 6: mug UV unwrap, coffee foam, and the Swingline coordinate bug recurring in a new place

Mug UV unwrap done for real, without the Mio3 UV extension (another external download, same
substitution reasoning as Part 5's PBR maps): seams placed at every sharp-angle edge (the handle's
real boundary with the body, the crown/rim/base transitions) plus the base cap boundary -- 110 seam
edges total, more fragmented than the tutorial's minimal hand-placed set, but a real, functioning
unwrap rather than the primitive cylinder's meaningless inherited UVs. Then angle-based unwrap.

Coffee foam: reused the mug's own inner-rim edge loop (found by comparing radius within the top
height band, not modeled fresh) as the foam disc's boundary, filled, double-inset for the raised
surface-tension edge real liquid shows against a rim, shade-smoothed, UV unwrapped, and given a
procedural foam-like material (noise-driven roughness/bump, substituting for the coffee-foam atlas
texture -- same external-download constraint as every other real PBR asset this project can't fetch).

**Caught the exact same class of bug already fixed once this project, in a new place.** The first
render showed a flat white disc sitting on top of the *donut*, nowhere near the mug. Root cause:
the foam's boundary vertices were read directly from the mug's mesh data (`bmesh.from_mesh`), which
is always in the mug object's *local* space -- and used as-is for a brand-new object whose own
origin is world `(0,0,0)`, not the mug's actual world position `(0.3, 0, 0.075)`. This is the
identical mistake already found and fixed on the Swingline stapler's hinge throat and anvil recess
earlier this project, just recurring in a different construction (copying geometry data *between*
two different objects, rather than editing one object's own mesh against its own origin). Fixed by
applying `mug.matrix_world` to every captured vertex before using the positions for the new object.
Worth stating plainly rather than filing away: this bug class has now cost real debugging time twice
on two unrelated builds -- any future script that reads vertex data from one object to place geometry
relative to another needs to convert through `matrix_world` as a matter of course, not as an
afterthought caught by a render.

## Plan for this run

Parts 1-6 done (donut, mug + UV unwrap, icing, plate, materials, lumpiness, camera/lighting, coffee
foam). Part 7 (Scattering -- sprinkles via geometry nodes) is next. Continuing part by part, each
with its own verified construction pass, a real structural sanity check performed *before* saving,
and an isolated render from the correct angle before trusting a shape, position, or composition reads
the way it's supposed to.
