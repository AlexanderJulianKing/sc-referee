# Ten Findings delivery plan

- **Status:** Active execution plan
- **Created:** 2026-08-04
- **Current production score:** 0 of 10 target envelopes may emit a production Finding
- **Current qualification score:** 0 of 10 target envelopes independently qualified
- **Current study state:** v2 contract and first finite selected-result verifier profile
  implemented; verifier unqualified; 0 v2 cases assigned
- **Execution authority:** This document controls work sequencing and progress reporting. It does
  not itself change record meaning, detector authority, or Finding eligibility.

## Goal

Deliver ten generic, independently qualified sc-referee production Finding capabilities for the
ten frozen scientific error classes. Each error-bearing workflow must produce its intended
deterministic, exactly localized Finding without a post-audit scientist Answer. Corrected,
valid-alternative, hard-negative, ambiguous, unsupported, and unrelated controls must remain
Finding-clean through both the CLI and the installed skill. Production logic must contain no
benchmark identity, answer value, repository identity, or fixture-specific shortcut.

## Role of this document

This is the day-to-day source of truth for the ten-Findings program. It narrows the
product-wide architecture in `GENERIC_REFEREE_CAPABILITY_REVAMP_PLAN.md` to the work required for
the program-level exit gate. The current prospective-study contract is Experiment 0053 and the
v2 evaluation package. Accepted ADRs and schemas remain authoritative for policy and record
meaning.

Broader roadmap, portfolio, refactoring, and research work is out of sequence unless it is required
to close one named unchecked item below. When such work is necessary, record the blocking checklist
item before starting it.

## Completion semantics

A target envelope is delivered only when all of the following are true for one exact frozen
detector/check/adapter binding:

1. an independently authored, previously unseen error-bearing workflow is independently
   adjudicated as containing the canonical issue;
2. every required applicability, scope, evidence, and finite counterevidence premise is complete;
3. detector implementation bytes and case assignment were frozen before qualification labels;
4. pilot thresholds were accepted before the held-out block was opened;
5. held-out metrics pass the accepted envelope-specific thresholds with no known disqualifying
   false accusation;
6. an exact qualification record and maintainer promotion decision exist;
7. the production CLI emits one replay-stable Finding on the frozen error-bearing acceptance case;
8. the installed skill emits the same Finding on a fresh machine; and
9. all frozen corrected and adverse controls emit zero Findings.

The following do **not** complete a target:

- a MaterialQuestion or scientist Answer;
- a Disclosure, ConditionalConcern, or `evaluation_finding_candidate`;
- a Finding-shaped draft blocked by maturity;
- a synthetic fixture, public benchmark case, or label-visible development smoke;
- a protocol, schema, template, scaffold, queue, shell, or passing test of those artifacts;
- an assigned case without authenticated independent review;
- a pilot result without a pre-held-out threshold decision; or
- a held-out metric without exact envelope promotion.

## Checklist rules

- `[x]` means the item is complete and has a durable evidence reference in this document.
- `[ ]` means incomplete. Partial work remains unchecked and may be described in its evidence note.
- If evidence is invalidated, contaminated, superseded, or no longer replays, reopen the item.
- Update this document in the same commit as the evidence that changes a checkbox.
- Record the exact commit, artifact digest, qualification record, or report path supporting every
  newly checked item.
- At the beginning and end of each implementation turn, identify the specific unchecked item being
  closed. Do not mark a broader phase complete because its tooling exists.
- Do not declare the persistent goal complete until every program exit item is checked.

## Honest baseline at plan creation

Durable development evidence at commit `0ecf460297c6ff794a2965f11056e089eb098b95` establishes:

- [x] Ten canonical issue classes and one generic relation envelope per class are enumerated.
- [x] Pre-analysis scientific requirements can be frozen and consumed by later audits.
- [x] A closed internal review/relation case seam and deterministic comparison path exist.
- [x] Implementation-authored development matrices exercise all ten relation families without
  benchmark identity in production grammar.
- [x] Development conflicts can emit evaluation candidates; corrected controls can emit covered
  negatives; ambiguous cases can abstain.
- [x] The complete-domain versus retained-subset relation additionally passes a post-label,
  qualification-ineligible two-case smoke.
