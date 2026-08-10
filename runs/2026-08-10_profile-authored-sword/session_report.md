# Profile-authored fantasy sword rebuild

Date: 2026-08-10

Reference: `C:\Users\odane\Downloads\blender\ref\matteo-swordconcept244.jpg`

Reference SHA-256: `7F769045C6E3A3DFB2D30F54D7026FC5E23063365CC788703CE7F0D3767A0D09`

Outcome: **technical PASS; normalized silhouette PASS; human professional acceptance not claimed**

## Why this rebuild exists

The earlier `runs/2026-08-10_heldout-fantasy-sword/` artifact passed its predeclared technical and silhouette gates, but its beauty render still read as primitive assembly: rectangular guard bars, repeated ring bands, weak secondary form, and a flat blade treatment. That is a real quality failure even though the automated gate passed.

This replacement applies the supplied `.blend` example study and the learned Blender lessons to a new implementation of the same reference. Because the reference had already been used, this is a quality rebuild, not fresh held-out evidence.

## Construction

The builder contains no `bpy.ops.mesh.primitive_*` calls. Nineteen semantic mesh components are made from:

- an authored nine-section diamond blade with changing width and thickness;
- authored x/z profile solids for four guard wings, a central shield, recess, and blade inlay;
- explicit closed cross-section tubes following four guard-groove paths;
- lathed grip, collar, pommel, recess, and gem profiles;
- one 6.25-turn helical grip wrap built from explicit transported rings and capped as a closed solid.

Every component has a UV layer. Bevel and Triangulate modifiers preserve editable low forms while defining evaluated edge and delivery contracts. Seven named node materials separate steel, recessed steel, brass, guard recesses, leather, wrap edges, and ruby.

## Closed-loop visual result

The comparison crops the transparent candidate to its foreground and resizes it into the measured reference foreground box. This intentionally removes translation and scale; the score tests normalized contour/proportion, not unaligned framing.

| Revision | Normalized silhouette IoU | Contour error | Observation |
|---|---:|---:|---|
| first profile-authored build | 0.729432 | 0.011716 | blade width was too high near the tip; upper guard defined the maximum width; grip was too heavy |
| localized correction | 0.780904 | 0.008977 | blade improved; guard gesture and vertical placement still diverged |
| final localized correction | **0.836941** | **0.006961** | width shifted down the blade, wings shifted down, lower guard became dominant, grip narrowed |

The final score exceeds both the 0.80 benchmark threshold and the earlier primitive-like asset's 0.828469. The durable comparison is `silhouette_comparison.json`; `silhouette_overlay.png` shows reference-only pixels in red, candidate-only pixels in cyan, and intersection in white.

## Technical result

The first detail implementation used converted bevel curves. Rendering looked valid, but fresh-process verification found non-manifold seam edges on all four grooves and the wrap, producing only 14/19 clean components. `failed_curve_conversion_verify.json` preserves that rejection.

The corrected implementation creates explicit tube rings and cap fans. `fresh_collection_verify.json` was generated after reopening the saved `.blend` in Blender 5.2 factory-startup mode and reports **19/19 clean**. Every evaluated mesh has:

- zero non-manifold edges;
- zero n-gons;
- zero loose vertices and edges;
- zero degenerate faces;
- positive signed volume;
- at least one UV layer.

## Evidence

- Editable asset: `profile_authored_sword.blend`
  - SHA-256: `4E7CDEB38837908D0CF207C1722A9B231ACBE6E3777127D3D7C08AD35957E2D2`
- Reproducible builder: `tools/run_profile_authored_sword_benchmark.py`
- Fresh verifier: `tools/verify_collection_meshes.py`
- Alignment/comparison tool: `tools/align_silhouette_to_reference.py`
- Beauty reviews: `front_beauty.png`, `side_beauty.png`, `isometric_beauty.png`
- Shape evidence: `front_alpha.png`, `reference_mask.png`, `candidate_mask_aligned.png`, `silhouette_overlay.png`, `silhouette_comparison.json`
- Structural evidence: `build_report.json`, `fresh_collection_verify.json`

## Honest limits

- This is a stylized hard-surface prop, not evidence of realistic weapon engineering.
- Smart-projected UV presence is verified, but texel density, texture painting, and high-to-low baking were not part of this rebuild.
- One normalized front contour cannot prove back-side detail, production texturing, deformation behavior, or broad modeling mastery.
- The model has not received independent experienced-modeler acceptance; automated metrics do not substitute for that judgment.
