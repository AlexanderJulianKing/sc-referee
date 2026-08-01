# ADR-0025: Use W3ID for immutable canonical schema identifiers

## Status

Accepted.

## Context

Schema identifiers may persist in publication-critical bundles longer than any single hosting arrangement.

## Decision

Versioned `$id` and `$ref` values use `https://w3id.org/sc-referee/schema/v<version>/...`. A `latest` path may aid browsing but is never persisted. See SA-FR-083.

## Consequences

- Published record identity is independent of repository hosting.
- The project must maintain the W3ID redirect configuration.
