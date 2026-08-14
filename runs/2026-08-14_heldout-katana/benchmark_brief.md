# Held-out benchmark: stylized katana + saya (scabbard) + tsuba

**Status (2026-08-14): PAUSED, deprioritized.** The blade blockout (typed-modeler revision 8) was
built with an acknowledged flaw (an angular kink rather than a smooth sori curve) and the user
called the direction out directly: "you were horribly inaccurate... start with simpler
shapes/props/models and work your way up because you genuinely dont know what you're doing in
terms of modelling it." The unsaved live-scene blade WIP was removed (nothing had been written to
a `.blend` file yet, so nothing on disk was lost). This matches a now-consistent pattern across
every complex held-out asset attempted in this project (boombox, camera assembly, adjustable
wrench, watering can, telephone): automated/topology checks passed cleanly every time, yet direct
visual review rejected the result every time. The reference material, frozen brief, and scene
decomposition below remain as durable knowledge; the katana build itself does not resume until a
run of genuinely simple shapes has been visually validated first, per
`feedback_start_simple_build_modeling_skill` guidance.

**Frozen before modeling**, per `docs/MASTER_DIRECTIVE.md` Section 3 and the pasted implementation
directive's Phase A. Source: `held_out_reference_registry.json`'s
`e1b39bffaae0d8e9dee5c2ff0d505895.png` entry (status `PROVIDED_UNMODELED_RESERVED_TRANSFER` prior to
this run) -- a supplied stylized illustration, not a photograph.

## Source honesty (per REFERENCE_COLLECTION_PROTOCOL.md)

Attempted to identify the exact source character/game via web search (two queries on distinctive
visual elements: oni-mask character, red lacquered saya, diamond-patterned grip, scalloped tsuba) to
find additional official reference views -- no exact match found, only generic real-world replica
products and stock illustrations. No reverse-image search available in this environment. Proceeding
on the single supplied illustration; this is a recorded, deliberate limitation, not a skipped step.

Single image file, but it contains four real sub-views: an unsheathed blade+tsuba+grip (top,
profile), the same assembly sheathed in the saya (second profile), a separate tsuba close-up (disc,
near-frontal), and a small character-holding-sword silhouette (context only, not used for
proportions). No true orthographic front/side/top set, no dimensional anchor, stylized/exaggerated
proportions likely (the blade curve and length-to-width ratio look artistically emphasized, not
photographically accurate). Confidence on exact proportions: MEDIUM at best, same tier as this
project's own prior single-illustration benchmarks (`fantasy_ceremonial_sword_001`,
`transfer_d_stylized_trident_001`), not a photographed/CC0-scanned product.

## Construction contract

Per `DEVELOPMENT_PRIORITIES.md`'s connected-topology rule and `docs/MASTER_DIRECTIVE.md` Section 6:

- **Blade**: one connected, profile-authored cage (curved katana blade with a distinct spine/edge
  taper toward the tip) -- no mesh-primitive assembly. This project has validated profile/lathe
  authored blade construction before (`profile_authored_sword`, `profile_authored_axe`); reuse that
  proven technique, not a fresh untested one.
- **Tsuba (guard)**: one connected disc with an ornamental cutout/scalloped silhouette (visible in
  the close-up sub-view) and a center aperture matching the blade's cross-section -- a separate
  object is justified (a real assembled, separately-manufactured guard).
- **Grip (tsuka)**: separate object, wrapped/ribbed cylindrical form -- justified as a separately
  wrapped/assembled part.
- **Saya (scabbard)**: one connected, curved tapered tube open at one end -- separate object,
  justified (a genuinely separate, removable sheath).
- Sharp-edge policy: decide per part from direct visual inspection at construction time, not
  assumed in advance -- per this project's own hard-earned lesson (`edge_crease.md`), do not default
  either mechanism without checking whether the part shows a visible chamfer (Bevel) or a soft/flat
  read with no visible chamfer (crease), and never crease a revolved ring's own circumferential loop.

## Predeclared gates

Silhouette/proportion gates are intentionally NOT frozen at a specific IoU threshold here, given the
MEDIUM-confidence single-illustration source (a photographed CC0 asset would get frozen numeric
gates; a stylized illustration's "correct" proportions are inherently softer). Instead:

1. Each of the four components (blade, tsuba, grip, saya) must be traceable to the reference's own
   sub-view it was measured from.
2. Fresh-process verification: 0 non-manifold edges, 0 degenerate faces, correct evaluated signed
   volume, per object.
3. `knowledge_engine/scene_decomposition.py` coverage check: a declared component decomposition
   written BEFORE construction, checked against the actual built object names after.
4. Direct visual comparison against the reference sub-views before declaring any stage complete --
   the single most important lesson from every asset built this same week.
5. Construction primarily through the live typed modeler (`mcp__modeler__*`) decision-transaction
   path now that it is connected, with any raw-script/Blender-Connector fallback explicitly
   disclosed per `docs/MASTER_DIRECTIVE.md` Section 8.

## Planned loop

Reference sub-view extraction -> scene decomposition (structured) -> primary blockout (blade
silhouette first, since it dominates the form) -> checkpoint against reference -> tsuba/grip/saya
secondary forms -> checkpoint -> topology/shading pass -> fresh verification -> report.
