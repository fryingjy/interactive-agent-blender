import ast
import tempfile
import unittest
from contextlib import suppress
from pathlib import Path
from types import SimpleNamespace


ADDON_PATH = Path(__file__).resolve().parents[1] / "addon.py"


def _load_resource_helpers(requests_double, tempfile_double=None):
    """Execute only the add-on's pure resource helpers without importing Blender."""
    tree = ast.parse(ADDON_PATH.read_text(encoding="utf-8"))
    selected = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.Assign))
        and (
            isinstance(node, ast.FunctionDef)
            and node.name in {"_unlink_quietly", "_download_to_temp_file"}
            or isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "DOWNLOAD_TIMEOUT"
                for target in node.targets
            )
        )
    ]
    namespace = {
        "Path": Path,
        "suppress": suppress,
        "tempfile": tempfile_double or tempfile,
        "requests": requests_double,
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(ADDON_PATH), "exec"), namespace)
    return namespace


class _Response:
    def __init__(self, chunks=(), failure=None):
        self.chunks = chunks
        self.failure = failure

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        if chunk_size != 8192:
            raise AssertionError(f"unexpected chunk size: {chunk_size}")
        for chunk in self.chunks:
            yield chunk
        if self.failure:
            raise self.failure


class AddonResourceSafetyTests(unittest.TestCase):
    def test_streamed_download_uses_timeout_and_skips_empty_chunks(self):
        calls = []

        def get(url, **kwargs):
            calls.append((url, kwargs))
            return _Response((b"abc", b"", b"def"))

        namespace = _load_resource_helpers(SimpleNamespace(get=get))
        path = namespace["_download_to_temp_file"](
            "https://example.test/model.glb",
            suffix=".glb",
            headers={"User-Agent": "test-agent"},
        )
        try:
            self.assertEqual(Path(path).read_bytes(), b"abcdef")
            self.assertEqual(calls[0][1]["timeout"], (10, 120))
            self.assertTrue(calls[0][1]["stream"])
            self.assertEqual(calls[0][1]["headers"], {"User-Agent": "test-agent"})
        finally:
            namespace["_unlink_quietly"](path)
        self.assertFalse(Path(path).exists())

    def test_failed_stream_removes_partial_file(self):
        created = []

        def named_temp_file(**kwargs):
            handle = tempfile.NamedTemporaryFile(**kwargs)
            created.append(handle.name)
            return handle

        def get(_url, **_kwargs):
            return _Response((b"partial",), RuntimeError("stream interrupted"))

        namespace = _load_resource_helpers(
            SimpleNamespace(get=get),
            SimpleNamespace(NamedTemporaryFile=named_temp_file),
        )
        with self.assertRaisesRegex(RuntimeError, "stream interrupted"):
            namespace["_download_to_temp_file"]("https://example.test/broken.glb")
        self.assertEqual(len(created), 1)
        self.assertFalse(Path(created[0]).exists())

    def test_every_requests_call_has_an_explicit_timeout(self):
        tree = ast.parse(ADDON_PATH.read_text(encoding="utf-8"))
        missing = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if not isinstance(node.func.value, ast.Name) or node.func.value.id != "requests":
                continue
            if node.func.attr not in {"get", "post", "put", "delete", "patch"}:
                continue
            if not any(keyword.arg == "timeout" for keyword in node.keywords):
                missing.append(node.lineno)
        self.assertEqual(missing, [])

    def test_addon_does_not_use_global_or_private_tempfile_cleanup(self):
        source = ADDON_PATH.read_text(encoding="utf-8")
        self.assertNotIn("tempfile._cleanup", source)
        self.assertNotIn("os.unlink(", source)
        self.assertNotIn("os.remove(", source)


if __name__ == "__main__":
    unittest.main()
