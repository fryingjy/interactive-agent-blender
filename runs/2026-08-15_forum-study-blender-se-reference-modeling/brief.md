# Blender Stack Exchange -- reference-image modeling case study

Curriculum items #11 (Level 3, listed as "Not yet processed") and #15 (Level 5, "same as #11") --
`blender.stackexchange.com/questions/63246`, "How do I make a 3 dimensional character out of flat
picture?" Read directly (not a video), per this project's Level 16 docs/forums extraction
discipline. This closes out Level 5 ("the target capability... started, 1/2") to 2/2.

## Why this source, read now

Level 5 is explicitly flagged in the curriculum doc as "the actual target capability (\"here is a
picture, build it\")" -- the single most important curriculum item in the whole document. It had
been sitting at 1/2 since 2026-08-14 (only the Ryan King reference-image-import video processed).
Closing it out was a natural next step after finishing the two priority chapters of the 100+ Tips
video.

## What the source actually is

Not a targeted tutorial -- a general "how do I 3D-ify a flat character" question whose top answer
(110 votes, Paul Gonet) happens to walk through a real, if terse, end-to-end modeling-to-rigging
pipeline. Only the MODELING section (quad-view multi-reference setup, Mirror modifier via
bisect+delete+modifier, extrude-then-subdivide blockout order) is relevant to this project's
current scope; UV/texturing/rigging/animation sections in the same answer were read but not
extracted, since they're outside the current modeling-focused priority.

## A genuine same-day contradiction, resolved by dating

The forum answer's Mirror-modifier setup (Ctrl+R bisect, delete one half with X, then add Mirror
Modifier) is the OLDER, more destructive method. The CG Boost 100+ Tips Modifiers chapter, read the
same day (`runs/2026-08-15_video-study-cgboost-100-tips-modifiers/`, tip #84), shows the Mirror
modifier's own Bisect option now does this non-destructively without a separate manual delete step.
Recorded the forum item as `CONTRADICTED` rather than either ignoring the older source or silently
treating it as still-current -- both sources independently confirm a Mirror modifier is the right
tool for this job, they just disagree on the best way to reach the one-half-editable state, and the
newer one wins.

## Items captured (3)

1. Toggle Quad View (Ctrl+Alt+Q) for simultaneous multi-view reference checking while modeling --
   complements the already-captured reference-import knowledge (which covers setup, not ongoing
   verification).
2. The (superseded) manual bisect+delete+Mirror sequence -- CONTRADICTED by the same-day 100+ Tips
   finding.
3. Extrude-to-fit-silhouette-first, then-subdivide-for-detail blockout order -- independent
   confirmation of a sequence this project's own curriculum doc already states as its reasoning
   process for Level 5, previously uncited.

## Curriculum status after this run

Level 5 (the target capability) is now 2/2 for its listed sources. This does NOT mean the target
capability itself is achieved -- per the external assessment already on file this session, "give it
any reference and get a professional model" remains unmet. Level 5 being "complete" means its two
listed *learning* sources are processed, not that the capability has been demonstrated end-to-end.
