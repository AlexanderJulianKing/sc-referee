# ADR-0012: Prohibit open-ended language-model issue discovery in production

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

Open-ended requests to find unspecified scientific mistakes produce frequent false positives and may repeat the blind spots present when the same class of model authored the workflow.

## Decision

The production `/scientific-audit` path does not run a general LLM concern search. The model may perform bounded semantic extraction and verified literal source interpretation. Future issue classes surface through unknown semantics, unsupported operations, coverage gaps, scientist reports, benchmark analysis, and new validated deterministic detectors.

## Consequences

The product sacrifices speculative recall to protect precision. Research-only experiments must remain isolated outside production reports and counts.
