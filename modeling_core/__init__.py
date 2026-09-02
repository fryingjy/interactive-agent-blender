"""Reference-conditioned shape solving before Blender mutation."""

from .compiler import compile_blender_command
from .camera import calibrate_perspective_view, camera_intrinsics
from .fitting import fit_hypothesis, mask_diagnostics
from .hypothesis import validate_hypothesis
from .mesh import build_curve_sweep, build_profile_extrusion, build_profile_revolution, build_profile_ring_extrusion, build_profile_sweep, build_section_loft, build_shape_mesh
from .render import render_silhouette
from .reference_evidence import analyze_reference_mask, extract_reference_evidence
from .component_evidence import extract_component_evidence
from .component_proposals import (
    import_component_region_proposal,
    materialize_confirmed_component_evidence,
    propose_component_regions,
    propose_cross_view_correspondences,
)
from .reference_bundle import build_multiview_evidence_bundle
from .assembly import propose_assembly_hypotheses, resolve_assembly_hypotheses
from .component_fitting import compile_component_assembly, fit_component_families
from .continuity import build_continuous_cage, shape_boundary_ports
from .refit import build_component_refit_tickets
from .initialization import (
    initialize_component_candidates,
    solve_orthographic_component_bounds,
    solve_perspective_component_bounds,
    solve_registered_component_bounds,
)
from .selection import select_shape_family

__all__ = [
    "build_section_loft",
    "build_profile_extrusion",
    "build_profile_revolution",
    "build_profile_ring_extrusion",
    "build_profile_sweep",
    "build_curve_sweep",
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
    "import_component_region_proposal",
    "materialize_confirmed_component_evidence",
    "propose_component_regions",
    "propose_cross_view_correspondences",
    "build_multiview_evidence_bundle",
    "propose_assembly_hypotheses",
    "resolve_assembly_hypotheses",
    "fit_component_families",
    "compile_component_assembly",
    "build_continuous_cage",
    "shape_boundary_ports",
    "build_component_refit_tickets",
    "initialize_component_candidates",
    "solve_orthographic_component_bounds",
    "solve_perspective_component_bounds",
    "solve_registered_component_bounds",
    "select_shape_family",
    "validate_hypothesis",
]
