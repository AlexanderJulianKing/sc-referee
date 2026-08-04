# Ten Findings delivery plan

- **Status:** Active execution plan
- **Created:** 2026-08-04
- **Current production score:** 0 of 10 target envelopes may emit a production Finding
- **Current qualification score:** 0 of 10 target envelopes independently qualified
- **Current study state:** the over-scoped selected-result meta-qualification was stopped before
  case authoring; lean direct detector qualification is active under Experiment 0056, with 0
  metric-eligible cases authored, the first envelope's repaired v3 detector/binding/comparator/
  evidence tuple frozen, 20 exact participant configurations declared, 14 no-replacement
  assignments frozen, and the seven-case held-out block sealed before labels or outcomes
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
the program-level exit gate. The current prospective-study contract is Experiment 0056 and the v3
evaluation-private evidence contract. Accepted ADRs and schemas remain authoritative for policy
and record meaning.

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
- [x] The v3 author-only declaration, coordinator binding, full-panel canonical-label projection,
  and exact independent-evidence contract are implemented and tested.
- [x] A deterministic answer-isolated selected-result comparator is implemented and adversarially
  tested; it has no independent scientific-label or Finding authority.
- [x] Exact current detector/check/adapter/comparator/evidence bytes and binding digests are frozen
  for the first direct-qualification envelope.
- [x] Exact first-envelope author, 4+2 reviewer, evidence-validator, and detector-implementer
  configurations are declared and frozen; authentication and reviewer calibration remain pending.
- [x] Fourteen opaque first-envelope cases are assigned without replacement and seven are sealed;
  none is authored, reviewed, labeled, or evaluated.
- [ ] Any numeric promotion threshold is accepted.
- [ ] Any direct-qualification held-out block is opened.
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
| 10 | Retained subset used for a complete-domain denominator | `check:complete-domain-exposure-denominator` | [x] | [x] | [ ] | [ ] | [ ] | [ ] | [ ] |

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

## Execution order

The gates below are applied envelope by envelope, beginning with
`check:complete-domain-exposure-denominator`. This produces a real 1/10 result after one complete
14-case lane instead of waiting for a non-normative 96-case verifier meta-study plus all 140 direct
cases. Each later envelope repeats the same gates without changing a previously frozen tuple. The
complete program still requires all 140 cases and every 10/10 exit item.

The accepted scientific qualification panel remains four blind Stage-1 reviews across two
providers plus two fresh cross-provider Stage-2 reviews per metric case. Cryptographic registrar
chains, exhaustive installed-distribution locking, and fresh-filesystem relocation are not part of
the delivery gate. Exact reviewer/model/context/prompt/tool/environment/transcript identity,
blindness, frozen labels, hashes, deterministic replay, held-out safety gates, and narrow public
claims remain mandatory.

## Gate 1 — Close shared harness and current-envelope anti-overfitting prerequisites

- [x] Reconcile the dirty local checkout, remote `main`, and this plan into one canonical working
  tree without losing unrelated work.
- [x] Implement the independent selected-result verifier required by Experiment 0053.
- [x] Freeze the deterministic selected-result comparator and build identity used only for
  answer-isolated label/result comparison; do not give it scientific-label authority.
- [x] Complete file, variable, function, level, and identifier renaming controls for the current
  envelope before its assignments are authored; repeat before each later envelope freezes.
- [x] Complete row/column reordering and equivalent-encoding controls wherever applicable to the
  current envelope.
- [x] Complete wrapper, alias, conflicting-flow, and dynamic-dispatch controls wherever source
  recognition is claimed.
- [x] Demonstrate at least one independently authored implementation style for the current
  envelope without using a metric-eligible case.
- [x] Confirm the current envelope has one exact selected-result scope and supported static producer
  path; otherwise mark the case unsupported before assignment.
- [x] Run the complete regression, packaging, replay, and skill matrix after the final pre-study
  detector change.

**Exit gate:** the current envelope's `Independent` cell is checked, the shared comparator/build is
frozen, and no known local capability defect remains for that lane. Repeat for each later envelope.

## Gate 2 — Freeze the current direct-qualification lane

