"""Reference-conditioned shape solving before Blender mutation."""

from .compiler import compile_blender_command
from .fitting import fit_hypothesis
from .hypothesis import validate_hypothesis
from .mesh import build_section_loft
from .render import render_silhouette

__all__ = [
    "build_section_loft",
    "compile_blender_command",
    "fit_hypothesis",
    "render_silhouette",
    "validate_hypothesis",
]
