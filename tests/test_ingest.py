import json
import tempfile
import unittest
from pathlib import Path

from knowledge_engine.ingest.scene_document import (
    UNFILLED,
    build_scene_document,
    fill_visual_descriptions,
    render_markdown,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "video" / "modeling_lesson.mp4"
FIXTURE_ROOT = FIXTURE.parent


class SceneDocumentTests(unittest.TestCase):
    def test_rejects_paths_outside_approved_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                build_scene_document(
                    FIXTURE,
                    approved_roots=[tmp],
                    output_dir=Path(tmp) / "out",
                    source_id="rejected",
                )

    def test_builds_scene_document_matching_observed_cloudglue_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = build_scene_document(
                FIXTURE,
                approved_roots=[FIXTURE_ROOT],
                output_dir=Path(tmp) / "out",
                source_id="test-lesson",
                scene_window=2.0,
                frames_per_scene=2,
            )

            self.assertEqual(document["file"]["filename"], "modeling_lesson.mp4")
            self.assertTrue(document["file"]["sha256"])
            self.assertAlmostEqual(document["file"]["duration_seconds"], 6.0, delta=0.5)
            self.assertEqual(document["title"], "Modeling Lesson")
            self.assertEqual(document["summary"], UNFILLED)

            self.assertEqual(len(document["scenes"]), 3)
            first, second, third = document["scenes"]
            self.assertEqual(first["start_label"], "00:00")
            self.assertEqual(first["end_label"], "00:02")
            self.assertEqual(first["visual_description"], UNFILLED)
            self.assertEqual([line["text"] for line in first["speech"]], ["Step 1: inspect the base cage."])
            self.assertEqual([line["text"] for line in second["speech"]], ["Step 2: inspect the evaluated surface."])
            self.assertEqual(
                [line["text"] for line in third["speech"]],
                ["Step 3: compare front, side, and top views."],
            )

            # frames_per_scene=2 requests one intra-scene sample in addition to the
            # coarse boundary frame, so each scene should see more than one frame.
            for scene in document["scenes"]:
                self.assertGreaterEqual(len(scene["frame_paths"]), 1)
                for frame_path in scene["frame_paths"]:
                    self.assertTrue(Path(frame_path).is_file())

            on_disk = json.loads((Path(tmp) / "out" / "scene_document.json").read_text(encoding="utf-8"))
            self.assertEqual(on_disk["title"], document["title"])

            markdown = render_markdown(document)
            self.assertIn("## File", markdown)
            self.assertIn("## Title", markdown)
            self.assertIn("## Summary", markdown)
            self.assertIn("## Scenes", markdown)
            self.assertIn("### Scene [00:00 - 00:02]", markdown)
            self.assertIn("**Speech:**", markdown)

    def test_fill_visual_descriptions_persists_reviewer_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_scene_document(
                FIXTURE,
                approved_roots=[FIXTURE_ROOT],
                output_dir=Path(tmp) / "out",
                source_id="test-lesson-fill",
                scene_window=2.0,
                frames_per_scene=1,
            )
            document_path = Path(tmp) / "out" / "scene_document.json"

            updated = fill_visual_descriptions(
                document_path,
                {0: "Blue card reading STEP 1."},
                summary="A three-step instructional sequence.",
            )

            self.assertEqual(updated["scenes"][0]["visual_description"], "Blue card reading STEP 1.")
            self.assertEqual(updated["scenes"][1]["visual_description"], UNFILLED)
            self.assertEqual(updated["summary"], "A three-step instructional sequence.")

            reloaded = json.loads(document_path.read_text(encoding="utf-8"))
            self.assertEqual(reloaded["scenes"][0]["visual_description"], "Blue card reading STEP 1.")

            markdown_on_disk = document_path.with_suffix(".md").read_text(encoding="utf-8")
            self.assertIn("Blue card reading STEP 1.", markdown_on_disk)


if __name__ == "__main__":
    unittest.main()
