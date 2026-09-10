"""Native Blender integration tests; fixtures are not reference-modeling evidence."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modeler.runtime import edit, inspect
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

    def test_modifier_change_invalidates_fingerprint(self):
        modifier = bpy.context.object.modifiers.new('Live bevel', 'BEVEL')
        before = inspect(self.name)['fingerprint']
        modifier.width = .2
        self.assertNotEqual(before, inspect(self.name)['fingerprint'])

    def test_render_is_temporary(self):
        before = inspect(self.name)['fingerprint']
        counts = (len(bpy.data.scenes), len(bpy.data.objects), len(bpy.data.cameras))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'preview.png'
            render(dict(action='render', object=self.name, eye=[4, -6, 3],
                        target=[0, 0, 0], scale=4, path=str(path)))
            self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
            self.assertGreater(path.stat().st_size, 1000)
        self.assertEqual(before, inspect(self.name)['fingerprint'])
        self.assertEqual(counts, (len(bpy.data.scenes), len(bpy.data.objects), len(bpy.data.cameras)))

    def test_invalid_input_does_not_mutate(self):
        before = inspect(self.name)['fingerprint']
        for values in ([0, 0, float('nan')], [0, 0], [True, 0, 0]):
            with self.assertRaises(ValueError):
                edit(self.request('move_vertices', vertices=[0], delta=values))
        self.assertEqual(before, inspect(self.name)['fingerprint'])


suite = unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeTests)
if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
    raise RuntimeError('Blender tests failed')
