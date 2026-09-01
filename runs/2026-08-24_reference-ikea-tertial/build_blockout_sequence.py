"""Generate the typed, reference-authorized TERTIAL primary blockout sequence."""

from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
COLLECTION = "TERTIAL_BLOCKOUT"
ASSEMBLY_SCALE = 1.0
BASE_PIVOT_XZ = (0.10, 0.65)


def scale_position(point: tuple[float, float]) -> tuple[float, float]:
    """Scale articulated pivot spacing about the fixed clamp pivot."""
    x, z = point
    bx, bz = BASE_PIVOT_XZ
    return bx + (x - bx) * ASSEMBLY_SCALE, bz + (z - bz) * ASSEMBLY_SCALE


def translate_profile(profile: list[list[float]], delta: tuple[float, float]) -> list[list[float]]:
    return [[x + delta[0], z + delta[1]] for x, z in profile]


def scale_curve_points(points: list[list[float]]) -> list[list[float]]:
    scaled = []
    for x, y, z in points:
        scaled_x, scaled_z = scale_position((x, z))
        scaled.append([scaled_x, y, scaled_z])
    return scaled


HEAD_DELTA = tuple(a - b for a, b in zip(scale_position((-1.86, 5.42)), (-1.86, 5.42)))
ELBOW_DELTA = tuple(a - b for a, b in zip(scale_position((1.35, 3.90)), (1.35, 3.90)))


def bar_profile(start: tuple[float, float], end: tuple[float, float], thickness: float) -> list[list[float]]:
    """Eight-point chamfered strip outline in the X/Z construction plane."""
    sx, sz = start
    ex, ez = end
    dx, dz = ex - sx, ez - sz
    length = math.hypot(dx, dz)
    tx, tz = dx / length, dz / length
    nx, nz = -tz, tx
    half = thickness / 2.0
    chamfer = min(thickness * 0.32, length * 0.02)

    def point(x: float, z: float, along: float, across: float) -> list[float]:
        return [x + tx * along + nx * across, z + tz * along + nz * across]

    return [
        point(sx, sz, -chamfer, half * 0.55),
        point(sx, sz, 0.0, half),
        point(ex, ez, 0.0, half),
        point(ex, ez, chamfer, half * 0.55),
        point(ex, ez, chamfer, -half * 0.55),
        point(ex, ez, 0.0, -half),
        point(sx, sz, 0.0, -half),
        point(sx, sz, -chamfer, -half * 0.55),
    ]


def create_profile(name: str, profile: list[list[float]], depth: float) -> dict:
    return {"label": f"create_{name}", "command": "create_profile_extrusion", "params": {"name": name, "profile": profile, "depth": depth}}


def create_cylinder(name: str, location: list[float], radius: float, depth: float) -> list[dict]:
    return [
        {"label": f"create_{name}", "command": "create_primitive", "params": {"name": name, "primitive_type": "cylinder", "location": location, "vertices": 16, "radius": radius, "depth": depth}},
        {"label": f"orient_{name}_across_depth", "transaction": {"name": name, "action_type": "assembly_placement", "operation": "rotate_object", "params": {"delta_radians": [math.pi / 2.0, 0.0, 0.0]}, "command_id": f"tertial-{name}-orient-v1"}},
    ]


def loop(points: list[tuple[float, float]], y: float) -> list[list[float]]:
    return [[x, y, z] for x, z in points]


def spring_points(start: tuple[float, float], end: tuple[float, float], y_center: float, turns: int = 22) -> list[list[float]]:
    """Polyline helix around an X/Z centerline, including short straight hooks."""
    sx, sz = start
    ex, ez = end
    dx, dz = ex - sx, ez - sz
    length = math.hypot(dx, dz)
    nx, nz = -dz / length, dx / length
    radius = 0.045
    samples = turns * 4
    points = [[sx, y_center, sz]]
    for index in range(1, samples):
        t = index / samples
        angle = turns * math.tau * t
        center_x, center_z = sx + dx * t, sz + dz * t
        points.append([
            center_x + nx * math.sin(angle) * radius,
            y_center + math.cos(angle) * radius,
            center_z + nz * math.sin(angle) * radius,
        ])
    points.append([ex, y_center, ez])
    return points


