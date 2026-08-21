"""Unit test for blender_ops.repair, whose only collaborators (mesh_ops, state_probe)
require live bpy. mesh_ops/state_probe are faked so the orchestration contract --
merge -> recalc normals -> triangulate, health probed before and after -- is verified
without needing a running Blender."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

REPAIR_PATH = Path(__file__).resolve().parents[1] / "blender_ops" / "repair.py"


def _load_repair_with_fakes():
    calls = []

    fake_mesh_ops = types.ModuleType("mesh_ops")
    fake_mesh_ops.merge_by_distance = lambda name, dist=0.0001: calls.append(("merge_by_distance", name, dist))
    fake_mesh_ops.recalc_normals = lambda name: calls.append(("recalc_normals", name))
    fake_mesh_ops.triangulate_ngons = lambda name: calls.append(("triangulate_ngons", name))

    health_results = iter([{"non_manifold_edges": 3, "ngons": 1}, {"non_manifold_edges": 0, "ngons": 0}])
    fake_state_probe = types.ModuleType("state_probe")
    fake_state_probe.mesh_health = lambda name: (calls.append(("mesh_health", name)), next(health_results))[1]

    sys.modules["mesh_ops"] = fake_mesh_ops
    sys.modules["state_probe"] = fake_state_probe
    try:
        spec = importlib.util.spec_from_file_location("_repair_under_test", REPAIR_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        del sys.modules["mesh_ops"]
        del sys.modules["state_probe"]

    return module, calls


def test_repair_non_manifold_from_boolean_calls_merge_then_recalc_then_triangulate():
    module, calls = _load_repair_with_fakes()

    result = module.repair_non_manifold_from_boolean("Cutter", merge_dist=0.001)

    assert calls == [
        ("mesh_health", "Cutter"),
        ("merge_by_distance", "Cutter", 0.001),
        ("recalc_normals", "Cutter"),
        ("triangulate_ngons", "Cutter"),
        ("mesh_health", "Cutter"),
    ]


def test_repair_non_manifold_from_boolean_returns_before_and_after_health():
    module, _ = _load_repair_with_fakes()

    result = module.repair_non_manifold_from_boolean("Cutter")

    assert result == {
        "before": {"non_manifold_edges": 3, "ngons": 1},
        "after": {"non_manifold_edges": 0, "ngons": 0},
    }


def test_repair_non_manifold_from_boolean_defaults_merge_dist():
    module, calls = _load_repair_with_fakes()

    module.repair_non_manifold_from_boolean("Cutter")

    merge_call = next(c for c in calls if c[0] == "merge_by_distance")
    assert merge_call == ("merge_by_distance", "Cutter", 0.0001)
