# JL Mussi energy-can tutorial reproduction

This is lesson 1 of the tutorial-led modeling reset. The source is JL Mussi's beginner hard-surface
energy-can build (`tRZh0K8R8mQ`). It was selected because it directly exercises the weaknesses seen
in rejected prop work: connected edit-mode construction, detail-driven density, deliberate loop
flow, quad caps, SubD control, and visual shading inspection.

A lesson is not complete because its transcript was summarized. Required evidence is: bounded
audiovisual review, an actual reproduction of the tutorial model, base/evaluated topology inspection,
solid and reflective diagnostics, a documented failure/correction loop, and a different-geometry
transfer test. Modifiers remain live in the learning file unless applying one is itself the lesson.

## Result

- `energy_can_surface.blend` contains four functionally justified components: one continuous
  revolved body, a separate manufactured lid, one connected pull-tab shell with two true openings,
  and a rivet pin. No stacked cylinders form the body.
- The first render was rejected because the lid floated, the base transition ballooned, and the
  positive-radius revolution made the rivet look like a torus. The v2 profile corrects all three.
- The fresh Blender 5.2 inspection reports an all-quad, manifold base mesh with live, unapplied
  modifiers. Solid and MatCap renders remain diagnostic evidence rather than a polished render.
- The different-geometry bottle comparison confirms that support distribution can reduce SubD
  volume loss, but also shows that clustered loops create new pinch candidates. The transfer rule
  is targeted, visually inspected density—not indiscriminate densification.

This completes one bounded beginner reproduction. It does not establish advanced modeling skill or
authorize a return to held-out prop reconstruction.
