# 3. Record model and evidence graph

## 3.1 Design objective

The record model must preserve three distinctions that scientific review commonly collapses:

1. what the workflow demonstrably did;
2. what the scientist intended and what the report stated; and
3. what the auditor can establish, conditionally infer, ask, or merely disclose.

Records are versioned, closed by default, source-indexed, and content-addressable. Published schema `$id` values use immutable versioned paths under `https://w3id.org/sc-referee/schema/`. Unknown and conflicted meanings are values, not missing fields.

## 3.2 Principal graph nodes

```text
ToolIdentity / AuditPlan / AuditRun / WorkItem / StageResult / PerformanceRecord / CachePolicy / StorageManifest / CacheEntry
RepositorySnapshot / ParserManifest / ParserResult / SandboxCapability / File / NotebookCell / DocumentChunk
DataAsset / AssetIdentity / Variable / Measurement
Operation / AnalysisDecision / Execution / Environment / EnvironmentReconstruction
ExternalEvidence / ReproductionRequest
Artifact / Result / Figure / Table / Report / PublicationSurface
ScientificContract / CausalContract / SemanticAssertion / SemanticUnknown / SemanticConflict
Claim / MaterialQuestion / Answer
DetectorManifest / DetectorResult
Finding / ConditionalConcern / Disclosure
ScientistDisposition / Adjudication / CoverageRecord
```

Edges include `reads`, `writes`, `derived_from`, `filtered_from`, `fit_from`, `selected_by`, `compared_with`, `renders`, `supports_claim`, `contradicts`, `implements_contract`, `identifies_asset`, `retrieved_as_evidence`, `reconstructs_environment`, `requests_external_reproduction`, `answers`, `blocks_detector`, `affects`, and `covered_by`.

## 3.3 Record families

### 3.3.1 Control plane

`AuditPlan`, `AuditRun`, `WorkItem`, `StageResult`, `PerformanceRecord`, and `CacheEntry` control scope, user-visible deadlines, scheduling, host-limit interruption, execution privilege, network policy, failure recovery, and incremental invalidation.

### 3.3.2 Observed computation and evidence acquisition

`RepositorySnapshot`, `FileRecord`, `DataAsset`, `AssetIdentity`, `Variable`, `Operation`, `AnalysisDecision`, `Artifact`, `Execution`, `Environment`, `EnvironmentReconstruction`, `ExternalEvidence`, `PublicationSurface`, and `ReproductionRequest` represent what exists, occurred, was retrieved, was reconstructed, or remains requested. These records never inherit authority from scientist intent or model interpretation.

### 3.3.3 Scientific semantics

`ScientificContract`, `CausalContract`, `SemanticAssertion`, explicit unknowns, conflicts, questions, and answers represent intended or interpreted scientific meaning. Each assertion has a semantic role, assertion class, authority scope, epistemic status, exact sources, provenance, and eligibility to support a Finding.

### 3.3.4 Claims, assessment, and exchange

The v0.5 schema baseline defines:

- `AuditPlan`;
- `RepositorySnapshot`, `ParserManifest`, `ParserResult`, `SandboxCapability`, `CacheEntry`, `PerformanceRecord`, and `DetectorQualification`;
- `AssetIdentity`;
- `PublicationSurface`;
- `ExternalEvidence`;
- `EnvironmentReconstruction`;
- `ReproductionRequest`;
- `ScientificContract` and `CausalContract`;
- `SemanticAssertion` and `Claim`;
- `DetectorManifest`, `DetectorResult`, and `DetectorQualification`;
- `Finding`, `ConditionalConcern`, `MaterialQuestion`, and `Disclosure`;
- `ScientistDisposition` and `Adjudication`;
- `AgentReview`, `BenchmarkAdjudication`, and `BenchmarkFixture`;
- `CapabilityMatrix` and `ROCrateExport`;
- `CoverageRecord`; and
- `AuditBundle`.

`Finding` is deliberately narrow. Conditional, unresolved, or informational items cannot be encoded as weaker Findings.

## 3.4 Record envelope and identity

Every record carries a schema version, stable identifier, audit-run identifier where applicable, provenance, and exact references to source or parent records. IDs should be content-derived when practical:

```text
operation:<file-digest>:<span>:<operation-kind>
claim:<report-digest>:<span>
artifact:<content-digest>
```

Content-derived identity supports stable diffs, cache reuse, and targeted invalidation. Human-authored IDs may be used where content identity is not appropriate, but alias and supersession history must be retained.

