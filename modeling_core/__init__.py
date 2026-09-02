"""Reference-conditioned shape solving before Blender mutation."""

from .compiler import compile_blender_command
from .camera import calibrate_perspective_view, camera_intrinsics
from .fitting import fit_hypothesis, mask_diagnostics
from .hypothesis import validate_hypothesis
from .mesh import build_profile_extrusion, build_section_loft, build_shape_mesh
from .render import render_silhouette
from .reference_evidence import analyze_reference_mask, extract_reference_evidence
from .component_evidence import extract_component_evidence
from .reference_bundle import build_multiview_evidence_bundle
from .selection import select_shape_family

__all__ = [
    "build_section_loft",
    "build_profile_extrusion",
    "build_shape_mesh",
    "calibrate_perspective_view",
    "camera_intrinsics",
    "compile_blender_command",
    "fit_hypothesis",
    "mask_diagnostics",
    "render_silhouette",
    "analyze_reference_mask",
    "extract_reference_evidence",
    "extract_component_evidence",
    "build_multiview_evidence_bundle",
    "select_shape_family",
    "validate_hypothesis",
]
