"""Object/scene-level helpers -- modifiers, undo/redo, file checkpoints --
distinct from mesh_ops.py's mesh-editing bmesh helpers, since none of these
touch bmesh at all.
"""

import math
import os
import time

import bpy

try:
    from . import persistent_ids
except ImportError:
    import persistent_ids


_PRIMITIVES = {
    "cube": bpy.ops.mesh.primitive_cube_add,
    "cylinder": bpy.ops.mesh.primitive_cylinder_add,
    "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
    "cone": bpy.ops.mesh.primitive_cone_add,
    "torus": bpy.ops.mesh.primitive_torus_add,
    "plane": bpy.ops.mesh.primitive_plane_add,
}


def create_primitive(name, primitive_type, location=(0.0, 0.0, 0.0), **kwargs):
    """Create a new mesh object from a basic primitive and give it `name`.
    Not itself an asset builder -- it's the one-time starting block a
    modeling session begins from, same as picking a base mesh in the
    Blender UI. All actual form comes from typed decisions afterward.

    kwargs are passed straight through to the underlying bpy.ops.mesh.*
    operator, since each primitive has different dimension parameters
    (cube/plane: size; cylinder/sphere: radius; cone: radius1/radius2/
    depth; torus: major_radius/minor_radius) -- there is no single generic
    "size" that means the same thing across all of them."""
    fn = _PRIMITIVES.get(primitive_type)
    if fn is None:
        raise ValueError(f"unknown primitive_type '{primitive_type}' -- available: {sorted(_PRIMITIVES)}")
    if name in bpy.data.objects:
        raise ValueError(f"object '{name}' already exists")
    fn(location=location, **kwargs)
    obj = bpy.context.active_object
    obj.name = name
    if obj.data is not None:
        obj.data.name = name
    return {"name": obj.name, "type": obj.type, "location": list(obj.location)}


def add_modifier(name, modifier_type, modifier_name=None):
    """CORRECTION (found live, chasing why a Subdivision Surface modifier's
    effect wasn't showing up in evaluated_probe's results): obj.modifiers.new()
    does NOT default show_viewport/show_render to True -- confirmed
    directly (a freshly created SUBSURF modifier read back show_viewport
    == False before this fix), so the modifier was silently invisible to
    both the evaluated-mesh dependency graph AND the actual Blender
    viewport the whole time. This likely also affected the speaker
    enclosure's earlier Bevel modifier test, which was never checked
    against the evaluated mesh (evaluated_probe.py didn't exist yet) --
    that decision is still an honest record of add_modifier/
    set_modifier_parameter succeeding, but not evidence the modifier was
    ever actually visible. Explicitly enabling both flags now."""
    obj = bpy.data.objects[name]
    mod = obj.modifiers.new(name=modifier_name or modifier_type.title(), type=modifier_type)
    mod.show_viewport = True
    mod.show_render = True
    return {"modifier_name": mod.name, "type": mod.type, "show_viewport": mod.show_viewport}


def set_modifier_parameter(name, modifier_name, parameter, value):
    obj = bpy.data.objects[name]
    mod = obj.modifiers.get(modifier_name)
    if mod is None:
        raise ValueError(f"no modifier '{modifier_name}' on '{name}' -- current modifiers: {[m.name for m in obj.modifiers]}")
    if not hasattr(mod, parameter):
        raise ValueError(f"modifier '{modifier_name}' ({mod.type}) has no parameter '{parameter}'")
    setattr(mod, parameter, value)
    return {"modifier_name": modifier_name, "parameter": parameter, "value": getattr(mod, parameter)}


