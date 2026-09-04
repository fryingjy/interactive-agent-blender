import subprocess
import sys


def test_base_knowledge_engine_import_does_not_load_optional_image_stack():
    code = (
        "import sys; import knowledge_engine; "
        "assert 'knowledge_engine.gemini_component_segmentation' not in sys.modules; "
        "assert 'cv2' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
