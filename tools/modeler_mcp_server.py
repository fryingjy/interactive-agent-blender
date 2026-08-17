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
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from knowledge_engine.surface_cause_classifier import SurfaceCauseEvidence, classify_surface_cause

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
def get_curve_state(object_name: str) -> dict:
    """Read an editable curve's spline control points, handles, bevel/profile,
    taper, transforms, and dimensions without converting it to mesh geometry."""
    return _call("get_curve_state", name=object_name)


@mcp.tool()
def create_primitive(name: str, primitive_type: str, location: list[float] | None = None, dimensions: dict | None = None) -> dict:
    """Create a new mesh object from a basic primitive (cube, cylinder, sphere, cone, torus, plane) as the one-time starting block for a modeling session. dimensions is passed straight through to the underlying Blender operator as keyword arguments, since each primitive has different dimension parameters -- cube/plane: {"size": ...}; cylinder/sphere: {"radius": ...}; cone: {"radius1": ..., "radius2": ..., "depth": ...}; torus: {"major_radius": ..., "minor_radius": ...}. Free to call outside a decision transaction."""
    return _call("create_primitive", name=name, primitive_type=primitive_type, location=location, **(dimensions or {}))


@mcp.tool()
def create_profile_extrusion(name: str, profile: list[list[float]], depth: float) -> dict:
    """Create a single connected mesh by extruding an authored closed X/Z profile along Y. This is for measured continuous shells that should start from one editable cage rather than several object primitives. Side walls are quads; profiles with more than four points begin with n-gon caps and must receive deliberate local quad topology before SubD surface work. Free to call outside a decision because the object does not yet exist."""
    return _call("create_profile_extrusion", name=name, profile=profile, depth=depth)


@mcp.tool()
def create_profile_loft(name: str, front_profile: list[list[float]], rear_profile: list[list[float]], depth: float) -> dict:
    """Create one connected mesh by bridging authored front and rear X/Z outline loops along Y. Use this when a continuous manufactured shell changes from front to rear (taper, A-frame, rollover) and must not be assembled from separate box/cylinder primitives. Both loops must have matching point counts/order. Bridge walls are quads; n-gon caps need deliberate local quad topology before SubD work."""
    return _call("create_profile_loft", name=name, front_profile=front_profile, rear_profile=rear_profile, depth=depth)


@mcp.tool()
def create_quad_shell_grid(name: str, front_grid: list[list[list[float]]], rear_grid: list[list[list[float]]], active_cells: list[list[bool]]) -> dict:
    """Create one closed, connected, all-quad shell from matching authored front/rear point grids. Each true active_cells entry creates a quad patch; false cells create integrated openings whose boundary is bridged through the shell. This is for connected manufactured cages with U openings, vents, or apertures—not separate primitive assemblies. Keep grid coordinates authored from the reference rather than copied source geometry."""
    return _call("create_quad_shell_grid", name=name, front_grid=front_grid, rear_grid=rear_grid, active_cells=active_cells)


@mcp.tool()
def create_quad_shell_sections(name: str, section_grids: list[list[list[list[float]]]], active_cells: list[list[bool]]) -> dict:
    """Create one closed connected all-quad shell through two or more authored depth-section grids. Use intermediate sections to match a rounded top, folded A-frame, or tapered transition while keeping the form one editable mesh; false active cells are integrated openings."""
    return _call("create_quad_shell_sections", name=name, section_grids=section_grids, active_cells=active_cells)


@mcp.tool()
def get_selection(object_name: str) -> dict:
    """Currently selected vertex/edge/face IDs and the active selection mode for a mesh object."""
    return _call("get_selection", name=object_name)


@mcp.tool()
def list_persistent_ids(object_name: str) -> dict:
    """List every current vertex, edge, and face persistent agent_id on a mesh, regardless of selection. Use this before select_by_ids when a whole component or previously unselected region must be targeted explicitly after mode/modifier/save/UI changes."""
    return _call("list_persistent_ids", name=object_name)


@mcp.tool()
def get_mesh_geometry(object_name: str) -> dict:
    """Read a mesh control cage keyed by persistent IDs: local vertex positions,
    edges, and face centers/normals. Use it to identify an observed region before
    calling select_by_ids; it makes no scene changes."""
    return _call("get_mesh_geometry", name=object_name)


@mcp.tool()
def get_evaluated_defect_regions(object_name: str, area_outlier_ratio: float = 0.05, angle_threshold_degrees: float = 10, angle_local_spike_ratio: float = 2.0, max_tickets: int = 20) -> dict:
    """Localize CANDIDATE SubD surface problem areas on object_name's evaluated mesh to actual positions, then map each to the nearest persistent-ID vertices/faces on the base control cage (spatial nearest-neighbor, not exact identity -- the evaluated mesh has no persistent IDs of its own). Unlike get_evaluated_state's surface_quality (global counts/max only), this returns individual tickets sorted by severity for triage -- where to look next, e.g. with render_silhouette on that region. HONEST LIMITATION: this does NOT reliably distinguish real pinching from healthy smooth curvature -- tested against a deliberately bad case and a known-clean mesh, severity scores landed in the same range for both. Treat tickets as candidates worth visual inspection, not confirmed defects; likely_pole_artifact flags a nearby non-4-valence control-cage vertex, which has inherently reduced Catmull-Clark smoothness and is often NOT a real defect on its own."""
    return _call("get_evaluated_defect_regions", name=object_name, area_outlier_ratio=area_outlier_ratio, angle_threshold_degrees=angle_threshold_degrees, angle_local_spike_ratio=angle_local_spike_ratio, max_tickets=max_tickets)


