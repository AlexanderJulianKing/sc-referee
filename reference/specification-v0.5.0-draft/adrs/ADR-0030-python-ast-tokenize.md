# ADR-0030: Use CPython ast plus tokenize for Python extraction

## Status

Accepted.

## Context

The prototype is read-only and prioritizes valid scientific source over source rewriting.

## Decision

Use CPython `ast` for semantic extraction and `tokenize` for comments, literals, and boundaries. Do not import or execute project modules. Rejected syntax becomes explicit partial coverage. See SA-FR-088.

## Consequences

- The stack is lightweight and standard-library based.
- Error recovery and newer-than-runtime syntax are explicit limitations.
