"""Exercise every newly registered typed mesh operation on isolated fixtures."""

from __future__ import annotations

import json
import math
import sys
import traceback
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "blender_ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

import decision_state
import mesh_ops
import modeler_server
import persistent_ids
from decision_transaction import DecisionTransaction


def stats(obj):
    return {"verts": len(obj.data.vertices), "edges": len(obj.data.edges), "faces": len(obj.data.polygons)}


def cube(name, x):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0, 0))
    obj = bpy.context.object
    obj.name = name
    return obj


def select(obj, vert_test=None, edge_test=None, face_test=None):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    for seq in (bm.verts, bm.edges, bm.faces):
        for item in seq: item.select = False
    if vert_test:
        for item in bm.verts:
            item.select = bool(vert_test(item))
    if edge_test:
        for item in bm.edges:
            item.select = bool(edge_test(item))
    if face_test:
        for item in bm.faces:
            item.select = bool(face_test(item))
    bm.to_mesh(obj.data); bm.free(); obj.data.update()


def circle_object(name, x, z_values=(0.0,), radius=0.6, segments=8, faces=False):
    verts=[]; edges=[]; polygons=[]
    for ring,z in enumerate(z_values):
        for i in range(segments):
            angle=2*math.pi*i/segments
            verts.append((radius*math.cos(angle),radius*math.sin(angle),z))
            edges.append((ring*segments+i,ring*segments+(i+1)%segments))
    if faces and len(z_values)==2:
        for i in range(segments):
            n=(i+1)%segments; polygons.append((i,n,segments+n,segments+i))
    mesh=bpy.data.meshes.new(name+"Mesh"); mesh.from_pydata(verts,edges,polygons); mesh.update()
    obj=bpy.data.objects.new(name,mesh); bpy.context.scene.collection.objects.link(obj); obj.location.x=x
    return obj


def run_case(records, case_id, fn):
    try:
        detail=fn(); records.append({"case_id":case_id,"pass":True,"detail":detail})
    except Exception as exc:
        records.append({"case_id":case_id,"pass":False,"error":str(exc),"traceback":traceback.format_exc()})


