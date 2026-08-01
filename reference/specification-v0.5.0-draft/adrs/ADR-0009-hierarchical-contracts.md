# ADR-0009: Author scientific contracts hierarchically and lock them flat

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-017, SA-FR-018, SA-FR-022, SA-FR-045; SA-NFR-002
- **Supersedes:** None

## Context

Many claims share the same study population, unit of analysis, assay, and broad adjustment policy. Re-inferring every dimension for every claim would be slow, repetitive, and inconsistent. Detectors nevertheless need a complete contract at the claim or analysis target.

## Decision

Scientific Contracts MUST support inheritance from study, cohort, analysis, and claim layers. Overrides MUST be explicit and provenance-bearing. At semantic-lock time, the controller MUST materialize a complete normalized contract for every detector target, preserving the source layer of each value.

## Consequences

### Positive

- Shared semantics are entered once.
- Model and scientist questions are reduced.
- Detectors receive deterministic complete records.

### Negative and trade-offs

- Inheritance and invalidation rules require care.
- An incorrect high-level assertion can affect many claims, so provenance and impact views are essential.

## Alternatives considered

### Independent full contract per claim

Rejected because it is expensive and invites inconsistent duplication.

### Implicit inheritance without materialization

Rejected because detector behavior would depend on runtime resolution and be harder to reproduce.

## Validation

Tests MUST cover override precedence, conflict preservation, inherited unknowns, source provenance, and deterministic flattening.