- [x] Freeze the current envelope's exact detector manifest and implementation bytes.
- [x] Freeze the current envelope's exact check/candidate/adapter binding digest.
- [x] Freeze the deterministic comparator/build identity and its finite supported grammar.
- [x] Freeze the canonical issue-class registry and selected-result evidence contract.
- [x] Freeze exact mutually independent author, four Stage-1 reviewer, two fresh Stage-2 reviewer,
  evidence-validator, and detector-implementer configurations across the required providers.
- [ ] Authenticate each enrolled participant configuration when it first participates, retain its
  exact identity and transcript digests, and disclose agent-only review.
- [x] Freeze benchmark-blind authoring briefs that expose no recognizer, expected answer, case role,
  block role, or prior detector output.
- [x] Freeze 14 opaque, no-replacement assignments for the current envelope and seal its held-out
  seven before pilot labels; repeat for the other nine envelopes for a final total of 140.
- [x] Verify that no public, answer-visible, v1, or implementation-authored case is metric-eligible
  in the frozen first-envelope assignment matrix.
- [x] Seal the held-out block before any pilot label or detector outcome exists.

**Exit gate:** all 14 assignments and relevant bytes for the current envelope are immutable and
replayable, its held-out seven are sealed, and zero scientific labels or detector outcomes exist.

## Gate 3 — Complete the current seven-case threshold pilot

- [ ] Author and retain all seven assigned pilot workflows for the current envelope without
  replacement; repeat to reach 70 across ten envelopes.
- [ ] Freeze every selected-result declaration before scientific review.
- [ ] Independently rederive every selected report, producer, operand path, and alternative producer
  from immutable case bytes.
- [ ] Complete four answer-blind Stage-1 reviews across two providers per case.
- [ ] Complete two fresh cross-provider Stage-2 reviews per case using canonical issue-class enums.
- [ ] Retain failures, withdrawals, contamination, disagreement, ambiguity, insufficiency, and
  unsupported cases in the outcome ledger.
- [ ] Run the frozen detector on every pilot opportunity and replay every result.
- [ ] Calculate per-envelope false-accusation, missed-error, precision, sensitivity, coverage, and
  abstention measures using the frozen opportunity denominators.
- [ ] Accept or reject a numeric threshold proposal for the current envelope through the required
  pilot-informed ADR and a forward accepted schema capable of representing the decision.
- [ ] Freeze the maintainer-approved threshold decision before opening this envelope's held-out
  material.

**Exit gate:** the complete pilot and threshold decision are immutable. Any detector logic change
creates a new version and reopens the affected freeze and pilot items.

## Gate 4 — Complete the current sealed seven-case held-out evaluation

- [ ] Open the sealed held-out block only after the threshold decision replays.
- [ ] Author and retain all seven assigned held-out workflows for the current envelope without
  replacement; repeat to reach 70 across ten envelopes.
- [ ] Complete the same independent evidence validation and two-stage scientific review used for
  the pilot.
- [ ] Run the unchanged frozen detector and replay every held-out opportunity.
- [ ] Calculate accepted per-envelope metrics and uncertainty from held-out outcomes only.
- [ ] Demonstrate zero known disqualifying high-severity false accusations.
- [ ] Convert every discovered false accusation and missed error into a permanent regression case
  without changing the evaluated version.
- [ ] Publish the qualification evidence and explicit limitations for the current envelope.

**Exit gate:** the current envelope's `Held-out` cell is checked and it has an immutable pass or
fail decision under its predeclared threshold. Repeat for each later envelope.

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

Calibrate and authenticate the exact six frozen reviewer configurations, retaining exact prompts,
outputs, identities, execution contexts, and transcript digests. Then open only the seven-case
pilot author briefs, authenticate their six frozen author contexts, and author all seven pilot
workflows without replacement. Freeze each truthful author-only selected-result declaration before
any scientific review. Preserve the stopped Experiment 0055 machinery as non-qualifying
development evidence, but perform no further cryptographic-registrar, distribution-`RECORD`,
hostile-importer, separate 96-case verifier-study, or filesystem-relocation work.

Do not reduce the accepted 4+2 scientific review panel, open held-out material before a
pilot-informed threshold ADR, or bypass the forward-schema requirement for promotion. Do not
perform unrelated capability expansion before the complete first pilot is retained.

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

