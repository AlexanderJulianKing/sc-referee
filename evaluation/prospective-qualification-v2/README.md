# Prospective qualification v2 planning artifacts

This directory fixes two design defects discovered in the complete v1 pilot without opening the
v1 held-out block:

1. reviewers select one frozen canonical issue-class identifier, while free-text descriptions are
   retained but excluded from label resolution; and
2. every authored case binds one selected reported result to one exact static producer and its
   source operands before scientific labels are frozen.

The generated ten-envelope template replaces the domain-specific map-exposure envelope with the
generic complete-domain denominator check. It still requires seven cells per envelope in separate
threshold-pilot and held-out blocks, for 140 new cases total.

`prospective_qualification_v2.py` and `prospective_selected_result_verifier.py` provide four
deterministic, evaluation-private artifact stages:

- `freeze_case_evidence_contract` freezes the author's exact selected-result declaration. The
  declaration has no verification or scientific authority.
- `freeze_independent_selected_result_derivation` enumerates one narrowly supported static Python
  report grammar directly from a closed case tree. It does not execute project code.
- `freeze_selected_result_validation` replays that derivation from case bytes and compares it with
  the previously frozen author declaration after the blind derivation is complete.
- `freeze_stage2_scientific_label` requires two distinct Stage-2 providers plus an independent
  verifier validation replayed from `case_root`. It resolves labels from enums and exact digests,
  never from free-text similarity.

The first verifier profile accepts only a closed tree containing one or more strict straight-line
Python producers, one nonexecutable ASCII/LF `.md`/`.txt` selected report, and the nonexecutable
ASCII/LF `.csv`/`.tsv` operands actually rederived from those producers. Output bytes must match
exactly. Other code, newline-translated or non-ASCII text, dynamic flow, extra files, ambiguous
producers, and resource-bound violations fail closed.

These artifacts do not authenticate people or providers, create cases, inspect held-out material,
set thresholds, calculate metrics, qualify this verifier or a detector, or grant Finding authority.
The verifier implementation must still be independently qualified and frozen before any v2 case
assignment may rely on it.

Regenerate the template with:

```bash
python scripts/build_prospective_qualification_v2_template.py
```
