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

`prospective_qualification_v2.py` provides two deterministic, evaluation-private artifact stages:

- `freeze_case_evidence_contract` freezes the author's exact selected-result declaration. The
  declaration has no verification or scientific authority.
- `freeze_stage2_scientific_label` requires two distinct Stage-2 providers plus an independent
  evidence-completeness validation. It resolves labels from enums and exact digests, never from
  free-text similarity.

These artifacts do not validate declaration truth, authenticate people or providers, create
cases, inspect held-out material, set thresholds, calculate metrics, qualify a detector, or grant
Finding authority. An independently implemented verifier must still rederive every selected-result
binding from immutable case bytes.

Regenerate the template with:

```bash
python scripts/build_prospective_qualification_v2_template.py
```
