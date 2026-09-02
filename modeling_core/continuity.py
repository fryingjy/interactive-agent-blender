"""Compile evidence-resolved continuous component groups into connected quad cages."""

from __future__ import annotations

from collections import defaultdict, deque
import math
from typing import Any

import numpy as np

from .mesh import build_shape_mesh


def shape_boundary_ports(shape: dict[str, Any]) -> dict[str, list[int]]:
    """Return explicit open boundary loops for supported generic shape families."""
    if shape["family"] == "section_loft":
        count = int(shape["segments"])
        station_count = len(shape["stations"])
        return {
            "start": list(range(count)),
            "end": list(range((station_count - 1) * count, station_count * count)),
        }
    if shape["family"] == "profile_extrusion":
        count = len(shape["profile"])
        station_count = len(shape["depth_stations"])
        return {
            "front": list(range(count)),
            "rear": list(range((station_count - 1) * count, station_count * count)),
        }
    raise ValueError(f"shape family has no continuity-port implementation: {shape.get('family')}")


def _ready_boundary_order(loop: list[int], faces: list[tuple[int, ...]]) -> list[int]:
    directed = {
        (face[index], face[(index + 1) % len(face)])
        for face in faces
        for index in range(len(face))
    }
    forward = all((loop[index], loop[(index + 1) % len(loop)]) in directed for index in range(len(loop)))
    reverse = all((loop[(index + 1) % len(loop)], loop[index]) in directed for index in range(len(loop)))
    if forward == reverse:
        raise ValueError("port is not one consistently oriented open boundary loop")
    return list(reversed(loop)) if forward else list(loop)


def _best_correspondence(
    vertices: np.ndarray,
    first_ready: list[int],
    second_ready: list[int],
) -> tuple[list[int], list[tuple[int, int]], np.ndarray]:
    if len(first_ready) != len(second_ready):
        raise ValueError("continuous ports require equal vertex counts for an all-quad connection")
    second_sequence = list(reversed(second_ready))
    options = []
    for shift in range(len(second_sequence)):
        shifted = second_sequence[shift:] + second_sequence[:shift]
        distances = np.linalg.norm(vertices[first_ready] - vertices[shifted], axis=1)
        options.append((float(distances.mean()), float(distances.max()), shift, shifted, distances))
    _mean, _maximum, _shift, matched, distances = min(options, key=lambda item: (item[0], item[1], item[2]))
    return matched, list(zip(first_ready, matched)), distances


class _DisjointSet:
    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, first: int, second: int) -> None:
        first_root, second_root = self.find(first), self.find(second)
        if first_root != second_root:
            self.parent[max(first_root, second_root)] = min(first_root, second_root)


def _compact_mesh(
    vertices: np.ndarray,
    faces: list[tuple[int, int, int, int]],
    disjoint: _DisjointSet,
) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    roots = [disjoint.find(index) for index in range(len(vertices))]
    used_roots = sorted({roots[index] for face in faces for index in face})
    compact_index = {root: index for index, root in enumerate(used_roots)}
    members: dict[int, list[int]] = defaultdict(list)
    for index, root in enumerate(roots):
        members[root].append(index)
    compact_vertices = np.asarray(
        [vertices[members[root]].mean(axis=0) for root in used_roots],
        dtype=np.float64,
    )
    compact_faces = []
    for face in faces:
        compact = tuple(compact_index[roots[index]] for index in face)
        if len(set(compact)) != 4:
            raise ValueError("continuity weld collapsed a quad into degenerate topology")
        compact_faces.append(compact)
    return compact_vertices, compact_faces


def _validate_quad_cage(vertices: np.ndarray, faces: list[tuple[int, int, int, int]]) -> dict[str, int]:
    edge_faces: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    adjacency: dict[int, set[int]] = defaultdict(set)
    for face in faces:
        if len(face) != 4 or len(set(face)) != 4:
            raise ValueError("continuity compiler produced a non-quad or degenerate face")
        points = vertices[list(face)]
        area = 0.5 * np.linalg.norm(np.cross(points[1] - points[0], points[2] - points[0]))
        area += 0.5 * np.linalg.norm(np.cross(points[2] - points[0], points[3] - points[0]))
        if area <= 1e-10:
            raise ValueError("continuity compiler produced a zero-area face")
        for index in range(4):
            first, second = face[index], face[(index + 1) % 4]
            edge_faces[tuple(sorted((first, second)))].append((first, second))
            adjacency[first].add(second)
            adjacency[second].add(first)
    if any(len(uses) > 2 for uses in edge_faces.values()):
        raise ValueError("continuity compiler produced a non-manifold edge with more than two faces")
    if any(len(uses) == 2 and uses[0] == uses[1] for uses in edge_faces.values()):
        raise ValueError("continuity compiler produced a face-winding conflict")
    used = {index for face in faces for index in face}
    reached = set()
    queue = deque([min(used)])
    while queue:
        current = queue.popleft()
        if current in reached:
            continue
        reached.add(current)
        queue.extend(adjacency[current] - reached)
    if reached != used:
        raise ValueError("continuity compiler did not produce one connected cage")
    return {
        "vertices": len(vertices),
        "faces": len(faces),
        "boundary_edges": sum(len(uses) == 1 for uses in edge_faces.values()),
        "manifold_edges": sum(len(uses) == 2 for uses in edge_faces.values()),
    }


