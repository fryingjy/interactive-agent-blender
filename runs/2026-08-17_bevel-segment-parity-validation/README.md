# Validating a CAPTURED skill end-to-end: Bevel segment parity vs. corner triangles

First full run through this project's `review -> reproduce -> transfer -> visually inspect ->
technically verify -> integrate with retrieval -> commit` pipeline for a single CAPTURED knowledge
item, chosen because it was the cleanest, most exhaustively-testable claim in the current backlog
(a discrete face-count fact, not a subjective surface-quality judgment) and because "convert
CAPTURED knowledge into tested runtime skills before expanding the library further" was the
explicit priority.

## Source claim (CAPTURED, transcript-only, not promoted as-is)

From `runs/2026-08-17_video-study-mcglasham-subd-primitives-and-connections/knowledge_items.json`:
odd Bevel segment counts create a triangle at a corner where multiple bevels meet; even counts
"keep the corner all-quad." Confidence 0.5, transcript-only -- exactly the kind of claim this
project's own discipline says must not be promoted without visual review and transfer.

## What was actually done, live, over the typed decision-transaction protocol

Four cubes, built and beveled through `mcp__modeler__begin_decision` / `perform_decision` /
`verify_decision` / `commit_decision` (not a headless batch script), with per-face vertex counts
queried directly via bmesh after each result (not trusting this project's own `mesh_health.ngons`
field alone -- see below):

1. **BevelTestOdd / BevelTestEven**: one isolated 3-edge corner, `segments=1` vs `segments=2`.
2. **BevelTestFullOdd / BevelTestFullEven**: all 12 edges of a fresh cube, `segments=1` vs
   `segments=2` -- the transfer test, genuinely different geometry (whole-object scope, not one
   hand-picked corner).

`wireframe_odd_vs_even.png` and `wireframe_full_odd_vs_even.png`: isometric wireframe renders
confirming the difference visually (a single sharp facet per corner at odd segments vs. a more
filled, rounder corner at even segments).

## Result: the core claim holds exactly; the stronger claim was wrong, and transfer testing caught it

| | Single corner (3 edges only) | Full cube (all 12 edges) |
|---|---|---|
| `segments=1` | 1 triangle, 6 quads, 3 pentagons | 8 triangles, 18 quads (one triangle per corner) |
| `segments=2` | 0 triangles, 12 quads, **3 hexagons** | 0 triangles, **54 quads, 0 ngons** |

The triangle-vs-no-triangle half of the source claim is confirmed exactly, both times. The
"all-quad" half is **not** literally true in general -- a partial corner bevel (segments=2, only
some of the edges at that vertex included) still leaves ngons behind. It only becomes genuinely
all-quad when every edge meeting at the vertex is beveled together, which the full-cube case does
automatically and the single-corner case does not. This is exactly the kind of source-claim
correction this project's own discipline exists to produce -- "always"/"never" language converted
into a conditional rule with the condition stated explicitly, not silently promoted as stated.

## A real gap found in this project's own tooling, not just the source

`mesh_health.ngons` reported `0` for the 8-triangle all-edges-beveled cube. Confirmed directly: this
field only counts faces with 5 or more vertices and silently excludes triangles. Anyone relying on
`ngons == 0` alone to mean "no bad faces" would miss triangles entirely. Recorded as a
`required_observations` item in the resulting skill file so this doesn't get re-discovered the hard
way on a real prop later.

## Integrated with retrieval and confirmed working, not just filed

`knowledge/skills/bevel-segments-parity-corner-triangle.json` written to match the project's
existing rich skill schema (matched against `modifier-stack-order-subd-safe.json` as the reference
example). Tested against the actual runtime consumer, `knowledge_engine.retrieval.StructuredSkillStore`:

- A natural-language planner-style query ("need to round off a hard surface corner where several
  edges meet without leaving a triangle") ranks this skill **first** (score 6.20, threshold 4.0).
- A keyword-heavy query ranks it first at 13.13.
- An unrelated query (UV seams for a character head) does **not** surface it at all -- correct
  abstention, confirmed by also checking that the genuinely relevant UV skill was returned instead.

## Status and honest limits

`TRANSFER_VALIDATED`, not `RUNTIME_VALIDATED` -- retrieval surfaces it correctly, but it has not yet
been selected and applied by a planner during a real modeling task on an unfamiliar reference. That
real-task application is the natural next step, not another isolated lab. Also untested: a
non-orthogonal multi-edge corner (this was cube corners only, all 90 degrees) and the object-level
Bevel modifier specifically (this used the typed `bevel_selection` edit-mode op throughout).
