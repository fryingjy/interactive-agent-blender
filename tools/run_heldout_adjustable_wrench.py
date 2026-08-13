"""Held-out benchmark: vintage adjustable (pipe) wrench.

Construction method, chosen specifically to avoid hard-coding this object's
shape: every cross-section station along the main body is read directly from
`reference_front_mask_measurement.json` / `reference_side_mask_measurement.json`
(tools/measure_reference.py output) -- front width becomes the station's world-X
half-extent, side width becomes its world-Y half-extent, both relative to a
centerline measured from the object's own round shaft/handle region, and height
becomes world-Z. An ellipse is swept through these measured (cx, cy, z, rx, ry)
stations and lofted into one continuous all-quad manifold body (closed caps at
both ends), the same "loft real measurements, don't sculpt by eye" discipline
already used for the watering can and desk lamp.

Per benchmark_brief.md Step 0, tools/verify_reference_view_orientation.py was run
prospectively against this reference BEFORE this script was written and passed
with --in-plane-axis X --wide-view front (see
runs/2026-08-12_heldout-adjustable-wrench/orientation_check/). That result is why
front width maps to X and side width maps to Y below, not assumed.

Known, deliberate limitation of a single elliptical loft: it cannot represent the
jaw's fork/mouth gap (two separate prongs) -- a single closed ring can only ever
pinch narrower there, not split. That pinch is still the real measured data (the
front-view bbox genuinely narrows at that row), so the candidate is left as one
continuous primary-form body and checked against gates honestly rather than
patched with an invented, unmeasured "tooth" shape. If gates fail specifically in
the jaw region, that is the next real gap to close with actual evidence (e.g. a
fill-ratio profile, not a bbox-width one, to detect a true two-lobe row) -- not a
license to hand-sculpt an answer.

CORRECTION (found on direct user review, 2026-08-13): the first version of this
script shipped with zero bevel weighting, no Bevel modifier, and blanket
use_smooth=True (no angle threshold, no recorded shading_policy) -- the whole
established hard-surface policy in smooth_by_angle.md was skipped entirely when
this asset used a new construction strategy. Every existing mesh-validity and
silhouette check passed anyway, because none of them check for this. Fixed by
applying that policy for real: weight the two reference-confirmed collar/step
seams (see COLLAR_TRANSITION_Y below), Bevel (WEIGHT-limited) before
Smooth by Angle. Also switched the ring parameterization from disk() (a
square-to-circle mapping only angle-uniform for a fixed single radius) to equal
angle, for clean circumferential edge loops instead of a warped grid -- a
topology-quality defect separate from the shading-policy gap, also caught on
direct review rather than by any automated check. Edited and re-saved in place
into the same heldout_adjustable_wrench.blend rather than a new run/version.

CONVENTION (2026-08-13): the working .blend now lives at models/adjustable_wrench.blend
-- this project's new single consolidated folder for the actual, accurately-named,
continuously-edited-in-place model files, per user instruction. Editing this asset
means editing that file directly, not creating another timestamped copy. The
runs/2026-08-12_heldout-adjustable-wrench/ directory remains the dated evidence
record (reference renders, measurement JSON, IoU reports, session narrative) for
this benchmark and is not duplicated into models/.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "runs" / "2026-08-12_heldout-adjustable-wrench" / "reference"
sys.path.insert(0, str(ROOT / "blender_ops"))
from render_passes import render_silhouette  # noqa: E402
import object_ops  # noqa: E402
import persistent_ids  # noqa: E402


def args():
    vals = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(vals) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    out = Path(vals[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    return out


def mat(name, color, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.metallic = metal
    m.roughness = rough
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    return m


def boundary(n):
    return ([(i, 0) for i in range(n)] + [(n - 1, j) for j in range(1, n)]
             + [(i, n - 1) for i in range(n - 2, -1, -1)] + [(0, j) for j in range(n - 2, 0, -1)])


def disk(u, v):
    if abs(u) < 1e-9 and abs(v) < 1e-9:
        return 0.0, 0.0
    if abs(u) > abs(v):
        r = u
        t = math.pi / 4 * (v / u)
    else:
        r = v
        t = math.pi / 2 - math.pi / 4 * (u / v)
    return r * math.cos(t), r * math.sin(t)


def make_obj(name, verts, faces, col, material, props=None):
    me = bpy.data.meshes.new(name + "Mesh")
    me.from_pydata(verts, [], faces)
    me.materials.append(material)
    me.update(calc_edges=True)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    uv = me.uv_layers.new(name="UVMap")
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    dx = max(xs) - min(xs) or 1
    dy = max(ys) - min(ys) or 1
    dz = max(zs) - min(zs) or 1
    for p in me.polygons:
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.y - min(ys)) / dy, (co.z - min(zs)) / dz)
    if props:
        for k, v in props.items():
            ob[k] = v
    return ob


def elliptical_loft(name, stations, grid_n, col, material, props=None):
    """stations: list of (cx, cy, z, rx, ry) ordered bottom-to-top. Generalizes
    this project's existing ring_loft (single radius, fixed center) to an
    independently-measured X/Y half-extent and an offset center per station, so
    it can loft an asymmetric measured profile instead of only a body of
    revolution.

    Ring vertices are placed at equal angular spacing (cos/sin theta), not by
    running boundary()'s square-perimeter indices through disk() the way
    ring_loft/path_loft do for their single-radius circular rings. disk() is a
    square-to-circle mapping that is only angle-uniform when every ring is the
    same shape; here rx/ry (eccentricity) changes every ring, so the same
    boundary index would land at a different true angle from one ring to the
    next, producing an uneven, non-radial quad flow down the whole body
    instead of clean circumferential edge loops -- a real topology-quality
    defect independent of silhouette accuracy (caught on direct review, not by
    any automated manifold/ngon check, which this passes either way)."""
    bc = boundary(grid_n)
    verts = []
    faces = []
    rings = []
    for cx, cy, z, rx, ry in stations:
        ring = []
        for k in range(len(bc)):
            theta = 2 * math.pi * k / len(bc)
            a, b = math.cos(theta), math.sin(theta)
            ring.append(len(verts))
            verts.append((cx + a * rx, cy + b * ry, z))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(len(a)):
            faces.append((a[k], a[(k + 1) % len(a)], b[(k + 1) % len(a)], b[k]))
    for ridx, up in ((0, False), (len(rings) - 1, True)):
        cx, cy, z, rx, ry = stations[ridx]
        mp = {bc[k]: rings[ridx][k] for k in range(len(bc))}
        for j in range(1, grid_n - 1):
            for i in range(1, grid_n - 1):
                a, b = disk(-1 + 2 * i / (grid_n - 1), -1 + 2 * j / (grid_n - 1))
                mp[(i, j)] = len(verts)
                verts.append((cx + a * rx, cy + b * ry, z))
        for j in range(grid_n - 1):
            for i in range(grid_n - 1):
                q = (mp[(i, j)], mp[(i + 1, j)], mp[(i + 1, j + 1)], mp[(i, j + 1)])
                faces.append(q if up else tuple(reversed(q)))
    return make_obj(name, verts, faces, col, material, props)


# Investigated and NOT applied: direct pixel run-length analysis of
# reference_front_mask.png confirmed rows y_px in [108, 132] genuinely
# contain two disjoint foreground spans (fixed jaw/teeth vs. movable jaw),
# not merely a pinch. A candidate that split the loft there -- fixed-jaw-only
# extents on Wrench_Body plus a separate Movable_Jaw insert over the left
# span -- was built and measured: front IoU went 0.916856 -> 0.911423 and
# front recall 0.982389 -> 0.973345 (runs/2026-08-12_heldout-adjustable-wrench/
# session_report.md has both full reports). The sudden single-lobe radius at
# those stations, next to full-span radius at neighboring stations, made the
# loft taper more sharply through that band and lose more true-reference
# coverage than the gap-carving recovered. Reverted rather than kept for a
# net-negative, added-complexity change -- see session_report.md for the
# full comparison instead of re-deriving it from git history.


def load_stations(sample_stride=8):
    front = json.loads((REF_DIR / "reference_front_mask_measurement.json").read_text())
    side = json.loads((REF_DIR / "reference_side_mask_measurement.json").read_text())
    front_by_y = {r["y_px"]: r for r in front["row_profile"]}
    side_by_y = {r["y_px"]: r for r in side["row_profile"]}
    common_y = sorted(set(front_by_y) & set(side_by_y))

    # Centerline: measured from the confirmed round shaft region (y_norm in
    # [0.55, 0.70], well below the jaw/adjuster and above the handle bulge),
    # where front width in px == side width in px (verified during
    # measurement -- a round cross-section is the only way both orthographic
    # widths match), so each view's own bbox-center in that region is its
    # true centerline, not an assumed image-center.
    y0, y1 = front["silhouette_bbox_px"]["y"]
    shaft_ys = [y for y in common_y if 0.55 <= (y - y0) / (y1 - y0) <= 0.70]
    front_centerline = sum((front_by_y[y]["x_min_px"] + front_by_y[y]["x_max_px"]) / 2 for y in shaft_ys) / len(shaft_ys)
    side_centerline = sum((side_by_y[y]["x_min_px"] + side_by_y[y]["x_max_px"]) / 2 for y in shaft_ys) / len(shaft_ys)

    SCALE = 1.0 / 200.0
    sampled = common_y[::sample_stride]
    if sampled[-1] != common_y[-1]:
        sampled.append(common_y[-1])
    stations = []
    for y in sampled:
        f, s = front_by_y[y], side_by_y[y]
        z = (y1 - y) * SCALE
        cx = ((f["x_min_px"] + f["x_max_px"]) / 2 - front_centerline) * SCALE
        cy = ((s["x_min_px"] + s["x_max_px"]) / 2 - side_centerline) * SCALE
        rx = (f["x_max_px"] - f["x_min_px"]) / 2 * SCALE
        ry = (s["x_max_px"] - s["x_min_px"]) / 2 * SCALE
        rx = max(rx, 0.004)
        ry = max(ry, 0.004)
        stations.append((cx, cy, z, rx, ry))
    stations.sort(key=lambda st: st[2])  # bottom (handle tip, z=0) to top (jaw tip)
    return stations, {"front_centerline_px": front_centerline, "side_centerline_px": side_centerline,
                       "scale": SCALE, "station_count": len(stations), "y1_px": y1}


# Genuine sharp seams, identified the same evidence-based way as the jaw fork
# above -- not a blanket geometric-angle threshold (this project's own
# documented Rose_Head/spout/handset regression is exactly why not). Found by
# scanning the measured station radii for large station-to-station jumps
# outside the already-known jaw/adjuster region (y_px > 150): a 37.5px front
# half-width drop at y_px=340 (housing block ending, shaft beginning) and a
# 10px side half-width jump at y_px=372 (shaft ending, handle collar
# beginning). Both are directly visible in reference_side_beauty.png as crisp
# machined steps, not smooth transitions. Each is weighted on both of its
# bounding rings (the wide side and the narrow side of the step) for a
# well-defined chamfer once beveled.
COLLAR_TRANSITION_Y = [340, 348, 364, 372]


def apply_hard_surface_shading_policy(obj_name, collar_y_values, y1, scale):
    """Applies this project's established policy
    (knowledge/foundation/operator_cards/smooth_by_angle.md): identify
    reference-confirmed sharp edges, weight them, Bevel (WEIGHT-limited,
    widest width that stays manifold/non-degenerate) before Smooth by Angle.
    This was skipped entirely on the first version of this asset -- caught on
    direct user review, not by any automated check, since a plain
    smooth-shaded loft with no Bevel modifier passes every existing
    mesh-validity and silhouette check without it."""
    obj = bpy.data.objects[obj_name]
    target_zs = [round((y1 - y) * scale, 6) for y in collar_y_values]

    edge_ids_to_weight = []
    persistent_ids.ensure_persistent_ids(obj_name)
    index_to_id = persistent_ids.get_id_maps(obj_name)["edges"]["index_to_id"]
    for edge in obj.data.edges:
        z0 = obj.data.vertices[edge.vertices[0]].co.z
        z1 = obj.data.vertices[edge.vertices[1]].co.z
        if abs(z0 - z1) > 1e-5:
            continue  # longitudinal edge, not a ring/circumferential edge
        if any(abs(z0 - target) < 1e-4 for target in target_zs):
            edge_ids_to_weight.append(index_to_id[edge.index])

    weight_result = object_ops.set_bevel_weight_by_ids(obj_name, edge_ids_to_weight, weight=1.0)

    accepted_width = None
    attempts = []
    for width in (0.03, 0.02, 0.012, 0.006):
        existing = [m for m in obj.modifiers if m.type == "BEVEL"]
        bevel = existing[0] if existing else obj.modifiers.new("Semantic weighted edge radius", "BEVEL")
        bevel.limit_method = "WEIGHT"
        bevel.width = width
        bevel.segments = 2
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        eval_mesh = eval_obj.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(eval_mesh)
        non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
        degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
        bm.free()
        eval_obj.to_mesh_clear()
        attempts.append({"width": width, "non_manifold_edges": non_manifold, "degenerate_faces": degenerate})
        if non_manifold == 0 and degenerate == 0:
            accepted_width = width
            break
        obj.modifiers.remove(bevel)

    smooth_result = object_ops.set_smooth_by_angle(obj_name)

    return {
        "weighted_edge_ids": edge_ids_to_weight,
        "weight_result": weight_result,
        "bevel_width_attempts": attempts,
        "accepted_bevel_width": accepted_width,
        "smooth_by_angle": smooth_result,
    }


def main():
    out = args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bpy.context.scene.world = world
    col = bpy.context.scene.collection

    steel = mat("Wrench Steel", (0.30, 0.30, 0.32), metal=0.75, rough=0.4)

    stations, meta = load_stations(sample_stride=8)
    body = elliptical_loft(
        "Wrench_Body", stations, 10, col, steel,
        props={
            "construction": "single elliptical loft, every station read from measured front/side reference row widths",
            "primitive_operators_used": 0,
            "source_absent": True,
            "measurement_meta": json.dumps(meta),
        },
    )

    shading_result = apply_hard_surface_shading_policy(
        "Wrench_Body", COLLAR_TRANSITION_Y, meta["y1_px"], meta["scale"]
    )
    audit = object_ops.hard_surface_shading_audit("Wrench_Body")

    bpy.ops.object.select_all(action="SELECT")
    all_objs = list(bpy.context.selected_objects)
    all_names = [ob.name for ob in all_objs]

    masks = {}
    for view in ("front", "side", "top", "isometric"):
        mask_path = out / f"candidate_{view}_mask.png"
        result = render_silhouette(all_names, str(mask_path), view=view, resolution=768)
        masks[view] = {"path": str(mask_path), "result": result}

    models_dir = ROOT / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(models_dir / "adjustable_wrench.blend"))

    verts_total = sum(len(ob.data.vertices) for ob in all_objs)
    faces_total = sum(len(ob.data.polygons) for ob in all_objs)

    report = {
        "objects": all_names,
        "station_meta": meta,
        "vertices_total": verts_total,
        "faces_total": faces_total,
        "shading_policy_result": shading_result,
        "hard_surface_shading_audit": audit,
        "masks": masks,
    }
    (out / "candidate_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
