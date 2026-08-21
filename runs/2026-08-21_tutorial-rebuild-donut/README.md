# Tutorial rebuild: Blender Guru "Beginner Blender Tutorial" (donut + mug)

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

## Plan for this run

Work through Part 1 first (this session), then Part 2, then continue part by part in later turns --
each part gets its own verified `DecisionTransaction`-backed construction pass and a render
comparison against what the tutorial actually shows, not just a health check. Not attempting to
compress multiple parts into one pass.
