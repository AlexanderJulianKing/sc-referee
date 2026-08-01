# ADR-0004: Use a budgeted, claim-centric audit scope

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-002, SA-FR-004, SA-FR-005, SA-FR-006, SA-FR-051, SA-FR-052, SA-FR-053; SA-NFR-003, SA-NFR-004
- **Supersedes:** None

## Context

“Inspect the entire repository” can be interpreted as sending every file through deep model reasoning or executing an entire workflow. That would be slow, costly, and often scientifically wasteful. The auditor still needs to detect selective reporting and outcome-guided choices in relevant exploratory paths.

## Decision

The auditor MUST inventory the entire project. It MUST prioritize deep inspection of the final publication surface, backward lineage from final claims, and the selection envelope that could have influenced those claims. Work MUST be scheduled under explicit wall-clock, model, execution, and data-read budgets.

Budget exhaustion MUST produce a valid partial report with unprocessed work represented as coverage gaps. The default audit MUST NOT silently expand into an unbounded reproduction run.

## Consequences

### Positive

- Interactive audits can finish in minutes rather than hours.
- Effort is concentrated on scientifically material paths.
- Selective-analysis risks remain in scope through the selection envelope.

### Negative and trade-offs

- Some unrelated exploratory errors may remain uninspected.
- Publication-surface and selection-envelope inference can itself be ambiguous.

## Alternatives considered

### Exhaustive deep inspection of every file

Rejected as computationally unbounded and unlikely to improve material issue detection proportionally.

### Inspect only the final model file

Rejected because it misses upstream cohort construction and outcome-guided selection.

## Validation

Benchmarks MUST measure final-claim coverage, material-root-cause recall, wall time, model tokens, and honest partial-result behavior under forced budgets.
