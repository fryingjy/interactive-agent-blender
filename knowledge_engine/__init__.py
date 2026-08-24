"""Research, ingestion, retrieval, and learning support for the Blender modeler."""

from .retrieval import RetrievalContext, StructuredSkillStore
from .reasoning import Diagnosis, RegionRepairHistory
from .surface_cause_classifier import (
    MixedSurfaceCauseDiagnosis,
    SurfaceCauseAblation,
    SurfaceCauseDiagnosis,
    SurfaceCauseEvidence,
    classify_surface_cause,
    diagnose_mixed_surface_causes,
)
from .telemetry import SkillUsageLog
from .reference_analysis import ReferenceItem, ReferenceSet, PropertyClaim, audit_reference_set, build_reference_stage_evidence, validate_depth_critical_reference_support
from .tutorial_reproduction import (
    tutorial_modeling_gate_required,
    tutorial_surface_gate_required,
    validate_tutorial_blockout_review,
    validate_tutorial_premodeling_evidence,
)

__all__ = [
    "Diagnosis",
    "RegionRepairHistory",
    "RetrievalContext",
    "SkillUsageLog",
    "StructuredSkillStore",
    "ReferenceItem",
    "ReferenceSet",
    "PropertyClaim",
    "validate_depth_critical_reference_support",
    "audit_reference_set",
    "build_reference_stage_evidence",
    "tutorial_modeling_gate_required",
    "tutorial_surface_gate_required",
    "validate_tutorial_blockout_review",
    "validate_tutorial_premodeling_evidence",
    "MixedSurfaceCauseDiagnosis",
    "SurfaceCauseAblation",
    "SurfaceCauseDiagnosis",
    "SurfaceCauseEvidence",
    "classify_surface_cause",
    "diagnose_mixed_surface_causes",
]
