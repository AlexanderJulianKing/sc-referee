# Three-claim single-cell pipeline

**Status:** runnable synthetic report-routing demo.

One experiment produces three scientific result families:

1. gene-expression differential expression;
2. alternative splicing; and
3. cluster abundance.

The purpose is not biological novelty. It demonstrates that Referee binds, audits, and renders each
reported artifact separately instead of allowing evidence from one pipeline step to contaminate
another.

```bash
.venv/bin/python demos/multi-claim-pipeline/build_demo.py
.venv/bin/referee demos/multi-claim-pipeline
```

`build_demo.py` deterministically regenerates the small count matrix. The text result tables, code,
and confirmed three-claim manifest are committed for inspection.

