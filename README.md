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
- `tools/verify_mesh.py` — independently verifies saved base geometry by default; pass
  `--evaluated` to verify the dependency-graph result after modifiers.

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

**Confirmed after the actual restart**: `mcp__modeler__get_capabilities` and `get_full_state`
called successfully, live, for the first time as genuine Claude Code tool calls (not a test
script) — Blender had also been closed in the meantime, so this additionally exercised launching
Blender fresh, reloading `modeler_server.py` into the new process, and reconnecting, before the
first real tool call landed correctly against the reloaded `Mug.blend`.

## Master directive: mode-correct reads + persistent IDs in selection

`docs/MASTER_DIRECTIVE.md` is the durable operating contract for the project. It defines the
evidence hierarchy, closed-loop modeling behavior, state and recovery requirements, quality
model, research discipline, and evaluation rules. Commit-bound status and implementation queues
remain in run evidence, foundation reports, and `docs/RESEARCH_ROADMAP.md`; current code and
reproducible evidence take precedence over stale prose.

Two previously prioritized items were completed and live-verified: **item 2** (migrate live
topology reads to mode-correct APIs) and **item 3** (return persistent IDs alongside indices in
selection/state). `blender_ops/state_probe.py`'s mesh-reading functions (`probe_object`,
`mesh_health`, `valence_distribution`, `vertex_neighborhood`, `get_selection`) and
`blender_ops/mesh_ops.py`'s internal read/write helpers all now route through `bmesh_io` instead of
the old `bmesh.new()+from_mesh()` pattern, which — as already found live during the mug-handle fix
— silently reads stale data when the object is in Edit Mode. The then-current directive required
an "Edit Mode truth" proof: entered Edit Mode on a scratch object, extruded a face via `bmesh.ops` *without
exiting Edit Mode*, then queried `state_probe.mesh_health`/`probe_object` and confirmed they
reported the exact live edit-bmesh counts (12/20/11 verts/edges/faces), matching an independent
ground-truth read, not the stale pre-extrude counts. `get_selection` now returns
`{"index": ..., "agent_id": ...}` pairs instead of bare indices for each selected vertex/edge/face,
tested by assigning persistent IDs to a scratch object and confirming every selected element came
back with its real `agent_id` rather than `None`. Full regression (raw socket protocol test + real
MCP client test) re-run clean afterward against the live Mug, unaffected by the refactor.

**Two more items from the same list, also live-verified:**

- **Item 6 (Blender-originated external-change detection), done via a different mechanism than
  first attempted.** The depsgraph-timing "ownership heuristic" tried earlier this session was
  disproved by direct testing — event latency isn't predictable enough to attribute origin. This
  is a genuinely different, non-timing-dependent mechanism: `modeler_server.py` snapshots an
  object's persistent-ID set after every `commit_decision`, and `begin_decision` compares the
  current ID set against that snapshot *before* opening a transaction. Any difference — added or
  removed IDs the server didn't cause itself — means the mesh changed through some other path,
  almost certainly a manual GUI edit, and `begin_decision` refuses to start with a clear diff in
  the error message, exactly matching the directive's "external_edit_detected → invalidate → stop
  → re-observe → resume" flow. Verified live: committed a baseline decision on a scratch object,
  then mutated it directly via `bpy.ops.mesh.subdivide` in Edit Mode *outside* the transaction
  system (simulating a human GUI edit), then called `begin_decision` again — it was correctly
  rejected, reporting the exact 30 added vertex/edge IDs the subdivide created. A retry immediately
  succeeded, since the rejection itself captures the new baseline. A read-only `check_external_edit`
  command was added too, for polling without opening a transaction.
- **Items 12-13 (command idempotency).** `perform_decision` now accepts an optional `command_id`;
  a retried call with the same id returns the original stored result instead of re-running the
  mutation. Verified live: called the same `command_id` twice against `add_ring_detail` and
  confirmed the vertex count only grew once, not twice.

## Item 13, continued: extrude/move/scale — six real bugs found chasing one operation

Added `extrude_selection`, `move_selection`, `scale_selection`, and `select_by_ids` to
`mesh_ops.py`/the typed operation registry — the first genuine artistic primitives beyond
mechanical/repair helpers, from the directive's initial typed vocabulary (section 12). Getting
`extrude_selection` actually correct took six rounds of live testing against a bare cube, each
one a real defect, not a false alarm:

