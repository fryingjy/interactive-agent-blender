import hashlib
import json

from tools.materialize_reference_hashes import process_manifest


def test_materializer_writes_and_then_verifies_local_hash(tmp_path):
    artifact = tmp_path / "front.png"
    artifact.write_bytes(b"fixed reference bytes")
    manifest = tmp_path / "reference_manifest.json"
    manifest.write_text(json.dumps({"items": [{"reference_id": "front", "local_file": "front.png"}]}))
    updated = process_manifest(manifest, write=True)
    assert updated["pass"] is True
    payload = json.loads(manifest.read_text())
    assert payload["items"][0]["local_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert process_manifest(manifest, write=False)["pass"] is True


def test_materializer_fails_on_missing_local_artifact(tmp_path):
    manifest = tmp_path / "reference_manifest.json"
    manifest.write_text(json.dumps({"items": [{"reference_id": "front", "local_file": "missing.png"}]}))
    report = process_manifest(manifest, write=True)
    assert report["pass"] is False
    assert report["errors"]
