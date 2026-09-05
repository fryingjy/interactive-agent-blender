import tempfile
import unittest
from pathlib import Path

from knowledge_engine.tutorial_reproduction import validate_surface_diagnostic


class SurfaceDiagnosticPolicyTests(unittest.TestCase):
    def test_isolated_live_modifier_trial_only(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'base.blend'
            base.touch()
            out = Path(directory) / 'trial.diagnostic.blend'
            step = {'transaction': {'operation': 'add_modifier', 'params': {'modifier_type': 'SUBSURF'}}}
            result = validate_surface_diagnostic([step], base, out)
            self.assertFalse(result['quality_accepted'])
            self.assertFalse(result['stage_advancement_authorized'])
            for command in ['save_file', 'apply_modifier', 'create_primitive', 'advance_stage']:
                with self.subTest(command=command), self.assertRaises(ValueError):
                    validate_surface_diagnostic([{'command': command}], base, out)
            with self.assertRaises(ValueError):
                validate_surface_diagnostic([step], base, base)
            out.touch()
            with self.assertRaises(ValueError):
                validate_surface_diagnostic([step], base, out)

    def test_disallows_geometry_and_ambiguous_steps(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'base.blend'
            base.touch()
            out = Path(directory) / 'trial.diagnostic.blend'
            for step in [
                {'transaction': {'operation':'move_selection','params':{}}},
                {'transaction': {'operation':'add_modifier','params':{'modifier_type':'NODES'}}},
                {'command':'get_full_state','advance_with_component_coverage':{}},
                {'command':'get_full_state','transaction':{'operation':'set_smooth_by_angle'}},
            ]:
                with self.subTest(step=step), self.assertRaises(ValueError):
                    validate_surface_diagnostic([step], base, out)
