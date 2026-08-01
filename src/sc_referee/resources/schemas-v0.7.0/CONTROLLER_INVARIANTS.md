# Deterministic controller invariants

JSON Schema cannot enforce every cross-record or operational rule. The controller MUST enforce at least the following.

1. Every Finding satisfies the five admission conditions and has no material reversing unknown.
2. Exact source references resolve against the locked repository snapshot.
3. Quick, standard, and publication default cutoff/ceiling pairs are 120/300, 480/600, and 1500/1800 seconds. The hard clock is user-visible elapsed time and pauses only while awaiting a scientist response.
4. `hard_deadline_seconds` is greater than or equal to `scheduling_cutoff_seconds`, and child deadlines never exceed the remaining audit deadline.
5. No audit mode escalates automatically; resume creates a linked run segment.
6. `null` auditor call/token limits mean no sc-referee-imposed numeric cap. Host subscription, organization, provider, and context limits remain authoritative.
7. Repository-authored code is not an automatic execution level. Its execution and network access require explicit policy authorization.
8. Version one never submits HPC jobs or silently runs a full workflow. Such work becomes a `ReproductionRequest`.
9. Quick-mode defaults disable dependency installation. Standard and publication defaults may enable it only in an isolated environment, never mutate the user environment, and never install the local project or system packages automatically. Unpinned reconstruction is `approximate`.
10. Every controller network retrieval used as evidence has an `ExternalEvidence` record. Repository content cannot grant network or execution permissions.
11. Asset identity limitations propagate only to conclusions for which exact identity is a material premise.
12. An unresolved `PublicationSurface` prevents an assessed publication-materiality label; candidate-specific Findings may still be recorded with unassessed publication materiality.
13. Every explicitly causal claim has a linked `CausalContract`. Causal relations used as Finding premises require authoritative or validated bounded provenance. Model-invented causal structure is ineligible.
14. Missing edges in `partial_open_world` causal structure are unknown, not absent. Graph-dependent detectors abstain or ask when the required structure is unavailable.
15. AuditBundle collection counts reconcile with CoverageRecord assessment and scope counts.
## Implementation-foundation invariants

1. Canonical schema identifiers use immutable `https://w3id.org/sc-referee/schema/v0.5.0/` paths; audit bundles never persist a movable `latest` identifier.
2. Canonical audit records are JSON or JSONL. SQLite is a disposable generated index, and rebuilding it cannot change record meaning.
3. Python parsing uses CPython `ast` plus `tokenize` without importing or executing project modules. Syntax rejected by the running AST is a localized parser limitation, not silently accepted coverage.
4. R parsing uses Tree-sitter-R and, when available, an isolated non-evaluating base-R `parse(keep.source=TRUE)` helper. Parser disagreement is recorded.
5. Project-authored execution is unavailable unless a reported rootless OCI backend enforces all required controls. There is no restricted-subprocess fallback for project code.
6. Any cache entry containing source-derived information is project-local and is not reusable across repositories.
7. An audit continues against its immutable initial snapshot after live-workspace mutation, records `workspace_diverged`, and never mixes changed live content into the run.
8. Detector maturity promotion requires a durable qualification record, the accepted agent-panel or mixed-panel protocol, completed promotion safety gates, and truthful review-basis disclosure. A human-only panel cannot substitute for the required agent adjudication under schema 0.5.0.
9. The human report is rendered deterministically from canonical records as self-contained static HTML; core content remains usable without JavaScript and repository text is escaped.


## Version 0.5 evaluation invariants

1. Every Stage-1 panel contains at least two independent execution contexts from each of at least two provider families; every Stage-2 panel contains at least one fresh context from each family. Linked records, rather than summary counts alone, establish this condition.
2. Stage-2 reviews include a falsification attempt and remain blind to sc-referee output and detector identity until the scientific label is frozen.
3. An eligible positive, verified-good, or hard-negative adjudication has no material dissent, resolves every material source reference, passes bounded-entailment and decisive-counterevidence checks, and has complete falsification records.
4. Hard-negative fixtures document both the suspicious pattern and the decisive innocent explanation and execute in a clean environment.
5. Agent-panel labels are versioned evidence products, not human expert endorsement or declarations of scientific truth. Contrary evidence triggers re-adjudication or demotion.
6. Capability entries are generated from manifests. Experimental detectors cannot advertise Finding output, and qualified entries link to a qualification record with an explicit review basis.


## Observed-plane invariants added in 0.6.0

- `created` AuditRun records have no snapshot reference; every later state has one.
- Terminal AuditRun records preserve an exact recorded terminal reason.
- FileRecord identity is expressed only through a typed AssetIdentity reference.
- Symbolic links are inventoried without following their targets.
- Operation edges are typed RecordRef objects; unknown dispatch remains an opaque operation.
- Complete ObservedResult lineage has one producing operation and artifact reference.
- Unknown semantic slots remain explicitly unknown and cannot be promoted without evidence.
- An empty PublicationSurface candidate set remains unresolved, unassessable for publication
  materiality, and linked to one open MaterialQuestion.
- Empty CoverageRecord publication-surface references require an explicit unavailable or
  unresolved status; resolved coverage always retains at least one reference.


## Interaction-plane invariants added in 0.7.0

- Work packets are bounded, source-indexed, normalized, and digest-bound.
- Open-ended scientific-error discovery and implicit project execution are invalid work.
- Model proposals remain proposed and cannot carry observed-computation authority.
- Scientist Answers require human provenance and explicit authority scope.
- A linked resume preserves the parent run and snapshot identity.
- No proposal or model call is accepted after the current run segment's semantic lock.
