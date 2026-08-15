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

1. **Blender Guru -- Beginner Blender Tutorial (2026).** `z-Xl9tGqH14`. REQUIRED. Navigation, basic
   modeling, modifiers, references, materials, UVs, Geometry Nodes.
   Status: partially processed (`runs/2026-08-14_video-study-blenderguru-beginner-course/`) --
   modeling portion covered (donut/mug/handle/plate), texturing/lighting/Geometry-Nodes portion not
   yet covered.
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
   ("why would a professional choose this tool here" instead of "what does this tool do"). Not yet
   processed (first pass).
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
    Subdivision. Read, not watched. Not yet processed.

## Level 4 -- Hard-surface modeling

12-13. CG Boost Hard-Surface Fundamentals and 6 Tricks (already listed as #5 and #7) -- revisit with
    focus on blockout, primitive construction, boolean usage, component construction, decals,
    materials, workflow order (12) and curves/cables/pipe joins/decals/normals/speed workflows (13).
14. **Josh Gambrell -- Hard Surface Modeling** (channel: `@JoshGambrell`). Do not ingest the whole
    channel -- identify the highest-value hard-surface videos specifically and study those per the
    extraction protocol. Not yet processed; channel not yet surveyed.

## Level 5 -- Reference-based modeling

Critical: this is the actual target capability ("here is a picture, build it").

15. Reference-image modeling case study (same as #11).
16. Reference-image setup tutorial: front/side/top references, orthographic alignment, image scale,
    transparency, camera/view consistency, matching landmarks. Specific video not yet identified --
    search and verify before treating any specific one as canonical.

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
    Processed (`runs/2026-08-14_video-study-blenderguru-anvil/`, 7 items) -- Part 1 only; later
    parts of the series not yet located/processed.

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
