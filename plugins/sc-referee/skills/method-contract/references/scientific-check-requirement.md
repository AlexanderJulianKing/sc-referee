# Atomic scientific-check requirement profile

Use this profile only when the scientist explicitly selects one option already published by the
installed sc-referee scientific-check registry:

```json
{
  "profile_id": "scientific_check_requirement_v1",
  "profile_version": "1.0.0",
  "check_id": "check:founder-orientation-before-hmm-emission",
  "candidate_id": "repair-before-emission"
}
```

All four keys are required and no other keys are accepted. Obtain the available `check_id` and
`candidate_id` values from the installed registry or the exact MaterialQuestion produced by an
audit. Never invent, translate, rank, or silently select an option for the scientist.

The contract freezes the complete check manifest, selected candidate, comparison form, semantic
dimension, and content digests. A later audit binds it only when the governing task bytes and the
installed check remain unchanged and that exact check produces one applicable selected-analysis
question. If it does not apply, the audit remains Finding-clean and reports `not_applicable`.

This records review-scoped human intent. It does not prove execution, numerical causality,
historical intent, universal correctness, or detector qualification.