1. **Wrong extrude direction.** Read `face.normal` for the push direction *after* calling
   `bmesh.ops.extrude_face_region`, but that operator reuses the original face object as the
   interior "back wall" of the extrusion and flips its winding — the normal read afterward was
   already inverted, pushing the new cap into the solid instead of out of it. Fixed by capturing
   the normal before the operation runs.
2. **Non-manifold result even with the right direction.** `extrude_face_region` does not
   delete/consume the original selected face — confirmed directly (it stayed valid and was
   absent from the operator's own "new geometry" return). Left in place, its boundary edges ended
   up shared by 3 faces instead of 2. Fixed by explicitly deleting the original face after
   extruding.
3. **New geometry left unselected.** After a correct extrude, the *old* boundary loop stayed
   selected (untouched by the operation) while the new cap was not — so a follow-up
   `move_selection`/`scale_selection` silently acted on stale geometry instead of what was just
   created. Fixed to explicitly select new geometry and deselect everything else, matching how
   Extrude behaves everywhere else in Blender.
4. **Persistent-ID theft.** The same custom-data interpolation behavior found earlier with bevel:
   the new cap face inherited the *deleted* original face's `agent_face_id` instead of getting a
   fresh one, and because the original was gone by the time `ensure_persistent_ids` next ran,
   there was never a simultaneous duplicate for the duplicate-detector to catch — a real blind
   spot in that safety net. Fixed with a new `persistent_ids.clear_ids_in_open_bmesh()`, called by
   the operation itself (which knows exactly what's genuinely new) right after creating geometry.
5. **A genuine bmesh gotcha, confirmed directly**: creating a *new* custom-data layer on a bmesh
   mid-session invalidates every previously-held Python element reference on that bmesh, not just
   ones related to the new layer — reproduced in isolation (capture a face reference, create an
   unrelated layer, the reference's `.is_valid` immediately goes `False`). Fixed by guaranteeing
   the three persistent-ID layers are created once, immediately after opening any bmesh in
   `mesh_ops._bm_from_object`, before any caller captures element references that need to survive
   the operation.
6. **A bug in the very code written to fix #4 and #5.** `clear_ids_in_open_bmesh` determined which
   domain (verts/edges/faces) it was processing via `seq is bm.verts` identity comparison — but
   `bm.verts`/`bm.edges`/`bm.faces` are not stable singletons, so the comparison silently failed
   for every domain, always falling through to "faces," which then created a spuriously-named new
   layer on the *verts* domain — triggering exactly the layer-creation invalidation from #5. Fixed
   by using explicit string labels instead of identity comparison.

Full protocol regression (idempotency, external-edit detection, all prior commands) re-run clean
against the live Mug afterward, unaffected throughout.

## Closing out the master directive's engineering priority list

Told to keep going without stopping. Worked through nearly all items in the then-current
directive's engineering priority list,
each live-tested, not just written:

- **Item 5 (separate identifiers), completed**: `event_id` (distinct from `seq`, which is only
  queue ordering) added to every pushed event; `session_id` added via the handshake below.
- **Item 8 (event coalescing)**: `_push_event` now bumps a `repeat_count` on the most recent queue
  entry instead of appending a new one for a repeated `(event_type, object)` pair. Verified
  directly with synthetic consecutive pushes (3 → 1 entry, `repeat_count=3`). Noted honestly: real
  depsgraph bursts observed in this environment tend to *alternate* between the target object and
  a companion object rather than repeat one consecutively, so live noise reduction is lower than
  the mechanism's ceiling — the mechanism itself is correct, that's just the real pattern observed.
- **Item 15 (session handshake) + item 14 (heartbeat)**: `session_id` (fresh per server start, not
  persisted — represents this running instance) and `started_at` in `get_capabilities`; a new
  `heartbeat` command reports session_id/pid/revision/uptime/pending-decision count.
- **Item 16 (reconnect without Blender restart)**: verified, not assumed. Began a decision on one
  TCP connection, closed it (simulating a client crash), opened a fresh connection, confirmed the
  same `session_id` and `pending_decisions==1` via `heartbeat`, then completed that same
  `decision_id`'s perform/verify/commit on the new connection — server-side state is independent of
  any one TCP connection by construction.
- **Item 17 (explicit ownership)**: `AGENT_CONTROL` / `USER_CONTROL` / `SHARED_OBSERVATION`, default
  `AGENT_CONTROL`. Unlike the removed depsgraph-timing heuristic, this has real teeth —
  `begin_decision` refuses to even attempt a mutation while control_mode isn't `AGENT_CONTROL`,
  rather than trying to detect a collision after the fact. Verified live: set `USER_CONTROL`,
  confirmed refusal with a clear message; switched back, confirmed a normal cycle succeeded.
- **Item 18 (semantic regions)**: `blender_ops/semantic_regions.py` — named, persistent-ID-keyed
  groups (`create/get/list/update/delete/select_region`), stored as JSON on an object custom
  property. `validate_region` re-checks every stored ID against the *current* mesh rather than
  assuming persistence, per the directive's "must invalidate honestly." Verified live: full
  lifecycle, then a genuinely destructive mutation (merge-by-distance at a large tolerance,
  collapsing 8 vertices to 1) correctly flagged the region invalid with exactly the 3 destroyed
  IDs listed as missing.
- **Item 19 (richer local topology graphs)**: `state_probe.inspect_region(name, center_ids,
  rings=2)` — a BFS-grown local graph keyed by agent_id, with pole locations, edge-length/face-area
  ratios, local tri/quad/ngon composition, and a real (not assumed) connected-component count.
  Verified read-only against the live Mug, targeting a known pole (one of the two flat trifan cap
  centers) — correctly identified it as the region's sole pole with 16 triangular + 16 quad faces
  around it.
- **Item 20 (viewport/camera state)**: `state_probe.viewport_state()` — projection type, view
  distance/location, shading mode, x-ray, local view, active camera transform, and a best-effort
  standard-orientation label (FRONT/BACK/TOP/BOTTOM/LEFT/RIGHT). First attempt at the reference
  quaternions was typed from memory and failed live testing (wrong values, and missing that a
  quaternion and its negation represent the same rotation) — fixed by reading the real values
  directly from `bpy.ops.view3d.view_axis()` for this Blender version. Verified against all six
  standard views (all correctly detected) plus a free-orbited view (correctly returns no label).
- **Item 13, remainder of the initial typed vocabulary**: `inset_selection`,
  `add_modifier`/`set_modifier_parameter` (new `blender_ops/object_ops.py`, object-level, not
  bmesh), `undo`/`redo`, `save_checkpoint`/`restore_checkpoint`/`save_file`.
  - `inset_region` turned out to behave *better* than `extrude_face_region`: the original face
    resizes in place and correctly keeps its own persistent ID and boundary verts (confirmed
    directly by tagging IDs before insetting and reading them after) — no delete-the-original step
    needed, unlike extrude. The genuinely new geometry is the ring of connecting faces plus a
    duplicate of the old outer boundary; those get their IDs cleared the same way extrude's new
    geometry does. Selection is correctly left on the shrunk original face (matching Blender's own
    Inset tool), not the ring, so a follow-up extrude/move can chain off it.
  - **A real, important limitation found live, not glossed over**: `undo`/`redo` do NOT reliably
    undo "the last decision." `DecisionTransaction` mutations write directly via
    `bm.to_mesh()+obj.data.update()`, which do not push an entry onto Blender's own undo stack —
    confirmed directly: one mutation followed by exactly one `undo()` call deleted an entire
    scratch object outright, jumping straight past the mutation to the last real
    `bpy.ops`-recorded action (its creation). Any number of committed decisions can sit between
    "now" and whatever `undo()` actually reverts to. Both functions' docstrings and MCP tool
    descriptions say this explicitly rather than implying a guarantee the code doesn't keep.
  - `save_checkpoint` verified live (wrote a real, loadable `.blend` file, confirmed on disk, then
    removed as a test artifact).

One real operational hiccup during this round, also worth recording honestly: mid-testing, the
socket connection dropped (`WinError 10054`) and the `ModelerServer` instance came back as `None`
on the next check — the accept thread apparently died silently. Blender's own MCP connection
(`execute_blender_code`) stayed healthy throughout, confirming Blender itself never crashed; only
the add-on's own server thread did. Recovered by reloading and restarting `modeler_server.py`
(the same procedure already documented above for hot-reload iteration) — no data was lost, since
`DecisionTransaction` commits are synchronous and the failure happened between test steps, not
mid-transaction. This is a real gap heartbeat/reconnect *detects* (a client would see the
connection refused) but does not yet *recover from automatically* — there's no supervisor
restarting the accept thread if it dies. Worth hardening if this becomes a recurring problem;
not attempted here since it was a single occurrence.

Not done, and not attempted without further instruction: **Blender-native visual passes** (item
21, and item 22 which depends on it) — this specifically reverses the project's founding
"no-screenshot" design tenet from the top of this README and needs an explicit confirmation, not a
default extrapolated from "keep going." Also not started: logging arbitrary `execute_blender_code`
usage as a fallback-path metric (item 14's other half) — that tool lives in a separate MCP server
(`blender-mcp`) this project doesn't control internally, so it isn't something addressable by
editing this repo's code. The research/curriculum system remained gated behind reliable
closed-loop engineering under that directive's sequencing rule — not started, as before.

## Item 23: first real modeling session through the typed protocol, not raw code

`runs/2026-08-07_speaker-typed-protocol/` — a genuinely unseen reference
(`reference/speaker_enclosure/notes.md`, no prep before this session) modeled almost entirely
through the typed `modeler` protocol (`begin_decision`/`perform_decision`/`verify_decision`/
`commit_decision`, `select_by_ids`, `inspect_region`) instead of raw `execute_blender_code` —
the first real proof this session's protocol work holds up for actual modeling, not just
infrastructure tests on bare cubes. Deliberately a different topology family than every prior
prop (Bottle/Flashlight/Mug are all revolved/cylindrical forms) — a boxy, rectilinear body with a
circular-in-intent driver cutout, chosen specifically to stress a different part of the tool
surface (inset/extrude on flat faces, not just cylinder rings).

**A real operational limitation hit immediately, documented rather than worked around silently**:
this Claude Code session's `modeler` MCP tool list was fixed to whatever existed when the tools
were first loaded — commands added afterward (`create_primitive`, `select_by_ids`, `inspect_region`,
etc.) aren't callable natively without restarting, because the MCP subprocess is long-lived and
doesn't re-read the file per call (a finer-grained instance of the same constraint documented
earlier for a full session restart). Rather than ask for another restart, the session was driven
through a small reusable raw-socket script speaking the identical wire protocol for the newer
commands, and native `mcp__modeler__*` tool calls for the ones already loaded
(`begin_decision`/`perform_decision`/`verify_decision`/`commit_decision`/`get_full_state`/
`get_selection`) — the underlying `DecisionTransaction`/`mesh_ops` guarantees are identical either
way; only the calling mechanism differs. No raw `execute_blender_code` was used for any modeling
mutation.

8 decisions, each individually verified, three genuinely adaptive corrections along the way:

1. **Scale to body proportions** — informed by actually inspecting the fresh primitive's real
   1×1×1 size via `inspect_region` rather than assuming Blender's default.
2. **Bevel the 4 vertical corner edges** for modest softening — introduced 2 n-gons (the flat
   top/bottom quad caps each became 8-sided octagons once all 4 corners got clipped), a real,
   expected geometric consequence, not silently accepted.
3. **`triangulate_ngons`** to repair it, keeping n-gons at zero throughout, consistent with every
   prior prop in this project.
4. **Inset the front face** for the driver footprint — surfaced a genuine tool limitation:
   `inset_region` always shrinks uniformly around the face's own centroid, with no way to inset
   off-center directly. Adapted by insetting centered first and repositioning afterward, rather
   than needing a new operation.
5. **Unexpected result, corrected**: the inset produced a 1.6×2.44 rectangle, not the intended
   roughly-square ~1.6×1.6 footprint for a circular driver silhouette — visibly different from
   what was planned, addressed with a follow-up Z-axis-only scale rather than ignored.
6. **Extrude the footprint inward** (negative offset, since the face's own outward normal points
   away from the body) to create the actual recess cavity.
7. **Move the whole recess (opening ring + cavity floor together)** upward for the "upper-middle,
   not centered" placement the reference called for — moving both groups together, not just the
   floor, to keep the recess walls straight instead of tapering.
8. **Bevel the recess opening** for a finished lip, rather than a raw sharp edge reading as a flat
   decal.

**A real, live verification worth recording, not just a decision**: `bevel_edges` was found to
never call the `clear_ids_in_open_bmesh` fix built earlier this session for extrude/inset's
ID-theft bug (see above). Rather than assume this was fine or assume it was broken, checked
directly for duplicate/unassigned persistent IDs across the whole object after two real bevels —
found none. The reason: `clear_ids_in_open_bmesh` exists specifically for operations that delete/
orphan the original ID-holder before `DecisionTransaction.verify()`'s standard `ensure_persistent_ids`
duplicate check runs (extrude's pattern); bevel doesn't orphan anything, so the existing general
duplicate-detection safety net already catches its interpolation copies. No code change was needed
— but this was verified, not assumed, which is the point.

**A quality judgment call, checked rather than reflexively "fixed"**: `inspect_region` swept the
whole finished mesh and found 4 valence-3 poles at the recess cavity floor's corners. Rather than
treat every non-4-valence vertex as a defect (the master directive explicitly warns against this,
section 17), the pole locations were inspected directly — they're the four corners of a simple
sharp-cornered rectangular recess, geometrically identical to how any box's own outer corners are
also valence-3. This is normal, expected orthogonal-box topology, not the kind of irregular pole
scatter across a surface that's supposed to be smooth that made the Mug's original topology bad.
Left as-is, judgment recorded rather than blindly bevel-everything.

That was 8 decisions — real, but short of the directive's 20-40 target for item 23. Told to extend
it rather than start a new prop, the same session continued for 12 more (decisions 9-20, revision
148→160), reaching the floor of the range. The back panel — left flat in the 8-decision cut per the
reference's "optional" note — got real treatment after all, since with more decisions genuinely
warranted, it stopped being the right place to economize:

9. **Inset the driver-cavity floor** for a dust-cap footprint, then **10. extrude it outward 0.04**
   to form a small dome — verified its position landed 0.11 units clear of the recess opening, not
   clipping through.
11. **Inset the back panel** (found via a `rings=6` region search that came up empty, then `rings=20`
    that found it — the BFS radius needed to span the whole 68-face mesh from a driver-region
    starting point was larger than first guessed) for a bordered detail area, then **12. extruded it
    inward** — reasoned the direction fresh from the back face's own +Y normal rather than assuming
    it mirrored the front's -Y convention, then confirmed the result at Y=0.97 directly.
13. **Bevel the back recess opening** for visual consistency with the front.
14. **Inset the base** for a foot ring — the bottom face turned out to be split into 2 triangles
    from an earlier corner bevel, not one quad; tested whether `inset_selection` handles a merged
    2-triangle region correctly (it does) rather than assuming.
15. **Extrude the foot plinth outward** — one edge got *removed*, not just added (the old
    triangle-diagonal got consumed as the region became a clean quad extrusion); inspected and
    judged sensible rather than assumed a bug.
16. **Bevel the plinth boundary** — surfaced a real, minor compounding effect: two existing
    valence-7 poles (from the original corner bevels) became valence-8, since the plinth's boundary
    intersects the same physical bottom corners as the earlier corner treatment. Investigated with a
    direct diagnostic query (pole positions, whole-mesh min/max face area — 0.011 to 6.34, nothing
    near-degenerate) rather than assumed either "fine" or "broken," and judged it an acceptable
    trade-off of stacking two detail treatments at one corner, not a defect.
17. **Inset a cable-port area** on the back recess floor — `select_by_ids(97)` initially picked a
    small side-wall quad instead of the actual floor; re-diagnosed via `get_selection` and found the
    right face (agent_id 272, area 5.97) before proceeding, rather than extruding the wrong thing.
18. **Extrude the port inward** for real cutout depth, confirmed at Y=0.92, still well clear of the
    front cavity.
19. **Bevel the port opening.**
20. **Bevel the driver-cavity floor's own boundary** — the one remaining sharp interior edge loop on
    the whole model by this point. **A real identity discontinuity, recorded honestly rather than
    hidden**: this bevel (`segments=1`) *removed* the four original floor-corner persistent IDs
    outright rather than keeping them alongside new ones (unlike the `segments=2` bevels used
    elsewhere, which preserve the original corner). Confirmed no orphaned/duplicate IDs resulted —
    final `persistent_id_coverage` (108/226/120) exactly matches final element counts.

**A genuine process-identity change, also not hidden**: `heartbeat` reported PID 15816 partway
through, differing from the 24112 recorded for decisions 1-8. The mesh state itself showed no
discontinuity (revision and vertex/edge/face counts continued exactly where decision 8 left off, both
persisted as real scene/mesh data), so no committed work was lost — but Blender's OS process
genuinely differs between the two halves of this session, most plausibly around the
earlier-documented `modeler_server` crash/restart. Logged plainly in decision 9's entry rather than
claimed as unbroken continuity.

**Logging discipline gap, also left visible rather than fixed retroactively**, matching this
project's established policy: decisions 9-20 were modeled live, one at a time, with real
verification at each step (the revision numbers, `id_delta`s, and `mesh_health` results are all
genuine per-decision data) — but the JSONL *logging* of those 12 entries happened as a batch write
at the end of the session rather than immediately after each decision. `decision_log.py
verify-count` correctly flags this: several timestamp pairs read as batched, and the PID split means
`pass: false`. Status is **PARTIAL, not PASS** — the same honest distinction this project has drawn
before between "the count is real" and "the strict verifier is satisfied."

Final result, independently verified against a fresh `.blend`
(`runs/2026-08-07_speaker-typed-protocol/verify_reports/SpeakerEnclosure_20260807T184842Z.json`):
108 vertices, 226 edges, 120 faces, 0 non-manifold edges, 0 n-gons, 0 degenerate faces, consistent
normals, `persistent_id_coverage` exactly matching element counts (no duplicate IDs anywhere in the
finished model). Two semantic regions (`driver_cavity`, `cable_port`) were also created on the
finished object via `create_region`, naming the model's real anatomy for future reference rather
than only testing the mechanism on throwaway cubes.

## Shape-authoring boundary

See the module docstring in `blender_ops/mesh_ops.py`. Short version: mechanical/repair/detail
helpers are fine to call directly and repeatedly, but never in a loop whose parameters are
generated by a formula — that's procedural asset generation wearing this module's clothes, the
exact failure mode an earlier, since-deleted version of this project fell into. Every call's
location and parameters must come from the agent inspecting current state and deciding that
specific instance.

## Roadmap: autonomous research & expertise acquisition (foundation active)

`docs/RESEARCH_ROADMAP.md` — the closed-loop runtime has substantial evidence and controlled
documentation/experiment work is active. Approved-root document/video ingestion, structured
retrieval, usage telemetry, uncertainty, rebuild decisions, and local machine transcription are
implemented and tested; external curriculum breadth and cross-asset promotion remain incomplete. Read it before starting
research/learning-related work.

`docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md` is the current directive-by-directive audit. It separates
implemented local capabilities from evidence that cannot be fabricated: long-horizon independent
retention, advanced lesson coverage, broad uncontaminated transfer, and experienced human review.

The typed modeler protocol is now version 0.2. Its decision registry includes the original
extrude/inset/move/scale/subdivide and modifier operations plus selection-driven rotate, bevel,
delete, dissolve, merge, fill, bridge, spin, loop cut, Bisect clear/cap, symmetrize, split, separate,
and smooth/flat shading. Bevel exposes explicit width type, profile, and overlap-clamp policy.
See `runs/2026-08-10_expanded-typed-ops/` for transaction, identity, rollback, and failure evidence.

Rejected transactions also have a multi-channel stress test in
`runs/2026-08-10_transaction-rollback/`: Object Mode rejection restores mesh/UV/material data,
modifiers, semantic and custom metadata, selection, active object, transform, and revision without
using Blender's global undo stack.

## Curriculum step D: subdivision-surface milestone (SoapDish)

`runs/2026-08-07_soap-dish-subsurf/` — the first prop in this project where the control cage is
not the final surface (a Subdivision Surface modifier is), following the master directive's
curriculum order (section 47: A. fundamentals → B. topology → C. simple hard-surface forms,
covered by four flat-panel-bevel props → D. subdivision-surface modeling, this one). Reference:
`reference/soap_dish/notes.md`, genuinely unseen beforehand — a rounded rectangular dish with a
shallow concave basin that has to read as smooth and continuous once subdivided, not faceted or
pinched at the basin/rim transition.

**A real capability gap closed first**: judging a subdivision-surface result by inspecting the
control cage (what every prior `state_probe` read) is close to meaningless — the cage isn't the
final surface. Built `blender_ops/evaluated_probe.py`, which reads the mesh through
`bpy.context.evaluated_depsgraph_get()` + `obj.evaluated_get(depsgraph).to_mesh()` — the actual
post-modifier result — and added face-area-outlier and max-adjacent-face-angle heuristics aimed
specifically at detecting pinching (a plain global min/max face-area check is a weak signal on a
subdivided surface, where small faces are normal everywhere near any curvature). Verified first
against a scratch cube + Subsurf level 2 (98v/192e/96f, exactly matching 6×4²) before trusting it
on real work.

**A real, silent bug found chasing that capability**: the Subsurf modifier's effect wasn't
showing up in `evaluated_probe`'s output at all. Root-caused directly (not assumed) —
`obj.modifiers.new()` does not default `show_viewport`/`show_render` to `True` via Blender's
Python API, so `object_ops.add_modifier` had been silently creating modifiers invisible to both
the viewport and the evaluated-mesh dependency graph the whole time. Fixed (`bd4648b`), with an
honest note that this likely also affected the SpeakerEnclosure's earlier Bevel-modifier decision,
which predates `evaluated_probe.py` and was never checked against the evaluated mesh — left as a
documented limitation on that earlier verification claim, not retroactively edited.

**A real topology mistake, a fast fix, and a better one from a live human correction**:
subdividing the basin's interior without matching the surrounding rim faces' resolution produced
4 seven-sided n-gons on the rim — a real, expected consequence of a resolution mismatch at a
subdivision boundary. Fixed fast with `triangulate_ngons`, reasoned as low-risk since the rim was
still flat at the time. Mid-session, `begin_decision` then failed with a genuine (not staged)
external-edit detection: vertex count had doubled, n-gons had reappeared, several elements showed
`agent_id: null`, mode was `EDIT`. Stopped immediately, reported the exact symptoms, and asked the
user directly whether they were editing live — confirmed: "yes im fixing the topology to be all
quads." Set `control_mode` to `USER_CONTROL` (the mechanism's first real deployment, built earlier
this session for exactly this scenario) and stood down without fighting the user's edit or
overwriting it.

The user's manual fix — resolution-matching the rim to the basin with proper all-quad topology,
rather than accepting the triangulated patch — is a real, tested correction, not just a style
preference. `get_evaluated_state` on the result: 258v/512e/256f, `valence_distribution
{3: 8, 4: 250}`, `area_outlier_count: 0`, `max_adjacent_face_angle_radians: 0.802` (~46°). The 8
valence-3 poles are exactly the 8 original box corners — none clustered at the scoop/rim
transition, and zero area-outlier faces anywhere on the evaluated surface. Real evidence the
resolution-matched fix avoided introducing new poles at the curved transition, the classic
pinching failure mode this whole milestone was chosen to exercise. Independently re-verified via
`tools/verify_mesh.py` against a fresh `.blend`
(`runs/2026-08-07_soap-dish-subsurf/verify_reports/SoapDish_20260807T191714Z.json`): clean, 0
non-manifold/n-gons/degenerate faces, consistent normals.

**Logging-discipline gap, stated honestly rather than backfilled**: a context-window compaction
happened mid-session, and per-decision JSON records for the build-up portion (primitive creation,
proportion scaling, basin inset/subdivide) were never written to disk before it — there is no
server-side decision-history API to reconstruct them with real fidelity afterward (checked:
`modeler_server.py`'s `_command_journal` is an in-memory idempotency cache, not a persisted audit
trail). Rather than invent plausible-looking entries with fabricated revision numbers,
`runs/2026-08-07_soap-dish-subsurf/decision_log.jsonl` starts empty and `note.md` documents the
gap directly — a process fix for future sessions (log every decision immediately, from decision 1)
rather than something to paper over this time. No genuine unresolvable topology problem has
appeared yet, so per `docs/RESEARCH_ROADMAP.md` no research episode is triggered — watched
honestly, not manufactured.
