# ADR-0024: Adopt the sc-referee public identity while retaining /scientific-audit

## Status

Accepted.

## Context

The original hackathon prototype already established the sc-referee identity. A descriptive user command need not equal the distribution name.

## Decision

The project, repository, primary distribution, and CLI use `sc-referee`; Python imports use `sc_referee`; the Claude action remains `/scientific-audit`. See SA-FR-001 and SA-FR-082.

## Consequences

- Continuity with the original prototype is preserved.
- The command remains legible to scientists.
- Package and command identities are intentionally decoupled.
