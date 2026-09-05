# Multiple-testing 3.3 terminal-presentation prototype sweep

This directory is answer-visible development evidence for the 3.3 design. It is not imported by
production code. The strict shadow performs two proof-only transformations:

1. it suppresses one hierarchy control only after proving the exact terminal count, verdict-local,
   or presentation-`If` production and total forward use; and
2. it lowers one single-call-site helper-returned flat record into an equivalent list-record
   surrogate after proving complete contract iteration and every p/conclusion consumer.

Neither shadow classifies a family. The unchanged 3.2 analyzer classifies the admitted original or
surrogate. `instrument_results.json` records the real 3.2 guard trace: E16 P2 first stops at the
line-54 verdict `IfExp`, E16 P4 first stops at the line-96 presentation `If`, and skipping only that
one proved control lets each reach `candidate/none`. It also records the executed P3 ladder.

The sweep executes 155 evidence cases (105 opened E10-E16 plus 50 corpus cases) and 203 fixtures.
The fixtures comprise the frozen 170-row 3.2 population, 12 reproduced gatekeeping cases, 17 new
correct-analysis adversaries, and four positive controls. Exactly E16 P2/P3/P4 move; all 140 earlier
evidence rows remain classification-byte-identical, no opened negative or corpus-correct case becomes
a candidate, and no correct fixture becomes a candidate.

Run from the repository root:

```bash
PYTHONPATH=src:evaluation/development/multitest-code-slice-v3_3/prototype-sweep \
  .venv/bin/python evaluation/development/multitest-code-slice-v3_3/prototype-sweep/sweep.py
PYTHONPATH=src:evaluation/development/multitest-code-slice-v3_3/prototype-sweep \
  .venv/bin/python evaluation/development/multitest-code-slice-v3_3/prototype-sweep/verify.py
```

`results.json` and `instrument_results.json` are canonical JSON. `MANIFEST.json` binds every file in
this directory except itself and interpreter caches. There are no timestamps; identities, rows, and
digests derive only from checked-in input bytes and closed structural values.
