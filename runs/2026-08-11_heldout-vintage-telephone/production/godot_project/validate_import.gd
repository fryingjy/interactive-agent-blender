extends SceneTree
const ASSET := "res://heldout_vintage_telephone.glb"
const REPORT := "res://godot_import_report.json"
func collect_meshes(node: Node, out: Array) -> void:
 if node is MeshInstance3D: out.append(node)
 for child in node.get_children(): collect_meshes(child,out)
func _initialize() -> void:
 var packed := load(ASSET) as PackedScene
 var loaded := packed != null
 var root := packed.instantiate() if loaded else null
 var items: Array = []
 if root != null: collect_meshes(root,items)
 var surfaces := 0; var uv_surfaces := 0; var tangent_surfaces := 0; var normal_mapped := 0; var vertices := 0; var unit_scales := true
 for raw_item in items:
  var item := raw_item as MeshInstance3D
  unit_scales = unit_scales and item.scale.is_equal_approx(Vector3.ONE)
  if item.mesh == null: continue
  for s in range(item.mesh.get_surface_count()):
   surfaces += 1
   var arrays: Array = item.mesh.surface_get_arrays(s)
   var fmt: int = item.mesh.surface_get_format(s)
   vertices += arrays[Mesh.ARRAY_VERTEX].size()
   if bool(fmt & Mesh.ARRAY_FORMAT_TEX_UV) and arrays[Mesh.ARRAY_TEX_UV].size() > 0: uv_surfaces += 1
   if bool(fmt & Mesh.ARRAY_FORMAT_TANGENT) and arrays[Mesh.ARRAY_TANGENT].size() > 0: tangent_surfaces += 1
   var material := item.mesh.surface_get_material(s) as BaseMaterial3D
   if material != null and material.normal_enabled and material.normal_texture != null: normal_mapped += 1
 var assertions := {
  "fresh_asset_loaded": loaded and root != null,
  "multiple_mesh_instances_present": items.size() >= 15,
  "nonzero_surface_and_vertex_data": surfaces > 0 and vertices > 0,
  "uv_data_present": uv_surfaces > 0,
  "tangent_data_present_for_normal_mapping": tangent_surfaces > 0,
  "normal_texture_semantics_preserved": normal_mapped > 0,
  "node_scales_are_unit": unit_scales,
 }
 var report := {"lab":"heldout_telephone_godot_4_7_1_import","godot_version":Engine.get_version_info(),"mesh_instances":items.size(),"surfaces":surfaces,"vertices":vertices,"uv_surfaces":uv_surfaces,"tangent_surfaces":tangent_surfaces,"normal_mapped_surfaces":normal_mapped,"assertions":assertions,"pass":assertions.values().all(func(v): return v)}
 var file := FileAccess.open(REPORT,FileAccess.WRITE); file.store_string(JSON.stringify(report,"  ")); file.close(); print("TELEPHONE_GODOT_RESULT:",JSON.stringify(report));
 if root != null: root.free()
 quit(0 if report["pass"] else 2)
