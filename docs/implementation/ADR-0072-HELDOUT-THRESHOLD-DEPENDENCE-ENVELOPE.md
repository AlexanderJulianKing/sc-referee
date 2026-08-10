# ADR-0072: Held-out threshold for the dependence envelope

- **Status:** Accepted by the maintainer on 2026-08-10, in session ("2/2, and yes go ahead with
  exam locks."), at the two-of-two sensitivity bar. Acceptance opens the sealed
  qualification-heldout block once the lane freeze exists and its briefs pass the pre-freeze
  hostile review.
- **Date:** 2026-08-10
- **Scope:** `check:authorized-independent-unit-entry-into-row-independent-procedure` version
  `1.1.0` exactly as registered at acceptance time, evaluated through the generic
  `detector:bounded-analysis-method-conflict` route. Any later change to the recognizer package
  or its registered adapter voids this threshold for unopened cases.
- **Relates to:** ADR-0062, ADR-0067, ADR-0068, ADR-0069, ADR-0070, ADR-0071, Experiment 0058.

## The complete blind pilot record

| Pilot | Recognizer | Outcome | Sensitivity | False accusations | Note |
|---|---|---|---|---|---|
| a | v1.1.0 | Review-unresolved | n/a (detector never ran) | n/a | Both blind reviewers unanimously judged the case template itself in-class; the protocol refused the answer key. Template redesigned (disjoint collections). |
| b | v1.1.0 | Closed at intake | n/a | n/a | Frozen-workflow-template enforcement predated its byte-exact statement in the briefs; authors honest; configuration defect category-closed (single shared constant). |
| c | v1.1.0 | Completed | 1/1 | 0/5 | Pasted-row positive caught; all controls clean; no escalation. |
| d | v1.1.0 | Completed | 1/1 | 0/5 | Genuine repeated-measurement positive caught; hard negative with a report byte-identical to the error's correctly cleared; no escalation. Pre-fire hostile review blocked and replaced an in-class decoy before authoring. |

Honest reading: the two completed pilots are 12/12 with zero false accusations, but both
positives were caught by the same key-multiplicity proof route, and every case was authored
inside a deliberately narrow frozen envelope (one workflow shape, prescribed literals). The
examination adds a fresh construction per role plus a second, independently structured positive
(three measurements per unit, a different row-independent procedure). A dress-rehearsal pilot
(the threshold-pilot block) runs after this acceptance and before the sealed block; that
ordering is disclosed here: the bars were chosen before the rehearsal, so the rehearsal informs
nothing about the bars and exists to validate the seventh construction blind.

## Held-out block structure and expected outcomes

Seven sealed cases: `error_bearing` and `renamed_implementation` (the two positives; the second
uses eight units with three measurements each and `scipy.stats.mannwhitneyu`), and five
controls: `corrected_twin`, `valid_alternative`, `hard_negative` (covered negatives),
`ambiguous` (question, no authorization lock by design), `unsupported` (named abstention). A
conflict candidate on any control is a false accusation.

## Decision (accepted)

1. **False-accusation bar: zero of five.** Any conflict candidate on any control case fails
   the envelope.
2. **Sensitivity bar: two of two.** Both positives must be caught. One caught and one missed
   fails the envelope, with the miss retained, localized, and locked as a regression, and the
   outcome published.
3. **One shot, no repair.** The block is authored, reviewed, labeled, and run through the
   frozen ADR-0068 pipeline exactly once. No re-run for this envelope's score.
4. **Tuple freeze.** The registry digests are recorded in the block's authoring protocol
   before any author call; any detector change after that voids the run.
5. **Disclosure.** The qualification report publishes the full pilot table above, the review
   design (ADR-0067) and provider composition (ADR-0066), every per-case outcome including
   misses, and the dependence-specific asymmetries: role-derived authority (the ambiguous
   control receives no lock); the detector observes `requirements.txt` while the blind reviewer
   does not; the covered-negative proof is scoped to the `k1` namespace only; the review-scope
   sentence's known one-directional effect on the paired-procedure control; and the fact that
   authority locks are minted post-intake by the unblinded orchestrator, so the examination's
   blindness claim covers authors, reviewers, and the detector's development, never the lock
   minter.

## Why two-of-two

The maintainer chose the stricter bar over ADR-0070's one-of-two precedent, with the tradeoff
stated at acceptance: envelope-10's rationale for one-of-two rested on fresh authors sampling
untraced corners of ordinary Python, whereas this envelope's byte-frozen workflow shape removes
that axis, leaving data-shaped constructions both of which the pilots caught cleanly; and the
promotion review of ADR-0071 demonstrated that a one-of-two exam bar permits a one-miss
detector to resolve a validated grant unless a stricter gate is added later. Two-of-two accepts
the risk that a single authoring accident on either positive fails a published examination.

## Examination authority locks

The maintainer's standing authorization of 2026-08-10 excluded sealed examinations. The
acceptance quoted above grants, per-decision, the minting of the six examination authorization
locks (all roles except `ambiguous`) under the established template: ordered `k1` unit
definition, registered procedures, `case_root` declared execution root, standard limitations,
intake-derived digests; minted after intake and before review; disclosed under rule 5.

## Consequences

- On acceptance and a passing pre-freeze brief review, the lane freeze is executed once; the
  threshold-pilot block runs as a dress rehearsal; the sealed block is then authored and
  processed once.
- If the dress rehearsal exposes a defect in any construction, the lane is rebuilt and resealed
  before the sealed block opens; this acceptance binds the envelope and the bars, not case
  identities, and survives such a rebuild.
- Passing moves the envelope to its qualification report and a separate promotion decision,
  which pins exam-time byte identities per the ADR-0071 precedent.
- Failing retains everything; the block's cases burn either way; the outcome is published
  whatever it is.
