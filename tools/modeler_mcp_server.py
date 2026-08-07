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


if __name__ == "__main__":
    mcp.run()
