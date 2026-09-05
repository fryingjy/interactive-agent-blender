"""Controlled replay of the inspected inset/extrude and radial repair drill.

Not a target builder, reference benchmark or autonomous planning test.
"""
import json
import os
from pathlib import Path
import subprocess

import pytest


@pytest.mark.skipif(not os.environ.get('BLENDER_TEST_EXECUTABLE'), reason='requires real Blender')
def test_connected_shell_transfer_preserves_cavity_and_repairs_radial_form(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    executable = os.environ['BLENDER_TEST_EXECUTABLE']
    code = f"""
import sys,bpy
sys.path.insert(0,{str(repo)!r})
from blender_ops.modeler_server import ModelerServer
bpy.ops.wm.read_factory_settings(use_empty=True)
server=ModelerServer(enforce_reference_authorization=False)
def mutate(name,operation,params):
    d=server.cmd_begin_decision(name,'CONSTRUCTION')['decision_id']
    server.cmd_perform_decision(d,operation,params)
    server.cmd_verify_decision(d)
    server.cmd_commit_decision(d)
for name,primitive,kwargs in [('Box','cube',{{'size':2}}),('Radial','cylinder',{{'vertices':16,'radius':1,'depth':.6}})]:
    server.cmd_create_primitive(name,primitive,**kwargs)
    g=server.cmd_get_mesh_geometry(name)
    if primitive=='cube':
        server.cmd_select_by_ids(name,vertex_ids=[v['agent_id'] for v in g['vertices']])
        mutate(name,'scale_selection',{{'factor':[1,.6,.3],'center':[0,0,0]}})
    g=server.cmd_get_mesh_geometry(name)
    top=[f['agent_id'] for f in g['faces'] if f['normal'][2]>.9]
    assert len(top)==1
    server.cmd_select_by_ids(name,face_ids=top)
    mutate(name,'inset_selection',{{'thickness':.08}})
    mutate(name,'extrude_selection',{{'offset':-.52}})
    mutate(name,'add_modifier',{{'modifier_type':'BEVEL','modifier_name':'EdgeRadius'}})
    for parameter,value in {{'width':.015,'segments':3,'limit_method':'ANGLE','angle_limit':.5235987756}}.items():
        mutate(name,'set_modifier_parameter',{{'modifier_name':'EdgeRadius','parameter':parameter,'value':value}})
    if name=='Radial':
        mutate(name,'set_smooth_by_angle',{{'angle':.5235987756,'keep_sharp_edges':False}})
server.cmd_save_file({str(tmp_path / 'before.blend')!r})
mutate('Radial','add_modifier',{{'modifier_type':'SUBSURF','modifier_name':'Curvature'}})
for parameter in ['levels','render_levels']:
    mutate('Radial','set_modifier_parameter',{{'modifier_name':'Curvature','parameter':parameter,'value':2}})
state=server.cmd_get_evaluated_state('Radial')
width=state['bounding_box']['evaluated_dimensions'][0]
assert 1.94<width<1.96
g=server.cmd_get_mesh_geometry('Radial')
server.cmd_select_by_ids('Radial',vertex_ids=[v['agent_id'] for v in g['vertices']])
mutate('Radial','scale_selection',{{'factor':[2/width,2/width,1],'center':[0,0,0]}})
mutate('Radial','package_high_low_variants',{{'low_object_name':'Radial_Low','low_subd_levels':0}})
server.cmd_save_file({str(tmp_path / 'after.blend')!r})
"""
    result = subprocess.run([executable, '-b', '--factory-startup', '--python-exit-code', '1',
                             '--python-expr', code], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr

    def inspect(file, name, label):
        output = tmp_path / f'{label}.json'
        result = subprocess.run([executable, '-b', '--factory-startup', '--python-exit-code', '1',
                                 '--python', str(repo / 'tests/fixtures/shell_construction/inspect_saved.py'),
                                 '--', str(tmp_path / file), name, str(output)],
                                capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(output.read_text())

    box = inspect('before.blend', 'Box', 'box')
    before = inspect('before.blend', 'Radial', 'before')
    after = inspect('after.blend', 'Radial', 'after')
    low = inspect('after.blend', 'Radial_Low', 'low')
    for record in (box, before, after):
        assert record['base']['connected_components'] == 1
        assert record['evaluated']['non_manifold_edges'] == 0
        assert record['center_floor_thickness'] == pytest.approx(.08, abs=.001)
        assert record['center_cavity_depth'] == pytest.approx(.52, abs=.001)
    assert box['base'] == {'vertices': 16, 'faces': 14, 'ngons': 0, 'connected_components': 1}
    assert after['base']['vertices'] == before['base']['vertices'] == 64
    assert before['radial_midheight']['samples'] == after['radial_midheight']['samples'] == 360
    assert after['radial_midheight']['peak_to_peak'] < before['radial_midheight']['peak_to_peak'] * .1
    assert after['evaluated']['dimensions'][0] == pytest.approx(2, abs=.001)
    assert after['collections'] == ['HIGH_POLY']
    assert low['collections'] == ['LOW_POLY']
    assert low['base'] == after['base']
    assert low['evaluated']['faces'] < after['evaluated']['faces']
    assert [m['type'] for m in low['modifiers']] == ['BEVEL', 'SUBSURF']
    assert [m['type'] for m in after['modifiers']] == ['BEVEL', 'SUBSURF']