- [x] Reports separate experimental outputs from production Findings.
- [x] Current CLI, wheels, replay, and installed skill packaging pass development validation.
- [x] The v2 evidence and canonical-label contract is implemented and tested.
- [ ] An independent selected-result verifier is implemented, frozen, and qualified.
- [ ] Exact v2 detector/check/adapter bytes and binding digests are frozen for qualification.
- [ ] Authenticated v2 authors, reviewers, and evidence validators are enrolled.
- [ ] Any v2 case is assigned, authored, reviewed, labeled, or evaluated.
- [ ] Any numeric promotion threshold is accepted.
- [ ] Any v2 held-out block is opened.
- [ ] Any target envelope is independently qualified or promoted.
- [ ] Any new target error can produce a production Finding.

## Ten-envelope delivery matrix

`Dev` records implementation-authored development recognition only. It is not qualification.
`Independent` requires a previously unseen, independently authored positive plus the full frozen
control family. `Frozen`, `Pilot`, `Held-out`, `Promoted`, and `Product` use the completion semantics
above.

| # | Canonical issue class | Check | Dev | Independent | Frozen | Pilot | Held-out | Promoted | Product |
|---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Unrepaired inherited orientation | `check:founder-orientation-before-hmm-emission` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 2 | Symmetric error used for a directional process | `check:directional-measurement-error-interpretation` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 3 | Pooling before cellwise calibration | `check:poststratified-misclassification-estimator` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 4 | Arithmetic mean used for a model-expected count | `check:expected-count-background-construction` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 5 | Recoverable technical group omitted | `check:recoverable-technical-group-adjustment` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 6 | Marginal instruments used for a conditional joint target | `check:phase-split-mvmr-instrument-construction` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 7 | Hard or binned dosage used for a continuous target | `check:classifier-derived-copy-dosage-representation` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 8 | Raw eligibility used for an adjusted clonality target | `check:somatic-clonality-representation` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 9 | Reduced residualized fit used for a joint target | `check:local-perturbation-regression-specification` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| 10 | Retained subset used for a complete-domain denominator | `check:complete-domain-exposure-denominator` | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

### Matrix column definitions

- **Dev:** Generic implementation-authored positive, corrected, and abstention behavior replays.
- **Independent:** An unseen independent implementation and its required controls pass before
  qualification freeze.
- **Frozen:** Exact detector, check, adapter, verifier, manifests, bytes, digests, assignments, and
  case contract are frozen before labels.
- **Pilot:** All seven pilot cells are retained, independently verified and adjudicated, and the
  envelope's pilot metrics are complete.
- **Held-out:** The threshold-preceded held-out seven-cell block is complete and retained.
- **Promoted:** The exact envelope passes accepted metrics and has an exact maintainer promotion.
- **Product:** Both CLI and installed skill emit the production Finding on the target and zero
  Findings on the complete acceptance-control family.

## Gate 1 — Close local capability and anti-overfitting prerequisites

- [x] Reconcile the dirty local checkout, remote `main`, and this plan into one canonical working
  tree without losing unrelated work.
- [x] Implement the independent selected-result verifier required by Experiment 0053.
- [ ] Qualify and freeze that verifier before it supplies qualification evidence.
- [ ] Complete file, variable, function, level, and identifier renaming controls for every claimed
  envelope.
- [ ] Complete row/column reordering and equivalent-encoding controls wherever applicable.
- [ ] Complete wrapper, alias, conflicting-flow, and dynamic-dispatch controls wherever source
  recognition is claimed.
- [ ] Demonstrate at least one independently authored implementation style for every envelope.
- [ ] Confirm every envelope has one exact selected-result scope and supported static producer path;
  otherwise mark the case unsupported before assignment.
- [ ] Run the complete regression, packaging, replay, and skill matrix after the final pre-study
  detector change.

**Exit gate:** every `Independent` cell is checked and no known local capability defect remains.

## Gate 2 — Freeze the v2 qualification study

- [ ] Freeze the exact detector manifest and implementation bytes.
- [ ] Freeze all ten exact check/candidate/adapter binding digests.
- [ ] Freeze the independently qualified verifier identity and bytes.
- [ ] Freeze the canonical issue-class registry and selected-result evidence contract.
- [ ] Enroll and authenticate mutually independent authors, Stage-1 reviewers, Stage-2 reviewers,
  evidence validators, and detector implementers across the required providers.
- [ ] Freeze benchmark-blind authoring briefs that expose no recognizer, expected answer, case role,
  block role, or prior detector output.
