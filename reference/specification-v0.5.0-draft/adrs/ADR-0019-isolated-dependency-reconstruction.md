# ADR-0019: Permit automatic isolated dependency reconstruction in standard mode

## Status

Accepted.

## Context

Static parsing and bounded verification sometimes require project dependencies. A blanket prohibition would reduce usefulness, but installing into the user's environment or guessing packages is unsafe and scientifically misleading.

## Decision

Standard mode may install declared project dependencies only into an isolated audit-owned environment. It does not mutate the user environment, use sudo, install system packages, or install the local project automatically. Unpinned resolution is approximate. See SA-FR-075 and SA-FR-081.

## Consequences

- More workflows can be inspected without manual setup.
- Installation latency counts against the deadline.
- Exact version-dependent conclusions require pinned or independently verified behavior.
