# Experiment 0041: Bounded Python and R static method adapters

- **Status:** Completed development experiment; qualification use forbidden
- **Date:** 2026-08-01
- **Decision:** Accepted ADR-0050
- **Backlog item:** L07
- **Public schema:** Unchanged at `0.18.0`
- **Finding authority:** None; every changed module remains question-only
- **Project execution:** None

## Question

Can existing scientific questions recognize the same normalized method choice in explicitly scoped
Python and R source, without adding controller special cases, executing target code, or allowing a
model to decide which call governs the analysis?

## Frozen development evidence

The source corpus in `evaluation/static-source-adapter-v1/` retains two exact benchmark-derived,
fresh-agent structural-copy workflows:

| Case | Exact source digest | Expected existing operand |
|---|---|---|
| ancestry-stratified multinomial classifier | `sha256:b0a4c2d33899d492b7c3b3bd6e46314ac0b245de9bbdc611c279901e295621b4` | `continuous_posterior_expected_copy_dosage` |
| group-specific ridge calibration | `sha256:1cdc64d849d1861f506ba42298ad77b7442133bbcfa77a72439fd1ceb45c8d32` | `direct_continuous_calibrated_copy_dosage` |

The frozen files are inert source payloads. Their manifest forbids qualification use and forbids
adapter rules from keying on case, experiment, repository, or origin identity.

The existing MVMR development family supplied the separate observed source gap for LD-covariance
whitening. Because those retained scripts contain both estimator implementations behind a runtime
configuration branch, they correctly remain unsupported as source-only primary-method evidence.
The admitted LD rules therefore cover only a smaller closed direct/library-call form whose robust
fit, redescending norm, Cholesky factor, and two triangular solves are all explicit.

## Implementation

`static_source_adapter.py` adds one shared boundary and four registry adapters:

1. Python classifier-derived copy dosage;
2. R classifier-derived copy dosage;
3. Python LD whitening before a redescending robust fit; and
4. R LD whitening before a redescending robust fit.

Python exact imports and finite aliases, R literal namespaces and one closed namespace-alias form,
literal class-state vectors, prediction method arguments, matrix formulas, assignments, and short
local function summaries normalize to the existing report operands. The source must reach the
selected publication surface through the accepted analysis-source selection, selected active cell,
or unique static writer path. An exact unscoped operand is retained only as an unsupported
suppressor.

Shadowing, wildcard imports, computed dispatch, method-defining branches, competing operands,
incomplete parser receipts, and R parser disagreement abstain. Source/report disagreement is left to
the existing registry reducer and becomes `ambiguous`; no confidence score can arbitrate it.

## Independent false-positive probe

The exact L07 adapters were applied statically to the 14 Python files in commit-pinned
`broadinstitute/tensorqtl` revision `0c4db65a0cdc47f3b824ae530b89d270ef5e0096`, previously frozen by
Experiment 0021. The scan produced zero copy-dosage operands and zero LD-whitening operands. Ten
files reached a conservative binding boundary and would therefore remain unsupported, not create a
question. The per-file projection digest is
`sha256:91adc4d9f8680c2b405b4eb05f598dbf898a2b7f43e3012fdbf18cc6c4b9e2e9`.

This public-repository probe is retained as an external development result rather than placed in
the executable offline ledger, because L02 deliberately refuses external sources without a
separately pinned materialization step.

## Result

The two exact frozen structural sources normalize to their correct existing operands without file,
repository, benchmark, or numeric-answer keys. Equivalent Python and R formulas normalize to the
same copy-dosage operand. Equivalent Python direct/aliased and R direct/namespaced robust-fit forms
normalize to the same LD-whitening operand.

A full non-executing audit over a uniquely connected source creates the existing bounded copy-dosage
scientist question, produces zero Findings, executions, execution authorizations, and model calls,
and replays the exact question. Removing the source adapters removes only the static-source evidence
plane. No controller, storage, report, admission, detector, or public-schema code changed.

The regression ledger now covers 26 components through 11 retained sources and 113 cases; all cases
remain qualification-excluded.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** 25 focused cases covering exact frozen sources; Python direct and aliased imports;
  R direct, namespaced, and closed namespace-alias calls; class-state formulas; robust-fit formulas
  and method arguments; shadowing; dynamic dispatch; branch dependence; competing calls; R parser
  disagreement; scoped and unscoped sources; report/source agreement and disagreement;
  cross-language equivalence; adapter removal; corpus and parser mutation; full audit authority
  ceilings; no execution/model calls; and replay.
- **Acceptance criterion satisfied:** both languages emit the same existing normalized operands,
  use the shared L05 scope graph, preserve disagreement explicitly, and require no controller,
  storage, reporting, admission, or schema change.
- **Remaining coverage limitation:** static source does not establish runtime values, package
  behavior, execution, dead-code absence, or primary-analysis status. The closed rules cover two
  existing questions, not arbitrary source semantics, wrappers, generated formulas, or all current
  checks. Notebook/Quarto/R Markdown cross-cell connectivity remains L08.
