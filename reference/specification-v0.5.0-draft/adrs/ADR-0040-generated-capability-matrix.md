# ADR-0040: Publish a generated multidimensional capability matrix

## Status

Accepted.

## Context

A domain-level “supported” checkmark conflates syntax parsing, operation extraction, semantic modeling, detector availability, qualification, version coverage, and abstention.

## Decision

Public capability claims are generated from manifests into narrow entries covering language, package, version, operation, semantics, detectors, maturity, review basis, output ceiling, gaps, and abstention conditions. Domain-wide support or validation is never inferred from one component. See SA-FR-100 and SA-FR-103.

## Consequences

- Public documentation stays aligned with implementation.
- Scientists can interpret negative results in their actual coverage envelope.
