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
from .reference_analysis import ReferenceItem, ReferenceSet, PropertyClaim, audit_reference_set, build_reference_stage_evidence

__all__ = [
    "Diagnosis",
    "RegionRepairHistory",
    "RetrievalContext",
    "SkillUsageLog",
    "StructuredSkillStore",
    "ReferenceItem",
    "ReferenceSet",
    "PropertyClaim",
    "audit_reference_set",
    "build_reference_stage_evidence",
    "MixedSurfaceCauseDiagnosis",
    "SurfaceCauseAblation",
    "SurfaceCauseDiagnosis",
    "SurfaceCauseEvidence",
    "classify_surface_cause",
    "diagnose_mixed_surface_causes",
]
