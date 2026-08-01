# ADR-0009: Separate evaluation candidates, Stage-3 equivalence, and clustered metrics

- **Status:** Accepted
- **Date:** 2026-07-28
- **Proposed schema release:** `0.10.0`
- **Related requirements:** SA-FR-023, SA-FR-085, SA-FR-097, SA-FR-101, SA-FR-102,
  AC-07, AC-09, AC-14, AC-15, AC-20, AC-43, AC-57–62, AC-64

## Context

Accepted ADR-0008 and public schema v0.9.0 freeze an answer-side scientific label before detector
output is visible and give each admitted positive one exact `AdjudicatedRootCause` identity. The
evaluation-private Stage-3 experiment can then bind one exact AuditBundle and enumerate its
DetectorResults and Findings. It deliberately cannot decide whether a detector's statement names
the same scientific root cause, whether its wording is stronger than the adjudicated defect, or
whether an unmatched in-scope statement is a false localization.

Two additional gaps make the current path circular:

1. an experimental detector is forbidden from emitting a production Finding or a public
   `finding_candidate`, but qualification needs to measure the Finding it would request if its
   maturity gate were satisfied; and
2. public `DetectorQualification.quantitative_metrics` is open-ended, so its contents cannot
   establish a reproducible denominator, cluster-aware interval, or promotion safety gate.

Giving an experimental detector provisional `validated` maturity would defeat the maturity gate.
Treating issue-class or source-reference overlap as semantic root-cause equivalence would also be
unsound. Text similarity, model confidence, and a single post-hoc reviewer are not acceptable
substitutes.

## Decision

Publish schema v0.10.0 from immutable v0.9.0 and create a qualification-only path with four closed
public records. The release is part of the architecture overhaul and creates no compatibility
requirement for the legacy public GitHub repository.

### 1. Qualification-only detector candidate

Add `DetectorEvaluationCandidate`. It records the exact Finding-shaped candidate that a detector
would submit to the ordinary admission service if the detector-maturity gate were ignored. It
contains:

- a stable candidate ID derived from the semantic-lock digest, detector ID/version/manifest
  digest, exact detector-result input, candidate statement, issue class, asserted root reference,
  affected records, evidence, and every non-maturity admission check;
- the exact source DetectorResult or evaluation-run reference and the immutable input AuditBundle
  digest;
- the proposed bounded statement, issue class, root locator, affected records, and evidence;
- the completed direct-entailment, no-reversing-unknown, applicability, counterevidence,
  bounded-wording, deterministic-replay, and source-resolution checks;
- `maturity_gate_bypassed_for_evaluation: true`;
- `production_admission_permitted: false`; and
- explicit non-inferences stating that it is not a Finding and cannot appear as one in a production
  report.

The production detector and ordinary admission logic remain unchanged. The evaluation package may
call the same deterministic detector and admission-check primitives, but the production package
must not import evaluation code. A failed non-maturity admission check cannot become an evaluation
Finding candidate; it remains a separately counted detector state.

This record removes the qualification circularity without granting an experimental detector
Finding authority.

### 2. Fresh Stage-3 comparison reviews

Add `Stage3ComparisonReview`. A Stage-3 packet is created only after the scientific-label freeze
and binds the exact fixture, adjudication, adjudicated roots, label-freeze digest, detector
candidate set, AuditBundle digest, detector identity, and declared scope. The minimum semantic
comparison panel is two fresh contexts, one from each provider family represented in scientific
adjudication. No Stage-1 or Stage-2 execution context may be reused.

Each reviewer must account for every admitted answer-side root and every in-scope evaluation
candidate. For each proposed candidate/root pair it records exact identifiers and separately
answers:

- whether both describe the same first material scientific divergence;
- whether the candidate statement is no stronger than the adjudicated bounded statement and its
  explicit stronger-claim exclusions;
- whether the issue class agrees;
- whether the asserted affected records stay within the adjudicated affected scope;
- which exact frozen evidence supports or defeats the mapping; and
- whether any material ambiguity remains.

The review also classifies candidates that have no proposed root mapping as in scope, out of scope,
or unresolved. Confidence may be retained as research metadata but has no identity, equivalence,
or metric authority.

