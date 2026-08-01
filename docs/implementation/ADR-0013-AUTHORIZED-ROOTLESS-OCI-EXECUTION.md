# ADR-0013: Evidence-bound authorization and rootless-OCI execution

- **Status:** Accepted
- **Date:** 2026-07-28
- **Coordinated accepted schema release:** `0.13.0`
- **Related requirements:** SA-FR-047–049, SA-FR-052, SA-FR-072, SA-FR-091,
  AC-28–32, AC-43, AC-49, AC-58

## Context

Accepted ADR-0012 and schema v0.12.0 can verify an already supplied project-workflow Execution and
SandboxCapability before admitting a clean verified-good or hard-negative fixture. The production
controller and isolated evaluator still cannot create that evidence. Static inspection and
auditor-owned verification remain the only implemented execution levels.

The current public records are also too weak for the first real executor:

- `Execution.sandbox.authorization_status: authorized` does not identify who authorized which
  exact snapshot, image, command, inputs, outputs, limits, or duration;
- `SandboxCapability` contains control booleans but no exact probe evidence or effective limit
  values;
- `Execution` has no closed initiating-WorkItem, purpose, container-image identity, effective
  sandbox policy, log-artifact, cleanup, or structured resource-consumption projection; and
- extensions cannot carry these material premises because older consumers may ignore them.

The configured local Docker Desktop daemon currently reports seccomp and cgroup namespaces but
does not report Docker rootless mode. It therefore cannot establish `rootless_verified: true`.
Presence of a `docker` or `podman` binary, a successful `run`, a VM boundary, or a restricted host
subprocess is not equivalent evidence.

Rootless support also cannot be inferred solely from a version string. Docker documents that
rootless resource flags may be ignored without the required cgroup-v2/systemd delegation, and
Podman documents host-specific rootless UID/GID, storage, and networking constraints. The
controller must probe effective controls and fail closed.

## Decision

Publish a forward-only schema v0.13.0 from immutable v0.12.0. Do not modify earlier packages.

### 1. Add an exact one-execution authorization record

Add public `ProjectExecutionAuthorization` with a closed authorization scope containing:

- one exact source AuditRun and semantic-lock digest, one newly allocated linked AuditRun with the
  source run as its `parent_run_ref`, one initiating WorkItem, and one RepositorySnapshot reference
  and semantic digest;
- one digest-pinned OCI image reference;
- one normalized argument vector and its digest, with no implicit shell interpretation;
- exact declared input record references and a closed list of normalized relative output paths,
  with no absolute path, traversal, symlink, or repository-defined glob expansion;
- an exact nonsecret environment-variable allowlist and its normalized digest;
- one exact SandboxCapability reference and semantic digest;
- network fixed to `denied`;
- numeric wall-time, CPU, memory, process, open-file, and writable-byte limits;
- an expiry time and a single-use authorization nonce;
- the declared local authorizing actor and `declared_local_user` identity assurance;
- explicit acknowledgements that project code will execute, the repository is untrusted, output is
  confined to an audit-owned root, network is denied, and no host or HPC escalation is granted;
  and
- provenance and limitations stating that local actor identity is declared rather than externally
  authenticated.

Only the direct user-facing authorization surface can create this record. The initial surface is a
CLI; any later API requires a separate accepted equivalent user-presence mechanism. Repository
text, model output, a Scientist Answer, a WorkItem, an earlier authorization, or fixture metadata
cannot create or broaden it. An authorization binds exactly one attempt; retry requires a new
record.

The initial authorization surface requires a controlling user at an attached interactive terminal,
shows the normalized launch envelope and bound source-lock digest, and requires a fresh
controller-generated challenge. It rejects piped standard input, a prefilled acknowledgement flag,
and direct record import as authorization. An agent or model proposal can populate a draft launch
request, but cannot complete the controller's authorization transition. This is a user-presence
barrier, not identity authentication: the record continues to claim only
`declared_local_user`. The controller registers the record in a newly created, non-symlink,
audit-owned authorization directory and binds its registry identity and linked output-root identity.
Copying the public JSON does not create a launchable authorization.

The authorization command records consent but does not execute. The execution command requires the
exact immutable authorization record as input and recomputes every bound digest before launch. It
then atomically creates a no-replace consumption receipt before invoking the runtime. The receipt
binds the authorization digest and nonce, attempt identity, source lock, linked output root,
controller identity, and claim time. Receipt existence consumes the authorization even if launch,
capture, timeout handling, cancellation, or the controller itself later fails. Concurrent claims,
registry copies, and retry after a crash fail closed. Recovery converts an orphaned receipt into an
explicit bounded failed/unknown attempt; it never deletes the receipt or makes the authorization
reusable.

