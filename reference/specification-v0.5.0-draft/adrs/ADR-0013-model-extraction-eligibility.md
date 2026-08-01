# ADR-0013: Allow only verified explicit model extraction as Finding evidence

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

Requiring scientist confirmation for every literal report extraction would be burdensome, but allowing model confidence to establish undocumented scientific meaning would be unsafe.

## Decision

A model-derived assertion may support a Finding only when it extracts explicit meaning from an exact source span, is independently checkable, and passes a non-model verification. Implicit scientific inference requires authoritative corroboration.

## Consequences

Literal claim wording can be processed efficiently. Variable roles, biological units, causal roles, timing rules, and scientific invariants remain unresolved until corroborated.
