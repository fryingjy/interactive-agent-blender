# Blender Bros Hive-controller topology reproduction

Stage 2 of the tutorial-reproduction track studies the chapter of `3wJ81Ua7o_w` that simplifies
mismatched traced sections, reconnects them at a shared low resolution, and evaluates SubD pinching
near boundaries. The required artifact is a connected curved shell with a true opening and explicit
loop correspondence, followed by a different-geometry transfer.

Transcript-derived claims remain candidates until the relevant video/audio range is independently
checked and the technique survives Blender reproduction plus visual diagnostics.

## Result

The bounded chapter is complete. Actual Gemini audiovisual inspection of 18:20-32:30 was checked
against visible browser frames/captions, then reproduced as a connected controller-like shell around
a true opening. The first 64-quad cage plus boundary creases rendered cleanly but produced 243
diagnostic pinch candidates. Adding radial support while retaining creases overconstrained the same
boundaries and increased the count to 287. The retained support-only correction uses 128 authored
quads, one live unapplied SubD modifier, Smooth by Angle, and 19 candidates.

Transfer to a 12-point rounded-rectangular panel with an offset aperture produced 96 authored quads,
0 non-manifold edges, 0 n-gons, 0 degenerates, and 2 diagnostic candidates. The validated rule is
therefore narrower than "always crease": reconnect matched low-resolution loops, add only local
radial support needed by the silhouette, and do not stack crease control on support loops without
visual and evaluated evidence that both are required.