def build_continuous_cage(
    component_shapes: dict[str, dict[str, Any]],
    relationships: list[dict[str, Any]],
    interfaces: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build one connected cage for one continuous component graph."""
    if not component_shapes:
        raise ValueError("continuous cage requires component shapes")
    expected_pairs = {item.get("pair_id") for item in relationships}
    if None in expected_pairs or set(interfaces) != expected_pairs:
        raise ValueError("continuity interfaces must exactly match continuous relationship pairs")

    vertices_parts = []
    faces: list[tuple[int, int, int, int]] = []
    ports: dict[str, dict[str, list[int]]] = {}
    offsets = {}
    offset = 0
    for component_id, shape in component_shapes.items():
        vertices, local_faces = build_shape_mesh(shape)
        vertices_parts.append(vertices)
        offsets[component_id] = offset
        faces.extend(tuple(index + offset for index in face) for face in local_faces)
        ports[component_id] = {
            name: [index + offset for index in loop]
            for name, loop in shape_boundary_ports(shape).items()
        }
        offset += len(vertices)
    vertices = np.concatenate(vertices_parts, axis=0)
    disjoint = _DisjointSet(len(vertices))
    used_ports = set()
    bridge_faces: list[tuple[int, int, int, int]] = []
    interface_reports = []
    for relationship in relationships:
        pair_id = relationship["pair_id"]
        specification = interfaces[pair_id]
        if not isinstance(specification, dict):
            raise ValueError(f"{pair_id}: interface specification must be an object")
        bindings = specification.get("ports")
        if not isinstance(bindings, dict) or set(bindings) != set(relationship.get("components", [])):
            raise ValueError(f"{pair_id}: interface ports must bind exactly the relationship components")
        component_ids = list(relationship["components"])
        first_component, second_component = component_ids
        first_port, second_port = bindings[first_component], bindings[second_component]
        for component_id, port_name in ((first_component, first_port), (second_component, second_port)):
            if not isinstance(port_name, str):
                raise ValueError(f"{pair_id}: continuity port names must be strings")
            if port_name not in ports[component_id]:
                raise ValueError(f"{pair_id}: unknown port {component_id}.{port_name}")
            key = (component_id, port_name)
            if key in used_ports:
                raise ValueError(f"{pair_id}: continuity port {component_id}.{port_name} is reused")
            used_ports.add(key)
        maximum_span = specification.get("maximum_bridge_span")
        if (
            isinstance(maximum_span, bool)
            or not isinstance(maximum_span, (int, float))
            or not math.isfinite(float(maximum_span))
            or maximum_span <= 0
        ):
            raise ValueError(f"{pair_id}: maximum_bridge_span must be a positive measured bound")
        raw_weld_tolerance = specification.get("weld_tolerance", 1e-5)
        if isinstance(raw_weld_tolerance, bool) or not isinstance(raw_weld_tolerance, (int, float)):
            raise ValueError(f"{pair_id}: weld_tolerance must be a finite nonnegative number")
        weld_tolerance = float(raw_weld_tolerance)
        if not math.isfinite(weld_tolerance) or weld_tolerance < 0:
            raise ValueError(f"{pair_id}: weld_tolerance must be a finite nonnegative number")
        first_ready = _ready_boundary_order(ports[first_component][first_port], faces)
        second_ready = _ready_boundary_order(ports[second_component][second_port], faces)
        matched_second, pairs, distances = _best_correspondence(vertices, first_ready, second_ready)
        maximum_distance = float(distances.max())
        if maximum_distance > float(maximum_span):
            raise ValueError(f"{pair_id}: fitted port span {maximum_distance:.6g} exceeds measured bound {maximum_span}")
        if maximum_distance <= weld_tolerance:
            mode = "WELD"
            for first, second in pairs:
                disjoint.union(first, second)
        else:
            mode = "BRIDGE"
            count = len(first_ready)
            for index in range(count):
                nxt = (index + 1) % count
                bridge_faces.append((first_ready[index], first_ready[nxt], matched_second[nxt], matched_second[index]))
        interface_reports.append({
            "pair_id": pair_id,
            "mode": mode,
            "port_vertex_count": len(first_ready),
            "mean_span": float(distances.mean()),
            "maximum_span": maximum_distance,
        })
    compact_vertices, compact_faces = _compact_mesh(vertices, faces + bridge_faces, disjoint)
    stats = _validate_quad_cage(compact_vertices, compact_faces)
    return {
        "vertices": compact_vertices,
        "faces": compact_faces,
        "component_ids": list(component_shapes),
        "interfaces": interface_reports,
        "stats": stats,
    }
