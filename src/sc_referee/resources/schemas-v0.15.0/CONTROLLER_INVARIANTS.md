# Controller invariants for v0.15.0

- Static controls use `not_executed` and exactly one bound static proof.
- Static proof facts are independently rederived from immutable full-digest bytes.
- Static proofs are qualification-controller inputs, never detector semantic inputs.
- Missing, ambiguous, unsupported, weak, over-budget, or conflicting closure is unavailable.
- Control families are never silently pooled.
- No record in this release grants detector promotion or global correctness.