## 3.5 Source references

A source reference is a tagged location suitable for its medium:

- file path, content digest, and line-column span;
- notebook cell ID, execution count, and output selector;
- Quarto or R Markdown chunk label;
- workflow rule, process, or channel name;
- shell command and command span;
- HTML selector;
- PDF page and region with extracted-text digest;
- runtime command and output digest;
- artifact identifier; or
- immutable external URI and supplied digest.

A Finding cannot be admitted unless every cited source resolves against the snapshot or is explicitly marked external with adequate identity.

## 3.6 Observed operation intermediate representation

All parsers emit one operation IR. Core kinds include:

```text
read, write, parse, validate, join, filter, exclude, sample,
transform, normalize, calibrate, impute, aggregate, reshape,
select_feature, choose_threshold, choose_subgroup, choose_model,
fit_model, test_hypothesis, estimate, predict, diagnose,
resample, adjust_multiple_testing, render, export, opaque_operation
```

An operation contains input and output references, parameters, code span, package or tool identity, environment, determinism, and actual parser coverage. Unknown dispatch remains an opaque operation rather than disappearing.

## 3.7 Analysis decisions

An `AnalysisDecision` records a choice among alternatives, including candidate models, cutoffs, exclusions, contrasts, subgroups, tuning values, transformations, and stopping rules. It records the decision inputs, selection statistic, whether the reported outcome or favorable estimate influenced the choice, rejected alternatives, and downstream scope.

Decision records are essential to the selection envelope. A final model cannot be interpreted independently from outcome-dependent choices that produced it.

## 3.8 Data and artifact identity

Every material asset receives an `AssetIdentity` tier:

| Tier | Evidence | Typical use |
|---|---|---|
| Full digest | Complete cryptographic digest | Source, reports, ordinary tables, manageable outputs |
| Immutable external | Stable object or dataset version, preferably with supplied digest | Versioned remote data or containers |
| Manifest | Versioned manifest or per-file checksums | Large collections and HPC inputs |
| Weak fingerprint | Path, size, modification metadata, and sampled fingerprint | Large local assets when stronger identity is unavailable within deadline |
| Unidentified | Location or description only | Missing or inaccessible assets |

The controller operates under a byte-read policy rather than a universal file-size cutoff. Weak identity does not automatically imply a scientific defect. It limits only claims, lineage, or detector results for which exact identity is a material premise.

## 3.9 Semantic assertions and authority

A `SemanticAssertion` records subject, predicate, object, semantic role, assertion class, authority scope, epistemic status, source evidence, qualitative certainty with basis, and provenance.

Assertion classes include direct observation, explicit text extraction, implicit scientific inference, scientist declaration, metadata definition, deterministic derivation, and external declaration.

A model-derived assertion may support a Finding only when:

1. it extracts explicit source meaning rather than guessing undocumented scientific meaning;
2. it cites the exact source span;
3. the structured extraction is independently checkable;
4. a non-model validator records the check as verified; and
5. its authority scope matches the source, such as report text establishing reported wording rather than biological truth.

Implicit model inference—such as assuming `sample_id` means donor, guessing an effect allele, or assigning a covariate a causal role—requires metadata, task text, runtime evidence, or scientist corroboration before it can become a material Finding premise. Model confidence alone has no authority.

## 3.10 Scientific and causal contracts

A Scientific Contract describes the meaning needed to interpret an analysis or claim. The core dimensions are:

1. target population;
2. analysis population;
3. unit of analysis;
4. exposure or treatment;
5. outcome;
6. estimand;
7. comparison;
8. time definition;
9. scale and orientation;
10. adjustment set;
11. denominator or universe;
12. control set;
13. dependence structure;
14. measurement model;
15. missingness and transport;
16. uncertainty target; and
17. selection process.

Each dimension is `known`, `unknown`, `conflicted`, or `not_applicable`. Contracts may inherit at study, cohort, analysis, and claim levels during authoring; the semantic lock materializes one effective contract for each audited claim.

Every explicitly causal claim also links to a `CausalContract` with four layers:

```text
claim intent
  -> target estimand
  -> identification strategy and assumptions
  -> estimator and implementation
  -> reported claim
```

The estimand layer covers target population, unit, intervention or exposure, treatment strategies, outcome, comparison, effect measure and scale, time zero, horizon, effect type, censoring and competing events, interference, and transport. The identification layer covers strategy, adjustment set, estimand-scoped covariate roles, temporal ordering, exchangeability, positivity, consistency and treatment versions, and measurement or calibration assumptions.

