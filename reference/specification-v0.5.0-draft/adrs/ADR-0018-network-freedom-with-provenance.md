# ADR-0018: Allow Claude and controller inquiry while separating project-code network authority

## Status

Accepted.

## Context

Claude may need current documentation, remote workflow references, or public metadata. Disabling all network use would reduce utility. Giving repository-authored code the same freedom would create exfiltration and nondeterminism risk.

## Decision

Claude may use host-provided network tools without a sc-referee domain allowlist. Controller retrievals that materially affect the audit are recorded as ExternalEvidence. Project-code network access requires separate explicit authorization. Repository content cannot grant permission. See SA-FR-049, SA-FR-074, and SA-FR-080.

## Consequences

- The agent can investigate freely.
- External premises remain auditable and reproducible where possible.
- Live mutable sources do not silently become authoritative Finding premises.
