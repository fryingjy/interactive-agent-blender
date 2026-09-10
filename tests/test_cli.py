"""End-to-end subprocess test. Set BLENDER_EXECUTABLE to run."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(os.environ.get('BLENDER_EXECUTABLE'), 'Requires Blender')
class CommandLineTest(unittest.TestCase):
    def test_observe_edit_observe_and_overwrite_rejection(self):
        blender = os.environ['BLENDER_EXECUTABLE']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.blend'
            script = ('import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); '
                      'bpy.ops.mesh.primitive_cube_add(); '
                      f'bpy.ops.wm.save_as_mainfile(filepath={str(source)!r})')
            subprocess.run([blender, '-b', '--factory-startup', '--disable-autoexec',
                            '--python-exit-code', '1', '--python-expr', script],
                           capture_output=True, check=True, timeout=60)
            original_hash = hashlib.sha256(source.read_bytes()).hexdigest()

            def run(label, request, input_path=source, output=None, success=True):
                req = root / (label + '.request.json')
                report = root / (label + '.report.json')
                req.write_text(json.dumps(request), encoding='utf-8')
                command = [sys.executable, '-m', 'modeler', '--blender', blender,
                           '--input', str(input_path), '--request', str(req), '--report', str(report)]
                if output:
                    command.extend(['--output', str(output)])
                result = subprocess.run(command, capture_output=True, text=True, timeout=90)
                if success:
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    return json.loads(report.read_text(encoding='utf-8'))
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(report.exists())

            state = run('inspect', {'action': 'inspect', 'object': 'Cube'})
            request = {'action': 'move_vertices', 'object': 'Cube',
                       'expected_fingerprint': state['fingerprint'],
                       'vertices': [0], 'delta': [.1, 0, 0]}
            output = root / 'edited.blend'
            result = run('edit', request, output=output)
            reloaded = run('reload', {'action': 'inspect', 'object': 'Cube'}, output)
            self.assertEqual(result['after']['fingerprint'], reloaded['fingerprint'])
            run('overwrite', request, output=output, success=False)
            run('stale', request, input_path=output, output=root/'stale.blend', success=False)
            self.assertFalse((root/'stale.blend').exists())
            self.assertEqual(original_hash, hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
