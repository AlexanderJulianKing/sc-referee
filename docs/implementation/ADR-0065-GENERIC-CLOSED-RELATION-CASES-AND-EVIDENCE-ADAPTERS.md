# ADR-0065: Add generic closed-relation cases and removable evidence adapters

- **Status:** Accepted under the repository owner's explicit generic-referee implementation
  request
- **Date:** 2026-08-04
- **Related decisions:** ADR-0012, ADR-0013, ADR-0015, ADR-0042, ADR-0059, ADR-0060,
  ADR-0061
- **Schema impact:** None; relation cases are internal frozen Python values and public output keeps
  the accepted `DetectorResult` shape
- **Finding impact:** None; new relations remain development-only until separately qualified and
  promoted per exact binding
- **Execution impact:** None; project-authored code remains unexecuted

## Context

The existing method-conflict path already freezes human scientific requirements, compiles exact
report or static-source evidence into canonical operands, applies finite counterevidence checks,
and emits ordinary development-only DetectorResults. Its evaluator is binding-driven, but its
workflow recognition remains a collection of narrow evidence adapters. A prospective pilot
confirmed that the evaluator cannot help when a renamed workflow never reaches a normalized
observation.

That recognition failure must not be addressed by benchmark identifiers, answer-side values,
open-ended model judgment, a universal workflow ontology, or trusting project-authored semantic
claims. A generic system still requires finite evidence grammars and must abstain on opaque
workflows.

## Decision

1. Add one small internal `RelationCase` representation between verified method evidence and the
   existing `ReviewCase`. It binds one authorized requirement, one or more independently verified
   observations, one registered method-conflict binding, the exact analysis-scope path, and the
   existing finite applicability and counterevidence gates.
2. The relation evaluator dispatches only on registered closed comparison forms. The initial
   forms are `value_equals`, `set_relation`, and `step_precedes`; their operands remain canonical
   scalars, sets, or ordered steps. It does not interpret candidate labels or scientific nouns.
3. Language, file-layout, and subject-area recognition remain in removable, content-addressed
   evidence adapters. An adapter may normalize only explicit, independently checkable bytes and
   parser products. Missing, conflicting, dynamic, or unsupported evidence yields abstention.
4. No new public relation-result record is introduced. A complete relation comparison maps to the
   existing DetectorResult states and carries optional relation-case and ReviewCase digests.
5. A mismatch may reach only an `evaluation_finding_candidate` until the exact detector, check,
   adapter, grammar, and binding envelope has independent qualification and maintainer promotion.
   Existing v0.3 identities and qualification artifacts remain immutable.
6. The first new adapter family is the domain-neutral denominator-domain relation: a selected rate
   or spacing estimate uses either the complete scientist-declared exposure domain or only a
   retained observed subset. Its grammar may recognize explicit selected-report statements across
   different subject areas, but cannot infer the governing domain or missing-data treatment.
7. A project-supplied workflow declaration may be considered later only as untrusted candidate
   location information. It cannot establish scope, execution, scientific intent, compatibility,
   or a Finding. Any accepted declaration relation must be independently rederived by an
   auditor-owned verifier before it contributes evidence.
8. Adapter development must include renamed subject-area variants, corrected controls, valid
   alternatives, close hard negatives, ambiguous cases, unsupported cases, and mutation tests.
   Public or label-visible pilot cases are development-only and cannot qualify the changed
   detector.
9. Any changed detector or adapter identity requires a new prospective assignment and threshold
   chronology. The sealed v1 held-out block remains unopened and cannot be retrofitted.

## Consequences

The core remains modular and small: adapters answer “what exact operand is explicitly evidenced,”
the relation evaluator answers “does that operand satisfy the authorized closed relation,” and
qualification alone answers “may this binding emit a production Finding.” Subject-area renaming
does not require new comparison logic, while unsupported prose or source remains visibly
unsupported.

The first denominator adapter can demonstrate development coverage on independently renamed
workflows without claiming arbitrary-workflow understanding. Reaching ten production Findings
still requires complete prospective cases for all ten relation families, canonical label
vocabulary, exact selected-result provenance, independent review, pilot-frozen thresholds, held-out
metrics, and ten separate promotion decisions.
