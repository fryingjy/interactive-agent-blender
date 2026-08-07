"""Live decision-revision counter, owned by the Blender scene itself -- not
by any script this agent writes. Stored as a custom property on the scene
datablock so it persists in the .blend and cannot be reset or faked by a
local Python variable inside one execute_blender_code call.

This exists to make batched "decisions" detectable: a genuine decision
cycle reads current_revision(), reasons about it, performs exactly one
mutation, then calls advance_revision(), which only succeeds if the
revision it's given matches what the scene actually holds right now. A
script that tries to apply five mutations in a row using one locally-cached
"before" value will find the second advance_revision() call rejects it,
because the first call already moved the scene's revision forward.
"""

import bpy

_KEY = "decision_revision"


def current_revision():
    return int(bpy.context.scene.get(_KEY, 0))


def advance_revision(expected_before):
    """Advance the live revision by exactly one, but only if expected_before
    matches what the scene actually holds. Raises ValueError otherwise --
    this is the mechanism that catches stale/batched decisions."""
    actual = current_revision()
    if expected_before != actual:
        raise ValueError(
            f"stale observation: decision was reasoned against revision "
            f"{expected_before}, but the scene is now at revision {actual} "
            f"-- re-observe before deciding the next action"
        )
    new_rev = actual + 1
    bpy.context.scene[_KEY] = new_rev
    return new_rev
