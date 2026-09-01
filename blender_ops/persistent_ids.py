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


def ensure_layers(bm):
    """Create the three persistent-ID custom data layers on this bmesh if
    they don't already exist, touching no element values.

    CORRECTION (found live, chasing a 'BMFace has been removed' error
    immediately after a clean extrude): creating a NEW custom data layer on
    a bmesh mid-session invalidates every previously-held Python element
    reference on that bmesh -- confirmed directly (captured a face
    reference, called bm.faces.layers.int.new(...) for an unrelated layer,
    and the captured reference's .is_valid immediately became False).
    mesh_ops._bm_from_object() calls this immediately after opening a bm,
    before any caller captures element references, so layer creation never
    happens later mid-operation and invalidates something still in use."""
    for seq, kind in ((bm.verts, "verts"), (bm.edges, "edges"), (bm.faces, "faces")):
        if seq.layers.int.get(_LAYER_NAMES[kind]) is None:
            seq.layers.int.new(_LAYER_NAMES[kind])


def clear_ids_in_open_bmesh(bm, verts=None, edges=None, faces=None):
    """For callers already holding an open bmesh mid-mutation (e.g.
    mesh_ops.extrude_selection): force the given elements' persistent-ID
    layer values back to 0 (unassigned), creating the layer if it doesn't
    exist yet.

    Exists because of a real gap in the duplicate-detection in
    ensure_persistent_ids(): that function only catches an ID appearing on
    2+ elements AT THE SAME TIME. If an operation creates new geometry that
    inherits a copied ID from an ORIGINAL element that gets deleted in the
    same operation (found live: bmesh.ops.extrude_face_region copies the
    input face's custom data onto the new cap, and extrude_selection then
    deletes the original as part of its own cleanup), there is never a
    moment where both elements coexist -- so no duplicate is ever observed,
    and the new element silently keeps an ID that isn't really its own. The
    caller that knows exactly which elements are genuinely new is in the
    best position to mark them unassigned explicitly, rather than relying
    on a detector with this blind spot.

    CORRECTION (found live, chasing another 'has been removed' error after
    the layer-creation fix above): the first version of this function
    determined which domain it was processing via `seq is bm.verts` /
    `... is bm.edges` identity comparison against a captured (seq, elements)
    tuple. bm.verts/bm.edges/bm.faces do not appear to be stable singletons
    -- the comparison silently failed for every domain, always falling
    through to the 'faces' branch, which then looked up (and, finding none,
    created) an "agent_face_id" layer on the VERTS domain -- a genuinely
    new layer, triggering the exact invalidation this function exists to
    avoid. Uses explicit string labels instead of identity comparison now."""
    for kind, seq, elements in (("verts", bm.verts, verts), ("edges", bm.edges, edges), ("faces", bm.faces, faces)):
        if not elements:
            continue
        layer = seq.layers.int.get(_LAYER_NAMES[kind])
        if layer is None:
            layer = seq.layers.int.new(_LAYER_NAMES[kind])
        for elem in elements:
            if elem.is_valid:
                elem[layer] = 0


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


def vertex_positions_by_id(name):
    """Return local-space positions keyed by complete persistent vertex ID."""
    ensure_persistent_ids(name)
    obj = bpy.data.objects[name]
    bm = bmesh_io.read_bmesh(obj)
    bm.verts.ensure_lookup_table()
    layer = bm.verts.layers.int.get(_LAYER_NAMES["verts"])
    result = {int(vertex[layer]): tuple(float(value) for value in vertex.co) for vertex in bm.verts}
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
