# ADR-0017: Separate execution privileges and prohibit interactive HPC submission in version one

## Status

Accepted.

## Context

Low expected runtime does not make project-authored code safe. Full bioinformatics workflows and HPC jobs are often incompatible with an interactive audit deadline.

## Decision

Automatic execution is limited to safe inspection and auditor-owned verification. Project-authored code requires explicit authorization and sandboxing. Version one does not submit HPC jobs or automatically run full workflows; it emits a ReproductionRequest. See SA-FR-048, SA-FR-072, and SA-FR-073.

## Consequences

- The auditor remains useful without becoming a general workflow-execution platform.
- Dynamic evidence may remain unavailable until imported.
- A later HPC adapter requires a separate security and lifecycle decision.
