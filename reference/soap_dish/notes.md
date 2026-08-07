# Reference: smooth rounded soap dish (subdivision-surface milestone)

Genuinely unseen for this milestone. Deliberately the first prop in this project to require
subdivision-surface workflow — every prior prop (Bottle, Flashlight, Mug, SpeakerEnclosure) used
flat-panel bevels on a mesh that was already its own final surface. This one is different in kind:
the control cage is not the final surface, a Subdivision Surface modifier is, and the modeling
problem is edge flow / support-loop placement / pole placement under that modifier — matching
curriculum step D (subdivision-surface modeling), the next step after C (simple hard-surface forms,
now covered by four props).

- Overall form: a rounded rectangular dish, roughly 2.6 wide (X) x 1.8 deep (Y) x 0.6 tall (Z),
  smooth and continuous, no sharp edges anywhere — the entire silhouette should read as soft and
  rounded once subdivided, not faceted.
- Top surface: a shallow concave scoop/basin across most of the top face, smoothly blended into the
  surrounding rim — not a hard-edged recess like the speaker enclosure's driver cavity. The scoop
  should read as one continuous curved surface under subdivision, with no visible pinching, faceting,
  or discontinuity at the transition between the scoop and the rim.
- Bottom: flat enough to sit stably on a surface (a slight rounded taper is fine, does not need to be
  perfectly flat).
- Symmetry: bilaterally symmetric on both X and Y (a simple, everyday desk-object silhouette, not
  asymmetric like the mug handle or the speaker's driver placement).

Exact control-cage topology (edge count, support-loop count/spacing, pole placement) is
NOT pre-specified — that is the actual judgment this milestone exists to exercise. Use
`evaluated_mesh_health`/`evaluated_surface_quality` (reads the true Subdivision-Surface-evaluated
result, not the control cage) to judge whether the scoop transition actually reads as smooth,
rather than assuming the control cage's own topology stats are sufficient. If a real pinching or
topology problem shows up that isn't resolvable with existing project knowledge, that is exactly
the trigger point for a genuine, problem-driven research episode per `docs/RESEARCH_ROADMAP.md` —
not before.
