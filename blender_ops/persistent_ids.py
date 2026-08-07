"""Persistent per-element IDs that survive topology changes to OTHER parts
of the mesh, unlike Blender's own vertex/edge/face indices, which can
renumber after any bmesh operation touches the mesh at all -- observed
directly this session, when a dissolve+requad on one part of the Mug
shifted indices the agent had been tracking elsewhere.

Stored as custom int attribute layers (agent_vertex_id / agent_edge_id /
agent_face_id) so they round-trip through save/load like any other mesh
data, plus a per-object counter (custom property agent_id_counter, on the
object, not the mesh) so IDs are never reused even if a mesh datablock is
rebuilt.

0 means "not yet assigned" (real IDs start at 1) -- this reuses Blender's
own default int-attribute fill value as the sentinel rather than inventing
a separate flag, so a freshly created layer starts fully "unassigned" with
no extra initialization pass.

CORRECTION (found live, same session): 0-as-sentinel alone is not enough.
bmesh operators that interpolate custom data onto new geometry for
continuity (confirmed with bmesh.ops.bevel; likely true of others) copy a
SOURCE element's existing nonzero ID onto the new element instead of
leaving it 0 -- e.g. beveling one edge left three different vertices
sharing persistent ID 7. A "0 or already-seen-this-call" duplicate check
is required in addition to the zero check, or IDs silently stop being
unique, which defeats the entire point.

ensure_persistent_ids() is idempotent and cheap to call often: it assigns
fresh IDs to any element that is unassigned (0) OR a duplicate of an ID
already seen earlier in the same pass (interpolation copy). Call it after
any mutation that might have added geometry, before trusting IDs to be
complete -- decision_transaction.py does this automatically around every
transaction's target object.
"""

import bpy

import bmesh_io

_LAYER_NAMES = {"verts": "agent_vertex_id", "edges": "agent_edge_id", "faces": "agent_face_id"}
_COUNTER_KEY = "agent_id_counter"


def ensure_persistent_ids(name):
    """Assign a persistent ID to any vertex/edge/face on object `name` that
    doesn't have one yet. Returns how many new IDs were assigned per
    element type."""
    obj = bpy.data.objects[name]
    bm = bmesh_io.read_bmesh(obj)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    counter = int(obj.get(_COUNTER_KEY, 0))
    assigned = {"verts": 0, "edges": 0, "faces": 0}

    for kind, seq in (("verts", bm.verts), ("edges", bm.edges), ("faces", bm.faces)):
        layer = seq.layers.int.get(_LAYER_NAMES[kind])
        if layer is None:
            layer = seq.layers.int.new(_LAYER_NAMES[kind])
        seen = set()
        for elem in seq:
            val = elem[layer]
            if val == 0 or val in seen:
                counter += 1
                elem[layer] = counter
                assigned[kind] += 1
                seen.add(counter)
            else:
                seen.add(val)

    obj[_COUNTER_KEY] = counter
    bmesh_io.write_bmesh(obj, bm)
    return assigned


def get_id_maps(name):
    """Return, per element type, {index_to_id, id_to_index} reflecting
    current state. Elements without an assigned ID yet (0) are omitted --
    call ensure_persistent_ids first if completeness matters."""
    obj = bpy.data.objects[name]
    bm = bmesh_io.read_bmesh(obj)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    result = {}
    for kind, seq in (("verts", bm.verts), ("edges", bm.edges), ("faces", bm.faces)):
        layer = seq.layers.int.get(_LAYER_NAMES[kind])
        index_to_id, id_to_index = {}, {}
        if layer is not None:
            for elem in seq:
                agent_id = elem[layer]
                if agent_id != 0:
                    index_to_id[elem.index] = agent_id
                    id_to_index[agent_id] = elem.index
        result[kind] = {"index_to_id": index_to_id, "id_to_index": id_to_index}
    if obj.mode != "EDIT":
        bm.free()
    return result


def find_by_id(name, element_type, agent_id):
    """Resolve a remembered persistent ID back to its current Blender index
    and live data, even after unrelated topology changes elsewhere in the
    mesh have renumbered other elements. element_type is 'verts', 'edges',
    or 'faces'."""
    if element_type not in _LAYER_NAMES:
        return {"error": f"element_type must be one of {list(_LAYER_NAMES)}"}
    obj = bpy.data.objects[name]
    bm = bmesh_io.read_bmesh(obj)
    seq = getattr(bm, element_type)
    seq.ensure_lookup_table()
    layer = seq.layers.int.get(_LAYER_NAMES[element_type])

    result = None
    if layer is None:
        result = {"error": f"no {_LAYER_NAMES[element_type]} layer on '{name}' yet -- call ensure_persistent_ids first"}
    else:
        found = next((elem for elem in seq if elem[layer] == agent_id), None)
        if found is None:
            result = {"error": f"no {element_type[:-1]} with agent id {agent_id} found on '{name}'"}
        else:
            result = {"index": found.index}
            if element_type == "verts":
                result["position"] = list(found.co)
                result["valence"] = len(found.link_edges)
            elif element_type == "edges":
                result["vertex_indices"] = [v.index for v in found.verts]
                result["length"] = found.calc_length()
            elif element_type == "faces":
                result["vertex_indices"] = [v.index for v in found.verts]
                result["area"] = found.calc_area()

    if obj.mode != "EDIT":
        bm.free()
    return result
