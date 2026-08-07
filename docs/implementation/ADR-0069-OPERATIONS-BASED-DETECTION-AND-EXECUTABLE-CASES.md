# ADR-0069: Operations-based detection and executable qualification cases

- **Status:** Accepted by the maintainer on 2026-08-07, in session, after two consecutive blind
  pilot failures of the prose-recognition approach
- **Date:** 2026-08-07
- **Scope:** The v2.0 recognizer for `check:complete-domain-exposure-denominator`, all future
  scientific-check recognizers, and all qualification cases authored from this date forward.
  Already-frozen artifacts and the six burned pilot cases are unaffected.
- **Relates to:** Experiment 0056; ADR-0067; ADR-0068; the accepted no-production-execution rule

## Context

Two blind pilots produced the same result pattern: zero false accusations, zero sensitivity.
Detector v1.1.0 missed because the blind author's nouns were outside its unit-word list.
Detector v1.2.0, repaired with a wider vocabulary, missed the next blind case because the author
sampled new nouns ("nest boxes", "planned set") and expressed the planted conflict only in
arithmetic (24 events over 32 retained units equals the stated 75.0 percent, while the declared
target is the complete set of 40), with no denominator sentence for a lexical rule to match.
Scratch counterfactuals confirmed both gaps independently. Closed word lists over report prose
do not generalize: every blind author, like every real scientist, invents nomenclature freely.

Separately, the render-only authoring grammar (adopted to make intake verification trivial
without execution) means authored cases contain no computation at all, so the benchmark itself
could never exercise an operations-based recognizer. The two designs propped each other up.

The maintainer's architectural direction: workflows abstract into recognizable mechanical
operation patterns; detection must key on those patterns, not on nomenclature.

## Decision

1. **Detection keys on operations and quantities, never nomenclature.** Recognizers may key on
   library API semantics (a filter, a merge, a division, a multiple-comparisons procedure),
   static dataflow structure, and arithmetic relations among extracted quantities. Variable
   names, column names, and report nouns never gate detection. Fixed word lists over free prose
   are retired as a recognition mechanism for new detector versions.
2. **Deterministic-first binding, agent last mile.** The deterministic layer binds quantities to
   scientific roles from structure: which input column feeds which operation, which computed
   value appears as the reported number. A calibrated agent binds only the residue the
   deterministic layer cannot resolve, and every agent binding is recorded as reviewable
   evidence, never applied silently.
3. **Authored qualification cases are real runnable workflows.** Blind authors produce small,
   genuinely executable analysis code (for example, a short pandas or standard-library script
   over a small input file) whose report follows from actually running it. The render-only
   string-gluing grammar is retired for new cases.
4. **Ground truth by bounded execution of our own authored code.** During case manufacture and
   intake, the pipeline may execute the authored workflow in a sandbox to verify the causal
   chain and the selected result. Runs are small and fast by construction; the program does not
   commission long-running computation. This is scoped to code the program itself commissioned
   from enrolled blind authors. The production audit of scientists' repositories remains
   strictly non-executing; nothing in this ADR weakens that rule.
5. **Minimal scientist input in production.** The skill derives everything it can from the
   repository (deterministic scan first, agent last mile second) and asks the scientist only the
   handful of questions code cannot answer, of which the governing one for this check is the
   declared analysis target. The method contract is the frozen record of those answers.
6. **The v2.0 recognizer for the active check derives the observed denominator mechanically.**
   From code dataflow where present, and from numeric-consistency relations among extracted
   quantities (planned count, retained count, event count, stated rate) where computation is
   absent. A stated rate that reconciles only with the retained subset while the frozen contract
   declares the complete domain is the conflict, regardless of wording.

## Consequences

- The active envelope requires a new tuple freeze and a fresh blind pilot under this
  architecture; the existing v1.2.0 tuple cannot be qualified.
- The six burned cases remain permanent regression fixtures. The two prose-era misses become the
  first regression targets for the v2.0 recognizer: it must catch the burned error cases through
  numeric consistency alone.
- Intake verification strengthens rather than weakens: byte-exact report matching is replaced by
  executing the authored workflow and comparing its actual output to the committed report.
- Detector qualification claims gain the sentence that matters: recognition depends on what the
  analysis does, not what the author calls things.
