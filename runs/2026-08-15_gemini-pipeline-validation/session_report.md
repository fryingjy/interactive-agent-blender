# Gemini video-understanding pipeline validation

## Declared test

- Source: Blender Guru, *Blender Beginner Tutorial - Part 1: Modeling an Anvil*
- Requested URL: `https://www.youtube.com/watch?v=yi87Dap_WOc`
- Model: `gemini-3.6-flash`
- Prompt: `blender-video-study-v1`
- Video downloaded or archived: no
- Goal: prove that the repository's documented Gemini method can be replayed as code and returns
  synchronized video/audio modeling episodes rather than a title or transcript summary.

## Result

The live API call completed and produced seven structured episodes in
`gemini_structured_analysis.json`. The output explicitly reports that video and audio were inspected
and keeps OBSERVED FACT, INSTRUCTOR CLAIM, INTERPRETATION, and HYPOTHESIS separate.

Two representative moments had already been independently inspected in the in-app browser against
the live YouTube page:

- Around 04:07, the visible Blender viewport showed the reference workspace and a plane used as the
  unambiguous rectangular base; the live caption discussed starting from a plane. This supports the
  structured primary-anchor episode (03:14-05:05) and the older study's tighter 04:06-04:35 range.
- At 12:44, the live caption said the form would be squashed because of the visible example, matching
  the structured global-proportion episode (12:37-13:40) and the older study's 12:40-13:18 range.

The structured extraction also converges with the prior 2026-08-14 study on the intentionally failed
manual step-extrusion, uniform loop cuts before deformation, constrained proportional scaling, and
late silhouette correction.

## Important failure found

Gemini reported `https://www.youtube.com/watch?v=132A89i34dQ` in its generated source metadata even
though the request supplied `yi87Dap_WOc` and the extracted content correctly described the Blender
Guru anvil lesson. The pipeline now treats source identity as request-owned provenance, preserves the
model-reported value for audit, and records whether it matches. Generated source metadata is not
silently trusted.

The first prompt also allowed some episode ranges to become broader than ideal and included at least
one plausible alternative not clearly shown. The committed prompt therefore asks for one decision per
tight interval and forbids unshown alternatives outside the HYPOTHESIS field.

## Verdict

The acquisition path is operational and reproducible, but this extraction remains
`MODEL_EXTRACTED_UNVERIFIED`; two spot checks do not validate every field or promote any principle.
The correct next gate is more timestamp verification, then controlled reproduction and transfer on
different geometry.
