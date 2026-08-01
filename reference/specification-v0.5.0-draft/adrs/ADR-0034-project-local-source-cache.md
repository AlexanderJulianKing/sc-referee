# ADR-0034: Keep source-derived caches project-local

## Status

Accepted.

## Context

Parse trees and semantic records can contain sensitive scientific structure even when raw source text is omitted.

## Decision

All source-derived caches remain project-local in version one. Global caches contain only tool-owned or public assets and isolated dependency environments. See SA-FR-092.

## Consequences

- Cross-project leakage risk is reduced.
- Some potential cache reuse is intentionally sacrificed.
