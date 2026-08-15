# Blender add-on resource-safety optimization

**Status:** PASS for the bounded code/resource-lifecycle scope.

## Problem found

The root Blender connector add-on had several concrete resource defects:

- external HTTP calls could wait forever because `requests` has no default timeout;
- HDRI cleanup called private global `tempfile._cleanup()` instead of deleting its own file;
- duplicate Hyper3D streaming implementations leaked completed files after successful import;
- Sketchfab cleanup was repeated on selected returns but absent on other exception paths;
- Hunyuan archive cleanup removed only two known files and left the extraction directory plus any
  MTL/texture dependencies;
- the asynchronous Hunyuan GLB callback leaked its file when Blender import raised.

## Implemented correction

`addon.py` now has one streamed temporary-download helper with partial-file rollback, one exact-path
unlink helper, explicit `(connect, read)` timeout policies, and lifecycle ownership around every
inspected temporary file or directory. Poly Haven images are packed before their backing files are
removed. The two Hyper3D import paths share the same downloader. Sketchfab and Hunyuan extraction
trees are removed from `finally` paths, and the asynchronous GLB importer also cleans up from a
`finally` block.

## Purge decision

No tracked file was deleted. The pre-change inventory found 488 tracked files, zero exact duplicate
groups, zero forbidden tracked artifacts, and zero unclassified root files. The tracked `.blend`,
render, transcript, and local-video files are unique dated evidence referenced by the repository's
knowledge and audit history. Calling them irrelevant without contrary evidence would destroy the
failure/verification record that the master directive requires retaining.

## Verification

- `python -m pytest -q`: 72 passed.
- New resource-safety regression tests: 4 passed, including an interrupted stream whose partial file
  is proven absent afterward.
- Static AST policy: 23/23 `requests` calls have explicit timeouts.
- `python -m pyflakes addon.py blender_ops knowledge_engine tests tools`: PASS.
- `python -m compileall -q addon.py blender_ops knowledge_engine tests tools`: PASS.
- `python tools/audit_repository.py`: PASS.
- Blender 5.2 factory-startup import/register/unregister: PASS.

The checks do not claim that every third-party API accepted a live request; no credentials or paid
service calls were needed for this bounded resource-lifecycle correction.
