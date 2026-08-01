# Experiment 0017: Targeted GeneBench recurrence pilot

- **Status:** Active evaluation-private experiment
- **Date:** 2026-07-29
- **Governing decisions:** Accepted ADR-0017 and ADR-0018
- **Corpus ceiling:** Public development; not held out, qualification eligible, or promotion eligible
- **Public schema change:** None; accepted schema v0.14.0 remains unchanged

## Purpose

Test whether any of Experiment 0016's four closed method-shape failures recur in three additional
scientific workflows. The experiment also tests whether the answer-isolation, semantic-lock,
no-post-lock-model, replay, and closed-grader boundaries continue to hold when the workflows and
answer contracts differ.

The experiment must not infer a production Finding from a grade, execute submitted source during
static inspection, expose answer-side material before lock, or broaden an existing profile merely
to make it fire on a new failure.

## Isolation and run protocol

The pinned GeneBench-Pro public package revision
`8bb6cde6ab0b0554e867c46f5698fd953bf2c68a` passed the existing full-package preflight as
`corpus-preflight:8730beb21ba287b04206`, digest
`sha256:cdec94825fc8801ddb6b8189ddc2595b033c6be09d83249e7d0a76ee70c6d37b`.
The existing preparer created three separate workspaces containing only derived `task.md` plus
declared data:

1. `statgen_scrna_ambient_state_eqtl`;
2. `structural_inversion_subhap_expression_risk`; and
3. `txr1_mtb_causal_sv`.

Three authorized fresh-context agents were each confined to one workspace and denied the package,
ground truth, grader, public reference report, sibling workspaces, network, and earlier run context.
Each agent authored and executed its own analysis. sc-referee then statically audited and locked the
workspace before any answer-side access. Every audit emitted zero Findings, verified no post-lock
model access, and replayed without project execution.

## Closed grader extension

The first grading attempt failed closed before comparison because two package-declared grader
shapes were not in the evaluation adapter. No grade was written. Version `0.3.0` adds only the exact
encountered forms:

- one `numeric_tolerance` field with config keys `answer_field`, `key`, and
  `absolute_tolerance`, where `answer_field` must be exactly `answer`; and
- one `composite` form whose nonempty `integer_keys` use exact JSON-integer equality plus declared
  minimum and optional maximum, and whose nonempty `numeric_keys` use finite absolute tolerance.
  The only optional outer flags are the pair `forbid_extra_keys` and `strict_answer_schema`, and
  both must be exactly true when present.

The adapter rejects JSON booleans and floats for integer fields, relative tolerances, numeric
bounds in this new composite form, one optional strictness flag without the other, unknown fields,
extra or missing answer keys, and any changed shape. It still does not import or execute the
package grader or submitted workflow. Grade records contain value digests rather than disclosed
ground-truth values and remain ineligible for Findings, labels, metrics, qualification, or
promotion.

## Frozen outcomes

| Case | Audit and semantic lock | Grade | Result |
|---|---|---|---|
| `statgen_scrna_ambient_state_eqtl` | `audit:95e8eb09f71642bda2aaae4a151707ea`; `sha256:1a710ba51a2e9d3be5932bb9da084db3e806dcc4c114708690e719e174934cd0` | `genebench-answer-grade:39cc5fcee4efc7244ada`; `sha256:2f709215bf02eea002137f7b1d952eb9500b1aa1d89aa46b8263cfe119d73030` | `beta_activated=-0.367833`; absolute error `0.232123` against tolerance `0.05`. |
| `structural_inversion_subhap_expression_risk` | `audit:52639cfa6264499e9d563a665ff11f50`; `sha256:8b0d40fdd6fa42275b6f472709307f987d8c757edb9467170293974c5070a565` | `genebench-answer-grade:378be85a770ebc5b5967`; `sha256:03f3776402239ecb632539c3ee6b0f29c68d8ba257f6475ec1e41eeb894b21b8` | Expression log fold-change and support code matched. Carrier count was `192` rather than `195`; clinical log-OR error was `0.075698` against tolerance `0.055`. |
| `txr1_mtb_causal_sv` | `audit:7fa4f843711c4a74a78fb26913b635f9`; `sha256:848ce78c4ea77af201ede1dce8aa6a5daae4c4f3ea62152ee6f9cf5252b7014c` | `genebench-answer-grade:647f1d5dd7f28767f26e`; `sha256:dccacf3092a567588e5ab033848de2a5d1274fe09c3792cace6f0b457a022a02` | Therapy code matched. Benefit, toxicity, and net-utility absolute errors were `6.4143`, `2.3689`, and `5.5252` percentage points against tolerances `0.5`, `1.0`, and `0.4`. |

These are answer-contract observations only. They do not independently establish scientific intent,
the executed method, or a root cause.

## Recurrence test

After semantic lock, the Experiment 0016 Python-AST probe applied all four existing profiles to
each unchanged `analysis.py`. All twelve case/profile combinations returned `unsupported_path`:

