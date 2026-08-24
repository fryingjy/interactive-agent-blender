# Architecture

## System boundary

The project separates Blender authority from planner/research policy. Blender owns scene state and
evaluated geometry; ordinary Python modules own ranking, evidence aggregation, and durable records.

```text
materialized references / brief / retrieved knowledge
                  |
                  v
 identity + continuity + representation spec
                  |
                  v
        planner and stage policy
                  |
                  v
 target authorization -> typed MCP call -> Blender modeler server
                  |
                  v
 observe -> transaction -> mutate -> verify -> commit/reject
                  |
       +----------+-----------+----------------+
       |                      |                |
       v                      v                v
   base cage          evaluated surface   visual passes
       |                      |                |
       +----------+-----------+----------------+
                  v
 artifact-bound stage checkpoint / independent verifier / run report
```

## Blender-side authority (`blender_ops/`)

- `state_probe.py` and `state_fingerprint.py` expose current mode, selection, topology, coordinates,
  transforms, and modifiers.
- `decision_transaction.py` captures transaction-owned rollback state and enforces one scoped
  artistic mutation on the sanctioned path.
- `persistent_ids.py` and `semantic_regions.py` preserve element identity and modeling intent across
  supported operations.
- `mesh_ops.py`, `object_ops.py`, `curve_ops.py`, and `profile_mesh.py` provide typed modeling
  operations and authored shape construction.
- `evaluated_probe.py` and `render_passes.py` inspect the dependency-graph result and Blender-native
  visual channels.
- `modeling_stage.py` and `stage_gates.py` make workflow transitions explicit and evidence-bound.
- `modeler_server.py` exposes the Blender command protocol used by the MCP layer. The live singleton
  is strict: construction needs a passing target/variant-bound reference authorization, created
  objects inherit its hash, and loaded objects require explicit binding.

## Policy and learning (`knowledge_engine/`)

- `planner.py`, `reasoning.py`, `strategy.py`, and `component_strategy.py` select one local action
  from live evidence, including fail-closed secondary-view resolution of component depth/continuity.
- `retrieval.py` ranks knowledge by query, stage, workflow, defect, topology, modifiers, prior use,
  and Blender-version relevance.
- `surface_cause_classifier.py`, `visual_compare.py`, and `quality_review.py` aggregate bounded
  evidence without collapsing technical, surface, and visual truth into one score.
- `reference_analysis.py` verifies materialized artifact hashes; `modeling_spec.py` binds semantic
  identity features to continuity and representation decisions; `gemini_reference_critic.py`
  produces exact-render root-cause tickets; `stage_checkpoint.py` and `iteration_control.py` retain
  one correction focus and force a strategy change after bounded stagnation.
- `telemetry.py` and `session_learning.py` retain real use and replay evidence.

## External interfaces

- `addon.py` starts the Blender-side socket endpoint.
- `.mcp.json` configures the generic Blender MCP connection.
- `tools/modeler_mcp_server.py` exposes the typed modeler operations to an MCP-aware agent.

Session identity, scene revision, decision ID, command ID, and event ID remain distinct. A command
return is never sufficient evidence of success; the actual Blender result must be inspected.

## Evidence channels

The architecture intentionally keeps four channels separate:

1. base cage — editable topology and semantic integrity;
2. evaluated surface — modifier/deformation result and surface health;
3. visual/reference — silhouette, proportions, negative space, highlights, and appearance;
4. technical validity — manifoldness as required, degenerates, normals, transforms, UVs, and scene
   hygiene.

Independent verifiers run in fresh factory-startup Blender processes and avoid importing the model
generator whenever practical.
