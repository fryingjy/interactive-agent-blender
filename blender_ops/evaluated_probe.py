"""Inspect the modifier-EVALUATED mesh, not the base control cage.

Every existing state_probe.py function reads obj.data directly -- the base
mesh, before any modifier stack runs. That was fine for every prop built so
far (Bottle/Flashlight/Mug/SpeakerEnclosure), none of which used a modifier
that changes the visible surface. It stops being fine the moment a
Subdivision Surface modifier enters the picture: the control cage and the
actual smoothed result are different meshes with different vertex/face
counts, and the topology problems that actually matter for subdivision
work (pinching, curvature discontinuity) only exist in the EVALUATED
result, invisible to every tool built before this one.

Uses bpy's own dependency graph (the same evaluation Blender's viewport
uses), not a reimplementation of Catmull-Clark or any other subdivision
algorithm -- so this reports exactly what the modifier stack actually
produces, not an approximation of it.
"""

import math

import bpy
import bmesh
import mathutils

try:
    from . import bmesh_io
except ImportError:
    import bmesh_io


def _read_evaluated_bmesh(obj):
    """Returns (bm, cleanup_fn). Caller must call cleanup_fn() when done --
    the evaluated mesh is a temporary datablock that must be explicitly
    freed (to_mesh_clear()), unlike obj.data which Blender owns."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh_eval)

    def cleanup():
        bm.free()
        obj_eval.to_mesh_clear()

    return bm, cleanup


def evaluated_mesh_health(name):
    """Same shape as state_probe.mesh_health(), but on the evaluated
    (post-modifier) mesh -- what the surface actually looks like, not the
    control cage that produces it."""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        return {
            "vertices": len(bm.verts),
            "edges": len(bm.edges),
            "faces": len(bm.faces),
            "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
            "ngons": sum(1 for f in bm.faces if len(f.verts) > 4),
            "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
            "degenerate_faces": sum(1 for f in bm.faces if f.calc_area() < 1e-8),
        }
    finally:
        cleanup()


def evaluated_valence_distribution(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        bm.verts.ensure_lookup_table()
        dist = {}
        for v in bm.verts:
            val = len(v.link_edges)
            dist[val] = dist.get(val, 0) + 1
        return dist
    finally:
        cleanup()


def evaluated_surface_quality(name):
    """Signals aimed specifically at spotting subdivision pinching, which
    doesn't show up as a validity failure (still 0 non-manifold, 0
    degenerate) -- it shows up as an unusually tight CLUSTER of very small,
    similarly-angled faces where the surface should be flowing smoothly.

    face_area_ratio alone (already used for hard-surface work) is a weak
    signal here since subdivided surfaces naturally have many small faces
    everywhere, not just at defects -- what's diagnostic for pinching is
    the presence of a face-area OUTLIER cluster (a few faces far smaller
    than the local median, not just smaller than the global max), and
    sharp normal-angle changes between adjacent faces in a region that's
    supposed to be a smooth continuous surface. Reports both rather than
    just the same min/max ratio already available elsewhere.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        bm.faces.ensure_lookup_table()
        areas = [f.calc_area() for f in bm.faces]
        areas_nonzero = sorted(a for a in areas if a > 1e-9)
        if not areas_nonzero:
            return {"error": "no non-degenerate faces on evaluated mesh"}
        median = areas_nonzero[len(areas_nonzero) // 2]
        outliers = [a for a in areas_nonzero if median > 1e-9 and a < median * 0.05]

        max_angle = 0.0
        angle_samples = 0
        for e in bm.edges:
            if len(e.link_faces) == 2:
                angle = e.calc_face_angle(0.0)
                max_angle = max(max_angle, angle)
                angle_samples += 1

        return {
            "face_count": len(areas),
            "min_area": round(min(areas_nonzero), 8),
            "max_area": round(max(areas_nonzero), 6),
            "median_area": round(median, 6),
            "area_outlier_count": len(outliers),
            "area_outlier_ratio": round(len(outliers) / len(areas_nonzero), 4) if areas_nonzero else 0,
            "max_adjacent_face_angle_radians": round(max_angle, 4),
            "angle_samples": angle_samples,
        }
    finally:
        cleanup()


def evaluated_surface_diagnostics(name, outlier_z_threshold=6.0):
    """Report scale-normalized local surface concentration and oscillation signals.

    This strengthens, but does not replace, visual judgment. A local Laplacian normal displacement
    that is an extreme robust outlier is a pinching candidate. Repeated sign changes in meaningful
    signed displacement are a waviness candidate. Results are descriptive with explicit thresholds;
    topology boundaries and intentional corrugation can produce the same signals.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}
    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.normal_update()
        edge_lengths = sorted(edge.calc_length() for edge in bm.edges if edge.calc_length() > 1e-9)
        if not edge_lengths:
            return {"error": "evaluated mesh has no measurable edges"}
        median_edge = edge_lengths[len(edge_lengths) // 2]
        samples = []
        for vert in bm.verts:
            neighbors = [edge.other_vert(vert) for edge in vert.link_edges]
            if len(neighbors) < 2:
                continue
            mean = sum((neighbor.co for neighbor in neighbors), mathutils.Vector()) / len(neighbors)
            laplacian = vert.co - mean
            signed = laplacian.dot(vert.normal) / median_edge
            normal_angles = [vert.normal.angle(neighbor.normal, 0.0) for neighbor in neighbors]
            samples.append({
                "index": vert.index,
                "position": list(vert.co),
                "signed_laplacian": signed,
                "absolute_laplacian": abs(signed),
                "mean_neighbor_normal_angle": sum(normal_angles) / len(normal_angles),
            })
        if not samples:
            return {"error": "no evaluable vertices"}
        absolute = sorted(item["absolute_laplacian"] for item in samples)
        median = absolute[len(absolute) // 2]
        deviations = sorted(abs(value - median) for value in absolute)
        mad = deviations[len(deviations) // 2]
        robust_scale = max(1.4826 * mad, median * 0.05, 1e-6)
        for item in samples:
            item["robust_outlier_z"] = (item["absolute_laplacian"] - median) / robust_scale
        outliers = [item for item in samples if item["robust_outlier_z"] >= outlier_z_threshold]
        outliers.sort(key=lambda item: item["robust_outlier_z"], reverse=True)

        signed_by_index = {item["index"]: item["signed_laplacian"] for item in samples}
        meaningful = max(median * 0.5, 0.02)
        sign_edges = 0
        sign_changes = 0
        for edge in bm.edges:
            a = signed_by_index.get(edge.verts[0].index)
            b = signed_by_index.get(edge.verts[1].index)
            if a is None or b is None or min(abs(a), abs(b)) < meaningful:
                continue
            sign_edges += 1
            sign_changes += int(a * b < 0)
        normal_angles = sorted(item["mean_neighbor_normal_angle"] for item in samples)
        p95_index = min(len(normal_angles) - 1, int(len(normal_angles) * 0.95))
        return {
            "vertex_samples": len(samples),
            "median_edge_length": round(median_edge, 8),
            "median_absolute_laplacian": round(median, 8),
            "laplacian_mad": round(mad, 8),
            "max_robust_outlier_z": round(max(item["robust_outlier_z"] for item in samples), 4),
            "pinch_candidate_count": len(outliers),
            "pinch_candidates": [
                {
                    "evaluated_vertex_index": item["index"],
                    "position": [round(value, 5) for value in item["position"]],
                    "robust_outlier_z": round(item["robust_outlier_z"], 4),
                    "signed_laplacian": round(item["signed_laplacian"], 6),
                }
                for item in outliers[:20]
            ],
            "meaningful_signed_edges": sign_edges,
            "laplacian_sign_change_ratio": round(sign_changes / sign_edges, 6) if sign_edges else 0.0,
            "mean_neighbor_normal_angle_p95_degrees": round(math.degrees(normal_angles[p95_index]), 4),
            "classification": "CANDIDATE_EVIDENCE_ONLY",
            "limitations": [
                "boundaries and intentional corrugation can resemble defects",
                "thresholds require validation by surface family and render/highlight inspection",
            ],
        }
    finally:
        cleanup()


def bounding_box_comparison(name):
    """Compare the base control cage's own bounding box to the modifier-
    evaluated result's bounding box, in local space.

    Exists for a specific, real judgment a plain area/angle check can't
    make: Catmull-Clark subdivision without support loops near a corner
    pulls the evaluated surface inward from that corner (the well-known
    "beach ball" shrinkage), which can quietly erode the intended silhouette
    proportions even when every other validity/pinching signal reads clean
    -- 0 non-manifold, 0 area outliers, a moderate max adjacent-face angle
    can all still coexist with a shape that's noticeably smaller/rounder
    than the control cage that was supposedly built to spec. shrinkage_ratio
    close to 1.0 on an axis means that axis's extent survived subdivision
    intact; a low ratio (e.g. under ~0.9) on an axis that's supposed to read
    as a firm silhouette edge is the concrete, local signal a support loop
    is missing there -- not just a vague "does this look rounded enough"
    impression.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}

    base_coords = [v.co for v in obj.data.vertices]
    if not base_coords:
        return {"error": f"'{name}' has no vertices"}
    base_min = [min(c[i] for c in base_coords) for i in range(3)]
    base_max = [max(c[i] for c in base_coords) for i in range(3)]

    bm, cleanup = _read_evaluated_bmesh(obj)
    try:
        eval_coords = [v.co for v in bm.verts]
        if not eval_coords:
            return {"error": "evaluated mesh has no vertices"}
        eval_min = [min(c[i] for c in eval_coords) for i in range(3)]
        eval_max = [max(c[i] for c in eval_coords) for i in range(3)]
    finally:
        cleanup()

    base_dims = [base_max[i] - base_min[i] for i in range(3)]
    eval_dims = [eval_max[i] - eval_min[i] for i in range(3)]
    shrinkage_ratio = [
        round(eval_dims[i] / base_dims[i], 4) if base_dims[i] > 1e-9 else None
        for i in range(3)
    ]

    return {
        "base_dimensions": [round(d, 4) for d in base_dims],
        "evaluated_dimensions": [round(d, 4) for d in eval_dims],
        "shrinkage_ratio_xyz": shrinkage_ratio,
        "base_bounds": {"min": [round(c, 4) for c in base_min], "max": [round(c, 4) for c in base_max]},
        "evaluated_bounds": {"min": [round(c, 4) for c in eval_min], "max": [round(c, 4) for c in eval_max]},
    }


