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

**A real remaining gap in the above**: `advance_revision()` alone only proves one
revision-advancing call happened per logged decision — not that only one Blender mutation occurred
before it. Five operations followed by one `advance_revision(rev)` would have looked identical in
the log. `blender_ops/decision_transaction.py` closes this: the only sanctioned mutation point is
`tx.perform(fn, *args, **kwargs)`, which raises if called a second time in the same transaction.
It cannot stop code from bypassing the object and calling `bpy.ops`/`bmesh.ops` directly — no
in-process Python API can fully sandbox its own caller — but it makes the sanctioned path one line
to use correctly and a visible, auditable choice to skip. `blender_ops/state_probe.py` also gained
the rich perception layer that was missing (`get_selection`, `vertex_neighborhood`,
`valence_distribution`, `modifier_state`, `active_state`) — selected vertex/edge/face IDs,
selection mode, local topology (valence, boundary state, neighbor IDs, connected edge
lengths/face areas), not just aggregate mesh-health counts.

**`runs/2026-08-07_mug-adaptive/`** exercises both for real: a genuinely unseen reference
(`reference/mug/notes.md`, no prep before that session) modeled through 20 decisions using
`DecisionTransaction` for every mutation and the new perception functions to actually pick targets
(e.g. the outermost handle vertex via `vertex_neighborhood`, not a blind heuristic). This is
deliberately not another 100-cycle count-chasing run — the point was demonstrating visible
adaptation, and it happened three times, unstaged: a boolean UNION handle attachment reproduced
the same defect class as an existing skill learned from DIFFERENCE cuts, and the fix was tested
(not assumed) to generalize across operation types — it did, and the skill's applicability was
updated with that evidence; a base-rim bevel introduced a sharper sliver (1.56°) than a
previously-accepted threshold (3.98°) and got fixed rather than blanket-accepted; and
investigating why a `bpy.ops`-based UV unwrap showed `op_delta==0` revealed
`window_manager.operators` is a capped ring buffer *also shared with the user's own concurrent GUI
clicks* — `decision_transaction.py`'s docstring was corrected on the spot to stop overclaiming that
signal's reliability. 19/20 entries accepted-or-repaired, independently verified clean; two more
honest timing-discipline flags left visible per the same no-retroactive-editing policy as the
100-cycle run.

**That mesh still had genuinely bad topology, and `runs/2026-08-07_mug-retopo/` is now the
authoritative evidence for the Mug specifically.** User feedback was blunt and correct: "topology
on the mug model is shit." Every check above (`mesh_health`, `verify_mesh.py`) only measures
*validity* — non-manifold edges, n-gons, degenerate faces — never *quality*: vertex valence/pole
distribution or face-area consistency. The `mug-adaptive` mesh passed every validity check while
carrying 83 irregular poles and a 6500:1 largest-to-smallest face-area ratio, because
`state_probe.py` had no way to even see that until this session added `valence_distribution()` to
the live diagnosis. Two real causes, found by direct inspection, not assumption: (1) the cylinder's
default `NGON` end caps have no edge flow to absorb an adjacent rim bevel cleanly, so beveling the
rim loop created a valence-3 pole at every one of the 32 cap-boundary vertices — fixed by rebuilding
with `end_fill_type='TRIFAN'`, which confines the necessary pole to each cap's flat center instead
of scattering it around the boundary; (2) the boolean-UNION handle attachment itself was the other
major pole source, replaced with clean edge-flow construction (`bmesh.ops.spin` to sweep the handle
profile, then `bpy.ops.mesh.bridge_edge_loops()` to close the far end without needing exact pivot
math — an initial hand-derived pivot placed the swept loop at radius ~1.37 instead of the intended
1.2, logged honestly as a caught mistake rather than silently patched, and bridging sidestepped the
need to get that math exact). One repair mistake surfaced along the way and is logged honestly
rather than hidden: a first attempt to clear a bridge-seam degenerate face via edge-collapse (the
technique that had worked repeatedly earlier) did not work, because the actual defect was two
vertices at identical coordinates — a doubled vertex, not a short edge — which needed
`merge_by_distance` instead.

