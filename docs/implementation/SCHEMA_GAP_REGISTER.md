# Schema gap register

The v0.5 architecture referred to observed-computation and control-plane records that were absent
from the v0.5 schema catalog. Accepted ADR-0002 resolves the six-record gap in the coordinated
local public schema release v0.6.0. The immutable v0.5 package remains unchanged.

## Blocking gaps for the walking skeleton

| Record | Why needed | Current treatment |
|---|---|---|
| `AuditRun` | Run state, linkage, terminal status | Public v0.6.0 schema and runtime record |
| `StageResult` | Durable partial and error states | Public v0.6.0 schema and runtime record |
| `FileRecord` | Inventory and identity | Public v0.6.0 schema and runtime record |
| `Operation` | Observed computation node | Public v0.6.0 schema and runtime record |
| `Artifact` | Report, result, and output node | Public v0.6.0 schema and runtime record |
| `ObservedResult` | Typed scalar used by first detector | Public v0.6.0 schema and runtime record |

## Resolved multidimensional-lineage gap

Accepted [ADR-0005](ADR-0005-MULTIDIMENSIONAL-LINEAGE-PLANE.md) and immutable public schema v0.8.0
add DataAsset, Variable, AnalysisDecision, SelectionEnvelope, Execution, and Environment records,
plus independent report, result, computation, input, execution, and semantic Claim grades. The
runtime, migration, coverage, report, JSONL/SQLite projection, interaction, and replay paths enforce
the authority split. Auditor verification never becomes project execution, and scientist intent
changes only semantic origin.

## Later gaps

- `Measurement` as a scientific measurement node distinct from observed Variable storage;
- `NotebookCell` and `DocumentChunk` for medium-native locations beyond file spans;
- `SemanticUnknown` and `SemanticConflict` as first-class graph nodes rather than only slot states
  or multiple assertions; and
- an explicit typed graph-edge record for relations not owned naturally by one endpoint.

These remaining normative graph nodes are absent from the public v0.9.0 catalog and AuditBundle.
Adapters or detectors whose material premises need them must abstain or obtain a separate accepted
ADR; they must not overload existing records or extensions.

Accepted revised ADR-0020 applies that rule to analysis-scoped scientific-check modules. A static
method observation must name its actual FileRecord or Operation and reach the selected analysis
surface through an exact replayable path owned by existing typed records. Repository co-presence,
matching vocabulary, or an `x-` extension containing both IDs is not a material join. If the QTL,
pulse-admixture, or MVMR marker cannot establish the path through v0.14.0 Operation, Artifact,
FileRecord, PublicationSurface, and source references, that module must abstain until a forward-
only schema ADR resolves the generic-edge gap. The first implementation proves the report Artifact
to selected PublicationSurface path and therefore permits report-derived analysis questions. Its
QTL Python adapter attaches the exact observation to the actual source FileRecord and recognizes
roles and bounded dataflow rather than local function names, but it cannot prove a source-to-
selected-report edge in the marker repository. The registry consequently retains that observation
only as an unscoped internal corroborator or suppressor; it never compiles it as a public assertion,
question premise, detector result, or Finding. This is an explicit remaining graph gap, not an
extension-field workaround.

## Scientific approximation-policy and tolerance gap

Public schema v0.14.0 has no ScientificContract dimension for a general governing approximation
policy or numeric tolerance. `measurement_model`, `uncertainty_target`, and arbitrary assertion or
extension payloads must not be repurposed to carry that meaning. Revised proposed ADR-0018 therefore
keeps approximation compatibility as a roadmap rule family and prohibits the first
`expected_count_background_v1` slice from calling alternative values material, acceptable,
negligible, or excessive without a separately accepted non-overloaded representation. It may
preserve exact differing values and ask which method governs. Any detector that requires the
tolerance as a material premise must abstain until an accepted ADR resolves or supersedes this gap.

Accepted [ADR-0004](ADR-0004-TYPED-SEMANTIC-INTERACTION-PLANE.md) resolves the public WorkItem,
Answer, proposal-submission, and pre-lock AuditRun-state gaps in schema v0.7.0. The v0.6.0 package
remains immutable.

## Resolved unavailable publication-surface gap

