# interactive-agent-blender

A live, no-screenshot connection between an LLM agent and Blender: the agent reads and mutates
actual scene state over a local socket instead of interpreting rendered images.

## Current state

- `addon.py` — the [blender-mcp](https://github.com/ahujasid/blender-mcp) Blender addon (installed
  and enabled in the local Blender 5.2 user preferences, auto-starts its TCP server on
  `localhost:9876` whenever Blender opens).
- `.mcp.json` — registers the `blender` MCP server (`uvx blender-mcp`) so an MCP-aware agent can
  connect to that running Blender session directly (`get_scene_info`, `execute_blender_code`,
  `get_object_info`, asset-generation tools, etc).

## Target benchmark

Seven proofs the agent needs to demonstrate against a live Blender session. This is the spine of
the project — do not add subsystems beyond what's needed to pass these honestly.

1. One Blender process survives 100 verified interactive actions
2. Agent creates a simple mesh interactively
3. Agent models against a reference
4. Agent detects and repairs its own mistake
5. Agent retrieves a previously learned topology skill
6. Agent completes an unseen hard-surface prop
7. Independent verification says the result is clean

**Authoritative evidence: `runs/2026-08-07_proof1-redo/`.** An earlier pass
(`runs/2026-08-06_seven-proofs/`) hit the Proof-1 count by looping `mesh_ops.add_ring_detail`
over a formula-derived list of z-values — mechanically real (each step individually verified,
zero non-manifold edges/n-gons throughout) but not 100 individually-decided actions; it was one
decision (the formula) applied 70 times. The redo rebuilds both props from clean primitives and
replaces every formula-driven step with a hand-authored one: explicit literal
`(z, offset, rationale)` tuples chosen per-instance, inspection-driven face/edge selections
(closest-face-to-a-target-point, not sweep-and-stamp), and a mix of operation types (ring
details, insets, boolean cuts, bevels) rather than one op repeated. The old session's log is kept
for transparency, not deleted, but `2026-08-07_proof1-redo` is what actually satisfies Proof 1.

**A further correction, now the actually-authoritative evidence: `runs/2026-08-07_decision-cycles/`.**
Even `2026-08-07_proof1-redo`'s hand-authored literals were still executed inside batched
`execute_blender_code` calls — several actions sharing the same sub-second timestamp gave it away.
Batched-but-well-reasoned isn't the same as genuinely separate decision cycles.
`blender_ops/decision_state.py` (a revision counter the Blender scene itself owns, not a local
Python variable) and `tools/decision_log.py` (validates strict revision chaining plus a minimum
gap between consecutive decision timestamps, and can only be advanced one mutation at a time via
`advance_revision()`) enforce this mechanically now, not by discipline alone.

`2026-08-07_decision-cycles` is 111 genuinely separate MCP round-trips. **Status: PARTIAL, not
PASS** — `verify-count --min 100` reports `accepted_or_repaired_count: 100` (the count threshold
is met) and a single PID (6180) throughout, but `pass: false`, because the validator's actual rule
is `len(accepted) >= min AND not problems`, and three historical timestamp pairs still fail the
anti-batching timing check (see below). Reaching the count and passing strict verification are two
different claims; only the second is currently false. A future clean run is needed to actually
flip `pass` to `true`, without altering these old timestamps. It's an honest complete record, not
a highlight reel: 15 real repairs, 3
mistakes caught mid-session (including two the agent introduced itself, e.g. a bevel that left a
0.52° sliver), 4 rejected attempts where a fix didn't work and was tried again differently (a
misleading Blender operator report caught by verifying independently, `bmesh.ops.holes_fill`
silently failing twice before falling back to the interactive-equivalent operator), and 2 live
collisions with a human editing the same Blender session concurrently — one where undo reverted a
logged fix without any corresponding entry, handled with a new `reverted` evaluation type rather
than silently resyncing. Three historical entries are flagged by the timestamp validator as
looking batched (`seq 19-20`, `40-41`, `74-75`) — each was independently confirmed to be genuinely
separate decisions, logged together afterward by a lapse in my own append discipline. Left visible
and explained rather than retroactively edited, since fixing the timestamps to make the validator
pass would be exactly the kind of gaming this mechanism exists to catch.

Along the way this run also found and fixed three real bugs nobody had noticed (materials
assigned to an empty slot while the real one sat unused; `diffuse_color` never reaching the
actual render-affecting BSDF input; a newly-added camera never set as `scene.camera`), each
encoded as a skill in `knowledge/skills/`, and added a `normals_consistent_ok` check to
`tools/verify_mesh.py` from a signed-volume technique discovered mid-session.

## Shape-authoring boundary

See the module docstring in `blender_ops/mesh_ops.py`. Short version: mechanical/repair/detail
helpers are fine to call directly and repeatedly, but never in a loop whose parameters are
generated by a formula — that's procedural asset generation wearing this module's clothes, the
exact failure mode an earlier, since-deleted version of this project fell into. Every call's
location and parameters must come from the agent inspecting current state and deciding that
specific instance.

## Roadmap: autonomous research & expertise acquisition (not started)

`docs/RESEARCH_ROADMAP.md` — a mandatory future subsystem, gated behind the closed-loop runtime
milestone above being proven reliable. Not optional, not to be dropped from scope, not to be
built early. Read it before starting any research/learning-related work.
