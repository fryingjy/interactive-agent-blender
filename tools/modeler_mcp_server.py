# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp[cli]<2,>=1.3.0"]
# ///
"""Typed MCP server for the custom Blender modeler add-on
(blender_ops/modeler_server.py, socket on localhost:9878). Wraps the raw
length-prefixed JSON protocol as named MCP tools, so the model calls
`bevel_selection`-shaped operations instead of sending arbitrary Python via
blender-mcp's execute_code.

Registered in .mcp.json as a second server ("modeler") alongside the
existing "blender" one -- MCP servers load at Claude Code session start,
so a session already running when this file is added will not see these
tools until it restarts. blender_ops/modeler_server.py must be running
inside Blender (loaded via execute_blender_code, or eventually via
permanent add-on registration) before any of these tools will succeed;
they fail with a clear connection error otherwise, not a silent hang.
"""
import json
import socket
import struct

from mcp.server.fastmcp import FastMCP

HOST = "localhost"
PORT = 9878

mcp = FastMCP("blender-modeler")


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("modeler_server closed the connection mid-message")
        buf += chunk
    return buf


def _call(command, **params):
    try:
        sock = socket.create_connection((HOST, PORT), timeout=15)
    except OSError as e:
        raise RuntimeError(
            f"could not reach the modeler add-on server at {HOST}:{PORT} ({e}) -- "
            "is blender_ops/modeler_server.py running inside Blender?"
        ) from e
    try:
        payload = json.dumps({"id": "1", "command": command, "params": params}).encode("utf-8")
        sock.sendall(struct.pack(">I", len(payload)) + payload)
        (length,) = struct.unpack(">I", _recv_exact(sock, 4))
        resp = json.loads(_recv_exact(sock, length).decode("utf-8"))
        if resp["status"] != "ok":
            raise RuntimeError(resp.get("message", "unknown modeler_server error"))
        return resp["result"]
    finally:
        sock.close()


@mcp.tool()
def get_capabilities() -> dict:
    """Report the modeler add-on's protocol version, Blender version, process ID, and which typed operations are currently available."""
    return _call("get_capabilities")


@mcp.tool()
def get_full_state(object_name: str) -> dict:
    """One consolidated read for a mesh object: live decision revision, mesh health (non-manifold/n-gon/degenerate counts), vertex valence distribution, current selection, and persistent-ID coverage."""
    return _call("get_full_state", name=object_name)


@mcp.tool()
def create_primitive(name: str, primitive_type: str, location: list[float] | None = None, dimensions: dict | None = None) -> dict:
    """Create a new mesh object from a basic primitive (cube, cylinder, sphere, cone, torus, plane) as the one-time starting block for a modeling session. dimensions is passed straight through to the underlying Blender operator as keyword arguments, since each primitive has different dimension parameters -- cube/plane: {"size": ...}; cylinder/sphere: {"radius": ...}; cone: {"radius1": ..., "radius2": ..., "depth": ...}; torus: {"major_radius": ..., "minor_radius": ...}. Free to call outside a decision transaction."""
    return _call("create_primitive", name=name, primitive_type=primitive_type, location=location, **(dimensions or {}))


@mcp.tool()
def get_selection(object_name: str) -> dict:
    """Currently selected vertex/edge/face IDs and the active selection mode for a mesh object."""
    return _call("get_selection", name=object_name)


