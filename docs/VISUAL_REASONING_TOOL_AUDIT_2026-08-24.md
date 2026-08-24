# Visual-reasoning and modeling-tool audit — 2026-08-24

## Decision

The largest capability gap is **semantic visual verification and 3D interpretation**, not Blender
command coverage. The repository can create, inspect, roll back, render and validate clean editable
meshes, yet a generic or wrongly represented asset can still pass topology and silhouette checks.

The highest-leverage feasible addition on this computer is a remote multi-image semantic critic
paired with existing deterministic measurements. `knowledge_engine.gemini_reference_critic` is the
first implementation. It compares hash-bound reference/candidate pairs, returns localized mismatch
tickets, and fails closed on contradictory advancement. It may block surface treatment; it cannot
grant human acceptance.

## Environment constraint

The host has Intel UHD integrated graphics, about 1 GB reported adapter memory, no NVIDIA runtime,
and no local PyTorch installation. Installing CUDA-first 3D foundation models here would create a
large nonfunctional dependency surface rather than improve modeling.

## Evidence from current systems and research

| Candidate | What it contributes | Fit here | Decision |
| --- | --- | --- | --- |
| [Gemini image understanding](https://ai.google.dev/gemini-api/docs/image-understanding) | Multiple images, structured output, normalized boxes and segmentation polygons; remote execution | Strong. Existing API key and SDK work without local GPU | **Implemented now** as semantic critic |
| [GPTEval3D](https://github.com/3DTopia/GPTEval3D) / [paper](https://arxiv.org/abs/2401.04092) | VLM pairwise comparison across many RGB and normal views aligns with human preferences better than narrow metrics | Strong architectural evidence; its 120-view tournament is excessive per edit | Adopt multi-view RGB/normal comparison and conservative verifier logic |
| [BlenderGym](https://github.com/richard-guyunqi/BlenderGym-Open) / [paper](https://arxiv.org/abs/2504.01786) | Generator/verifier trees; verifier-side inference scaling improves graphics editing, while current VLMs still struggle on human-easy tasks | Directly relevant | Add verifier passes before spending more mutations; do not assume a VLM is a professional modeler |
| [fSpy](https://github.com/stuffmatic/fSpy) and [Blender importer](https://github.com/stuffmatic/fSpy-Blender) | Calibrated still-image camera matching from vanishing lines | Useful only for perspective photos with reliable parallel-line evidence | Do not install globally yet; invoke when a selected target satisfies its assumptions |
| [PartCrafter](https://github.com/wgsxm/PartCrafter) / [paper](https://arxiv.org/abs/2506.05573) | Single-image multi-part 3D hypotheses, including occluded parts | Potentially useful as a component/depth hypothesis | Cloud/demo-only candidate. Local path requires CUDA and at least 8 GB VRAM; output is not authored topology |
| [CAD-Coder](https://github.com/anniedoris/CAD-Coder) / [paper](https://arxiv.org/abs/2505.14646) | Editable CadQuery code from images for CAD-like forms | Promising for regular manufactured parts, not stylized SubD surfaces | Retain as future representation hypothesis; local LLaVA/flash-attention stack is unsuitable here |
| [CAD-Recode](https://github.com/filaPro/cad-recode) | Point cloud to editable CadQuery code | Useful only after trustworthy point-cloud acquisition | Not an image-reference solution by itself; ZeroGPU demo may support bounded future tests |
| [MeshAnything V2](https://github.com/buaacyw/MeshAnythingV2) | Re-meshes a dense shape into an artist-like mesh, capped below 1,600 faces | Poor local fit: about 8 GB VRAM on A6000; input quality dominates output | Do not install. Its own issue history retains an axe failure and density/accuracy tradeoff |
| [Hunyuan3D 2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | High-fidelity image-to-shape and PBR hypothesis mesh | Existing connector may make remote bounded use possible | Never treat as final topology. Local shape needs about 10 GB VRAM; full shape+texture about 29 GB |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | High-resolution image-to-3D with complex/open topology and PBR | Not locally viable | Requires Linux plus NVIDIA GPU with at least 24 GB; current host has neither |
| [DUSt3R](https://github.com/naver/dust3r) / [MASt3R](https://github.com/naver/mast3r) | Sparse-view camera/point-map reconstruction for same-scene photographs | Potential depth/camera evidence when genuine same-object views exist | Non-commercial license and PyTorch/GPU burden; evaluate remotely only for an actual matching case |
| [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) and [SAM 2](https://github.com/facebookresearch/sam2) | Monocular depth and segmentation | Useful evidence channels, but local foundation models add GPU burden | Gemini already supplies remote segmentation; depth remains a hypothesis unless cross-view corroborated |

Reddit's public search and JSON endpoint were both attempted. The site required a CAPTCHA and
returned HTTP 403 to the public API, so no Reddit claims are represented as inspected evidence.
GitHub issues supplied practitioner-level counterevidence instead.

## Implemented architecture

```text
same-target references
  -> deterministic masks, bounds, landmarks and projection checks
  -> sparse editable base cage
  -> solid + wireframe + normal/depth renders
  -> hash-bound Gemini semantic comparison
  -> localized representation/component/proportion/depth tickets
  -> one typed corrective mutation
  -> re-render and re-critic
  -> surface gate only after deterministic and semantic passes
  -> human visual review still decides acceptance
```

The critic deliberately excludes effort, modifier sophistication, clean topology and materials from
its likeness judgment. Every image path and SHA-256 is retained in the output. A model-produced
`ADVANCE_TO_SURFACE_CANDIDATE` is rejected if any supplied score is below 0.90 or any mismatch has
severity above 0.10.

## Real failure replay

The first live replay compared Grant Abbitt's actual side-orthographic lesson reference with the
old technically clean sword render:

- semantic match: `0.35`;
- silhouette match: `0.30`;
- component relationship: `0.40`;
- decision: `REJECT_REPRESENTATION`;
- detected faults: missing upward sweep/wide belly and the wrong generic collar construction.

This is the same failure the user identified visually. The result is retained in
`runs/2026-08-24_tutorial-grant-abbitt-sword-reference-rebuild/old_candidate_gemini_critic.json`.
It proves the critic can expose one known failure; it does not prove reliable professional judgment.

## Next validation

1. Produce a measured raw cage from the actual lesson reference.
2. Render side, isometric, wireframe and normal channels before modifiers.
3. Run deterministic and Gemini review.
4. Correct only the highest-severity ticket and re-review.
5. Test a second unrelated manufactured/weapon form before promoting the critic as generally useful.
6. Add a second verifier pass only after the first real false positive or missed mismatch reveals
   what the extra inference must check.
