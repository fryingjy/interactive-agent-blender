import ast
from pathlib import Path
import unittest


SERVER_PATH = Path(__file__).resolve().parents[1] / "blender_ops" / "modeler_server.py"
RENDER_PATH = Path(__file__).resolve().parents[1] / "blender_ops" / "render_passes.py"


class ModelerServerRenderContractTests(unittest.TestCase):
    def test_silhouette_wrapper_forwards_multi_object_frame_name(self):
        tree = ast.parse(SERVER_PATH.read_text(encoding="utf-8"))
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "cmd_render_silhouette"
        )
        self.assertIn("frame_name", [argument.arg for argument in method.args.args])
        call = next(
            node
            for node in ast.walk(method)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "render_silhouette"
        )
        forwarded = {keyword.arg: keyword.value for keyword in call.keywords}
        self.assertIsInstance(forwarded.get("frame_name"), ast.Name)
        self.assertEqual(forwarded["frame_name"].id, "frame_name")

    def test_diagnostic_wrapper_forwards_read_only_smooth_preview_selection(self):
        tree = ast.parse(SERVER_PATH.read_text(encoding="utf-8"))
        method = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "cmd_render_diagnostic_pass"
        )
        self.assertIn("preview_smooth_names", [argument.arg for argument in method.args.args])
        call = next(
            node for node in ast.walk(method)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "render_diagnostic_pass"
        )
        forwarded = {keyword.arg: keyword.value for keyword in call.keywords}
        self.assertIsInstance(forwarded.get("preview_smooth_names"), ast.Name)
        self.assertEqual(forwarded["preview_smooth_names"].id, "preview_smooth_names")

    def test_diagnostic_report_uses_authoritative_revision_counter(self):
        tree = ast.parse(RENDER_PATH.read_text(encoding="utf-8"))
        function = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "render_diagnostic_pass"
        )
        revision_value = next(
            value
            for node in ast.walk(function)
            if isinstance(node, ast.Dict)
            for key, value in zip(node.keys, node.values)
            if isinstance(key, ast.Constant) and key.value == "scene_revision"
        )
        self.assertIsInstance(revision_value, ast.Call)
        self.assertIsInstance(revision_value.func, ast.Attribute)
        self.assertEqual(revision_value.func.attr, "current_revision")


if __name__ == "__main__":
    unittest.main()
