"""Explicit local/world coordinate conversion.

Why this exists (2026-08-23 audit): the same coordinate-space confusion bug
recurred in at least 3 unrelated builds -- a world-space target position
applied directly to local mesh data without conversion (Swingline 747's
recess/hinge-throat cuts), local-space vertices from one object's mesh placed
at a different object's world origin (the donut/mug coffee-foam placement),
and a parent-inverse matrix that cancelled rather than composed with the
parent's transform (the ramen machine's glow-window placement). None of those
scripts had an obvious, correctly-named conversion helper to reach for; each
inlined its own (wrong) assumption instead. These two functions are that
helper -- thin wrappers, no new concepts, so there is no reason left to
reinvent the conversion.
"""

from __future__ import annotations

from mathutils import Vector


def world_to_local(obj, point):
    """Convert a world-space point to obj's local (mesh-data) space."""
    return obj.matrix_world.inverted() @ Vector(point)


def local_to_world(obj, point):
    """Convert a point in obj's local (mesh-data) space to world space."""
    return obj.matrix_world @ Vector(point)
