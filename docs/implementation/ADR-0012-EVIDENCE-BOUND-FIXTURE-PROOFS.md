# ADR-0012: Bind fixture proof obligations to replayable evidence

- **Status:** Accepted
- **Date:** 2026-07-28
- **Coordinated accepted schema release:** `0.12.0`
- **Related requirements:** SA-FR-085, SA-FR-091, SA-FR-097, SA-FR-102,
  AC-14, AC-43, AC-49, AC-55–59, AC-62

## Context

Public schema v0.11.0 distinguishes positive, verified-good, scope-verified-good, hard-negative,
and ambiguous fixtures and gives each fixture seven boolean proof obligations. It does not retain
the exact inputs that establish those booleans. In particular, `execution_evidence` is an enum but
does not identify the Execution and SandboxCapability records behind
`clean_environment_executed`; hard-negative pattern and decisive innocent-explanation booleans do
not cite evidence; and contract/operation references do not carry the exact digests used during
admission.

The isolated evaluator can safely generate a public-development positive fixture today because it
re-runs the complete 4+2 panel, canonical-root, and immutable source checks before writing the
record. It preserves those exact inputs in namespaced extensions, but extensions are not an
accepted public proof contract. Generating an eligible verified-good or hard-negative record from
unbound booleans would make stored claims impossible to replay independently. Treating a
subprocess as clean project execution would also violate the rootless-OCI requirement.

The current capture-only CLI verifies each review directory, packet, transcript, and capture
manifest, but then passes only the loaded reviews into fixture construction. The durable fixture
therefore cannot prove which packets and capture manifests were checked. The current source gate
also proves that review citations resolve against supplied snapshot bytes, but it does not prove
that the snapshot existed before the blind workspace and reviews. A snapshot captured after the
panel can presently satisfy the same byte checks. That chronology is too weak for an independently
replayable qualification label.

## Decision

Publish a forward-only schema v0.12.0 from immutable v0.11.0. Do not modify earlier packages.

### 1. Add a closed fixture-proof status and evidence projection

Every BenchmarkFixture gains a required `qualification_proof_status` with exactly:

- `complete` for a newly constructed, independently replayable eligible label;
- `excluded_label` for an ambiguous, insufficient, or failed label that cannot enter resolved
  qualification denominators; or
- `legacy_proof_projection_unavailable` for fail-closed migration.

Every complete fixture carries a required `proof_evidence` object containing sorted exact
reference/digest pairs for the public source snapshot, adjudication, linked AgentReviews, canonical
root causes, declared ScientificContracts, declared Operations, project Executions, and their
exact Environments and SandboxCapabilities. Verified review captures, exact review packets,
transcript bytes, and Stage-1
blind-workspace manifests use separate closed artifact-kind/identity/digest entries; they are not
misrepresented as public record types. Empty categories remain explicit arrays. The object also
carries the exact source-validation report digest and the controller profile that recomputed
admission.

Positive fixtures require the complete scientific panel and root-cause inputs. Verified-good,
scope-verified-good, and hard-negative fixtures require the complete negative panel plus every
declared contract and operation input. References and digests must resolve against the containing
evaluation bundle or an explicitly supplied immutable external input set before construction,
reporting, or replay.

### 2. Bind the blind-review input and chronology chain

The private evaluation protocol gains exact source and time bindings needed to compile the public
proof projection:

- each blind-workspace manifest identifies the source RepositorySnapshot by typed reference and
  semantic digest, records its own creation time, and proves that every copied file path and digest
  resolves against that snapshot's content-addressed manifest;
- every Stage-1 and Stage-2 packet records its creation time;
- complete fixture construction consumes verified capture manifests, packets, and transcript
  digests rather than loose AgentReview objects; and
- Stage-1 and Stage-2 freezes consume capture manifests and preserve their exact digests rather
  than discarding them after load.

Digest dependencies establish logical happens-before edges even when timestamp sources have
coarse precision. Timestamps may be equal across a dependency edge but may never reverse. For each
relevant capture chain, the closed order is snapshot capture, blind-workspace construction,
Stage-1 packet, Stage-1 review, Stage-1 capture, Stage-1 freeze, Stage-2 packet, Stage-2 review,
Stage-2 capture, scientific adjudication, and fixture construction. Every Stage-2 packet must
continue to bind the exact Stage-1 freeze and exact answer-side evidence it received. Detector
output remains prohibited until the separate scientific-label freeze.

API callers do not receive a loose-review bypass: complete construction requires the same verified
capture inputs as the CLI. Missing capture, packet, transcript, workspace, snapshot, or chronology
evidence yields an explicit incomplete proof and cannot create a complete eligible fixture.

### 3. Make clean execution an evidence-backed state

`clean_environment_executed` is permitted only when the proof projection identifies at least one
successful project-workflow Execution and its exact SandboxCapability. The controller verifies:

- explicit authorization;
- a verified rootless OCI backend;
- read-only repository mounts and separate writable roots;
- default network denial;
- restricted devices and dropped capabilities;
- enforced process and resource limits;
- no unsafe fallback;
- exact input/output and environment references; and
- a successful observed exit.

