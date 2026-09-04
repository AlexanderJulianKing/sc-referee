# Atomic scientific-check requirement profile

Use this profile only when the requirement is one option already published by the installed
sc-referee scientific-check registry. The scientist never types the JSON: `draft-profile` proposes
it from the protocol and the CSV header, and the scientist confirms or edits it.

## Legacy option-only profile (`1.0.0`)

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

## Drafted outcome-family profile (`1.2.0`)

`sc-referee draft-profile` writes exactly this shape for the authorized-outcome-family requirement:

```json
{
  "profile_id": "scientific_check_requirement_v1",
  "profile_version": "1.2.0",
  "check_id": "check:authorized-complete-family-correction-over-code-test-battery",
  "candidate_id": "complete-correction-over-authorized-outcome-family",
  "semantic_role_authority": {
    "authorized_test_family": {
      "material_input_path": "data.csv",
      "group_contrast_column": "arm",
      "outcome_columns": ["alpha_mg", "beta_pct", "gamma_score"],
      "family_member_rule": "one-two-group-test-per-named-outcome-column",
      "correction_scope": "complete-authorized-family"
    }
  }
}
```

The field set is closed at both levels; no extra key is accepted, so draft provenance is written to
a separate `.provenance.json` sidecar rather than into the profile. `outcome_columns` holds at least
three distinct header column names in the order the protocol names them, and never the group column.
`family_member_rule` and `correction_scope` are fixed strings.

The draft rule is closed. Outcome columns are the columns the protocol names as outcomes, matched to
the header. The group column is the column the protocol names as the two-group contrast, matched to
the header. Identifier, design-label, and group columns are never outcomes. If the protocol names no
outcome family or no group column, the draft refuses; take the unresolved-contract MaterialQuestion
path rather than supplying the values yourself.

The scientist may edit any drafted value before the freeze. The freeze records whether the draft was
edited. If the scientist supplies an unsupported, partial, or internally inconsistent object,
preserve the unresolved contract and explain the exact validation error.

## What the contract does and does not establish

The contract freezes the complete check manifest, selected candidate, comparison form, semantic
dimension, and content digests. A later audit binds it only when the governing task bytes and the
installed check remain unchanged and that exact check produces one applicable selected-analysis
question. If it does not apply, the audit remains Finding-clean and reports `not_applicable`.

This records review-scoped human intent. It does not prove execution, numerical causality,
historical intent, universal correctness, or detector qualification.