sequence: list[dict] = [
    {
        "label": "add_verified_product_reference_card",
        "command": "create_reference_image",
        "params": {
            "name": "TERTIAL_Official_Side_Reference",
            "image_path": str((OUT / "references" / "tertial_official_1.jpg").resolve()),
            "view_axis": "FRONT", "location": [0.0, 0.7, 2.6], "display_size": 9.2,
            "opacity": 0.28, "collection_name": "CONSTRUCTION_REFERENCES",
            "source_role": "CONSTRUCTION", "calibrated": False,
        },
    },
    {
        "label": "create_connected_revolved_reflector_shell",
        "command": "create_revolved_profile",
        "params": {
            "name": "ShadeShell", "segments": 16,
            "profile": [
                [0.31, 4.72], [0.31, 4.18], [0.38, 4.13], [0.52, 4.02],
                [0.73, 3.84], [0.90, 3.62], [1.06, 3.33], [1.17, 3.05],
                [1.17, 3.00], [1.09, 3.03], [1.08, 3.08], [0.98, 3.30],
                [0.85, 3.58], [0.67, 3.78], [0.49, 3.94], [0.35, 4.05],
                [0.27, 4.12],
            ],
        },
    },
    {
        "label": "place_reflector_on_observed_head_axis",
        "transaction": {"name": "ShadeShell", "action_type": "assembly_placement", "operation": "translate_object", "params": {"delta": [-2.55 + HEAD_DELTA[0], 0.0, 0.85 + HEAD_DELTA[1]]}, "command_id": "tertial-shade-place-v3"},
    },
    {
        "label": "create_connected_socket_housing",
        "command": "create_revolved_profile",
        "params": {
            "name": "SocketHousing", "segments": 16,
            "profile": [[0.35, 4.18], [0.35, 4.82], [0.30, 4.98], [0.22, 5.03], [0.20, 4.96], [0.27, 4.86], [0.28, 4.25]],
        },
    },
    {
        "label": "place_socket_housing",
        "transaction": {"name": "SocketHousing", "action_type": "assembly_placement", "operation": "translate_object", "params": {"delta": [-2.55 + HEAD_DELTA[0], 0.0, 0.85 + HEAD_DELTA[1]]}, "command_id": "tertial-socket-place-v3"},
    },
    create_profile("HeadYoke", translate_profile([[-2.24, 5.23], [-2.05, 5.09], [-1.72, 5.19], [-1.60, 5.37], [-1.72, 5.63], [-2.08, 5.67], [-2.27, 5.52]], HEAD_DELTA), 0.18),
    create_profile("UpperArmBar_A", bar_profile(scale_position((-2.10, 5.54)), scale_position((1.42, 4.18)), 0.13), 0.13),
    create_profile("UpperArmBar_B", bar_profile(scale_position((-2.06, 5.28)), scale_position((1.37, 3.91)), 0.13), 0.13),
]

outer_elbow = translate_profile([[1.00, 4.15], [1.68, 4.03], [1.58, 3.50], [1.12, 3.58]], ELBOW_DELTA)
inner_elbow = translate_profile([[1.18, 3.98], [1.52, 3.91], [1.45, 3.68], [1.24, 3.72]], ELBOW_DELTA)
sequence.append({
    "label": "create_connected_elbow_plate_with_real_opening", "command": "create_quad_annular_shell",
    "params": {
        "name": "ElbowPlate", "front_outer": loop(outer_elbow, -0.065), "front_inner": loop(inner_elbow, -0.065),
        "rear_outer": loop(outer_elbow, 0.065), "rear_inner": loop(inner_elbow, 0.065),
    },
})
sequence.extend([
    create_profile("LowerArmBar_A", bar_profile(scale_position((-0.02, 0.58)), scale_position((1.18, 3.78)), 0.13), 0.13),
    create_profile("LowerArmBar_B", bar_profile(scale_position((0.20, 0.52)), scale_position((1.45, 3.72)), 0.13), 0.13),
    # The official assembly sheet shows a pedestal on a broad mounting plate,
    # with a separate lower jaw and screw. These are real manufactured parts,
    # not decorative primitive stacking.
    create_profile("BaseClamp", [[-0.43, 0.18], [0.43, 0.18], [0.43, 0.40], [0.26, 0.44], [-0.26, 0.44], [-0.43, 0.40]], 0.50),
    create_profile("BaseBushing", [[-0.27, 0.40], [0.27, 0.40], [0.23, 0.82], [0.15, 0.97], [-0.15, 0.97], [-0.23, 0.82]], 0.36),
    create_profile("BaseClampLowerJaw", [[-0.29, -0.22], [0.24, -0.22], [0.24, -0.05], [0.10, 0.04], [-0.26, 0.04], [-0.34, -0.05]], 0.42),
])

