"""Explicit per-object modeling-stage tracking (directive section 11/12).

"Do not polish detail while the major form is still wrong." The gadget
prop this session (since deleted) violated this directly: primitives were
placed once, then treated as directly comparable to the finished reference
with no formal check that primary blockout's own gate criteria ("major
proportions plausible, primary silhouette sufficiently close, component
layout stable") had actually been met first. There was no mechanism
forcing that check to happen -- this module is that mechanism.

Stored as a custom property on the object itself (matching
decision_state.py's and persistent_ids.py's own pattern: scene-owned state,
not a Python variable this session could lose or silently skip), so the
current stage and its transition history persist in the .blend and survive
a reconnect.

This does NOT automatically verify gate criteria -- it cannot know whether
"proportions are plausible" without the same kind of real measurement work
tools/measure_reference.py does, which is asset-specific. What it enforces
is that every transition is DECLARED with explicit evidence, creating an
auditable record, rather than a stage being skipped silently under time
pressure.
"""

import json

import bpy

STAGES = [
    "REFERENCE_ANALYSIS",
    "PRIMARY_BLOCKOUT",
    "PROPORTION_SILHOUETTE",
    "SECONDARY_FORMS",
    "TOPOLOGY_SURFACE",
    "TERTIARY_DETAIL",
    "PRODUCTION_PREP",
    "FINAL_REVIEW",
]

_KEY_STAGE = "modeling_stage"
_KEY_LOG = "modeling_stage_log"

# What each stage's own gate is supposed to check before advancing PAST it
# -- directive section 11's own examples, plus the rest inferred from the
# same "do not polish detail while the major form is still wrong" logic.
# Descriptive, not machine-enforced (see module docstring).
GATE_CRITERIA = {
    "REFERENCE_ANALYSIS": "component decomposition and measured proportions/ratios recorded (not eyeballed) before any geometry is created",
    "PRIMARY_BLOCKOUT": "major proportions plausible; primary silhouette sufficiently close; component layout stable",
    "PROPORTION_SILHOUETTE": "measured silhouette comparison (e.g. render_silhouette + fill-ratio or better) against the reference, not just visual impression",
    "SECONDARY_FORMS": "distinct sub-components/features present and correctly placed, still without fine surface detail",
    "TOPOLOGY_SURFACE": "technical validity acceptable (verify_mesh.py clean); surface quality acceptable (evaluated_probe signals); topology contextually appropriate",
    "TERTIARY_DETAIL": "fine detail added only after the above are stable",
    "PRODUCTION_PREP": "naming/organization/materials-UV readiness as applicable",
    "FINAL_REVIEW": "independent verification + final reference comparison recorded",
}


def get_stage(name):
    obj = bpy.data.objects[name]
    return obj.get(_KEY_STAGE, STAGES[0])


def get_stage_log(name):
    obj = bpy.data.objects[name]
    return json.loads(obj.get(_KEY_LOG, "[]"))


def set_stage(name, stage, evidence):
    """Explicitly set/advance the stage. `evidence` is a required
    free-text (or dict) description of why the gate is judged passed --
    this is what gets logged, not enforced automatically. Allows moving
    to any stage (including backward, e.g. a TOPOLOGY_SURFACE check
    reveals the silhouette was actually wrong and PROPORTION_SILHOUETTE
    needs revisiting) -- honest regression is a normal, expected outcome
    here, not an error condition, matching this project's established
    stance on 'reverted'/'external_edit' log entries elsewhere."""
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    obj = bpy.data.objects[name]
    previous = obj.get(_KEY_STAGE, STAGES[0])
    obj[_KEY_STAGE] = stage

    log = json.loads(obj.get(_KEY_LOG, "[]"))
    log.append({
        "from": previous,
        "to": stage,
        "evidence": evidence,
        "gate_criteria_for_to_stage": GATE_CRITERIA.get(stage),
    })
    obj[_KEY_LOG] = json.dumps(log)

    return {
        "name": name,
        "stage": stage,
        "previous_stage": previous,
        "is_regression": STAGES.index(stage) < STAGES.index(previous) if previous in STAGES else False,
    }
