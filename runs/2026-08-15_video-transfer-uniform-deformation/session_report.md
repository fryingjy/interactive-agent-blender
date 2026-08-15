# Video-principle transfer: uniform deformation rings

## Question

Does the Blender Guru anvil lesson's demonstrated strategy—establish the full extent, distribute
loops evenly, then shape the profile—transfer from a square-section anvil waist to a different
12-sided circular product form?

This run tests two captured items from `yi87Dap_WOc`:

- 05:07-05:40: repeated manual extrude-and-scale steps accumulate uneven spacing and profile error;
- 06:06-06:40: uniform loop distribution provides a controllable scaffold before deformation.

The predeclared hypothesis, controls, thresholds, and claim boundary are in
`experiment_contract.json`.

## Construction

Both lamp-pedestal variants use identical topology:

- one connected object per variant;
- 12 radial vertices and 13 axial rings;
- 156 vertices, 308 edges, 154 faces;
- 154/154 quads, including strip-quad top and bottom caps;
- 24 cap-perimeter edges selected for semantic bevel weight;
- WEIGHT-limited Bevel before Subdivision Surface;
- Smooth by Angle rather than blanket smooth shading.

The control deliberately contains uneven ring heights plus small deterministic per-step radius
errors. The candidate uses uniform ring heights sampled from the same declared smooth target
profile. This is a controlled failure reproduction, not a claim that any mesh made through manual
extrusion must fail.

## Results

Both the lab and independent fresh-process verifier pass every predeclared gate:

| Metric | Manual-step control | Uniform-ring candidate | Result |
| --- | ---: | ---: | --- |
| Ring-spacing CV | 0.389872 | effectively 0 | candidate passes |
| Profile RMSE | 0.015517 | 0.002778 | 82.10% reduction |
| Maximum profile error | 0.036000 | 0.005485 | lower |
| Side-quad aspect ratio p95 | 3.246915 | 1.466130 | 54.85% reduction |
| Base non-manifold edges | 0 | 0 | clean |
| Base non-quad faces | 0 | 0 | all quad |
| Evaluated non-manifold/degenerate | 0 / 0 | 0 / 0 | clean |

Visual review of the solid front/isometric images agrees with the metrics: the candidate carries a
more even transition through the waist; the base-cage wireframe makes the control's clustered and
stretched rings directly visible.

## Rejected attempts retained

1. The first Blender launch failed before saving because factory startup supplied no World
   datablock. The render setup now creates one explicitly; no geometry result from that launch was
   accepted.
2. The next run failed the semantic edge gate: 32 cap edges were weighted because the selector also
   included eight coplanar internal cap chords. `failed_semantic_cap_weight_report.json` preserves
   that result. The correction selects only adjacent perimeter-ring pairs, producing the required
   24/24 intended sharp edges.
3. The initial Workbench wire overlay produced a blank image. It was rejected and replaced by the
   repository's Blender-native wireframe diagnostic on modifier-disabled base cages. The final image
   has a 0.029789 foreground fill ratio and visibly shows both cages.

## Knowledge and planner outcome

The two source items advance from `CAPTURED` to `TRANSFER_VALIDATED`. The structured skill
`deformation.topology.uniform_rings_before_shaping` is now retrievable for matching smooth-profile
deformation defects.

The planner behavior is deliberately gated:

- without the skill, an `uneven_deformation_density` ticket remains `INSPECT`;
- a merely `CAPTURED` skill also remains non-actionable;
- the transfer-validated skill changes the matching localized ticket to the scoped
  `loop_cut_selection` action while preserving ticket-owned targets and parameters;
- non-manifold geometry still preempts the skill and triggers technical localization.

## Honest boundary

This is deterministic controlled transfer, not adaptive reference modeling. It validates one
principle on one different radial product form. It does not prove arbitrary deformation quality,
does not promote the skill to `RUNTIME_VALIDATED`, and does not add a successful `runtime_usage`
record. That requires a later real reference task where the planner retrieves the skill, the typed
runtime applies it, and the resulting asset improves without tuning to this fixture.
