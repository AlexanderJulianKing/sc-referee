# Experiment 0019: Interactive post-hoc fixed-workspace validation

- **Status:** Active evaluation-private experiment
- **Date:** 2026-07-29
- **Governing decision:** Accepted ADR-0019
- **Public schema change:** None; accepted schema v0.14.0 remains unchanged
- **Production capability change:** None

## Purpose

Test whether a narrow scientist Answer can be bound to exact source evidence and compiled through
`posthoc_method_ledger_v1` after a scientific workflow already exists. The experiment reuses the
frozen QTL, CRISPRi/CasRx, pulse-admixture, and MVMR workspaces. It does not regenerate those
workflows, execute their code, treat a public answer-side report as production intent, or promote
an evaluation result into a Finding.

The repository owner approved these four evaluation-scoped Answers:

| Case | Scoped Answer |
|---|---|
| `multiparent_qtl_hmm_lmm` | `scale_and_orientation` must equal `repair_ril_founder_orientation_before_hmm_emission`. |
| `popgen_recent_pulse_sexbias` | `denominator_or_universe` must equal `full_chromosome_map_exposure`. |
| `statgen_cis_mvmr_winnerscurse_scaling_ldaware` | `measurement_model` must equal `ld_covariance_cholesky_whitening_before_robust_fit`. |
| `crispri_casrx_transcript_vs_locus` | Retain the governing method as unknown. |

The approval statement is bound by digest
`sha256:96cb535346861657f82f14fd1cafd91570a3f0ec7412e9895eead1be7d79bdb4`.
These Answers govern only this review set. They do not establish the workflow authors' historical
intent, execution, numeric causality, or a universally correct method.

## Implemented evaluation boundary

`source_method_probe.py` version `0.2.0` adds three fixed, Python-AST-only source profiles:

1. `ril_founder_orientation_before_emission_v1`;
2. `full_map_ancestry_exposure_v1`; and
3. `ld_covariance_before_robust_fit_v1`.

The profiles inspect one immutable regular Python file without import or execution. They are
evaluation-only, public-development-only, Finding-ineligible, metric-ineligible, and promotion-
ineligible. They are not production detectors and do not appear in the capability matrix.

`sc-referee-eval compile-posthoc-validation-review` then verifies the probe's canonical digest and
safety flags, binds one exact case-scoped human Answer, constructs the minimum controller inputs
needed by the existing ledger, and emits one write-once self-digested review. Structured Answers
must equal the selected profile's closed expected form and use an allowed existing
ScientificContract dimension/comparison binding. An unknown Answer must leave profile, dimension,
comparison form, and value unset; the compiler will not overload `measurement_model` or invent a
generic object to make the case appear covered.

The compiler independently marks every output as non-authoritative for production intent,
historical intent, execution, numeric causality, metrics, held-out status, promotion, and Findings.

## Fixed-workspace outcomes

| Case | Source probe | Review | Bounded outcome |
|---|---|---|---|
| `multiparent_qtl_hmm_lmm` | `evaluation-python-source-method-probe:86ecc18544bbb564baeb`; `sha256:6bea5cbad220168265fa7bfa8dc100c5512e11999994c6f2b481039592f8b4ba` | `evaluation-posthoc-validation-review:c499064e2968b9df56d5`; `sha256:7b53dce87ac693bf4906605175dea4b6ef576a99feb99ddb8966304fcb2b9af2` | `exact_conflict_candidate`: the source uses supplied founder alleles directly rather than the scientist-specified orientation-repair-before-emission form. |
| `popgen_recent_pulse_sexbias` | `evaluation-python-source-method-probe:defd6b0e437e1e97f4e2`; `sha256:a718059c4922d740f76b5f63227da8ef5125842ea2908e77f4f3682d369eee10` | `evaluation-posthoc-validation-review:0eea23bfbacdd448758f`; `sha256:a6c8b81bc052b2166355c15540803577e850b0043d9f2ed7054024d4164867ee` | `exact_conflict_candidate`: the source uses called high-confidence tract exposure rather than the scientist-specified full chromosome-map exposure. |
| `statgen_cis_mvmr_winnerscurse_scaling_ldaware` | `evaluation-python-source-method-probe:329c0c8f21531f31e326`; `sha256:19f534298b2e7f4de4e1362cbc276fccc24d2aec9ead5e2a486e7df0bd5b3cad` | `evaluation-posthoc-validation-review:845917588138a18b2546`; `sha256:41aa6cb8671d3bc6222e9bec6c0a25ea84e0006293425f662cf2ed460d1173b6` | `covered_negative`: the source constructs the LD covariance and Cholesky-whitens both design and outcome before the robust fit. |
| `crispri_casrx_transcript_vs_locus` | `evaluation-python-source-method-probe:898a94635c647bcbceb5`; `sha256:0ccfffa254ef9baddc1733b2eda14f8154c79cf03fd17e5e0ad94f697714307b` | `evaluation-posthoc-validation-review:f37ac3b01f3097df947f`; `sha256:1177e5b5c106815b4b1c061cd4db27618b897031fe2acc60449604befb5f314c` | `unresolved_obligation`: no profile, dimension, reported assertion, conflict, or Finding is manufactured. |

