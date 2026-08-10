"""Research, ingestion, retrieval, and learning support for the Blender modeler."""

from .retrieval import RetrievalContext, StructuredSkillStore
from .reasoning import Diagnosis, RegionRepairHistory
from .surface_cause_classifier import (
    SurfaceCauseDiagnosis,
    SurfaceCauseEvidence,
    classify_surface_cause,
)
from .telemetry import SkillUsageLog

__all__ = [
    "Diagnosis",
    "RegionRepairHistory",
    "RetrievalContext",
    "SkillUsageLog",
    "StructuredSkillStore",
    "SurfaceCauseDiagnosis",
    "SurfaceCauseEvidence",
    "classify_surface_cause",
]
