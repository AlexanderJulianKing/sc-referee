# Atomic scientific-check requirement profile

Use this profile only when the requirement is one option already published by the installed
sc-referee scientific-check registry. The scientist never types the JSON: the agent proposes the
family from the protocol, `draft-profile` checks that proposal and writes the JSON, and the
scientist confirms or corrects it.

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

## Validated outcome-family profile (`1.2.0`)

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
three distinct header column names in the order the caller proposes them, and never the group
column. `family_member_rule` and `correction_scope` are fixed strings.

## What the validation rule checks

`method-contract-draft/outcome-family/v2` validates a proposal; it does not derive one. Every check
fails closed:

- every proposed column exists in the header exactly, case-sensitive;
- the header has no blank name, no exact duplicate, no case-colliding pair, and no byte-order mark;
- every proposed name occurs verbatim as a whole token in the protocol text, and the provenance
  records the line numbers;
- the group column is not also an outcome;
- identifier-shaped names and any column the caller flags with `--exclude <name>=<reason>` are
  refused as outcomes;
- at least three outcomes;
- the protocol names no other `.csv` file anywhere in its text; and
- no proposed name shares a sentence with a qualifying word: "not", "excluded", "exclude",
  "except", or "secondary". This is a conservative tripwire, not sentence parsing. It refuses so a
  human reads the sentence.

Design-label columns such as `plot` or `replicate` are not special-cased. They are refused when the
protocol does not name them or when the caller flags them with `--exclude`, and accepted when the
protocol names them verbatim as outcomes and nobody excludes them. The scientist is the authority
there, not a heuristic.

The scientist may correct any proposed value; re-run `draft-profile` with the corrected values. The
freeze records whether the confirmed profile differs from the validated one, and refuses a sidecar
whose bound protocol bytes or CSV header have changed. If the scientist supplies an unsupported,
partial, or internally inconsistent object, preserve the unresolved contract and explain the exact
validation error.

## What the contract does and does not establish

The contract freezes the complete check manifest, selected candidate, comparison form, semantic
dimension, and content digests. A later audit binds it only when the governing task bytes and the
installed check remain unchanged and that exact check produces one applicable selected-analysis
question. If it does not apply, the audit remains Finding-clean and reports `not_applicable`.

This records review-scoped human intent. It does not prove execution, numerical causality,
historical intent, universal correctness, or detector qualification.