- [ ] Freeze 140 opaque, no-replacement assignments: ten envelopes by seven cells by two blocks.
- [ ] Verify that no public, answer-visible, v1, or implementation-authored case is metric-eligible.
- [ ] Seal the held-out block before any pilot label or detector outcome exists.

**Exit gate:** every assignment and relevant byte is immutable and replayable, with zero scientific
labels or detector outcomes yet available.

## Gate 3 — Complete the 70-case threshold pilot

- [ ] Author and retain all 70 assigned pilot workflows without replacement.
- [ ] Freeze every selected-result declaration before scientific review.
- [ ] Independently rederive every selected report, producer, operand path, and alternative producer
  from immutable case bytes.
- [ ] Complete authenticated answer-blind Stage-1 review.
- [ ] Complete fresh cross-provider Stage-2 review using canonical issue-class enums.
- [ ] Retain failures, withdrawals, contamination, disagreement, ambiguity, insufficiency, and
  unsupported cases in the outcome ledger.
- [ ] Run the frozen detector on every pilot opportunity and replay every result.
- [ ] Calculate per-envelope false-accusation, missed-error, precision, sensitivity, coverage, and
  abstention measures using the frozen opportunity denominators.
- [ ] Accept or reject a numeric threshold proposal for each envelope.
- [ ] Freeze the maintainer-approved threshold decision before opening held-out material.

**Exit gate:** the complete pilot and threshold decision are immutable. Any detector logic change
creates a new version and reopens the affected freeze and pilot items.

## Gate 4 — Complete the 70-case held-out evaluation

- [ ] Open the sealed held-out block only after the threshold decision replays.
- [ ] Author and retain all 70 assigned held-out workflows without replacement.
- [ ] Complete the same independent evidence validation and two-stage scientific review used for
  the pilot.
- [ ] Run the unchanged frozen detector and replay every held-out opportunity.
- [ ] Calculate accepted per-envelope metrics and uncertainty from held-out outcomes only.
- [ ] Demonstrate zero known disqualifying high-severity false accusations.
- [ ] Convert every discovered false accusation and missed error into a permanent regression case
  without changing the evaluated version.
- [ ] Publish the qualification evidence and explicit limitations for every envelope.

**Exit gate:** every `Held-out` cell is checked, and each envelope has an immutable pass or fail
decision under its predeclared threshold.

## Gate 5 — Promote exact envelopes

- [ ] Promote founder orientation only if its exact held-out envelope passes.
- [ ] Promote directional measurement error only if its exact held-out envelope passes.
- [ ] Promote poststratified misclassification only if its exact held-out envelope passes.
- [ ] Promote expected-count background construction only if its exact held-out envelope passes.
- [ ] Promote recoverable technical-group adjustment only if its exact held-out envelope passes.
- [ ] Promote phase-split MVMR instrument construction only if its exact held-out envelope passes.
- [ ] Promote classifier-derived continuous dosage only if its exact held-out envelope passes.
- [ ] Promote somatic clonality representation only if its exact held-out envelope passes.
- [ ] Promote local-perturbation regression specification only if its exact held-out envelope passes.
- [ ] Promote complete-domain exposure denominator only if its exact held-out envelope passes.
- [ ] Confirm that every failed or unevaluated sibling remains Finding-ineligible.
- [ ] Publish exact supported envelopes, abstentions, known limitations, and versioned grants.

**Exit gate:** every `Promoted` cell accurately reflects one exact accepted qualification and
maintainer decision; there is no family-wide or portfolio-wide implied authority.

## Gate 6 — Prove installed product behavior

- [ ] Run the frozen ten-positive acceptance matrix through the production CLI.
- [ ] Confirm the CLI emits the intended ten Findings with exact evidence localization.
- [ ] Run all corrected twins, valid alternatives, hard negatives, ambiguous cases, unsupported
  cases, unrelated controls, and the two existing correct cold workflows through the CLI.
- [ ] Confirm every acceptance control remains Finding-clean.
- [ ] Install the packaged skill on a fresh Codex environment and repeat the complete matrix.
- [ ] Install the packaged skill on a fresh Claude Code environment and repeat the complete matrix.
- [ ] Confirm CLI and both installed-skill runs are byte-replayable for all deterministic records.
- [ ] Confirm no benchmark identity, answer-side value, or qualification-private label is reachable
  from the production decision path.
