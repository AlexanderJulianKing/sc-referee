# ADR-0008: Use static-first inspection and sandboxed selected reproduction

- **Status:** Accepted for this draft
- **Date:** 2026-07-27
- **Related requirements:** SA-FR-047, SA-FR-048, SA-FR-049; SA-NFR-007, SA-NFR-008
- **Supersedes:** None

## Context

Scientific repositories may contain expensive workflows, destructive commands, malicious content, unsafe serialized objects, or dependencies unavailable outside an HPC environment. Execution is sometimes useful for verifying lineage but cannot be trusted by default.

## Decision

Static inspection MUST be the default. The controller MAY perform bounded metadata inspection and selected reproduction only under an explicit policy and sandbox. Project content MUST be treated as untrusted data, not instructions. Selected commands MUST have resource limits, logged inputs and outputs, restricted write scope, and network behavior recorded. Full workflow execution MUST NOT occur by default.

## Consequences

### Positive

- Audits remain safer, faster, and more reproducible.
- HPC workflows can still be assessed through definitions, manifests, and imported traces.
- Execution evidence becomes additive rather than a hidden prerequisite.

### Negative and trade-offs

- Static analysis will leave some dynamic semantics opaque.
- Sandbox behavior may differ across platforms.

## Alternatives considered

### Import and execute project code during discovery

Rejected because import-time behavior is unsafe and can alter the environment or data.

### Never execute anything

Rejected because low-cost reproduction can materially verify claims and lineage.

## Validation

Security tests MUST show that source comments, notebook text, symlinks, unsafe serialization, and subprocesses cannot alter audit policy or write outside the permitted output area.
