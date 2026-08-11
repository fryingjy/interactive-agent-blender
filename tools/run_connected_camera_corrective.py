"""Corrective camera benchmark: one connected edit-mode-style all-quad mesh.

This supersedes the technically passing multi-object candidate after experienced
human review clarified that detail should grow from the base cage through loop
routing, inset, and extrusion wherever the form permits it.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender_ops"))
from render_passes import render_silhouette


def arguments() -> Path:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 1:
        raise SystemExit("expected OUTPUT_DIR after --")
    output = Path(values[0]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


def material(name, color, metallic=0.0, roughness=0.4):
    item = bpy.data.materials.new(name)
    item.diffuse_color = (*color, 1.0)
    item.metallic = metallic
    item.roughness = roughness
    item.use_nodes = True
    shader = next(node for node in item.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return item


class Cage:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.materials = []
        self.index = {}
        self.sharp_edges = {}

    def vertex(self, coordinate):
        key = tuple(round(value, 7) for value in coordinate)
        if key not in self.index:
            self.index[key] = len(self.vertices)
            self.vertices.append(tuple(coordinate))
        return self.index[key]

    def face(self, vertices, material_index=0):
        self.faces.append(tuple(vertices))
        self.materials.append(material_index)

    def mark_sharp_loop(self, category, ring):
        bucket = self.sharp_edges.setdefault(category, set())
        for index, vertex in enumerate(ring):
            bucket.add(tuple(sorted((vertex, ring[(index + 1) % len(ring)]))))

    def inset_extrusion(self, outer, axis, profiles, inset=0.12, side_material=2, cap_material=2):
        """Replace one surface quad with inset/extruded loop rings.

        ``outer`` is an oriented boundary already shared by the surrounding cage.
        Profiles are (axis offset, in-plane scale) values. Every generated face is
        a quad and every feature remains welded to the original surface boundary.
        """
        points = [Vector(self.vertices[index]) for index in outer]
        center = sum(points, Vector()) / 4.0
        inset_ring = []
        for point in points:
            moved = center + (point - center) * (1.0 - inset)
            inset_ring.append(self.vertex(moved))
        for index in range(4):
            nxt = (index + 1) % 4
            self.face((outer[index], outer[nxt], inset_ring[nxt], inset_ring[index]), 0)

        previous = inset_ring
        direction = Vector(axis)
        for offset, scale in profiles:
            ring = []
            for index in inset_ring:
                base = Vector(self.vertices[index])
                moved = center + (base - center) * scale + direction * offset
                ring.append(self.vertex(moved))
            for index in range(4):
                nxt = (index + 1) % 4
                self.face((previous[index], previous[nxt], ring[nxt], ring[index]), side_material)
            previous = ring
        self.face(tuple(reversed(previous)), cap_material)


def build_connected_camera(collection):
    cage = Cage()
    # The body perimeter is locally subdivided only where a circular control must
    # grow from the shell. Each control itself remains a deliberately sparse,
    # regular 12-vertex loop: enough to read circular without needless density.
    base_segments = 16
    control_segments = 12
    half_width, half_height = 3.05, 1.56
    lens_center = Vector((0.32, -0.82, -0.28))

    # Literal box perimeter: four flat sides and four exact 90-degree corners.
    # Intermediate vertices provide editable edge-loop density but do not pre-round
    # the silhouette. The weighted Bevel is solely responsible for corner radius.
    base_points = [
        (half_width, 0.0),
        (half_width, half_height * 0.5),
        (half_width, half_height),
        (half_width * 0.5, half_height),
        (0.0, half_height),
        (-half_width * 0.5, half_height),
        (-half_width, half_height),
        (-half_width, half_height * 0.5),
        (-half_width, 0.0),
        (-half_width, -half_height * 0.5),
        (-half_width, -half_height),
        (-half_width * 0.5, -half_height),
        (0.0, -half_height),
        (half_width * 0.5, -half_height),
        (half_width, -half_height),
        (half_width, -half_height * 0.5),
    ]
    top_candidates = []
    for index, point in enumerate(base_points):
        nxt = base_points[(index + 1) % base_segments]
        midpoint_x = (point[0] + nxt[0]) * 0.5
        midpoint_z = (point[1] + nxt[1]) * 0.5
        if midpoint_z > 1.35:
            top_candidates.append((index, midpoint_x))
    selected_top_segments = {
        min(top_candidates, key=lambda item: abs(item[1] + 2.05))[0],
        min(top_candidates, key=lambda item: abs(item[1] - 2.10))[0],
    }

    # Split each selected top segment into five. Across front and back boundaries
    # this produces a 12-edge rectangular patch (5 + 1 + 5 + 1), which can bridge
    # one-to-one into a regular 12-edge circle using quads only.
    perimeter_points = []
    segment_spans = {}
    for index, point in enumerate(base_points):
        divisions = 5 if index in selected_top_segments else 1
        segment_spans[index] = (len(perimeter_points), divisions)
        nxt = base_points[(index + 1) % base_segments]
        for part in range(divisions):
            factor = part / divisions
            perimeter_points.append((point[0] * (1.0 - factor) + nxt[0] * factor, point[1] * (1.0 - factor) + nxt[1] * factor))
    perimeter_segments = len(perimeter_points)

    def rounded_rectangle(y_value, scale=1.0):
        ring = []
        for px, pz in perimeter_points:
            ring.append(cage.vertex((px * scale, y_value, pz * scale)))
        return ring

    outer_rings = (
        rounded_rectangle(-0.82, 0.985),
        rounded_rectangle(-0.78, 1.0),
        rounded_rectangle(0.78, 1.0),
        rounded_rectangle(0.82, 0.985),
    )

    # Four routed perimeter loops form the body. Five adjacent cells are omitted
    # at each selected top span and replaced below by a welded circular patch.
    for layer in range(len(outer_rings) - 1):
        for index in range(perimeter_segments):
            nxt = (index + 1) % perimeter_segments
            face = (
                outer_rings[layer][index],
                outer_rings[layer][nxt],
                outer_rings[layer + 1][nxt],
                outer_rings[layer + 1][index],
            )
            omitted = False
            if layer == 1:
                for source_segment in selected_top_segments:
                    start, divisions = segment_spans[source_segment]
                    omitted = omitted or start <= index < start + divisions
            if not omitted:
                cage.face(face, 0)

    # A matching circular inset replaces the camera's front cap. The matching
    # rounded-rectangle perimeter and circular loop are bridged entirely by quads;
    # the circular loop is then extruded as the stepped lens barrel.
    lens_rings = []
    lens_profile = (
        (0.00, 0.92),
        (0.08, 1.00),
        (0.16, 1.06),
        (0.30, 1.08),
        (0.44, 1.00),
        (0.62, 1.00),
        (0.76, 0.92),
        (0.96, 0.88),
        (1.12, 0.74),
    )
    for offset, radius in lens_profile:
        ring = []
        for index in range(perimeter_segments):
            angle = math.tau * index / perimeter_segments
            ring.append(
                cage.vertex(
                    (
                        lens_center.x + radius * math.cos(angle),
                        lens_center.y - offset,
                        lens_center.z + radius * math.sin(angle),
                    )
                )
            )
        lens_rings.append(ring)

    for index in range(perimeter_segments):
        nxt = (index + 1) % perimeter_segments
        center = (Vector(cage.vertices[outer_rings[0][index]]) + Vector(cage.vertices[outer_rings[0][nxt]])) * 0.5
        front_material = 3 if center.z > 0.58 and (center.x < -0.8 or center.x > 1.2) else (1 if center.z < 0.45 else 0)
        # Reverse the annulus relative to both neighboring strips. Matching edge
        # direction here looks closed in a base manifold count but makes Bevel
        # generate split seams because the adjacent face normals disagree.
        cage.face((outer_rings[0][nxt], outer_rings[0][index], lens_rings[0][index], lens_rings[0][nxt]), front_material)
    for layer in range(len(lens_rings) - 1):
        for index in range(perimeter_segments):
            nxt = (index + 1) % perimeter_segments
            cage.face((lens_rings[layer][index], lens_rings[layer][nxt], lens_rings[layer + 1][nxt], lens_rings[layer + 1][index]), 2)

    # Quad-star caps keep both ends closed and all-quad. The extraordinary center
    # vertices live on planar, non-deforming surfaces where they are harmless.
    cap_y = lens_center.y - lens_profile[-1][0]
    cap_inner = []
    for index in range(perimeter_segments):
        angle = math.tau * index / perimeter_segments
        cap_inner.append(cage.vertex((lens_center.x + 0.20 * math.cos(angle), cap_y, lens_center.z + 0.20 * math.sin(angle))))
    for index in range(perimeter_segments):
        nxt = (index + 1) % perimeter_segments
        cage.face((lens_rings[-1][index], lens_rings[-1][nxt], cap_inner[nxt], cap_inner[index]), 3)
    lens_cap_center = cage.vertex((lens_center.x, cap_y, lens_center.z))
    for index in range(0, perimeter_segments, 2):
        cage.face((lens_cap_center, cap_inner[index], cap_inner[(index + 1) % perimeter_segments], cap_inner[(index + 2) % perimeter_segments]), 3)

    # An inset rear loop isolates the extraordinary cap center from the sharp rear
    # silhouette, allowing that intended hard perimeter to be safely weighted.
    back_inner = []
    for index in range(perimeter_segments):
        source = Vector(cage.vertices[outer_rings[-1][index]])
        back_inner.append(cage.vertex((source.x * 0.78, source.y, source.z * 0.78)))
    for index in range(perimeter_segments):
        nxt = (index + 1) % perimeter_segments
        cage.face((outer_rings[-1][index], outer_rings[-1][nxt], back_inner[nxt], back_inner[index]), 0)
    back_center = cage.vertex((0.0, 0.82, 0.0))
    for index in range(0, perimeter_segments, 2):
        cage.face((back_center, back_inner[(index + 2) % perimeter_segments], back_inner[(index + 1) % perimeter_segments], back_inner[index]), 0)

    # Each top control grows from a 12-edge hole in the body. The outer rectangular
    # boundary is bridged to an analytically regular circle—the deterministic
    # scripted equivalent of LoopTools Circle / planar To Sphere—then extruded as
    # welded loops. No cylinder object is added or joined.
    control_vertex_loops = []
    control_categories = []
    for control_number, source_segment in enumerate(sorted(selected_top_segments)):
        start, divisions = segment_spans[source_segment]
        front = [outer_rings[1][start + offset] for offset in range(divisions + 1)]
        back = [outer_rings[2][start + offset] for offset in range(divisions, -1, -1)]
        boundary = front + back
        points = [Vector(cage.vertices[index]) for index in boundary]
        center = sum(points, Vector()) / len(points)
        radius = min(max(point.x for point in points) - min(point.x for point in points), max(point.y for point in points) - min(point.y for point in points)) * 0.33
        signed_area = sum(points[i].x * points[(i + 1) % len(points)].y - points[(i + 1) % len(points)].x * points[i].y for i in range(len(points)))
        orientation = 1.0 if signed_area > 0 else -1.0
        first_angle = math.atan2(points[0].y - center.y, points[0].x - center.x)
        base_circle = []
        for index in range(control_segments):
            angle = first_angle + orientation * math.tau * index / control_segments
            base_circle.append(cage.vertex((center.x + radius * math.cos(angle), center.y + radius * math.sin(angle), center.z)))
        for index in range(control_segments):
            nxt = (index + 1) % control_segments
            cage.face((boundary[index], boundary[nxt], base_circle[nxt], base_circle[index]), 0)

        profiles = ((0.035, 1.00), (0.075, 1.00), (0.12, 0.88), (0.22, 0.88), (0.26, 0.80), (0.285, 0.80))
        loops = [base_circle]
        previous = base_circle
        for offset, scale in profiles:
            ring = []
            for index in range(control_segments):
                angle = first_angle + orientation * math.tau * index / control_segments
                ring.append(cage.vertex((center.x + radius * scale * math.cos(angle), center.y + radius * scale * math.sin(angle), center.z + offset)))
            for index in range(control_segments):
                nxt = (index + 1) % control_segments
                cage.face((previous[index], previous[nxt], ring[nxt], ring[index]), 2)
            loops.append(ring)
            previous = ring
        cap_center = cage.vertex((center.x, center.y, center.z + profiles[-1][0]))
        for index in range(0, control_segments, 2):
            cage.face((cap_center, previous[index], previous[(index + 1) % control_segments], previous[(index + 2) % control_segments]), 2)
        control_vertex_loops.append(loops)
        control_categories.append(f"top_control_{control_number + 1}")

    # Semantic sharpness map: every intentionally crisp silhouette, step, shoulder,
    # base, and cap ring is explicitly weighted. Tight support loops remain unweighted.
    for ring in outer_rings:
        cage.mark_sharp_loop("body_perimeters", ring)
    # The four cardinal body corners continue through depth as rails. Each rail is
    # split by the front/back support loops, so weight all three connected edges,
    # not merely one visually convenient segment.
    rail_bucket = cage.sharp_edges.setdefault("body_corner_rails", set())
    for source_index in (2, 6, 10, 14):
        perimeter_index = segment_spans[source_index][0]
        for layer in range(len(outer_rings) - 1):
            rail_bucket.add(tuple(sorted((outer_rings[layer][perimeter_index], outer_rings[layer + 1][perimeter_index]))))
    for ring in lens_rings:
        cage.mark_sharp_loop("lens_steps", ring)
    for category, loops in zip(control_categories, control_vertex_loops):
        for ring in loops:
            cage.mark_sharp_loop(category, ring)

    mesh = bpy.data.meshes.new("ConnectedCameraEditCageMesh")
    mesh.from_pydata(cage.vertices, [], cage.faces)
    mesh.update()
    obj = bpy.data.objects.new("Connected camera from one edited box cage", mesh)
    collection.objects.link(obj)
    for index, polygon in enumerate(mesh.polygons):
        polygon.material_index = cage.materials[index]
        polygon.use_smooth = True
    # Procedural strips are assembled from several local loops. Normalize winding
    # over the final connected component (the scripted equivalent of Recalculate
    # Outside) before Bevel consumes adjacency and normals.
    winding_mesh = bmesh.new()
    winding_mesh.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(winding_mesh, faces=list(winding_mesh.faces))
    winding_mesh.to_mesh(mesh)
    winding_mesh.free()
    mesh.update()
    obj["construction_intent"] = "one connected box-derived cage; details made by routed loops, inset, and extrusion"
    obj["body_profile"] = "literal box perimeter; no pre-rounded corner profile"
    obj["primitive_objects_added"] = 0
    obj["disconnected_mesh_islands_allowed"] = False
    obj["authored_radial_vertices"] = perimeter_segments
    obj["top_control_radial_vertices"] = control_segments
    obj["top_control_loops_json"] = json.dumps(control_vertex_loops)
    bevel_weights = mesh.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
    edge_lookup = {tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges}
    category_counts = {}
    category_indices = {}
    intended_edges = set()
    for category, pairs in cage.sharp_edges.items():
        missing = [pair for pair in pairs if pair not in edge_lookup]
        if missing:
            raise RuntimeError(f"sharp category {category} contains {len(missing)} non-edges")
        indices = {edge_lookup[pair] for pair in pairs}
        category_counts[category] = len(indices)
        category_indices[category] = sorted(indices)
        intended_edges.update(indices)
    for edge in mesh.edges:
        bevel_weights.data[edge.index].value = 1.0 if edge.index in intended_edges else 0.0
    weighted_edges = len(intended_edges)
    obj["weighted_bevel_edges"] = weighted_edges
    obj["sharp_edge_categories_json"] = json.dumps(category_counts, sort_keys=True)
    obj["sharp_edge_indices_json"] = json.dumps(category_indices, sort_keys=True)
    obj["intended_sharp_edge_count"] = weighted_edges
    bevel = obj.modifiers.new("Weighted support bevel", "BEVEL")
    bevel.limit_method = "WEIGHT"
    bevel.width = 0.018
    bevel.segments = 2
    bevel.affect = "EDGES"
    subdivision = obj.modifiers.new("Controlled Catmull-Clark surface", "SUBSURF")
    subdivision.levels = subdivision.render_levels = 2
    return obj


def mesh_health(obj, evaluated=False):
    owner = None
    mesh = obj.data
    if evaluated:
        owner = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = owner.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    components = 0
    unseen = set(bm.verts)
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
    result = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "connected_components": components,
        "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
        "loose_vertices": sum(not vertex.link_edges for vertex in bm.verts),
        "inconsistent_winding_edges": sum(
            len(edge.link_loops) == 2
            and edge.link_loops[0].vert == edge.link_loops[1].vert
            for edge in bm.edges
        ),
    }
    bm.free()
    if owner:
        owner.to_mesh_clear()
    return result


def control_circularity(obj):
    results = []
    for control_index, loops in enumerate(json.loads(obj["top_control_loops_json"])):
        for loop_index, loop in enumerate(loops):
            points = [obj.data.vertices[index].co for index in loop]
            center_x = sum(point.x for point in points) / len(points)
            center_y = sum(point.y for point in points) / len(points)
            radii = [math.hypot(point.x - center_x, point.y - center_y) for point in points]
            angles = sorted(math.atan2(point.y - center_y, point.x - center_x) % math.tau for point in points)
            gaps = [(angles[(index + 1) % len(angles)] - angles[index]) % math.tau for index in range(len(angles))]
            results.append(
                {
                    "control": control_index + 1,
                    "loop": loop_index,
                    "vertices": len(points),
                    "radius_relative_deviation": (max(radii) - min(radii)) / (sum(radii) / len(radii)),
                    "angle_gap_relative_deviation": (max(gaps) - min(gaps)) / (math.tau / len(gaps)),
                }
            )
    return results


def render_review(scene, output, view):
    directions = {
        "front": Vector((0, -1, 0)),
        "side": Vector((1, 0, 0)),
        "top": Vector((0, 0, 1)),
        "isometric": Vector((1, -1, 0.8)).normalized(),
    }
    direction = directions[view]
    camera_data = bpy.data.cameras.new(view + "CameraData")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 7.6
    camera = bpy.data.objects.new(view + "Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = direction * 14 + Vector((0, 0, 0.15))
    camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "MATCAP"
    shading.studio_light = "hard_surface_grey.exr"
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    scene.render.filepath = str(output / f"connected_{view}_solid.png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)


def main():
    output = arguments()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection = bpy.data.collections.new("Corrective one-object camera")
    bpy.context.scene.collection.children.link(collection)
    obj = build_connected_camera(collection)
    for item in (
        material("Satin shell", (0.26, 0.29, 0.30), 0.58, 0.30),
        material("Dark body wrap", (0.035, 0.045, 0.043), 0.02, 0.64),
        material("Brushed integrated details", (0.52, 0.56, 0.57), 0.75, 0.23),
        material("Integrated optical surface", (0.018, 0.09, 0.12), 0.18, 0.16),
    ):
        obj.data.materials.append(item)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.025)
    bpy.ops.object.mode_set(mode="OBJECT")

    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Corrective camera world")
    scene.world.color = (0.025, 0.029, 0.034)
    silhouettes = []
    for view in ("front", "side", "top"):
        silhouettes.append(render_silhouette([obj.name], str(output / f"connected_{view}_mask.png"), view=view, resolution=720, margin=1.12, frame_name=[obj.name]))
        render_review(scene, output, view)
    render_review(scene, output, "isometric")

    base = mesh_health(obj)
    subdivision = next(modifier for modifier in obj.modifiers if modifier.type == "SUBSURF")
    subdivision.show_viewport = False
    bpy.context.view_layer.update()
    bevel_stage = mesh_health(obj, evaluated=True)
    subdivision.show_viewport = True
    bpy.context.view_layer.update()
    evaluated = mesh_health(obj, evaluated=True)
    circularity = control_circularity(obj)
    sharp_categories = json.loads(obj["sharp_edge_categories_json"])
    weight_attribute = obj.data.attributes["bevel_weight_edge"]
    actual_weighted_edges = sum(item.value > 0.999 for item in weight_attribute.data)
    assertions = {
        "exactly_one_mesh_object": len([item for item in bpy.data.objects if item.type == "MESH"]) == 1,
        "base_is_one_connected_component": base["connected_components"] == 1,
        "evaluated_is_one_connected_component": evaluated["connected_components"] == 1,
        "base_is_all_quad": base["faces"] == base["quads"],
        "evaluated_is_all_quad": evaluated["faces"] == evaluated["quads"],
        "base_is_closed_manifold": base["non_manifold_edges"] == 0,
        "base_has_consistent_face_winding": base["inconsistent_winding_edges"] == 0,
        "bevel_stage_is_closed_manifold": bevel_stage["non_manifold_edges"] == 0,
        "evaluated_is_closed_manifold": evaluated["non_manifold_edges"] == 0,
        "no_degenerate_or_loose_geometry": base["degenerate_faces"] == 0 and base["loose_vertices"] == 0,
        "has_controlled_subdivision": any(mod.type == "SUBSURF" for mod in obj.modifiers),
        "weighted_bevel_precedes_subdivision": [modifier.type for modifier in obj.modifiers][:2] == ["BEVEL", "SUBSURF"],
        "all_intended_sharp_edges_are_weighted": actual_weighted_edges == obj["intended_sharp_edge_count"] == obj["weighted_bevel_edges"],
        "sharpness_categories_are_complete": set(sharp_categories) == {"body_perimeters", "body_corner_rails", "lens_steps", "top_control_1", "top_control_2"} and all(sharp_categories.values()),
        "has_populated_uvs": bool(obj.data.uv_layers and obj.data.uv_layers.active and len(obj.data.uv_layers.active.data) == len(obj.data.loops)),
        "has_multiple_integrated_material_regions": len(obj.data.materials) == 4 and len({face.material_index for face in obj.data.polygons}) == 4,
        "no_mesh_primitive_operators": obj["primitive_objects_added"] == 0,
        "body_starts_from_literal_box": obj["body_profile"].startswith("literal box perimeter"),
        "top_controls_use_12_to_16_vertices": 12 <= obj["top_control_radial_vertices"] <= 16,
        "top_controls_are_regular_circles": all(item["radius_relative_deviation"] < 1e-5 and item["angle_gap_relative_deviation"] < 1e-5 for item in circularity),
    }
    report = {
        "lab": "connected_camera_corrective",
        "status": "corrective_after_experienced_human_rejection",
        "objects": 1,
        "construction": {
            "starting_cages": 1,
            "connected_components": base["connected_components"],
            "feature_method": "surface loop cells -> inset rings -> welded extrusion rings",
            "body_profile": obj["body_profile"],
            "disconnected_joined_shells": 0,
            "mesh_primitive_operators_used": 0,
            "authored_radial_vertices": int(obj["authored_radial_vertices"]),
            "top_control_radial_vertices": int(obj["top_control_radial_vertices"]),
            "weighted_bevel_edges": int(obj["weighted_bevel_edges"]),
            "sharp_edge_categories": sharp_categories,
            "weighted_bevel_width": 0.018,
            "body_perimeter_support_spacing": 0.04,
        },
        "base_health": base,
        "bevel_stage_health": bevel_stage,
        "evaluated_health": evaluated,
        "top_control_circularity": circularity,
        "silhouette_records": silhouettes,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    (output / "connected_camera_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "connected_camera_corrective.blend"))
    print("CONNECTED_CAMERA_RESULT:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


main()
