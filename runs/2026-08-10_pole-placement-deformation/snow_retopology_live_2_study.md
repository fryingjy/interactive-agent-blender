# Snow retopology live #2: source-to-skill study

## Source and inspected modalities

- Source: [Snow - Stylized Character Retopology Live #2](https://www.youtube.com/watch?v=tRqCeWZLqQo)
- Creator/uploader: Blender Studio
- Published: 2021-04-22
- Duration: 7,938.020136 seconds
- Processing copy SHA-256: `c839efc9c4982e94b1cc01256165bd8afc88a5694d10202b9c5ceb7d5b8a79dd`
- Inspected evidence: video, audio, 27 decoded checkpoints, and 4,595 automatic-caption segments
- Caption limitation: automatic captions are fallible. Important claims below were checked against decoded frames; wording is paraphrased, not quoted.

## Timestamped visual and reasoning observations

- 00:05:00: eye, mouth, and jaw loops establish facial deformation regions rather than merely tracing the resting silhouette.
- 00:10:00: three- and five-valence poles redirect flow between mouth and eye patches. The reason is to delimit readable regions without carrying every loop through the entire head.
- 00:15:00: facial rings and redirections are inspected by following where loops actually lead; a locally tidy patch can still create an unwanted spiral downstream.
- 00:25:00: the forehead patch demonstrates adding and removing loops in response to form, then relaxing spacing without moving critical landmarks.
- 00:45:00: loops are reduced before entering the neck. Density follows deformation and silhouette need instead of remaining uniform.
- 01:00:00: ear and rear-face patches use lower density than eye and mouth regions and move redirections away from stronger creases.
- 01:15:00: cheek-to-ear routing shows that poles should delimit patches while avoiding high-motion or tightly supported crease zones.
- 01:30:00 and 01:45:00: inner-ear topology is intentionally simpler than the face. Support/proximity loops preserve sharper folds after subdivision, but unnecessary loops are removed.
- 02:00:00: the inner mouth is extruded as a functional structure rather than faked into the outer lip surface.
- 02:10:00: the completed facial layout is evaluated as connected patches. Reusable topology still requires expression testing; static appearance alone is insufficient.

Additional lesson rules corroborated by frames and captions:

- Avoid six-or-higher valence where a three/five-pole redirection can keep the patch readable.
- Keep poles away from sharp proximity-loop creases and primary articulation when possible.
- Match upper/lower eye-loop counts when closure is a requirement.
- Use localized relax/smoothing while protecting landmarks and sharp folds.
- Add or remove loops responsively; topology density is a functional allocation, not decoration.

## Different-shape transfer

The facial rule was transferred to a non-face articulated tapered hose. Three otherwise controlled cages were evaluated with Subdivision Surface level 2 and the same explicit 92-degree circular-arc deformation:

1. all-quad reference;
2. an identical diagonal five-pole pair away from the bend;
3. the same pole pair inside the bend.

Against the all-quad bent reference, the away case produced bend-zone mean nearest-surface error `4.136976507061967e-08`; the in-bend case produced `0.00014221976184966483`. The in-bend error was `3437.7705942223893x` larger. This supports the bounded rule that an avoidable redirection should be moved out of the principal articulation zone when the surrounding topology and deformation are otherwise held constant.

Fresh Blender 5.2 factory-startup verification passed 6/6 evaluated meshes: closed manifold, no n-gons, no loose or degenerate geometry, positive signed volume, and UVs present.

## Retained failure and correction

The first Simple Deform setup aligned the tube and bend axis so the centerline stayed straight. A second orientation produced a bow-tie/hourglass rather than a hose. Both were rejected after visual review. The accepted experiment evaluates the same subdivision settings first and then applies an explicit analytic arc, removing modifier-axis ambiguity.

## Bounded conclusion

This experiment validates a geometric mechanism on one subdivided tube; it does not prove facial animation quality, skinning, expression-loop behavior, or every all-quad pole pattern. Nearest-surface error measures deviation from a control, not artistic appeal. Rigged facial expression transfer and independent professional acceptance remain open.

Artifacts: `pole_placement_deformation.blend`, `pole_placement_comparison.png`, `pole_placement_deformation_report.json`, `fresh_collection_verify.json`, and `failed_simple_deform_axis.json`.