### 3. Deterministic case reconciliation

Add `DetectorCaseOutcome`. The evaluator admits it only when the two provider families produce
identical closed candidate-to-root mappings and identical boundedness and scope decisions. It
recomputes every candidate identity, resolves every typed reference, validates the scientific
freeze and chronology, and verifies that all roots and candidates were accounted for. Majority
vote, prose similarity, embeddings, and an LLM tie-breaker are forbidden. Any material
disagreement or missing evidence makes the case `comparison_excluded` and metric-ineligible.

For an admitted positive case, each adjudicated root has exactly one of:

- `boundedly_localized`: at least one evaluation candidate maps to that root and stays within its
  statement and affected scope;
- `localized_but_overstated`: the first divergence matches but the candidate wording or affected
  scope exceeds the root;
- `missed`: no evaluation candidate maps to the root; or
- `unresolved`: the case is excluded from metrics.

Each in-scope evaluation candidate has exactly one of:

- `bounded_root_match`;
- `overstated_root_match`;
- `false_root_localization`; or
- `unresolved`.

A candidate cannot map to more than one root. Multiple bounded candidates may map to one root, but
they count as one recalled root. On a `verified_good_fixture`, `scope_verified_good`, or
`hard_negative_fixture`, every Finding-shaped candidate inside the exact completed declared scope
is a false accusation; no positive root is invented. Out-of-scope and mixed-detector candidates
are disclosed and excluded, never silently counted as correct or incorrect.

The existing `BenchmarkAdjudication.stage3_detector_comparison_refs` remains empty in newly frozen
adjudications. Stage 3 links forward to the immutable adjudication and freeze; it never mutates the
pre-detector scientific record or changes its digest.

### 4. Typed clustered metric evidence

Add `QualificationMetricSet`. It consumes only admitted, digest-verified
`DetectorCaseOutcome` records for one exact detector ID/version/manifest and one declared
qualification envelope. It stores the input outcome refs and digests, exact problem-cluster IDs,
all exclusions, and integer numerators and denominators before any ratio.

The first profile, `root-cause-clustered-metrics-v1`, reports at minimum:

- workflow-level probability of any false or overstated Finding-shaped candidate;
- detector-opportunity false-positive rate, separately for all completed opportunities and for
  applicable covered opportunities;
- Finding-candidate precision, with overstated candidates excluded from the numerator;
- false-root-localization and overstatement rates;
- recall of adjudicated roots, where duplicates cannot inflate recall;
- bounded root-localization accuracy;
- abstention, unsupported, detector-error, and unresolved-comparison rates; and
- exact case, workflow, opportunity, candidate, root, and problem-cluster counts.

Point estimates are ratios of the stored integer counts. Uncertainty uses deterministic
problem-cluster resampling, never workflow-row resampling: 10,000 bootstrap replicates, 95 percent
percentile intervals, and a SHA-256 counter stream derived from the canonical metric-input digest.
All stochastic siblings for one `problem_id` move together. The record reports invalid-replicate
counts and marks an interval `not_estimable` when fewer than two nonempty problem clusters or fewer
than two valid replicate estimates exist. Fewer than twenty problem clusters adds an explicit
small-cluster limitation. Workflow-level and detector-opportunity-level denominators remain
separate.

This interval profile is a reproducibility decision, not a detector-promotion threshold.

### 5. Promotion remains closed

Schema v0.10.0 makes a `DetectorQualification` promotion invalid while its numeric-threshold policy
is `deferred_until_pilot_threshold_adr`. A typed metric set can therefore exercise the entire
calculation and public-report path without promoting a detector. The first validated promotion
still requires:

- the later pilot-informed threshold ADR;
- held-out, problem-cluster-separated eligible cases rather than public development fixtures;
- verified-good, hard-negative, positive, unsupported, ambiguous, and decisive-counterevidence
  coverage;
- all non-negotiable safety gates;
- maintainer approval and a public qualification report; and
- publication-grade independent-corpus evidence when that maturity is requested.

Capability-matrix generation may cite an experimental metric set as evaluation evidence, but it
must retain `experimental`, `not_qualified`, and a strongest output no stronger than
`conditional_concern` until a valid promoted qualification exists.

