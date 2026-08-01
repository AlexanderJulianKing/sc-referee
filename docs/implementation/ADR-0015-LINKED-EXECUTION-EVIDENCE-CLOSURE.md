# ADR-0015: Bind clean controls to a closed linked-execution evidence record

- **Status:** Deferred by accepted ADR-0017
- **Date:** 2026-07-29
- **Former proposed coordinated schema release:** `0.15.0` (not scheduled)
- **Related requirements:** SA-FR-047–049, SA-FR-091, AC-28–32, AC-43, AC-49, AC-58–62

## Context

Accepted ADR-0013 and ADR-0014 now permit a narrowly bounded project-workflow attempt only after
an immutable source request, a qualifying rootless-OCI capability record, and fresh direct
single-use authorization. The v0.14 controller verifies and privately restages the exact source
snapshot, records every terminal attempt, publishes a linked semantic lock and AuditBundle, and
replays full-digest log and output bytes without model or runtime access.

That evidence is sufficient to inspect one attempt, but the immutable v0.14 BenchmarkFixture
contract cannot bind it as one closed clean-control premise. Its `proof_evidence.public_inputs`
can bind an Execution, Environment, and SandboxCapability, but not the exact:

- source WorkItem and source semantic-lock digest;
- ProjectExecutionAuthorization and private-consumption outcome;
- linked AuditRun and linked semantic-lock digest; or
- log/output Artifact and AssetIdentity record meanings.

The v0.14 Execution lists log and output record identifiers, but those identifiers alone do not
pin the semantic digests of records later supplied under the same IDs. A fixture could therefore
appear structurally complete while omitting or substituting a material dependency. Process success
and captured output bytes also do not establish scientific correctness.

This ADR assumes the capability itself has a trusted controller-observed origin. The separate gap
and correction are specified in proposed ADR-0016; both decisions coordinate on schema v0.15.0.

A second fail-closed issue exists in v0.14: `execution_kind: project_workflow` fixes the actor and
sandbox state but does not restrict `authorization_evidence_status` to `complete` or the explicit
legacy-unavailable state. The general enum therefore admits inconsistent imported/not-required
project-workflow combinations.

## Decision

Publish a forward-only schema v0.15.0 from immutable v0.14.0. Do not change any earlier accepted
schema package.

### 1. Add a closed `LinkedExecutionEvidence` record

Add a public `linked_execution_evidence` record and corresponding AuditBundle collection. One
record binds, by typed reference and semantic digest:

- the source AuditRun, source semantic lock, RepositorySnapshot, and project-execution WorkItem;
- the ProjectExecutionAuthorization, SandboxCapability, exact Environment, linked AuditRun, and
  project-workflow Execution;
- every controller-event, stdout, stderr, consumption, output-manifest, and accepted-output
  Artifact; and
- every AssetIdentity that establishes the exact bytes of those material artifacts.

The record also carries a fixed closure profile, the linked semantic-lock digest, a deterministic
sorted dependency inventory, a model-free replay profile, and a controller-derived eligibility
state with explicit ineligibility reasons. Its semantic digest pins the complete public dependency
closure. Private registry files remain private and inert; the record binds their public receipt
artifacts but does not recreate launch authority.

Eligibility is derived, never asserted by a model or copied from repository text. It requires a
completed execution, complete authorization evidence, a still-qualifying exact capability and
environment binding, all required resource observations, untruncated logs, successful cleanup,
an exact output manifest, complete full-digest identities, and successful model-free replay. It
does not imply scientific correctness, result validity, or Finding eligibility.

### 2. Make clean-control fixture proof depend on the closure

Extend `BenchmarkFixture.proof_evidence.public_inputs` with typed, digest-bound
`linked_execution_evidence` inputs. A clean control must bind exactly one eligible closure record
and its resolved dependency records. Loose Execution, Environment, or SandboxCapability records
cannot substitute for the closure. Fixture construction and report validation independently
recompute the closure and reject missing, extra, duplicate, ID-substituted, digest-drifted, or
ineligible dependencies.

Positive, hard-negative, and non-clean-control fixture classes retain their existing proof rules
and do not acquire project-execution requirements.

### 3. Tighten project-workflow Execution states

For `execution_kind: project_workflow`, allow only:

- `authorization_evidence_status: complete` with non-null complete project-execution evidence; or
- `legacy_authorization_projection_unavailable` with `project_execution: null`, explicit
  limitations, and no clean-control eligibility.

Reject `not_required` and `imported` project-workflow Executions. Auditor verification and imported
executions retain their existing non-project meanings.

### 4. Preserve output-record meaning

