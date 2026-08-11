"""Independently rerun and verify the Godot tangent-bake import evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-11_godot-engine-validation"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def glb_json(path: Path) -> dict:
    with path.open("rb") as handle:
        magic, version, total_length = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF" or version != 2 or total_length != path.stat().st_size:
            raise ValueError(f"invalid GLB header: {path}")
        chunk_length, chunk_type = struct.unpack("<II", handle.read(8))
        if chunk_type != 0x4E4F534A:
            raise ValueError(f"first GLB chunk is not JSON: {path}")
        return json.loads(handle.read(chunk_length).decode("utf-8").rstrip(" \x00"))


def primitive_state(document: dict) -> dict:
    primitive = document["meshes"][0]["primitives"][0]
    material = document["materials"][primitive["material"]]
    pbr = material.get("pbrMetallicRoughness", {})
    return {
        "attributes": sorted(primitive["attributes"]),
        "has_normal_texture": "normalTexture" in material,
        "has_base_color_texture": "baseColorTexture" in pbr,
        "metallic_factor": pbr.get("metallicFactor"),
        "roughness_factor": pbr.get("roughnessFactor"),
        "image_mime_types": sorted(image.get("mimeType", "") for image in document.get("images", [])),
    }


def run_godot(godot: Path) -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory(prefix="godot-tangent-verify-") as temp_name:
        temp = Path(temp_name)
        for name in (
            "project.godot",
            "validate_import.gd",
            "godot_tangent_bake_valid.glb",
            "godot_tangent_bake_invalid_color_wiring.glb",
        ):
            shutil.copy2(RUN / name, temp / name)
        imported = subprocess.run(
            [str(godot), "--headless", "--import", "--path", str(temp)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        validated = subprocess.run(
            [str(godot), "--headless", "--path", str(temp), "--script", "res://validate_import.gd"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        runtime_report_path = temp / "godot_import_report.json"
        runtime_report = json.loads(runtime_report_path.read_text(encoding="utf-8")) if runtime_report_path.exists() else {}
        process = {
            "import_returncode": imported.returncode,
            "validation_returncode": validated.returncode,
            "import_stdout_has_completion": "DONE" in imported.stdout,
            "validation_stdout_has_result": "GODOT_IMPORT_RESULT:" in validated.stdout,
            "stderr": (imported.stderr + validated.stderr).strip(),
        }
        return runtime_report, process


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--godot",
        type=Path,
        default=RUN / "media" / "Godot_v4.7.1-stable_win64_console.exe",
    )
    args = parser.parse_args()
    godot = args.godot.resolve()
    if not godot.is_file():
        raise SystemExit(f"Godot executable not found: {godot}")

    valid_path = RUN / "godot_tangent_bake_valid.glb"
    invalid_path = RUN / "godot_tangent_bake_invalid_color_wiring.glb"
    valid = primitive_state(glb_json(valid_path))
    invalid = primitive_state(glb_json(invalid_path))
    runtime, process = run_godot(godot)
    blender = json.loads((RUN / "blender_export_report.json").read_text(encoding="utf-8"))
    source_dimensions = blender["source"]["dimensions_blender_xyz"]
    expected_godot_dimensions = [source_dimensions[0], source_dimensions[2], source_dimensions[1]]
    actual_godot_dimensions = runtime.get("valid", {}).get("aabb_size_godot_xyz", [])

    assertions = {
        "fresh_godot_import_and_script_exit_zero": process["import_returncode"] == 0 and process["validation_returncode"] == 0,
        "fresh_runtime_report_passes": runtime.get("pass") is True,
        "named_engine_version_is_4_7_1_stable": runtime.get("godot_version", {}).get("string") == "4.7.1-stable (official)",
        "valid_glb_declares_position_normal_tangent_uv": {"POSITION", "NORMAL", "TANGENT", "TEXCOORD_0"}.issubset(valid["attributes"]),
        "valid_glb_declares_normal_texture": valid["has_normal_texture"] and not valid["has_base_color_texture"],
        "invalid_control_declares_wrong_base_color_semantic": invalid["has_base_color_texture"] and not invalid["has_normal_texture"],
        "material_values_match_in_both_packages": all(
            abs(state[key] - expected) < 1e-6
            for state in (valid, invalid)
            for key, expected in (("metallic_factor", 0.15), ("roughness_factor", 0.42))
        ),
        "normal_pixels_are_embedded_png": valid["image_mime_types"] == ["image/png"] and invalid["image_mime_types"] == ["image/png"],
        "godot_axis_conversion_preserves_dimensions": len(actual_godot_dimensions) == 3 and all(
            abs(actual - expected) < 1e-5 for actual, expected in zip(actual_godot_dimensions, expected_godot_dimensions)
        ),
        "runtime_detects_deliberate_semantic_failure": runtime.get("assertions", {}).get("failure_control_detected") is True,
    }
    zip_path = godot.with_name("Godot_v4.7.1-stable_win64.exe.zip")
    report = {
        "lab": "independent_godot_tangent_bake_verification",
        "method": "fresh temporary Godot project plus direct GLB 2.0 JSON inspection; no Blender API",
        "engine": {
            "executable": str(godot),
            "executable_sha256": sha256(godot),
            "download_zip_sha256": sha256(zip_path) if zip_path.is_file() else None,
            "official_download": "https://godotengine.org/download/archive/4.7.1-stable/",
        },
        "glb": {
            "valid": {**valid, "sha256": sha256(valid_path)},
            "invalid_color_wiring": {**invalid, "sha256": sha256(invalid_path)},
        },
        "process": process,
        "runtime": runtime,
        "dimension_mapping": {
            "blender_xyz": source_dimensions,
            "expected_godot_xyz_after_y_up_export": expected_godot_dimensions,
            "actual_godot_xyz": actual_godot_dimensions,
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (RUN / "independent_verify_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("GODOT_INDEPENDENT_VERIFY_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
