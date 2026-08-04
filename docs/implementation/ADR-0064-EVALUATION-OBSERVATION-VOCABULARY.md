# ADR-0064: Evaluation-only detector-observation vocabulary

- **Status:** Accepted
- **Date:** 2026-08-03
- **Scope:** Evaluation-private prospective qualification artifacts only
- **Production Finding impact:** None

## Context

The prospective qualification outcome ledger originally encoded detector observations as
`finding`, `no_finding`, or `unavailable`. The detector frozen for the ten-envelope study is
experimental and explicitly forbidden from emitting a production Finding. Recording its
evaluation candidate as a `finding` would collapse the distinction the study exists to protect.

## Decision

Replace the evaluation-private observation vocabulary with the detector's exact terminal states:

- `evaluation_finding_candidate` for a positive experimental candidate;
- `no_issue_detected_within_coverage` for an applicable, covered negative result;
- `insufficient_semantics` when exact required semantics are unresolved;
- `unsupported_path` when the governed relation is outside the supported static path; and
- `unavailable` when no detector result can be retained.

The first four values replay the frozen detector-result vocabulary without a lossy study-only
translation. These values describe detector behavior only. They are not scientific labels,
Findings, promotion decisions, or evidence that qualification succeeded. Exact detector output
remains retained by content digest in the outcome artifacts.

## Consequences

Prospective metrics can distinguish positive candidates, covered negatives, unresolved semantics,
and unsupported paths without granting production meaning. Any future projection from a qualified,
binding-scoped candidate to a Finding remains a separate maintainer-controlled action under the
forward promotion schema.