A causal graph is optional. When supplied, it declares `partial_open_world`, `complete_for_named_query`, or `closed_world` scope. Missing edges in an open-world graph are unknown. A variable role is always scoped to a particular estimand; a global label such as “age is a confounder” is insufficient.

## 3.11 Material questions and answers

A `MaterialQuestion` is created only when plausible answers can change detector applicability, assessment type, potential impact, root grouping, or affected claims. It contains:

- the exact unknown;
- why it matters;
- evidence already searched;
- plausible answers, including `unknown`;
- blocked detectors;
- affected claims;
- priority and status; and
- linked conditional concerns.

When one plausible answer produces a specific material consequence, the controller creates a linked pair:

> **Question:** What does `sample_id` identify?  
> **Why it matters:** If it identifies biological donors, the fitted model appears to treat repeated donor measurements as independent.

The question and concern share one logical root and are not double-counted. Answers retain respondent, timestamp when available, source, authority scope, qualitative certainty, and conflicts.

## 3.12 Claims

A Claim stores the exact report text and a structured proposition: subject, population, comparison, estimate or direction, magnitude, unit, scale, uncertainty, time, and causal, associational, predictive, diagnostic, or recommendation strength.

Extraction records whether the proposition came from deterministic parsing, model-assisted explicit extraction, or human entry, and whether independent verification succeeded. The original text remains authoritative for what was reported.

## 3.13 Computational and semantic lineage

Lineage is graded independently across:

1. report origin;
2. result origin;
3. computational origin;
4. input origin;
5. execution origin; and
6. semantic origin.

A claim marked complete has no missing material links or opaque dependencies in the declared scope. Qualitative claims such as model adequacy must link to the diagnostics and decision rule used to support them.

## 3.14 Publication surface, external evidence, environments, and reproduction requests

A `PublicationSurface` record stores candidates, explicit precedence evidence, resolved or unresolved status, and whether publication materiality can be assessed. When scope is unresolved, candidate-specific Findings may exist, but their publication materiality is `unassessed` and candidates remain separate.

An `ExternalEvidence` record stores the requested and resolved resource, purpose, retrieval time, redirects, authentication use, cache state, content identity, version, reproducibility effect, and eligibility to support a Finding premise. Claude may retrieve freely through its host, but an external source that materially affects the deterministic audit must be persisted.

An `EnvironmentReconstruction` record distinguishes exact, approximate, failed, timed-out, and skipped reconstruction. Installation occurs in an audit-owned environment. Unpinned resolution is approximate and cannot establish exact version-dependent behavior without independent evidence.

A `ReproductionRequest` records external work the interactive auditor does not perform, especially full workflows or HPC jobs. It specifies the target, why it matters, required inputs and environment, resource class, security constraints, and expected output identities.

## 3.15 Opaque-boundary trust

Trust is multidimensional rather than Boolean:

- artifact identity;
- execution provenance;
- numerical correctness;
- scientific semantics; and
- reproducibility.

A proprietary or custom tool output may be accepted as an input artifact while its internal error model remains uninspected. The boundary propagates only to dependent claims and detectors that require the unavailable trust dimension.

## 3.16 Assessment taxonomy

| Record | Meaning | Impact language |
|---|---|---|
| `Finding` | Demonstrated, narrowly bounded issue | Severity and publication materiality when the final surface is resolved; otherwise materiality is unassessed |
| `ConditionalConcern` | Possible issue if an explicit unknown or conflict is true | Potential impact and review priority |
| `MaterialQuestion` | Unknown meaning that can change the audit | Question priority and blocked analyses |
| `Disclosure` | Coverage, lineage, opacity, availability, or reproducibility limit | Importance and interpretive consequence |

There is no public `supported` category, generic production hypothesis record, or user-facing numerical finding confidence. This prevents a high-severity speculation from looking like an established accusation.

## 3.17 Finding identity and grouping

A root Finding has a canonical key approximating:

```text
detector_id + causal_root_node_id + violated_semantic_dimension
```

It lists all graph-reachable affected claims, artifacts, models, and decisions with relationship paths. Text similarity alone cannot establish a common root.

## 3.18 Scientist disposition and adjudication

Scientists may record `confirmed`, `accepted_risk`, `disputed`, `not_material`, `deferred`, or `corrected_in_later_revision`. A factual answer can change the evidence graph and withdraw an item on deterministic rerun. A bare disagreement remains disputed.