The consumption receipt is canonical controller control-plane state rather than portable execution
authority. Its identity and terminal disposition are projected into the public Execution. A public
bundle can therefore replay the observed authorization and consumption evidence without becoming a
launch credential.

### 2. Bind SandboxCapability to an effective tool-owned probe

Extend `SandboxCapability` with a required proof projection whenever
`project_code_execution_supported` is true. It contains:

- backend executable identity, version, endpoint/context identity, and normalized info digest;
- a fixed `rootless-oci-capability-probe-v1` profile;
- exact references/digests for auditor-owned probe logs and artifacts;
- the observed rootless/user-namespace state;
- observed support for a read-only repository mount and a separate writable root;
- observed network-namespace denial;
- observed all-capability drop and no-new-privileges behavior;
- observed restricted device access;
- effective wall-time, CPU, memory, PID, open-file, and writable-byte enforcement support; and
- probe time, host platform, OCI runtime identity, limitations, and expiry.

The probe executes only versioned sc-referee-owned probe code and never project files. It may run
automatically as auditor-owned verification. An arbitrary or unbound remote endpoint, privileged
daemon, absent rootless signal, ignored resource controller, probe failure, stale probe, or
unavailable evidence produces `project_code_execution_supported: false`. There is no subprocess or
unverified-container fallback.

Initial support is one backend profile at a time. The recommended first implementation is Podman
rootless on Linux or through a Podman-managed Linux machine only when the service itself reports
rootless operation and every control probe passes. Docker is accepted only when the connected
daemon explicitly reports rootless mode and the same effective probes pass. Docker Desktop by
itself is not treated as proof of rootless mode.

A Podman-managed machine is not treated as an anonymous remote merely because its client uses a
socket connection. Qualification binds the locally managed machine identity, connection identity,
service identity, VM and runtime versions, and normalized capability-probe result. A generic
SSH/TCP endpoint, a user-selected remote host, or identity drift invalidates the capability. This
ADR grants no authority to transmit project bytes to an arbitrary host.

### 3. Add an exact project-execution projection

For `execution_kind: project_workflow`, extend `Execution` with required:

- authorization reference/digest and `complete` authorization-evidence status;
- consumption-receipt digest and terminal single-use disposition;
- initiating WorkItem reference and bounded purpose;
- image reference and immutable image digest;
- exact normalized argument vector and digest;
- the effective policy copied from the authorization and capability;
- stdout, stderr, controller-event-log, and output-manifest Artifact references;
- observed start, finish, exit, timeout, and cleanup states;
- observed peak CPU time, memory, process count, and written bytes, with explicit unavailable fields
  where the runtime cannot observe a value; and
- exact input/output/environment/capability references.

The qualifying control path requires all material policy enforcement and cleanup evidence to be
observed. Unavailable resource observations may remain valid Execution evidence with limitations,
but cannot establish a clean qualification control when the corresponding limit premise is
material.

### 4. Use one closed launch envelope

The executor launches an argument vector without a host shell and with all of these controls:

- immutable snapshot mounted read-only at `/project`;
- an OCI-enforced, byte-bounded, tool-owned writable filesystem mounted at `/output`, with accepted
  bytes copied into a fresh audit-owned linked output root only after the project process stops;
- read-only container root filesystem and OCI-bounded temporary filesystems;
- `network=none` with no host network or published ports;
- all Linux capabilities dropped and no-new-privileges enabled;
- no privileged mode, runtime socket, host PID/IPC/UTS namespace, added device, arbitrary host
  mount, SSH agent, credential directory, or inherited secret;
- a non-root container user;
- explicit CPU, memory, PID, open-file, writable-byte, and wall-time limits;
- an exact digest-pinned image already present or retrieved by a separate provenance-recorded
  controller action; and
- working directory `/project`.

Counting output after execution is not writable-byte enforcement. The qualifying backend must prove
an effective runtime or storage control that bounds bytes allocated by `/output` and temporary
filesystems while project code runs; a plain host bind mount plus a later scanner cannot qualify.
Logical file sizes, path allowlists, and aggregate accepted bytes are checked independently during
capture. The controller extracts output only while no project-authored process remains capable of
writing, then terminates and removes the retained sandbox. Failure to establish that quiescent state
or to clean up is recorded and blocks clean control evidence.

The initial profile does not install dependencies, invoke a shell, run a workflow engine, mount
large external data, use GPUs, or submit HPC work. Those remain unavailable or produce a
ReproductionRequest. Image retrieval is controller network activity, never project network
permission.

The executor passes only explicitly declared environment variables. Repository configuration
cannot add mounts, devices, capabilities, namespaces, ports, secrets, hooks, or runtime flags.

### 5. Capture outputs without trusting them

The controller streams stdout and stderr into bounded audit-owned files, records truncation, and
hashes the final bytes. After the project process exits and the writable filesystem is quiescent, it
inventories `/output` without executing or deserializing its contents, rejects symlinks and special
files, enforces the authorized relative-path and logical-byte budget, and emits exact
Artifact/FileRecord/AssetIdentity records where applicable.

