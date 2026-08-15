# Blender Modeling Learning Curriculum v2

Superseding `docs/VIDEO_LEARNING_CURRICULUM.md` (2026-08-14, user-authored restructuring). This
curriculum progresses **Blender fundamentals → modeling → topology → hard-surface/SubD → reference
reconstruction → production → advanced technique**, with sculpting deliberately deferred to last
(Level 15) since the target capability is reasoning from an unfamiliar reference to a professional
model, not sculpt-first workflows. Weapon-specific material is excluded by design; focus stays on
general props, products, mechanical objects, hard-surface, topology, and production.

**Governing rule for every video in this list**: follow `docs/VIDEO_EXTRACTION_PROTOCOL.md`, not a
"watch and summarize" pass. A video contributes to the system only once a claim extracted from it
survives verification and a transfer test on different geometry -- accumulating summaries of 100
videos without that loop is the failure mode this curriculum exists to avoid.

## Level 0 -- Blender fundamentals

1. **Blender Guru -- Beginner Blender Tutorial (2026).** `z-Xl9tGqH14` (4h19m). REQUIRED.
   Navigation, basic modeling, modifiers, references, materials, UVs, Geometry Nodes. Fully
   processed across two passes: modeling portion (donut/mug/handle/plate) in
   `runs/2026-08-14_video-study-blenderguru-beginner-course/` (10 items); texturing/UV/scattering
   (Geometry Nodes)/lighting portion in
   `runs/2026-08-14_video-study-blenderguru-beginner-course-part2/` (6 items) -- Non-Color texture
   space + normal-map decoding, in-shader non-destructive color grading, cylindrical-UV seam
   placement + Gridify, vertex-group-masked GN scattering, per-instance Color-Ramp randomization,
   and light-radius-driven shadow softness/three-point lighting. **Item 1 (REQUIRED) now complete.**
2. **Blender Guru -- Beginner Blender 4.0 Tutorial.** `4haAdmHqGOw`. REQUIRED/supplementary.
   Extrusion, Subdivision, Solidify, Shrinkwrap, reference-image modeling, organization. Older
   version, useful for the same reasoning taught a second way. Processed
   (`runs/2026-08-14_video-study-blenderguru-beginner-4.0/`, 5 items) -- SubD/Catmull-Clark,
   Shrinkwrap-above-Solidify stack order, mask+Mesh-Filter uniform sculpt deformation, Geometry
   Nodes point-distribute scattering, and clamped-bevel hard-surface profile modeling.
3. **CG Boost -- Retopology in Blender.** `X2GNyEUvpD4`. Later but required. Snapping, Shrinkwrap,
   F2, LoopTools, topology cleanup. Processed (`runs/2026-08-14_video-study-cgboost-retopology/`,
   7 items).

## Level 1 -- Core modeling

