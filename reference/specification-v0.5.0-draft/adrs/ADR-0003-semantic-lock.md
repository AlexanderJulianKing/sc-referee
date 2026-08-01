# ADR-0003: Use a content-addressed semantic lock for deterministic reruns

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-045, SA-FR-046; SA-NFR-002, SA-NFR-010, SA-NFR-015
- **Supersedes:** None

## Context

The audit must be reproducible without Claude after scientific meanings have been established. Model behavior and prompts can change, and interactive answers may arrive over multiple sessions.

## Decision

The controller MUST create a validated semantic lock containing normalized contracts, assertions, answers, conflicts, unknowns, source identities, extractor versions, and prompt or model provenance where relevant. The lock MUST be content-addressed. Detector execution, grouping, coverage calculation, and report rendering MUST be rerunnable from the snapshot and lock without a language model.

A lock MUST be invalidated when a material source, answer, schema, or extraction dependency changes.

## Consequences

### Positive

- Findings are replayable and diffable.
- Publication artifacts can refer to an immutable audit state.
- Model upgrades can be evaluated without rewriting prior results.

### Negative and trade-offs

- Lock construction and invalidation rules add engineering complexity.
- Some source changes will require semantic re-resolution.

## Alternatives considered

### Persist only the final report

Rejected because it is not sufficient to reproduce detector decisions or coverage.

### Persist model transcripts as the canonical state

Rejected because transcripts are not typed, stable, or deterministic input to the audit kernel.

## Validation

A replay test MUST produce byte-equivalent normalized detector and coverage outputs from the same lock, aside from explicitly non-semantic rendering timestamps.