@mcp.tool()
def classify_surface_defect_cause(
    base_geometry_changed: bool = False,
    evaluated_geometry_changed: bool = False,
    silhouette_or_depth_changed: bool = False,
    face_orientation_or_split_normals_changed: bool = False,
    normal_repair_neutralizes: bool = False,
    material_state_changed: bool = False,
    neutral_material_neutralizes: bool = False,
    lighting_state_changed: bool = False,
    neutral_lighting_neutralizes: bool = False,
    bevel_parameters_changed: bool = False,
    bevel_repair_neutralizes: bool = False,
) -> dict:
    """Classify GEOMETRY, NORMALS, MATERIAL, LIGHTING, or BEVEL_PROFILE from controlled intervention evidence. This does not diagnose a beauty image by itself. Supply state comparisons and whether the matching repair neutralized the discrepancy; mixed signatures return CONFLICTING and insufficient evidence returns UNRESOLVED."""
    diagnosis = classify_surface_cause(SurfaceCauseEvidence(
        base_geometry_changed=base_geometry_changed,
        evaluated_geometry_changed=evaluated_geometry_changed,
        silhouette_or_depth_changed=silhouette_or_depth_changed,
        face_orientation_or_split_normals_changed=face_orientation_or_split_normals_changed,
        normal_repair_neutralizes=normal_repair_neutralizes,
        material_state_changed=material_state_changed,
        neutral_material_neutralizes=neutral_material_neutralizes,
        lighting_state_changed=lighting_state_changed,
        neutral_lighting_neutralizes=neutral_lighting_neutralizes,
        bevel_parameters_changed=bevel_parameters_changed,
        bevel_repair_neutralizes=bevel_repair_neutralizes,
    ))
    return {
        "cause": diagnosis.cause,
        "confidence": diagnosis.confidence,
        "reasons": list(diagnosis.reasons),
        "next_action": diagnosis.next_action,
    }


@mcp.tool()
def get_modeling_stage(object_name: str) -> dict:
    """Current modeling stage for object_name (REFERENCE_ANALYSIS / PRIMARY_BLOCKOUT / PROPORTION_SILHOUETTE / SECONDARY_FORMS / TOPOLOGY_SURFACE / TERTIARY_DETAIL / PRODUCTION_PREP / FINAL_REVIEW, defaulting to REFERENCE_ANALYSIS if never set) plus the full transition log with the evidence recorded for each change."""
    return _call("get_modeling_stage", name=object_name)


@mcp.tool()
def set_modeling_stage(object_name: str, stage: str, evidence: dict) -> dict:
    """Move exactly one stage forward only after structured evidence passes the CURRENT stage's machine gate. Moving backward is an explicit logged regression. Forward transitions cannot skip stages or bypass the gate."""
    return _call("set_modeling_stage", name=object_name, stage=stage, evidence=evidence)


@mcp.tool()
def check_scene_component_coverage(decomposition: dict, collection_name: str | None = None) -> dict:
    """Read live mesh names and evaluated world bounds against a reference decomposition. This read-only, revision/session-bound record checks one-to-one presence plus optional board-supplied placement/proportion ranges; it does not judge shape, topology, or visual likeness."""
    return _call(
        "check_scene_component_coverage",
        decomposition=decomposition,
        collection_name=collection_name,
    )


@mcp.tool()
def create_curve(name: str, points: list[list[float]], bevel_depth: float = 0.05, closed: bool = False, curve_type: str = "POLY") -> dict:
    """Create a curve object from a list of [x, y, z] control points -- for geometry a mesh primitive can't represent (a path that wraps, overlaps, or tapers along its length; a torus is a symmetric ring and cannot do this). bevel_depth gives the path a round 3D cross-section of that radius. curve_type 'POLY' (straight segments, easiest to verify against measured reference coordinates) or 'BEZIER'. closed=True connects the last point back to the first. Free to call outside a decision transaction, same as create_primitive."""
    return _call("create_curve", name=name, points=points, bevel_depth=bevel_depth, closed=closed, curve_type=curve_type)


@mcp.tool()
def set_curve_bevel_depth(object_name: str, depth: float) -> dict:
    """Change a curve object's cross-section radius after creation."""
    return _call("set_curve_bevel_depth", name=object_name, depth=depth)


@mcp.tool()
def set_curve_points(object_name: str, points: list[list[float]]) -> dict:
    """Revise an existing curve's control-point coordinates without converting
    its spline, bevel profile, taper, or other editable curve settings. For a
    recoverable artistic decision, use begin_decision -> perform_decision with
    operation='set_curve_points' -> verify_decision -> commit/reject instead."""
    return _call("set_curve_points", name=object_name, points=points)


