# Prospective qualification v3 planning artifacts

The directory name is retained as an immutable migration path; the active template and evidence
contract are version 3.0.0.

This directory fixes two design defects discovered in the complete v1 pilot without opening the
v1 held-out block:

1. reviewers select one frozen canonical issue-class identifier, while free-text descriptions are
   retained but excluded from label resolution; and
2. every authored case binds one selected reported result to one exact static producer and its
   source operands before scientific labels are frozen.

The generated ten-envelope template replaces the domain-specific map-exposure envelope with the
generic complete-domain denominator check. It still requires seven cells per envelope in separate
threshold-pilot and held-out blocks, for 140 new cases total.

`prospective_qualification_v2.py` and `prospective_selected_result_verifier.py` provide five
deterministic, evaluation-private artifact stages:

- `freeze_author_selected_result_declaration` freezes only the author's result-selection facts,
  without exposing the envelope, check, candidate, canonical issue class, or detector identity.
- `freeze_case_evidence_contract` lets the coordinator bind that already-frozen declaration to the
  scientific envelope. Neither artifact has verification or scientific authority.
- `freeze_independent_selected_result_derivation` enumerates one narrowly supported static Python
  report grammar directly from a closed case tree. It does not execute project code.
- `freeze_selected_result_validation` replays that derivation from case bytes and compares it with
  the previously frozen author declaration after the blind derivation is complete.
- `freeze_stage2_scientific_label` requires the full schema-valid Stage-2 AgentReview bytes, their
  exact pre-detector 4+2 panel freeze, and independent verifier validation replayed from
  `case_root`. It derives compact fields from those exact records and resolves labels from enums
  and digests, never from free-text similarity.

The first verifier profile accepts only a closed tree containing one or more strict straight-line
Python producers, one nonexecutable ASCII/LF `.md`/`.txt` selected report, and the nonexecutable
ASCII/LF `.csv`/`.tsv` operands actually rederived from those producers. Output bytes must match
exactly. Other code, newline-translated or non-ASCII text, dynamic flow, extra files, ambiguous
producers, and resource-bound violations fail closed.

These artifacts do not authenticate people or providers, create cases, inspect held-out material,
set thresholds, calculate metrics, qualify a detector, or grant Finding authority. Under
Experiment 0056, the selected-result comparator is frozen deterministic, auditor-owned
infrastructure; its implementation and build identity are fixed and its finite grammar and
adversarial controls are tested, but it does not undergo a separate meta-qualification study.

V3 execution reuses the v1 prospective allocation freezer to enroll declared roles and freeze the
detector lock, two study blocks, authoring-brief digests, and all opaque case assignments before
labels are opened. The v2 case-evidence and selected-result artifacts are created only after the
corresponding authored case exists.

Regenerate the template with:

```bash
python scripts/build_prospective_qualification_v2_template.py
```
