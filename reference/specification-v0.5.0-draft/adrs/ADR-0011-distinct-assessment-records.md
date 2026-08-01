# ADR-0011: Use distinct assessment record types

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

A generic Finding carrying demonstrated, conditional, unresolved, and informational badges would cause scientists to interpret unanswered questions and limitations as accusations. Severity on uncertain records amplifies that problem.

## Decision

Use four production assessment records: `Finding`, `ConditionalConcern`, `MaterialQuestion`, and `Disclosure`. A Finding is demonstrated by definition. Remove the public `supported` tier and user-facing numerical finding confidence. Reserve severity and publication materiality for Findings.

## Consequences

Counts, APIs, and report sections remain epistemically distinct. Migration from schema 0.1.0 is breaking. Renderers must not aggregate all assessment records as Findings.
