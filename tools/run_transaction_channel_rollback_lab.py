"""Stress transaction rollback across mesh data, modifiers, semantic metadata, and selection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]; OPS=ROOT/"blender_ops"
if str(OPS) not in sys.path: sys.path.insert(0,str(OPS))

import decision_state
import persistent_ids
import semantic_regions
from decision_transaction import DecisionTransaction


def snapshot(obj):
    selected_faces=[polygon.index for polygon in obj.data.polygons if polygon.select]
    return {
        "vertices":[list(vertex.co) for vertex in obj.data.vertices],
        "uv_layers":[layer.name for layer in obj.data.uv_layers],
        "materials":[material.name if material else None for material in obj.data.materials],
        "modifiers":[{"name":mod.name,"type":mod.type,"width":getattr(mod,"width",None),"segments":getattr(mod,"segments",None)} for mod in obj.modifiers],
        "custom":{key:obj[key] for key in obj.keys()},
        "selected_faces":selected_faces,
        "object_selected":obj.select_get(),
        "location":list(obj.location),
    }


def mutate_every_channel(name):
    obj=bpy.data.objects[name]
    obj.data.vertices[0].co.x += 0.75
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    obj.data.materials.clear()
    obj.modifiers[0].width=0.45
    extra=obj.modifiers.new("Temporary Solidify","SOLIDIFY"); extra.thickness=0.2
    obj["agent_semantic_regions"]="{\"corrupted\": true}"
    obj["temporary_property"]="must disappear"
    for polygon in obj.data.polygons: polygon.select=False
    obj.select_set(False)
    obj.location=(2,3,4)
    return {"mutated":True}


def main():
    out=ROOT/"runs"/"2026-08-10_transaction-rollback"; out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add(); obj=bpy.context.object; obj.name="RollbackChannels"
    persistent_ids.ensure_persistent_ids(obj.name)
    maps=persistent_ids.get_id_maps(obj.name); face_id=next(iter(maps["faces"]["id_to_index"]))
    semantic_regions.create_region(obj.name,"panel","flat_panel",face_ids=[face_id])
    obj.data.uv_layers.new(name="ProductionUV")
    material=bpy.data.materials.new("RollbackMaterial"); obj.data.materials.append(material)
    bevel=obj.modifiers.new("Production Bevel","BEVEL"); bevel.width=.12; bevel.segments=3
    obj.data.polygons[0].select=True; obj.select_set(True); bpy.context.view_layer.objects.active=obj
    before=snapshot(obj); rev=decision_state.current_revision()
    with DecisionTransaction(rev,"rollback_channel_stress",obj.name) as tx:
        tx.perform(mutate_every_channel,obj.name); during=snapshot(obj); tx.verify(); rejected=tx.reject("channel restoration test")
    after=snapshot(obj)
    assertions={
        "mutation_changed_state":during!=before,
        "mesh_vertices_restored":after["vertices"]==before["vertices"],
        "uv_and_materials_restored":after["uv_layers"]==before["uv_layers"] and after["materials"]==before["materials"],
        "modifier_stack_restored":after["modifiers"]==before["modifiers"],
        "semantic_and_custom_metadata_restored":after["custom"]==before["custom"] and "temporary_property" not in after["custom"],
        "selection_restored":after["selected_faces"]==before["selected_faces"] and after["object_selected"]==before["object_selected"],
        "transform_restored":after["location"]==before["location"],
        "revision_unchanged":decision_state.current_revision()==rev,
    }
    report={"lab":"transaction_multichannel_rollback","before":before,"during":during,"after":after,"rejected":rejected,"assertions":assertions,"pass":all(assertions.values())}
    (out/"transaction_rollback_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"transaction_rollback_lab.blend"))
    print("TRANSACTION_ROLLBACK_RESULT:"+json.dumps(report))
    if not report["pass"]: raise SystemExit(2)


if __name__=="__main__": main()