Independent adjudication records `adjudicated_true_positive`, `adjudicated_false_positive`, `detector_defect`, or `insufficient_evidence`. Neither disposition nor adjudication deletes the original detector result or assessment.

## 3.19 Serialization and migration

Canonical records use JSON or JSONL; safe YAML is permitted for scientist-authored answers and policy. SQLite is generated and disposable. Published schema versions and versioned W3ID identifiers are immutable. A `latest` alias is never persisted into an audit bundle.

Schema 0.5.0 is intentionally breaking relative to 0.4.0 because it adds agent-review, benchmark-adjudication, fixture, capability-matrix, RO-Crate-export, and revised detector-qualification records. The W3ID namespace, epistemic taxonomy, runtime policy, causal model, and implementation-foundation records remain compatible in meaning.

## 3.20 Implementation-foundation records

### RepositorySnapshot

Records the immutable initial project view, Git and dirty-overlay state, content digest, file manifest, large-asset identity policy, and whether the live workspace later diverged. `workspace_diverged` never changes the snapshot contents.

### ParserManifest and ParserResult

A ParserManifest states backend, supported syntax versions, capabilities, implementation digest, and known limitations. A ParserResult records the exact source unit, parser state, emitted graph records, syntax issues, opaque constructs, secondary-parser linkage, and disagreement. Parser coverage is empirical output, not inferred from file extension alone.

### SandboxCapability

Reports the backend and controls actually available. Project-code execution support is true only for a verified rootless OCI backend satisfying the required mount, network, device, capability, process, and resource controls.

### CacheEntry

Records input digests, output references, dependencies, scope, and whether source-derived information is present. A source-derived entry must be project-local and non-shareable across repositories.

### PerformanceRecord

Records elapsed and paused time, model usage, I/O, cache behavior, stage timings, peak resources, and termination reason.

### DetectorQualification

Records requested and effective maturity, maintainers, review basis (`agent_only`, `mixed`, or `human`), pinned agent-adjudication references, optional human approvals, domain expertise, evaluation and independent-corpus references, promotion safety gates, disagreement, metrics, threshold policy, and the public qualification report. Cross-provider context separation and disclosure are controller invariants.

## 3.21 Provenance interoperability

The internal representation remains typed records and graph edges. Exporters may map entities, activities, agents, and derivations to W3C PROV and package research artifacts through RO-Crate or similar formats. Interoperability exports do not become the canonical internal store.


## 3.22 Evaluation and qualification records

### AgentReview

Records one isolated benchmark review, including stage, exact provider and model identifier, agent surface and version, reasoning configuration, execution-context identity, system and task prompt digests, tool-policy and environment digests, blindness state, reviewed scope, verdict, bounded statement, evidence, counterevidence, unresolved questions, transcript digest, and—at Stage 2—an explicit falsification attempt containing the strongest innocent explanation and reversing premises. Self-reported confidence is retained only as research metadata and is explicitly ineligible for labeling.

### BenchmarkAdjudication

Links at least four Stage-1 blind reviews and two fresh Stage-2 adjudications across at least two provider families. It records the protocol version, frozen reference configurations, cross-provider agreement, material dissent, deterministic evidence and falsification-completeness checks, per-provider participation, label eligibility, and an explicit agent-only or mixed-review disclosure. Majority vote is prohibited.

### BenchmarkFixture

Represents `verified_good_fixture`, `scope_verified_good`, `hard_negative_fixture`, `positive_issue_fixture`, or `ambiguous_fixture` with immutable snapshot, exact negative or positive scope, execution evidence, contract references, proof obligations, adjudication reference, known limitations, and a mandatory prohibition on global correctness claims.

### CapabilityMatrix

A release-generated record containing narrow capability entries by language, package, version, operation, semantic profile, detector, maturity, review basis, output ceiling, gap, and abstention condition. The record prohibits domain-wide support inference.

### ROCrateExport

Records an RO-Crate 1.3 export of a native audit bundle, including crate metadata path, contained record references, validation state, content digest, and generation provenance. The export does not replace the native canonical records.

### DetectorQualification revision

Qualification records distinguish agent-panel, mixed-panel, and human review bases. Agent adjudication references, optional human approvals, public review-basis disclosure, promotion safety gates, evaluation references, independent-corpus references for publication-grade promotion, metrics, and the deferred numeric-threshold policy are explicit.