@mcp.tool()
def get_evaluated_defect_regions(object_name: str, area_outlier_ratio: float = 0.05, angle_threshold_degrees: float = 10, angle_local_spike_ratio: float = 2.0, max_tickets: int = 20) -> dict:
    """Localize CANDIDATE SubD surface problem areas on object_name's evaluated mesh to actual positions, then map each to the nearest persistent-ID vertices/faces on the base control cage (spatial nearest-neighbor, not exact identity -- the evaluated mesh has no persistent IDs of its own). Unlike get_evaluated_state's surface_quality (global counts/max only), this returns individual tickets sorted by severity for triage -- where to look next, e.g. with render_silhouette on that region. HONEST LIMITATION: this does NOT reliably distinguish real pinching from healthy smooth curvature -- tested against a deliberately bad case and a known-clean mesh, severity scores landed in the same range for both. Treat tickets as candidates worth visual inspection, not confirmed defects; likely_pole_artifact flags a nearby non-4-valence control-cage vertex, which has inherently reduced Catmull-Clark smoothness and is often NOT a real defect on its own."""
    return _call("get_evaluated_defect_regions", name=object_name, area_outlier_ratio=area_outlier_ratio, angle_threshold_degrees=angle_threshold_degrees, angle_local_spike_ratio=angle_local_spike_ratio, max_tickets=max_tickets)


@mcp.tool()
def get_modeling_stage(object_name: str) -> dict:
    """Current modeling stage for object_name (REFERENCE_ANALYSIS / PRIMARY_BLOCKOUT / PROPORTION_SILHOUETTE / SECONDARY_FORMS / TOPOLOGY_SURFACE / TERTIARY_DETAIL / PRODUCTION_PREP / FINAL_REVIEW, defaulting to REFERENCE_ANALYSIS if never set) plus the full transition log with the evidence recorded for each change."""
    return _call("get_modeling_stage", name=object_name)


@mcp.tool()
def set_modeling_stage(object_name: str, stage: str, evidence: str) -> dict:
    """Explicitly declare object_name has moved to `stage`, with `evidence` describing why that stage's gate criteria are judged met (see blender_ops/modeling_stage.py's GATE_CRITERIA for what each stage expects) -- not automatically verified, but logged, so the check has to be articulated rather than silently skipped. Moving backward (e.g. a later check reveals an earlier stage's judgment was wrong) is normal and logged as a regression, not an error."""
    return _call("set_modeling_stage", name=object_name, stage=stage, evidence=evidence)


@mcp.tool()
def create_curve(name: str, points: list[list[float]], bevel_depth: float = 0.05, closed: bool = False, curve_type: str = "POLY") -> dict:
    """Create a curve object from a list of [x, y, z] control points -- for geometry a mesh primitive can't represent (a path that wraps, overlaps, or tapers along its length; a torus is a symmetric ring and cannot do this). bevel_depth gives the path a round 3D cross-section of that radius. curve_type 'POLY' (straight segments, easiest to verify against measured reference coordinates) or 'BEZIER'. closed=True connects the last point back to the first. Free to call outside a decision transaction, same as create_primitive."""
    return _call("create_curve", name=name, points=points, bevel_depth=bevel_depth, closed=closed, curve_type=curve_type)


@mcp.tool()
def set_curve_bevel_depth(object_name: str, depth: float) -> dict:
    """Change a curve object's cross-section radius after creation."""
    return _call("set_curve_bevel_depth", name=object_name, depth=depth)


@mcp.tool()
def set_curve_taper(object_name: str, taper_object_name: str) -> dict:
    """Attach a separate curve object (typically a simple 2-point width-vs-position profile) as object_name's taper, scaling its cross-section along its own length. Both curve objects must already exist."""
    return _call("set_curve_taper", name=object_name, taper_object_name=taper_object_name)


@mcp.tool()
def convert_curve_to_mesh(object_name: str, new_mesh_name: str | None = None, merge_dist: float = 0.0001) -> dict:
    """Bake a curve's evaluated (bevel + taper applied) shape into a new, separate editable mesh object -- the bridge back into the normal bmesh-based typed vocabulary (bevel_edges, subdivide_selection, etc.) once a curve-based blockout reads correctly. Leaves the source curve object untouched. Automatically welds the beveled tube's end-cap seams (a real, confirmed gap in Blender's own curve-to-mesh conversion -- the caps are not merged to the tube wall by default), so the result is already 0-non-manifold, not something the caller needs to clean up separately."""
    return _call("convert_curve_to_mesh", name=object_name, new_mesh_name=new_mesh_name, merge_dist=merge_dist)