### 2026-08-04 — Qualification v1.0 invalidation and v1.1 no-go

- Experiment 0054 was invalidated before target execution because its proposed oracle copied
  semantic truth from the author certificate and its profile did not fully specify the target's
  classification grammar.
- Corrective Experiment 0055 added answer-blind v1.1 assignments and development-only security
  scaffolding. No provider case, semantic attestation, target output, metric, or promotion from
  that experiment is qualification evidence.
- Independent adversarial review of the uncommitted v1.1 controller reproduced false registered-
  reason acceptance from two fabricated attestations, acceptance of an evidence-free pilot pass,
  acceptance of an ad-hoc under-specified runner freeze, and reviewer/target identity overlap.
- The same review confirmed the exact-span, assignment/packet, import-firewall, and validation-
  wrapper corrections, but classified the full v1.1 tuple as no-go pending the blockers in the
  immediate-next-item section.
- No checkbox changed. The honest qualification and production scores remain 0/10.

### 2026-08-04 — Stop over-scoped verifier meta-qualification; begin direct qualification

- A read-only audit of the accepted specification, ADRs, v0.18 schemas, and Milestone 0 build spec
  found no requirement for Experiment 0055's separate 96-case verifier study, cryptographic
  registrar, exhaustive installed-distribution locking, hostile local-importer defense, or two
  fresh-filesystem-location replays.
- The same audit confirmed the requirements that remain mandatory: the five-part Finding gate,
  validated envelope maturity, four blind Stage-1 plus two fresh Stage-2 reviews per case,
  label-before-detector ordering, pilot-informed thresholds, held-out safety gates, deterministic
  replay, public qualification evidence, maintainer promotion, and narrow capability claims.
- Experiment 0055 was stopped before any metric-eligible case existed. Its comparator and security
  work remain non-qualifying development evidence. Experiment 0056 now qualifies each detector
  directly, beginning with the complete-domain exposure-denominator envelope.
- The interrupted development branch was restored to 178 passing selected-result qualification,
  packaging, launcher, target-worker, and lazy-import tests before the change in study direction.
- No qualification or production checkbox changed. The honest scores remain 0/10.

### 2026-08-04 — First-envelope Gate 1 controls and regression closure

- The complete-domain profile was widened generically from interval-like units to also recognize
  transects, observations, samples, and sites, plus the ordinary exclusion wording “left out.” The
  profile is now check/adapter version `1.1.0`; no filename, case ID, benchmark identity, numeric
  answer, or source identifier enters its scientific grammar.
- A detector-blind independent author produced the development-only acoustic-route workflow at
  `evaluation/development-cases/complete-domain-exposure-independent-style-1`. It initially exposed
  the generality gap and then passed unchanged after the generic grammar repair. Its manifest keeps
  it ineligible for qualification metrics.
- `evaluation/development-controls/complete-domain-exposure-v1.1.0/MANIFEST.json` records the
  applicable renaming, prose-layout, source-identifier, control-family, independent-style, and
  exact-selected-result axes. Row/column reordering and source wrapper/alias/dynamic-dispatch are
  explicitly not applicable because this adapter claims only a selected Markdown prose relation;
  source names and flow cannot provide scientific evidence.
- A separate three-file development control replays as exactly one static selected result under
  `selected-result-profile:python-static-marked-report-v1` without executing project code. The
  independently authored acoustic workflow remains outside that narrow producer grammar and would
  be classified unsupported if proposed as a metric case; it is evidence of detector style
  independence, not of comparator coverage.
- Exact current identities before the precase freeze are: check manifest
  `sha256:ab5760d4bd5201bd7dc35ae80afa0ba563f89d761a849940190baa9b64970fba`, adapter manifest
  `sha256:cbf4d745348c8ca733e22903cd2d6121fec9cc9112f92a253117c1e6753f1b50`, and method-conflict
  binding `sha256:127306babb8127dc820ea2d3f322ca47e7da0af976ea771eb7ef10e445fcb4f5`.
