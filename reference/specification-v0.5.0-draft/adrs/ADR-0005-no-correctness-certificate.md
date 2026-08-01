# ADR-0005: Never present absence of findings as a correctness certificate

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-039, SA-FR-040, SA-FR-044; SA-NFR-001, SA-NFR-005
- **Supersedes:** None

## Context

The detector library will always have coverage boundaries, semantic unknowns, and unsupported operations. A green status or “passed” message could cause scientists to infer validation that the system cannot establish.

## Decision

The product MUST NOT issue a global correctness, validity, reproducibility, publication-readiness, or safety certificate. Every human report MUST pair finding counts with coverage, unresolved semantics, opaque boundaries, and uninspected work. A no-finding result MUST use bounded wording such as “No demonstrated contradictions were found in the inspected paths.”

## Consequences

### Positive

- The report does not encourage unsafe overreliance.
- Detector coverage remains visible even on verified-good workflows.
- Product claims remain compatible with future issue classes.

### Negative and trade-offs

- Users seeking a simple pass/fail result may find the output less convenient.
- The UI must communicate progress and value without a reassuring green badge.

## Alternatives considered

### Traffic-light global status

Rejected because it collapses findings and coverage into a misleading judgment.

## Validation

Snapshot tests MUST reject prohibited correctness language and require a coverage statement in every report summary.