## Migration from v0.9.0

- Existing public AuditBundles receive empty arrays for the four new record types.
- Existing evaluation-private Stage-3 observations do not become equivalence reviews, case
  outcomes, or metric evidence.
- Existing `BenchmarkAdjudication.stage3_detector_comparison_refs` values are preserved only as
  explicitly legacy opaque references and cleared from the authoritative forward-link field; no
  frozen adjudication is rewritten into a scored case.
- Open-ended v0.9.0 `DetectorQualification.quantitative_metrics` objects cannot become typed metric
  sets. A promoted legacy qualification migrates fail-closed to a non-promoted/deferred state while
  retaining its prior status and payload in namespaced migration metadata.
- No migration creates a detector/root equivalence decision, false-positive classification,
  interval, capability claim, or maturity promotion.

## Alternatives

### Compare issue class and source identifiers deterministically

Rejected because equal labels and overlapping locations do not establish the same first material
scientific divergence or bounded wording.

### Let the detector emit the adjudicated root ID

Rejected because the detector must remain blind to answer-side labels and could trivially game the
metric.

### Temporarily mark the detector validated so it can emit Findings

Rejected because qualification would then depend on the authority it is supposed to establish.

### Use one Stage-3 reviewer or a majority vote

Rejected because semantic equivalence can change precision and recall materially. One model or a
vote cannot override cross-provider disagreement.

### Compute metrics directly from Findings and fixture labels

Rejected because it conflates duplicate symptoms with root-cause recall, treats overstatement as a
correct match, and cannot distinguish abstention, unsupported scope, and negative coverage.

### Set promotion thresholds now

Rejected because the normative specification defers universal cutoffs until pilot-corpus evidence
exists. The schema must keep promotion closed while that decision is deferred.

## Acceptance evidence required

1. Schema examples and negative invariants for all four records, forward-only chronology, and
   fail-closed qualification promotion.
2. An experimental detector can produce a stable evaluation candidate while remaining unable to
   emit a production Finding.
3. Stage-3 packets are created only after label freeze, reveal detector output only then, and use
   fresh cross-provider contexts.
4. Exact cross-provider mapping agreement creates a stable case outcome; disagreement, confidence,
   prose similarity, missing roots, missing candidates, mixed attribution, or unresolved evidence
   makes it metric-ineligible.
5. Positive, verified-good, hard-negative, ambiguous, abstaining, unsupported, and detector-error
   cases receive the declared disjoint outcomes without inventing Findings or roots.
6. Duplicate candidate manifestations cannot inflate root recall, and one candidate cannot claim
   multiple roots.
7. Metric numerators and denominators recompute exactly from case outcomes; problem siblings stay
   together in deterministic cluster bootstrap samples; byte-identical replay holds across the
   supported Python versions.
8. Small or zero denominators and insufficient clusters produce explicit `not_estimable` values,
   never fabricated zeroes or perfect scores.
9. Public development cases, excluded comparisons, and legacy v0.9 observations cannot contribute
   to promotion evidence.
10. Canonical JSONL, disposable SQLite, AuditBundle validation, report rendering, wheel isolation,
    and model-free replay preserve every new record and reference.
11. A fail-closed v0.9-to-v0.10 migration invents no equivalence, metric, interval, or maturity.
12. No model call or project-authored execution occurs in deterministic reconciliation, metric
    calculation, or replay.

## Consequences

- K06 can classify exact detector/root outcomes and calculate reproducible clustered metrics
  without granting premature Finding authority.
- Public schema version becomes v0.10.0; accepted v0.9.0 and earlier packages remain immutable.
- Stage 3 introduces a second cross-provider semantic panel, increasing qualification cost but
  localizing the only non-deterministic equivalence judgment.
- Metric calculation becomes deterministic once comparison reviews are frozen, while the
  threshold needed for validated maturity remains deliberately unresolved.
- Real reviewer calibration, real held-out corpus evidence, public reports, RO-Crate export, and a
  pilot-informed promotion threshold remain external or later implementation gates.

## Acceptance record

Accepted by the repository owner on 2026-07-28 as proposed, including schema v0.10.0. Accepted
v0.9.0 and earlier schema packages remain immutable.
