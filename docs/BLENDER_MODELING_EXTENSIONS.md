# Blender modeling extensions

## Installed and enabled for Blender 5.2

The official Blender Extensions repository was synchronized on 2026-08-11. Blender's Online Access
preference was enabled at the user's request. The following modeling-focused extensions were then
verified as enabled in the live Blender process and persisted to user preferences:

| Extension | Use |
| --- | --- |
| LoopTools | Circle, relax, space, bridge, curve, and loop cleanup workflows |
| F2 | Faster face/edge construction in Edit Mode |
| EdgeFlow | Redistribute selected topology along curved surfaces |
| Auto Mirror | Fast symmetric modeling setup |
| Bool Tool | Interactive hard-surface Boolean workflow |
| tinyCAD Mesh Tools | Precision mesh intersections and CAD-like construction |
| Texel Density Checker | UV texel-density measurement and normalization |
| Magic UV | Expanded UV editing tools |
| Material Utilities | Material assignment and selection utilities |
| Bsurfaces GPL Edition | Surface construction and retopology |
| MeasureIt | Scene and object measurement |

LoopTools, F2, EdgeFlow, Auto Mirror, Bool Tool, tinyCAD, Texel Density Checker, Magic UV, and
Material Utilities were already installed but disabled. Bsurfaces, MeasureIt, 3D Print Toolbox, and
Precision Drawing Tools were installed from `extensions.blender.org`; all fourteen were initially
enabled and confirmed through `addon_utils.check()` on their fully qualified
`bl_ext.blender_org.<package_id>` module names as `(loaded=True, enabled=True)`.

At the user's request, ND (the HugeMenace non-destructive toolkit), 3D Print Toolbox, and Precision
Drawing Tools were then removed. Their extension packages are no longer installed, their preference
entries are absent, and the open Blender process reported `(loaded=False, enabled=False)` for all
three after saving preferences. The retained modeling set therefore contains eleven extensions.

Machine-readable local validation:
`runs/2026-08-11_connected-camera-corrective/blender_environment_report.json`.

Official CLI reference:
<https://docs.blender.org/manual/en/latest/advanced/command_line/extension_arguments.html>

These tools expand interactive modeling capability. Their presence is not evidence that a technique
was learned or that an asset is correct; each workflow still requires controlled use and evaluated
geometry/visual checks.
