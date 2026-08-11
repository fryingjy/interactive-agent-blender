extends SceneTree

const VALID_PATH := "res://godot_tangent_bake_valid.glb"
const INVALID_PATH := "res://godot_tangent_bake_invalid_color_wiring.glb"
const REPORT_PATH := "res://godot_import_report.json"


func find_mesh_instance(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node
	for child in node.get_children():
		var found := find_mesh_instance(child)
		if found != null:
			return found
	return null


func inspect_asset(path: String) -> Dictionary:
	var packed := load(path) as PackedScene
	if packed == null:
		return {"loaded": false, "path": path}
	var root := packed.instantiate()
	var mesh_instance := find_mesh_instance(root)
	if mesh_instance == null or mesh_instance.mesh == null:
		root.free()
		return {"loaded": true, "mesh_found": false, "path": path}
	var mesh := mesh_instance.mesh
	var arrays := mesh.surface_get_arrays(0)
	var format: int = mesh.surface_get_format(0)
	var material := mesh.surface_get_material(0) as BaseMaterial3D
	var aabb := mesh.get_aabb()
	var normal_texture_present := false
	var normal_enabled := false
	var albedo_texture_present := false
	var metallic := -1.0
	var roughness := -1.0
	if material != null:
		normal_enabled = material.normal_enabled
		normal_texture_present = material.normal_texture != null
		albedo_texture_present = material.albedo_texture != null
		metallic = material.metallic
		roughness = material.roughness
	var result := {
		"path": path,
		"loaded": true,
		"mesh_found": true,
		"surface_count": mesh.get_surface_count(),
		"vertex_count": arrays[Mesh.ARRAY_VERTEX].size(),
		"normal_count": arrays[Mesh.ARRAY_NORMAL].size(),
		"tangent_scalar_count": arrays[Mesh.ARRAY_TANGENT].size(),
		"uv_count": arrays[Mesh.ARRAY_TEX_UV].size(),
		"index_count": arrays[Mesh.ARRAY_INDEX].size(),
		"format_has_tangent": bool(format & Mesh.ARRAY_FORMAT_TANGENT),
		"format_has_uv": bool(format & Mesh.ARRAY_FORMAT_TEX_UV),
		"material_class": material.get_class() if material != null else "",
		"normal_enabled": normal_enabled,
		"normal_texture_present": normal_texture_present,
		"albedo_texture_present": albedo_texture_present,
		"metallic": metallic,
		"roughness": roughness,
		"aabb_position_godot_xyz": [aabb.position.x, aabb.position.y, aabb.position.z],
		"aabb_size_godot_xyz": [aabb.size.x, aabb.size.y, aabb.size.z],
		"node_scale": [mesh_instance.scale.x, mesh_instance.scale.y, mesh_instance.scale.z],
	}
	root.free()
	return result


func _initialize() -> void:
	var valid := inspect_asset(VALID_PATH)
	var invalid := inspect_asset(INVALID_PATH)
	var assertions := {
		"valid_import_loaded": valid.get("loaded", false) and valid.get("mesh_found", false),
		"valid_uv_preserved": valid.get("format_has_uv", false) and valid.get("uv_count", 0) > 0,
		"valid_tangents_preserved": valid.get("format_has_tangent", false) and valid.get("tangent_scalar_count", 0) > 0,
		"valid_normal_semantics_preserved": valid.get("normal_enabled", false) and valid.get("normal_texture_present", false),
		"valid_material_values_preserved": abs(valid.get("metallic", -1.0) - 0.15) < 0.001 and abs(valid.get("roughness", -1.0) - 0.42) < 0.001,
		"valid_scale_preserved": valid.get("node_scale", []) == [1.0, 1.0, 1.0],
		"failure_import_still_loads": invalid.get("loaded", false) and invalid.get("mesh_found", false),
		"failure_control_detected": not invalid.get("normal_enabled", true) and not invalid.get("normal_texture_present", true) and invalid.get("albedo_texture_present", false),
	}
	var report := {
		"lab": "godot_4_7_1_external_engine_tangent_bake_import",
		"godot_version": Engine.get_version_info(),
		"valid": valid,
		"invalid_color_wiring": invalid,
		"assertions": assertions,
		"pass": assertions.values().all(func(value): return value),
	}
	var file := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("GODOT_IMPORT_RESULT:", JSON.stringify(report))
	quit(0 if report["pass"] else 2)
