# ADR-0007: Require executable detector coverage contracts

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-031, SA-FR-032, SA-FR-039, SA-FR-060; SA-NFR-014
- **Supersedes:** None

## Context

A detector cannot formally prove that it understands every future workflow. Nevertheless, the system must distinguish “ran and found nothing” from “not applicable,” “insufficient semantics,” and “unsupported path.”

## Decision

Every detector MUST declare a machine-readable manifest containing applicability, supported operation signatures and versions, required semantic fields, assumptions, abstention conditions, evidence ceiling, maturity, limitations, and positive, negative, ambiguous, and unsupported fixtures. The controller MUST calculate actual audit coverage from these declarations and observed targets.

## Consequences

### Positive

- Negative detector results have a bounded interpretation.
- Coverage gaps can be measured and regression-tested.
- Detector expansion does not require pretending to have universal support.

### Negative and trade-offs

- Detector authors must maintain manifests and fixtures.
- Coverage declarations may initially be conservative and reduce apparent recall.

## Alternatives considered

### Free-form detector documentation

Rejected because it cannot support deterministic applicability or coverage computation.

### Formal proof of semantic coverage

Rejected as impractical for dynamic scientific software and open-ended domains.

## Validation

The controller MUST emit distinct states for a covered negative result, inapplicability, missing semantics, unsupported operations, unavailable execution evidence, and detector error.
