# Held-out chair quality disposition

**Status: FAIL — not professional modeling evidence**

The run reached a normalized single-view silhouette IoU of 0.72747 against a predeclared 0.72
mechanical gate. That metric did not establish professional modeling quality.

User review correctly rejected the result as low-level primitive assembly. The scene decomposed the
chair into beveled cubes, converted curves, and spheres, then optimized one side silhouette. It did
not demonstrate authored cushion topology, controlled upholstery transitions/seams, robust
multi-view form development, or professional surface/highlight judgment. The system also spent too
much effort on infrastructure and metric iteration after the form strategy itself should have been
rejected.

Lessons retained:

1. A silhouette threshold is a diagnostic channel, never a professional acceptance gate by itself.
2. Primitive blockout is temporary; if it remains the final construction language, the asset must
   fail the topology/editability/form review even when the outline matches.
3. A side-view pass cannot substitute for front, top, perspective, surface, and component-transition
   review.
4. Repeated local silhouette patches should trigger `REBUILD_REGION` or strategy replacement, not
   continued metric optimization.
5. Held-out modeling must remain paused until the directive's foundation and judgment work is
   completed honestly.

The `.blend` and intermediate renders remain local diagnostic evidence and are not promoted as a
benchmark pass.