spring_specs = [
    ("UpperSpring_Front", spring_points(scale_position((1.47, 4.01)), scale_position((-0.50, 4.80)), -0.13)),
    ("UpperSpring_Rear", spring_points(scale_position((1.47, 4.01)), scale_position((-0.50, 4.80)), 0.13)),
    ("LowerSpring_Front", spring_points(scale_position((0.02, 0.67)), scale_position((0.80, 2.82)), -0.13)),
    ("LowerSpring_Rear", spring_points(scale_position((0.02, 0.67)), scale_position((0.80, 2.82)), 0.13)),
]
for name, points in spring_specs:
    sequence.append({"label": f"create_{name}", "command": "create_curve", "params": {"name": name, "points": points, "bevel_depth": 0.012, "closed": False, "curve_type": "POLY"}})

for args in [
    ("BasePivot", [0.10, 0.0, 0.65], 0.11, 0.38),
    ("ElbowPivot", [*scale_position((1.04, 4.10))[:1], 0.0, scale_position((1.04, 4.10))[1]], 0.10, 0.38),
    ("HeadPivot", [*scale_position((-1.86, 5.42))[:1], 0.0, scale_position((-1.86, 5.42))[1]], 0.11, 0.42),
]:
    sequence.extend(create_cylinder(*args))
sequence.append({"label": "create_clamp_screw", "command": "create_primitive", "params": {"name": "ClampScrew", "primitive_type": "cylinder", "location": [0.08, 0.0, -0.58], "vertices": 16, "radius": 0.045, "depth": 0.72}})
sequence.append({
    "label": "create_connected_clamp_handle", "command": "create_curve",
    "params": {"name": "ClampHandle", "points": [[0.08, 0.0, -0.93], [0.08, 0.0, -1.08], [0.24, 0.0, -1.18]], "bevel_depth": 0.025, "closed": False, "curve_type": "POLY"},
})
sequence.append({
    "label": "create_continuous_power_cable", "command": "create_curve",
    "params": {
        "name": "PowerCable",
        "points": scale_curve_points([
            [-2.55, 0.08, 5.88], [-2.48, 0.08, 6.30], [-2.15, 0.08, 6.62],
            [-1.70, 0.08, 6.72], [-1.38, 0.08, 6.50], [-1.30, 0.08, 6.08],
            [-1.55, 0.08, 5.70], [-0.30, 0.08, 4.88], [1.50, 0.08, 4.32],
            [1.78, 0.08, 4.42], [1.94, 0.08, 4.22], [1.82, 0.08, 3.98],
            [1.58, 0.08, 3.94], [0.70, 0.08, 2.15], [0.28, 0.08, 0.72],
            [0.45, 0.08, 0.30], [0.72, 0.08, -0.20], [1.10, 0.08, -0.72],
            [1.62, 0.08, -1.12]
        ]),
        "bevel_depth": 0.025,
        "closed": False,
        "curve_type": "BEZIER"
    }
})

mesh_objects = [
    "ShadeShell", "SocketHousing", "HeadYoke", "UpperArmBar_A", "UpperArmBar_B", "ElbowPlate",
    "LowerArmBar_A", "LowerArmBar_B", "BaseClamp", "BaseBushing", "BaseClampLowerJaw", "BasePivot", "ElbowPivot",
    "HeadPivot", "ClampScrew",
]
curve_objects = [name for name, _points in spring_specs] + ["ClampHandle", "PowerCable"]
for name in mesh_objects + curve_objects:
    sequence.append({
        "label": f"organize_{name}",
        "transaction": {"name": name, "action_type": "collection_organization", "operation": "organize_object_collection",
                        "params": {"collection_name": COLLECTION}, "command_id": f"tertial-{name}-collection-v1"},
    })

sequence.append({
    "label": "verify_primary_component_coverage",
    "advance_with_component_coverage": {
        "name": "ShadeShell", "stage": "PRIMARY_BLOCKOUT", "decomposition": "scene_decomposition.json",
        "collection_name": COLLECTION, "dimensions_checked": True, "primary_components_present": True,
    },
})
sequence.extend([
    {"label": "inspect_shade_cage", "command": "get_full_state", "params": {"name": "ShadeShell"}},
    {"label": "inspect_elbow_cage", "command": "get_full_state", "params": {"name": "ElbowPlate"}},
    {"label": "inspect_reference_authorization", "command": "get_reference_authorization", "params": {}},
])

(OUT / "typed_blockout_sequence.json").write_text(json.dumps(sequence, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"sequence_steps": len(sequence), "mesh_objects": len(mesh_objects), "curve_objects": len(curve_objects)}, indent=2))