4. **CG Boost -- 100+ Tips to Boost Modeling in Blender.** `JMBMHSca_j0`. REQUIRED. Broad exposure
   to modeling techniques and viewport workflows. Revisit at Level 10 with a different question
   ("why would a professional choose this tool here" instead of "what does this tool do") -- that
   SECOND pass is still not done; what follows is the first pass only. **First pass COMPLETE,
   all 7 chapters processed** (video is 1:57:05; processed chapter-by-chapter across
   2026-08-15, mesh-modeling/modifiers chapters via Gemini video-understanding, the rest
   transcript-only since visual observation wasn't available/needed for their content). 44 items
   total across 7 run directories:
   - **Mesh Modeling** (29:22-58:16, tips #30-62, `runs/2026-08-15_video-study-cgboost-100-tips-meshmodeling/`,
     8 items) -- a genuine, sourced fix candidate for the project's repeatedly-confirmed T-junction
     ngon bug (Connect Vertex Path, `J`, splits an existing face along a vertex path instead of
     inserting a mid-edge vertex into a shared boundary edge), plus two independent alternative
     hole-cutting techniques (Bridge Edge Loops between matching opposing faces; Loop Tools Circle)
     and Grid Fill / batch non-manifold repair / Offset Edge Slide.
   - **Modifiers** (1:07:24-1:42:01, tips #74-93, `runs/2026-08-15_video-study-cgboost-100-tips-modifiers/`,
     6 items) -- a genuine, sourced CONTRADICTION with this project's standing Bevel-before-SubD
     policy (flagged unresolved, see `blender-modeling-technique-corrections` memory), a Weld-modifier
     technique for beveling boolean-cut seams (a real gap), a Quad Sphere construction avoiding
     UV-Sphere pole-pinching, and independent confirmation of the vertex-group-scoped
     Shrinkwrap-Project mechanism already flagged for the mug's handle-attachment failure.
   - **User Interface** (0:00-24:42, tips #01-22, `runs/2026-08-15_video-study-cgboost-100-tips-userinterface/`,
     7 items) -- deliberately fewer items (lower-value UI/viewport convenience vs. this project's
     topology/SubD/boolean priorities): MatCap/Cavity shading for reading surface defects, Local
     View over hide-invert-unhide, Align View to Face Normal for flatness checks, Quad View.
   - **Selection** (24:42-29:22, tips #23-29, `runs/2026-08-15_video-study-cgboost-100-tips-selection/`,
     5 items) -- Select Linked with Delimit:Seam, invert-the-smaller-selection strategy, Checker
     Deselect, Select Shortest Path/Fill Region, Select Similar.
   - **Transformation** (58:16-1:07:24, tips #63-73, `runs/2026-08-15_video-study-cgboost-100-tips-transformation/`,
     8 items) -- Snap to Surface as a second, distinct mechanism from Shrinkwrap for conforming
     discrete parts to curved hosts (one-time interactive snap vs. persistent modifier), plus a
     Duplicate-Linked/Copy-Object-Data kitbash workflow for modular hardware.
   - **Organization** (1:42:01-1:49:27, tips #94-100, `runs/2026-08-15_video-study-cgboost-100-tips-organization/`,
     6 items) -- Collection Instances + Mirror Collections as whole-assembly symmetry (distinct scope
     from the Modifiers chapter's Mirror-modifier-Bisect, which is single-mesh); flagged the
     part-group collection nesting shown here as an untested, plausible extension to (not a
     replacement for) this project's Model/low-poly collection convention.
   - **Bonus** (1:49:27-1:56:03, tips #101-102, `runs/2026-08-15_video-study-cgboost-100-tips-bonus/`,
     4 items) -- Draw Cables (first captured technique for cable/hose/wire-type parts, a category
     this project has never built) and a graduated weight-paint variant of the vertex-group
     Shrinkwrap technique (third independent confirmation of that mechanism now).
   Two standing follow-ups from this pass remain open, not resolved by any of the above: (1) the
   Bevel-before-vs-after-SubD contradiction needs a controlled test, not a documentation edit
   (confirmed the manual itself doesn't state a preference either -- see
   `runs/2026-08-15_docs-study-bevel-harden-normals/`); (2) the vertex-group-scoped Shrinkwrap
   Project technique (now confirmed 3 times) is still just an untested hypothesis for the mug's
   handle-attachment failure -- worth actually trying, not re-noting as plausible again.
5. **CG Boost -- Blender Hard-Surface Modeling Fundamentals.** `nsTjnQ067sw`. REQUIRED. **Already
   processed** -- `runs/2026-08-14_video-study-cgboost-hardsurface-fundamentals/` (5 items,
   transcript-only pass, pre-dates the Gemini video-understanding pipeline).
6. **The Parabox EN -- Hard Surface Modeling in Blender.** `vPeeybzxfLI`. REQUIRED. References, body
   construction, boolean details, buttons, holes, lettering, components, materials, rendering.
   Processed (`runs/2026-08-14_video-study-parabox-hardsurface/`, 7 items).
7. **CG Boost -- 6 Hard-Surface Modeling Tricks I Wish I Knew Earlier.** `Ml2t8uxPAQU`. REQUIRED.
   **Already processed** -- `runs/2026-08-14_video-study-cgboost-6-tricks/` (6 items, Gemini
   video-understanding pass).

## Level 2 -- Modifiers

8. **Blender Bash -- All 54 Modifiers Explained.** `idcFMhoSdIc`. REQUIRED as an overview. Use for
   conceptual purpose only -- verify current behavior against the Blender Manual before trusting any
   specific claim, since the video is older than the current Blender version.
   Processed (`runs/2026-08-14_video-study-blenderbash-54-modifiers/`, 4 items).

## Level 3 -- Topology

(Item 9 is CG Boost Retopology, already listed as #3 -- part of both fundamentals and topology.)

10. **JL Mussi -- Perfect Cylinders / No Shading Errors.** `XX1RCxid5QM` (found and confirmed by
    title/channel search). HIGH priority -- connects topology directly to surface quality/shading
    rather than polygon counting. Processed (`runs/2026-08-14_video-study-jl-mussi-perfect-cylinders/`,
    7 items).
11. **Blender Stack Exchange -- reference-image modeling case study.** Not a video --
    `blender.stackexchange.com/questions/63246`. Multi-view reference modeling, Mirror, extrusion,
    Subdivision. Read, not watched. Processed
    (`runs/2026-08-15_forum-study-blender-se-reference-modeling/`, 3 items) -- Toggle Quad View for
    simultaneous multi-reference checking, the (now-superseded, per the same-day 100+ Tips finding)
    manual bisect+delete+Mirror sequence, and confirmation of the extrude-then-subdivide blockout
    order.

## Level 4 -- Hard-surface modeling

12-13. CG Boost Hard-Surface Fundamentals and 6 Tricks (already listed as #5 and #7) -- revisit with
    focus on blockout, primitive construction, boolean usage, component construction, decals,
    materials, workflow order (12) and curves/cables/pipe joins/decals/normals/speed workflows (13).
14. **Josh Gambrell -- Hard Surface Modeling** (channel: `@JoshGambrell`, now rebranded "Josh -
    Blender Bros"). Do not ingest the whole channel -- identify the highest-value hard-surface
    videos specifically and study those per the extraction protocol. Channel surveyed 2026-08-15
    (full recent-videos listing reviewed; channel is now mostly Hard Ops/Boxcutter/Plasticity
    add-on tutorials and business content, not pure technique videos -- 3 videos selected as
    highest-value and processed, transcript-only):
    - **"How to fix SHADING ERRORS in Blender"** (`EdEIUkWzYY0`, 13:07,
      `runs/2026-08-15_video-study-blenderbros-shading-errors/`, 4 items) -- most valuable of the
      three: draws a real, previously-undocumented boundary on this project's own bevel-weight
      policy (Weighted Normal fixes flat-surface bevel shading distortion but NOT curved-surface
      distortion, which is a different problem requiring clean topology / denser geometry / Data
      Transfer instead), plus a Mark-Sharp-splits-into-two-holding-edges-on-bevel failure mode.
    - **"PERFECT curves with holes in Blender"** (`FjWrEccXREY`, 9:24,
      `runs/2026-08-15_video-study-blenderbros-perfect-curves-holes/`, 4 items) -- a curve-to-mesh
      construction method for tubular parts with holes (genuinely different from this project's
      repeated extrude-and-rotate-chain approach), plus independent confirmation of Loop Tools
      Circle for perfect circular holes (also found today via CG Boost 100+ Tips).
    - **"CONVERT your blocky objects into perfect bevels"** (`bgxT83mPTzI`, 10:37,
      `runs/2026-08-15_video-study-blenderbros-blocky-to-bevels/`, 3 items) -- judgment-level
      principles only (no new mechanics): full-blockout-before-any-bevels (a third independent
      source for this sequencing), bevel edge placement as a silhouette-design decision, bevel
      width as a tunable soft/hard design axis per edge.

## Level 5 -- Reference-based modeling

Critical: this is the actual target capability ("here is a picture, build it").

15. Reference-image modeling case study (same as #11).
16. Reference-image setup tutorial: front/side/top references, orthographic alignment, image scale,
    transparency, camera/view consistency, matching landmarks. `lpIonmH90-k` ("How to Use
    Background Images in Blender", Ryan King Art -- found via search). Processed
    (`runs/2026-08-14_video-study-ryanking-reference-images/`, 5 items) -- orthographic-locked
    import, reference Depth (Front/Back) for occlusion control, orthographic-only display to keep
    perspective navigation clean, locking reference collections unselectable, and multi-view
    landmark-based alignment to a shared origin. **Level 5 (the target capability) sources 2/2 --
    but this means the two listed learning sources are processed, NOT that the target capability
    itself ("give it any reference and get a professional model") has been demonstrated. That
    remains unmet per the 2026-08-14 external assessment on file in `docs/RESEARCH_ROADMAP.md`.**

Reasoning process to learn (not a fixed shortcut sequence):
```
reference -> orthographic views -> establish proportions -> primitive/blockout
-> extrusion -> multi-view checking -> Subdivision
```

## Level 6 -- Intermediate modeling

17. **Blender Guru -- Intermediate Modeling / Anvil series** (channel: `@blenderguru`). `yi87Dap_WOc`.
    HIGH priority. Jump from beginner to an actual intermediate asset workflow; later parts cover
    final modeling touches leading into UV work. Treat as modeling reasoning/training data, not
    current-API documentation (older Blender version).
    Processed (`runs/2026-08-14_video-study-blenderguru-anvil/`, 7 items) -- Part 1. **Series now
    complete, all 4 modeling parts processed (transcript-only, 2026-08-15):**
    Part 2 (`WxMwa0njGSM`, "Boolean!", `runs/2026-08-15_video-study-blenderguru-anvil-part2/`, 8
    items) -- boolean setup/cleanup; confirms this project's existing boolean-workflow gap (no Weld
    modifier, no post-boolean bevel -- this video uses manual Remove Doubles + quad-preserving
    knife-cuts instead, and defers edge rounding to support loops, not a bevel, at any point).
    Part 3 (`lITV4F_P4E0`, "Sharpening Edges", `runs/2026-08-15_video-study-blenderguru-anvil-part3/`,
    6 items) -- a third, bevel-free edge-sharpness technique (support/proximity loops narrowing the
    Subdivision Surface averaging span) that doesn't resolve the live Bevel-before-vs-after-SubD
    contradiction (see item #4 above) but adds a real adjacent data point: Edge Crease only behaves
    predictably at maximum value, not partial values.
    Part 4 (`9ViVKUiG8ks`, "Final Touches", `runs/2026-08-15_video-study-blenderguru-anvil-part4/`,
    9 items) -- edge-flow redirection via delete-face+Alt+M merge (Ctrl+E Rotate Edge explicitly
    rejected as too imprecise), and a real judgment-call principle: check reference photos for
    actual edge sharpness *before* spending effort solving a topology problem that reference may
    show doesn't need solving at all.

## Level 7 -- UVs

18. **CG Boost -- UV Unwrapping** (channel: `@cgboost`). `xPoxqOcUzNQ`. Full beginner UV-unwrapping
    workflow. Processed (`runs/2026-08-14_video-study-cgboost-uv-unwrapping/`, 7 items).
19. **Josh Gambrell -- Simple UV workflow.** `ww5BP-T28Ow` ("A Simple Approach to UVs (Practical
    Example)", found via title search on the Josh - Blender Bros channel; not the same video as
    `runs/2026-08-14_video-study-blenderbros-5-best-tricks/`, `uWyKgmTWQGE`). Practical hard-surface
    UV technique, repeatedly recommended in Blender community discussions. Processed
    (`runs/2026-08-14_video-study-joshgambrell-simple-uv-approach/`, 5 items) -- sharp-edge
    auto-seams + Conformal unwrap, clearing unneeded seams on low-curvature surfaces, cutting closed
    rings/holes, keeping bevels attached to their neighbor island, and splitting extreme-aspect-ratio
    islands for packing efficiency. **Level 7 (UVs) complete, 2/2.**

## Level 8 -- Materials and shading

20. **Blender Guru -- PBR Materials Part 1.** `V3wghbZ-Vh4`. Conceptual PBR treatment, still useful
    despite age. Processed 2026-08-14 (`runs/2026-08-14_video-study-blenderguru-pbr-materials/`) --
    6 items: Fresnel falloff, energy conservation (Cycles vs. legacy), F0/F90 grazing reflectance,
    "everything has Fresnel", roughness-dampened edge Fresnel, roughness perceptual linearization.
21. **Blender Guru -- PBR Materials Part 2: Metal.** `m1PkSViBi-M`. Physically plausible metal
    specifically. Processed 2026-08-14 (`runs/2026-08-14_video-study-blenderguru-pbr-metal/`) --
    5 items: zero-diffuse metals, wavelength-selective specular tinting, oxidation as a dielectric
    layer over a conductor, measured real-world F0 values, binary conductor/dielectric metalness
    masking.
22. **Default Cube -- procedural material fundamentals.** `O3gLBhC353Y`. Explains underlying node
    behavior rather than demonstrating a finished material; recommended directly by a Blender Stack
    Exchange discussion. Processed (`runs/2026-08-14_video-study-default-cube-procedural-materials/`,
    5 items) once the Gemini free-tier daily quota reset. **Level 8 complete, 3/3.**

## Level 9 -- Normal maps / baking

23. **Normal/displacement workflow.** `pMT0eMcUlK8`. Distinction between actual geometry, shading
    detail, normal information, and displacement. Processed
    (`runs/2026-08-14_video-study-normal-vs-displacement/`, 4 items).

## Level 10 -- Production asset workflow

24. Second pass on CG Boost's 100+ Tips (#4), asking "why would a professional choose this tool
    here" instead of "what does this tool do." Not yet done (first pass itself not yet done).

## Level 11 -- Curves / procedural modeling

25. Hard-surface curves section within CG Boost's 6 Tricks video (#7, already processed) -- when
    curves beat manually-extruded mesh for pipes, cables, hoses, wires, repeated curved elements.
    Partially covered already (the bridge-elbow and Bezier-cutter items in the existing extraction);
    revisit specifically for the curve-vs-mesh decision framing.

## Level 12 -- Geometry Nodes

26. Geometry Nodes sections within the Blender Guru 2026 beginner course (#1, partially processed) --
    scattering, points, collections, procedural variation. Goal: learn to choose between manual
    modeling / modifier / geometry nodes / curve / hybrid based on the asset, not master GN itself
    yet. Not P0.

## Level 13 -- Stylized modeling

27. **Polygon Runway -- full environment/object modeling process.** `pUdHo2maqTM` ("Winter Café
    Illustration in Blender - 3D Modeling Process", found via title search -- a genuine long-form
    full-scene walkthrough matching this item's description). Processed
    (`runs/2026-08-14_video-study-polygonrunway-winter-cafe/`, 6 items) -- camera-first composition,
    exaggerated stylized blockout proportions, modular instance-scattering for organic decoration,
    pressure-based Cloth sim as a soft-prop shortcut, low-sided-primitive-plus-bevel stylized
    hard-surface look, and warm/cool lighting contrast for mood. **Level 13 complete, 1/1.**

## Level 14 -- Professional modeling judgment

28. Search/watch professional breakdowns from CG Boost, Josh Gambrell, Blender Studio, Blender Guru,
    CG Cookie, Blender Secrets, and other experienced professional Blender artists. Extract the
    reasoning chain, not the mesh:
    ```
    reference interpretation -> blockout decision -> representation choice -> topology decision
    -> modifier decision -> detail decision -> surface/shading decision -> mistake -> correction
    ```
    Substantially covered already via videos processed outside this list's exact numbering, during
    the extended-curriculum push: `blenderbros-subd-hardsurface(-2)`, `blenderbros-subd-hive-controller`,
    `blenderbros-tertiary-details`, `blenderbros-decals-workflow`, `blenderbros-curvy-organic`,
    `blenderbros-5-best-tricks`, `cgcookie-hardsurface-intro`, `cgvoice-amateur-mistakes`,
    `crnt-boolean-triangle`, `elementza-clean-topology`, `grant-abbitt-beginners`, `gnomon-bryant-momo-koshu`,
    `jl-mussi` / `jl-mussi-5-tips` / `jl-mussi-easy-once-you-learn`, `mcglasham-subd`, `pzthree-retopology`,
    `rileyb3d-advanced-hardsurface`, `subd-3dprint` (all under `runs/2026-08-14_video-study-*/`). Not
    exhaustively cross-referenced against the reasoning-chain framework above; worth a dedicated
    synthesis pass rather than treating "processed" as "fully extracted for this specific level's goal."

## Level 15 -- Sculpting (LAST, deliberately deferred)

29. **CG Boost -- Sculpting fundamentals** (channel: `@cgboost`, course:
    `cgboost.com/courses/master-3d-sculpting-in-blender`). Treat as a later specialization, not the
    primary modeling solution -- the target capability is reasoning from reference to professional
    hard-surface/production model, and sculpting is not the primary path there.

## Level 16 -- Official documentation and community knowledge (ongoing, not a single pass)

**Governing rule, same as the video track**: read purposefully and extract real, cited
`KnowledgeItem`s (`source_id` = the manual page or forum thread URL) via
`mcp__Blender__search_manual_docs` / `search_api_docs` and targeted web search of Blender Stack
Exchange / Blender Artists -- not a "skim the whole manual" pass. Started 2026-08-14 per direct
instruction to actually learn the documentation and forums, not just reference them in passing
(the project had one prior manual citation, curriculum item #11, before this).

30. **Official Blender manual -- Bevel, Weighted Normal modifier, Bridge Edge Loops.** Processed
    (`runs/2026-08-14_docs-study-bevel-weighted-normal-bridge/`, 6 items, 5 from the manual + 1 from
    a Blender Artists forum thread). Chosen deliberately, not at random: connects directly to this
    project's standing bevel-weight policy (Face Strength + Weighted Normal Face Influence is a
    winner-take-all mechanism, not a blend) and root-causes an unresolved bug from the same session
    (Bridge Edge Loops' undocumented-in-this-project `Twist` parameter explains the teapot handle's
    twisted-bridge failure; the typed `bridge_selection` wrapper doesn't expose it yet -- a concrete
    fix, not just a diagnosis).
31. **Official Blender manual -- Bevel modifier Harden Normals / Face Strength.** Processed
    (`runs/2026-08-15_docs-study-bevel-harden-normals/`, 2 items). Chosen to try to resolve the
    live Bevel-before-vs-after-Subdivision-Surface contradiction (item #4 above) via the manual --
    it doesn't (the manual documents modifier options, not workflow-ordering recommendations; that
    question stays genuinely open, ruled out "check the manual" as the way to resolve it). Did
    surface two real, useful findings anyway: Harden Normals as a possible one-checkbox alternative
    to a separate Weighted Normal modifier pass for flat-surface bevel shading, and confirmation
    that Face Strength is explicitly meant to pair with a Weighted Normal modifier placed AFTER
    Bevel (a different, already-settled ordering question from the open SubD one).
32. Remaining manual sections and forum topics: not yet scoped. Pick the next topic by relevance to
    active work (an unresolved bug, a standing policy, a curriculum gap) the same way items 30-31
    were chosen, rather than working through the manual's table of contents in order.

## Study order (phases, not strict sequential blocking -- later phases can start once earlier ones
are "solid enough," per the extraction protocol's verification loop, not once every video is watched)

```
1. Blender fundamentals       6. Modifiers            11. Stylized / complex props
2. Basic polygon modeling     7. SubD + shading        12. Professional breakdowns
3. Reference-based modeling   8. UV + materials         13. Advanced/generalization
4. Topology                   9. Baking + production    14. Sculpting
5. Hard-surface               10. (folded into 5/9 above per this doc's level numbering)
```

## Final hierarchy this curriculum is building toward

```
1. Reference understanding   6. Curves        11. Baking
2. Blockout                  7. UV            12. Production
3. Polygon modeling          8. Materials     13. Sculpting
4. Hard surface              9. --
5. SubD / Topology           10. Modifiers
```
