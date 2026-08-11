# Intro to Shading: source-to-skill study

## Source and access

- Official source: [Intro to Shading - Blender 2.80 Fundamentals](https://www.youtube.com/watch?v=RRilLLyyn1Y), Blender / Dillon Gu
- Legal processing copy: [Wikimedia Commons, CC BY 3.0](https://commons.wikimedia.org/wiki/File:Intro_to_Shading_-_Blender_2.80_Fundamentals.webm)
- Duration: 276.521 seconds
- SHA-256: `cdc7d3a0a49aee26b3624e74c044be88903d23f944f93e9000ddc80f8cf9639f`
- Inspected: audio, 11 decoded checkpoints, and 47 local `tiny.en` machine-transcript segments
- Version limit: the UI is Blender 2.80; node/material/world/render-context concepts were checked through Blender 5.2 experiments.

## Timestamped observations and bounded reasoning

- 00:30: the Shading workspace exposes object material, world context, image/file access, and the node editor together. Appearance diagnosis must identify which context is active.
- 01:00: one object can carry multiple material slots. A localized appearance change can therefore be material assignment rather than changed geometry.
- 01:30: a new slot/material datablock is visible independently of the mesh shape. Material-state comparison is a useful causal intervention.
- 02:00: world shading is a separate node context. A background/environment change can alter the whole review without any asset mutation.
- 02:30-03:00: render-engine and rendered-preview choices change what evidence is visible. A viewport appearance is not automatically equivalent to the final render path.
- 03:30-04:00: Workbench, material preview, and rendered contexts expose different combinations of geometry, material, world, and lighting. Compare contexts rather than diagnosing from one beauty image.

This lesson does not deeply teach mesh normals or topology defects. It is credited only for separating material, world/lighting, render engine, and viewport contexts.

## Different-shape transfer

The rule was transferred to a manually authored chamfered product enclosure (not a mesh primitive). Five controlled discrepancies changed one causal family at a time: base geometry, one face orientation, material assignment/roughness, lighting rig, or bevel profile. A conservative classifier consumes state comparisons plus a matching repair intervention:

- geometry requires base/evaluated geometry and silhouette/depth change;
- normals require fixed geometry, changed orientation/split-normal state, and a neutralizing normal repair;
- material requires fixed geometry/normals and a neutralizing material override;
- lighting requires unchanged object state and a neutralizing light-rig replacement;
- bevel requires changed bevel parameters/evaluated topology and a neutralizing bevel repair.

All five controlled labels classified correctly. Every defect changed more than 100 pixels above a 0.02 RGB threshold; measured changed-pixel counts ranged from 4,089 (material) to 68,737 (lighting). Mixed qualifying signatures return `CONFLICTING`, and insufficient evidence returns `UNRESOLVED`.

Fresh Blender 5.2 verification passed 5/5 evaluated specimens: closed manifold, zero n-gons/loose/degenerate geometry, positive volume, and UVs.

## Retained failures and limits

The first render crashed in the Intel OpenGL driver during shutdown, the first collection audit targeted an empty collection, and the first authored enclosure winding produced negative volume. All are retained in `failed_runs.json`; none was accepted as a pass.

This is a controlled intervention protocol, not screenshot-only automatic diagnosis. Real assets can contain multiple simultaneous causes, and the normal case covers a flipped face rather than every custom-normal pathology. Production mixed-cause transfer remains open.
