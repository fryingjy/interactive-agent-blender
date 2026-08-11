"""Layered external-edit fingerprinting (master directive section 9).

modeler_server.py's original _check_external_edit only diffed persistent-ID
SETS -- it proves topology was added/removed, but a human can move existing
vertices, change the object's transform, or change a modifier's parameters
while every persistent ID stays exactly the same, and the old check would
report no edit at all. compute() returns four independent layers so a caller
can tell not just THAT something changed but WHICH kind of change happened:

    topology    -- persistent-ID sets per element type (the original check)
    geometry    -- a hash of (persistent_id, rounded position) pairs, so any
                   vertex move is caught even with zero ID churn
    transform   -- the object's own location/rotation/scale
    modifiers   -- name/type/show_viewport/params per modifier, catching a
                   parameter tweak (e.g. dragging the Subsurf level in the
                   GUI) that touches no mesh data at all

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
    id_maps = persistent_ids.get_id_maps(name)
    topology = {kind: frozenset(m["id_to_index"]) for kind, m in id_maps.items()}
    return {
        "topology": topology,
        "geometry_hash": _geometry_hash(obj),
        "transform": {
            "location": tuple(round(c, 6) for c in obj.location),
            "rotation_euler": tuple(round(c, 6) for c in obj.rotation_euler),
            "scale": tuple(round(c, 6) for c in obj.scale),
        },
        "modifiers": _modifier_params(obj),
    }


def diff(previous, current):
    """Compare two compute() results layer by layer. Returns
    (detected: bool, diff: dict) -- diff always has all four keys so a
    caller can see which layers were checked, not just whether SOMETHING
    changed."""
    detected = False
    out = {}

    topo_diff = {}
    for kind in ("verts", "edges", "faces"):
        added = sorted(current["topology"][kind] - previous["topology"][kind])
        removed = sorted(previous["topology"][kind] - current["topology"][kind])
        if added or removed:
            detected = True
        topo_diff[kind] = {"added": added, "removed": removed}
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

    return detected, out