Successful process exit is an observed fact, not scientific correctness. Output bytes remain
untrusted evidence. A failed, timed-out, killed, truncated, cleanup-failed, policy-divergent, or
out-of-scope execution remains an Execution record but cannot establish clean control evidence.

### 6. Preserve static-first and semantic-lock ordering through a linked reproduction segment

Production project execution is schedulable only after snapshot, inventory, static parsing, and an
explicit execution WorkItem exist in a source run. That source run reaches semantic lock first, as
required by the normative lifecycle. The direct user authorization binds that exact source
semantic-lock digest, WorkItem, snapshot, capability, image, argument vector, inputs, outputs, and
limits.

Authorized execution then occurs in a new linked reproduction segment. The source lock and source
audit remain immutable. The linked segment permits no model calls, performs at most the one
authorized attempt, and creates a new content-addressed semantic lock that includes the exact
authorization, capability, Execution, environment, logs, output manifest, accepted output
identities, and every retained failure or limitation. Detector execution that depends on those
records begins only from this post-reproduction linked lock. Model-free replay consumes the linked
lock and recorded output identities; it does not relaunch the container or reuse the authorization.

This two-lock linked-run profile resolves the otherwise circular requirement that authorization
bind an existing semantic lock while reproduction evidence that affects detectors must itself be
fixed by the lock used for detection. It also prevents an execution result from mutating a
published source lock or becoming a post-lock model prompt. Evaluation-only execution follows the
same ordering before the blind scientific panel and remains answer-side; fixture construction
continues to validate records without launching code.

### 7. Keep failure local and authority narrow

Capability absence, denied authorization, expiry, digest drift, runtime failure, timeout, or output
rejection yields a bounded unavailable/failed state and coverage or ReproductionRequest evidence.
It does not fail unrelated static inspection, become a Finding, imply a global risk state, or grant
future execution authority.

### 8. Make the authorization and linked topology public without making it executable

Schema v0.13.0 adds `ProjectExecutionAuthorization` to the public record catalog, record union,
JSONL/SQLite projection, examples, and a required (possibly empty)
`AuditBundle.project_execution_authorizations` array. It revises `SandboxCapability` and
`Execution` with the closed projections above. A project-workflow Execution must use the linked
AuditRun identity bound by its authorization; that linked AuditRun must name the source AuditRun in
its existing `parent_run_ref`. The authorization's source-lock digest and the bundle's linked-lock
digest are distinct and cannot be substituted for one another.

The linked semantic-lock manifest version advances and includes the authorization, consumption,
capability, execution, environment, log, and accepted-output identities. The authorization record
is portable evidence only. Launch also requires the matching unconsumed controller-registry entry,
so importing a record, bundle, JSONL stream, SQLite projection, migration result, fixture, or replay
artifact cannot execute code.

## Migration from v0.12.0

- AuditBundles receive an empty `project_execution_authorizations` array. Migration never creates a
  controller-registry entry or launchable authorization.
- Existing `SandboxCapability` records with project execution support receive
  `capability_evidence_status: legacy_probe_projection_unavailable` and become ineligible to
  authorize new execution. No probe result is inferred.
- Existing project-workflow Executions receive
  `authorization_evidence_status: legacy_authorization_projection_unavailable`. Their observed
  existence is preserved, but authorization, effective controls, and qualification eligibility are
  not inferred.
- Complete v0.12 fixtures that depend on such legacy execution are downgraded to
  `legacy_proof_projection_unavailable`; linked case outcomes become metric- and
  promotion-ineligible, and authoritative metric sets are removed as in ADR-0012.
- Existing auditor-verification and imported Executions remain non-project-execution evidence and
  receive the appropriate not-required/imported authorization status without gaining authority.
- No migrated run is reclassified as a linked reproduction segment, and no parent/source-lock
  relationship is inferred beyond already represented `parent_run_ref` evidence.
- StorageManifests are cleared because canonical bytes change.

## Alternatives

### Treat Docker Desktop or any container command as qualifying OCI isolation

Rejected because container availability does not prove a rootless daemon or effective limits.

### Use v0.12 booleans plus extensions

Rejected because authorization, resource, command, image, log, and probe premises are material and
must survive consumers that ignore extensions.

### Reuse Scientist Answer as execution authorization

Rejected because accepted interaction policy explicitly prevents an Answer from granting execution
privilege. Scientific intent and host-security consent are different authorities.

### Fall back to a restricted subprocess

Rejected by SA-FR-091 and accepted architecture ADR-0033.

### Let the executor resolve image tags or install dependencies

Rejected for the first profile because mutable resolution and installation hooks introduce
separate network, supply-chain, and untrusted-execution evidence requirements.