An arbitrary repository can legitimately contain no report-like artifact. Public v0.6.0 currently
requires at least one `PublicationSurface.candidates` item and at least one
`CoverageRecord.scope.publication_surface_refs` item. The controller cannot meet both constraints
without inventing a surface.

[ADR-0003](ADR-0003-UNAVAILABLE-PUBLICATION-SURFACE.md) is accepted. The coordinated local v0.6.0
release now represents an empty unresolved PublicationSurface and empty CoverageRecord surface
references only under explicit unavailable/unresolved invariants. The controller emits the linked
open MaterialQuestion and schedules no dependent detector target.

## AuditBundle pre-lock partial-run gap

The public v0.9.0 `AuditBundle` schema still requires `semantic_lock_digest`, while the
normative lifecycle permits a hard deadline before semantic lock. A controller
cannot truthfully emit that required field for a pre-lock partial run without
either inventing a semantic lock or changing the field's meaning.

Milestone 0 H03 therefore exercises checkpointed partial bundle and report
generation only after a valid semantic lock. Earlier deadline states persist
through public `AuditRun` and `StageResult` records, but promotion of a
pre-lock partial bundle requires an ADR and public schema revision that makes the
lock state explicit.

## Audit-diff and detailed deadline-event gaps

The architecture names stable audit diffs, but public v0.9.0 has no `AuditDiff` record. The current
digest-bound `sc-referee diff` output and linked `observed/deadline-ledger.json` are canonical
implementation protocols, not public record types. They must not be described as an accepted
public interchange format.

Accepted [ADR-0006](ADR-0006-SEMANTIC-LOCK-PERFORMANCE-PROJECTION.md) resolves the bounded aggregate
projection without changing immutable schema v0.8.0: every completed general or interaction lock
has one PerformanceRecord measured through semantic lock. It carries current-segment elapsed and
paused time, metered snapshot identity reads, and current-run parser-cache counts. It explicitly
does not represent total run duration. The detailed event/segment chain, post-lock elapsed time,
complete I/O, CPU, memory, token, network, and service-latency measurements remain unrepresented.
A future public event chain or run-final boundary requires a new accepted ADR and, where new record
types are needed, a schema release.

## Resolved answer-side root-cause reconciliation gap

Accepted [ADR-0008](ADR-0008-CANONICAL-ROOT-CAUSE-RECONCILIATION.md) addresses this with
review-local Stage-1 candidate identities, exact fresh Stage-2 candidate-set reconciliation, and a
public adjudicated root-cause record in immutable schema v0.9.0. Candidate IDs are recomputed from
closed review content, Stage 1 receives no canonical grouping, and two fresh provider families
must select the identical cross-provider Stage-1 candidate set. The evaluator, fail-closed
v0.8-to-v0.9 migration, positive-admission gate, label-freeze replay, AuditBundle, JSONL, SQLite,
and report acceptance tests now pass locally. Prose similarity, confidence, and majority vote have
no identity authority.

The separate Stage-3 detector-to-root-cause equivalence and qualification-metric meaning remains
open. The accepted root record establishes the answer-side panel decision only; it does not score
or qualify a detector.

## Cancellation coverage-status gap

The normative lifecycle and report vocabulary include cancellation with preserved artifacts,
but public `CoverageRecord.overall_status` has no cancellation value. Mapping a scientist
cancellation to `partial_error`, `partial_evidence_unavailable`, or
`partial_budget_exhausted` would change its meaning.

Until a public schema revision adds an exact cancellation status, cancellation is persisted
truthfully in public `AuditRun` and `StageResult` records and does not fabricate a public
CoverageRecord status. Post-lock host-limit exhaustion may use
`partial_budget_exhausted`, and genuine controller failures may use `partial_error`.

## Resolved Stage-3 detector-comparison gap

Accepted [ADR-0010](ADR-0010-EXPERIMENTAL-DETECTOR-CANDIDATE-STATE.md),
[ADR-0011](ADR-0011-REPRODUCIBLE-QUALIFICATION-METRIC-INPUTS.md), and public schema v0.11.0 resolve
the two v0.10.0 information losses without modifying that immutable baseline. A closed
`evaluation_finding_candidate` DetectorResult state now represents a Finding-shaped output blocked
only by experimental maturity and can never pass production Finding admission. Each complete
DetectorCaseOutcome now retains one exact digest-bound projection per DetectorResult, and the
accepted formulas, exclusion rules, counter bytes, percentile indices, and fail-closed legacy
behavior make all twelve metrics independently reproducible. The v0.10→v0.11 migration does not
invent either missing projection and removes legacy metric sets from authoritative arrays.