Represent execution logs, manifests, receipts, and accepted outputs as Artifact plus AssetIdentity
records. Do not create a FileRecord merely to satisfy the ADR-0014 allowed-output type list:
FileRecord is scoped to a RepositorySnapshot and would falsely imply that a newly produced output
already belonged to the immutable source snapshot. A later audit may create a FileRecord only by
capturing that output into a new RepositorySnapshot.

### 5. Migrate fail closed

The v0.14→v0.15 migration:

- creates no LinkedExecutionEvidence record from loose v0.14 IDs;
- preserves already consistent project-workflow Execution evidence but grants no closure or
  clean-control authority;
- rewrites inconsistent imported/not-required project-workflow projections to the explicit
  legacy-unavailable state with limitations and no project-execution payload;
- downgrades every legacy clean-control fixture whose complete closure cannot be reconstructed;
  and
- removes dependent outcomes, metrics, qualifications, and promotion authority using the existing
  fail-closed migration policy.

## Alternatives

### Add more loose arrays directly to `BenchmarkFixture`

Rejected because each consumer would have to rediscover the same cross-record closure and could
silently disagree about which artifacts, identities, locks, or receipts are material.

### Treat the linked semantic-lock digest alone as sufficient

Rejected because fixture validation and static reporting must resolve the exact public dependency
meanings without relying on an unavailable external directory or opaque lock bytes.

### Treat successful exit and output capture as a clean control

Rejected because process success is not scientific correctness and does not prove resource,
cleanup, authorization, identity, or replay premises.

## Acceptance evidence required

1. Schema and bundle tests accept one complete closure and reject a missing, extra, duplicated,
   wrong-type, wrong-ID, or semantic-digest-drifted dependency.
2. Compiler tests independently rederive eligibility and reject incomplete authorization,
   capability, environment, resource, cleanup, log, output, identity, or replay evidence.
3. Replay tests copy only exact full-digest bytes and prove that replay performs no model call,
   container launch, authorization reuse, or private-registry reconstruction.
4. Clean-control fixture construction and report validation require the same exact eligible
   closure and fail when any bound dependency or linked-lock digest changes.
5. Execution schema tests reject imported/not-required project-workflow states and preserve the
   two explicit complete/legacy branches.
6. v0.14→v0.15 migration invents no closure, authorization, execution, clean fixture, metric,
   qualification, or promotion authority.
7. Reports state that the record demonstrates only the bounded execution controls and observed
   bytes; it is never a Finding or scientific-correctness certificate.

## Consequences

- Existing v0.14 linked attempts remain inspectable and replayable but cannot qualify a clean
  control without new v0.15 closure evidence.
- Real launch also remains disabled until ADR-0016 replaces standalone capability-record admission
  with a trusted packaged probe identity and fresh controller observation.
- The actual Podman adapter has bounded direct resource observation on local Linux cgroup v2;
  remote Podman-machine cgroups remain unavailable, and no live observation has yet passed.
- A harmless live workflow may be attempted only after this contract is accepted and implemented,
  on a host whose effective probe satisfies ADR-0013, and after a fresh direct authorization.
- Schema v0.14.0 remains an immutable migration baseline containing the discovered proof gap.

## Pre-acceptance v0.14 inspection preparation

The internal `inspect_linked_execution_v14` function now performs the strongest read-only closure
check that does not invent a v0.15 record or eligibility state. It validates the linked lock and
all public records, requires exact authorization/capability/environment/run/execution bindings,
closes the emitted Artifact role inventory, enforces one deterministic AssetIdentity per Artifact,
and verifies every retained path against its full digest without following symlinks or accepting
externally hard-linked bytes. It also opens the retained canonical source lock and independently
recovers and validates the exact RepositorySnapshot and project-execution WorkItem semantic
digests. Replay now uses the same strengthened source-lock and retained-byte checks before writing
any output. No model or runtime is called.

`tests/test_execution_runtime.py` covers read-only inspection, exact retained/public/source digest
inventories, removal of an otherwise unreferenced source-lock Artifact, identity substitution,
wrong Environment linkage, duplicate Artifacts, orphan output Artifacts, hard-linked retained
bytes, a symlinked retained-path ancestor, and a reidentified/rehashed source lock whose semantics
drift from the linked binding. This is implementation preparation for acceptance criteria 1 and 3.
It does not satisfy the ADR: the source AuditRun record is absent, the WorkItem and
RepositorySnapshot exist only inside an opaque source-lock Artifact rather than the linked public
arrays, there is no public dependency-inventory record, and the inspection grants neither
clean-control eligibility nor trusted capability origin.
