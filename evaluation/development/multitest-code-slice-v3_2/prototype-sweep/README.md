# Multiple-testing 3.2 AP(C, POS) prototype sweep

This directory is answer-visible development evidence for the 3.2 correction-recognition design.
It is not imported by production code.  The sweep runs the frozen 3.1/3.0 source analyzer, applies
the strict `AP(C, POS)` shadow recognizer in `ap_shadow.py`, and records every one of the 90 opened
envelope cases, all 50 open-corpus cases, the frozen 71-fixture record-model matrix, and the new
correction-recognition adversaries and controls. The exact fixture census is 170: the frozen 71,
the cumulative 63-row B5 field/expression grid, all 16 independent 3.1 laundering-adjacent
controls, and 20 AP-specific fixtures. The last two AP fixtures assert the exact
`cross-function-record-flow` and `_record_merge_reason` gate identities, not merely their refusal
outcomes.

The shadow admission is intentionally no looser than the design grammar.  It accepts only an exact
family-size Bonferroni product (optionally capped by exact `min`/`numpy.minimum`) or an exact
family-alpha divided by the proved family size.  A surrogate rewrite removes only the recognized
correction node and then reruns the frozen analyzer; a movement is admitted only when that analyzer
proves the unchanged downstream family as `candidate/none`.  Factor claims, field names, comments,
format strings, reports, and case identities never supply evidence.

Run from the repository root:

```bash
PYTHONPATH=src .venv/bin/python \
  evaluation/development/multitest-code-slice-v3_2/prototype-sweep/sweep.py
PYTHONPATH=src .venv/bin/python \
  evaluation/development/multitest-code-slice-v3_2/prototype-sweep/verify.py
```

`results.json` is canonical JSON. `MANIFEST.json` binds every authored or generated file in this
directory except itself. Timestamps are absent; all identities and digests derive only from input
bytes and closed structural values.
