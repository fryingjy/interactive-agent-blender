# Live Edit Mode BMesh and custom-data evidence

This bounded Blender 5.2.0 LTS lab closes the prior documentation-map gap around
`bmesh.from_edit_mesh()`, destructive `update_edit_mesh()`, valid selection flushing, and
representative current custom-data layers. It is an API fixture, not an authored asset or evidence
of professional topology judgment.

## Reproduce

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python tools\run_bmesh_editmode_customdata_lab.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python tools\verify_bmesh_editmode_customdata.py -- runs\2026-08-16_bmesh-editmode-customdata\bmesh_editmode_customdata.blend --output runs\2026-08-16_bmesh-editmode-customdata\fresh_verification.json
```

The builder records 11/11 passing assertions. The independent verifier opens the saved `.blend`
in a fresh process and passes 8/8 assertions for exact topology, attribute values, UV presence,
closure, nondegeneracy, and all-quad faces.

Official sources:

- <https://docs.blender.org/api/current/bmesh.html>
- <https://docs.blender.org/api/current/bmesh.types.html>
- <https://docs.blender.org/api/current/bmesh.ops.html>