@mcp.tool()
def select_by_ids(object_name: str, vertex_ids: list[int] | None = None, edge_ids: list[int] | None = None, face_ids: list[int] | None = None, extend: bool = False) -> dict:
    """Select mesh elements by persistent agent_id (from get_selection/get_full_state) rather than a raw index, so the caller can remember and reselect specific elements even after unrelated topology changes elsewhere in the mesh. Set extend=True to add to the current selection instead of replacing it. This is a selection change, not an artistic mutation -- callable freely, no decision transaction needed."""
    return _call("select_by_ids", name=object_name, vertex_ids=vertex_ids, edge_ids=edge_ids, face_ids=face_ids, extend=extend)


@mcp.tool()
def get_viewport_state() -> dict:
    """Direct viewport state for the first 3D viewport: projection type (perspective/orthographic/camera), a best-effort standard-orientation label (FRONT/TOP/RIGHT/...), view distance/location, shading mode (wireframe/solid/material/rendered), x-ray, local view, and the active camera's transform if one is set. Lets you know what kind of view you're evaluating without inferring it from rendered pixels."""
    return _call("get_viewport_state")


@mcp.tool()
def inspect_region(object_name: str, center_ids: list[int], rings: int = 2) -> dict:
    """A local topology graph around one or more persistent vertex agent_ids, grown outward by `rings` edge-hops. Returns every vertex/edge/face touching the region (keyed by agent_id, not raw index), plus region-level quality signals: pole locations (valence != 4), edge-length ratio, face-area ratio, local triangle/quad/ngon counts, and connected-component count. Richer than get_selection/vertex_neighborhood for judging whether a specific area of the mesh reads as clean."""
    return _call("inspect_region", name=object_name, center_ids=center_ids, rings=rings)


@mcp.tool()
def create_region(object_name: str, region_id: str, role: str, vertex_ids: list[int] | None = None, edge_ids: list[int] | None = None, face_ids: list[int] | None = None) -> dict:
    """Name a persistent group of mesh elements (by agent_id, not index) for later reference -- e.g. 'outer_handle_curve' with role 'silhouette_feature'. Suggested roles: primary_form, secondary_form, outer_contour, silhouette_feature, corner, transition, support_loop, feature_edge, mirror_seam, hole_boundary, attachment_region, bevel_edge (any string is accepted; unrecognized roles are flagged, not rejected). All IDs must currently exist on the object."""
    return _call("create_region", name=object_name, region_id=region_id, role=role, vertex_ids=vertex_ids, edge_ids=edge_ids, face_ids=face_ids)


@mcp.tool()
def get_region(object_name: str, region_id: str) -> dict:
    """Look up a previously created named region."""
    return _call("get_region", name=object_name, region_id=region_id)


@mcp.tool()
def list_regions(object_name: str) -> dict:
    """List all named region IDs stored on an object."""
    return _call("list_regions", name=object_name)


@mcp.tool()
def validate_region(object_name: str, region_id: str) -> dict:
    """Re-check whether every element in a named region still exists on the CURRENT mesh -- a topology change elsewhere could have merged or deleted some of them even if the region itself was never touched directly. A region is not assumed valid just because it was once created correctly."""
    return _call("validate_region", name=object_name, region_id=region_id)


@mcp.tool()
def update_region(object_name: str, region_id: str, vertex_ids: list[int] | None = None, edge_ids: list[int] | None = None, face_ids: list[int] | None = None, role: str | None = None) -> dict:
    """Update a named region's stored element IDs and/or role. Only the fields you pass are changed."""
    return _call("update_region", name=object_name, region_id=region_id, vertex_ids=vertex_ids, edge_ids=edge_ids, face_ids=face_ids, role=role)


