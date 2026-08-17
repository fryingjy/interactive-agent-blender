# Ian McGlasham -- "A better cylinder" (Subdivision Surface Modelling series)

Video `pWOh9cWwYqU`, 5:29, channel `@IanMcGlasham`. Transcript-only extraction. Not a routine
curriculum pass -- this is problem-driven research against a real, freshly-discovered defect
(`runs/2026-08-17_flashlight-model/`), following direct user instruction to research and fix, not
just narrate, an identified modeling weakness.

## The problem that sent me here

The user directly stated the flashlight held-out build's modeling quality was bad and asked to see
actual shaded Blender renders instead of silhouettes. The first real beauty render
(`beauty_iso.png`) showed a visible concave crater/dimple at the front cap -- completely invisible
in every silhouette render shown earlier, which is itself a real lesson: silhouette-only comparison
is not sufficient to catch surface-quality defects.

## Diagnosis, then the fix, both done live

Queried the mesh directly rather than guessing: exactly 32 faces (one per radial segment of the
revolve) had all four vertices within 0.5 units of the revolution axis, and those faces connected
the tail-tip ring at z=0 to the front-tip ring at z=25.4 -- an implicit long, thin, near-degenerate
quad strip running the object's full length, created by this project's own `revolve_closed_profile`
helper's wraparound closing behavior when a profile pinches to near-zero radius at both ends.

This video was picked specifically because its channel (Ian McGlasham) is already a trusted source
in this project's own knowledge base (`mcglasham-subd`, cited as the single strongest item in the
Level 14 synthesis run two days prior) and its title directly named the exact object category
(cylinder) and exact tool (Subdivision Surface) at issue. It confirmed the general failure mode
(naive n-gon/triangle-fan caps break visibly under Subsurf) and gave the general fix pattern (inset
away from the edge, use a real control loop, Grid Fill instead of a pole).

The flashlight fix applied the simpler half of that pattern immediately: delete the 32 pathological
"spine" faces (identified by the geometric query above, not by trial and error), then cap each of
the two resulting open rings with a single ngon via `fill_selection`. Re-rendered:
`beauty_iso_v2.png` / `beauty_side_v2.png` show a clean, correctly rounded cap -- no dimpling.

## Items captured (2)

1. FAILURE, `TRANSFER_VALIDATED` -- the near-zero-both-ends pinch produces a long degenerate spine
   that breaks Subsurf shading; caught and fixed within the same session on the same asset (a
   same-build transfer test, not yet tested on a different asset).
2. PROCEDURE, `CAPTURED` -- the full McGlasham technique (inset for a proper corner pole, control
   loop, Grid Fill instead of a bare cap) is the natural next refinement; only the simpler
   delete-and-ngon-cap half of it was applied so far. The flashlight's neck/shoulder transition still
   has no explicit holding loop and would benefit from the same control-loop treatment.

## Not captured as a separate item

The video continues into cone-capping technique (5:20 onward) -- not relevant to this session's
cylindrical/revolved-body problem, not watched/extracted.
