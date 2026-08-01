# ADR-0033: Require rootless OCI isolation for project-authored execution

## Status

Accepted.

## Context

A restricted subprocess is not an adequate security boundary for unfamiliar project code.

## Decision

Project-authored execution requires a capability-reported rootless OCI backend enforcing required controls. No unsafe fallback is offered. Auditor-owned verification may use a restricted subprocess. See SA-FR-091.

## Consequences

- Static audits remain available everywhere.
- Selected project execution is unavailable on unsupported hosts.
