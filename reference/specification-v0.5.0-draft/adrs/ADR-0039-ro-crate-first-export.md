# ADR-0039: Export RO-Crate 1.3 before W3C PROV

## Status

Accepted.

## Context

Publication packaging is immediately useful, while a complete formal mapping to W3C PROV would add semantic and maintenance work before a concrete consumer exists.

## Decision

Version one exports RO-Crate 1.3 containing native sc-referee records, the HTML report, identity manifests, environments, detector qualification references, execution evidence, licensing, and authorship. Native JSON/JSONL remains canonical. W3C PROV mapping is deferred until an identified interoperability need exists. See SA-FR-099.

## Consequences

- Audits can be archived as research objects early.
- Internal semantic distinctions are not prematurely flattened into another model.