@mcp.tool()
def set_curve_taper(object_name: str, taper_object_name: str) -> dict:
    """Attach a separate curve object (typically a simple 2-point width-vs-position profile) as object_name's taper, scaling its cross-section along its own length. Both curve objects must already exist."""
    return _call("set_curve_taper", name=object_name, taper_object_name=taper_object_name)


@mcp.tool()
def set_curve_bevel_object(object_name: str, bevel_object_name: str, hide_profile: bool = True) -> dict:
    """Assign an editable CURVE cross-section to a curve path, allowing flattened
    or shaped profiles instead of a circular bevel-depth tube."""
    return _call("set_curve_bevel_object", name=object_name, bevel_object_name=bevel_object_name, hide_profile=hide_profile)


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
def analyze_bridge_selection(
    object_name: str,
    twist_offsets: list[int] | None = None,
    allow_unequal: bool = False,
) -> dict:
    """Simulate Bridge Edge Loops offsets without mutating object_name. Returns loop counts, per-offset connector/topology metrics, and a minimum-connector-length suggestion. Unequal loop counts are rejected unless allow_unequal=True; a suggestion is diagnostic evidence, not automatic artistic approval."""
    return _call(
        "analyze_bridge_selection",
        name=object_name,
        twist_offsets=twist_offsets,
        allow_unequal=allow_unequal,
    )


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
    """Read modifier-evaluated health, topology, surface-quality, candidate pinch/waviness diagnostics, and cage-vs-result bounds. Surface diagnostics remain candidate evidence and require contextual visual review."""
    return _call("get_evaluated_state", name=object_name)


@mcp.tool()
def get_hard_surface_shading_audit(object_name: str) -> dict:
    """Audit a hard-surface mesh's recorded semantic bevel weights, WEIGHT Bevel/SubD order, Smooth by Angle policy, and object-scale warning. Missing semantic intent is reported as REVIEW_REQUIRED rather than inferred."""
    return _call("get_hard_surface_shading_audit", name=object_name)


@mcp.tool()
def get_production_high_low_audit(
    high_object_name: str,
    low_object_name: str,
    silhouette_iou_by_view: dict[str, float],
    high_collection_name: str = "HIGH_POLY",
    low_collection_name: str = "LOW_POLY",
    max_low_to_high_face_ratio: float = 0.65,
    minimum_silhouette_iou: float = 0.90,
    minimum_view_count: int = 2,
    require_live_modifiers: bool = True,
) -> dict:
    """Audit separate high/low collections, genuinely lower base topology, connectivity, UV validity, multiview shape preservation, and live unapplied modifier stacks. Equal cages are classified as editable variants, not production retopology."""
    return _call(
        "get_production_high_low_audit",
        high_name=high_object_name,
        low_name=low_object_name,
        silhouette_iou_by_view=silhouette_iou_by_view,
        high_collection_name=high_collection_name,
        low_collection_name=low_collection_name,
        max_low_to_high_face_ratio=max_low_to_high_face_ratio,
        minimum_silhouette_iou=minimum_silhouette_iou,
        minimum_view_count=minimum_view_count,
        require_live_modifiers=require_live_modifiers,
    )


@mcp.tool()
def render_diagnostic_pass(object_names: list[str], output_path: str, pass_type: str, view: str = "front", resolution: int = 512, margin: float = 1.15, frame_names: list[str] | None = None) -> dict:
    """Render a Blender-native solid, MatCap, wireframe, normal, depth, or component-mask diagnostic PNG with scene revision and camera metadata."""
    return _call("render_diagnostic_pass", name=object_names, output_path=output_path, pass_type=pass_type, view=view, resolution=resolution, margin=margin, frame_name=frame_names)


@mcp.tool()
def render_semantic_region(object_name: str, region_id: str, output_path: str, view: str = "front", resolution: int = 512, margin: float = 1.15) -> dict:
    """Render one persistent-ID face region against its base-cage context; stale regions are rejected."""
    return _call("render_semantic_region", name=object_name, region_id=region_id, output_path=output_path, view=view, resolution=resolution, margin=margin)


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
    """Perform one sanctioned mutation for a pending decision. Choose an operation from get_capabilities; params are its keyword arguments. A stable command_id makes retries idempotent."""
    return _call("perform_decision", decision_id=decision_id, operation=operation, params=params, command_id=command_id)


@mcp.tool()
def check_external_edit(object_name: str) -> dict:
    """Read-only check: has object_name changed since this server last observed it (at the previous begin_decision or commit_decision), through a path other than a committed decision -- most likely a manual GUI edit? Does not require an open transaction. Safe to poll before starting new work; also runs automatically inside begin_decision, which refuses to start a transaction if this detects a change."""
    return _call("check_external_edit", name=object_name)


@mcp.tool()
def verify_decision(decision_id: str) -> dict:
    """Verify a performed decision. Mesh targets report health and persistent
    ID deltas; curve targets report editable spline/path state and null
    id_delta because curve controls are not mesh elements."""
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
