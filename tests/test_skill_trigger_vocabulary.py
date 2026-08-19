"""Fail closed when a skill's planner trigger cannot be reached from observation.

Origin (2026-08-19 audit): three skills were marked RUNTIME_VALIDATED on the strength of tests
that hand-authored a ticket whose `type` string had been copied out of the skill's own
`planner_hint.trigger_ticket_types`, and whose `operation_params` carried the fix. Nothing in the
system observed geometry and emitted those types, so the skills could never fire during real
modeling. The tests asserted the answer they had just supplied.

These tests make that class of mistake visible instead of silently passing:

1. Every trigger type is either emitted by a real classifier, or explicitly labelled
   NOT_YET_OBSERVABLE. Silence is not allowed -- a skill may not imply runtime reachability it
   does not have.
2. A skill may not claim RUNTIME_VALIDATED while its trigger vocabulary is unreachable.
3. A skill that supplies technique defaults must not try to supply scene-specific facts.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "knowledge" / "skills"

# Ticket types any observer in the repo can actually emit from geometry.
# `corner_triangle` comes from knowledge_engine.defect_classifier; the other two come from
# blender_ops.evaluated_probe.evaluated_defect_regions.
OBSERVABLE_TICKET_TYPES = {"corner_triangle", "area_outlier", "high_angle"}

# Facts that belong to the scene and may never be supplied by a skill.
SCENE_OWNED_KEYS = {"target", "object_name", "name", "face_ids", "edge_ids", "vertex_ids"}


def _skills_with_hints():
    for path in sorted(SKILLS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        hint = data.get("planner_hint")
        if isinstance(hint, dict):
            yield path.name, data, hint


def test_every_trigger_type_is_observable_or_declared_unreachable():
    unexplained = []
    for name, data, hint in _skills_with_hints():
        triggers = set(map(str, hint.get("trigger_ticket_types", [])))
        unreachable = triggers - OBSERVABLE_TICKET_TYPES
        if unreachable and not hint.get("trigger_vocabulary_status"):
            unexplained.append((name, sorted(unreachable)))
    assert not unexplained, (
        "These skills declare planner triggers that no observer emits, without saying so. "
        "Either add a classifier that emits the type, or set "
        "planner_hint.trigger_vocabulary_status explaining why it is not yet observable: "
        f"{unexplained}"
    )


def test_runtime_validated_requires_reachable_trigger_vocabulary():
    overclaimed = []
    for name, data, hint in _skills_with_hints():
        if str(data.get("status")) != "RUNTIME_VALIDATED":
            continue
        triggers = set(map(str, hint.get("trigger_ticket_types", [])))
        if not triggers & OBSERVABLE_TICKET_TYPES:
            overclaimed.append((name, sorted(triggers)))
    assert not overclaimed, (
        "A skill cannot be RUNTIME_VALIDATED when no observer can emit any of its trigger types -- "
        "any runtime evidence must have hand-authored the triggering ticket, which proves nothing: "
        f"{overclaimed}"
    )


def test_skills_never_supply_scene_owned_facts_as_defaults():
    violations = []
    for name, data, hint in _skills_with_hints():
        defaults = hint.get("default_operation_params")
        if not isinstance(defaults, dict):
            continue
        leaked = SCENE_OWNED_KEYS & set(defaults)
        if leaked:
            violations.append((name, sorted(leaked)))
    assert not violations, (
        "planner_hint.default_operation_params may carry technique parameters only. These skills "
        f"tried to supply scene-specific facts: {violations}"
    )


@pytest.mark.parametrize("name,data,hint", list(_skills_with_hints()))
def test_declared_unreachable_triggers_state_a_reason(name, data, hint):
    status = hint.get("trigger_vocabulary_status")
    if status is None:
        return
    assert str(status).startswith("NOT_YET_OBSERVABLE"), (
        f"{name}: trigger_vocabulary_status must begin with NOT_YET_OBSERVABLE and explain why"
    )
    assert len(str(status)) > 60, f"{name}: trigger_vocabulary_status must explain, not just label"
