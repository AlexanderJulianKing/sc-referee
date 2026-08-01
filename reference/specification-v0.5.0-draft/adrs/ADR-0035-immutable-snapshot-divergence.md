# ADR-0035: Continue against the immutable initial snapshot after live edits

## Status

Accepted.

## Context

Aborting on every autosave is disruptive, while following live files would mix incompatible evidence.

## Decision

Each run stays bound to its initial immutable snapshot. Live edits set `workspace_diverged` and may trigger a linked follow-up run; they never enter the current run. See SA-FR-093.

## Consequences

- One run remains internally coherent.
- Scientists may continue editing without corrupting the audit.
