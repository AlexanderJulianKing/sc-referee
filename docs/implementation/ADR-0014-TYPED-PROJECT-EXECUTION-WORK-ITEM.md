# ADR-0014: Give project execution a non-model WorkItem contract

- **Status:** Accepted
- **Date:** 2026-07-29
- **Coordinated accepted schema release:** `0.14.0`
- **Related requirements:** SA-FR-047–049, SA-FR-091, AC-28–32, AC-43, AC-49

## Context

Accepted ADR-0013 requires every one-use authorization to bind an explicit execution WorkItem in
an already locked source run. Public schema v0.13.0 cannot truthfully create that WorkItem:

- `WorkItem.kind` has no project-execution value;
- every `WorkItem.packet.policy.project_code_execution` is fixed to `false`;
- every packet is structurally a model prompt packet and requires prompt-template identities; and
- `required_output_record_types` allows only Claim, SemanticAssertion, and MaterialQuestion, not
  authorization, execution, environment, log, or output evidence.

Using `auditor_owned_verification` for project code, inventing a prompt identity, or setting the
scheduling privilege to project execution while the packet forbids it would produce a
schema-valid but materially contradictory record. A generic existing WorkItem also cannot prove
that the source run deliberately scheduled the linked reproduction attempt required by ADR-0013.

This gap was discovered while implementing the accepted v0.13 capability probe, before exposing
an authorization CLI or executor. The capability probe is unaffected because it executes only
versioned sc-referee-owned code.

## Decision

Publish a forward-only schema v0.14.0 from immutable v0.13.0. Do not alter the accepted v0.13.0
package.

### 1. Add a project-execution WorkItem variant

Add `project_execution` to `WorkItem.kind` and `awaiting_authorization` to `WorkItem.status`.
Project-execution WorkItems must use `scheduling.execution_privilege: project_code_execution` and
remain `awaiting_authorization` in the immutable source lock. They do not authorize execution.

Make `WorkItem.packet` a closed discriminated union:

- `semantic_or_auditor_work_v1` preserves the existing v0.13 prompt-packet meaning, keeps
  `project_code_execution:false`, and remains the only packet accepted by model-proposal paths;
  and
- `project_execution_request_v1` is a controller work packet, not a model prompt. It binds the
  source snapshot digest, bounded purpose, exact target/input record references, normalized
  allowed output paths, and any explicitly proposed image/argv/environment/limit envelope. It
  states that direct interactive authorization is still required, network is denied, repository
  text and model/scientist output cannot authorize or broaden the request, and host/HPC escalation
  is prohibited.

An unresolved launch field remains explicit in the packet. It does not become a Finding and does
not make the WorkItem launchable. The direct authorization surface may narrow a proposed envelope
or fill a field declared unresolved by the source WorkItem; it may not change the WorkItem's
purpose, targets, inputs, allowed output paths, network policy, or privilege boundary.

Project-execution packets have no prompt-template identifier and are never submitted to a model.
Their expected evidence types are limited to ProjectExecutionAuthorization, Execution,
Environment, Artifact, FileRecord, AssetIdentity, AuditRun, and SandboxCapability.

### 2. Bind authorization to the exact WorkItem meaning

Extend `ProjectExecutionAuthorization` with a required WorkItem semantic digest and a required
binding status:

- `complete_project_execution_work_item` for a newly verified v0.14 project-execution WorkItem; or
- `legacy_work_item_semantics_unavailable` for migrated v0.13 evidence.

Only the complete status can enter the controller authorization registry or support a new launch.
The controller verifies that the referenced WorkItem belongs to the source AuditRun, is present in
the bound source semantic lock, has the project-execution packet variant and awaiting status, and
that every immutable scope field agrees before presenting the fresh user challenge.

### 3. Preserve linked-run and single-use rules

The source WorkItem remains byte-identical after authorization. The linked reproduction run
records authorization, consumption, execution, outputs, and its own semantic lock. It may project
the source WorkItem reference and digest but does not rewrite the source WorkItem to completed.
Replay never turns either WorkItem or public authorization JSON into launch authority.

### 4. Migrate fail closed

The v0.13→v0.14 migration:

