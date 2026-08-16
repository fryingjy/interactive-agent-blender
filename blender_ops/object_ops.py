"""Object/scene-level helpers -- modifiers, undo/redo, file checkpoints --
distinct from mesh_ops.py's mesh-editing bmesh helpers, since none of these
touch bmesh at all.
"""

import math
import os
import sys
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

_REFERENCE_AXIS_ROTATIONS = {
    "FRONT": (math.pi / 2.0, 0.0, 0.0),
    "RIGHT": (0.0, math.pi / 2.0, 0.0),
    "TOP": (0.0, 0.0, 0.0),
}

_REFERENCE_AXIS_NORMALS = {
    "FRONT": (0.0, -1.0, 0.0),
    "RIGHT": (1.0, 0.0, 0.0),
    "TOP": (0.0, 0.0, 1.0),
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


def translate_object(name, delta):
    """Translate an independently manufactured assembly in world space.

    Mesh edits remain the right mechanism for a connected cage. This operation
    is intentionally separate for assemblies (dial modules, controls, moving
    hands) whose relative placement is a reversible object-level decision.
    ``DecisionTransaction`` snapshots object transforms, so rejection restores
    this translation without depending on global Undo.
    """
    if not isinstance(delta, (list, tuple)) or len(delta) != 3:
        raise ValueError("delta must contain exactly three numeric values")
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type not in {"MESH", "CURVE"}:
        raise ValueError(f"translate_object requires a MESH or CURVE object, got {name!r}")
    offset = tuple(float(value) for value in delta)
    obj.location = tuple(float(current) + change for current, change in zip(obj.location, offset))
    return {"name": obj.name, "location": [float(value) for value in obj.location], "delta": list(offset)}


def create_reference_image(
    name,
    image_path,
    view_axis,
    location=(0.0, 0.0, 0.0),
    display_size=1.0,
    opacity=0.7,
    collection_name="CONSTRUCTION_REFERENCES",
    source_role="CONSTRUCTION",
    calibrated=True,
    custom_rotation=None,
):
    """Create one typed image Empty with explicit construction-view authority.

    FRONT/RIGHT/TOP are principal-axis construction references. CUSTOM is retained only for
    observed perspective cards or controlled failure fixtures and can never be marked calibrated.
    The operation does not infer that two cards depict the same object or that a photograph is
    orthographic; those are reference-evidence questions outside Blender's scene state.
    """
    clean_name = str(name).strip()
    if not clean_name:
        raise ValueError("reference object name cannot be empty")
    if clean_name in bpy.data.objects:
        raise ValueError(f"object '{clean_name}' already exists")
    source_path = os.path.abspath(os.path.expanduser(str(image_path)))
    if not os.path.isfile(source_path):
        raise ValueError(f"reference image does not exist: {source_path}")
    axis = str(view_axis).strip().upper()
    if axis not in {*_REFERENCE_AXIS_ROTATIONS, "CUSTOM"}:
        raise ValueError("view_axis must be FRONT, RIGHT, TOP, or CUSTOM")
    if axis == "CUSTOM":
        if custom_rotation is None or len(custom_rotation) != 3:
            raise ValueError("CUSTOM reference alignment requires a three-value custom_rotation")
        if calibrated:
            raise ValueError("CUSTOM reference alignment cannot be marked calibrated")
        rotation = tuple(float(value) for value in custom_rotation)
    else:
        if custom_rotation is not None:
            raise ValueError("custom_rotation is valid only for CUSTOM alignment")
        rotation = _REFERENCE_AXIS_ROTATIONS[axis]
    size = float(display_size)
    alpha = float(opacity)
    if size <= 0:
        raise ValueError("display_size must be positive")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("opacity must be in [0, 1]")

    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(str(collection_name))
        bpy.context.scene.collection.children.link(collection)
    image = bpy.data.images.load(source_path, check_existing=True)
    obj = bpy.data.objects.new(clean_name, None)
    collection.objects.link(obj)
    obj.empty_display_type = "IMAGE"
    obj.data = image
    obj.empty_display_size = size
    obj.empty_image_depth = "FRONT"
    obj.color[3] = alpha
    obj.show_in_front = True
    obj.location = tuple(float(value) for value in location)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = rotation
    obj["reference_view_axis"] = axis
    obj["reference_source_role"] = str(source_role).strip().upper() or "CONSTRUCTION"
    obj["reference_calibrated"] = bool(calibrated) and axis != "CUSTOM"
    obj["reference_source_path"] = source_path
    return {
        "name": obj.name,
        "type": obj.type,
        "display_type": obj.empty_display_type,
        "image": image.name,
        "view_axis": axis,
        "calibrated": bool(obj["reference_calibrated"]),
        "rotation_euler": [float(value) for value in obj.rotation_euler],
        "location": [float(value) for value in obj.location],
        "collection": collection.name,
    }


def audit_reference_images(
    collection_name="CONSTRUCTION_REFERENCES",
    angular_tolerance_degrees=0.1,
    require_distinct_sources=False,
):
    """Audit typed image references without claiming photographic calibration or fidelity."""
    from mathutils import Vector

    collection = bpy.data.collections.get(str(collection_name))
    if collection is None:
        raise ValueError(f"missing reference collection: {collection_name}")
    # Direct object-property writes do not guarantee an immediately refreshed matrix_world.
    # Force the same dependency update a viewport redraw would provide before measuring axes.
    bpy.context.view_layer.update()
    tolerance = float(angular_tolerance_degrees)
    if tolerance < 0:
        raise ValueError("angular_tolerance_degrees must be non-negative")
    records = []
    source_axes = {}
    for obj in sorted(collection.all_objects, key=lambda item: item.name):
        axis = str(obj.get("reference_view_axis", "")).upper()
        source_path = str(obj.get("reference_source_path", ""))
        expected = _REFERENCE_AXIS_NORMALS.get(axis)
        actual = obj.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
        actual.normalize()
        if expected:
            dot = min(1.0, max(-1.0, abs(actual.dot(Vector(expected)))))
            angular_error = math.degrees(math.acos(dot))
        else:
            angular_error = None
        source_axes.setdefault(source_path, set()).add(axis)
        checks = {
            "is_image_empty": obj.type == "EMPTY" and obj.empty_display_type == "IMAGE",
            "image_loaded": obj.data is not None,
            "principal_axis_declared": expected is not None,
            "axis_alignment_within_tolerance": (
                angular_error is not None and angular_error <= tolerance
            ),
            "calibration_intent_recorded": bool(obj.get("reference_calibrated", False)),
        }
        records.append(
            {
                "name": obj.name,
                "view_axis": axis,
                "source_path": source_path,
                "source_role": obj.get("reference_source_role"),
                "actual_normal": [float(value) for value in actual],
                "angular_error_degrees": angular_error,
                "checks": checks,
                "pass": all(checks.values()),
            }
        )
    duplicated_cross_axis_sources = sorted(
        path for path, axes in source_axes.items() if path and len(axes & set(_REFERENCE_AXIS_NORMALS)) > 1
    )
    distinct_sources_ok = not require_distinct_sources or not duplicated_cross_axis_sources
    return {
        "collection": collection.name,
        "reference_count": len(records),
        "records": records,
        "duplicated_cross_axis_sources": duplicated_cross_axis_sources,
        "checks": {
            "references_present": bool(records),
            "all_principal_axis_references_valid": bool(records) and all(item["pass"] for item in records),
            "distinct_sources_when_required": distinct_sources_ok,
        },
        "pass": bool(records) and all(item["pass"] for item in records) and distinct_sources_ok,
        "claim_boundary": (
            "This audit verifies Blender image-Empty type, declared role, and principal-axis "
            "alignment. It does not prove that source photographs are orthographic, same-variant, "
            "dimensionally calibrated, or visually sufficient."
        ),
    }


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
    """CORRECTION (found live, setting up a Shrinkwrap's `target` for the
    handle-attachment transfer test): a modifier property that points at
    another object (Shrinkwrap.target, Mirror.mirror_object, Boolean.object,
    Array.offset_object, ...) is a bpy.types.Object reference, not a string --
    `setattr(mod, 'target', 'SomeObjectName')` raises `expected a Object type,
    not str`. Every other typed op in this module takes plain object *names*,
    so resolving a string value against bpy.data.objects here (only for
    properties whose RNA type is actually POINTER-to-Object) keeps that same
    convention instead of forcing callers to know this one property behaves
    differently."""
    obj = bpy.data.objects[name]
    mod = obj.modifiers.get(modifier_name)
    if mod is None:
        raise ValueError(f"no modifier '{modifier_name}' on '{name}' -- current modifiers: {[m.name for m in obj.modifiers]}")
    if not hasattr(mod, parameter):
        raise ValueError(f"modifier '{modifier_name}' ({mod.type}) has no parameter '{parameter}'")
    prop_rna = mod.bl_rna.properties.get(parameter)
    if (
        isinstance(value, str)
        and prop_rna is not None
        and prop_rna.type == "POINTER"
        and getattr(prop_rna.fixed_type, "identifier", None) == "Object"
    ):
        target_obj = bpy.data.objects.get(value)
        if target_obj is None:
            raise ValueError(f"'{parameter}' expects an object, but '{value}' does not exist in bpy.data.objects")
        value = target_obj
    setattr(mod, parameter, value)
    result_value = getattr(mod, parameter)
    if isinstance(result_value, bpy.types.Object):
        result_value = result_value.name
    return {"modifier_name": modifier_name, "parameter": parameter, "value": result_value}


def _copy_modifier_stack(source, target):
    for modifier in list(target.modifiers):
        target.modifiers.remove(modifier)
    copied = []
    for source_modifier in source.modifiers:
        target_modifier = target.modifiers.new(name=source_modifier.name, type=source_modifier.type)
        for prop in source_modifier.bl_rna.properties:
            identifier = prop.identifier
            if identifier in {"rna_type", "name", "type"} or prop.is_readonly:
                continue
            try:
                setattr(target_modifier, identifier, getattr(source_modifier, identifier))
            except (AttributeError, TypeError, ValueError):
                continue
        copied.append({"name": target_modifier.name, "type": target_modifier.type})
    return copied


def replace_mesh_from_object(name, source_name, copy_modifiers=True, copy_transform=False):
    """Replace a failed component cage while preserving its stable object identity.

    The source remains untouched as a reversible candidate. A decision transaction snapshots the
    target, so rejection restores the previous target without relying on Blender Undo.
    """
    target = bpy.data.objects.get(name)
    source = bpy.data.objects.get(source_name)
    if target is None or target.type != "MESH":
        raise ValueError(f"target '{name}' must be an existing mesh object")
    if source is None or source.type != "MESH":
        raise ValueError(f"source '{source_name}' must be an existing mesh object")
    if target is source:
        raise ValueError("source and target objects must differ")
    if target.mode != "OBJECT" or source.mode != "OBJECT":
        raise ValueError("mesh replacement requires both objects in Object Mode")
    old_mesh = target.data
    new_mesh = source.data.copy()
    new_mesh.name = f"{target.name}_Mesh"
    target.data = new_mesh
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    copied_modifiers = _copy_modifier_stack(source, target) if bool(copy_modifiers) else []
    if bool(copy_transform):
        target.matrix_world = source.matrix_world.copy()
    target["replacement_source"] = source.name
    return {
        "target": target.name,
        "source": source.name,
        "mesh": target.data.name,
        "vertices": len(target.data.vertices),
        "edges": len(target.data.edges),
        "faces": len(target.data.polygons),
        "copied_modifiers": copied_modifiers,
        "transform_copied": bool(copy_transform),
        "source_preserved": source.name in bpy.data.objects,
    }


def archive_object(name, collection_name="REJECTED_COMPONENTS"):
    """Move a failed component into a hidden, recoverable collection instead of deleting it."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"object '{name}' does not exist")
    clean_collection_name = str(collection_name).strip()
    if not clean_collection_name:
        raise ValueError("archive collection name cannot be empty")
    collection = bpy.data.collections.get(clean_collection_name)
    created = collection is None
    if collection is None:
        collection = bpy.data.collections.new(clean_collection_name)
        bpy.context.scene.collection.children.link(collection)
    previous = [item.name for item in obj.users_collection]
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.hide_render = True
    obj.hide_set(True)
    obj["archived_component"] = True
    return {
        "name": obj.name,
        "archive_collection": collection.name,
        "archive_collection_created": created,
        "previous_collections": previous,
        "hidden_in_viewport": obj.hide_get(),
        "hidden_in_render": obj.hide_render,
        "recoverable": True,
    }


def object_lifecycle_state(name):
    """Read the identity, ownership, visibility, geometry, and modifier state of one object."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError(f"object '{name}' does not exist")
    return {
        "name": obj.name,
        "type": obj.type,
        "data": obj.data.name if obj.data is not None else None,
        "collections": sorted(collection.name for collection in obj.users_collection),
        "hidden_in_viewport": bool(obj.hide_get()),
        "hidden_in_render": bool(obj.hide_render),
        "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
        "edges": len(obj.data.edges) if obj.type == "MESH" else None,
        "faces": len(obj.data.polygons) if obj.type == "MESH" else None,
        "modifiers": [{"name": modifier.name, "type": modifier.type} for modifier in obj.modifiers],
        "replacement_source": obj.get("replacement_source"),
        "archived_component": bool(obj.get("archived_component", False)),
    }


def package_high_low_variants(
    name,
    low_object_name,
    high_collection_name="HIGH_POLY",
    low_collection_name="LOW_POLY",
    low_subd_levels=0,
    hide_low=True,
):
    """Package one cage as separate editable high/low collection variants.

    This is non-destructive packaging, not retopology: the low object gets an
    independent copy of the base mesh and modifier stack. Subdivision remains
    present at ``low_subd_levels`` and no modifier is applied.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' must be an existing mesh object")
    low_object_name = str(low_object_name).strip()
    high_collection_name = str(high_collection_name).strip()
    low_collection_name = str(low_collection_name).strip()
    if not low_object_name or not high_collection_name or not low_collection_name:
        raise ValueError("low object and collection names cannot be empty")
    if low_object_name == name:
        raise ValueError("low_object_name must differ from the high/source object name")
    if high_collection_name == low_collection_name:
        raise ValueError("high and low collection names must differ")
    if (
        not isinstance(low_subd_levels, int)
        or isinstance(low_subd_levels, bool)
        or not 0 <= low_subd_levels <= 6
    ):
        raise ValueError("low_subd_levels must be an integer between 0 and 6")
    if low_object_name in bpy.data.objects:
        raise ValueError(f"object '{low_object_name}' already exists")
    high_collection = bpy.data.collections.get(high_collection_name)
    low_collection = bpy.data.collections.get(low_collection_name)
    if (high_collection is None) != (low_collection is None):
        existing = high_collection_name if high_collection is not None else low_collection_name
        missing = low_collection_name if low_collection is None else high_collection_name
        raise ValueError(
            f"incomplete variant collection pair: '{existing}' exists but '{missing}' does not"
        )
    collections_reused = high_collection is not None
    if high_collection is None:
        high_collection = bpy.data.collections.new(high_collection_name)
        low_collection = bpy.data.collections.new(low_collection_name)
        bpy.context.scene.collection.children.link(high_collection)
        bpy.context.scene.collection.children.link(low_collection)
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    high_collection.objects.link(obj)
    obj["production_variant"] = "HIGH_POLY"

    low = obj.copy()
    low.data = obj.data.copy()
    low.name = low_object_name
    low.data.name = f"{low_object_name}_Mesh"
    low["production_variant"] = "LOW_POLY"
    low_collection.objects.link(low)
    for modifier in low.modifiers:
        if modifier.type == "SUBSURF":
            modifier.levels = low_subd_levels
            modifier.render_levels = low_subd_levels
    # ``hide_set`` is view-layer state and does not reliably survive a fresh
    # file open.  The asset packaging contract needs a durable saved-file
    # setting, so record both the global object flag and current-view state.
    low.hide_viewport = bool(hide_low)
    low.hide_render = bool(hide_low)
    low.hide_set(bool(hide_low))

    def modifier_record(target):
        return [
            {
                "name": modifier.name,
                "type": modifier.type,
                "levels": getattr(modifier, "levels", None),
                "viewport_levels": getattr(modifier, "levels", None),
                "render_levels": getattr(modifier, "render_levels", None),
            }
            for modifier in target.modifiers
        ]

    def variant_record(target, collection):
        return {
            "object": target.name,
            "mesh": target.data.name,
            "collection": collection.name,
            "base_vertices": len(target.data.vertices),
            "base_edges": len(target.data.edges),
            "base_faces": len(target.data.polygons),
            "modifiers": modifier_record(target),
            "modifiers_applied": False,
            "hidden_in_viewport": bool(target.hide_viewport),
            "hidden_in_active_view_layer": target.hide_get(),
            "hidden_in_render": target.hide_render,
        }

    return {
        "high": variant_record(obj, high_collection),
        "low": variant_record(low, low_collection),
        "separate_collections": True,
        "collections_reused": collections_reused,
        "independent_mesh_datablocks": obj.data is not low.data,
        "all_modifiers_unapplied": True,
        "workflow_boundary": "editable duplicate packaging; low-poly retopology is not performed",
    }


def production_high_low_audit(
    high_name,
    low_name,
    silhouette_iou_by_view,
    high_collection_name="HIGH_POLY",
    low_collection_name="LOW_POLY",
    max_low_to_high_face_ratio=0.65,
    minimum_silhouette_iou=0.90,
    minimum_view_count=2,
    require_live_modifiers=True,
):
    """Read-only audit separating production topology from editable duplicate packaging.

    Current live modifier stacks are observable; past modifier application is not. The result keeps
    that history boundary explicit and never infers retopology from collection names alone.
    """
    high = bpy.data.objects.get(high_name)
    low = bpy.data.objects.get(low_name)
    if high is None or high.type != "MESH":
        raise ValueError(f"'{high_name}' must be an existing mesh object")
    if low is None or low.type != "MESH":
        raise ValueError(f"'{low_name}' must be an existing mesh object")
    if high is low:
        raise ValueError("high and low objects must differ")

    def connected_components(obj):
        adjacency = {vertex.index: set() for vertex in obj.data.vertices}
        for edge in obj.data.edges:
            a, b = edge.vertices
            adjacency[a].add(b)
            adjacency[b].add(a)
        unseen = set(adjacency)
        count = 0
        while unseen:
            count += 1
            stack = [unseen.pop()]
            while stack:
                current = stack.pop()
                neighbors = adjacency[current] & unseen
                unseen.difference_update(neighbors)
                stack.extend(neighbors)
        return count

    def uv_record(obj):
        layer = obj.data.uv_layers.active
        if layer is None:
            return {
                "layer": None,
                "loop_count": 0,
                "degenerate_faces": len(obj.data.polygons),
                "inside_unit_tile": False,
            }
        degenerate = 0
        inside = True
        for polygon in obj.data.polygons:
            coords = [layer.data[index].uv for index in polygon.loop_indices]
            area = abs(sum(
                coords[index].x * coords[(index + 1) % len(coords)].y
                - coords[(index + 1) % len(coords)].x * coords[index].y
                for index in range(len(coords))
            ) * 0.5)
            if area < 1e-10:
                degenerate += 1
            inside = inside and all(
                -1e-6 <= uv.x <= 1.000001 and -1e-6 <= uv.y <= 1.000001
                for uv in coords
            )
        return {
            "layer": layer.name,
            "loop_count": len(layer.data),
            "degenerate_faces": degenerate,
            "inside_unit_tile": inside,
        }

    high_collections = {collection.name for collection in high.users_collection}
    low_collections = {collection.name for collection in low.users_collection}
    separate_collections = bool(
        high_collection_name in high_collections
        and low_collection_name in low_collections
        and low_collection_name not in high_collections
        and high_collection_name not in low_collections
    )
    low_uv = uv_record(low)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from knowledge_engine.high_low_audit import HighLowEvidence, audit_production_high_low

    evidence = HighLowEvidence(
        high_object=high.name,
        low_object=low.name,
        separate_collections=separate_collections,
        independent_mesh_datablocks=high.data is not low.data,
        high_base_faces=len(high.data.polygons),
        low_base_faces=len(low.data.polygons),
        high_connected_components=connected_components(high),
        low_connected_components=connected_components(low),
        high_live_modifiers=tuple(f"{modifier.name}:{modifier.type}" for modifier in high.modifiers),
        low_live_modifiers=tuple(f"{modifier.name}:{modifier.type}" for modifier in low.modifiers),
        low_uv_layer=low_uv["layer"],
        low_uv_loop_count=low_uv["loop_count"],
        low_degenerate_uv_faces=low_uv["degenerate_faces"],
        low_uv_inside_unit_tile=low_uv["inside_unit_tile"],
        silhouette_iou_by_view=dict(silhouette_iou_by_view),
    )
    result = audit_production_high_low(
        evidence,
        max_low_to_high_face_ratio=max_low_to_high_face_ratio,
        minimum_silhouette_iou=minimum_silhouette_iou,
        minimum_view_count=minimum_view_count,
        require_live_modifiers=require_live_modifiers,
    )
    result["evidence"] = {
        "high_object": evidence.high_object,
        "low_object": evidence.low_object,
        "high_collections": sorted(high_collections),
        "low_collections": sorted(low_collections),
        "independent_mesh_datablocks": evidence.independent_mesh_datablocks,
        "high_base_faces": evidence.high_base_faces,
        "low_base_faces": evidence.low_base_faces,
        "high_connected_components": evidence.high_connected_components,
        "low_connected_components": evidence.low_connected_components,
        "high_live_modifiers": list(evidence.high_live_modifiers),
        "low_live_modifiers": list(evidence.low_live_modifiers),
        "low_uv": low_uv,
        "silhouette_iou_by_view": evidence.silhouette_iou_by_view,
    }
    return result


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


def declare_bevel_edge_intent(name, edge_ids, rationale):
    """Declare every edge expected to receive a physical bevel radius.

    This is deliberately separate from assigning the weights.  If declaration
    and assignment are the same operation, an omitted sharp edge silently
    disappears from both sets and a completeness audit can never detect it.
    Persistent IDs keep the authored design intent inspectable after unrelated
    topology edits.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    if obj.mode == "EDIT":
        raise ValueError("declare_bevel_edge_intent requires Object Mode")
    if not rationale or not str(rationale).strip():
        raise ValueError("rationale is required for an explicit bevel-edge declaration")
    persistent_ids.ensure_persistent_ids(name)
    id_map = persistent_ids.get_id_maps(name)["edges"]["id_to_index"]
    requested = sorted({int(agent_id) for agent_id in edge_ids})
    if not requested:
        raise ValueError("declare at least one intended bevel edge")
    missing = [agent_id for agent_id in requested if agent_id not in id_map]
    if missing:
        raise ValueError(f"unknown persistent edge IDs: {missing}")
    obj["hard_surface_intended_bevel_edge_ids"] = requested
    obj["hard_surface_bevel_intent_source"] = "EXPLICIT_DECLARATION"
    obj["hard_surface_bevel_intent_rationale"] = str(rationale).strip()
    return {
        "intended_bevel_edge_ids": requested,
        "intent_source": "EXPLICIT_DECLARATION",
        "rationale": str(rationale).strip(),
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
    # Preserve an explicit declaration when one exists.  Older callers that
    # assign without declaring remain supported, but their intent is marked as
    # inferred from the assignment and therefore cannot prove edge-selection
    # completeness independently.
    index_to_id = persistent_ids.get_id_maps(name)["edges"]["index_to_id"]
    weighted_ids = sorted(
        int(index_to_id[index]) for index, item in enumerate(attribute.data) if item.value > 0.999
    )
    if obj.get("hard_surface_bevel_intent_source") != "EXPLICIT_DECLARATION":
        obj["hard_surface_intended_bevel_edge_ids"] = weighted_ids
        obj["hard_surface_bevel_intent_source"] = "WEIGHT_ASSIGNMENT_INFERRED"
    obj.data.update()
    return {
        "attribute": "bevel_weight_edge",
        "weight": value,
        "assigned_edge_ids": assigned,
        "missing_edge_ids": missing,
        "clear_others": bool(clear_others),
        "intent_source": obj.get("hard_surface_bevel_intent_source"),
    }


def set_edge_crease_by_ids(name, edge_ids, value=1.0, clear_others=False):
    """Assign a semantic edge-crease set by persistent edge IDs -- a second,
    genuinely different sharp-edge mechanism from set_bevel_weight_by_ids,
    not a synonym for it.

    Crease protects a Subdivision Surface edge from the modifier's own
    smoothing WITHOUT adding any geometry (no chamfer, no extra vertices);
    Bevel adds a real physical radius as new geometry. They solve different
    problems: Bevel is for an edge that needs an actual visible chamfer
    width (the reference shows a machined/pressed radius); crease is for an
    edge that just needs to stay sharp/flat despite an already-active SubD
    modifier smoothing the rest of the object, at a fraction of the
    evaluated polygon cost.

    Found by studying a professional battle-axe .blend
    (docs/BLEND_FILE_STUDY_PROTOCOL.md): every sharp edge across all 5 of
    its objects uses full crease (value 1.0), zero Bevel modifiers anywhere.
    Reproduced and validated in runs/2026-08-13_blend-file-study/
    crease_experiment/: crease alone matches Bevel's sharp-edge read almost
    exactly (98 vs. 290 evaluated verts on the same test cage) -- BUT ONLY
    when the cage has adequate supporting topology. A bare single-quad face
    bounded only by creased edges "pillows" (bulges outward) under SubD even
    though its boundary edge itself stays sharp; the same face pre-
    subdivided into a grid stays flat. This is not a flaw specific to
    crease -- it's the same sparse-cage-under-SubD principle
    knowledge/foundation/operator_cards/topology_context_subd.md already
    documents, just visible here as pillowing instead of area-variation.
    Callers must ensure adequate face density before relying on crease
    alone for a flat-panel read.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    if obj.mode == "EDIT":
        raise ValueError("set_edge_crease_by_ids requires Object Mode; leave Edit Mode before changing mesh attributes")
    crease_value = float(value)
    if not 0.0 <= crease_value <= 1.0:
        raise ValueError(f"value must be in [0, 1], got {value}")
    persistent_ids.ensure_persistent_ids(name)
    id_map = persistent_ids.get_id_maps(name)["edges"]["id_to_index"]
    attribute = obj.data.attributes.get("crease_edge")
    if attribute is None:
        attribute = obj.data.attributes.new("crease_edge", "FLOAT", "EDGE")
    if attribute.domain != "EDGE":
        raise ValueError("crease_edge exists but is not an EDGE-domain attribute")
    if clear_others:
        for item in attribute.data:
            item.value = 0.0
    assigned, missing = [], []
    for agent_id in edge_ids:
        edge_index = id_map.get(int(agent_id))
        if edge_index is None:
            missing.append(int(agent_id))
            continue
        attribute.data[edge_index].value = crease_value
        assigned.append(int(agent_id))
    index_to_id = persistent_ids.get_id_maps(name)["edges"]["index_to_id"]
    # A partial crease is still deliberate SubD edge intent. The previous
    # >0.999 threshold silently discarded common production values such as
    # 0.82 from the intent record even though Blender visibly used them.
    # Record every non-zero crease and retain the requested value separately.
    obj["hard_surface_intended_crease_edge_ids"] = sorted(
        int(index_to_id[index]) for index, item in enumerate(attribute.data) if item.value > 1e-6
    )
    obj["hard_surface_last_crease_value"] = crease_value
    obj.data.update()
    return {
        "attribute": "crease_edge",
        "value": crease_value,
        "assigned_edge_ids": assigned,
        "missing_edge_ids": missing,
        "clear_others": bool(clear_others),
    }


def mark_no_sharp_edges_needed(name, reason):
    """Explicitly record that this mesh has no edges requiring Bevel or
    crease at all -- a fourth, genuinely different sanctioned state, not a
    weaker version of the other three.

    Found necessary building a watering can's wire handle: a plain
    round-profile curve-to-mesh tube has nothing that should ever read as
    sharp, the same negative case `bat.blend` confirmed during the
    professional-file study (one object, 354 verts, Smooth by Angle only, no
    SubD/Bevel/crease at all). Without this, hard_surface_shading_audit's
    three existing paths (WEIGHT-Bevel, ANGLE/VGROUP-Bevel, crease) all read
    "no intent recorded" as a failure, which is correct for a part that
    forgot to consider hard edges but wrong for a part that has none to
    consider -- those are different situations and must not share one
    unrecorded state. This requires an explicit call with a stated reason so
    it stays auditable and distinguishable from silence, matching the other
    three paths' own discipline.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        raise ValueError(f"'{name}' is not a mesh object")
    if not reason or not str(reason).strip():
        raise ValueError("reason is required -- this must be a deliberate claim, not a silent default")
    obj["hard_surface_no_sharp_edges_intended"] = True
    obj["hard_surface_no_sharp_edges_reason"] = str(reason)
    return {"name": name, "no_sharp_edges_intended": True, "reason": str(reason)}


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
            if item.value > 1e-6 and index in id_maps["index_to_id"]
        )
    intended_ids = sorted(int(item) for item in obj.get("hard_surface_intended_bevel_edge_ids", []))
    intent_source = obj.get("hard_surface_bevel_intent_source", "LEGACY_UNSPECIFIED")
    missing_weight_ids = sorted(set(intended_ids) - set(weighted_ids))
    unexpected_weight_ids = sorted(set(weighted_ids) - set(intended_ids))
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

    # Third, structurally different sanctioned path: deliberate edge crease (see
    # set_edge_crease_by_ids). Found by studying a professional battle-axe
    # .blend (docs/BLEND_FILE_STUDY_PROTOCOL.md) -- every sharp edge across
    # all 5 of its objects uses crease, zero Bevel modifiers anywhere.
    # Reproduced and validated in runs/2026-08-13_blend-file-study/
    # crease_experiment/. Crease has no Bevel-vs-SubD ordering dependency
    # (the SubD modifier reads crease values directly), so a crease-only
    # object with no Bevel modifier at all must not be penalized by the
    # bevel_before_subd check below.
    crease_attr = obj.data.attributes.get("crease_edge")
    creased_ids = []
    if crease_attr is not None and crease_attr.domain == "EDGE":
        creased_ids = sorted(
            int(id_maps["index_to_id"][index]) for index, item in enumerate(crease_attr.data)
            # Partial creases are a valid, recorded design choice.  Treating
            # only 1.0 as a crease made the audit contradict
            # set_edge_crease_by_ids(), which explicitly supports [0, 1].
            if item.value > 1e-6 and index in id_maps["index_to_id"]
        )
    intended_crease_ids = sorted(int(item) for item in obj.get("hard_surface_intended_crease_edge_ids", []))
    crease_path_ok = bool(intended_crease_ids) and creased_ids == intended_crease_ids

    # Fourth sanctioned path: an explicit, reasoned claim that this mesh has
    # no edges that should ever be sharp (see mark_no_sharp_edges_needed).
    # Only a mesh with zero Bevel modifiers and zero non-zero crease values
    # can honestly make this claim -- otherwise geometry already contradicts
    # the recorded intent.
    no_sharp_edges_claimed = bool(obj.get("hard_surface_no_sharp_edges_intended"))
    no_sharp_edges_path_ok = (
        no_sharp_edges_claimed
        and not bevel_modifiers
        and not creased_ids
        and not weighted_ids
    )

    checks = {
        "semantic_intent_recorded": bool(intended_ids),
        "semantic_intent_explicitly_declared": intent_source == "EXPLICIT_DECLARATION",
        "semantic_weights_match_intent": bool(intended_ids) and weighted_ids == intended_ids,
        "weight_limited_bevel_present": bool(weighted_bevel_indices),
        "angle_or_vgroup_intent_recorded": scoping_intent_recorded,
        "angle_or_vgroup_intent_matches_actual": scoping_intent_matches_actual,
        "crease_intent_recorded": bool(intended_crease_ids),
        "crease_matches_intent": crease_path_ok,
        "no_sharp_edges_claimed": no_sharp_edges_claimed,
        "no_sharp_edges_claim_matches_geometry": no_sharp_edges_path_ok,
        "bevel_before_subd": (
            not subd_indices
            or (bool(effective_bevel_indices) and min(effective_bevel_indices) < min(subd_indices))
            or (crease_path_ok and not bevel_modifiers)
            or no_sharp_edges_path_ok
        ),
        "smooth_by_angle_recorded": obj.get("shading_policy") == "SMOOTH_BY_ANGLE",
        "uniform_object_scale": uniform_scale,
        "not_unannotated_blanket_smooth": not (blanket_smooth and obj.get("shading_policy") != "SMOOTH_BY_ANGLE"),
    }
    weight_path_ok = checks["semantic_intent_recorded"] and checks["semantic_weights_match_intent"] and checks["weight_limited_bevel_present"]
    passed = (
        (weight_path_ok or angle_or_vgroup_path_ok or crease_path_ok or no_sharp_edges_path_ok)
        and checks["bevel_before_subd"]
        and checks["smooth_by_angle_recorded"]
        and checks["uniform_object_scale"]
        and checks["not_unannotated_blanket_smooth"]
    )
    warnings = []
    if intended_ids and intent_source != "EXPLICIT_DECLARATION":
        warnings.append(
            "Semantic bevel intent was inferred from the weight assignment; this verifies the saved "
            "map but cannot independently prove that every edge which should be sharp was selected."
        )
    if missing_weight_ids:
        warnings.append(f"Declared bevel edges missing full weight: {missing_weight_ids}")
    if unexpected_weight_ids:
        warnings.append(f"Weighted edges absent from the declared bevel intent: {unexpected_weight_ids}")
    if no_sharp_edges_claimed and not no_sharp_edges_path_ok:
        warnings.append(
            "hard_surface_no_sharp_edges_intended is set but the mesh has a Bevel modifier, "
            "weighted edges, or creased edges -- the claim contradicts the actual geometry."
        )
    if not weight_path_ok and not angle_or_vgroup_path_ok and not crease_path_ok and not no_sharp_edges_path_ok:
        if intended_ids and intent_source == "EXPLICIT_DECLARATION":
            warnings.append(
                "Explicit semantic bevel intent is recorded, but the saved weight map does not "
                "cover it exactly; repair the missing or unexpected edge assignments."
            )
        elif non_weight_scoped_indices and not weighted_bevel_indices:
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
        "bevel_intent_source": intent_source,
        "missing_weight_edge_ids": missing_weight_ids,
        "unexpected_weight_edge_ids": unexpected_weight_ids,
        "creased_edge_ids": creased_ids,
        "intended_crease_edge_ids": intended_crease_ids,
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
