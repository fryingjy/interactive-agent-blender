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
from knowledge_engine.scene_decomposition import SceneDecomposition
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

PLANNER_ACTIONABLE_SKILL_STATUSES = {"TRANSFER_VALIDATED", "RUNTIME_VALIDATED", "PROMOTED"}


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
    reference_decomposition: SceneDecomposition | None = None
    component_strategy_resolution: dict[str, Any] | None = None
    external_edit_detected: bool = False
    intentional_non_manifold_edge_ids: tuple[int, ...] = ()
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
        if len(set(self.intentional_non_manifold_edge_ids)) != len(self.intentional_non_manifold_edge_ids):
            raise ValueError("intentional_non_manifold_edge_ids must be unique persistent edge IDs")
        if self.reference_decomposition is not None:
            self.reference_decomposition.validate()
        if self.component_strategy_resolution is not None:
            disposition = self.component_strategy_resolution.get("disposition")
            if disposition not in {"TARGETED_REFERENCE_RESEARCH", "SELECT_STRATEGY"}:
                raise ValueError(f"invalid component strategy disposition: {disposition}")
            if disposition == "SELECT_STRATEGY" and self.component_strategy_resolution.get(
                "chosen_policy"
            ) not in {"CONTINUOUS_MESH", "SEPARATE_COMPONENTS"}:
                raise ValueError("selected component strategy requires a valid chosen_policy")


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


def _skill_guided_ticket_decision(
    context: PlannerContext, ticket: dict[str, Any]
) -> DecisionContract | None:
    """Use only transfer-validated-or-better knowledge to resolve a matching ticket.

    A retrieved record does not get to invent targets or parameters. The visual/topology
    ticket still owns those scene-specific facts; the skill contributes the operation,
    expected effect, and verification policy for a narrow declared ticket type.
    """
    ticket_type = str(ticket.get("type", ""))
    for retrieved in context.retrieved_skills:
        skill = retrieved.get("skill", retrieved)
        status = str(retrieved.get("status", skill.get("status", "UNKNOWN")))
        hint = skill.get("planner_hint")
        if status not in PLANNER_ACTIONABLE_SKILL_STATUSES or not isinstance(hint, dict):
            continue
        if ticket_type not in set(map(str, hint.get("trigger_ticket_types", []))):
            continue
        stages = set(map(str, hint.get("modeling_stages", [])))
        if stages and context.stage not in stages:
            continue
        required_fields = set(map(str, hint.get("required_ticket_fields", [])))
        if any(ticket.get(field) in (None, "", [], {}) for field in required_fields):
            continue
        operation = hint.get("operation")
        if not operation:
            continue
        skill_id = retrieved.get("skill_id") or retrieved.get("id") or skill.get("skill_id") or skill.get("id")
        return _contract(
            context,
            disposition="ACT",
            action=str(hint.get("action", "APPLY_RETRIEVED_SKILL")),
            operation=str(operation),
            operation_params=dict(ticket.get("operation_params", {})),
            target_object=context.active_object,
            target_region=str(ticket.get("target")) if ticket.get("target") else None,
            rationale=(
                f"highest-priority visual ticket is {ticket_type}",
                f"transfer-validated skill {skill_id} matches this ticket",
                str(hint.get("reason", "use the validated local intervention before broader repair")),
            ),
            expected_effect=str(hint.get("expected_effect", "Reduce the named local defect.")),
            verification=tuple(map(str, hint.get("verification", ["reinspect the affected region"]))),
            confidence=str(hint.get("confidence", "MEDIUM")),
        )
    return None


def _effective_brief(context: PlannerContext) -> ModelingBrief:
    if context.reference_decomposition is None:
        return context.brief
    return context.reference_decomposition.to_modeling_brief(context.brief)


def _next_stage(stage: str) -> str | None:
    index = STAGES.index(stage)
    return STAGES[index + 1] if index + 1 < len(STAGES) else None


def _passed_stage_contract(
    context: PlannerContext, target: str | None
) -> DecisionContract:
    """Return the single valid outcome for a passed stage gate."""
    following = _next_stage(context.stage)
    if following is None:
        return _contract(
            context,
            disposition="COMPLETE",
            action="ACCEPT_FINAL_REVIEW",
            operation=None,
            operation_params={},
            target_object=target,
            target_region=None,
            rationale=(f"{context.stage} gate passed",),
            expected_effect="Accept the independently verified asset without another mutation.",
            verification=("persist final evidence", "save the editable source"),
            confidence="HIGH",
        )
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
        verification=(
            "stage transition is persisted",
            "scene revision is unchanged by evidence-only transition",
        ),
        confidence="HIGH",
        next_stage=following,
    )


