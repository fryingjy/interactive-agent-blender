# Blender video-learning curriculum (v1, superseded)

**Superseded 2026-08-14 by `docs/BLENDER_MODELING_CURRICULUM_V2.md`** -- kept here as the historical
record of what was actually processed under this list (17 of 20 entries; see
`runs/2026-08-14_video-curriculum/video_manifest.json` for per-entry status and the run directories
each entry maps to). New curriculum work should follow v2 and
`docs/VIDEO_EXTRACTION_PROTOCOL.md`.

Curated by the user (2026-08-14) as the training-video dataset for this project's video-knowledge
pipeline (`knowledge_engine/video_knowledge.py`). The goal is not to summarize these videos --
it is to extract what transfers: what the artist sees, what decision they make, what operation they
perform, why, what visual problem caused the decision, and how the technique transfers to another
object. A video is learned only when its extracted knowledge helps on an unseen modeling problem,
never merely from being able to summarize it (see `apply_transfer_test` in `video_knowledge.py`).

## Priority topics

Reference analysis, form decomposition, proportion, blockout, hard-surface modeling, Subdivision
Surface, topology, edge flow, bevel strategy, boolean strategy, shading, visual problem diagnosis,
modeling decisions, professional workflow, transfer to unseen objects.

Lower priority: shortcuts, interface knowledge, rendering tricks, decorative details,
addon-specific workflows.

## Level 0 -- fundamentals

1. **Blender Guru -- Beginners Academy.** Core interface, basic mesh operations, reference
   gathering and analysis. Unusually relevant because it teaches reference analysis explicitly,
   not just tool usage. Sections: Hard Surface Modeling, Hard Surface Challenge, Gathering
   Reference, Analysis, Smooth Surface Modeling.
2. **Grant Abbitt -- Complete Beginners Guide.** Edit Mode, edge loops, loop cuts, basic
   construction. Use for geometric vocabulary only -- do not overweight; foundation material, not
   professional judgment.

## Level 1 -- first hard-surface workflows

3. **JL Mussi -- Blender Hard Surface Modeling for Beginners: Learn Pro Workflows in 2 Hours.**
   Production-oriented workflow, topology, edge flow, decision-making. Project: energy drink can.
   HIGH PRIORITY -- emphasizes repeatable professional workflows and the reasoning behind choices,
   not shortcuts. **First video actually studied** (2026-08-14, via TubeAlfred): full timestamped
   transcript in `runs/2026-08-14_video-study-jl-mussi/`.
4. **CG Cookie -- Modeling a Hard Drive in Blender.** Real-world scale, symmetry, bevels,
   modifiers, booleans, shading, disconnected details. Layered mechanical/product construction
   without being overwhelming.
5. **Blender Guru -- Hard Surface Modeling.** Primary form -> secondary form -> smaller details ->
   presentation. This hierarchy is important for the agent to internalize.

## Level 2 -- intermediate hard surface

6. **JL Mussi -- 5 Blender Hard Surface Modeling Tips.** Treat as a decision-extraction video --
   pay special attention to stated reasons for preferring one technique over another.
7. **Blender Bros -- Hard Surface Modeling: Tertiary Details.** Detail hierarchy; when to model
   detail versus represent it through shading/material.
8. **CRNT Designers -- Boolean on Triangle.** The relationship between booleans and topology, not
   booleans as a magic geometry generator.
9. **Ian McGlasham -- Hard Surfaces #12: Subdivision Surface Modeling in Blender.** SubD, inset,
   shading, lightweight controllable meshes. Key distinction: "looks acceptable" vs. "structurally
   correct and controllable."

## Level 3 -- subdivision / professional topology

10. **Blender Bros -- SubD Hard Surface Modeling Tutorial.** HIGH PRIORITY. Extract: support-loop
    placement, edge-sharpness decisions, topology redirection, transition handling, diagnosing
    pinching, preserving planar surfaces.
11. **Blender Bros -- Blender SubD Modeling for Hard Surface.** HIGH PRIORITY. Treat as reusable
    principles, not a copy-this-asset tutorial.
12. **HardVertex -- Subdivision Surface Modeling.** HIGH PRIORITY. Isolates individual topology
    problems (cylinders, spheres, transitions, radial topology, ridge clusters, retopology) rather
    than hiding them inside one large asset build.
13. **Squeaky Clean Topology in Blender -- Topology on a Hard Surface.** Hard-surface topology is
    not "make everything quads" -- learn why topology flows where it does, where it can terminate,
    how normals affect appearance, how structure affects later editing.

## Level 4 -- advanced hard surface

14. **RileyB3D -- Blender Modeling Tutorial: Advanced Hard Surface.** HIGH PRIORITY. Blockout,
    lattice, circular forms, secondary detail, shrinkwrap, proportional editing. Extract the
    reasoning behind the progression from broad shape to specific geometry.
15. **Blender Bros -- Subdivision Surface Modeling Program.** One of the most important long-form
    sources here. Prioritize lessons on shape construction, topology, redirection, shading,
    cleanup, and difficult transitions.
16. **Elementza -- Hard Surface Topology Workshop.** HIGH PRIORITY. The point is not the finished
    model -- it is why a professional chooses one topology structure over another.
17. **Blender -- Expert in Hard Surface Modeling.** Use after fundamentals are established.

## Level 5 -- professional / expert observation

18. **Advanced hard-surface breakdowns** (RileyB3D, Blender Bros, Josh Gambrell, Arrimus 3D,
    Elementza, HardVertex and similar). Don't ask "what steps did they follow" -- ask "what did the
    artist notice that caused them to change strategy."
19. **Professional modeling breakdowns.** Prefer videos where the artist receives a reference,
    analyzes it, blocks out proportions, makes construction decisions, encounters problems, changes
    topology, fixes shading, revises. Valuable because they expose decision-making under
    uncertainty.
20. **Long-form real project work** (30-180 minutes, complete assets, real client/product work,
    minimal cuts, visible UI, commentary). Potentially more valuable than a polished 10-minute
    tutorial because it exposes mistakes, iteration, and expert judgment.

## Recommended consumption order

1. Phase 1 (basic language): items 1-2.
2. Phase 2 (hard-surface fundamentals): items 3-5.
3. Phase 3 (intermediate decisions): items 6-9.
4. Phase 4 (SubD + topology): items 10-13.
5. Phase 5 (advanced construction): items 14-17.
6. Phase 6 (expert observation): items 18-20.

## Video selection rules

Prefer videos that show the entire modeling process, show the viewport clearly, contain spoken
explanation, explain why (not only what), show reference images, show intermediate states, show
mistakes or revisions, contain topology decisions and multiple strategies, and build objects that
differ from previous entries in this list.

Avoid overweighting UI-introduction videos, "N shortcuts" videos, purely decorative modeling,
uncommented timelapses/speed-modeling, and tutorials that only reproduce one asset without
explaining decisions.

## The ultimate test

After consuming a group of videos, give the agent a new reference that does not appear in any
training video and ask it to: analyze the reference, decompose the object, identify relevant
learned techniques, explain why they apply, select a strategy, build the object, compare against
the reference, identify visual failures, revise, and report which learned principles actually
transferred. A video is successfully learned only when its extracted knowledge measurably helps on
an unseen modeling problem -- not when the agent can summarize it. This is implemented directly as
`apply_transfer_test` in `knowledge_engine/video_knowledge.py`.
