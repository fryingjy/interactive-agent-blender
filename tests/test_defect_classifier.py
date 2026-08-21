from knowledge_engine.defect_classifier import classify_corner_triangles, classify_geometry


def _face(agent_id, vertex_ids):
    return {"agent_id": agent_id, "vertex_ids": vertex_ids}


def test_classify_corner_triangles_flags_triangle_at_high_valence_corner():
    faces = [_face(1, [10, 11, 12])]
    valence = {10: 3, 11: 2, 12: 2}

    tickets = classify_corner_triangles(faces, valence)

    assert len(tickets) == 1
    ticket = tickets[0]
    assert ticket["type"] == "corner_triangle"
    assert ticket["face_ids"] == [1]
    assert ticket["vertex_ids"] == [10, 11, 12]
    assert ticket["corner_vertex_ids"] == [10]


def test_classify_corner_triangles_ignores_non_triangles():
    faces = [_face(1, [10, 11, 12, 13])]
    valence = {10: 5, 11: 5, 12: 5, 13: 5}

    assert classify_corner_triangles(faces, valence) == []


def test_classify_corner_triangles_ignores_triangle_with_no_corner_vertex():
    faces = [_face(1, [10, 11, 12])]
    valence = {10: 2, 11: 2, 12: 2}

    assert classify_corner_triangles(faces, valence) == []


def test_classify_corner_triangles_respects_custom_minimum_corner_valence():
    faces = [_face(1, [10, 11, 12])]
    valence = {10: 3, 11: 2, 12: 2}

    tickets_default = classify_corner_triangles(faces, valence, minimum_corner_valence=3)
    assert len(tickets_default) == 1

    assert classify_corner_triangles(faces, valence, minimum_corner_valence=4) == []


def test_classify_geometry_reports_ticket_types_and_claim_boundary():
    faces = [_face(1, [10, 11, 12]), _face(2, [20, 21, 22, 23])]
    valence = {10: 3, 11: 2, 12: 2, 20: 2, 21: 2, 22: 2, 23: 2}

    result = classify_geometry(faces, valence)

    assert result["ticket_types"] == ["corner_triangle"]
    assert len(result["tickets"]) == 1
    assert "claim_boundary" in result


def test_classify_geometry_emits_nothing_for_ambiguous_geometry():
    faces = [_face(1, [10, 11, 12, 13])]
    valence = {10: 1, 11: 1, 12: 1, 13: 1}

    result = classify_geometry(faces, valence)

    assert result["tickets"] == []
    assert result["ticket_types"] == []
