# CG Boost -- 100+ Tips to Boost Modeling in Blender (Modifiers chapter)

Second chapter of curriculum item #4's first pass (see
[[../2026-08-15_video-study-cgboost-100-tips-meshmodeling/brief.md]] for the Mesh Modeling chapter
and the overall video's scope). This run covers **Modifiers** (1:07:24-1:42:01, tips #74-93 of
101), chosen next because it was flagged as the highest-value remaining chapter for this project's
active bevel/SubD/boolean work.

## Most important finding: a real contradiction with the standing bevel-weight policy

Tip #81 ("Clean Hard-Surface Sub-D Modeling") demonstrates Crease/Weight -> Subdivision Surface ->
Bevel (Weight limit, Harden Normals), explicitly framed by the video as avoiding pinched shading on
curved hulls -- the REVERSE order of this project's own standing policy in
[[blender-modeling-technique-corrections]] #2 ("Bevel modifier ordered BEFORE Subdivision
Surface"). This is recorded as a `PRINCIPLE`-type knowledge item with `status: CONTRADICTED`, not
silently resolved in either direction. Plausible reconciliation, not yet tested: the right order
may depend on WHAT the bevel represents -- a physically-radiused edge meant to read as genuinely
round even in a close-up (Bevel before SubD, so SubD then smooths the bevel's own facets) vs. a
crisp mechanical seam meant to stay sharp-edged at any distance (Bevel after SubD, so SubD doesn't
get a chance to round the bevel itself). This needs an actual controlled test (bevel-before-SubD vs
bevel-after-SubD on the same test edge, compared for pinching/distortion) before the existing policy
memory is edited -- flagged here, not fixed here.

## Second finding: independent confirmation of the mug's untested shrinkwrap hypothesis

Tip #93 (vertex-group-scoped Shrinkwrap Project) is the same mechanism [[video-curriculum-mug-diagnosis]]
already flagged as an untested hypothesis for the mug's unresolved handle-attachment failure. This
doesn't prove it will work on the mug, but it's now confirmed as a real, established technique from
an independent source (not just a plausible guess), which raises the priority of actually testing it.

## Other items captured

- Multiple stacked Bevel modifiers scoped by Vertex Group (tip #80) -- for cases needing different
  bevel radii on the same object, not currently expressible with this project's single-bevel-by-weight
  approach.
- Weld modifier between Boolean and Bevel (tips #82-83) -- fills a real, previously-unaddressed gap:
  this project's boolean workflow has never included post-boolean cleanup/beveling.
- Quad Sphere via Cube + Subdivision + Cast-to-Sphere (tip #90) -- the correct starting primitive for
  any future round hard-surface part (domes, ball joints), avoiding UV-Sphere pole-pinching.
- Mirror modifier's Bisect option (tip #84) -- non-destructive alternative to manually deleting half
  a mesh before mirroring.

## Not captured as formal items

Tips #74-78 (Quick Favorites, Apply All Modifiers, batch Alt-editing, Copy Modifiers, Harden Normals
basics -- UI/workflow conveniences, no typed-op-surface implication), #85 (Affect Only Origins for
mirror position), #86 (array+boolean grille pattern -- useful someday but no active need), #87-89
(circular array / SimpleDeform bend / curve-and-hooks for tentacle rigs -- organic/rigging-adjacent,
outside current hard-surface priority), #91-92 (Skin modifier, Multires sculpting -- different
construction paradigms than this project's current edge-loop/decision-transaction approach, worth
revisiting only if a future asset genuinely calls for them).

## Remaining chapters for curriculum item #4

User Interface (0:00-24:42), Selection (24:42-29:22), Transformation (58:16-1:07:24), Organization
(1:42:01-1:49:27), Bonus (1:49:27-1:56:03) still not processed. None flagged as urgent the way Mesh
Modeling and Modifiers were -- lower priority for a future pass, not blocking.
