"""Stage-aware next-decision planner for the autonomous modeling loop.

The planner does not generate an asset or execute Blender operations.  It composes the state and
evidence channels the runtime already exposes into one auditable next-decision contract.  The
caller must re-observe after executing that decision before asking for another one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from blender_ops.stage_gates import evaluate_stage_gate
from knowledge_engine.reasoning import Diagnosis, RegionRepairHistory
from knowledge_engine.strategy import ModelingBrief, choose_strategy


STAGES = (
    "REFERENCE_ANALYSIS",
    "PRIMARY_BLOCKOUT",
    "PROPORTION_SILHOUETTE",
    "SECONDARY_FORMS",
    "TOPOLOGY_SURFACE",
    "TERTIARY_DETAIL",
    "PRODUCTION_PREP",
    "FINAL_REVIEW",
)


@dataclass
class PlannerContext:
    task_id: str
    asset_id: str
    stage: str
    session_id: str
    scene_revision: int
    control_mode: str = "AGENT_CONTROL"
    active_object: str | None = None
    mode: str = "OBJECT"
    selection: dict[str, Any] = field(default_factory=dict)
    base_state: dict[str, Any] = field(default_factory=dict)
    evaluated_state: dict[str, Any] = field(default_factory=dict)
    semantic_regions: list[dict[str, Any]] = field(default_factory=list)
    visual_tickets: list[dict[str, Any]] = field(default_factory=list)
    stage_evidence: dict[str, Any] = field(default_factory=dict)
    recent_decisions: list[dict[str, Any]] = field(default_factory=list)
    retrieved_skills: list[dict[str, Any]] = field(default_factory=list)
    diagnosis: Diagnosis | None = None
    repair_history: RegionRepairHistory | None = None
    brief: ModelingBrief = field(default_factory=ModelingBrief)
    external_edit_detected: bool = False
    minimum_stage_iou: float = 0.9

    def validate(self) -> None:
        if not self.task_id or not self.asset_id:
            raise ValueError("task_id and asset_id are required")
        if self.stage not in STAGES:
            raise ValueError(f"unknown modeling stage: {self.stage}")
        if not self.session_id:
            raise ValueError("session_id is required")
        if self.scene_revision < 0:
            raise ValueError("scene_revision must be non-negative")


@dataclass(frozen=True)
class DecisionContract:
    disposition: str
    action: str
    target_object: str | None
    target_region: str | None
    rationale: tuple[str, ...]
    expected_effect: str
    verification: tuple[str, ...]
    observed_revision: int
    confidence: str
    operation: str | None = None
    operation_params: dict[str, Any] = field(default_factory=dict)
    retrieved_skill_ids: tuple[str, ...] = ()
    next_stage: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        # JSON evidence uses lists rather than dataclass tuples.
        for key in ("rationale", "verification", "retrieved_skill_ids"):
            result[key] = list(result[key])
        return result


def _skill_ids(context: PlannerContext) -> tuple[str, ...]:
    values = []
    for item in context.retrieved_skills:
        skill_id = item.get("skill_id") or item.get("id")
        if skill_id and skill_id not in values:
            values.append(str(skill_id))
    return tuple(values)


def _contract(context: PlannerContext, **kwargs: Any) -> DecisionContract:
    return DecisionContract(
        observed_revision=context.scene_revision,
        retrieved_skill_ids=_skill_ids(context),
        **kwargs,
    )


def _technical_health(context: PlannerContext) -> dict[str, Any]:
    evaluated = context.evaluated_state.get("mesh_health", context.evaluated_state)
    base = context.base_state.get("mesh_health", context.base_state)
    # The evaluated result is what is displayed; use base only when no evaluated channel exists.
    return evaluated or base or {}


def _highest_ticket(context: PlannerContext) -> dict[str, Any] | None:
    if not context.visual_tickets:
        return None
    return sorted(
        context.visual_tickets,
        key=lambda item: (
            int(item.get("priority", 10**6)),
            -float(item.get("severity", 0.0)),
            str(item.get("type", "")),
        ),
    )[0]


def _next_stage(stage: str) -> str | None:
    index = STAGES.index(stage)
    return STAGES[index + 1] if index + 1 < len(STAGES) else None


def plan_next_decision(context: PlannerContext) -> DecisionContract:
    """Return exactly one next action from the latest observed state.

    Priority is deliberate: authority/staleness, technical breakage, uncertainty/rebuild pressure,
    visual/reference mismatch, stage transition, then stage-specific observation.  A cosmetic
    ticket can never hide a broken evaluated mesh or a stale transaction baseline.
    """

    context.validate()
    target = context.active_object

    if context.control_mode != "AGENT_CONTROL":
        return _contract(
            context,
            disposition="WAIT",
            action="YIELD_CONTROL",
            target_object=target,
            target_region=None,
            rationale=(f"control mode is {context.control_mode}",),
            expected_effect="No mutation occurs while another owner controls the scene.",
            verification=("poll control mode before planning again",),
            confidence="HIGH",
        )

    if context.external_edit_detected:
        return _contract(
            context,
            disposition="INSPECT",
            action="REOBSERVE_AFTER_EXTERNAL_EDIT",
            operation="get_full_state",
            operation_params={"object_name": target} if target else {},
            target_object=target,
            target_region=None,
            rationale=("the observed transaction baseline is stale",),
            expected_effect="Replace stale topology, transform, modifier, and selection assumptions.",
            verification=("capture a new layered fingerprint", "confirm a new observed revision"),
            confidence="HIGH",
        )

    health = _technical_health(context)
    if health.get("non_manifold_edges", 0) > 0:
        history = context.repair_history.decision() if context.repair_history else None
        rebuild = history and history["decision"] == "REBUILD_REGION"
        return _contract(
            context,
            disposition="ACT",
            action="REBUILD_OPEN_REGION" if rebuild else "LOCALIZE_NON_MANIFOLD_REGION",
            operation=None if rebuild else "inspect_region",
            operation_params={} if rebuild else {"rings": 2},
            target_object=target,
            target_region=context.repair_history.region_id if context.repair_history else None,
            rationale=(
                f"evaluated mesh has {health['non_manifold_edges']} non-manifold edges",
                "technical breakage has priority over visual polish",
                *(('repeated repair evidence crosses the rebuild threshold',) if rebuild else ()),
            ),
            expected_effect="Identify or replace the smallest region responsible for the open/invalid surface.",
            verification=("evaluated non-manifold count decreases", "visual silhouette does not regress"),
            confidence="HIGH" if rebuild else "MEDIUM",
        )

    if health.get("degenerate_faces", 0) > 0 or health.get("loose_verts", 0) > 0:
        return _contract(
            context,
            disposition="INSPECT",
            action="LOCALIZE_DEGENERATE_GEOMETRY",
            operation="get_evaluated_defect_regions",
            operation_params={"object_name": target, "max_tickets": 20},
            target_object=target,
            target_region=None,
            rationale=("technical cleanup needs a localized cause before mutation",),
            expected_effect="Produce persistent-ID targets for one scoped repair.",
            verification=("defect ticket resolves to current persistent IDs",),
            confidence="HIGH",
        )

    if context.diagnosis and context.diagnosis.next_action() == "INSPECT_OR_RESEARCH":
        return _contract(
            context,
            disposition="RESEARCH",
            action="RESOLVE_LOW_CONFIDENCE_DIAGNOSIS",
            target_object=target,
            target_region=context.repair_history.region_id if context.repair_history else None,
            rationale=(
                f"diagnosis confidence {context.diagnosis.confidence:.2f} is below the action threshold",
                *tuple(f"alternative: {item}" for item in context.diagnosis.alternatives),
            ),
            expected_effect="Obtain discriminating evidence before risking an artistic mutation.",
            verification=("state which alternative was ruled in or out", "record source or local probe evidence"),
            confidence="LOW",
        )

    ticket = _highest_ticket(context)
    if ticket is not None:
        ticket_type = str(ticket.get("type", "visual_mismatch"))
        region = ticket.get("target")
        suggested = ticket.get("suggested_operation")
        if ticket_type in {"missing_component", "component_mismatch"}:
            strategy = choose_strategy(context.brief)
            representation = strategy["representation"]["choice"]
            return _contract(
                context,
                disposition="ACT",
                action="BLOCK_OUT_MISSING_COMPONENT",
                operation="create_curve" if representation == "CURVE" else "create_primitive",
                operation_params={"component_id": region, "representation": representation},
                target_object=target,
                target_region=str(region) if region else None,
                rationale=(f"highest-priority ticket is {ticket_type}", *tuple(strategy["representation"]["reasons"])),
                expected_effect="Add the missing primary/secondary silhouette contribution as an editable component.",
                verification=("component mask is present", "component graph remains valid", "recompute silhouette metrics"),
                confidence=strategy["representation"]["confidence"],
            )
        return _contract(
            context,
            disposition="ACT" if suggested else "INSPECT",
            action="CORRECT_LOCAL_REFERENCE_MISMATCH" if suggested else "LOCALIZE_REFERENCE_MISMATCH",
            operation=str(suggested) if suggested else "render_semantic_region",
            operation_params=dict(ticket.get("operation_params", {})),
            target_object=target,
            target_region=str(region) if region else None,
            rationale=(
                f"highest-priority visual ticket is {ticket_type}",
                f"ticket severity is {float(ticket.get('severity', 0.0)):.3f}",
            ),
            expected_effect="Reduce the named local reference error without regressing other relevant views.",
            verification=("recompute the ticket metric", "check all relevant views for regression", "inspect evaluated surface"),
            confidence="MEDIUM" if suggested else "LOW",
        )

    gate = evaluate_stage_gate(context.stage, context.stage_evidence, min_iou=context.minimum_stage_iou)
    following = _next_stage(context.stage)
    if gate["pass"] and following:
        return _contract(
            context,
            disposition="ADVANCE_STAGE",
            action="ADVANCE_MODELING_STAGE",
            operation="set_modeling_stage",
            operation_params={"stage": following, "evidence": context.stage_evidence},
            target_object=target,
            target_region=None,
            rationale=(f"{context.stage} gate passed",),
            expected_effect=f"Move the asset to {following} without changing geometry.",
            verification=("stage transition is persisted", "scene revision is unchanged by evidence-only transition"),
            confidence="HIGH",
            next_stage=following,
        )

    return _contract(
        context,
        disposition="INSPECT",
        action="COLLECT_STAGE_GATE_EVIDENCE",
        operation="get_full_state" if target else "get_viewport_state",
        operation_params={"object_name": target} if target else {},
        target_object=target,
        target_region=None,
        rationale=tuple(gate["failures"] or [f"missing evidence: {item}" for item in gate["missing"]]),
        expected_effect=f"Resolve the next unsupported claim in the {context.stage} gate.",
        verification=("rerun the stage gate with newly observed evidence",),
        confidence="HIGH",
    )