@mcp.tool()
def delete_region(object_name: str, region_id: str) -> dict:
    """Delete a named region."""
    return _call("delete_region", name=object_name, region_id=region_id)


@mcp.tool()
def select_region(object_name: str, region_id: str, extend: bool = False) -> dict:
    """Select every element stored in a named region -- the bridge from 'the region called X' to an actual selection you can then extrude/move/scale/bevel."""
    return _call("select_region", name=object_name, region_id=region_id, extend=extend)


@mcp.tool()
def undo() -> dict:
    """Call Blender's own undo. WARNING, confirmed by direct testing: this does NOT reliably undo "the last decision." DecisionTransaction mutations write directly via bmesh, which do not push entries onto Blender's undo stack -- one such mutation followed by a single undo() call deleted an entire object, jumping straight past the mutation to the last real bpy.ops-recorded action (its creation). Any number of committed decisions can sit between "now" and whatever this actually reverts to. Always check mesh_health/get_full_state before and after; do not assume a small, single-decision-sized change."""
    return _call("undo")


@mcp.tool()
def redo() -> dict:
    """Call Blender's own redo. See undo()'s warning -- the same disconnect between Blender's undo stack and DecisionTransaction's bmesh-direct mutations applies in reverse."""
    return _call("redo")


@mcp.tool()
def save_checkpoint(label: str, directory: str) -> dict:
    """Save a labeled, timestamped snapshot of the current file (copy, not a save-and-continue-from-here) to directory. Returns the filepath."""
    return _call("save_checkpoint", label=label, directory=directory)


@mcp.tool()
def restore_checkpoint(filepath: str) -> dict:
    """Reload a previously saved checkpoint file, replacing the entire live scene. Irreversible for any unsaved work since that checkpoint."""
    return _call("restore_checkpoint", filepath=filepath)


@mcp.tool()
def save_file(filepath: str | None = None) -> dict:
    """Save the current file. Pass filepath to save a copy elsewhere without switching the working file; omit to save in place."""
    return _call("save_file", filepath=filepath)


@mcp.tool()
def get_evaluated_state(object_name: str) -> dict:
    """Read the modifier-EVALUATED mesh (what the surface actually looks like after the modifier stack runs, e.g. Subdivision Surface), not the base control cage every other state command reads. Returns mesh_health, valence_distribution, surface_quality (face-area outlier detection and max adjacent-face angle -- signals aimed at spotting subdivision pinching, which doesn't show up as a validity failure), and bounding_box (base-cage vs evaluated-surface dimensions/shrinkage_ratio_xyz per axis -- catches SubD silhouette shrinkage from missing support loops, which pinching signals alone can miss)."""
    return _call("get_evaluated_state", name=object_name)


@mcp.tool()
def heartbeat() -> dict:
    """Cheap liveness/identity check: session_id, process ID, current revision, uptime, and pending-decision count. Call after a reconnect to confirm you're still talking to the same Blender process and server session as before, not a fresh unrelated one."""
    return _call("heartbeat")


@mcp.tool()
def get_control_mode() -> dict:
    """Report the current ownership mode: AGENT_CONTROL (default -- the agent may start decisions), USER_CONTROL (a human has declared control; begin_decision refuses to start), or SHARED_OBSERVATION."""
    return _call("get_control_mode")


@mcp.tool()
def set_control_mode(mode: str) -> dict:
    """Set the ownership mode to one of AGENT_CONTROL, USER_CONTROL, or SHARED_OBSERVATION. While not AGENT_CONTROL, begin_decision refuses to start any new transaction -- the agent does not attempt mutations while a human has declared control."""
    return _call("set_control_mode", mode=mode)


