# ADR-0042: Fix promotion safety gates before numerical thresholds

## Status

Accepted, with numerical cutoffs deferred under OD-036.

## Context

Numerical thresholds selected before the corpus exists would be arbitrary, while purely discretionary promotion would be too weak for an accusation-sensitive tool.

## Decision

Non-negotiable safety gates cover high-severity false accusations, conditional-case exclusion, verified-good and hard-negative controls, decisive counterevidence, clustered uncertainty, held-out qualification cases, regression fixtures, disagreement exclusion, and public reports. Universal numeric cutoffs are set later through a pilot-informed ADR before the first validated promotion. See SA-FR-102.

## Consequences

- Qualification has enforceable protections now.
- Thresholds can reflect actual corpus dependence and diversity rather than invented precision.