## Answer-side grader-evidence gap

Public v0.9.0 has no runner-side grader-result record. Active Experiment 0004 therefore stores a
private, self-digested exact-JSON observation after reconstructing the public content-addressed
snapshot manifest. A match or mismatch cannot enter the public bundle, admit a scientific label,
contribute a detector metric, or establish a Finding. General grader evidence, tolerances, units,
stochastic outputs, and public adjudication linkage require an accepted ADR and later schema
release rather than an extension-field convention.

## Resolved fixture-proof evidence gap

Accepted [ADR-0012](ADR-0012-EVIDENCE-BOUND-FIXTURE-PROOFS.md) and immutable public schema v0.12.0
replace v0.11.0's unbound proof booleans with a closed proof status and exact public-record and
private-artifact digest projection. Complete construction is capture-only and checks snapshot,
workspace, packet, review, capture, freeze, adjudication, and fixture chronology. Verified-good and
hard-negative controls additionally require exact contracts and operations plus supplied successful
authorized project-workflow execution under a qualifying rootless-OCI capability; the generator
validates records and never executes project code. Hard-negative pattern and decisive-explanation
evidence resolve independently. Stage 3 replays the complete supplied proof, outcomes and metrics
bind the exact fixture digest/status, reports re-resolve bundled public proof inputs, and the
v0.11→v0.12 migration marks legacy evidence incomplete without inventing proof or metric authority.

Remaining limitation: the passing construction and replay evidence is synthetic. Private capture
artifacts are supplied separately to Stage 3 rather than embedded in public AuditBundles, and the
static report can therefore preserve their typed digest projection but cannot independently open
those private bytes. Reviewer authentication, real cross-provider independence, and a real
answer-blind corpus remain external qualification evidence.

## Project-execution authorization and effective-control gap

Public v0.12.0 can label an Execution `authorized` and a SandboxCapability `rootless_verified`, but
it cannot identify the exact authorization, effective backend probe, image, argument vector,
initiating WorkItem, purpose, policy values, resource observations, log artifacts, cleanup state,
or single-use scope behind those material premises. Generic references and extensions are not an
independently replayable authorization contract. The configured Docker Desktop daemon also does
not currently report rootless mode, so it cannot establish project-execution support.

Accepted
[ADR-0013](ADR-0013-AUTHORIZED-ROOTLESS-OCI-EXECUTION.md) and coordinated schema v0.13.0 add an
exact one-execution authorization record, evidence-bound effective capability probe, closed launch
envelope, structured execution provenance, fail-closed output capture, crash-safe single-use
consumption, and legacy migration. Its linked reproduction-segment rule now resolves the sequencing
conflict discovered during readiness review: the normative source run locks before selected
reproduction, authorization binds that immutable source lock, and a model-free linked lock binds the
resulting execution evidence before dependent detectors run. A second readiness correction binds a
locally managed Podman-machine identity instead of rejecting it as an anonymous remote, and requires
effective OCI/storage writable-space enforcement instead of treating post-hoc host-directory
counting as a limit. No published lock is mutated, copied public evidence is not launch authority,
and replay never relaunches the container or reuses authorization. Accepted ADR-0014 and schema
v0.14.0 supply the WorkItem correction and expose the bounded three-stage executor. sc-referee must
not manufacture clean execution evidence from Docker availability, v0.12 booleans, a restricted
subprocess, a plain writable bind mount, or repository text.

### Resolved project-execution WorkItem mismatch discovered in v0.13.0

The accepted v0.13.0 authorization requires an initiating WorkItem, but its immutable WorkItem
schema has no project-execution kind, fixes packet policy to `project_code_execution:false`,
requires model-prompt identities, and cannot name execution evidence among required outputs.
Reusing `auditor_owned_verification` would falsely identify project-authored execution.

Accepted [ADR-0014](ADR-0014-TYPED-PROJECT-EXECUTION-WORK-ITEM.md) and coordinated schema v0.14.0
add a closed non-model project-execution packet, awaiting-authorization state, exact
WorkItem-digest binding, and fail-closed v0.13 migration. The controller now exposes request,
fresh direct authorization, and one-use execution as separate commands.