- Verification passed: 14 focused first-envelope tests; 1,865 repository tests; Ruff check and
  format; mypy for 122 production and 41 evaluation source files; 79 public schema examples; all
  147 retained regression cases and 31 module baselines; deterministic replay; production and
  evaluation wheel build/install smoke; and the complete handoff verifier. A reproducible
  evaluation-wheel build using `SOURCE_DATE_EPOCH=1785880000` produced identical independent
  SHA-256 values
  `9af1306585d973fde9646de4618253f3367cd1a8d9e15f9ea44c3e3d7fbf7e29`.
- These are development and readiness results only. Zero metric-eligible cases, scientific labels,
  thresholds, held-out outcomes, promotions, or production Findings exist; the honest score
  remains 0/10.

### 2026-08-04 — Historical first-envelope v2 precase tuple freeze (superseded)

- Source checkpoint `f6d5adb6d6314f58fa2ea9a09e721015732ed2c4` was committed only after the
  complete Gate 1 verification passed.
- `evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-precase/FREEZE_MANIFEST.json`
  binds that checkpoint to the exact detector manifest and implementation, check and adapter
  manifests, method-conflict binding, canonical issue-class entry, case-evidence contract,
  deterministic comparator implementation/runtime/profile, development-control record, and the
  twice-reproduced evaluation-wheel digest. Its self-digest is
  `sha256:55a515535246aa1a4d1c091ed020e8a087b78552b727ee947439b26a01142ae8`.
- Two fail-closed tests replay the freeze against the current registries and exact source bytes.
  Any later change to a bound file or digest invalidates this tuple instead of silently changing
  the study target.
- The freeze explicitly contains zero metric cases, labels, detector outcomes, thresholds,
  qualification authority, promotion, or Finding permission. The delivery matrix therefore
  remains 0/10 qualified and 0/10 production; the `Frozen` cell remains unchecked until all 14
  assignments and roles are frozen.

### 2026-08-04 — Repaired v3 evidence contract and replacement tuple freeze

- A pre-assignment audit found that the v2 author artifact exposed coordinator-only scientific
  identities, could not truthfully represent multiple or statically unsupported selected results,
  and accepted caller-authored compact Stage-2 summaries instead of deriving them from the exact
  full 4+2 panel evidence. No case had been assigned, so nothing was grandfathered.
- Commit `b723f000bccff18d49efca64a4d6ece92e2b5dd2` repaired those defects in v3 while preserving
  the accepted review panel, label-before-detector ordering, identity/context independence, and
  zero authority. The historical v2 freeze remains immutable but is not current.
- The replacement precase manifest at
  `evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-v3-precase/FREEZE_MANIFEST.json`
  binds the repaired evidence contract, direct lane, exact detector/check/adapter/binding,
  deterministic comparator, review protocol, and twice-reproduced evaluation wheel. Its digest is
  `sha256:2526c7d710705bc8705ffc8dbc062f233c5555f8e9445d1ffea23c50a68a14d6`.
- Verification passed 1,894 repository tests, Ruff check and format, mypy for 122 production and 42
  evaluation source files, 79 public schema examples, all 147 regression cases and 31 module
  baselines, deterministic wheel reproduction, and the complete handoff verifier.
- No case, label, detector outcome, threshold, promotion, or production Finding was created; the
  honest qualification and production scores remain 0/10.

### 2026-08-04 — First direct lane assignments frozen and held-out sealed

- A pre-exposure replay found that the first lane's author system prompt mentioned a README while
  the frozen selected-result grammar permits only the exact input, Python producer, and selected
  report roles. That lane was superseded with zero participant authentications, brief exposures,
  authored cases, labels, or outcomes; its bytes and supersession record remain retained.
- The replacement exact enrollment freezes 12 author contexts, a 2+2 cross-provider Stage-1 panel,
  a fresh 1+1 cross-provider Stage-2 panel, one deterministic evidence validator, and one
  label-blind detector implementer. Its digest is
  `sha256:c29bdc3c277b840c2bf9b4369f69181190663530467926ccfdfb24407eff0016`;
  all configurations remain declared-not-authenticated and the six reviewers remain calibration-
  gated.
- The authoring manifest freezes fourteen opaque author-visible briefs after a finite literal and
  field leakage screen. It contains no controller cell/block role, recognizer identity, expected
  answer, prior label, or detector output. Its digest is
  `sha256:7133cb96256ab17a7eff58efa4d2b9a97dc9c2addac575a3ec03b830c869ec8e`.