def set_shading(name, smooth=True):
    """Set polygon interpolation explicitly on one mesh object.

    Smooth/flat shading changes the visible surface without changing topology, so it belongs in
    the same one-decision transaction path as modifier edits rather than in presentation fallback
    code.  The mesh snapshot owned by DecisionTransaction preserves polygon flags for rollback.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    value = bool(smooth)
    changed = 0
    for polygon in obj.data.polygons:
        if polygon.use_smooth != value:
            polygon.use_smooth = value
            changed += 1
    obj.data.update()
    return {"smooth": value, "changed_polygons": changed, "polygon_count": len(obj.data.polygons)}


def set_smooth_by_angle(name, angle=0.5235987756, keep_sharp_edges=True):
    """Apply Blender's Smooth by Angle asset to one mesh.

    This is the hard-surface default when a mesh needs normal interpolation
    without smoothing across every design transition.  It deliberately does
    not replace topology: first identify semantic hard edges, use a scoped
    Bevel (normally WEIGHT) where a physical radius is required, put Bevel
    before SubD when both are warranted, then use this for the remaining
    normal split/shading behavior.  Do not call ``set_shading(..., True)`` as
    a blanket substitute for that sequence.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    result = bpy.ops.object.shade_smooth_by_angle(
        angle=float(angle), keep_sharp_edges=bool(keep_sharp_edges)
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Smooth by Angle failed for '{name}': {result}")
    obj["shading_policy"] = "SMOOTH_BY_ANGLE"
    obj["smooth_by_angle_radians"] = float(angle)
    obj["smooth_by_angle_keep_sharp_edges"] = bool(keep_sharp_edges)
    return {
        "shading": "SMOOTH_BY_ANGLE",
        "angle": float(angle),
        "keep_sharp_edges": bool(keep_sharp_edges),
        "modifier_count": len(obj.modifiers),
    }


def set_bevel_weight_by_ids(name, edge_ids, weight=1.0, clear_others=False):
    """Assign a semantic bevel-weight set by persistent edge IDs.

    The caller must first inspect the cage and choose the design edges that
    require a physical radius. It is not a "make everything sharp" command.
    Blender 5 stores this as the generic ``bevel_weight_edge`` float
    attribute, so persistent IDs protect authored intent across unrelated
    topology edits.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    if obj.mode == "EDIT":
        raise ValueError("set_bevel_weight_by_ids requires Object Mode; leave Edit Mode before changing mesh attributes")
    value = float(weight)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"weight must be in [0, 1], got {weight}")
    persistent_ids.ensure_persistent_ids(name)
    id_map = persistent_ids.get_id_maps(name)["edges"]["id_to_index"]
    attribute = obj.data.attributes.get("bevel_weight_edge")
    if attribute is None:
        attribute = obj.data.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
    if attribute.domain != "EDGE":
        raise ValueError("bevel_weight_edge exists but is not an EDGE-domain attribute")
    if clear_others:
        for item in attribute.data:
            item.value = 0.0
    assigned, missing = [], []
    for agent_id in edge_ids:
        edge_index = id_map.get(int(agent_id))
        if edge_index is None:
            missing.append(int(agent_id))
            continue
        attribute.data[edge_index].value = value
        assigned.append(int(agent_id))
    # Persist exactly what this decision regarded as sharp so later review can
    # distinguish an incomplete semantic map from an intentionally sparse one.
    index_to_id = persistent_ids.get_id_maps(name)["edges"]["index_to_id"]
    obj["hard_surface_intended_bevel_edge_ids"] = sorted(
        int(index_to_id[index]) for index, item in enumerate(attribute.data) if item.value > 0.999
    )
    obj.data.update()
    return {
        "attribute": "bevel_weight_edge",
        "weight": value,
        "assigned_edge_ids": assigned,
        "missing_edge_ids": missing,
        "clear_others": bool(clear_others),
    }


def set_bevel_scoping(name, method, modifier_name=None, angle_deg=None, vertex_group=None, width=None, segments=None):
    """Configure a Bevel modifier's scoping method and record matching deliberate
    intent, for the two documented alternatives to WEIGHT (see bevel_modifier.md:
    ANGLE correctly excludes coplanar triangulation edges in a controlled test).

    Unlike WEIGHT (`set_bevel_weight_by_ids`, which maps to inspectable persistent
    edge IDs), ANGLE and VGROUP intent is recorded as an explicit parameter value
    the caller is asserting was a deliberate choice, not merely Blender's default
    left untouched. This does not retroactively grant intent to an existing
    unrecorded Bevel modifier; the caller must actively call this to claim it.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    if method not in ("ANGLE", "VGROUP"):
        raise ValueError("set_bevel_scoping only handles ANGLE or VGROUP; use set_bevel_weight_by_ids for WEIGHT")
    if method == "ANGLE" and angle_deg is None:
        raise ValueError("angle_deg is required to record deliberate ANGLE intent")
    if method == "VGROUP" and not vertex_group:
        raise ValueError("vertex_group is required to record deliberate VGROUP intent")
    if method == "VGROUP" and vertex_group not in obj.vertex_groups:
        raise ValueError(f"vertex group '{vertex_group}' does not exist on '{name}'")

    bevel = None
    if modifier_name is not None:
        bevel = obj.modifiers.get(modifier_name)
        if bevel is None or bevel.type != "BEVEL":
            raise ValueError(f"'{modifier_name}' is not a Bevel modifier on '{name}'")
    else:
        existing = [m for m in obj.modifiers if m.type == "BEVEL"]
        bevel = existing[0] if existing else obj.modifiers.new("Semantic scoped edge radius", "BEVEL")

    bevel.limit_method = method
    if width is not None:
        bevel.width = float(width)
    if segments is not None:
        bevel.segments = int(segments)
    if method == "ANGLE":
        bevel.angle_limit = math.radians(float(angle_deg))
        obj["hard_surface_bevel_scoping_method"] = "ANGLE"
        obj["hard_surface_bevel_angle_deg"] = float(angle_deg)
        obj.pop("hard_surface_bevel_vertex_group", None)
    else:
        bevel.vertex_group = vertex_group
        obj["hard_surface_bevel_scoping_method"] = "VGROUP"
        obj["hard_surface_bevel_vertex_group"] = vertex_group
        obj.pop("hard_surface_bevel_angle_deg", None)
    obj.data.update()
    return {
        "modifier": bevel.name,
        "limit_method": bevel.limit_method,
        "angle_deg": float(angle_deg) if method == "ANGLE" else None,
        "vertex_group": vertex_group if method == "VGROUP" else None,
        "width": bevel.width,
        "segments": bevel.segments,
    }


def hard_surface_shading_audit(name):
    """Read whether an annotated hard-surface mesh follows the active policy.

    This intentionally cannot decide which unannotated edges *should* be
    sharp. It verifies the narrower, auditable contract: identified semantic
    edges are weighted, a WEIGHT Bevel is ordered before any SubD, the normal
    policy is Smooth by Angle, and unapplied non-uniform scale is visible.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    persistent_ids.ensure_persistent_ids(name)
    id_maps = persistent_ids.get_id_maps(name)["edges"]
    attr = obj.data.attributes.get("bevel_weight_edge")
    weighted_ids = []
    if attr is not None and attr.domain == "EDGE":
        weighted_ids = sorted(
            int(id_maps["index_to_id"][index]) for index, item in enumerate(attr.data)
            if item.value > 0.999 and index in id_maps["index_to_id"]
        )
    intended_ids = sorted(int(item) for item in obj.get("hard_surface_intended_bevel_edge_ids", []))
    modifier_types = [modifier.type for modifier in obj.modifiers]
    bevel_modifiers = [(index, modifier) for index, modifier in enumerate(obj.modifiers) if modifier.type == "BEVEL"]
    weighted_bevel_indices = [index for index, modifier in bevel_modifiers if modifier.limit_method == "WEIGHT"]
    # ANGLE and VGROUP are documented, deliberate scoping mechanisms distinct from WEIGHT
    # (see knowledge/foundation/operator_cards/bevel_modifier.md: ANGLE correctly excluded
    # coplanar triangulation edges in a controlled test). They are not treated as equivalent
    # to a recorded semantic edge-ID map, because neither maps to inspectable persistent IDs
    # the way `hard_surface_intended_bevel_edge_ids` does, but a bare limit_method of NONE
    # (or no Bevel modifier at all) is a materially weaker, undifferentiated case.
    bevel_scoping_methods = sorted({modifier.limit_method for _, modifier in bevel_modifiers})
    non_weight_scoped_indices = [
        index for index, modifier in bevel_modifiers
        if modifier.limit_method in ("ANGLE", "VGROUP")
    ]
    subd_indices = [index for index, modifier in enumerate(obj.modifiers) if modifier.type == "SUBSURF"]
    scale = tuple(float(item) for item in obj.scale)
    uniform_scale = max(scale) - min(scale) < 1e-6
    blanket_smooth = bool(obj.data.polygons) and all(poly.use_smooth for poly in obj.data.polygons)

    # Second, differently-shaped path to auditable intent: a caller that used
    # set_bevel_scoping() to deliberately claim an ANGLE/VGROUP parameter, not
    # merely leaving a modifier at whatever value it happened to have. This is
    # additive -- it never grants intent to a bevel that never called it.
    recorded_method = obj.get("hard_surface_bevel_scoping_method")
    angle_scoped_indices = [index for index, modifier in bevel_modifiers if modifier.limit_method == "ANGLE"]
    vgroup_scoped_indices = [index for index, modifier in bevel_modifiers if modifier.limit_method == "VGROUP"]
    scoping_intent_recorded = recorded_method in ("ANGLE", "VGROUP")
    scoping_intent_matches_actual = False
    scoping_bevel_indices = []
    if recorded_method == "ANGLE":
        scoping_bevel_indices = angle_scoped_indices
        recorded_angle = obj.get("hard_surface_bevel_angle_deg")
        scoping_intent_matches_actual = bool(scoping_bevel_indices) and recorded_angle is not None and any(
            abs(math.degrees(obj.modifiers[index].angle_limit) - float(recorded_angle)) < 0.01
            for index in scoping_bevel_indices
        )
    elif recorded_method == "VGROUP":
        scoping_bevel_indices = vgroup_scoped_indices
        recorded_group = obj.get("hard_surface_bevel_vertex_group")
        scoping_intent_matches_actual = bool(scoping_bevel_indices) and recorded_group is not None and any(
            obj.modifiers[index].vertex_group == recorded_group for index in scoping_bevel_indices
        )
    angle_or_vgroup_path_ok = scoping_intent_recorded and scoping_intent_matches_actual
    effective_bevel_indices = weighted_bevel_indices or (scoping_bevel_indices if angle_or_vgroup_path_ok else [])

    checks = {
        "semantic_intent_recorded": bool(intended_ids),
        "semantic_weights_match_intent": bool(intended_ids) and weighted_ids == intended_ids,
        "weight_limited_bevel_present": bool(weighted_bevel_indices),
        "angle_or_vgroup_intent_recorded": scoping_intent_recorded,
        "angle_or_vgroup_intent_matches_actual": scoping_intent_matches_actual,
        "bevel_before_subd": not subd_indices or (bool(effective_bevel_indices) and min(effective_bevel_indices) < min(subd_indices)),
        "smooth_by_angle_recorded": obj.get("shading_policy") == "SMOOTH_BY_ANGLE",
        "uniform_object_scale": uniform_scale,
        "not_unannotated_blanket_smooth": not (blanket_smooth and obj.get("shading_policy") != "SMOOTH_BY_ANGLE"),
    }
    weight_path_ok = checks["semantic_intent_recorded"] and checks["semantic_weights_match_intent"] and checks["weight_limited_bevel_present"]
    passed = (
        (weight_path_ok or angle_or_vgroup_path_ok)
        and checks["bevel_before_subd"]
        and checks["smooth_by_angle_recorded"]
        and checks["uniform_object_scale"]
        and checks["not_unannotated_blanket_smooth"]
    )
    warnings = []
    if not weight_path_ok and not angle_or_vgroup_path_ok:
        if non_weight_scoped_indices and not weighted_bevel_indices:
            method_names = "/".join(bevel_scoping_methods)
            warnings.append(
                f"No WEIGHT-based semantic edge-ID intent is recorded; this object uses "
                f"{method_names}-limited Bevel but never recorded deliberate intent via "
                f"set_bevel_scoping(), so it cannot be distinguished from an unmodified default."
            )
        else:
            warnings.append("No persistent semantic bevel-edge intent is recorded; edge completeness cannot be judged.")
    if not checks["uniform_object_scale"]:
        warnings.append("Non-uniform object scale can distort Bevel width in world space.")
    if not checks["smooth_by_angle_recorded"]:
        warnings.append("Smooth by Angle was not recorded as the normal policy.")
    if not checks["bevel_before_subd"]:
        warnings.append("The intent-recorded Bevel must precede Subdivision Surface for this policy.")
    return {
        "name": name,
        "status": "PASS" if passed else "REVIEW_REQUIRED",
        "checks": checks,
        "bevel_limit_methods_present": bevel_scoping_methods,
        "weighted_edge_ids": weighted_ids,
        "intended_bevel_edge_ids": intended_ids,
        "modifier_types": modifier_types,
        "object_scale": scale,
        "warnings": warnings,
    }


def undo():
    """CORRECTION (found live, testing this against a scratch object):
    this does NOT reliably undo "the last decision." DecisionTransaction
    mutations write via bm.to_mesh()+obj.data.update(), which do NOT push
    an entry onto Blender's own undo stack -- confirmed directly: one
    mesh_ops mutation followed by exactly one undo() call deleted the
    ENTIRE object, jumping straight past the mutation to the last real
    bpy.ops-recorded action (object creation). Any number of committed
    decisions on an object can be sitting between "now" and whatever
    undo() actually reverts to. Do not call this expecting it to revert
    one committed decision -- verify with get_full_state/mesh_health
    before and after, on every call, and treat a large unexpected change
    as the normal outcome, not a bug."""
    bpy.ops.ed.undo()
    return {"undone": True}


def redo():
    """See undo()'s docstring -- the same disconnect between Blender's
    undo stack and DecisionTransaction's bmesh-direct mutations applies
    in reverse."""
    bpy.ops.ed.redo()
    return {"redone": True}


def save_checkpoint(label, directory):
    """Save a labeled, timestamped copy of the current file WITHOUT
    switching the working file (copy=True) -- a restorable snapshot, not a
    save-and-continue-from-here."""
    os.makedirs(directory, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    filename = f"{label}_{ts}.blend"
    filepath = os.path.join(directory, filename)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)
    return {"filepath": filepath}


def restore_checkpoint(filepath):
    """Reload a previously saved checkpoint, replacing the entire live
    scene. Irreversible for any unsaved work since that checkpoint --
    callers should save_checkpoint first if the current state matters."""
    bpy.ops.wm.open_mainfile(filepath=filepath)
    return {"restored": filepath}


def save_file(filepath=None):
    if filepath:
        bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)
        return {"filepath": filepath}
    bpy.ops.wm.save_mainfile()
    return {"filepath": bpy.data.filepath}
