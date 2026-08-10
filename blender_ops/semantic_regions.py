"""Named, persistent groups of mesh elements -- "the outer handle curve",
"the mirror seam" -- so the agent can ask for a region by name instead of
rediscovering the same geometry every turn. Builds directly on persistent
element IDs: a region stores agent_ids (vertex/edge/face), not raw indices,
so it survives unrelated topology changes elsewhere in the mesh the same
way a single remembered element does.

Stored as a JSON string in a custom property on the object
(agent_semantic_regions), so it persists in the .blend like any other
object data, keyed by region_id.

Topology changes must update/invalidate regions honestly (directive
section 16): validate_region() re-checks that every stored ID still
resolves to a real element on the CURRENT mesh, rather than assuming
persistence. A region is not "valid" just because it was once created
correctly.
"""

import json

import bpy

import decision_state
import mesh_ops
import persistent_ids

_PROP_KEY = "agent_semantic_regions"

KNOWN_ROLES = {
    "primary_form", "secondary_form", "outer_contour", "silhouette_feature",
    "corner", "transition", "support_loop", "feature_edge", "mirror_seam",
    "hole_boundary", "attachment_region", "bevel_edge",
    "high_curvature", "flat_panel",
}


def _load(obj):
    raw = obj.get(_PROP_KEY, "")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _save(obj, regions):
    obj[_PROP_KEY] = json.dumps(regions)


def create_region(name, region_id, role, vertex_ids=None, edge_ids=None, face_ids=None):
    """Store a named region. role is free-form but should generally be one
    of KNOWN_ROLES for consistency; an unrecognized role is accepted (the
    vocabulary is a suggestion, not an enum) but flagged in the response.
    All given IDs are checked against the CURRENT id maps before storing --
    a region can't be created pointing at IDs that don't currently exist."""
    obj = bpy.data.objects[name]
    id_maps = persistent_ids.get_id_maps(name)
    vertex_ids = vertex_ids or []
    edge_ids = edge_ids or []
    face_ids = face_ids or []

    missing = {
        "verts": [i for i in vertex_ids if i not in id_maps["verts"]["id_to_index"]],
        "edges": [i for i in edge_ids if i not in id_maps["edges"]["id_to_index"]],
        "faces": [i for i in face_ids if i not in id_maps["faces"]["id_to_index"]],
    }
    if any(missing.values()):
        return {"error": f"some IDs don't currently exist on '{name}': {missing}"}

    revision = decision_state.current_revision()
    regions = _load(obj)
    regions[region_id] = {
        "region_id": region_id,
        "role": role,
        "vertex_ids": vertex_ids,
        "edge_ids": edge_ids,
        "face_ids": face_ids,
        "created_revision": revision,
        "last_validated_revision": revision,
    }
    _save(obj, regions)
    return {"region_id": region_id, "role_recognized": role in KNOWN_ROLES, "stored": regions[region_id]}


def get_region(name, region_id):
    obj = bpy.data.objects[name]
    regions = _load(obj)
    region = regions.get(region_id)
    if region is None:
        return {"error": f"no region '{region_id}' on '{name}'"}
    return region


def list_regions(name):
    obj = bpy.data.objects[name]
    regions = _load(obj)
    return {"region_ids": list(regions.keys())}


def validate_region(name, region_id):
    """Re-check every stored ID against the CURRENT mesh, not the mesh as
    of creation -- a topology change elsewhere could have merged/deleted
    some of this region's elements even if the region itself was never
    touched directly. Updates last_validated_revision only if still fully
    valid; a region with any missing element is reported invalid, not
    silently trimmed down."""
    obj = bpy.data.objects[name]
    regions = _load(obj)
    region = regions.get(region_id)
    if region is None:
        return {"error": f"no region '{region_id}' on '{name}'"}

    id_maps = persistent_ids.get_id_maps(name)
    missing = {
        "verts": [i for i in region["vertex_ids"] if i not in id_maps["verts"]["id_to_index"]],
        "edges": [i for i in region["edge_ids"] if i not in id_maps["edges"]["id_to_index"]],
        "faces": [i for i in region["face_ids"] if i not in id_maps["faces"]["id_to_index"]],
    }
    valid = not any(missing.values())
    if valid:
        region["last_validated_revision"] = decision_state.current_revision()
        regions[region_id] = region
        _save(obj, regions)
    return {"region_id": region_id, "valid": valid, "missing_ids": missing, "region": region}


def update_region(name, region_id, vertex_ids=None, edge_ids=None, face_ids=None, role=None):
    obj = bpy.data.objects[name]
    regions = _load(obj)
    region = regions.get(region_id)
    if region is None:
        return {"error": f"no region '{region_id}' on '{name}'"}
    if vertex_ids is not None:
        region["vertex_ids"] = vertex_ids
    if edge_ids is not None:
        region["edge_ids"] = edge_ids
    if face_ids is not None:
        region["face_ids"] = face_ids
    if role is not None:
        region["role"] = role
    regions[region_id] = region
    _save(obj, regions)
    return region


def delete_region(name, region_id):
    obj = bpy.data.objects[name]
    regions = _load(obj)
    if region_id not in regions:
        return {"error": f"no region '{region_id}' on '{name}'"}
    del regions[region_id]
    _save(obj, regions)
    return {"deleted": region_id}


def select_region(name, region_id, extend=False):
    """Resolve a region's stored persistent IDs to current selection --
    the natural bridge from "the region called X" to an actual mesh_ops
    selection call."""
    region = get_region(name, region_id)
    if "error" in region:
        return region
    return mesh_ops.select_by_ids(
        name, vertex_ids=region["vertex_ids"], edge_ids=region["edge_ids"],
        face_ids=region["face_ids"], extend=extend,
    )