@mcp.tool()
def poll_events(since_seq: int = 0) -> dict:
    """Poll for scene-change events (mesh_changed, undo, redo, file_saved) with sequence number greater than since_seq. This is eventual-consistency polling, not real-time push -- event delivery latency is tied to Blender's redraw cycle and can be tens of seconds with no other viewport activity; do not treat a missing event as proof nothing changed."""
    return _call("poll_events", since_seq=since_seq)


@mcp.tool()
def begin_decision(object_name: str, action_type: str) -> dict:
    """Start exactly one decision transaction against object_name, labeled with action_type. Must be followed by perform_decision, verify_decision, and commit_decision (in that order) before starting another transaction on the same object."""
    return _call("begin_decision", name=object_name, action_type=action_type)


@mcp.tool()
def perform_decision(decision_id: str, operation: str, params: dict, command_id: str | None = None) -> dict:
    """Perform the single sanctioned mutation for a pending decision_id. operation must be one of the available_operations reported by get_capabilities (currently: bevel_edges, merge_by_distance, add_ring_detail, recalc_normals, triangulate_ngons); params are that operation's keyword arguments. Pass a stable command_id to make retries safe: a repeated call with the same command_id returns the original stored result instead of mutating the mesh again."""
    return _call("perform_decision", decision_id=decision_id, operation=operation, params=params, command_id=command_id)


@mcp.tool()
def check_external_edit(object_name: str) -> dict:
    """Read-only check: has object_name changed since this server last observed it (at the previous begin_decision or commit_decision), through a path other than a committed decision -- most likely a manual GUI edit? Does not require an open transaction. Safe to poll before starting new work; also runs automatically inside begin_decision, which refuses to start a transaction if this detects a change."""
    return _call("check_external_edit", name=object_name)


@mcp.tool()
def verify_decision(decision_id: str) -> dict:
    """Verify a performed decision: before/after mesh health, and the added/removed persistent vertex/edge/face IDs (id_delta) -- the real, provable change caused by exactly this one decision."""
    return _call("verify_decision", decision_id=decision_id)


@mcp.tool()
def commit_decision(decision_id: str) -> dict:
    """Commit a verified decision, advancing the live decision-revision counter by exactly one and releasing decision_id."""
    return _call("commit_decision", decision_id=decision_id)


@mcp.tool()
def render_silhouette(object_name: str | list[str], output_path: str, view: str = "front", resolution: int = 512, margin: float = 1.15) -> dict:
    """Blender-native (not a GUI screenshot) orthographic silhouette render of object_name's modifier-evaluated mesh to output_path (PNG, transparent background, flat unlit fill -- the alpha channel IS the silhouette mask directly). object_name may be a single name or a list of names, rendered as one combined silhouette framed to their combined bounding box -- use a list for a multi-component prop modeled as separate objects. view is one of 'front'/'side'/'top'. Read-only: does not require or affect a decision transaction. Returns silhouette_fill_ratio (fraction of the frame the silhouette covers) alongside the output path."""
    return _call("render_silhouette", name=object_name, output_path=output_path, view=view, resolution=resolution, margin=margin)


@mcp.tool()
def abandon_decision(decision_id: str, reason: str = "") -> dict:
    """Discard a pending decision that never reached perform_decision (e.g. perform_decision itself failed -- a mid-transaction external edit, an invalid operation, bad params). Use this instead of reject_decision when nothing was ever actually mutated -- reject_decision correctly refuses that case since there's no mutation to roll back."""
    return _call("abandon_decision", decision_id=decision_id, reason=reason)


@mcp.tool()
def reject_decision(decision_id: str, reason: str = "") -> dict:
    """Transaction-owned rollback: restore the target object to exactly its state before perform_decision ran (geometry and transform), independent of Blender's global undo stack, and release decision_id WITHOUT advancing the live decision-revision counter -- the scene is left exactly as if this decision never happened. Use this instead of commit_decision when verify_decision's result is judged unacceptable."""
    return _call("reject_decision", decision_id=decision_id, reason=reason)


if __name__ == "__main__":
    mcp.run()