def _reference_decomposition_contract(
    context: PlannerContext, target: str | None
) -> DecisionContract | None:
    """Require evidence-bound component claims after the reference-set audit passes."""
    if context.reference_decomposition is None:
        return None
    readiness = context.reference_decomposition.blockout_readiness()
    if readiness["ready_for_blockout"]:
        return None
    needs_research = bool(
        readiness["high_impact_unresolved_claims"]
        or readiness["conflicting_modeling_signals"]
    )
    return _contract(
        context,
        disposition="RESEARCH" if needs_research else "INSPECT",
        action="RESOLVE_REFERENCE_UNCERTAINTY" if needs_research else "COMPLETE_REFERENCE_DECOMPOSITION",
        operation=None,
        operation_params={
            "missing_requirements": readiness["missing_requirements"],
            "claim_ids": readiness["high_impact_unresolved_claims"],
            "research_questions": readiness["research_questions"],
            "conflicting_modeling_signals": readiness["conflicting_modeling_signals"],
        },
        target_object=target,
        target_region=None,
        rationale=tuple(
            [f"missing reference requirement: {item}" for item in readiness["missing_requirements"]]
            + [f"high-impact unresolved claim: {item}" for item in readiness["high_impact_unresolved_claims"]]
            + [f"conflicting modeling signal: {item}" for item in readiness["conflicting_modeling_signals"]]
        ),
        expected_effect="Resolve the reference claim or keep the affected construction reversible before geometry hardens the guess.",
        verification=(
            "bind each resolved claim to observed evidence or a cited inference",
            "rerun reference blockout readiness",
            "record rejected construction strategies",
        ),
        confidence="HIGH" if needs_research else "MEDIUM",
    )


