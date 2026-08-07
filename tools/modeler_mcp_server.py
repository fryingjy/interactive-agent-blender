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
def get_selection(object_name: str) -> dict:
    """Currently selected vertex/edge/face IDs and the active selection mode for a mesh object."""
    return _call("get_selection", name=object_name)


@mcp.tool()
def select_by_ids(object_name: str, vertex_ids: list[int] | None = None, edge_ids: list[int] | None = None, face_ids: list[int] | None = None, extend: bool = False) -> dict:
    """Select mesh elements by persistent agent_id (from get_selection/get_full_state) rather than a raw index, so the caller can remember and reselect specific elements even after unrelated topology changes elsewhere in the mesh. Set extend=True to add to the current selection instead of replacing it. This is a selection change, not an artistic mutation -- callable freely, no decision transaction needed."""
    return _call("select_by_ids", name=object_name, vertex_ids=vertex_ids, edge_ids=edge_ids, face_ids=face_ids, extend=extend)


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