def main():
    out=ROOT/"runs"/"2026-08-10_expanded-typed-ops"; out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    records=[]

    def rotation():
        obj=cube("Typed_Rotate",-12); select(obj,vert_test=lambda v:v.co.z>0)
        before=[tuple(v.co) for v in obj.data.vertices]; count=mesh_ops.rotate_selection(obj.name,math.pi/4,(0,0,1)); after=[tuple(v.co) for v in obj.data.vertices]
        assert count==4 and before!=after; return {"moved":count,"stats":stats(obj)}
    run_case(records,"rotate_selection",rotation)

    def bevel():
        obj=cube("Typed_Bevel",-10); select(obj,edge_test=lambda e:True); before=stats(obj); result=mesh_ops.bevel_selection(obj.name,0.1,2); after=stats(obj)
        assert after["verts"]>before["verts"]; return {"result":result,"before":before,"after":after}
    run_case(records,"bevel_selection",bevel)

    def delete():
        obj=cube("Typed_Delete",-8); select(obj,face_test=lambda f:f.normal.z>0.9); result=mesh_ops.delete_selection(obj.name)
        assert stats(obj)["faces"]==5; return {"result":result,"stats":stats(obj)}
    run_case(records,"delete_selection",delete)

    def dissolve():
        obj=cube("Typed_Dissolve",-6); select(obj,edge_test=lambda e:abs(e.verts[0].co.z-1)<.01 and abs(e.verts[1].co.z-1)<.01); result=mesh_ops.dissolve_selection(obj.name)
        assert result["dissolved"]>0; return {"result":result,"stats":stats(obj)}
    run_case(records,"dissolve_selection",dissolve)

    def merge():
        obj=circle_object("Typed_Merge",-4,(0,),segments=4); select(obj,vert_test=lambda v:v.co.x>0); before=stats(obj); result=mesh_ops.merge_selection(obj.name); after=stats(obj)
        assert after["verts"]==before["verts"]-1; return {"result":result,"before":before,"after":after}
    run_case(records,"merge_selection",merge)

    def fill():
        obj=circle_object("Typed_Fill",-2,(0,),segments=8); select(obj,edge_test=lambda e:True,vert_test=lambda v:True); result=mesh_ops.fill_selection(obj.name)
        assert stats(obj)["faces"]>=1; return {"result":result,"stats":stats(obj)}
    run_case(records,"fill_selection",fill)

    def bridge():
        obj=circle_object("Typed_Bridge",0,(-0.5,0.5),segments=8); select(obj,edge_test=lambda e:True,vert_test=lambda v:True); result=mesh_ops.bridge_selection(obj.name)
        assert stats(obj)["faces"]==8; return {"result":result,"stats":stats(obj)}
    run_case(records,"bridge_selection",bridge)

    def spin():
        obj=circle_object("Typed_Spin",2,(0,),radius=.25,segments=8); obj.data.transform(__import__('mathutils').Matrix.Translation((.8,0,0))); select(obj,edge_test=lambda e:True,vert_test=lambda v:True)
        before=stats(obj); result=mesh_ops.spin_selection(obj.name,2*math.pi,12,(0,0,0),(0,0,1)); after=stats(obj)
        assert after["faces"]>before["faces"]; return {"result":result,"before":before,"after":after}
    run_case(records,"spin_selection",spin)

    def loop_cut():
        obj=cube("Typed_LoopCut",4); select(obj,edge_test=lambda e:abs(e.verts[0].co.z-e.verts[1].co.z)>1.9); before=stats(obj); result=mesh_ops.loop_cut_selection(obj.name,1); after=stats(obj)
        assert after["verts"]>before["verts"]; return {"result":result,"before":before,"after":after}
    run_case(records,"loop_cut_selection",loop_cut)

    def bisect():
        obj=cube("Typed_Bisect",6); select(obj,vert_test=lambda v:True,edge_test=lambda e:True,face_test=lambda f:True); before=stats(obj); result=mesh_ops.bisect_selection(obj.name,(0,0,0),(0,0,1)); after=stats(obj)
        assert after["verts"]>before["verts"]; return {"result":result,"before":before,"after":after}
    run_case(records,"bisect_selection",bisect)

    def symmetrize():
        obj=cube("Typed_Symmetrize",8)
        select(obj,vert_test=lambda v:v.co.x>0); mesh_ops.delete_selection(obj.name)
        select(obj,vert_test=lambda v:True,edge_test=lambda e:True,face_test=lambda f:True)
        before=stats(obj); result=mesh_ops.symmetrize_selection(obj.name,"-X_TO_+X"); after=stats(obj)
        if not (result["result_geometry"]>0 and after["verts"]>before["verts"]):
            raise AssertionError(json.dumps({"result":result,"before":before,"after":after}))
        return {"result":result,"before":before,"after":after}
    run_case(records,"symmetrize_selection",symmetrize)

    def split():
        obj=cube("Typed_Split",10); select(obj,face_test=lambda f:f.normal.z>0.9); before=stats(obj); result=mesh_ops.split_selection(obj.name); after=stats(obj)
        assert after["verts"]>before["verts"]; return {"result":result,"before":before,"after":after}
    run_case(records,"split_selection",split)

    def separate_and_rollback():
        obj=cube("Typed_Separate",12); select(obj,face_test=lambda f:f.normal.z>0.9); before=stats(obj); rev=decision_state.current_revision()
        with DecisionTransaction(rev,"separate_selection",obj.name) as tx:
            result=tx.perform(mesh_ops.separate_selection,obj.name,"Typed_SeparatedPart"); verified=tx.verify(); rejected=tx.reject("rollback coverage")
        assert bpy.data.objects.get("Typed_SeparatedPart") is None and stats(obj)==before
        return {"operation_result":result,"verified":verified,"rejected":rejected,"restored":stats(obj)}
    run_case(records,"separate_selection_transaction_rollback",separate_and_rollback)

    def transaction_identity():
        obj=cube("Typed_TransactionIdentity",14); persistent_ids.ensure_persistent_ids(obj.name)
        before_maps=persistent_ids.get_id_maps(obj.name); original_vert_ids=set(before_maps["verts"]["id_to_index"])
        select(obj,edge_test=lambda e:abs(e.verts[0].co.z-e.verts[1].co.z)>1.9)
        rev=decision_state.current_revision()
        with DecisionTransaction(rev,"loop_cut_selection",obj.name) as tx:
            operation=tx.perform(mesh_ops.loop_cut_selection,obj.name,1); verified=tx.verify(); new_revision=tx.commit()
        after_maps=persistent_ids.get_id_maps(obj.name)
        assert new_revision==rev+1 and original_vert_ids.issubset(set(after_maps["verts"]["id_to_index"])) and verified["id_delta"]["verts"]["added"]
        return {"operation":operation,"verification":verified,"revision":[rev,new_revision]}
    run_case(records,"transaction_identity_reconciliation",transaction_identity)

    def registry():
        expected={"rotate_selection","bevel_selection","delete_selection","dissolve_selection","merge_selection","fill_selection","bridge_selection","spin_selection","loop_cut_selection","bisect_selection","symmetrize_selection","split_selection","separate_selection"}
        missing=sorted(expected-set(modeler_server._OPS))
        assert not missing and modeler_server.PROTOCOL_VERSION=="0.2"
        return {"protocol":modeler_server.PROTOCOL_VERSION,"registered":sorted(expected),"missing":missing}
    run_case(records,"modeler_registry_protocol",registry)

    report={"lab":"expanded_typed_modeling_operations","records":records,"passed":sum(r["pass"] for r in records),"total":len(records)}
    report["pass"]=report["passed"]==report["total"]
    (out/"expanded_typed_ops_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"expanded_typed_ops_lab.blend"))
    print("EXPANDED_TYPED_OPS_RESULT:"+json.dumps(report))
    if not report["pass"]: raise SystemExit(2)


if __name__=="__main__": main()