| Case | Source and diagnostic digests | Existing-profile result |
|---|---|---|
| `statgen_scrna_ambient_state_eqtl` | source `sha256:f586864539d3de45d766eec93bac4091e98d08dfea8d02e4bd8c4a889097aadb`; diagnostic `sha256:bf34e9aaa1c0aef489818770a372c3c222a25a31e161c6de6843a5fdb08c5549` | Four `unsupported_path` results. |
| `structural_inversion_subhap_expression_risk` | source `sha256:a28b02ce02f91b2f08bb2ccf8e9be6a3720be9b0c9e2ad69570514e43a1c9efa`; diagnostic `sha256:1aa6dedf96966c067b1a4e961dac0f466fdb82a52f366ab2a71d63826cf49a23` | Four `unsupported_path` results. |
| `txr1_mtb_causal_sv` | source `sha256:77e174b01ecc3e9fd5e25ddd6ec1f6addedb2122eec2774ae233b7dc2f86c89a`; diagnostic `sha256:b7947eb17292ba16045ed55d08ff1dde5840b82843383b73a3700a81173a658f` | Four `unsupported_path` results. |

Therefore the targeted pilot does **not** supply recurrence for directional measurement error,
phased-composite construction, mutually exclusive class calibration, or calibration-before-
standardization. Preserving `unsupported_path` is the correct result; expanding those grammars to
capture unrelated failures would invalidate their closed meanings.

## Answer-side method adjudication

The following comparisons use public-development reference reports only after lock. Those reports
do not establish production scientific intent.

### Ambient-state eQTL

The submitted source correctly performs target/marker ambient correction, state restriction,
donor pseudobulk, and an exposure offset, but its design matrix contains genotype, sex, age, and
BMI only. It never reconstructs the contamination-derived donor group from mean HBB contamination.
The reference report, digest
`sha256:1d18cbb9f63d288fc8ffb41a5901e0f1f97d06fcc63b25415e69dca0fa823e77`,
shows that the donor groups are separated in released data and that omitting this recovered group
gives `-0.366414`, closely reproducing the submitted `-0.367833`; including it with corrected
CXCL10 gives the released target near `-0.600`. This is strong fixed-case answer-side causal
evidence for an omitted recoverable technical-group adjustment, not a production Finding.

### Structural-inversion nested dosage

The submitted source uses visibly stricter long-read QC gates than the reference, retaining 476
calibration samples and 192 carriers rather than the reference's 483 and 195. It then trains
classifiers and writes integer `predict(...)` outputs as both nested and outer dosages. The
reference report, digest
`sha256:561c9cbec34e364a10d35efd92d0af9b6aac312defd3f2079d490f0c0fbc9f32`,
defines the visible reliability gap and requires ancestry-stratified continuous calibrated dosage;
several continuous regression variants are tolerance-equivalent, while hard calls estimate a
different exposure. The strict gates directly explain the carrier-count miss. The dosage-form
conflict is a credible explanation for the clinical miss, but this experiment did not run a
single-change evaluator-owned ablation against the submitted pipeline, so sole numeric causality
for the log-OR remains unestablished.

### TXR1 target-trial analysis

The submitted source computes a purity/copy-adjusted CCF proxy but never uses it in its target call.
Its long-read, distance, expression, ASE, and phase thresholds differ from the reference and produce
387 target patients rather than the requested recoverable target population of 354. Its assessment
model also includes observed week-8 toxicity, a post-treatment variable that the reference contract
explicitly excludes, and its selected imputation estimate omits the inverse-assessment factor used
by its own alternate estimator. The reference report, digest
`sha256:3c459331786b109d3dc1131f9f2a31fa37f460d75616b67c00d920a7c9a3156b`,
documents answer-changing target-reconstruction and no-assessment-weighting ablations. Because the
submission differs at several stages simultaneously, the pilot records a compound incompatibility
and does not claim that one isolated change would recover all three numeric fields.

## Acceptance evidence

- **Change:** evaluation grader version `0.3.0` adds only the exact single-numeric and
  integer/numeric composite contracts encountered after lock.
- **Tests:** `tests/test_evaluation_corpus.py` covers closed single-numeric success and malformed
  `answer_field`, exact integer/numeric composite success, one-sided integer minimums, bounded
  integer codes, JSON-float rejection for integer fields, false strictness flags, and unknown-field
  rejection while retaining the earlier numeric and string/numeric contracts.
- **Acceptance criterion satisfied:** all three frozen answers can be graded without workflow or
  package-grader execution; the four prior probes abstain on every unrelated source; exact
  answer-side method differences are localized without becoming Findings or production profiles.
- **Remaining coverage limitation:** the agents are unauthenticated public-development runners;
  the three new failure families each have one case; only the ambient omission has a near-exact
  reference ablation match; and no new profile has positive, verified-good, hard-negative,
  ambiguity, or independent recurrence evidence.

## Decision

Do not promote or broaden any Experiment 0016 profile. The attempted recurrence test was negative,
which is useful evidence that the closed probes do not simply fire on every wrong workflow. Retain
the three newly observed method families as candidates for future contract design only if another
case establishes recurrence or a human-authorized pre-analysis contract makes the obligation
explicit. Production schema v0.14.0, detector manifests, capability claims, Finding eligibility,
and qualification status remain unchanged.
