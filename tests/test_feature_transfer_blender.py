"""Opt-in real Blender regression: BLENDER_TEST_EXECUTABLE=/path/to/blender.

The concave shoulder stays manifold while SubD overlaps its column. This test
must observe that failure before verifying an explicit coplanar-constraint repair.
"""
import json
import os
from pathlib import Path
import subprocess

import pytest

from modeling_core.construction import propose_feature_edges


@pytest.mark.skipif(not os.environ.get("BLENDER_TEST_EXECUTABLE"), reason="requires real Blender")
def test_coplanar_shoulder_constraints_repair_evaluated_overlap(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    executable = os.environ["BLENDER_TEST_EXECUTABLE"]
    setup = f"""
import sys,json,bpy
from pathlib import Path
sys.path.insert(0,{str(repo)!r})
from blender_ops.modeler_server import ModelerServer
import persistent_ids,state_probe
root=Path({str(tmp_path)!r})
server=ModelerServer(enforce_reference_authorization=False)
def mutate(operation,params):
    decision=server.cmd_begin_decision('Housing','SURFACE_CONTROL')['decision_id']
    server.cmd_perform_decision(decision,operation,params)
    server.cmd_verify_decision(decision)
    server.cmd_commit_decision(decision)
def overlap_count():
    bpy.context.view_layer.update()
    obj=bpy.data.objects['Housing'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=obj.to_mesh()
    count=sum(abs(v.co.z-.4)<1e-5 and abs(v.co.x)<.2999 and abs(v.co.y)<.1999 for v in mesh.vertices)
    obj.to_mesh_clear()
    return count
"""
    create = """
bpy.ops.wm.read_factory_settings(use_empty=True)
sections=[(0,.5,.3),(.2,.5,.3),(.4,.5,.3),(.4,.3,.2),(.6,.3,.2),(.9,.3,.2)]
vertices=[(x,y,z) for z,w,d in sections for x,y in [(w,d),(-w,d),(-w,-d),(w,-d)]]
faces=[(4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j) for i in range(5) for j in range(4)]
faces += [(3,2,1,0),(20,21,22,23)]
server._dispatch('create_authored_quad_mesh',{'name':'Housing','vertices':vertices,'faces':faces})
ids=list(persistent_ids.get_id_maps('Housing')['verts']['id_to_index'])
probe=state_probe.inspect_region('Housing',ids,rings=0)
(root/'probe.json').write_text(json.dumps(probe))
mutate('add_modifier',{'modifier_type':'SUBSURF','modifier_name':'LiveSubdivision'})
mutate('set_modifier_parameter',{'modifier_name':'LiveSubdivision','parameter':'levels','value':2})
bpy.ops.wm.save_as_mainfile(filepath=str(root/'base.blend'))
"""

    def run(code):
        result = subprocess.run([executable, "--background", "--factory-startup", "--python-exit-code", "1", "--python-expr", setup + code], capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stdout + result.stderr

    run(create)
    edges = json.loads((tmp_path / "probe.json").read_text())["edges"]
    initial = propose_feature_edges(edges, angle_degrees=25, rationale="Preserve manufactured corners")
    # Fixture-local localization, not a production rule based on vertex indices.
    supports = [e["agent_id"] for e in edges if min(e["vertex_indices"]) in range(8, 12) and max(e["vertex_indices"]) in range(12, 16)]
    repaired = propose_feature_edges(edges, angle_degrees=25, rationale="Prevent observed shoulder overlap", preserve_ids=supports)
    assert len(supports) == 4
    run(f"""
bpy.ops.wm.open_mainfile(filepath=str(root/'base.blend'))
mutate('set_edge_crease_by_ids',{{'edge_ids':{initial['candidate_edge_ids']!r},'value':1.0,'clear_others':True}})
before=overlap_count()
mutate('set_edge_crease_by_ids',{{'edge_ids':{repaired['candidate_edge_ids']!r},'value':1.0,'clear_others':True}})
after=overlap_count()
(root/'result.json').write_text(json.dumps({{'before':before,'after':after,'live_modifiers':len(bpy.data.objects['Housing'].modifiers)}}))
""")
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["before"] == 8
    assert result["after"] == 0
    assert result["live_modifiers"] == 1
