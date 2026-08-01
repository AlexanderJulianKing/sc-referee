# ADR-0040: Freeze an experimental bounded analysis-method conflict candidate

- **Status:** Accepted under the repository owner's standing authorization for non-authority-
  changing development ADRs
- **Date:** 2026-07-31
- **Related decisions:** Accepted ADR-0018, ADR-0019, ADR-0020, and ADR-0039
- **Schema impact:** None; accepted schema v0.15.0 remains unchanged
- **Finding impact:** None; the detector is experimental and cannot emit a production Finding

## Context

ADR-0039 closes one real source-to-selected-report scope path. On the frozen multiparent-QTL
workflow, sc-referee can now establish all of the following without executing project code:

1. the selected report explicitly says that supplied founder alleles were used directly;
2. one exact static source shape says the same thing;
3. that source contains the unique statically reachable writer for the exact selected report;
4. the repository owner supplied a scope-bound review requirement to repair founder orientation
   before HMM emission; and
5. the closed method ledger compares those exact operands and reports a conflict for this review.

The current production output remains a non-accusatory Disclosure. Before any possible Finding
promotion, the project needs a frozen detector implementation and an answer-blind qualification
portfolio. Freezing the detector now makes that later test meaningful: the candidate cannot be
changed after seeing qualification labels merely to improve its score.

## Decision

### 1. Add one reusable engine with one release-allowlisted check

Add experimental detector `detector:bounded-analysis-method-conflict` version `0.1.0`. Its engine
consumes the common analysis-scoped question, human Answer, post-hoc ledger, SemanticAssertions,
and exact scope graph. Release version `0.1.0` allowlists only
`check:founder-orientation-before-hmm-emission` because that is the only complete real
report/source path currently evidenced.

The architecture is modular: another scientific check may use the engine only after defining its
own closed operand grammar, answer candidates, comparison form, scope join, counterevidence, and
tests. Similar wording or a method name alone does not qualify a new check.

### 2. Require three independent evidence roles

An exact conflict candidate requires:

- one human Answer that establishes only the requirement governing this review;
- one exact selected-report operand and one exact static-source operand that agree; and
- one full-digest `FileRecord -> writer Operation -> selected Artifact ->
  PublicationSurface` path.

No one role substitutes for another. The Answer cannot prove what the repository says; static
source cannot prove what ran; report prose cannot prove source authorship; and the selected-output
writer declaration cannot prove execution.

### 3. Complete ten finite checks before producing a candidate

The detector must complete, in order:

1. analysis-requirement authority;
2. selected-report operand uniqueness;
3. static-source operand uniqueness;
4. agreement between report and source operands;
5. selected-output scope closure;
6. alternate or superseding intent;
7. governing protocol amendment;
8. approved method deviation;
9. conditional applicability; and
10. sensitivity-only or unsupported-method qualification.

Missing evidence, ambiguity, disagreement, or counterevidence produces `insufficient_semantics`
or `unsupported_path`, never a candidate. A matching requirement produces one covered negative,
which is not a correctness certificate.

### 4. Keep the candidate evaluation-only

The exact mismatch may produce an internal `evaluation_finding_candidate` so that the frozen
detector can be scored. Its manifest remains `experimental`, its strongest public output is
`disclosure`, and `x-production-finding-permitted` is false. The controller emits zero production
Findings from this detector.

Candidate wording is limited to the demonstrated declaration mismatch: the selected report and
exactly scoped static source declare one operand, while the scientist's requirement for this
review names another. It must explicitly avoid claiming that the source ran, that the mismatch
caused a numerical error, or that the scientist's requirement is universally correct.

### 5. Freeze before answer-blind qualification

The implementation digest, manifest, ten-check protocol, test fixtures, and capability entry are
part of the frozen candidate. Qualification remains empty. Promotion would require the separately
accepted answer-blind cross-provider portfolio and maintainer decision; any later logic change
invalidates the candidate's qualification identity and starts a new candidate version.

## Alternatives rejected

### Emit a Finding now because the real QTL case conflicts

Rejected because one successful real case is development evidence, not independent qualification.

### Compare the scientist Answer with source or report evidence alone

Rejected because either plane alone leaves a material provenance and scope alternative open.

### Generalize immediately to every scientific-check question

Rejected because the common records are reusable but each scientific operand and its
counterevidence boundary still require separate evidence and qualification.

### Require execution before testing the detector

Rejected because this detector's claim is a declaration mismatch, not an executed-result or
numeric-cause claim. Execution would not resolve all of those stronger meanings and is outside the
MPP.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** an exact conflict; a matching verified-good negative; a non-allowlisted hard
  negative; missing full-digest scope identity; one mutation for each of the ten finite checks;
  schema validation; deterministic repeated evaluation; full Answer/lock/controller integration;
  byte-identical replay of detector results; authoritative/plugin skill-copy validation; and skill
  package structural validation.
- **Acceptance criterion satisfied:** the exact real connectivity path now reaches a frozen,
  deterministic, evaluation-only detector boundary, while every tested ambiguity or
  counterevidence mutation suppresses the candidate and production Findings remain empty.
- **Remaining limitation:** the answer-blind independent positive, ambiguous, hard-negative,
  removal, cross-provider, and maintainer-promotion portfolio has not yet been completed. Only one
  scientific check is allowlisted, and no fresh-context user has yet exercised this exact new
  candidate through the installed skill. Execution, numerical causality, historical intent,
  universal method adequacy, and domain-wide correctness remain unsupported.
