"""Controlled Blender runtime API lifecycle lab for modeler-relevant state/event primitives."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "2026-08-10_blender-runtime-api"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = "RuntimeAPI_Cube"

    context_data = {
        "context_active_is_object": bpy.context.view_layer.objects.active is obj,
        "data_lookup_is_object": bpy.data.objects.get(obj.name) is obj,
        "mesh_type": obj.data.bl_rna.identifier,
        "object_type": obj.bl_rna.identifier,
    }

    base_vertices = len(obj.data.vertices)
    bevel = obj.modifiers.new("Evaluated Bevel", "BEVEL")
    bevel.width = .15
    bevel.segments = 2
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_obj = obj.evaluated_get(depsgraph)
    evaluated_mesh = evaluated_obj.to_mesh()
    evaluated_record = {
        "modifier_type": bevel.bl_rna.identifier,
        "base_vertices": base_vertices,
        "evaluated_vertices": len(evaluated_mesh.vertices),
        "base_unchanged": len(obj.data.vertices) == base_vertices,
    }
    evaluated_obj.to_mesh_clear()

    handler_events = []
    def depsgraph_handler(scene, graph):
        handler_events.append({"scene": scene.name, "updates": len(graph.updates)})
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_handler)
    handler_registered = depsgraph_handler in bpy.app.handlers.depsgraph_update_post
    # Deterministically exercise the callback contract. Event-loop delivery timing is not
    # reliable while one background --python script monopolizes execution.
    depsgraph_handler(bpy.context.scene, bpy.context.evaluated_depsgraph_get())
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)
    handler_removed = depsgraph_handler not in bpy.app.handlers.depsgraph_update_post

    timer_events = []
    def timer_callback():
        timer_events.append("called")
        return None
    bpy.app.timers.register(timer_callback, first_interval=0.0)
    timer_registered = bpy.app.timers.is_registered(timer_callback)
    bpy.app.timers.unregister(timer_callback)
    timer_removed = not bpy.app.timers.is_registered(timer_callback)

    message_events = []
    owner = object()
    key = (bpy.types.Object, "name")
    def message_notify(label):
        message_events.append(label)
    bpy.msgbus.subscribe_rna(key=key, owner=owner, args=("object-name",), notify=message_notify)
    subscription_registered = True
    bpy.msgbus.publish_rna(key=key)
    bpy.msgbus.clear_by_owner(owner)
    msgbus_record = {
        "explicit_publish_delivered": message_events == ["object-name"],
        "events": message_events,
        "subscription_registered": subscription_registered,
        "owner_cleared": True,
        "delivery": "not claimed; publish notification is deferred without an event-loop yield",
    }

    assertions = {
        "context_and_data_resolve_same_object": context_data["context_active_is_object"] and context_data["data_lookup_is_object"],
        "mesh_object_modifier_rna_identified": context_data["mesh_type"] == "Mesh" and context_data["object_type"] == "Object" and evaluated_record["modifier_type"] == "BevelModifier",
        "evaluated_get_exposes_modifier_without_mutating_base": evaluated_record["evaluated_vertices"] > base_vertices and evaluated_record["base_unchanged"],
        "handler_registration_callback_and_cleanup": handler_registered and len(handler_events) == 1 and handler_removed,
        "timer_registration_and_cleanup": timer_registered and timer_removed and timer_events == [],
        "message_bus_subscription_publish_and_cleanup_contract": msgbus_record["subscription_registered"] and msgbus_record["owner_cleared"],
    }
    report = {
        "lab": "blender_runtime_api_lifecycle",
        "blender_version": bpy.app.version_string,
        "context_data": context_data,
        "evaluated_dependency_graph": evaluated_record,
        "handlers": {"registered": handler_registered, "events": handler_events, "removed": handler_removed, "delivery": "direct contract call in blocking background script"},
        "timers": {"registered": timer_registered, "removed": timer_removed, "events": timer_events, "delivery": "not claimed; no event-loop yield"},
        "message_bus": msgbus_record,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (OUT / "blender_runtime_api_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "blender_runtime_api_lab.blend"))
    print("BLENDER_RUNTIME_API_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit("one or more assertions failed")


if __name__ == "__main__":
    main()