The fixture generator only validates and compiles already existing records. It never launches
project-authored code. A restricted subprocess, an auditor-verification Execution, a missing
capability record, or documented prose alone cannot establish clean execution.

`documented_external_execution` remains usable only for a scope-bounded fixture and must cite an
imported Execution with its limitations. It cannot satisfy the verified-good or hard-negative
clean-execution requirement.

### 4. Bind hard-negative semantics to exact evidence

A complete hard-negative fixture additionally carries nonempty evidence arrays for:

- the suspicious pattern that could trigger a false accusation; and
- the decisive innocent explanation that defeats that accusation inside the declared scope.

Each evidence item uses ordinary source/record references and is independently resolved. A model
statement, reviewer confidence, or free-form fixture specification cannot set either proof
obligation by itself. The generator derives both booleans only after the evidence arrays validate.

### 5. Propagate proof completeness into case outcomes and metrics

DetectorCaseOutcome gains the exact fixture semantic digest and copied
`qualification_proof_status`. Only `complete` fixtures can be `metric_eligible` for resolved
performance metrics or `promotion_evidence_eligible`. Excluded-label cases remain available to the
declared diagnostic rates where ADR-0011 permits them. Legacy-incomplete fixtures are preserved but
excluded from authoritative metric sets.

The Stage-3 reconciler verifies the fixture projection before copying it. Metric calculation and
report validation independently re-resolve the exact case-outcome inputs and fail closed on fixture
or proof drift.

### 6. Keep corpus authority and promotion closed

The first generators emit only `public_development`. This ADR does not invent held-out assignment,
reviewer authentication, reviewer independence, numerical thresholds, or detector promotion. A
later pilot-informed decision must define corpus assignment and thresholds before any metric set
can permit promotion.

## Migration from v0.11.0

- Existing positive, verified-good, scope-verified-good, and hard-negative fixtures receive
  `qualification_proof_status: legacy_proof_projection_unavailable`; no review, contract,
  capture, packet, transcript, workspace, chronology, operation, execution, sandbox, pattern, or
  innocent-explanation evidence is inferred.
- Existing excluded fixtures receive `qualification_proof_status: excluded_label` and retain their
  exact prior evidence without becoming eligible.
- Existing case outcomes copy the legacy or excluded status, become metric- and
  promotion-ineligible when the proof is unavailable, and receive a newly derived identity that
  binds that state.
- Existing QualificationMetricSets are removed from authoritative bundle arrays and retained only
  as namespaced legacy evidence because their resolved denominators did not include fixture-proof
  completeness.
- StorageManifests are cleared because canonical bytes change.

## Alternatives

### Trust the existing proof-obligation booleans

Rejected because a boolean cannot show which execution, contract, operation, or evidence made it
true and therefore cannot support independent replay.

### Standardize namespaced extensions without a schema release

Rejected because extensions are not a public semantic contract and older consumers may ignore
them while still treating the fixture as eligible.

### Execute the fixture automatically during generation

Rejected because construction is answer-side evidence compilation, not authorization to run
project code. Execution requires a separate explicit authorization and qualifying rootless OCI
backend.

### Treat reviewer agreement as clean execution or an innocent explanation

Rejected because panel agreement cannot establish an observed execution fact, and model confidence
cannot establish a material premise.

## Acceptance evidence required

1. Schema invariants close proof status, exact reference/digest inputs, hard-negative evidence,
   and clean-execution conditions.
2. Positive construction replays the full panel/root/snapshot/capture/packet/workspace chronology
   gate and rejects any source, review, transcript, capture, packet, root, or digest mutation.
3. A snapshot created after its workspace or panel, a reversed packet/review/capture time, a loose
   review, or a capture omitted from either freeze cannot produce a complete proof.
4. Verified-good and hard-negative construction fails without a successful authorized project
   Execution and qualifying rootless OCI SandboxCapability.
5. A restricted subprocess, auditor Execution, failed execution, unsafe fallback, network-enabled
   capability, or unresolved contract/operation reference cannot establish a complete control.
6. Hard-negative pattern and decisive-explanation evidence each resolve exactly and mutation fails
   closed.
7. Legacy migration invents no proof, execution, comparison, metric, corpus partition, or
   qualification authority.
8. Canonical JSONL, disposable SQLite, AuditBundle validation, reports, CLI/wheel isolation, and
   model-free replay preserve the complete proof projection.
9. No model call or project-authored execution occurs during fixture construction, validation,
   reporting, or replay.

## Consequences

- Eligible controls become replayable evidence products instead of trusted labels with booleans.
- The first usable external validation run may still use public-development fixtures, but it cannot
  be represented as held-out qualification or detector promotion.
- Implementing a real clean verified-good or hard-negative path remains dependent on a separately
  authorized rootless OCI execution backend and supplied external panel evidence.

## Acceptance record

Accepted by the repository owner on 2026-07-28 as proposed with the strengthened capture, packet,
transcript, workspace, snapshot, and chronology bindings, including coordinated schema v0.12.0.
Accepted status authorizes implementation; qualification and promotion claims remain conditional
on the evidence gates in this ADR.
