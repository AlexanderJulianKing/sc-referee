# Experiment 0029: Freeze a multiple-testing control family before detector work

- **Status:** Control family and accepted ADR-0044 calculation-check mechanism implemented;
  production detector not authorized
- **Date:** 2026-07-31
- **Scientific scope:** Benjamini-Hochberg conformance under an explicit complete-family FDR contract
- **Project execution:** Disabled
- **Finding authority:** None

## Question

Can the first recovered single-cell capability begin from a small evaluator-owned family that
distinguishes a true complete-family BH mismatch from a corrected twin, a superficially suspicious
but inapplicable primary-hypothesis case, and a genuinely unresolved incomplete-family case?

## Decision

Freeze four answer-isolated workspaces before production detector implementation:

1. a positive with an explicit complete-family BH/FDR contract whose adjusted column equals its raw
   p-values and whose four reported discoveries include two that fail the independent BH oracle;
2. a corrected twin with identical raw p-values and exact oracle-derived adjustments and calls;
3. a hard negative containing one preregistered primary hypothesis for which no discovery-family
   multiplicity procedure governs; and
4. an ambiguous selected-hits table that lacks both the complete testing family and a governing
   multiplicity procedure.

Labels, reasons, and the oracle stay outside each `workspace/`. The exact-decimal oracle is located
in the evaluator-owned builder and imports no production detector, scientific adapter, or
multiple-testing implementation. The old public repository supplies historical motivation only;
it is explicitly not authority for the control labels or the future implementation.

## Why synthetic controls are appropriate here

The desired distinction is a closed arithmetic and scope relation, so a small constructed family
provides stronger causal isolation than a naturally occurring repository with many simultaneous
method choices. Synthetic status does not make the cases qualification evidence: they establish
mechanism behavior only. Fresh agent-authored variants and real external workflows remain required
before any recognition-rate or production Finding claim.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** known-value and invalid-input oracle tests; four-role completeness; positive/
  corrected raw-family identity; exact call-count difference; hard-negative and ambiguity boundary
  assertions; byte-reproducible no-replace construction; complete content-manifest validation;
  ordinary audit/report/storage/semantic-lock/replay; malformed and over-budget fail-closed cases;
  workspace drift; and registry removal isolation.
- **Acceptance criterion satisfied:** the scientific contract and four distinct expected outcomes
  were frozen before adapter code; no answer-side label is present inside an audit workspace; and
  the generic adapter produces the expected typed observation, question, or abstention with zero
  Findings.
- **Remaining limitation:** this one ten-hypothesis family does not test natural wording, table
  binding, arbitrary column names, unordered or tied p-values, missing values, alternative FDR
  procedures, hierarchical/weighted/adaptive testing, or large result tables. It grants no
  production capability or Finding authority.
