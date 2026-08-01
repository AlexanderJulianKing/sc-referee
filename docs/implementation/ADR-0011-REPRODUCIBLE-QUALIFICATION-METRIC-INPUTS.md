# ADR-0011: Preserve exact qualification opportunities and close metric formulas

- **Status:** Accepted
- **Date:** 2026-07-28
- **Coordinated accepted schema release:** `0.11.0`
- **Related requirements:** ADR-0009 §3–5, SA-FR-023, SA-FR-085, SA-FR-097,
  SA-FR-101, SA-FR-102, AC-57–62, AC-64

## Context

Accepted ADR-0009 and public schema v0.10.0 require a `QualificationMetricSet` to be exactly
recomputable from digest-verified `DetectorCaseOutcome` inputs. Implementation of deterministic
case reconciliation exposed two information losses:

1. `DetectorCaseOutcome.detector_run_outcome` retains only aggregate execution, applicability,
   and coverage states. When a case has more than one DetectorResult, it cannot distinguish or
   count `no_issue_detected_within_coverage`, `not_applicable`, `insufficient_semantics`,
   `unsupported_path`, `execution_evidence_unavailable`, and `detector_error`, nor can it determine
   which exact opportunity produced an evaluation candidate.
2. ADR-0009 names twelve metrics and a deterministic clustered bootstrap, but does not close every
   numerator, denominator, exclusion, counter-byte encoding, rejection rule, or percentile index.
   More than one plausible implementation would satisfy the prose while producing different
   public values.

Computing a convenient interpretation would invent durable metric meaning. Reading the source
AuditBundle during replay would also violate the requirement that the typed case outcomes are the
complete metric inputs.

The source AuditBundle is necessarily an external, prior input to a later evaluation bundle. Its
typed reference and digest cannot point to the containing evaluation bundle because adding the
evaluation records would change that bundle's digest. Evaluation admission therefore resolves the
external bundle before creating a case outcome; later storage and reports preserve, but do not
reinterpret, the external reference.

## Decision

Coordinate this correction with accepted ADR-0010 in public schema v0.11.0. Accepted v0.10.0 and
earlier packages remain immutable.

### 1. Preserve one exact projection per detector opportunity

Add required `metric_input_status` and `detector_result_outcomes` fields to
`DetectorCaseOutcome`.

Newly reconciled outcomes use `metric_input_status: complete`. Every DetectorResult for the exact
detector ID/version/manifest in the source AuditBundle contributes exactly one ordered projection
containing:

- its typed result reference and semantic digest;
- its closed state, including ADR-0010's accepted `evaluation_finding_candidate` state;
- its exact applicability and coverage status;
- the sorted evaluation-candidate references derived from that result; and
- an explicit `completed` or `detector_error` execution class derived only from the result state.

The case reconciler verifies the projection against the supplied digest-bound source AuditBundle,
requires every candidate to cite exactly one projected result, and includes the complete projection
in the stable case-outcome identity. One DetectorResult is one detector opportunity. Multiple
candidates sourced from one result never create extra opportunities.

`metric_input_status: legacy_source_projection_unavailable` permits an empty projection only for a
fail-closed v0.10 migration. Such an outcome retains its scientific comparison record but is
metric- and promotion-ineligible.

### 2. Close the selected corpus and exclusions

A metric-set input is one exact detector-case outcome selected for the declared detector identity,
qualification envelope, and corpus partitions. `case_outcome_inputs` contains every selected
outcome, including a comparison-excluded outcome needed for the unresolved-comparison diagnostic.
Every `excluded_case_outcomes` reference must be a subset of those inputs and states why it is
excluded from resolved performance denominators. No unlisted outcome contributes to a value.

For this profile:

- one case outcome is one workflow;
- one projected DetectorResult is one opportunity;
- a completed opportunity has execution class `completed`;
- an applicable-covered opportunity is completed with applicability `applicable` and coverage
  `covered`;