def _reference_stage_contract(
    context: PlannerContext, target: str | None
) -> DecisionContract:
    """Prevent every geometry action until structured reference evidence passes."""
    gate = evaluate_stage_gate(
        context.stage, context.stage_evidence, min_iou=context.minimum_stage_iou
    )
    if gate["pass"]:
        decomposition_gate = _reference_decomposition_contract(context, target)
        if decomposition_gate is not None:
            return decomposition_gate
        resolution = context.component_strategy_resolution
        if resolution and resolution["disposition"] == "TARGETED_REFERENCE_RESEARCH":
            return _contract(
                context,
                disposition="RESEARCH",
                action="RESOLVE_SECONDARY_VIEW_STRATEGY",
                operation=None,
                operation_params={
                    "queries": list(resolution.get("queries", [])),
                    "required_secondary_views": list(
                        resolution.get("required_secondary_views", [])
                    ),
                },
                target_object=target,
                target_region=None,
                rationale=(str(resolution.get("reason", "component strategy is unresolved")),),
                expected_effect=(
                    "Acquire a discriminating same-variant view before choosing continuous or "
                    "separate construction."
                ),
                verification=(
                    "rerun multi-view component-strategy resolution",
                    "retain the rejected strategy and measured view scores",
                ),
                confidence="HIGH",
            )
        return _passed_stage_contract(context, target)
    queries = tuple(map(str, context.stage_evidence.get("targeted_research_queries", [])))
    return _contract(
        context,
        disposition="RESEARCH",
        action="TARGETED_REFERENCE_RESEARCH",
        operation=None,
        operation_params={"queries": list(queries)},
        target_object=target,
        target_region=None,
        rationale=tuple(
            gate["failures"] or [f"missing evidence: {item}" for item in gate["missing"]]
        ),
        expected_effect=(
            "Acquire the missing same-target, view, dimension, or property evidence before "
            "geometry is created."
        ),
        verification=(
            "rerun the structured reference-set audit",
            "do not model while the audit is incomplete",
        ),
        confidence="HIGH",
    )


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

    # Reference readiness preempts every geometry mutation, including technical repair of a stale
    # or placeholder object left in the scene.  Existing geometry is not evidence that modeling may
    # continue.
    if context.stage == "REFERENCE_ANALYSIS":
        return _reference_stage_contract(context, target)

    health = _technical_health(context)
    observed_non_manifold = int(health.get("non_manifold_edges", 0))
    allowed_non_manifold = len(context.intentional_non_manifold_edge_ids)
    unexpected_non_manifold = max(0, observed_non_manifold - allowed_non_manifold)
    if unexpected_non_manifold > 0:
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
                f"evaluated mesh has {observed_non_manifold} non-manifold edges; {allowed_non_manifold} are explicitly allowlisted intentional boundaries",
                f"{unexpected_non_manifold} non-manifold edges remain unexplained",
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

    if context.stage == "PRIMARY_BLOCKOUT":
        decomposition_gate = _reference_decomposition_contract(context, target)
        if decomposition_gate is not None:
            return decomposition_gate
        coverage_gate = evaluate_stage_gate(
            context.stage, context.stage_evidence, min_iou=context.minimum_stage_iou
        )
        coverage = context.stage_evidence.get("component_coverage")
        captured_revision = (
            coverage.get("scene_revision") if isinstance(coverage, dict) else None
        )
        coverage_is_current = captured_revision == context.scene_revision
        if context.reference_decomposition is not None and (
            "component_coverage" in coverage_gate["missing"]
            or "structured one-to-one component coverage is missing or invalid" in coverage_gate["failures"]
            or not coverage_is_current
        ):
            return _contract(
                context,
                disposition="INSPECT",
                action="CAPTURE_LIVE_COMPONENT_COVERAGE",
                operation="check_scene_component_coverage",
                operation_params={
                    "decomposition": context.reference_decomposition.to_dict()
                    if context.reference_decomposition else {},
                    "collection_name": context.stage_evidence.get("component_coverage_collection"),
                },
                target_object=target,
                target_region=None,
                rationale=(
                    "primary blockout cannot advance on a caller-authored component-presence assertion",
                    "capture actual live mesh names against the evidence-bound component board",
                    *(
                        (f"coverage revision {captured_revision} differs from observed revision {context.scene_revision}",)
                        if captured_revision is not None and not coverage_is_current else ()
                    ),
                ),
                expected_effect=(
                    "Produce a session/revision-bound one-to-one primary-component coverage record "
                    "before further blockout decisions."
                ),
                verification=(
                    "coverage has no unmatched primary components",
                    "captured scene revision matches the current observation",
                    "rerun the primary-blockout stage gate",
                ),
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
        ticket_revision = ticket.get("scene_revision")
        if ticket.get("source") == "EXTERNAL_HUMAN_REVIEW" and ticket_revision != context.scene_revision:
            return _contract(
                context,
                disposition="INSPECT",
                action="RECAPTURE_STALE_HUMAN_REVIEW",
                target_object=target,
                target_region=str(region) if region else None,
                rationale=(
                    f"human review targets scene revision {ticket_revision}, not observed revision {context.scene_revision}",
                    "a later edit may have repaired or moved the reviewed region",
                ),
                expected_effect="Obtain a current human judgment before using it to drive a repair.",
                verification=("review scene revision equals the current observation",),
                confidence="HIGH",
            )
        suggested = ticket.get("suggested_operation")
        skill_guided = _skill_guided_ticket_decision(context, ticket)
        if skill_guided is not None:
            return skill_guided
        if ticket_type in {"missing_component", "component_mismatch"}:
            effective_brief = _effective_brief(context)
            strategy = choose_strategy(effective_brief)
            representation = strategy["representation"]["choice"]
            component_policy = strategy["components"]["choice"]
            strategy_resolution = context.component_strategy_resolution
            if strategy_resolution and strategy_resolution["disposition"] == "SELECT_STRATEGY":
                component_policy = str(strategy_resolution["chosen_policy"])
            return _contract(
                context,
                disposition="ACT",
                action="BLOCK_OUT_MISSING_COMPONENT",
                operation="create_curve" if representation == "CURVE" else "create_primitive",
                operation_params={
                    "component_id": region,
                    "representation": representation,
                    "component_policy": component_policy,
                    "component_strategy_candidate": (
                        strategy_resolution.get("chosen_candidate_id")
                        if strategy_resolution
                        and strategy_resolution["disposition"] == "SELECT_STRATEGY"
                        else None
                    ),
                    "reference_claim_notes": list(effective_brief.notes),
                },
                target_object=target,
                target_region=str(region) if region else None,
                rationale=(
                    f"highest-priority ticket is {ticket_type}",
                    *tuple(strategy["representation"]["reasons"]),
                    *tuple(strategy["components"]["reasons"]),
                    *(
                        (str(strategy_resolution.get("reason")),)
                        if strategy_resolution
                        and strategy_resolution["disposition"] == "SELECT_STRATEGY"
                        else ()
                    ),
                ),
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
    if gate["pass"]:
        return _passed_stage_contract(context, target)

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
