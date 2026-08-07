# Reference: sci-fi wristband gadget (first actual-image milestone)

The project's first benchmark using a real reference IMAGE rather than only a written proportions
spec (directive section 10/50/55 item 13 -- "the next benchmark must use an actual image
reference, not only structured text notes").

## Source and selection

Sourced from the user's own `C:\Users\odane\Downloads\blender\ref` folder, per their explicit
instruction to pick the simplest reference there. That folder is dominated by weapon references
(real handgun/replica-sword product photos, fictional combat-game weapon concept art) --
`docs/MASTER_DIRECTIVE.md` section 1 explicitly excludes real-world weapon-construction
references from this project's learning material, and more generally the curriculum's first
image benchmark (section 10) calls for a *simple*, clear-silhouette, limited-component object,
not a weapon. `da2vssl-1c8dd218-9334-479b-94a5-dcb9d2099327.png` -- an isolated, clean turnaround
render of a stylized sci-fi wristband gadget (a wearable device with a domed rotating dial, a
textured wristband, and two side buttons) -- was the clearest non-weapon match in that folder:
single object, plain background, clear silhouette, bounded component count. Flagged this
substitution to the user rather than silently picking without explanation, since it deviates from
"simplest" taken literally (several weapon images were visually simpler).

## What the reference shows

- A rounded dome/cap assembly on top, with a raised circular bezel and an angular dark
  "hazard/warning" style graphic on its face.
- A wide wristband wrapping below the dome, with a lighter horizontal panel section and a
  darker ribbed/textured lower section.
- Two small cylindrical buttons/protrusions on opposite sides of the dome, roughly
  perpendicular to the band.
- Overall silhouette: a compact, rounded-cylindrical primary form (the dome) sitting on a
  curved secondary form (the band), a moderate number of distinct components rather than a
  single primitive -- appropriate first complexity step up from the soap dish's single-body
  form.

## What this milestone is actually testing

Per directive section 10, this isn't about matching this exact prop perfectly -- it's the
project's first real test of:

```
reference image -> visual decomposition -> primary blockout -> Blender-native silhouette
comparison -> local correction -> topology/surface review -> independent verification
```

Exact component breakdown, proportions, and control-cage topology are intentionally not
pre-specified here -- deciding those from the image is the actual exercise.
