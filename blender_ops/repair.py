import mesh_ops
import state_probe


def repair_non_manifold_from_boolean(name, merge_dist=0.0001):
    """Standard fix for non-manifold edges / stray n-gons left by a boolean
    DIFFERENCE cut: merge coincident verts at the seam, recalc normals, then
    triangulate whatever n-gons remain."""
    before = state_probe.mesh_health(name)
    mesh_ops.merge_by_distance(name, dist=merge_dist)
    mesh_ops.recalc_normals(name)
    mesh_ops.triangulate_ngons(name)
    after = state_probe.mesh_health(name)
    return {"before": before, "after": after}
