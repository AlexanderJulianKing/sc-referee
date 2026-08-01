# ADR-0028: Support Python 3.11 or newer

## Status

Accepted.

## Context

Scientific and HPC environments need broad compatibility, while Python 3.10 is approaching end of support.

## Decision

The first public implementation requires Python 3.11 or newer. Source-syntax parser coverage is reported separately from runtime support. See SA-FR-086.

## Consequences

- Compatibility remains broad.
- Newer-language features may require compatibility helpers.
