# ADR-0070: Held-out qualification threshold for the complete-domain envelope

- **Status:** Proposed (maintainer acceptance required; accepting this ADR opens the sealed
  held-out block)
- **Date:** 2026-08-08
- **Scope:** The first envelope (`check:complete-domain-exposure-denominator`) only. The
  detector tuple under test is check/adapter version 2.0.4 exactly as registered at acceptance
  time; any later detector change voids this threshold for unopened cases.
- **Relates to:** Experiment 0056; ADR-0067; ADR-0068; ADR-0069

## The complete blind pilot record

Every blind pilot ever run for this envelope, in order, with the detector version that faced
it. A "fresh" result means the detector had never seen any material from that pilot.

| Pilot | Detector | Sensitivity | False accusations | Miss cause (localized and locked as regression) |
| --- | --- | --- | --- | --- |
| v4 (panel) | 1.1.0 | 0/1 | 0/2 | closed word-list vocabulary |
| v120 (lean) | 1.2.0 | 0/1 | 0/2 | conflict stated only in arithmetic |
| b | 2.0.0 | 0/1 | 0/2 | threshold/retention numeric coincidence; toy-only trace |
| c | 2.0.1 | 0/1 | 0/2 | compound-token phantom; helper-function division |
| d | 2.0.2 | 1/1 | 0/2 | pass |
| e | 2.0.2 | 1/1 | 0/2 | pass |
| f | 2.0.2 | 0/1 | 0/2 | argument-taking helper return untagged |
| g | 2.0.3 | 0/1 | 0/2 | resolved division discarded near a table-building loop |
| h | 2.0.4 | 1/1 | 0/2 | pass |

Aggregates: false accusations 0 of 18 blind controls across nine pilots (and zero anywhere
else, ever). Fresh-test sensitivity of the version current at test time: 3 of 9 overall, 3 of 6
in the v2 architecture, 1 of 1 for v2.0.4. All eighteen burned cases are permanent regression
fixtures; v2.0.4 passes all eighteen.

The honest reading: the conservative side of the detector is stable and strong. The
recognition side improves monotonically (every burned evasion stays caught), but each fresh
blind author has roughly a coin-flip chance of finding a new corner of ordinary-Python or
arithmetic-coincidence space. A threshold for the held-out block must price that in rather
than assume the pass streak continues.

## Held-out block structure and expected outcomes

The sealed block holds seven case identities in seven frozen roles. Expected outcomes:

| Role | Expected detector behavior | Counts toward |
| --- | --- | --- |
| error-bearing | conflict candidate | sensitivity (positive 1 of 2) |
| independently renamed implementation | conflict candidate | sensitivity (positive 2 of 2) |
| corrected twin | no conflict | false-accusation control |
| valid alternative | no conflict | false-accusation control |
| hard negative | no conflict | false-accusation control |
| ambiguous | abstention, no conflict | false-accusation control |
| unsupported | abstention, no conflict | false-accusation control |

## Decision (proposed)

1. **False-accusation bar: zero of five.** Any conflict candidate on any control case fails the
   envelope. This is the product's central claim and the record supports it at 0 for 18.
2. **Sensitivity bar: at least one of two positives.** Catching at least one planted error with
   zero false accusations across seven blind cases qualifies the envelope. Both positives
   caught is reported as such; one caught and one missed still qualifies, with the miss
   disclosed per-case in the qualification report.
3. **One shot, no repair.** The block is authored, reviewed, labeled, and run through the
   frozen ADR-0068 pipeline once. A missed positive is retained, localized, and locked as a
   regression for future versions, but the block is never re-run for this envelope's score.
4. **Tuple freeze.** The v2.0.4 registry digests are recorded in the block's authoring
   protocol before any author call; any detector change after that voids the run.
5. **Disclosure.** The qualification report states the full pilot table above, the
   single-review-with-escalation design (ADR-0067), the single-provider composition
   (ADR-0066), and every per-case held-out outcome, misses included.

## Why 1-of-2 rather than 2-of-2

Requiring both positives makes the envelope's pass/fail hinge on whether one blind author
samples a not-yet-traced corner of ordinary Python, which the record shows happens roughly
half the time per fresh case even while every known corner stays fixed. Requiring one of two
with a hard zero on false accusations makes the claim that matters provable and keeps the
incentive structure honest: a miss still costs (it is published), but it does not erase the
demonstrated capability. The maintainer may instead choose 2-of-2 at acceptance time by
editing rule 2; nothing else in this ADR changes.

## Consequences

- On acceptance, the seal's `withheld_until_approved_threshold` condition is met: seven fresh
  cases are blind-authored under the ADR-0069 executable-workflow rules and processed once.
- Passing moves the envelope to its qualification report and the maintainer promotion
  decision (Experiment 0056 steps 9 through 11); the honest program score can then move from
  0/10 toward 1/10.
- Failing retains everything, and the envelope waits for a future tuple and a fresh sealed
  block; the current block's cases burn either way.
