"""Research, ingestion, retrieval, and learning support for the Blender modeler."""

from .iteration_control import evaluate_iteration_budget
from .modeling_spec import validate_reference_modeling_spec
from .reasoning import Diagnosis, RegionRepairHistory
from .reference_analysis import (
    PropertyClaim,
    ReferenceItem,
    ReferenceSet,
    audit_reference_set,
    build_reference_stage_evidence,
    validate_depth_critical_reference_support,
)
from .retrieval import RetrievalContext, StructuredSkillStore
from .stage_checkpoint import build_visual_stage_checkpoint
from .surface_cause_classifier import (
    MixedSurfaceCauseDiagnosis,
    SurfaceCauseAblation,
    SurfaceCauseDiagnosis,
    SurfaceCauseEvidence,
    classify_surface_cause,
    diagnose_mixed_surface_causes,
)
from .telemetry import SkillUsageLog
from .tutorial_reproduction import (
    asset_mutation_gate_required,
    asset_surface_gate_required,
    procedural_fixture_sequence,
    reference_modeling_gate_required,
    tutorial_modeling_gate_required,
    tutorial_surface_gate_required,
    validate_tutorial_blockout_review,
    validate_tutorial_premodeling_evidence,
)
from .gemini_reference_critic import (
    analyze_reference_candidate,
    critic_to_repair_tickets,
    derive_correction_directive,
    load_critic_manifest,
    validate_critic_analysis,
    validate_critic_record,
)

__all__ = [
    "Diagnosis",
    "RegionRepairHistory",
    "evaluate_iteration_budget",
    "RetrievalContext",
    "SkillUsageLog",
    "StructuredSkillStore",
    "ReferenceItem",
    "ReferenceSet",
    "PropertyClaim",
    "validate_depth_critical_reference_support",
    "audit_reference_set",
    "build_reference_stage_evidence",
    "validate_reference_modeling_spec",
    "build_visual_stage_checkpoint",
    "tutorial_modeling_gate_required",
    "asset_surface_gate_required",
    "asset_mutation_gate_required",
    "procedural_fixture_sequence",
    "reference_modeling_gate_required",
    "tutorial_surface_gate_required",
    "validate_tutorial_blockout_review",
    "validate_tutorial_premodeling_evidence",
    "analyze_reference_candidate",
    "critic_to_repair_tickets",
    "derive_correction_directive",
    "load_critic_manifest",
    "validate_critic_analysis",
    "validate_critic_record",
    "MixedSurfaceCauseDiagnosis",
    "SurfaceCauseAblation",
    "SurfaceCauseDiagnosis",
    "SurfaceCauseEvidence",
    "classify_surface_cause",
    "diagnose_mixed_surface_causes",
]
