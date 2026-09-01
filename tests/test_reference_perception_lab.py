import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ReferencePerceptionLabTests(unittest.TestCase):
    def test_controlled_camera_and_segmentation_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(__file__).resolve().parents[1]
            output = Path(directory) / "lab"
            result = subprocess.run(
                [sys.executable, str(root / "tools" / "run_reference_perception_lab.py"), "--output", str(output)],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["pass"])
            self.assertGreater(
                report["metrics"]["correct_geometry_registered"]["silhouette_iou"],
                report["metrics"]["wrong_geometry_registered"]["silhouette_iou"],
            )


if __name__ == "__main__":
    unittest.main()