- The lane freeze binds every brief to one no-replacement assignment, reuses the accepted
  prospective protocol, and seals the seven assigned held-out identities with author access
  withheld until an approved pilot threshold. Its digest is
  `sha256:c58ee57c01d5f7c46855eb9f554d0a476f664e44edbdd7e15679bd53d72fa12b`.
- Exact rebuild and replay tests confirm the 14-cell matrix, participant isolation, configuration
  digests, brief blindness, held-out seal, and zero authority. All 1,904 repository tests, Ruff,
  production and evaluation mypy, and starter validation pass; the one wheel smoke that initially
  encountered an unwritable user cache passed with the project-local uv cache. No author session,
  reviewer session, scientific label, detector outcome, metric, qualification, promotion, or
  Finding exists. The `Frozen` matrix cell remains unchecked until the authored case contracts and
  complete pre-label evidence are frozen; scores remain 0/10.

## Evidence log

| Date | Change | Evidence | Checkboxes changed |
|---|---|---|---|
| 2026-08-04 | Baseline plan created after correcting the distinction between development recognition and production delivery. | Commit `0ecf460297c6ff794a2965f11056e089eb098b95`; `GENERIC_REFEREE_CAPABILITY_REVAMP_PLAN.md`; Experiments 0052 and 0053; green CI run `30897659713`. | Development baseline only; qualification, promotion, and product cells remain unchecked. |
| 2026-08-04 | Replaced the non-normative verifier meta-study with lean direct envelope qualification while retaining every accepted scientific review and Finding gate. | Experiment 0056; accepted-spec/ADR/schema audit; 178 focused tests. | No qualification, promotion, or product cell changed; score remains 0/10. |
| 2026-08-04 | Closed the first envelope's generic controls and verified its independent development style plus exact static selected-result scope. | `evaluation/development-controls/complete-domain-exposure-v1.1.0/MANIFEST.json`; 14 focused tests; 1,865 full tests; complete handoff verifier; reproducible wheel digest `9af1306585d973fde9646de4618253f3367cd1a8d9e15f9ea44c3e3d7fbf7e29`. | First-envelope `Independent` and six applicable Gate 1 control/readiness items checked; qualification, promotion, product, and production score remain 0/10. |
| 2026-08-04 | Froze the first envelope's exact detector/binding/comparator/evidence tuple before case authoring. | Source commit `f6d5adb6d6314f58fa2ea9a09e721015732ed2c4`; freeze digest `sha256:55a515535246aa1a4d1c091ed020e8a087b78552b727ee947439b26a01142ae8`; two replay tests. | Gate 1 comparator freeze and first four Gate 2 tuple-freeze items checked; `Frozen`, qualification, promotion, and product cells remain unchecked. |
| 2026-08-04 | Repaired the evaluation-private evidence contract before assignment and superseded the zero-case v2 tuple with an exact v3 replacement. | Commit `b723f000bccff18d49efca64a4d6ece92e2b5dd2`; replacement freeze digest `sha256:2526c7d710705bc8705ffc8dbc062f233c5555f8e9445d1ffea23c50a68a14d6`; 1,894 full tests and complete handoff verifier. | Current first-envelope tuple items remain checked; no qualification, promotion, product, or score change. |
| 2026-08-04 | Froze the exact first-envelope participant configurations, blind author briefs, fourteen no-replacement assignments, and seven-case held-out seal; superseded one unexposed prompt-conflicted lane before use. | Replacement enrollment digest `sha256:c29bdc3c277b840c2bf9b4369f69181190663530467926ccfdfb24407eff0016`; brief digest `sha256:7133cb96256ab17a7eff58efa4d2b9a97dc9c2addac575a3ec03b830c869ec8e`; lane digest `sha256:c58ee57c01d5f7c46855eb9f554d0a476f664e44edbdd7e15679bd53d72fa12b`; zero-exposure supersession digest `sha256:b4035359abb43bc83850751ca5cc05f513754e4b50c61fe73998536b39e81ea1`. | Five first-envelope Gate 2 freeze/seal items checked; participant authentication, `Frozen`, qualification, promotion, product, and scores remain incomplete. |
