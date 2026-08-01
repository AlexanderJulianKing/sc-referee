# ADR-0031: Use Tree-sitter-R plus a non-evaluating base-R parser helper

## Status

Accepted.

## Context

R availability and syntax validity vary, while the language parser supplies valuable source-reference data.

## Decision

Use Tree-sitter-R for resilient inventory and an isolated helper calling `parse(keep.source = TRUE)` and `getParseData()` when R is available. Never source or evaluate project code. See SA-FR-089.

## Consequences

- R remains inspectable without a complete environment.
- Parser disagreement and dynamic semantics stay visible.
