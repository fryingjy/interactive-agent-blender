# Reference: lever door handle (second replacement transfer-test candidate)

**Built 2026-08-14** (`runs/2026-08-14_transfer-test-doorhandle-grown-lever/`): rose, boss, and
lever arm as one continuous 300-vertex mesh, 0 non-manifold edges throughout. Transfer test PASSED
against the connected-topology principle -- see the run's brief.md for the full record, including
one honest limitation (the tip curve undershot the spec's 30-40deg target, landing closer to 8-9deg).

Written proportions spec (no image download requested). A deliberately different form factor from
the mug/teapot family (not a revolved vessel with an appendage) -- tests the same "connected
topology, not a separate touching object" principle on a mechanical/hardware object instead of a
container, so it doesn't just retest the vessel-plus-handle case a second way.

- Rose (the round wall-mounted base plate): a flat cylindrical disc, diameter ~2.2 units, thickness
  ~0.25 units, with a small edge bevel and a central spindle hole (diameter ~0.5 units) through it.
- Spindle boss: a short cylindrical collar grown from the rose's face around the spindle hole,
  standing proud by ~0.4 units, diameter ~0.9 units -- this is where the lever actually attaches,
  and it must read as one continuous piece with the rose, not a separate ring merely touching it.
- Lever arm: grown from the spindle boss (extrude/loop-cut/bridge from the boss's own mesh, not a
  separate primitive), extending outward roughly horizontal for ~3.5 units, then curving gently
  downward at the far end (~30-40 degrees) -- the classic lever-handle silhouette. Cross-section
  tapers slightly from a thicker base near the boss (~0.6 units) to a slightly narrower grip
  section (~0.45 units) partway along its length.
- Symmetry: the rose/boss are rotationally symmetric; the lever arm is a one-off asymmetric
  extrusion in a single direction, matching the mug/teapot handle's asymmetric-detail pattern but
  on an entirely different base form.
- Wall thickness: solid throughout for this milestone.
- Why this is a useful second candidate alongside the teapot: the teapot re-tests the exact
  vessel-plus-appendage case the mug failed on (now with two appendages instead of one); this one
  deliberately changes the base object type so the connected-topology lesson gets tested as a
  general principle, not just as "know how to build a mug handle specifically."
