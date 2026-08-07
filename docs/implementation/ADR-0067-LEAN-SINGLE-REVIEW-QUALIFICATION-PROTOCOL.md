# ADR-0067: Lean single-review qualification protocol for later envelopes

- **Status:** Accepted by the maintainer on 2026-08-07, in session, as part of an explicit
  two-part green light covering this ADR and the completion of the first envelope's pilot under
  the pre-existing rules
- **Date:** 2026-08-07
- **Scope:** Envelopes whose review protocols have not yet been frozen (currently envelopes 1
  through 9 in the delivery matrix). The active first envelope
  (`check:complete-domain-exposure-denominator`) completes under its already-frozen protocols
  and ADR-0066.
- **Relates to:** Experiment 0056; ADR-0066; the 4+2 review-panel requirement inherited from the
  accepted specification baseline

## Context

The 4+2 panel design (four blind Stage-1 reviews plus two fresh Stage-2 reviews per case) was
adopted when reviewer disagreement rates were unknown. The program now has direct evidence: across
all thirty admitted scientific reviews and every completed calibration to date, no two reviewers
have ever disagreed on a verdict. The only cross-reviewer differences have been procedural
(unresolved-material-question hygiene and output formatting). Meanwhile each panel costs six
model calls, calibrations, and multiple frozen artifacts per case, and the program has nine more
envelopes, each with a three-case pilot and a seven-case held-out block.

The maintainer reviewed the panel design and directed a leaner protocol, reserving redundancy
for the situations where it adds information.

## Decision

For each in-scope envelope's pilot and held-out review work:

1. **One merged blind review per case replaces the 4+2 panel by default.** The single reviewer,
   blind to case roles, expected answers, and detector output, both states whether the in-scope
   issue is demonstrably present and, when present, names the exact canonical issue class. A
   wrong issue class is a miss, exactly as a wrong verdict is.
2. **Escalation instead of standing redundancy.** A second blind review from a different model
   family is required only when the first review is not clean: a non-eligible verdict on an
   expected shape, a nonempty unresolved-material-questions array, any admission failure, or any
   verdict that disagrees with the frozen case-role expectation once unblinded. On disagreement
   between the two, the case is retained as unresolved rather than adjudicated by a third call.
3. **Retained without reduction:** blind authoring by enrolled non-detector authors; reviewer
   calibration before first participation; freeze-before-call for every prompt and protocol;
   one-shot calls with all failures retained; the deterministic selected-result verifier;
   label-before-detector ordering with the label freeze; deterministic replay; served-model
   post-verification for CLI transports; and the maintainer threshold decision before held-out
   material opens.
4. **The evidence contract collapses into the recording code.** The recorder's fail-closed
   validations are the contract; no separate per-envelope contract tuple artifact is required.
   The recorder implementation files are digest-bound in each envelope's frozen protocol, which
   preserves the replay guarantee the standalone contract provided.
5. **Model families follow ADR-0066:** reviews may come from distinct Anthropic model families
   while cross-provider access is unavailable, with the same disclosure obligations. When a
   second provider is available again, the escalation reviewer in rule 2 should come from it.
6. **Disclosure:** every qualification report for material reviewed under this ADR must state
   that the review design was single-review-with-escalation and cite this ADR, the empirical
   zero-disagreement record that motivated it, and any escalations that occurred.
7. **Reversal trigger:** if any envelope accumulates two or more escalations that end in genuine
   verdict disagreement, the 4+2 panel design is restored for that envelope's remaining cases
   before further labels are created.

## Consequences

- Per-case review cost drops from six model calls to one in the common case.
- A single reviewer's undetected mistake can now mislabel a case; the mitigations are the
  role-expectation unblinding check in rule 2, the deterministic verifier, and the reversal
  trigger. The maintainer accepts this trade for development velocity, with the audit trail
  unchanged in kind.
- Existing frozen first-envelope artifacts are unaffected; nothing already frozen reopens.
