# ADR-0010: Represent maturity-blocked detector candidates without granting Finding authority

- **Status:** Accepted
- **Date:** 2026-07-28
- **Accepted schema release:** `0.11.0`
- **Related requirements:** ADR-0009 §1, SA-FR-023, SA-FR-085, AC-07, AC-14, AC-20, AC-43

## Context

Accepted ADR-0009 requires an experimental detector to produce a qualification-only
`DetectorEvaluationCandidate` representing the exact Finding-shaped candidate it would submit if
only the maturity gate were ignored. The accepted public v0.10.0 schema requires that record to
cite one exact source `DetectorResult` and its digest.

However, v0.10.0 permits `DetectorResult.state: finding_candidate` only when
`detector_maturity` is `validated` or `publication_grade`. Its other states mean no issue within
coverage, non-applicability, insufficient semantics, unsupported path, unavailable execution
evidence, detector error, or a different assessment type. None truthfully means “all non-maturity
Finding admission checks passed, but production admission is blocked because the detector is
experimental.”

Using `finding_candidate` with simulated validated maturity would recreate the circular
qualification that ADR-0009 forbids. Using another existing state would misstate the detector
observation. Removing the source-result binding would weaken replay and provenance. Accepted
v0.10.0 is immutable, so the mismatch requires a forward schema release.

## Decision

Publish schema v0.11.0 from immutable v0.10.0 with one additive, closed
`DetectorResult.state` value: `evaluation_finding_candidate`.

When that state is present, the schema requires:

- `detector_maturity: experimental`;
- a `candidate` with `assessment_type: finding`;
- a nonempty exact material-premise set and an empty unresolved-material-premise set; and
- the ordinary DetectorResult evidence, applicability, coverage, counterevidence, deterministic
  input digest, detector identity, and provenance fields.

The existing `finding_candidate` state remains restricted to `validated` and
`publication_grade`. The production admission service continues to recognize only
`finding_candidate`; it must always reject `evaluation_finding_candidate`. The isolated evaluation
package may project the latter into a `DetectorEvaluationCandidate` only after the same shared
deterministic non-maturity checks used by ordinary Finding admission pass.

The evaluation candidate remains the sole public record asserting that the maturity gate was
bypassed for measurement. The source DetectorResult records only the detector’s exact output
state; it is not a Finding and cannot appear in the production Findings array or report section.

## Migration from v0.10.0

- Existing records receive only the v0.11.0 schema namespace/version update.
- No existing DetectorResult is reclassified as `evaluation_finding_candidate`.
- No DetectorEvaluationCandidate, Finding, equivalence decision, metric, or qualification is
  created.
- StorageManifest records are cleared because migrated canonical bytes require a new manifest.

## Alternatives

### Simulate validated maturity during evaluation

Rejected because qualification would rely on the authority it is intended to establish and the
source record would make a false maturity claim.

### Reuse `insufficient_semantics`, `no_issue_detected_within_coverage`, or `detector_error`

Rejected because each state contradicts the demonstrated non-maturity admission checks and would
corrupt detector-state metrics.

### Put the untyped detector output only in extensions

Rejected because extensions cannot establish record meaning or durable replay, and the accepted
candidate schema requires an exact typed source DetectorResult.

### Remove the source DetectorResult requirement

Rejected because the candidate would lose the exact detector-state and input-digest binding needed
for deterministic replay and error/abstention accounting.

## Acceptance evidence required

1. v0.11.0 accepts an experimental `evaluation_finding_candidate` with a Finding-shaped candidate
   and rejects validated/publication-grade maturity for that state.
2. `finding_candidate` remains invalid for experimental detectors.
3. The production admission service rejects `evaluation_finding_candidate` even when every other
   check passes.
4. The evaluation projector admits the same record only when every shared non-maturity admission
   check passes and emits a stable `DetectorEvaluationCandidate`.
5. Failed applicability, coverage, premise, counterevidence, wording, source-resolution, or replay
   checks remain detector states and cannot become evaluation candidates.
6. A fail-closed v0.10-to-v0.11 migration invents no detector output, candidate, Finding,
   equivalence, metric, interval, or maturity.
7. Canonical JSONL, disposable SQLite, AuditBundle validation, report policy, wheel isolation, and
   model-free replay preserve the new state without granting production Finding authority.

## Consequences

- ADR-0009’s experimental-candidate path becomes implementable without semantic overloading.
- Public schema v0.10.0 and earlier remain immutable.
- Schema v0.11.0 is a narrow correction; it adds no detector, scientific domain, model call, or
  project-authored execution.

## Acceptance record

Accepted by the repository owner on 2026-07-28 as proposed, coordinated with ADR-0011 and public
schema v0.11.0. Public schema v0.10.0 and earlier remain immutable migration baselines.
