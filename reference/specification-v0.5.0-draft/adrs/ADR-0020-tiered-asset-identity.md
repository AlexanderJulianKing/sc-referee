# ADR-0020: Use tiered identity for data and artifacts

## Status

Accepted.

## Context

Full hashing of terabyte-scale inputs can consume the interactive deadline without improving every detector decision.

## Decision

Assets use full digest, immutable external, manifest, weak fingerprint, or unidentified identity. Identity limitations propagate only to conclusions for which exact identity is material. See SA-FR-050.

## Consequences

- Large and remote workflows remain auditable.
- End-to-end reproducibility claims remain bounded by identity strength.
- Reports must disclose weak identity without calling it a scientific defect.
