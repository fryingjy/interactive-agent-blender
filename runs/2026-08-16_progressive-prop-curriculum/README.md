# Progressive prop curriculum ingestion

The user-supplied 30-prop ladder is represented as an executable curriculum rather than as a claim
of completed modeling evidence. `curriculum_validation.json` checks sequential prop/tier IDs,
mandatory A-G gates, the human-review override, the document authority boundary, evidence breadth,
and the current Swingline lock.

Current state remains `EXTERNAL_REVIEW_REQUIRED`: the Swingline reference board is machine-ready,
but no geometry is authorized until a human records `APPROVE_REVERSIBLE_BLOCKOUT`.