That pass got the mesh to 0 non-manifold/n-gons/degenerate-faces but still left 8 irregular poles
at the bridge seam (down from 83) — "clean" by the validity checks but the user correctly called
it out again: "topology on the handle is bad." Direct inspection found a real, specific defect the
pole count alone didn't name: the bottom handle-hole junction had two actual triangles (faces with
non-negligible area, not slivers) plus a redundant overlapping quad, all traceable to two extra
vertices left behind by the imprecise spin/bridge repair — comparing directly against the clean,
all-quad top junction (which never went through that repair) showed exactly what "clean" should
have looked like. Mid-repair — after dissolving the six faces around those two extra vertices into
one region as step one of a planned two-step requad — the object was found to have live changes
underneath the script that no automated transaction had made: 200 vertices had dropped to 162, with
valence collapsing from 8 irregular poles to 4, then, after a mode switch, to zero. This was a live
concurrent edit: a manual Merge-by-Distance / Limited Dissolve run directly in the Blender GUI,
independently confirmed by inspecting `bmesh.from_edit_mesh` while the object was still in Edit
Mode rather than assumed. `decision_state`'s revision counter is a script-owned integer with no way
to observe GUI edits, so this divergence is invisible to `DecisionTransaction` by construction —
handled by adding a new `external_edit` evaluation type to `tools/decision_log.py` (parallel to the
existing `reverted` type added for the opposite case, a GUI undo rolling a scripted decision back)
rather than silently resyncing or overwriting it, so the log states plainly that the mesh changed
through a channel it cannot see, instead of falsely claiming a scripted decision.

Final result, independently verified against a fresh `.blend`
(`runs/2026-08-07_mug-retopo/verify_reports/Mug_20260807T153000Z.json`): valence distribution
`{4: 160, 16: 2}` — zero irregular poles anywhere in the mesh; the only non-4-valence vertices are
the two flat trifan cap centers, where a pole is harmless by construction. Face-area ratio 25:1
(versus 6500:1 in `mug-adaptive`). `runs/2026-08-07_mug-retopo/decision_log.jsonl` records the full
honest sequence — including the intermediate n-gon, the failed requad attempt, and the external
edit — rather than only the clean endpoint.

## Perception upgrade: persistent element IDs + per-decision deltas

Prompted by an architecture proposal for a much larger custom-add-on protocol (push events, delta
state, semantic regions, ownership locking, and more). The full protocol would mean writing a new
Blender add-on with its own socket server — a multi-session rebuild of what blender-mcp already
provides, not an incremental step. Rather than attempt all of it at once (the same over-scoping
risk this project has caught before — see the batching and mug-topology corrections above), the
two pieces with real, provable value on top of the existing MCP bridge were built first: stable
element IDs and per-decision deltas.

`blender_ops/persistent_ids.py` assigns custom int attributes (`agent_vertex_id`, `agent_edge_id`,
`agent_face_id`, backed by a per-object `agent_id_counter` custom property) so an element can be
referred back to by a stable ID even after unrelated topology changes elsewhere in the mesh
renumber Blender's own indices. **A real bug surfaced immediately on first use, not left for
later**: `bmesh.ops.bevel` (and presumably other ops that interpolate custom data for continuity)
silently copies an existing nonzero ID onto newly created geometry instead of leaving it at the 0
sentinel — one test bevel left vertex ID 7 shared by three different vertices. A "0 means
unassigned" check alone is not sufficient; `ensure_persistent_ids()` now also detects and repairs
same-pass duplicates, verified by deliberately re-triggering the bug and confirming zero duplicate
IDs remained afterward. `blender_ops/bmesh_io.py` factors out mode-aware bmesh read/write
(`bmesh.from_edit_mesh` vs `bmesh.new()+from_mesh()`), fixing the same stale-read risk that broke a
mid-session repair during the mug-handle fix above.

`DecisionTransaction` now backfills and diffs persistent IDs automatically around every
transaction's target object, adding an `id_delta` (added/removed IDs per vertex/edge/face) to
`verify()`'s return value — the real, provable delta scoped to exactly one decision, which is the
actual unit of change in this project, rather than an arbitrary revision-range cache.
`state_probe.get_full_state()` consolidates revision, mesh health, valence distribution, selection,
and ID coverage into one call. All of this was tested live against the Mug, including the
duplicate-ID bug and its fix, then the test mutations were discarded by reloading the last verified
`.blend` rather than left on the actual deliverable object.

## Typed modeler protocol: custom add-on + MCP server (build in progress)