### Blocking clean-control linked-evidence closure discovered in v0.14.0

Schema v0.14.0 can publish a linked execution lock containing the source WorkItem binding,
authorization, capability, exact Environment, Execution, logs, accepted outputs, identities, and
linked AuditRun. Its BenchmarkFixture proof projection, however, can bind only loose source
snapshots, reviews, scientific records, operations, Environments, Executions, and sandbox
capabilities. It has no field for the authorization, source WorkItem, linked AuditRun, linked
semantic-lock digest, or output/log Artifact and AssetIdentity digests. An Execution names output
record IDs but does not independently pin the meaning of records later supplied under those IDs.
Consequently v0.14 cannot make the full execution dependency closure an independently replayable
clean-control premise.

Deferred [ADR-0015](ADR-0015-LINKED-EXECUTION-EVIDENCE-CLOSURE.md) specifies a possible closed
linked-execution-evidence record, clean-control fixture proof, tighter project-workflow
authorization states, and fail-closed migration. Accepted ADR-0017 moves that work beyond the MPP
and did not schedule an execution schema. Accepted v0.15.0 is instead the unrelated static-proof
release. Linked execution evidence may be inspected and replayed but must
not qualify a clean-control fixture or promotion metric under v0.14.0.

### Blocking capability-probe origin and public-record admission gap in v0.14.0

The v0.14 capability command accepts any digest-pinned probe image, even though that image controls
the interpreter used to produce the purported auditor-owned probe result. The authorization command
then accepts a standalone canonical SandboxCapability JSON file. An immutable image or
self-consistent record proves identity and shape, not that the image is auditor-owned or that the
controller performed the probe. Direct human consent cannot establish those factual premises.

Deferred [ADR-0016](ADR-0016-TRUSTED-CAPABILITY-PROBE-ADMISSION.md) specifies a possible packaged
auditor-owned probe-image manifest and tool identity, fresh controller probe, inert standalone
public capability JSON, and fail-closed migration. Accepted ADR-0017 moves that work beyond the MPP
and did not schedule an execution schema. Accepted v0.15.0 grants no execution authority. The
v0.14 launch CLI remains test-only and must not execute
project-authored code.

### Resolved static qualification-control proof basis in v0.15.0

[Experiment 0023](EXPERIMENT-0023-STATIC-QUALIFICATION-PROOF-GAP-AUDIT.md) confirms that a complete
v0.14.0 `verified_good_fixture` or `hard_negative_fixture` cannot use
`execution_evidence: not_executed`. Both branches require clean project execution, while
`scope_verified_good` permits only bounded documented external execution. The evaluator enforces
the same boundary independently. Existing imported execution therefore cannot supply the
verified-good and hard-negative controls required to qualify a detector whose complete premise is
static.

[Accepted ADR-0022](ADR-0022-STATIC-CLOSED-SCOPE-QUALIFICATION-PROOF.md) and immutable public schema
v0.15.0 define distinct
`static_scope_verified_good` and `static_scope_hard_negative` kinds so existing clean-control
meaning is unchanged. A pre-case frozen profile binds the exact detector and an independently
implemented verifier; a typed proof rederives every material fact from immutable raw bytes and
uses derived dependency/chronology invariants rather than trusted booleans. Metrics and reports
remain stratified by control family. The isolated verifier, fixture construction, Stage-3
chronology, metrics, report replay, packaging, and fail-closed migration now pass synthetic and
mutation tests without executing project code. Answer-blind panel, threshold, and promotion gates
remain; implementation of the proof mechanism does not itself qualify or promote a detector.

### Resolved second static-profile representation gap in v0.16.0

Accepted ADR-0040 freezes `detector:bounded-analysis-method-conflict` over one exact report,
static-source, selected-output-writer, and human-review-requirement path. Its candidate wording
makes no execution or numerical-causality claim, so verified-good and hard-negative qualification
controls should use the accepted `static_closed_scope` proof family rather than manufacture a
project execution.

Immutable schema v0.15.0 cannot represent that proof. `StaticQualificationProfile` fixes the
target detector and verifier entry point to the earlier bounded mean-direction profile, while
`StaticQualificationProof.derived_facts` fixes the direction-specific CSV means, literal
orientation, and three-file dataflow shape. Reusing those fields, weakening them through
extensions, or labelling the ADR-0040 detector as the older detector would invent material
qualification evidence.

