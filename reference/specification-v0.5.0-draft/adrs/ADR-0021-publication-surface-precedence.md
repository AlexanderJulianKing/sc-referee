# ADR-0021: Resolve publication surface by explicit precedence and leave materiality unassessed when ambiguous

## Status

Accepted.

## Context

Repositories often contain multiple plausible final notebooks or manuscripts. Recency alone is unreliable, but asking in every unambiguous case is unnecessarily interruptive.

## Decision

Use explicit user or active-workspace selection, declared build target, explicit task or repository statement, and unique lineage evidence in that order. Filename and time only support ranking. When unresolved, candidate audits remain separate and publication materiality is unassessed. See SA-FR-004 and SA-FR-076.

## Consequences

- The system avoids auditing the wrong manuscript silently.
- A bounded issue may still be recorded inside a candidate surface.
- Headline counts and materiality cannot merge unresolved candidates.
