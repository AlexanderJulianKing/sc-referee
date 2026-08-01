# Changelog

## 0.7.0

- Accepted ADR-0004 and added public WorkItem and Answer records.
- Added semantics-proposed, awaiting-answers, and semantics-resolved AuditRun states.
- Added required WorkItem and Answer arrays to AuditBundle and the public record union.
- Preserved v0.6.0 interaction history as empty arrays during migration.


## 0.6.0

- Accepted ADR-0002 and added public AuditRun, StageResult, FileRecord, Operation, Artifact, and
  ObservedResult records.
- Added typed graph edges and explicit epistemic states for observed-result semantics.
- Made the six corresponding AuditBundle arrays required and added all records to the public
  record union and schema catalog.
- Added fail-closed migration rules from provisional v0.1.0 records and immutable public v0.5.0
  bundles.
- Accepted ADR-0003 and added explicit unavailable publication-surface and coverage states without
  inventing an Artifact.


## 0.5.0

- Added cross-provider agent-review and benchmark-adjudication records, including Stage-2 falsification attempts and explicit provider participation.
- Added verified-good, scope-verified-good, and hard-negative fixture taxonomy.
- Added machine-generated capability matrix and RO-Crate 1.3 export records.
- Replaced mandatory human scientific approvals with explicitly disclosed agent-panel, mixed, or human qualification bases.
- Added non-negotiable promotion safety gates while deferring numeric thresholds to a pilot-corpus ADR.

## 0.4.0 — 2026-07-27

- Adopted the `sc-referee` project identity and W3ID schema namespace.
- Added tool identity, repository snapshot, parser, sandbox capability, cache policy and entry, storage manifest, performance, and detector qualification records.
- Extended AuditPlan with canonical storage, parser, snapshot, cache, sandbox, and report policy.
- Added tiered detector-promotion and immutable-live-workspace invariants.

## 0.3.0 — 2026-07-27

- Added runtime and execution control records.
- Adopted user-visible elapsed deadlines with quick 2/5, standard 8/10, and publication 25/30 minute cutoff/ceiling defaults.
- Removed auditor-imposed model-call and token caps from the default policy; host limits remain authoritative.
- Added network retrieval, isolated environment reconstruction, data identity, publication surface, reproduction request, and causal contract records.
- Allowed unresolved publication scope to leave Finding publication materiality unassessed.

## 0.2.0 — 2026-07-27

- Reserved Finding for demonstrated issues and separated conditional concerns, material questions, and disclosures.
- Added conservative admission, disposition, and adjudication records.
