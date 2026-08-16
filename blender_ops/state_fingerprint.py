"""Layered external-edit fingerprinting (master directive section 9).

modeler_server.py's original _check_external_edit only diffed persistent-ID
SETS -- it proves topology was added/removed, but a human can move existing
vertices, change the object's transform, or change a modifier's parameters
while every persistent ID stays exactly the same, and the old check would
report no edit at all. compute() returns five independent layers so a caller
can tell not just THAT something changed but WHICH kind of change happened:

    topology    -- persistent-ID sets per element type (the original check)
    geometry    -- a hash of (persistent_id, rounded position) pairs, so any
                   vertex move is caught even with zero ID churn
    transform   -- the object's own location/rotation/scale
    modifiers   -- name/type/show_viewport/params per modifier, catching a
                   parameter tweak (e.g. dragging the Subsurf level in the
                   GUI) that touches no mesh data at all
    object_state -- visibility and collection ownership, so hiding or
                    archiving a component is also detected

Each layer is compared independently in diff() so a caller can distinguish
"someone moved a vertex" from "someone added geometry" from "someone changed
a modifier slider" rather than getting one undifferentiated boolean.
"""

import hashlib

import bpy

import bmesh_io
import persistent_ids

_VERT_LAYER = "agent_vertex_id"


def _geometry_hash(obj):
    """Hash of (persistent_vertex_id, rounded position) pairs, sorted by ID
    -- order-independent and stable across unrelated topology changes
    elsewhere on the mesh, unlike raw vertex-index-ordered coordinates."""
    bm = bmesh_io.read_bmesh(obj)
    bm.verts.ensure_lookup_table()
    layer = bm.verts.layers.int.get(_VERT_LAYER)
    positions = {}
    if layer is not None:
        for v in bm.verts:
            vid = v[layer]
            if vid != 0:
                positions[vid] = tuple(round(c, 6) for c in v.co)
    if obj.mode != "EDIT":
        bm.free()
    payload = repr(sorted(positions.items())).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _curve_geometry_hash(obj):
    """Hash authored curve controls/handles without coercing a curve to mesh."""
    payload = []
    for spline in obj.data.splines:
        if spline.type == "BEZIER":
            payload.append((spline.type, bool(spline.use_cyclic_u), [
                (tuple(round(c, 6) for c in point.co),
                 tuple(round(c, 6) for c in point.handle_left),
                 tuple(round(c, 6) for c in point.handle_right),
                 point.handle_left_type, point.handle_right_type)
                for point in spline.bezier_points
            ]))
        else:
            payload.append((spline.type, bool(spline.use_cyclic_u), [
                tuple(round(c, 6) for c in point.co) for point in spline.points
            ]))
    return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()


def _modifier_params(obj):
    """Serialize every modifier's simple (int/float/str/bool) properties.
    Skips complex properties (object refs, arrays) deliberately -- this is
    a change-detection signature, not a full modifier serializer, and
    read-only/RNA-internal properties are excluded since they can't have
    been set by an edit anyway."""
    result = []
    for mod in obj.modifiers:
        params = {}
        for prop in mod.bl_rna.properties:
            if prop.identifier == "rna_type" or prop.is_readonly:
                continue
            try:
                val = getattr(mod, prop.identifier)
            except Exception:
                continue
            if isinstance(val, (int, float, str, bool)):
                params[prop.identifier] = val
        result.append({
            "name": mod.name, "type": mod.type,
            "show_viewport": mod.show_viewport, "show_render": mod.show_render,
            "params": params,
        })
    return result


def compute(name):
    """Full layered fingerprint for object `name`. Caller must have already
    called persistent_ids.ensure_persistent_ids(name) if completeness of the
    topology layer matters (mirrors the existing _snapshot_ids contract)."""
    obj = bpy.data.objects[name]
    if obj.type == "MESH":
        id_maps = persistent_ids.get_id_maps(name)
        topology = {kind: frozenset(m["id_to_index"]) for kind, m in id_maps.items()}
        geometry_hash = _geometry_hash(obj)
    elif obj.type == "CURVE":
        topology = {"splines": tuple(
            (spline.type, len(spline.bezier_points if spline.type == "BEZIER" else spline.points), bool(spline.use_cyclic_u))
            for spline in obj.data.splines
        )}
        geometry_hash = _curve_geometry_hash(obj)
    else:
        raise ValueError(f"state fingerprint supports MESH or CURVE, got {obj.type!r}")
    return {
        "object_type": obj.type,
        "topology": topology,
        "geometry_hash": geometry_hash,
        "transform": {
            "location": tuple(round(c, 6) for c in obj.location),
            "rotation_euler": tuple(round(c, 6) for c in obj.rotation_euler),
            "scale": tuple(round(c, 6) for c in obj.scale),
        },
        "modifiers": _modifier_params(obj),
        "object_state": {
            "hide_viewport": bool(obj.hide_get()),
            "hide_render": bool(obj.hide_render),
            "collections": tuple(sorted(collection.name for collection in obj.users_collection)),
        },
    }


def diff(previous, current):
    """Compare two compute() results layer by layer. Returns
    (detected: bool, diff: dict) -- diff always records every layer so a
    caller can see which layers were checked, not just whether SOMETHING
    changed."""
    detected = False
    out = {}

    topo_diff = {}
    if previous.get("object_type") == current.get("object_type") == "MESH":
        for kind in ("verts", "edges", "faces"):
            added = sorted(current["topology"][kind] - previous["topology"][kind])
            removed = sorted(previous["topology"][kind] - current["topology"][kind])
            if added or removed:
                detected = True
            topo_diff[kind] = {"added": added, "removed": removed}
    else:
        topology_changed = previous.get("topology") != current.get("topology")
        if topology_changed:
            detected = True
        topo_diff = {"object_type_before": previous.get("object_type"), "object_type_after": current.get("object_type"), "changed": topology_changed}
    out["topology"] = topo_diff

    geometry_moved = current["geometry_hash"] != previous["geometry_hash"]
    if geometry_moved:
        detected = True
    out["geometry_moved"] = geometry_moved

    transform_changed = current["transform"] != previous["transform"]
    if transform_changed:
        detected = True
    out["transform_changed"] = transform_changed
    if transform_changed:
        out["transform_before"] = previous["transform"]
        out["transform_after"] = current["transform"]

    modifiers_changed = current["modifiers"] != previous["modifiers"]
    if modifiers_changed:
        detected = True
    out["modifiers_changed"] = modifiers_changed
    if modifiers_changed:
        out["modifiers_before"] = previous["modifiers"]
        out["modifiers_after"] = current["modifiers"]

    object_state_changed = current.get("object_state") != previous.get("object_state")
    if object_state_changed:
        detected = True
    out["object_state_changed"] = object_state_changed
    if object_state_changed:
        out["object_state_before"] = previous.get("object_state")
        out["object_state_after"] = current.get("object_state")

    return detected, out
