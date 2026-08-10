"""One-mutation runtime-use proof for a retrieved material-slot skill."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from knowledge_engine.retrieval import RetrievalContext, StructuredSkillStore
from knowledge_engine.telemetry import SkillUsage, SkillUsageLog


def output_directory():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("expected one OUTPUT_DIR after --")
    path = Path(args[0]).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def orphan_count(obj):
    used = {polygon.material_index for polygon in obj.data.polygons}
    return sum(index not in used for index in range(len(obj.data.materials)))


def main():
    output = output_directory()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = "MaterialSkillUse"
    for name in ("Body", "Accent"):
        material = bpy.data.materials.new(name)
        material.diffuse_color = (0.2, 0.3, 0.4, 1.0) if name == "Body" else (0.8, 0.15, 0.05, 1.0)
        obj.data.materials.append(material)

    context = RetrievalContext(query="unused material slot", workflow="materials", defect="orphan assignment")
    retrieved = StructuredSkillStore(REPO_ROOT / "knowledge" / "skills").search(context, top_k=3)
    if not retrieved or retrieved[0]["skill_id"] != "material-slot-orphan-assignment":
        raise SystemExit("expected material-slot skill was not top-ranked")

    before = {"revision": 0, "orphan_slots": orphan_count(obj), "material_indices": sorted({p.material_index for p in obj.data.polygons})}
    # Exactly one scoped scene mutation: assign the top half of faces to the
    # already-present Accent slot. No slot deletion or second repair is batched.
    for polygon in obj.data.polygons:
        if polygon.center.z >= 0:
            polygon.material_index = 1
    bpy.context.scene["decision_revision"] = 1
    after = {"revision": 1, "orphan_slots": orphan_count(obj), "material_indices": sorted({p.material_index for p in obj.data.polygons})}

    success = before["orphan_slots"] == 1 and after["orphan_slots"] == 0
    usage = SkillUsage(
        skill_id=retrieved[0]["skill_id"],
        decision_id="material-skill-use-001",
        asset_id="controlled-material-cube",
        scene_revision_before=0,
        scene_revision_after=1,
        problem="Accent material existed in slot 1 but no polygon used it",
        action="Assign the intended top-half polygons to material slot 1",
        success=success,
        measured_effect={"orphan_slots_before": before["orphan_slots"], "orphan_slots_after": after["orphan_slots"]},
        unexpected_effects=[],
        blender_version=bpy.app.version_string,
    )
    usage_log = SkillUsageLog(output / "skill_usage.jsonl")
    usage_log.append(usage)
    report = {
        "lab": "retrieved_skill_runtime_use",
        "blender_version": bpy.app.version_string,
        "retrieval": {"top_skill": retrieved[0]["skill_id"], "score": retrieved[0]["score"], "score_breakdown": retrieved[0]["score_breakdown"]},
        "before": before,
        "after": after,
        "telemetry_summary": usage_log.summary(retrieved[0]["skill_id"]),
        "single_mutation": True,
        "pass": success,
    }
    (output / "material_skill_use_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "material_skill_use.blend"))
    print(json.dumps(report, indent=2))
    if not success:
        raise SystemExit("retrieved skill did not solve measured problem")


if __name__ == "__main__":
    main()
