# Blender MatCap resources

## Installed user set

On 2026-08-11, 15 user MatCaps from **Assorted Matcaps** by hecko were installed for Blender
5.2. They are licensed CC0 and distributed from:

- Source page: <https://opengameart.org/content/assorted-matcaps>
- Archive: <https://opengameart.org/sites/default/files/assorted_matcaps.zip>
- Downloaded archive SHA-256:
  `C12C0C29C684CAAB060361AC06322548AE01AE2C43BE3E93296822A83646FBA0`

Blender's own API resolved the user installation directory as:

```text
C:\Users\odane\AppData\Roaming\Blender Foundation\Blender\5.2\datafiles\studiolights\matcap
```

Files are prefixed `CC0_Hecko_` to preserve provenance and avoid collisions. A clean Blender 5.2
process refreshed Studio Lights and recognized all 15 files as user-defined MatCaps. The live
Blender process was refreshed again on 2026-08-11 and recognized 42 usable MatCaps total: 27
built-in review MatCaps plus the 15 CC0 user additions.

Machine-readable local validation is recorded in
`runs/2026-08-11_connected-camera-corrective/blender_environment_report.json`.

A much larger public GitHub MatCap dump was reviewed but deliberately not installed: its own license
notice says original author/source relationships were not retained. Quantity without usable
provenance is not an acceptable asset-library upgrade.

The images are intentionally not duplicated in this repository. They remain in Blender's user-data
directory under their source license. A Blender process that was already running during installation
must refresh Studio Lights or restart before its MatCap menu shows the new entries.

## Selection guidance

- Use Blender's built-in `hard_surface_grey.exr`, `clay_studio.exr`, or another neutral MatCap for
  topology, edge flow, and highlight review.
- Use the CC0 skin, pearl, glass, dark-latex, and rim-light variants for secondary material/form
  inspection, not as substitutes for neutral topology evidence.
- MatCap and Solid Workbench renders are fast review channels. They do not replace final
  material/lighting renders when a production material claim is being evaluated.
