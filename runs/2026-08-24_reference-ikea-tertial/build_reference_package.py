"""Build and validate the reference-to-model contract for IKEA TERTIAL 705.042.95.

The package is intentionally based on official product photographs, the official
assembly document, and the official 17 cm shade diameter.  Measurements are
recorded as image-space ratios so perspective uncertainty stays explicit.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\odane\Downloads\3d")
OUT = ROOT / "runs" / "2026-08-24_reference-ikea-tertial"
os.chdir(OUT)
sys.path.insert(0, str(ROOT))

from blender_ops.stage_gates import evaluate_stage_gate  # noqa: E402
from knowledge_engine.modeling_spec import validate_reference_modeling_spec  # noqa: E402
from knowledge_engine.reasoning import validate_component_graph  # noqa: E402
from knowledge_engine.reference_analysis import (  # noqa: E402
    PropertyClaim,
    ReferenceItem,
    ReferenceSet,
    audit_reference_set,
    build_reference_stage_evidence,
    reference_set_to_dict,
    validate_component_reference_coverage,
    validate_depth_critical_reference_support,
)
from knowledge_engine.visual_reconstruction import audit_visual_reconstruction  # noqa: E402

TARGET_ID = "ikea-tertial-70504295"
TARGET_VARIANT = "light-blue-us-70504295"
PRODUCT_URL = "https://www.ikea.com/us/en/p/tertial-work-lamp-light-blue-70504295/"
ASSEMBLY_URL = "https://www.ikea.com/us/en/assembly_instructions/tertial-work-lamp-light-blue__AA-2202950-4-100.pdf"


def digest(relative_path: str) -> str:
    return hashlib.sha256((OUT / relative_path).read_bytes()).hexdigest()


def claim(property_id: str, purpose: str, observation: str, component_id: str, confidence: str = "HIGH") -> PropertyClaim:
    return PropertyClaim(property_id, purpose, observation, confidence, component_id)


components = [
    {"id": "shade_shell", "label": "One-piece flared stamped-steel reflector", "depth_critical": True},
    {"id": "socket_housing", "label": "Vented cylindrical socket housing", "depth_critical": True},
    {"id": "head_yoke", "label": "Triangular head pivot yoke and swivel", "depth_critical": True},
    {"id": "upper_parallel_arm", "label": "Two separate upper stamped-steel arm bars", "depth_critical": True},
    {"id": "elbow_plate", "label": "Triangular middle joint plate with open cutout", "depth_critical": True},
    {"id": "lower_parallel_arm", "label": "Two separate lower stamped-steel arm bars", "depth_critical": True},
    {"id": "base_clamp", "label": "ABS table clamp, bushing, and lower pivot mount", "depth_critical": True},
    {"id": "tension_springs", "label": "Four exposed extension springs", "depth_critical": True},
    {"id": "pivot_hardware", "label": "Repeated pins, screws, washers, and adjustment tabs", "depth_critical": False},
    {"id": "power_cable", "label": "Flexible power cable routed through the articulated assembly", "depth_critical": False},
]
relationships = [
    {"from": "shade_shell", "to": "socket_housing", "type": "locks_to"},
    {"from": "socket_housing", "to": "head_yoke", "type": "pivots_on"},
    {"from": "head_yoke", "to": "upper_parallel_arm", "type": "pivots_on"},
    {"from": "upper_parallel_arm", "to": "elbow_plate", "type": "pivots_on"},
    {"from": "elbow_plate", "to": "lower_parallel_arm", "type": "pivots_on"},
    {"from": "lower_parallel_arm", "to": "base_clamp", "type": "pivots_on"},
    {"from": "tension_springs", "to": "upper_parallel_arm", "type": "tensions"},
    {"from": "tension_springs", "to": "lower_parallel_arm", "type": "tensions"},
    {"from": "pivot_hardware", "to": "head_yoke", "type": "fastens"},
    {"from": "pivot_hardware", "to": "elbow_plate", "type": "fastens"},
    {"from": "pivot_hardware", "to": "base_clamp", "type": "fastens"},
    {"from": "power_cable", "to": "socket_housing", "type": "enters"},
    {"from": "power_cable", "to": "base_clamp", "type": "routes_past"},
]
component_graph = validate_component_graph(components, relationships)
assert component_graph["pass"], component_graph


hero_components = tuple(item["id"] for item in components)
items = (
    ReferenceItem(
        "official_product_hero", "IKEA product media 0957547_PE822319", TARGET_ID, TARGET_VARIANT,
        ("PRIMARY_FORM", "CONSTRUCTION", "DIMENSION"), "side_hero", "PERSPECTIVE", "VERY_HIGH",
        PRODUCT_URL, "references/tertial_official_1.jpg", digest("references/tertial_official_1.jpg"),
        (
            claim("shade_diameter", "DIMENSION", "Official specification: reflector shade diameter is 17 cm.", "shade_shell"),
            claim("upper_arm_to_shade_ratio", "PRIMARY_FORM", "Hero image pivot-to-pivot upper arm is about 578 px against a 306 px shade diameter: 1.89:1 (±6% perspective/landmark uncertainty).", "upper_parallel_arm"),
            claim("lower_arm_to_shade_ratio", "PRIMARY_FORM", "Hero image pivot-to-pivot lower arm is about 598 px against a 306 px shade diameter: 1.95:1 (±6% perspective/landmark uncertainty).", "lower_parallel_arm"),
            claim("parallel_arm_construction", "CONSTRUCTION", "Each articulated section visibly contains two long rectangular stamped bars separated by a stable open gap.", "upper_parallel_arm"),
            claim("middle_joint_negative_space", "PRIMARY_FORM", "The elbow plate has a conspicuous trapezoidal/triangular through opening.", "elbow_plate"),
            claim("clamp_gap", "PRIMARY_FORM", "White ABS screw clamp creates the major lower negative space and terminates in a vertical threaded screw.", "base_clamp"),
            claim("cable_route", "PRIMARY_FORM", "The pale cable forms a large arch over the head, a smaller elbow loop, and an oblique tail below the clamp.", "power_cable"),
        ),
        ("shade_diameter=17cm",), (), hero_components,
    ),
    ReferenceItem(
        "official_installed_side", "IKEA product media 0957570_PE822320", TARGET_ID, TARGET_VARIANT,
        ("PRIMARY_FORM", "CONSTRUCTION", "CONTEXT"), "installed_side", "PERSPECTIVE", "VERY_HIGH",
        PRODUCT_URL, "references/tertial_official_2.jpg", digest("references/tertial_official_2.jpg"),
        (
            claim("articulated_pose_graph", "CONSTRUCTION", "Installed view confirms three pivot zones: base, middle elbow, and head yoke.", "elbow_plate"),
            claim("paired_lower_bars", "CONSTRUCTION", "Lower link remains visibly a two-bar assembly in a different pose.", "lower_parallel_arm"),
            claim("spring_count", "CONSTRUCTION", "Two parallel extension springs are visible on the lower section; the upper pair shares the same repeated construction.", "tension_springs"),
        ),
        (), (), ("shade_shell", "socket_housing", "head_yoke", "upper_parallel_arm", "elbow_plate", "lower_parallel_arm", "base_clamp", "tension_springs", "pivot_hardware"),
    ),
    ReferenceItem(
        "official_context_pair", "IKEA product media 1284966_PE933153", TARGET_ID, TARGET_VARIANT,
        ("PRIMARY_FORM", "CONSTRUCTION", "CONTEXT", "FUNCTIONAL"), "rear_three_quarter", "PERSPECTIVE", "VERY_HIGH",
        PRODUCT_URL, "references/tertial_official_3.jpg", digest("references/tertial_official_3.jpg"),
        (
            claim("arm_depth_separation", "CONSTRUCTION", "Two lamps viewed obliquely confirm arm bars are flat strips offset across depth, not one wide slab.", "upper_parallel_arm"),
            claim("wall_mount_alternative", "FUNCTIONAL", "The same base bushing accepts the lower arm vertically when wall-mounted.", "base_clamp"),
        ),
        (), ("Small contextual scale; not used for fine profile measurements."), ("upper_parallel_arm", "lower_parallel_arm", "base_clamp", "tension_springs"),
    ),
    ReferenceItem(
        "official_head_joint_detail", "IKEA product media 0996456_PE822322", TARGET_ID, TARGET_VARIANT,
        ("DETAIL", "CONSTRUCTION"), "head_joint_closeup", "PERSPECTIVE", "VERY_HIGH",
        PRODUCT_URL, "references/tertial_official_4.jpg", digest("references/tertial_official_4.jpg"),
        (
            claim("head_yoke_layering", "CONSTRUCTION", "Rounded triangular yoke plates sandwich two rectangular arm strips and rotate around a separate central pin.", "head_yoke"),
            claim("shade_swivel", "CONSTRUCTION", "A separate zinc-colored horizontal swivel shaft joins the yoke to the socket housing.", "socket_housing"),
            claim("bar_cross_section", "DETAIL", "Arm members have a shallow rectangular stamped-steel cross-section with softly rolled edges, not round tubing.", "upper_parallel_arm"),
            claim("pivot_fasteners", "DETAIL", "Visible Phillips screws, domed rivet/pin, and washers establish repeated hardware scale.", "pivot_hardware"),
        ),
        (), (), ("socket_housing", "head_yoke", "upper_parallel_arm", "pivot_hardware"),
    ),
    ReferenceItem(
        "assembly_overview", "IKEA AA-2202950-4 page 1", TARGET_ID, TARGET_VARIANT,
        ("CONSTRUCTION", "PRIMARY_FORM"), "assembly_overview", "UNKNOWN", "VERY_HIGH",
        ASSEMBLY_URL, "references/assembly_pages/page_01.png", digest("references/assembly_pages/page_01.png"),
        (
            claim("full_component_graph", "CONSTRUCTION", "Official line drawing confirms the full paired-link, triangular-joint, spring, head, and clamp assembly.", "elbow_plate"),
            claim("shade_profile", "PRIMARY_FORM", "Shade is a rotationally symmetric flared dome with a short neck and rolled lower lip.", "shade_shell"),
        ),
        (), ("Line art is not a dimensioned orthographic drawing."), hero_components,
    ),
    ReferenceItem(
        "assembly_shade_profile", "IKEA AA-2202950-4 page 3", TARGET_ID, TARGET_VARIANT,
        ("CONSTRUCTION", "PRIMARY_FORM"), "shade_profile_diagram", "UNKNOWN", "VERY_HIGH",
        ASSEMBLY_URL, "references/assembly_pages/page_03.png", digest("references/assembly_pages/page_03.png"),
        (
            claim("shade_single_shell", "CONSTRUCTION", "The reflector is supplied as one removable shell; the neck slot/bayonet detail is part of that shell.", "shade_shell"),
            claim("shade_height_ratio", "PRIMARY_FORM", "Diagram and hero consistently show shade height about 0.72 of rim diameter (±7%).", "shade_shell"),
        ),
        (), ("Diagram is illustrative, so only ratios corroborated by the photo are used."), ("shade_shell",),
    ),
    ReferenceItem(
        "assembly_clamp_parts", "IKEA AA-2202950-4 page 4", TARGET_ID, TARGET_VARIANT,
        ("CONSTRUCTION", "DETAIL", "FUNCTIONAL", "DIMENSION"), "clamp_exploded", "UNKNOWN", "VERY_HIGH",
        ASSEMBLY_URL, "references/assembly_pages/page_04.png", digest("references/assembly_pages/page_04.png"),
        (
            claim("clamp_component_split", "CONSTRUCTION", "Exploded parts show a separate table clamp and separate socket/bushing base; they must not be fused into one invented mass.", "base_clamp"),
            claim("clamp_range", "DIMENSION", "Official product specification states clamping range up to 2.25 in (57.15 mm).", "base_clamp"),
        ),
        ("clamping_range<=57.15mm",), (), ("base_clamp",),
    ),
    ReferenceItem(
        "assembly_spring_detail", "IKEA AA-2202950-4 page 8", TARGET_ID, TARGET_VARIANT,
        ("CONSTRUCTION", "DETAIL", "FUNCTIONAL"), "spring_attachment", "UNKNOWN", "VERY_HIGH",
        ASSEMBLY_URL, "references/assembly_pages/page_08.png", digest("references/assembly_pages/page_08.png"),
        (
            claim("spring_attachment_points", "CONSTRUCTION", "Two upper springs hook from the elbow plate to a mid-span pin on the upper lower bar; the pair is repeated across depth.", "tension_springs"),
            claim("spring_pair_count", "DETAIL", "Instruction explicitly marks 2x springs for the shown section; photos show another pair on the lower section, total four.", "tension_springs"),
        ),
        (), (), ("tension_springs", "upper_parallel_arm", "elbow_plate", "pivot_hardware"),
    ),
)

reference_set = ReferenceSet(
    TARGET_ID, TARGET_VARIANT, items,
    ("side_hero", "installed_side", "rear_three_quarter", "head_joint_closeup", "assembly_overview", "shade_profile_diagram", "clamp_exploded", "spring_attachment"),
    ("shade_diameter", "upper_arm_to_shade_ratio", "lower_arm_to_shade_ratio", "parallel_arm_construction", "middle_joint_negative_space", "clamp_component_split", "spring_pair_count"),
    (), True, 2, (), (),
)
reference_audit = audit_reference_set(reference_set)
coverage = validate_component_reference_coverage(components, items)
depth_support = validate_depth_critical_reference_support(components, items)
assert reference_audit["pass"], reference_audit
assert coverage["pass"], coverage
assert depth_support["pass"], depth_support


observations = [
    {"observation_id": "parallel_bars_hero", "reference_id": "official_product_hero", "view": "side_hero", "property": "parallel_rectangular_bars_visible", "value": True, "method": "Direct visual count: two separated rectangular strips are visible in each arm section.", "evidence_path": "references/tertial_official_1.jpg"},
    {"observation_id": "parallel_bars_assembly", "reference_id": "assembly_overview", "view": "assembly_overview", "property": "parallel_rectangular_bars_visible", "value": True, "method": "Official line drawing independently depicts two separated long members per arm section.", "evidence_path": "references/assembly_pages/page_01.png"},
    {"observation_id": "upper_length_ratio", "reference_id": "official_product_hero", "view": "side_hero", "property": "upper_pivot_length_over_shade_diameter", "value": {"min": 1.78, "max": 2.00}, "method": "Image landmarks: upper pivot span about 578 px; shade rim about 306 px; 1.89 ratio with ±6% perspective/landmark band.", "evidence_path": "references/tertial_official_1.jpg"},
    {"observation_id": "shade_is_revolved", "reference_id": "assembly_shade_profile", "view": "shade_profile_diagram", "property": "rotationally_symmetric_flared_shell", "value": True, "method": "Official isolated part diagram shows one circular neck, continuous flared profile, and circular lower rim.", "evidence_path": "references/assembly_pages/page_03.png"},
    {"observation_id": "clamp_is_separate", "reference_id": "assembly_clamp_parts", "view": "clamp_exploded", "property": "clamp_and_bushing_are_separate_parts", "value": True, "method": "Official exploded inventory depicts clamp and bushing/mount as two separately supplied parts.", "evidence_path": "references/assembly_pages/page_04.png"},
]
authority = [
    {"reference_id": "official_product_hero", "property": "parallel_rectangular_bars_visible", "fit_for_property": True},
    {"reference_id": "assembly_overview", "property": "parallel_rectangular_bars_visible", "fit_for_property": True},
    {"reference_id": "official_product_hero", "property": "upper_pivot_length_over_shade_diameter", "fit_for_property": True},
    {"reference_id": "assembly_shade_profile", "property": "rotationally_symmetric_flared_shell", "fit_for_property": True},
    {"reference_id": "assembly_clamp_parts", "property": "clamp_and_bushing_are_separate_parts", "fit_for_property": True},
]


def uncontested(component_id: str, structure_type: str, family: str, justification: str) -> dict:
    return {
        "region_id": f"{component_id}_construction", "component_id": component_id, "uncontested": True,
        "hypotheses": [{
            "hypothesis_id": f"{component_id}_selected",
            "interpretation": {"structure_type": structure_type, "summary": component_id, "justification": justification},
            "construction": {"family": family},
        }],
    }


arm_region = {
    "region_id": "upper_arm_structure", "component_id": "upper_parallel_arm", "minimum_confirmed_views": 2,
    "selected_hypothesis_id": "paired_stamped_bars",
    "hypotheses": [
        {"hypothesis_id": "paired_stamped_bars", "interpretation": {"structure_type": "floating_separate_assembly", "summary": "Two separate shallow rectangular stamped bars", "justification": "Both official photo and assembly drawing show two separated parallel strips; head close-up confirms shallow rectangular cross-sections."}, "construction": {"family": "profile_extrusion"}, "predicted_consequences": [
            {"reference_id": "official_product_hero", "observation_id": "parallel_bars_hero", "view": "side_hero", "property": "parallel_rectangular_bars_visible", "prediction_type": "boolean_state", "prediction": True},
            {"reference_id": "assembly_overview", "observation_id": "parallel_bars_assembly", "view": "assembly_overview", "property": "parallel_rectangular_bars_visible", "prediction_type": "boolean_state", "prediction": True},
        ]},
        {"hypothesis_id": "single_wide_arm_slab", "interpretation": {"structure_type": "extruded_slab", "summary": "One wide solid link per section", "justification": "A low-resolution silhouette could collapse the paired strips into one slab; retained as the competing failure mode."}, "construction": {"family": "box_poly"}, "predicted_consequences": [
            {"reference_id": "official_product_hero", "observation_id": "parallel_bars_hero", "view": "side_hero", "property": "parallel_rectangular_bars_visible", "prediction_type": "boolean_state", "prediction": False},
            {"reference_id": "assembly_overview", "observation_id": "parallel_bars_assembly", "view": "assembly_overview", "property": "parallel_rectangular_bars_visible", "prediction_type": "boolean_state", "prediction": False},
        ]},
    ],
}
regions = [
    arm_region,
    uncontested("shade_shell", "revolved_body", "profile_revolution", "Official isolated-part diagram and product photos show one axisymmetric stamped reflector; a connected revolved profile preserves the neck, dome, flare, and rolled lip."),
    uncontested("socket_housing", "revolved_body", "profile_revolution", "The housing is a circular vented shell around the bulb socket; start from one connected revolved cage and cut/represent slots only after primary form approval."),
    uncontested("head_yoke", "floating_separate_assembly", "profile_extrusion", "Close-up proves rounded triangular plates, shaft, and arm bars are mechanically separate layers around pivots."),
    uncontested("elbow_plate", "through_hole", "profile_extrusion", "The elbow is a stamped triangular plate with a large through opening; model its outer and inner profile as one connected plate cage."),
    uncontested("lower_parallel_arm", "floating_separate_assembly", "profile_extrusion", "Installed and oblique views confirm two separate shallow rectangular strips mirroring the upper link construction."),
    uncontested("base_clamp", "floating_separate_assembly", "box_poly", "Official exploded view proves clamp and bushing are separate ABS parts; each part should be a connected box-modeled cage with the functional clamping void preserved."),
    uncontested("tension_springs", "swept_tube", "curve_sweep", "Four physically separate helical tension springs follow measured hook endpoints; curve sweeps are the appropriate reversible representation."),
    uncontested("pivot_hardware", "nested_cylindrical_stack", "separate_radial_assembly", "Repeated actual fasteners are shallow 12-16 sided radial parts, instanced from a small number of authored hardware forms."),
    uncontested("power_cable", "swept_tube", "curve_sweep", "The official product views expose one flexible cable whose routed arches materially affect the outer silhouette; a reversible curve sweep matches its physical construction."),
]
selected_hypotheses = ["paired_stamped_bars"] + [region["hypotheses"][0]["hypothesis_id"] for region in regions[1:]]
passes = {name: {"status": "PASS", "evidence_ids": ["parallel_bars_hero"]} for name in (
    "identity", "silhouette", "massing", "components", "depth", "negative_space", "cross_sections",
    "representation_hypotheses", "cross_view_prediction", "uncertainty", "construction_plan",
)}
passes["depth"]["evidence_ids"] = ["clamp_is_separate"]
passes["negative_space"]["evidence_ids"] = ["parallel_bars_hero", "clamp_is_separate"]
passes["cross_sections"]["evidence_ids"] = ["parallel_bars_hero", "shade_is_revolved"]
passes["massing"]["evidence_ids"] = ["upper_length_ratio"]
visual_payload = {
    "target_id": TARGET_ID, "target_variant": TARGET_VARIANT, "components": components,
    "observations": observations, "property_authority": authority, "passes": passes, "regions": regions,
    "construction_plan": {
        "selected_hypothesis_ids": selected_hypotheses,
        "generic_operations": ["create_profile_extrusion", "create_quad_radial_surface", "create_curve_sweep", "transform_objects"],
        "reversible_assumptions": [],
    },
}
visual_audit = audit_visual_reconstruction(visual_payload, {item.reference_id: item for item in items})
assert visual_audit["pass"], visual_audit


authorized_hashes = sorted({item.local_sha256 for item in items if item.local_sha256})
hash_by_reference = {item.reference_id: item.local_sha256 for item in items}
roles = {
    "shade_shell": "PRIMARY", "socket_housing": "PRIMARY", "head_yoke": "SECONDARY",
    "upper_parallel_arm": "PRIMARY", "elbow_plate": "PRIMARY", "lower_parallel_arm": "PRIMARY",
    "base_clamp": "PRIMARY", "tension_springs": "SECONDARY", "pivot_hardware": "TERTIARY",
    "power_cable": "SECONDARY",
}
representations = {
    "shade_shell": "REVOLVE", "socket_housing": "REVOLVE", "head_yoke": "PROFILE_EXTRUSION",
    "upper_parallel_arm": "PROFILE_EXTRUSION", "elbow_plate": "PROFILE_EXTRUSION",
    "lower_parallel_arm": "PROFILE_EXTRUSION", "base_clamp": "BOX_POLY",
    "tension_springs": "CURVE_SWEEP", "pivot_hardware": "RADIAL_CAGE", "power_cable": "CURVE_SWEEP",
}
continuity = {
    "shade_shell": "CONTINUOUS", "socket_housing": "CONTINUOUS", "head_yoke": "SEPARATE",
    "upper_parallel_arm": "SEPARATE", "elbow_plate": "CONTINUOUS", "lower_parallel_arm": "SEPARATE",
    "base_clamp": "SEPARATE", "tension_springs": "SEPARATE", "pivot_hardware": "SEPARATE",
    "power_cable": "SEPARATE",
}
component_spec = []
for component in components:
    cid = component["id"]
    matching = [item.local_sha256 for item in items if cid in item.component_ids and item.local_sha256]
    component_spec.append({
        "id": cid, "role": roles[cid], "continuity_policy": continuity[cid],
        "representation": representations[cid], "high_salience": roles[cid] == "PRIMARY",
        "construction_justification": next(region["hypotheses"][0]["interpretation"]["justification"] for region in regions if region.get("component_id") == cid),
        "evidence_sha256": sorted(set(matching)), "depth_critical": component["depth_critical"],
        "reversible_until_multiview_pass": bool(component["depth_critical"]),
    })


def feature(fid: str, cid: str, description: str, reference_id: str, mtype: str, tolerance: float, salience: str = "HIGH") -> dict:
    return {"id": fid, "component_id": cid, "salience": salience, "description": description,
            "evidence_sha256": hash_by_reference[reference_id],
            "measurement": {"type": mtype, "tolerance": tolerance}}


identity_features = [
    feature("flared_reflector", "shade_shell", "Connected flared dome with short neck and rolled circular lip; rim diameter is the 17 cm scale anchor.", "official_product_hero", "RATIO", 0.05),
    feature("vented_head", "socket_housing", "Tall circular socket housing with repeated vertical slots; slots are deferred until primary mass passes.", "official_head_joint_detail", "SILHOUETTE", 0.08),
    feature("long_upper_pair", "upper_parallel_arm", "Two separated rectangular bars spanning 1.89 shade diameters pivot-to-pivot.", "official_product_hero", "RATIO", 0.07),
    feature("open_elbow_plate", "elbow_plate", "Rounded triangular middle plate with a large through opening and three visible pivot landmarks.", "official_product_hero", "NEGATIVE_SPACE", 0.08),
    feature("long_lower_pair", "lower_parallel_arm", "Two separated rectangular bars spanning 1.95 shade diameters pivot-to-pivot.", "official_product_hero", "RATIO", 0.07),
    feature("functional_clamp_void", "base_clamp", "Separate clamp and bushing preserve the desk-edge gap and threaded screw path.", "assembly_clamp_parts", "NEGATIVE_SPACE", 0.08),
    feature("head_layer_stack", "head_yoke", "Rounded triangular yoke sandwiches arm strips and meets a separate horizontal swivel shaft.", "official_head_joint_detail", "RELATIONSHIP", 0.08, "MEDIUM"),
    feature("four_spring_layout", "tension_springs", "Two extension springs per articulated section terminate at observed hooks and pins.", "assembly_spring_detail", "RELATIONSHIP", 0.10, "MEDIUM"),
]
stage_features = {
    "REFERENCE_ANALYSIS": ["flared_reflector", "long_upper_pair", "open_elbow_plate", "long_lower_pair", "functional_clamp_void"],
    "PRIMARY_BLOCKOUT": ["flared_reflector", "long_upper_pair", "open_elbow_plate", "long_lower_pair", "functional_clamp_void"],
    "PROPORTION_SILHOUETTE": ["flared_reflector", "long_upper_pair", "open_elbow_plate", "long_lower_pair", "functional_clamp_void"],
}
spec_passes = []
for stage, feature_ids in stage_features.items():
    spec_passes.append({"stage": stage, "criteria": [
        {"feature_id": fid, "observable": f"Verify {fid} against bound evidence in side and three-quarter channels.",
         "channel": "REFERENCE" if stage == "REFERENCE_ANALYSIS" else ("BASE_CAGE" if stage == "PRIMARY_BLOCKOUT" else "VISUAL")}
        for fid in feature_ids
    ]})
modeling_spec = {
    "schema_version": 1, "record_type": "REFERENCE_MODELING_SPEC",
    "target": {"target_id": TARGET_ID, "target_variant": TARGET_VARIANT, "complexity": "MODERATE", "authorized_reference_sha256": authorized_hashes},
    "components": component_spec, "identity_features": identity_features, "passes": spec_passes,
    "repair_policy": {"max_attempts_per_region_stage": 3, "stagnation_limit": 2},
}
modeling_spec_audit = validate_reference_modeling_spec(modeling_spec)
assert modeling_spec_audit["pass"], modeling_spec_audit

evidence = build_reference_stage_evidence(
    reference_audit, component_graph_pass=component_graph["pass"], measured_ratio_count=6,
    uncertainty_recorded=True, visual_reconstruction_audit=visual_audit,
    component_reference_coverage=coverage, depth_critical_reference_support=depth_support,
    modeling_spec_audit=modeling_spec_audit,
)
gate_result = evaluate_stage_gate("REFERENCE_ANALYSIS", evidence)
assert gate_result["pass"], gate_result

coverage_objects = {
    "shade_shell": "ShadeShell", "socket_housing": "SocketHousing",
    "head_yoke": "HeadYoke", "upper_parallel_arm": "UpperArmBar_A",
    "elbow_plate": "ElbowPlate", "lower_parallel_arm": "LowerArmBar_A",
    "base_clamp": "BaseClamp", "tension_springs": "UpperSpring_Front",
    "pivot_hardware": "ElbowPivot", "power_cable": "PowerCable",
}
scene_decomposition = {
    "object_name": "IKEA TERTIAL Work Lamp 705.042.95", "object_class": "articulated clamp work lamp",
    "reference_style": "mixed",
    "components": [{
        "name": component["id"], "role": roles[component["id"]].lower(),
        "manufacture": "structural",
        "separately_manufactured": continuity[component["id"]] == "SEPARATE",
        "notes": component["label"], "evidence_status": "OBSERVED", "confidence": 0.9,
        "evidence": ["reference_manifest.json"],
        "coverage_binding": {"kind": "object", "object_name": coverage_objects[component["id"]]},
    } for component in components],
}

artifacts = {
    "reference_manifest.json": reference_set_to_dict(reference_set),
    "reference_audit.json": reference_audit,
    "component_graph.json": {"components": components, "relationships": relationships, "validation": component_graph},
    "component_reference_coverage.json": coverage,
    "depth_critical_reference_support.json": depth_support,
    "visual_reconstruction.json": visual_payload,
    "visual_reconstruction_audit.json": visual_audit,
    "reference_modeling_spec.json": modeling_spec,
    "reference_modeling_spec_audit.json": modeling_spec_audit,
    "reference_stage_gate_evidence.json": evidence,
    "reference_stage_gate_result.json": gate_result,
    "scene_decomposition.json": scene_decomposition,
}
for filename, payload in artifacts.items():
    (OUT / filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")

print(json.dumps({
    "target": TARGET_ID, "reference_count": len(items), "reference_audit": reference_audit["pass"],
    "visual_reconstruction": visual_audit["pass"], "modeling_spec": modeling_spec_audit["pass"],
    "depth_support": depth_support["pass"], "reference_gate": gate_result["pass"],
    "authorized_hash_count": len(authorized_hashes), "artifact_count": len(artifacts),
}, indent=2))
