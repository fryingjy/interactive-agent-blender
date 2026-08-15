# Official Blender manual -- Bevel modifier Harden Normals / Face Strength

Level 16 (official documentation, ongoing track). Read directly via `search_manual_docs` (bundled
manual RST, not a live web fetch). Picked as the next Level 16 topic specifically because it's
relevant to active work, per that level's own governing rule ("pick the next topic by relevance to
active work... rather than working through the manual's table of contents in order") -- searched
for manual guidance on Bevel-modifier-vs-Subdivision-Surface stack ordering, which is the live
unresolved contradiction found earlier today (three independent tutorial sources disagree/add
nuance, see [[blender-modeling-technique-corrections]]).

## What was actually found (and what wasn't)

The manual does NOT contain direct guidance on Bevel-before-vs-after-Subdivision-Surface ordering --
searched multiple phrasings ("bevel modifier order subdivision surface stack", "modifier stack
order recommendation subsurf", "pinching subdivision surface bevel corner") and got no relevant
hits. This is consistent with that question being a workflow/technique judgment call (the kind of
thing tutorials disagree about) rather than a documented API/reference fact -- the manual describes
what each modifier's options DO, not which order to combine them in for a given aesthetic goal. The
open contradiction remains genuinely open; this search ruled out "check the manual" as a way to
resolve it, which is itself useful to know (the real answer will have to come from a controlled
test, not a documentation lookup).

What the search DID surface, on the Bevel Modifier's own options page: a built-in **Harden
Normals** option that does, in one Bevel-modifier checkbox, close to what this project has been
using a separate Weighted Normal modifier for on flat-surface bevels -- and an explicit statement
that the Bevel modifier's **Face Strength** option is specifically designed to be read by a
Weighted Normal modifier placed AFTER it in the stack (with Face Influence enabled), confirming and
sharpening this project's existing but vaguer note about Face Strength being a "winner-take-all
mechanism."

## Items captured (2)

1. PROCEDURE -- Bevel modifier's Harden Normals option as a possible one-step alternative to a
   separate Weighted Normal modifier pass for flat-surface bevel shading. Not yet tested against a
   live asset in this project.
2. PROCEDURE -- Face Strength is explicitly meant to be paired with a Weighted Normal modifier
   placed after Bevel in the stack; confirms and sharpens the existing project note.

## What this does NOT resolve

The live Bevel-before-vs-after-Subdivision-Surface contradiction is unaffected by this run -- Harden
Normals and Face Strength/Weighted Normal are both about fixing SHADING on a bevel's own faces,
which is a different question from WHERE in the stack the Bevel modifier itself sits relative to
Subdivision Surface. Still needs a controlled test (bevel-before-SubD vs bevel-after-SubD on the
same test edge, compared for pinching) before the standing policy memory is edited either direction.