def evaluated_defect_regions(name, area_outlier_ratio=0.05, angle_threshold_degrees=10, angle_local_spike_ratio=2.0, max_tickets=20):
    """Localize SubD surface defects, not just count them (directive
    section 8): evaluated_surface_quality can say "area_outlier_count: 3"
    or report one global max_adjacent_face_angle, but neither says WHERE --
    a modeler (or this system) needs to know which part of the control cage
    to actually go fix.

    For each individual outlier face / high-curvature-discontinuity edge on
    the EVALUATED mesh, finds its real position, then reports the nearest
    persistent-ID vertices/faces on the BASE control cage by straight
    spatial distance (evaluated-mesh vertex coordinates from
    obj.evaluated_get().to_mesh() are in the same local space as obj.data,
    confirmed by bounding_box_comparison's own working use of both without
    a matrix_world conversion between them -- so this is a direct, valid
    comparison, not an approximation across coordinate spaces).

    Deliberately NOT exact 1:1 evaluated-to-base vertex identity -- the
    evaluated mesh has no persistent IDs of its own and subdivision doesn't
    have a single canonical parent-vertex mapping worth relying on. Spatial
    nearest-neighbor is what the directive itself says is sufficient: "It
    does not need perfect one-to-one evaluated vertex identity. It needs
    enough spatial correspondence to create actionable local repair
    tickets."

    angle_threshold_degrees is a floor (skip near-flat edges entirely, not
    a defect cutoff by itself) -- an edge only becomes a "high_angle"
    ticket if its angle also exceeds angle_local_spike_ratio times the
    average angle of its own immediately neighboring edges, i.e. a real
    local discontinuity, not just a high value in the mesh's global
    population. See the inline correction below for why: a first version
    using angle_threshold_degrees as an absolute cutoff produced 144 false
    positives on the known-clean SoapDish, whose rounded corners legitimately
    have a smooth gradient up to ~46deg with no discontinuity anywhere.

    HONEST LIMITATION, found testing the local-ratio fix, not glossed over:
    it still doesn't cleanly separate "healthy smooth curvature" from real
    pinching. Tested against a deliberately built bad case (a cube with one
    face subdivided at a mismatched resolution vs its neighbors -- the same
    defect class documented in the SoapDish rim n-gon issue) and the
    resulting max severity (~2.65) landed in the SAME range as SoapDish's
    own healthy severity scores (up to 3.0), not clearly higher. The root
    issue: comparing an edge to its immediate neighbors' average flags ANY
    local curvature peak, healthy or not -- a smooth bump's apex always
    "outshines" the edges on its own rising/falling slope by construction,
    independent of whether the bump is a good rounded corner or a bad
    pinch. A more correct signal would likely need to measure whether
    elevated curvature is CONCENTRATED into an abnormally small area
    relative to how much surface it affects (closer to how area_outlier
    already works) rather than a simple neighbor-ratio -- not attempted
    here. Treat this function's tickets as ranked CANDIDATE locations worth
    a closer look (numeric triage, narrowing down where to render/inspect
    next), not as confirmed defects -- matching the directive's own
    observation (section 37) that this kind of judgment is normally a
    visual task for a human modeler, not something fully reducible to a
    single clean threshold.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return {"error": f"'{name}' is not a mesh object"}

    bm, cleanup = _read_evaluated_bmesh(obj)
    tickets = []
    try:
        bm.faces.ensure_lookup_table()
        areas = [(f, f.calc_area()) for f in bm.faces]
        areas_nonzero = sorted(a for _, a in areas if a > 1e-9)
        median = areas_nonzero[len(areas_nonzero) // 2] if areas_nonzero else 0.0
        for f, a in areas:
            if median > 1e-9 and 0 < a < median * area_outlier_ratio:
                tickets.append({
                    "type": "area_outlier",
                    "position": list(f.calc_center_median()),
                    "severity": round(1.0 - (a / (median * area_outlier_ratio)), 4),
                    "area": round(a, 8), "median_area": round(median, 6),
                })

        # CORRECTION (found live, first real test against the known-clean
        # SoapDish): an ABSOLUTE angle threshold is wrong for this. Direct
        # measurement showed SoapDish's evaluated edge angles form a smooth,
        # continuous gradient from ~0deg up to ~46deg at its rounded
        # corners (median 3.7deg, 90th percentile 42deg, 99th 44.8deg) --
        # normal, healthy Catmull-Clark rounding across a smoothly curved
        # surface, not isolated pinch points. A flat 25deg cutoff flagged
        # 144 "defects" on a mesh already independently confirmed clean
        # (0 area outliers, poles only at expected corners) -- pure false
        # positives from treating "in the top percentile of the whole
        # mesh" as equivalent to "a localized spike," which it is not:
        # a whole rounded edge legitimately having uniformly elevated
        # angles together is the healthy case, exactly what "rounded"
        # means geometrically. Real pinching is a DISCONTINUITY -- one
        # edge's angle standing out sharply from its own immediate
        # neighbors' angles, not from the mesh's global population. Compare
        # each edge against the local average of edges sharing one of its
        # two vertices instead, mirroring how area_outlier already compares
        # against a local median rather than an absolute area.
        bm.edges.ensure_lookup_table()
        edge_angles = {}
        for e in bm.edges:
            if len(e.link_faces) == 2:
                edge_angles[e.index] = e.calc_face_angle(0.0)
        angle_min = math.radians(angle_threshold_degrees)
        for e in bm.edges:
            angle = edge_angles.get(e.index)
            if angle is None or angle < angle_min:
                continue
            neighbor_angles = [
                edge_angles[ne.index]
                for v in e.verts for ne in v.link_edges
                if ne.index != e.index and ne.index in edge_angles
            ]
            if not neighbor_angles:
                continue
            local_avg = sum(neighbor_angles) / len(neighbor_angles)
            if local_avg > 1e-6 and angle > local_avg * angle_local_spike_ratio:
                mid = (e.verts[0].co + e.verts[1].co) / 2.0
                tickets.append({
                    "type": "high_angle",
                    "position": list(mid),
                    "severity": round(angle / local_avg, 4),
                    "angle_degrees": round(math.degrees(angle), 2),
                    "local_neighbor_avg_degrees": round(math.degrees(local_avg), 2),
                })
    finally:
        cleanup()

    tickets.sort(key=lambda t: t["severity"], reverse=True)
    total_found = len(tickets)
    tickets = tickets[:max_tickets]

    base_bm = bmesh_io.read_bmesh(obj)
    base_bm.verts.ensure_lookup_table()
    base_bm.faces.ensure_lookup_table()
    vert_layer = base_bm.verts.layers.int.get("agent_vertex_id")
    face_layer = base_bm.faces.layers.int.get("agent_face_id")

    for t in tickets:
        pos = mathutils.Vector(t["position"])
        vert_dists = []
        if vert_layer is not None:
            for v in base_bm.verts:
                vid = v[vert_layer]
                if vid != 0:
                    vert_dists.append((round((v.co - pos).length, 4), vid))
        face_dists = []
        if face_layer is not None:
            for f in base_bm.faces:
                fid = f[face_layer]
                if fid != 0:
                    face_dists.append((round((f.calc_center_median() - pos).length, 4), fid))
        vert_dists.sort(key=lambda x: x[0])
        face_dists.sort(key=lambda x: x[0])
        t["position"] = [round(c, 4) for c in t["position"]]
        t["nearby_cage_verts"] = [{"agent_id": vid, "distance": d} for d, vid in vert_dists[:3]]
        t["nearby_cage_faces"] = [{"agent_id": fid, "distance": d} for d, fid in face_dists[:3]]

        # A control-cage pole (valence != 4) has genuinely reduced
        # smoothness in Catmull-Clark's own limit surface -- a known,
        # unavoidable mathematical property of the algorithm at
        # extraordinary vertices, not evidence of bad support-loop
        # placement. Flag it so the caller can apply the same judgment
        # the master directive requires elsewhere (section 17/section 4.2:
        # "explicitly warns against treating every non-4-valence vertex as
        # a defect... inspect... judge context"), rather than this tool
        # silently pretending to auto-classify pinching with certainty it
        # doesn't have.
        if vert_dists:
            nearest_id = vert_dists[0][1]
            nearest_vert = None
            for v in base_bm.verts:
                if vert_layer is not None and v[vert_layer] == nearest_id:
                    nearest_vert = v
                    break
            if nearest_vert is not None:
                valence = len(nearest_vert.link_edges)
                t["nearest_cage_vertex_valence"] = valence
                t["likely_pole_artifact"] = valence != 4

    if obj.mode != "EDIT":
        base_bm.free()

    return {"defect_count_total": total_found, "tickets_returned": len(tickets), "tickets": tickets}
