# ADR-0059: Use cold workflows to develop generic question-only recognition

- **Status:** Accepted under the repository owner's explicit request to turn the existing
  evidence infrastructure into useful scientific recognition
- **Date:** 2026-08-03
- **Related decisions:** ADR-0020, ADR-0056, ADR-0057
- **Schema impact:** None; retain public schema `0.18.0`
- **Finding impact:** None; all affected scientific checks remain question-only and
  Finding-ineligible
- **Execution impact:** None; the production auditor continues not to execute project-authored
  code

## Context

The scientific-check registry has a sound extension seam, immutable evidence, deterministic
replay, and conservative admission, but most installed checks recognize only enumerated report
wording. Fresh, independently authored GeneBench-Pro workflows demonstrated the practical
consequence: a wrong method can be visible in ordinary source or prose while the audit returns no
material scientific question.

Benchmark filenames, expected answers, and post-hoc model judgment cannot be moved into production
recognizers. Conversely, synthetic exact-phrase fixtures alone are inadequate evidence that a
check works on naturally written workflows.

## Decision

1. Use answer-isolated cold workflow authoring as a development loop. Authors receive only the
   public task and declared inputs. Their workspace is frozen and audited before answer-side
   grading or reference-method inspection.
2. A cold miss may motivate a production change only when the resulting rule is an abstract method
   relation, contains no benchmark identity or answer value, and has renamed-layout, corrected,
   hard-negative, ambiguous, and unsupported controls.
3. Extend the founder-orientation Python adapter with bounded local interprocedural data flow. It
   may follow unique assignments, lexical closures, and explicit local call parameters from a
   founder-semantic input to a two-role emission comparison. All callers must resolve to one origin
   and one orientation state. Dynamic dispatch, competing origins, mixed direct/repaired flows,
   nonlocal targets, and nonsemantic inputs abstain.
4. Admit two explicit orientation transformations before emission: binary complement and a
   single-argument call whose identifier contains an orientation, flip, invert, complement, or
   recode token. This observation records only a static transformation step; it does not establish
   execution or the scientific correctness of that transformation.
5. Add a bounded Python observation-error algebra adapter. It recognizes symmetric two-state error
   algebra, its equivalent affine form, and distinct forward/reverse two-state rates. Error-rate
   semantics must be explicit in identifiers or literal field names. Branch-dependent, competing,
   unrelated-mixture, duplicate-binding, dynamic, or non-Python forms abstain.
6. Broaden existing report adapters only with bounded method paraphrases that preserve the same
   normalized operands. Initial additions cover calibration-before/after-standardization order,
   replicate-specific same-diagonal arithmetic expected counts, focal-target omission from its
   expected background, a directional-error decomposition stated around decimal-valued error
   summaries, the conjunction of an explicit negative-control technical signal, unit-level
   aggregation, and a primary model whose enumerated adjustment terms omit that signal, classifier
   posterior expectations used as continuous dosage, sequential outcome imputation that conditions
   on a post-treatment endpoint, raw molecule-fraction/local-copy target gates, local-perturbation
   row scope and adjustment-set declarations, called-path rather than full-map pulse exposure, and
   exact hidden-path integration across unobserved intervals.
7. Static evidence must retain an accepted source-to-analysis scope path before it creates a public
   question. Exact unscoped operands remain suppressors. Static evidence does not establish
   execution, primary-analysis status, historical intent, numerical causality, or scientific
   correctness.
8. Record GeneBench development coverage separately from production capability. Ledger states are:
   `absent` when no relevant installed check exists; `unsupported` when the family exists but a
   bounded adapter cannot close; `applicable` when an operand is recognized but the governing
   requirement is unresolved; and `checked` only after an external human or evaluation contract is
   compared with the observed operand. `checked` must separately report compatible, incompatible,
   or unresolved outcome.
9. A public-development answer mismatch is not a Finding and does not establish its scientific
   cause. A method question is not an accusation. Only an independently authorized requirement and
   the existing deterministic comparison can produce a review-scoped compatibility result; no
   production Finding authority is added here.
10. GeneBench identifiers, paths, revisions, grading contracts, and coverage mappings remain in
    evaluation records and documentation. Production adapters and manifests must be free of them.

## Consequences

The product begins measuring natural workflow recognition rather than only fixture conformance.
False accusations remain bounded because unsupported data flow, unclear semantics, and missing
scope still abstain. The first milestone is useful question localization, not production Finding
promotion. The existing disclosure-count problem and the generic dependence/pseudoreplication
vertical remain separate follow-on work.

## Acceptance evidence

- a frozen wrong workflow missed by the prior release becomes one localized high-priority method
  question without answer-side access;
- a structurally different direct-flow fixture and renamed-layout fixture normalize to the same
  operand;
- explicit complement and semantic orientation-call controls normalize to the repaired operand;
- mixed direct/repaired callers, non-founder mixtures, branches, duplicate bindings, and competing
  operands abstain;
- symmetric and directional error algebra normalize independently and an unrelated mixture is not
  applicable;
- report paraphrases work across renamed strata and generic diagonal/focal terminology;
- a renamed negative-control/aggregation/model layout reaches the technical-group question while
  an explicitly adjusted model remains unsupported rather than being labeled omitted;
- classifier-derived posterior dosage and direct continuous calibration remain separate operands;
- post-treatment endpoint integration and assessment weighting without that endpoint remain
  separate missingness/transport operands;
- a raw molecular-fraction/local-copy target gate remains distinct from a purity/copy-adjusted
  clonality gate;
- nominal focal-row restriction, full-assay cross-modal screening, single-axis residualization,
  and joint nuisance-adjusted local modeling are localized without target names or answer values;
- called-path pulse exposure and full-map exposure remain independent from the ancestry-fraction
  denominator, while exact hidden-gap integration remains an independent path-continuity choice;
- every result remains zero-Finding, non-executing, and replayable; and
- the content-addressed scientific-check release manifest binds every changed implementation and
  grammar.

## Deferred work

- Collapse unrelated not-applicable coverage from the headline report.
- Add explicit analysis-source selection for otherwise unscoped source-only workflows.
- Build data-and-model adapters for recoverable technical strata and other cases that cannot be
  supported from report prose alone.
- Add a bounded data/model adapter for group-specific binary-label orientation diagnostics; the
  cold population-genetics workflow's chromosome-local label inversion is not yet localized.
- Complete independent non-benchmark validation and the ordinary qualification process before any
  promotion proposal.