All four outputs record `project_code_executed: false`, `model_invoked: false`, and
`production_finding_eligible: false`. The two conflicts are exact incompatibilities with the
scientist-specified requirements for these reviews, not accusations of historical noncompliance
and not proof that either difference caused the numeric miss. The MVMR covered result demonstrates
that the comparator can recognize compatible source without demanding textual identity; it is not
a correctness certificate.

## Test and mutation evidence

- **Tests added:** `tests/test_posthoc_method_ledger.py`, the post-hoc cases in
  `tests/test_interaction_protocol.py`, `tests/test_evaluation_source_method_probe.py`, and
  `tests/test_evaluation_posthoc_review.py`.
- **Acceptance criteria satisfied:** the three comparison forms and their dimension bindings are
  closed; human Answers are scope-bound and controller-verified; exact conflict, covered, unknown,
  unsupported, duplicate, and not-applicable states are deterministic; the fixed QTL and
  population-genetics conflicts, MVMR covered control, and CRISPR unknown control compile without
  project execution or model calls; replay-equivalent compilation is stable.
- **Fail-closed coverage:** profile, task/case scope, Answer value, comparison form, dimension,
  source digest, model authority, finite operand, duplicate operand, missing/duplicate source
  assertion, write-once output, and unknown-overloading mutations are rejected or preserve an
  unresolved/unsupported state. A synthetic false-self-compliance control proves that a repository
  declaration claiming the required method neither establishes execution nor overrides a
  contradictory closed static source shape.

## Remaining coverage limitation

This experiment proves the ledger core and fixed source profiles. Accepted ADR-0020 subsequently
adds a normal raw-repository path for three exact report-derived method families, but it does not
generally infer domain-specific Claims, ScientificContract dimensions, or arbitrary method
operands. The original three AST profiles remain evaluation-only one-case adapters. The new QTL
static adapter is role/dataflow based, but without a typed source-to-selected-analysis join it can
only corroborate or suppress a report question and cannot become public evidence. An ordinary
audit outside the exact installed QTL, pulse-admixture, and MVMR report profiles therefore remains
unsupported; the CRISPRi/CasRx case still has no invented dimension.

Experiment 0020 has now completed ADR-0019's authorized fresh-context skill usability run. The
independent agent correctly invoked, interpreted, integrity-checked, and replayed the ordinary
audit without answer access or project execution, but the raw repository produced no Claim,
ScientificContract, method SemanticAssertion, or MaterialQuestion. The transport therefore passes
while the original scientist interaction path fails before the question boundary. Accepted revised
ADR-0020 implements the reusable remedy as a modular scientific-check registry with separate
method rules and language/tool adapters plus one shared analysis-scoped question path. QTL, pulse-
admixture, MVMR, and a removable conformance module use the same interface, not controller
branches or the definition of scientific scope. A fresh-context QTL follow-up now reaches one
exact scientist question, preserves zero Findings, and stops for the scientist's authority. Its
Answer/lock/replay transition now records repair-before-emission, compiles one exact review-scoped
incompatibility Disclosure, retains zero Findings, and replays deterministically without post-lock
model access. Outputs remain non-accusatory and Finding-ineligible; no production detector,
qualification, accuracy, or broad scientific-workflow support claim changes.