- [ ] Publish a final ten-envelope product acceptance report.

**Exit gate:** every `Product` cell is checked.

## Program exit checklist

- [ ] Ten independently adjudicated error-bearing workflows produce their intended production
  Findings without post-audit human rescue.
- [ ] Ten corrected twins produce zero Findings.
- [ ] Ten valid alternatives produce zero Findings.
- [ ] Ten close hard negatives produce zero Findings.
- [ ] Ten ambiguous cases produce zero Findings and preserve the unresolved premise.
- [ ] Ten unsupported cases produce zero Findings and localize the unsupported boundary.
- [ ] Independently renamed implementations behave according to their scientific state rather than
  their names or layout.
- [ ] The two existing correct cold workflows produce zero Findings.
- [ ] Every Finding is deterministic, exactly localized, independently qualified, narrowly worded,
  and reproducible through CLI and installed skills.
- [ ] No target relies on benchmark identity, answers, filenames, expected counts, or post-audit
  scientist rescue.
- [ ] The capability matrix reports 10 of 10 `finding_qualified` and 10 of 10 installed-product
  acceptance passes.

## Immediate next unchecked item

Independently qualify and freeze the exact selected-result verifier implementation and profile at
commit `57f4e581ff424c8713fceb5926e521cc3c060fe6`. Then continue the remaining Gate 1 renaming,
encoding, dynamic-dispatch, and independent-implementation controls. Do not assign v2 cases or
perform unrelated capability expansion before Gate 1 is complete.

## Evidence log

### 2026-08-04 — Canonical repository reconciliation

- Canonical remote `main` was reconciled at commit
  `b2f85043ee1d31fb51efd69e6ad349c91749898a`.
- Superseded but potentially useful work was preserved on branch
  `preserve/prospective-v1-scaffold-20260804` at commit
  `7855669`; it was not silently discarded or merged into the delivery baseline.
- Twelve duplicate working files were moved out of the canonical tree to
  `/Users/alexanderking/Desktop/random_stuff/sc-referee-implementation-v0.1.0/tmp/preserved-duplicate-files-20260804/`.
- The canonical delivery plan was published on `main`; repository reconciliation did not change
  any Finding eligibility or count.

### 2026-08-04 — Selected-result verifier implementation

- Implementation commit: `57f4e581ff424c8713fceb5926e521cc3c060fe6`.
- Verifier module SHA-256:
  `d34ad9b7a85bf78840fb9109bd764a26e5a25a4e89484ce2788436120ead7eac`.
- The auditor-owned profile rederives selected report, exact output bytes, producer, source
  operands, and alternatives from a closed retained case tree without executing project code.
- Closed outcomes preserve ambiguity, insufficiency, and unsupported structure. Caller-supplied
  candidates, reasons, author labels, and self-digested forgeries cannot satisfy byte replay.
- The finite v1 profile intentionally supports only a narrow ASCII/LF, static Python,
  literal-`Path`, `.csv`/`.tsv` operand grammar. Other source languages, dynamic flow, extra files,
  encoding cookies, translated newlines, executable inputs, and resource-ceiling violations
  abstain.
- Adversarial independent review reproduced and closed forward references, hidden Python and shell
  producers, role overlap, import order, retained-byte mismatch, locale/newline drift, encoding
  cookies, symlinks, tree races, and pre-allocation/cumulative-budget attacks. Final review reported
  no remaining P1/P2 blocker. This review is implementation evidence, **not** verifier
  qualification.
- Verification passed: 70 focused verifier/v2/distribution tests; 1,723 full tests; Ruff check and
  format; mypy for 122 production and 31 evaluation source files; starter validation; regression
  replay; production and evaluation wheel build/install smoke; and the complete handoff verifier.
- No v2 case, label, threshold, qualification, promotion, CLI Finding, or installed-skill Finding
  was created. The honest program score remains 0/10.

## Evidence log

| Date | Change | Evidence | Checkboxes changed |
|---|---|---|---|
| 2026-08-04 | Baseline plan created after correcting the distinction between development recognition and production delivery. | Commit `0ecf460297c6ff794a2965f11056e089eb098b95`; `GENERIC_REFEREE_CAPABILITY_REVAMP_PLAN.md`; Experiments 0052 and 0053; green CI run `30897659713`. | Development baseline only; qualification, promotion, and product cells remain unchecked. |