- marks every existing non-project WorkItem packet `semantic_or_auditor_work_v1` without changing
  its prior policy;
- creates no project-execution WorkItem and no controller registry state;
- marks existing ProjectExecutionAuthorization records
  `legacy_work_item_semantics_unavailable` with no invented WorkItem digest;
- makes project-workflow Executions depending on those authorizations ineligible as clean-control
  evidence; and
- downgrades dependent fixtures/outcomes and removes authoritative metrics using the same
  fail-closed policy as ADR-0012 and ADR-0013.

## Alternatives

### Reuse `auditor_owned_verification`

Rejected because project-authored code and auditor-owned verification have different privilege
and epistemic meanings.

### Treat the authorization record itself as the WorkItem

Rejected because ADR-0013 requires the source run to lock an explicit scheduled purpose before
the direct post-lock authorization transition.

### Keep the prompt packet and flip its execution boolean

Rejected because this would misrepresent a host-security control request as model work and would
leave its expected evidence types unrepresentable.

## Acceptance evidence required

1. Schema tests reject project-execution WorkItems using prompt packets, non-project WorkItems
   using execution packets, incorrect privileges/statuses, prompt identities in execution packets,
   broadenable output paths, or authorizing policy values.
2. Existing semantic/model WorkItems retain their v0.13 fail-closed behavior and proposal paths
   reject the execution packet variant.
3. Authorization creation rejects an absent, mutable, cross-run, non-project, non-awaiting, or
   digest-mismatched WorkItem before presenting a challenge or writing registry state.
4. Authorization scope cannot broaden the WorkItem purpose, targets, inputs, output paths, network
   policy, or declared launch-envelope constraints.
5. Source lock bytes remain unchanged through authorization, consumption, execution, linked lock,
   and replay.
6. v0.13→v0.14 migration invents no execution WorkItem, WorkItem digest, authorization authority,
   registry state, qualifying execution, fixture proof, metric, or promotion evidence.

## Consequences

- Authorization and executor implementation must pause at the WorkItem admission boundary until
  this durable meaning is accepted and implemented.
- The rootless-OCI capability probe and static audit remain usable because neither executes
  project-authored code.
- Schema v0.13.0 remains an immutable migration baseline containing the discovered limitation.

## Acceptance record

Accepted by the project owner on 2026-07-29 with the coordinated public schema release
`0.14.0` as recommended. This acceptance authorizes implementation of the typed request and
admission boundary. It does not authorize execution of project-authored code; every actual
launch still requires the separate fresh, direct, single-use authorization defined by ADR-0013.

## Implementation record

Implemented on 2026-07-29 with immutable reference and packaged schema v0.14.0.

| Change | Test evidence | Acceptance criterion |
|---|---|---|
| Closed project-execution WorkItem packet, schema union, examples, and fail-closed v0.13 migration | `tests/test_project_execution_work_item_schema_release.py`, `tests/test_v013_to_v014_migration.py` | 1, 2, 6 |
| Exact request lock and model-path rejection | `tests/test_execution_request.py`, proposal-path tests in the complete suite | 1, 2, 5 |
| Fresh attached-terminal authorization bound to the exact source lock, WorkItem, capability, and narrowed launch envelope | `tests/test_execution_authorization_registry.py`, `tests/test_execution_request.py` | 3, 4, 5 |
| Private single-use registry, exact snapshot verification/restaging, terminal execution attempts, linked public evidence, and model-free artifact replay | `tests/test_execution_runtime.py` | 3, 4, 5 |

Remaining coverage limitations are explicit: no project-authored code has been executed; the
current host has no qualifying Podman backend; direct cgroup-v2 resource observation is tested from
synthetic kernel-file fixtures but not a live container and remains unavailable for remote
Podman-machine cgroups; and schema v0.14.0 cannot bind the complete linked execution dependency
closure into clean-control fixture proof. Capability admission also cannot yet distinguish a
trusted controller probe from standalone self-consistent JSON or bind an auditor-owned probe image.
These limitations are recorded in the schema-gap register and proposed ADR-0015/ADR-0016 rather
than being hidden behind loose record IDs or provenance strings.
