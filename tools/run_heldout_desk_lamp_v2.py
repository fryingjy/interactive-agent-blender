"""Second attempt at the held-out articulated desk-lamp benchmark.

The first attempt (runs/2026-08-12_heldout-desk-lamp/) was rejected: it never
came close to its frozen gates (best mean IoU 0.406 vs 0.66) because the arm's
paired rails were placed across depth, collapsing the side-view silhouette.
Its own conclusion: "The next attempt must begin with explicit side-view
rail/frame landmarks and component proportions rather than broad manual span
adjustments."

This attempt does exactly that. Landmarks below were read directly from
tools/measure_reference.py's row-profile output against
reference_side_mask.png and reference_front_mask.png (both already saved from
the first attempt; not re-downloaded or re-inspected as source geometry).
The front-view profile confirms the whole mechanism is nearly planar (max
width ~0.26 of total height in the depth axis), so the arm is built in one
X-Z plane with only minor Y-axis thickness, instead of guessing a pose.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from render_passes import render_silhouette  # noqa: E402

VIEWS = {"front": Vector((0, -1, 0)), "side": Vector((1, 0, 0)), "top": Vector((0, 0, 1)), "isometric": Vector((1, -1, .8)).normalized()}

# --- Landmarks measured from reference_side_mask.png (720x720), bbox x:[181,538] y:[100,619] ---
# Normalized within bbox, then mapped to world (x,z): x=(nx-0.5)*W, z=(1-ny)*H
W, H = 2.064, 3.0  # matches measured aspect_ratio_w_over_h = 0.6879


def to_world(nx, ny):
    return ((nx - 0.5) * W, (1 - ny) * H)


SHADE_TIP = to_world(0.756, 0.0)
SHADE_RIM_L = to_world(0.512, 0.164)
SHADE_RIM_R = to_world(0.986, 0.164)
SHADE_NECK = to_world(0.580, 0.245)
UPPER_ARM_TOP = to_world(0.417, 0.251)
ELBOW = to_world(0.022, 0.462)
BASE_JOINT = to_world(0.451, 0.794)
CLAMP_BOTTOM = to_world(0.493, 1.0)


def args():
    vals = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
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
    return [(i, 0) for i in range(n)] + [(n-1, j) for j in range(1, n)] + [(i, n-1) for i in range(n-2, -1, -1)] + [(0, j) for j in range(n-2, 0, -1)]


def disk(u, v):
    if abs(u) < 1e-9 and abs(v) < 1e-9:
        return 0., 0.
    if abs(u) > abs(v):
        r = u; t = math.pi/4*(v/u)
    else:
        r = v; t = math.pi/2 - math.pi/4*(u/v)
    return r*math.cos(t), r*math.sin(t)


def make_obj(name, verts, faces, col, material, props=None):
    me = bpy.data.meshes.new(name+"Mesh")
    me.from_pydata(verts, [], faces)
    me.materials.append(material)
    me.update(calc_edges=True)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    uv = me.uv_layers.new(name="UVMap")
    xs = [v.co.x for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    dx = max(xs)-min(xs) or 1; dz = max(zs)-min(zs) or 1
    for p in me.polygons:
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x-min(xs))/dx, (co.z-min(zs))/dz)
    if props:
        for k, v in props.items():
            ob[k] = v
    return ob


def path_loft(name, centers, radii, grid_n, col, material, up_hint=Vector((0, 0, 1)), props=None):
    bc = boundary(grid_n); verts = []; faces = []; rings = []; frames = []
    for k, c in enumerate(centers):
        tangent = (Vector(centers[min(k+1, len(centers)-1)]) - Vector(centers[max(k-1, 0)]))
        if tangent.length < 1e-9:
            tangent = Vector((0, 0, 1))
        tangent = tangent.normalized()
        bx = tangent.cross(up_hint)
        if bx.length < 1e-6:
            bx = Vector((0, 1, 0))
        bx = bx.normalized()
        by = tangent.cross(bx).normalized()
        frames.append((bx, by))
        ring = []
        for i, j in bc:
            u = -1+2*i/(grid_n-1); v = -1+2*j/(grid_n-1); a, b = disk(u, v)
            p = Vector(c) + (bx*a + by*b) * radii[k]
            ring.append(len(verts)); verts.append(tuple(p))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(len(a)):
            faces.append((a[k], a[(k+1) % len(a)], b[(k+1) % len(a)], b[k]))
    for ridx, outward in ((0, False), (len(rings)-1, True)):
        mp = {bc[k]: rings[ridx][k] for k in range(len(bc))}
        c = Vector(centers[ridx]); bx, by = frames[ridx]; r = radii[ridx]
        for j in range(1, grid_n-1):
            for i in range(1, grid_n-1):
                a, b = disk(-1+2*i/(grid_n-1), -1+2*j/(grid_n-1))
                mp[(i, j)] = len(verts); verts.append(tuple(c+(bx*a+by*b)*r))
        for j in range(grid_n-1):
            for i in range(grid_n-1):
                q = (mp[(i, j)], mp[(i+1, j)], mp[(i+1, j+1)], mp[(i, j+1)])
                faces.append(q if outward else tuple(reversed(q)))
    return make_obj(name, verts, faces, col, material, props)


def ring_loft(name, specs, grid_n, col, material, props=None):
    """specs: list of (center_xyz, radius) for a revolved profile around Z through given centers."""
    bc = boundary(grid_n); verts = []; faces = []; rings = []
    for c, r in specs:
        ring = []
        for i, j in bc:
            u = -1+2*i/(grid_n-1); v = -1+2*j/(grid_n-1); x, y = disk(u, v)
            ring.append(len(verts)); verts.append((c[0]+x*r, c[1]+y*r, c[2]))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(len(a)):
            faces.append((a[k], a[(k+1) % len(a)], b[(k+1) % len(a)], b[k]))
    for ridx, up in ((0, False), (len(rings)-1, True)):
        c, r = specs[ridx]
        mp = {bc[k]: rings[ridx][k] for k in range(len(bc))}
        for j in range(1, grid_n-1):
            for i in range(1, grid_n-1):
                x, y = disk(-1+2*i/(grid_n-1), -1+2*j/(grid_n-1))
                mp[(i, j)] = len(verts); verts.append((c[0]+x*r, c[1]+y*r, c[2]))
        for j in range(grid_n-1):
            for i in range(grid_n-1):
                q = (mp[(i, j)], mp[(i+1, j)], mp[(i+1, j+1)], mp[(i, j+1)])
                faces.append(q if up else tuple(reversed(q)))
    return make_obj(name, verts, faces, col, material, props)


def main():
    out = args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world = bpy.data.worlds.new("World"); world.use_nodes = True; bpy.context.scene.world = world
    col = bpy.context.scene.collection

    metal_dark = mat("Lamp Metal Dark", (0.05, 0.05, 0.06), metal=0.85, rough=0.35)
    metal_light = mat("Lamp Metal Light", (0.62, 0.62, 0.64), metal=0.7, rough=0.3)

    ax, az = ELBOW; bx_, bz = BASE_JOINT; cx, cz = CLAMP_BOTTOM
    ux, uz = UPPER_ARM_TOP
    nx, nz = SHADE_NECK

    # NOTE: the reference's full zigzag profile is its "side" view, which
    # render_silhouette's "side" looks along +X (seeing the YZ plane). So the
    # in-plane measured coordinate goes in Y here, not X -- X is reserved for
    # the small cross-axis thickness offset (twin-rail separation etc.).
    # This is exactly the axis mistake the first attempt made; getting it
    # backwards here would silently reproduce it.

    # Clamp base: short vertical post + horizontal foot, both thin tubes.
    clamp_post = path_loft(
        "Clamp_Post", [(0, cx, cz), (0, bx_, bz)], [0.035, 0.035], 8, col, metal_dark,
    )
    clamp_foot = path_loft(
        "Clamp_Foot", [(0, cx-0.22, cz+0.03), (0, cx+0.14, cz+0.03)], [0.03, 0.03], 8, col, metal_dark,
    )

    # Lower arm: base joint -> elbow. Reference front view shows this segment
    # as, top to bottom: a pinched neck near the elbow, a triangular funnel
    # flaring OUT (the scissor mechanism spreading), a wide rectangular
    # damper-cylinder block, then narrowing back down toward the clamp.
    # Widened throughout from the first pass: the front-view comparison
    # showed low recall (0.385) with decent precision (0.599) -- the whole
    # candidate was too thin, not misplaced.
    lower_arm_main = path_loft(
        "Lower_Arm_Main", [(0, bx_, bz), (0, ax, az)], [0.06, 0.05], 8, col, metal_light,
    )
    fx0, fz0 = bx_ + (ax-bx_)*0.12, bz + (az-bz)*0.12
    fx1, fz1 = bx_ + (ax-bx_)*0.32, bz + (az-bz)*0.32
    fx2, fz2 = bx_ + (ax-bx_)*0.68, bz + (az-bz)*0.68
    lower_arm_funnel = ring_loft(
        "Lower_Arm_Funnel",
        [((0, fx0, fz0), 0.035), ((0, fx1, fz1), 0.10), ((0, fx2, fz2), 0.10)],
        8, col, metal_dark,
    )
    lower_arm_damper = path_loft(
        "Lower_Arm_Damper",
        [(0.08, bx_ + (ax-bx_)*0.15, bz + (az-bz)*0.15), (0.08, bx_ + (ax-bx_)*0.75, bz + (az-bz)*0.75)],
        [0.07, 0.07], 8, col, metal_dark,
    )

    elbow_joint = path_loft("Elbow_Joint", [(-0.08, ax, az), (0.08, ax, az)], [0.11, 0.11], 8, col, metal_dark)

    # Upper arm: elbow -> shade mount, straight parallel twin rail.
    upper_arm_main = path_loft(
        "Upper_Arm_Main", [(0, ax, az), (0, ux, uz)], [0.055, 0.045], 8, col, metal_light,
    )
    upper_arm_rail2 = path_loft(
        "Upper_Arm_Rail2",
        [(0.07, ax, az), (0.07, ux, uz)], [0.032, 0.026], 8, col, metal_light,
    )

    shade_joint = path_loft("Shade_Joint", [(-0.05, ux, uz), (0.05, ux, uz)], [0.06, 0.06], 8, col, metal_dark)

    # Shade: revolved frustum from a small neck up to the wide rim, then a
    # short back wall up to the tip -- matches the reference's cone-with-cap
    # profile (wide rim at z=SHADE_RIM z, narrowing to a small vented cap).
    rim_r = (SHADE_RIM_R[0] - SHADE_RIM_L[0]) / 2
    rim_center = (0.0, (SHADE_RIM_L[0]+SHADE_RIM_R[0])/2, SHADE_RIM_L[1])
    tip_y, tip_z = SHADE_TIP
    shade = ring_loft(
        "Shade",
        [
            (rim_center, rim_r),
            ((0, rim_center[1]*0.55+tip_y*0.45, rim_center[2]*0.35+tip_z*0.65), rim_r*0.22),
            ((0, tip_y, tip_z), rim_r*0.12),
        ],
        10, col, metal_dark,
        props={"assembly_reason": "separate serviceable shade component, articulates independently"},
    )

    for ob in (clamp_post, clamp_foot, lower_arm_main, lower_arm_funnel, lower_arm_damper, elbow_joint,
               upper_arm_main, upper_arm_rail2, shade_joint, shade):
        ob["source_absent"] = True

    bpy.ops.object.select_all(action="SELECT")
    all_objs = list(bpy.context.selected_objects)
    all_names = [ob.name for ob in all_objs]

    masks = {}
    for view in ("front", "side", "top", "isometric"):
        mask_path = out / f"candidate_{view}_mask.png"
        result = render_silhouette(all_names, str(mask_path), view=view, resolution=768)
        masks[view] = {"path": str(mask_path), "result": result}

    bpy.ops.wm.save_as_mainfile(filepath=str(out / "heldout_desk_lamp_v2.blend"))

    verts_total = sum(len(ob.data.vertices) for ob in all_objs)
    faces_total = sum(len(ob.data.polygons) for ob in all_objs)
    report = {
        "blender_version": bpy.app.version_string,
        "object_count": len(all_objs),
        "object_names": [ob.name for ob in all_objs],
        "base_vertices": verts_total,
        "base_faces": faces_total,
        "masks": masks,
        "landmarks_world": {
            "shade_tip": SHADE_TIP, "shade_rim_l": SHADE_RIM_L, "shade_rim_r": SHADE_RIM_R,
            "shade_neck": SHADE_NECK, "upper_arm_top": UPPER_ARM_TOP, "elbow": ELBOW,
            "base_joint": BASE_JOINT, "clamp_bottom": CLAMP_BOTTOM,
        },
    }
    (out / "candidate_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