Told to proceed with the full architecture proposal ("even though it's a much bigger commitment, if
it makes it better, do it"). This is genuinely large — a new Blender add-on with its own socket
server plus a new MCP server is a real rebuild, not an incremental step — so it's being built and
verified incrementally rather than claimed complete in one pass, the same discipline used
everywhere else in this project.

**Built and live-verified so far:**

- `blender_ops/modeler_server.py` — a second, typed socket server inside Blender (port 9878,
  alongside blender-mcp's own 9876), built directly on the already-verified `state_probe`/
  `persistent_ids`/`decision_transaction`/`mesh_ops` modules rather than duplicating logic. Uses
  length-prefixed JSON framing (4-byte big-endian length + payload), more robust than blender-mcp's
  own accumulate-and-hope-`json.loads`-succeeds approach, since this protocol was designed fresh.
  Commands: `get_capabilities`, `get_full_state`, `get_selection`, `poll_events`, and the full
  `begin_decision` → `perform_decision` → `verify_decision` → `commit_decision` lifecycle, wrapping
  five existing `mesh_ops` operations (`bevel_edges`, `merge_by_distance`, `add_ring_detail`,
  `recalc_normals`, `triangulate_ngons`). This is a small slice of the proposed command surface
  (extrude/move/scale/loop_cut are not wired up yet) — proven end-to-end for a few commands rather
  than stubbed shallowly for many.
- `tools/modeler_mcp_server.py` — wraps that socket protocol as named MCP tools. Verified with a
  **genuine MCP-protocol client** (the official `mcp` SDK's stdio client, spawning the server as a
  real subprocess and driving it through actual JSON-RPC — not just testing the raw socket
  underneath it): tool listing and `get_capabilities`/`get_full_state` calls all passed, reaching
  live into the running Blender session and back. Registered in `.mcp.json` as a second server,
  `modeler`.

**Two real bugs found and fixed during this build, not left for later:**

1. An "ownership heuristic" was attempted — tagging each `mesh_changed` event as `agent` or
   `external` via a flag set around command dispatch, on the assumption `depsgraph_update_post`
   fires within roughly one `bpy.app.timers` tick of the write that caused it. Direct instrumented
   testing disproved this: `depsgraph_update_post` did not fire even 3 seconds after a synchronous,
   direct mutation — it only fired once *later, unrelated* Blender activity (e.g. the next
   `execute_blender_code` call) forced a redraw/dependency-graph evaluation. One observed gap
   exceeded 30 seconds. Every event was misattributed "external," including the agent's own
   changes. Rather than ship a plausible-looking signal that's actually always wrong, the field was
   removed entirely. `poll_events` still reports real change events with real timestamps and
   sequence numbers — useful for eventual-consistency polling — but genuine ownership/locking
   (item 9 of the original proposal) needs a different mechanism (e.g. comparing persistent-ID sets
   against last-known transaction state, the same technique that already caught the real human/agent
   collision during the mug-handle fix) and is not built yet.
2. Hot-reloading `modeler_server.py` in-session (`importlib.reload` + stop/start) left zombie accept
   threads bound to the port — Windows' `SO_REUSEADDR` allowed a second `bind()` to succeed while
   the first socket was still listening, so an old, buggy instance kept intermittently answering
   connections even after the "fixed" code was reloaded and started. Caught via `threading.enumerate()`
   showing multiple live `_accept_loop` threads. Worked around by moving to a fresh port for this
   session and documented directly in the module so future hot-reloading captures and stops the
   existing instance first; a real Blender restart doesn't have this problem.

**Not yet built, deliberately:** semantic geometry regions, viewport/camera state exposure,
Blender-native visual passes (silhouette/wireframe/normals — this one reverses the project's
founding "no-screenshot" design tenet from the top of this README and should get an explicit
confirmation before being built, not be waved through inside a larger bundle), real
ownership/ locking (see the finding above), heartbeat/reconnect, and restricting
`execute_blender_code` to a fallback/debug role (a policy change once the typed surface covers
enough real operations to be the primary path).

**Operational note, not a limitation of the code:** MCP servers load from `.mcp.json` at Claude
Code session start. A session already running when `modeler` was added to `.mcp.json` cannot call
its tools until that session restarts — this was verified independently via a real MCP client
subprocess specifically because the agent driving this build could not simply call its own new
tools to check.

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
