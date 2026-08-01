# Experiment 0001: Typed publication-surface answer and linked rerun

- **Status:** Superseded by accepted ADR-0004 and public schema v0.7.0
- **Date:** 2026-07-28
- **Scope:** Publication-surface selection only

## Purpose

Exercise the agent/controller interaction boundary before introducing a public `Answer` record.
The experiment lets a scientist select one already-inventoried publication candidate from an
integrity-verified unresolved audit. It then starts a new, linked audit against an identical
repository snapshot.

## Envelope

The Pydantic-validated envelope binds:

- protocol version and answer type;
- answer identifier and self-digest;
- source audit-run identifier, semantic-lock digest, and snapshot digest;
- exact MaterialQuestion identifier;
- selected repository-relative path and Artifact identifier;
- scientist actor identifier and `this_audit` authority scope; and
- recorded timestamp.

The new run may use the answer only when the new immutable snapshot digest matches the source
snapshot and the selected artifact identity is reproduced exactly. Its `AuditRun` records link the
source run as `parent_run_ref`; its semantic lock embeds the complete experimental input.

## Safety boundaries

- The command creates an answer only for an open publication-surface MaterialQuestion and an
  existing candidate Artifact.
- It cannot resolve ScientificContract dimensions, assert observed computation, admit a Finding,
  authorize project execution, or modify the completed source run.
- Actor identity is locally declared, not cryptographically authenticated. The CLI and skill must
  invoke it only after a direct scientist answer.
- The envelope is not placed in the public AuditBundle or record union. It remains experimental
  until an ADR defines Answer authority, signing/authentication, revocation, and migration.
- A repository change after the answer forces a new unresolved decision; the answer is rejected.

## Exit criteria

- Positive linked-rerun test with exact parent, question, snapshot, artifact, and lock binding.
- Negative tests for noncandidate selection, envelope tampering, and snapshot divergence.
- Model-free replay preserves the answer-bound selection.

## Disposition

The experiment satisfied its exit criteria and was removed from the runtime. Accepted ADR-0004
replaced it with public WorkItem and Answer records, exact-snapshot pre-lock resume segments, and
the `resume` → `work-queue` → `work-packet` → `submit-proposals` → `record-answer` →
`lock-semantics` protocol. This document is historical evidence only and is not a supported
interface.