- a resolved in-scope candidate has status `bounded_root_match`, `overstated_root_match`, or
  `false_root_localization`; and
- a resolved adjudicated root has status `boundedly_localized`,
  `localized_but_overstated`, or `missed`.

Out-of-declared-scope, mixed-attribution, unresolved, comparison-excluded, and
`metric_input_status`-incomplete records do not enter resolved performance denominators. They remain
preserved and disclosed. The diagnostic opportunity-state rates below still count exact projected
states from comparison-excluded cases when the projection itself is complete.

### 3. Close all twelve point estimates

The profile `root-cause-clustered-metrics-v1` uses these exact ratios:

| Metric | Numerator | Denominator |
|---|---|---|
| workflow unsafe candidate probability | metric-eligible workflows with at least one false or overstated candidate | metric-eligible workflows |
| completed-opportunity false-positive rate | completed opportunities linked to at least one false or overstated candidate | completed opportunities in metric-eligible workflows |
| applicable-covered-opportunity false-positive rate | applicable-covered opportunities linked to at least one false or overstated candidate | applicable-covered opportunities in metric-eligible workflows |
| Finding-candidate precision | bounded root matches | all resolved in-scope candidates |
| false-root-localization rate | false root localizations | all resolved in-scope candidates |
| overstatement rate | overstated root matches | all resolved in-scope candidates |
| adjudicated-root recall | boundedly localized plus localized-but-overstated roots | all resolved adjudicated roots |
| bounded root-localization accuracy | boundedly localized roots | all localized roots, bounded or overstated |
| abstention rate | `insufficient_semantics` plus `execution_evidence_unavailable` opportunities | all complete-projection opportunities |
| unsupported rate | `unsupported_path` opportunities | all complete-projection opportunities |
| detector-error rate | `detector_error` opportunities | all complete-projection opportunities |
| unresolved-comparison rate | comparison-excluded workflows | all selected complete-projection workflows |

`not_applicable` is neither an error nor an abstention. `no_issue_detected_within_coverage` is a
completed negative decision. Conditional-concern, material-question, and disclosure candidates are
completed lower-authority outputs, not Finding candidates or abstentions. An opportunity-level
false-positive numerator counts an opportunity once even if several unsafe candidate manifestations
cite it.

The public integer counts are recomputed from the same closed status sets. A zero denominator gives
`estimate: null`, never zero or one. Otherwise the estimate is exactly numerator divided by
denominator. Metric order is the schema's declared twelve-name order.

### 4. Close deterministic problem-cluster resampling

The bootstrap input digest is the semantic digest of a domain-separated canonical JSON object
containing the metric profile, detector ID/version/manifest, qualification envelope, sorted corpus
partitions, and sorted case-outcome references plus digests.

For each of 10,000 replicates, sample exactly `N` problem-cluster IDs with replacement, where `N`
is the number of distinct input `problem_id` values. Draw position `j` in replicate `r` uses the
first accepted SHA-256 block over:

```text
UTF8("sc-referee-bootstrap-v1\0") ||
raw_32_byte_input_digest ||
uint64_be(r) || uint64_be(j) || uint64_be(retry)
```

Interpret the block as an unsigned big-endian 256-bit integer. For `N` clusters, reject values at
or above `2^256 - (2^256 mod N)` and select `value mod N`. Increment `retry` only after rejection.
All workflows and opportunities for a selected problem move together and are repeated with the
cluster's sample multiplicity.

A replicate whose metric denominator is zero is invalid for that metric. With at least two
nonempty input clusters and at least two valid estimates, sort exact rational replicate estimates
and use nearest-rank indices `ceil(valid/40)-1` and `ceil(39*valid/40)-1` for the 2.5th and 97.5th
percentiles. Otherwise the interval is `not_estimable` with null bounds. Fewer than twenty clusters
adds the required small-cluster limitation whether or not an interval is estimable.

### 5. Promotion stays closed