[Accepted ADR-0041](ADR-0041-SECOND-STATIC-QUALIFICATION-PROFILE.md) and immutable public schema
v0.16.0 add a separately discriminated `bounded_analysis_method_conflict_v1` profile and proof.
The evaluator independently enumerates strict-UTF-8 Markdown and Python candidates, rederives both
operands and the unique selected-output writer from full-digest bytes, and binds the exact scoped
Question, human Answer, ScientificContract, and accepted requirement assertion. Missing identity,
ambiguous writers or operands, unsupported dataflow, counterevidence, chronology drift, and byte or
inventory drift fail closed. The isolated verifier, fixture, Stage-3, report, storage, schema,
migration, packaging, and replay paths pass local synthetic and mutation controls without executing
project code.

Remaining limitation: local mechanism tests are not answer-blind cross-provider qualification.
ADR-0040 remains experimental, evaluation-only, and Finding-ineligible until the complete frozen
portfolio, metrics, and explicit maintainer promotion gate are satisfied.

### Resolved modular method-proof representation gap in v0.17.0

Accepted [ADR-0042](ADR-0042-MODULAR-METHOD-CHECK-EXTENSION-BOUNDARY.md) records that v0.16.0's
founder-specific binding, operands, and verifier entry point could not represent another method
check without rewriting public meaning. Immutable schema v0.17.0 replaces that branch with
`typed_static_method_conflict_v1`: one digest-bound check/detector/qualification-adapter binding,
one closed scalar/set/order relation, one or two explicitly required evidence planes, exact
independently retained declarations, human authority records, finite checks, and a permanent
no-Finding ceiling. Migration preserves v0.16 proofs only as namespaced historical evidence and
infers no generic binding or qualification.

The local implementation has an explicit packaged binding registry, generic detector dispatch,
isolated active adapter identities, an independent typed qualification engine, and a real
founder-orientation qualification adapter. Report-only, static-only second-language, and
step-order ambiguity/counterevidence controls exercise the extension boundary without changing
controller, storage, reporting, admission, or schema meaning. This resolves representation and
local mechanism only. Authenticated answer-blind cross-provider evidence, thresholds, promotion,
and Finding authority remain external and absent.

### Accepted v0.3 method-conflict promotion representation; installation gate remains

Accepted ADR-0060 and Experiment 0047 advance the generic contract-bound method-conflict detector
to version `0.3.0`, add an internal ReviewCase projection, and bind substantive registered
scientific checks to the unchanged closed comparison core. Historical schema v0.18.0 could not
encode its qualification or promotion without reusing the wrong v0.2 freeze.

Accepted schema v0.19.0 closes that representation gap with a v0.3 static profile, exact production
binding scope, content-addressed pilot-informed threshold policy, thresholded metric evidence, and
binding-level DetectorQualification. The complete-domain and dependence envelopes have retained
sealed qualification evidence, maintainer promotion decisions, and evaluation-private Round-2
records re-derived at current v0.19 pins. The fail-closed resolver validates those records only
against exact test-local pins.

The remaining gate is installation and public production authority, not schema representation or
held-out evidence. `qualification-manifests.json` and the installed `GRANT_PINS` mapping remain
empty, detector manifests remain experimental, and production bindings remain
`production_finding_permitted: false`. No production Finding can be admitted until a separate
maintainer decision installs exact grants and completes the remaining production release wiring.

## Resolved pre-snapshot AuditRun failure gap

Public v0.9.0 permits `created`, `cancelled`, and `failed_controller` records without a fabricated
snapshot reference. The controller creates its append-only journal before capture, and a dedicated
test verifies a schema-valid terminal record when snapshot capture fails.

## Rule

Historical provisional schemas remain under `provisional-schemas/` solely for migration evidence.
They are not production schemas. Future promotion requires:

1. an ADR;
2. public schema version bump;
3. migration notes;
4. record-union and audit-bundle integration;
5. examples and invariant tests.

The coordinated promotion contract and exact release version are documented in accepted
[ADR-0002](ADR-0002-OBSERVED-PLANE-PROMOTION.md). W3ID deployment remains a distribution gate;
the local release package does not claim that deployment occurred.
