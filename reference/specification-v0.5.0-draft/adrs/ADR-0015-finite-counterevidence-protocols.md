# ADR-0015: Require finite detector-specific counterevidence protocols

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

Searching every conceivable innocent explanation is unbounded, while a single `counterevidence_complete` Boolean is too vague to audit.

## Decision

Every Finding-capable detector declares a finite checklist of counterevidence checks, applicability, sources, treatment of unavailable evidence, and candidate effect. Completion means all applicable versioned checks were executed for the available evidence.

## Consequences

Admission is finite and testable. A decisive unavailable source forces abstention, a MaterialQuestion, a ConditionalConcern, or a Disclosure rather than a Finding.