All v0.11 metric sets retain `promotion_permitted: false` and
`numeric_threshold_policy: deferred_until_pilot_threshold_adr`. Public-development input, any
metric-incomplete outcome, or any outcome whose own promotion-evidence flag is false forces the
metric set's `promotion_evidence_eligible` to false. A true evidence-eligibility flag still does not
promote a detector.

## Migration from v0.10.0

- A v0.10 DetectorCaseOutcome receives
  `metric_input_status: legacy_source_projection_unavailable`, an empty
  `detector_result_outcomes` array, and fail-closed metric/promotion eligibility. Its prior flags are
  retained in namespaced migration metadata; no result state or candidate-to-opportunity link is
  inferred.
- A v0.10 QualificationMetricSet cannot establish the newly closed formulas or counter stream. An
  AuditBundle migration clears it from the authoritative metric-set array and preserves its exact
  legacy payload only in namespaced migration metadata. Standalone migration reports it as
  non-authoritative legacy evidence rather than emitting a v0.11 metric set.
- No migration creates a DetectorResult state, evaluation candidate, opportunity projection,
  equivalence decision, estimate, interval, capability claim, or maturity promotion.
- StorageManifest records are cleared because canonical migrated bytes change.

## Alternatives

### Re-open the source AuditBundle during every metric replay

Rejected because the typed case outcome would not be the complete metric input and replay could
silently depend on missing or substituted external bytes.

### Treat aggregate applicability and coverage as exact opportunity counts

Rejected because aggregation loses multiplicity, joint applicability/coverage state, exact result
state, and candidate-to-opportunity attribution.

### Choose formulas in implementation code and document them afterward

Rejected because multiple reasonable ratios exist, especially for abstention and bounded
localization accuracy. Public metric meaning requires an accepted decision first.

### Use a seeded language-runtime random-number generator

Rejected because its algorithm and cross-version byte behavior are not the public protocol.

## Acceptance evidence required

1. Schema invariants require exact per-result projections for new complete outcomes and reject
   incomplete projections as metric-eligible.
2. Reconciliation verifies every projection and candidate/result link against the exact source
   AuditBundle and includes them in stable identity.
3. Positive, verified-good, hard-negative, no-issue, not-applicable, abstaining, unsupported,
   unavailable-execution, detector-error, and comparison-excluded cases recompute the declared
   disjoint counts.
4. Multiple results per workflow and multiple candidates per result cannot inflate workflow or
   opportunity numerators.
5. Every metric numerator, denominator, estimate, and public count is independently recomputed from
   the closed case-outcome inputs; mutation fails closed.
6. Problem siblings always move together, the counter stream matches fixed byte-vector examples,
   and 10,000-replicate output replays byte-for-byte on supported Python versions.
7. Zero denominators, zero/one cluster, fewer than two valid replicates, and fewer than twenty
   clusters produce the declared nulls and limitations.
8. Public-development, excluded, legacy-incomplete, and mixed-detector evidence cannot support
   promotion.
9. Canonical JSONL, disposable SQLite, AuditBundle validation, report rendering, wheel isolation,
   and model-free replay preserve the new projection and metric evidence.
10. No model call or project-authored execution occurs during projection, calculation, bootstrap,
    report generation, or replay.

## Consequences

- Qualification metrics become a deterministic compilation of complete typed case outcomes rather
  than an interpretation of aggregate state.
- DetectorCaseOutcome grows because it deliberately preserves the minimum opportunity projection
  needed for replay.
- Accepted v0.10.0 remains a valid immutable design milestone but cannot by itself produce an
  authoritative metric set.
- Numeric promotion thresholds, real corpus evidence, and reviewer calibration remain separate
  later gates.

## Acceptance record

Accepted by the repository owner on 2026-07-28 as proposed, coordinated with ADR-0010 and public
schema v0.11.0. Public schema v0.10.0 and earlier remain immutable migration baselines.
