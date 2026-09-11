"""Native Blender integration tests; fixtures are not reference-modeling evidence."""
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modeler.runtime import edit, inspect, set_subdivision
from modeler.render import render


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.mesh.primitive_cube_add()
        self.name = bpy.context.object.name

    def request(self, action, **kwargs):
        return dict(object=self.name, action=action,
                    expected_fingerprint=inspect(self.name)['fingerprint'], **kwargs)

    def test_extrude_connected_and_reload(self):
        initial = inspect(self.name)
        face = next(p.index for p in bpy.context.object.data.polygons if p.normal.z > .9)
        result = edit(self.request('extrude_face', face=face, delta=[0, 0, 1]))
        self.assertEqual(result['after']['health'],
                         dict(components=1, nonmanifold_edges=0, degenerate_faces=0))
        self.assertEqual(len(result['after']['geometry']['vertices']), 12)
        self.assertNotEqual(initial['fingerprint'], result['after']['fingerprint'])
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'checkpoint.blend')
            bpy.ops.wm.save_as_mainfile(filepath=path)
            bpy.ops.wm.open_mainfile(filepath=path, use_scripts=False)
            self.assertEqual(inspect(self.name)['fingerprint'], result['after']['fingerprint'])

    def test_failure_rolls_back_mesh(self):
        initial = inspect(self.name)
        # Collapse the cube's top face onto the bottom, making side faces degenerate.
        top = [v.index for v in bpy.context.object.data.vertices if v.co.z > 0]
        with self.assertRaises(ValueError):
            edit(self.request('move_vertices', vertices=top, delta=[0, 0, -2]))
        self.assertEqual(inspect(self.name)['fingerprint'], initial['fingerprint'])
        self.assertEqual(len(bpy.data.meshes), 1)

    def test_stale_rejected(self):
        request = self.request('move_vertices', vertices=[0], delta=[0, 0, .2])
        bpy.context.object.location.x = 1
        with self.assertRaises(ValueError):
            edit(request)

    def test_live_subdivision_and_crease(self):
        state=inspect(self.name)
        edit(self.request('set_edge_crease', edges=list(range(len(state['geometry']['edges']))), weight=.6))
        state=inspect(self.name)
        self.assertIn('crease_edge', state['geometry']['attributes'])
        result=set_subdivision(self.request('set_subdivision', levels=2))['after']
        self.assertEqual(len(result['geometry']['vertices']),8)
        self.assertGreater(result['evaluated_counts']['vertices'],8)
        self.assertEqual(len(bpy.context.object.modifiers),1)
        edit(self.request('set_vertex_crease', vertices=[0], weight=.9))
        self.assertIn('crease_vert', inspect(self.name)['geometry']['attributes'])
        set_subdivision(self.request('set_subdivision', levels=1))
        self.assertEqual(len(bpy.context.object.modifiers),1)

    def test_region_inset_keeps_quads_and_closure(self):
        state = inspect(self.name)
        edit(self.request('subdivide_edges', edges=list(range(len(state['geometry']['edges']))), cuts=2))
        faces=[p.index for p in bpy.context.object.data.polygons if p.normal.y < -.9]
        result=edit(self.request('inset_region', faces=faces, thickness=.1, depth=-.05))['after']
        self.assertTrue(all(len(face)==4 for face in result['geometry']['faces']))
        self.assertEqual(result['health'], dict(components=1,nonmanifold_edges=0,degenerate_faces=0))

    def test_partial_subdivision_warns_about_ngons(self):
        result=edit(self.request('subdivide_edges', edges=[0], cuts=1))
        self.assertGreater(result['after']['topology']['ngons'],0)
        self.assertTrue(result['warnings'])

    def test_smoothing_is_scoped(self):
        before=inspect(self.name)['geometry']['vertices']
        edit(self.request('set_face_smoothing', faces=[0], smooth=True))
        self.assertEqual(sum(p.use_smooth for p in bpy.context.object.data.polygons),1)
        self.assertEqual(before,inspect(self.name)['geometry']['vertices'])

    def test_subdivision_failure_restores_modifier(self):
        request=self.request('set_subdivision',levels=2)
        before=inspect(self.name)
        with patch('modeler.runtime.inspect',side_effect=[before,RuntimeError('Probe failed')]):
            with self.assertRaises(RuntimeError):set_subdivision(request)
        self.assertEqual(len(bpy.context.object.modifiers),0)
        set_subdivision(self.request('set_subdivision',levels=1))
        request=self.request('set_subdivision',levels=2)
        before=inspect(self.name)
        with patch('modeler.runtime.inspect',side_effect=[before,RuntimeError('Probe failed')]):
            with self.assertRaises(RuntimeError):set_subdivision(request)
        modifier=bpy.context.object.modifiers['Modeler_Subdivision']
        self.assertEqual((modifier.levels,modifier.render_levels),(1,1))

    def test_subdivide_and_position_preserve_closed_cage(self):
        state = inspect(self.name)
        edit(self.request('subdivide_edges', edges=list(range(len(state['geometry']['edges']))), cuts=2))
        state = inspect(self.name)
        self.assertEqual(len(state['geometry']['vertices']), 56)
        positions = [[i, [x*.5, y*.1, z]] for i, (x,y,z) in enumerate(state['geometry']['vertices'])]
        changed = edit(self.request('set_vertex_positions', positions=positions))
        self.assertEqual(changed['after']['health'], dict(components=1, nonmanifold_edges=0, degenerate_faces=0))

    def test_modifier_change_invalidates_fingerprint(self):
        modifier = bpy.context.object.modifiers.new('Live bevel', 'BEVEL')
        before = inspect(self.name)['fingerprint']
        modifier.width = .2
        self.assertNotEqual(before, inspect(self.name)['fingerprint'])

    def test_cpu_render_is_temporary(self):
        before = inspect(self.name)['fingerprint']
        def counts():
            return tuple(len(x) for x in (bpy.data.scenes,bpy.data.objects,bpy.data.cameras,bpy.data.materials,bpy.data.lights))
        initial_counts = counts()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'preview.png'
            render(dict(action='render', object=self.name, eye=[4, -6, 3],
                        target=[0, 0, 0], scale=4, path=str(path), engine='CYCLES'))
            self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
            self.assertGreater(path.stat().st_size, 1000)
        self.assertEqual(before, inspect(self.name)['fingerprint'])
        self.assertEqual(initial_counts, counts())

    def test_malformed_positions_roll_back(self):
        before=inspect(self.name)['fingerprint']
        for positions in ([[]], [[0]], [['x',[1,2,3]]], [[0,[1,2,3]],[0,[4,5,6]]]):
            with self.assertRaises(ValueError):
                edit(self.request('set_vertex_positions', positions=positions))
            self.assertEqual(before,inspect(self.name)['fingerprint'])
            self.assertEqual(len(bpy.data.meshes),1)

    def test_invalid_input_does_not_mutate(self):
        before = inspect(self.name)['fingerprint']
        for values in ([0, 0, float('nan')], [0, 0], [True, 0, 0]):
            with self.assertRaises(ValueError):
                edit(self.request('move_vertices', vertices=[0], delta=values))
        self.assertEqual(before, inspect(self.name)['fingerprint'])


suite = unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeTests)
if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
    raise RuntimeError('Blender tests failed')
