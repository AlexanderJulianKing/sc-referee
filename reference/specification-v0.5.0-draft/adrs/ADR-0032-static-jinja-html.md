# ADR-0032: Render self-contained static HTML with Jinja2

## Status

Accepted.

## Context

The report must be deterministic, offline, safe against repository HTML, and readable without project execution.

## Decision

Use Jinja2 with explicit autoescaping and strict undefined variables. Embed required assets; JavaScript is optional enhancement only. See SA-FR-090.

## Consequences

- Reports are portable and rerenderable from records.
- Template wording remains centrally controlled.
