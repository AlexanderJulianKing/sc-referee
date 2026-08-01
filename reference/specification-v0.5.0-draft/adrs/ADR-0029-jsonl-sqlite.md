# ADR-0029: Use canonical JSON/JSONL with a generated SQLite index

## Status

Accepted.

## Context

Durable diffable records and fast local graph queries have different storage requirements.

## Decision

JSON and JSONL are canonical; safe YAML is allowed for editable answers and policy; SQLite is generated and disposable. See SA-FR-087.

## Consequences

- Audit meaning survives database deletion.
- Local graph traversal remains efficient without a database service.