## Acceptance evidence required

1. Schema invariants close authorization scope, exact image/argv/snapshot/capability digests,
   effective controls, logs, resources, linked-run topology, consumption, and legacy states.
2. A capability probe fails closed for absent rootless reporting, rootful or arbitrary/unbound
   remote endpoints, local-machine identity drift, stale evidence, ignored resource limits, network
   reachability, writable project mounts, retained capabilities, device access, or unsafe fallback.
3. Repository text, model proposals, Scientist Answers, and WorkItems cannot create or broaden an
   authorization. The authorization command rejects non-interactive/piped input, prefilled
   acknowledgement, direct record import, and a stale or incorrect fresh challenge.
4. Atomic no-replace consumption prevents concurrent launch, copied-registry launch, retry, and
   reuse after controller crash, runtime-start failure, timeout, or cancellation. Recovery preserves
   the receipt and emits an explicit bounded failure/unknown state.
5. Authorization mutation, expiry, snapshot drift, command drift, image drift, input/output drift,
   linked-run drift, or capability drift prevents launch.
6. The exact launch argument vector contains every required control and rejects shell, privileged,
   host namespace, socket, device, secret, port, arbitrary-mount, or network escalation.
7. Effective tests prove physical writable-space enforcement during execution and reject a plain
   host bind mount plus post-hoc counting. Logical byte excess, timeout, signal, nonzero exit, log
   truncation, output symlink/special file, path escape, and cleanup failure are recorded and cannot
   establish clean control evidence.
8. A successful bounded test workflow produces exact authorization, capability, environment,
   Execution, consumption, log, output-manifest, and output records in a linked reproduction lock
   and replays without the runtime or a second authorization attempt. The source lock remains
   byte-identical.
9. Fixture generation consumes those records without executing code; Stage 3, metrics, storage,
   AuditBundle, reports, and both wheels preserve the projection without granting promotion or
   launch authority.
10. v0.12→v0.13 migration invents no authorization, probe, execution, output, metric, corpus,
    promotion, linked-run, or controller-registry evidence.
11. Static-only audit remains available and unchanged when no qualifying backend exists.
12. At least one separately authorized live rootless backend passes the effective probe and a
    harmless bounded test workflow before the capability is claimed locally.

## Consequences

- This closes the implementation mechanism blocking real clean controls without weakening static
  defaults.
- The current host remains static-only until a qualifying rootless backend is installed and passes
  the effective probe.
- Schema v0.13.0 is required because v0.12.0 cannot durably represent the material authorization
  and runtime premises.
- This ADR does not authorize any particular project execution, model call, dataset download,
  dependency installation, or detector promotion.

## References

- [Docker rootless mode](https://docs.docker.com/engine/security/rootless/)
- [Docker rootless resource-limit constraints](https://docs.docker.com/engine/security/rootless/tips/)
- [Podman rootless mode](https://docs.podman.io/en/latest/markdown/podman.1.html#rootless-mode)
- [Podman run controls](https://docs.podman.io/en/latest/markdown/podman-run.1.html)
- [OCI Linux runtime configuration](https://github.com/opencontainers/runtime-spec/blob/main/config-linux.md)

## Acceptance record

Accepted by the repository owner on 2026-07-29 as recommended with coordinated schema v0.13.0 and
the fail-closed, evidence-bound execution envelope above. Acceptance authorizes implementation of
the capability probe, authorization registry, and executor; it does not authorize any particular
project execution.

## Resource-observer implementation record

The 2026-07-29 v0.14 executor follow-through adds a background local-Linux cgroup-v2 observer. It
uses the exact Podman container name to obtain the running host PID, resolves that PID's unified
cgroup without invoking container code, and reads cumulative `cpu.stat`, kernel `memory.peak`,
kernel `pids.peak`, and bounded descendant `cgroup.procs` evidence while the main thread drains
stdout/stderr. `open_files_peak` is the maximum per-process descriptor count seen at 50 ms samples,
matching the per-process `RLIMIT_NOFILE` envelope; the report limitation states that shorter spikes
may be missed. Non-Linux, remote-machine, missing, malformed, oversized, or inaccessible cgroup
evidence remains null and cannot support clean-control eligibility. Observed memory, PID,
open-file, or written-byte overages also fail closed.

`tests/test_execution_resources.py` covers exact CPU conversion, memory/PID kernel peaks,
per-process descriptor counting, bounded descendant cgroups, unavailable fields, exact PID/cgroup
binding, remote/unavailable behavior, concurrent log draining, and timeout shutdown. The execution
runtime tests cover complete synthetic eligibility and observed-limit rejection. This advances
acceptance criteria 1, 7, and 8 mechanically. Criterion 12 remains external: no live Podman cgroup
or project-authored workflow was executed on this host.
