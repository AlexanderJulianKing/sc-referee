# 2. System architecture

## 2.1 Architectural thesis

sc-referee is an evidence compiler:

```text
project snapshot
  -> complete inventory and parser coverage
  -> observed computational graph
  -> bounded claim and semantic extraction
  -> resolved semantics, explicit unknowns, and conflicts
  -> content-addressed semantic lock
  -> deterministic detector results
  -> admitted Findings, ConditionalConcerns, MaterialQuestions, and Disclosures
  -> root-cause groups, coverage, and reports
```

Claude helps structure explicit report meaning, propose scientific contracts from bounded evidence, and interact with the scientist. Claude is not the finding authority and does not perform an open-ended production search for scientific mistakes.

## 2.2 System context

The principal inputs are task text, code, workflow definitions, notebooks, reports, local data or metadata, artifacts, logs, environments, scientist answers, and audit policy. The principal outputs are a machine-readable audit bundle, a human-readable HTML report, a semantic lock, source-indexed evidence records, and performance and coverage records.

The system treats repository content as untrusted evidence. It does not treat comments, README instructions, notebook prose, data values, or generated reports as instructions that may change audit policy or tool permissions.

## 2.3 Package model

### 2.3.1 `sc-referee-core`

A model-independent Python 3.11+ package containing schemas and generated models, snapshotting, inventory, parser adapters, operation IR, evidence graph, work planner, budgets, questions, semantic lock, detector registry, admission, root grouping, coverage, caching, report generation, and CLI.

The primary import namespace is `sc_referee`; component distributions, when published separately, use `sc-referee-*` names. `sc-referee-core` MUST NOT depend on a model SDK, Claude Code, or benchmark answer-side records.

### 2.3.2 `sc-referee-claude`

A thin integration package containing `/scientific-audit`, bounded extraction agents, typed local tool configuration, and interaction policy. All model output enters a proposed namespace and is validated by core APIs.

### 2.3.3 `sc-referee-profiles`

Independently versioned language, workflow, package, domain, and detector extensions. Each profile carries signatures, semantic roles, manifests, fixtures, validation evidence, and maturity declarations.

### 2.3.4 `sc-referee-eval`

A physically separate package for answer-blind workflow generation, runner-side grading, expert adjudication, detector qualification, benchmark analysis, and runtime evaluation. Production packages cannot import it.

## 2.4 Implementation foundations

### 2.4.1 Canonical storage

JSON and JSONL files are authoritative. Safe YAML is limited to editable scientist answers and policy. SQLite is generated from canonical records for recursive graph traversal, search, and report queries. Deleting and rebuilding the database must preserve normalized audit output.

### 2.4.2 Parser architecture

The Python adapter uses CPython `ast` plus `tokenize`. It prioritizes valid syntax accepted by the running parser and reports newer, malformed, or dynamic syntax as partial or unsupported coverage. It does not import project modules.

The R adapter combines Tree-sitter-R with an isolated non-evaluating base-R helper that calls `parse(keep.source = TRUE)` and `getParseData()` when R is available. The two parser results remain independently identifiable; disagreement, tidy evaluation, generated formulas, and dynamic dispatch remain visible.

### 2.4.3 Report rendering

A self-contained Jinja2 renderer converts canonical records into static HTML. Autoescaping and strict undefined-variable handling are mandatory. JavaScript is optional progressive enhancement; core content and source evidence remain readable without it.

### 2.4.4 Sandbox capability

Project execution is available only through a capability-reported rootless OCI backend. Auditor-owned verification may use a restricted subprocess because it executes versioned sc-referee code rather than project code. No subprocess-only fallback may be presented as project isolation.

### 2.4.5 Cache boundary

Project-derived cache remains under the project audit root and is never shared across repositories in version one. Global caches are limited to public or tool-owned assets, dependency environments, parser binaries, and pinned grammars.

## 2.5 Evidence planes

### 2.5.1 Observed computational and control plane

Represents ToolIdentity, AuditPlan, CachePolicy, StorageManifest, audit deadlines, repository snapshots, parser manifests and results, files, cells, chunks, workflow nodes, commands, reads, writes, filters, transformations, fits, tests, diagnostics, decisions, artifacts, inputs, outputs, environments, dependency reconstructions, sandbox capabilities, cache entries, asset identities, external evidence retrievals, and runtime traces. Observed records are immutable within an audit run.

### 2.5.2 Scientific semantic plane

Represents Scientific Contracts, Causal Contracts, assertions, unknowns, conflicts, scientist answers, populations, estimands, identification assumptions, comparisons, covariate roles, dependence, measurement, missingness, timing, scale, orientation, and selection semantics.

### 2.5.3 Claim plane

Represents exact report spans and structured propositions, including quantity, population, comparison, direction, scale, uncertainty, time, and causal or associational strength. Claims link to computational and semantic lineage.

### 2.5.4 Assessment and coverage plane

Represents detector manifests and results, demonstrated Findings, linked ConditionalConcerns and MaterialQuestions, Disclosures, root-cause descendants, scientist dispositions, independent production adjudications, agent benchmark reviews, benchmark adjudications and fixtures, capability matrices, parser and detector coverage, audit performance, and RO-Crate exports.

No plane may overwrite another. A mismatch among intent, realized computation, and reported wording is often the scientific issue.

## 2.6 Authority model

| Question | Primary authority | Rule |
|---|---|---|
| What was scientifically intended? | Scientist or explicit task text | Model proposals remain provisional unless they are verified literal extraction. |
| What code exists? | Locked repository snapshot | Content-addressed and immutable within the run. |
| What operation is realized? | Static or runtime observation | Opacity and actual coverage are preserved. |
| What output exists? | Artifact or execution evidence | Identity strength and environment remain attached. |
| What does the report say? | Exact report text | Clarification does not rewrite the original claim. |
| What does an undocumented variable mean? | Authoritative metadata or scientist | Naming conventions and model guesses are not facts. |
| How does the scientist respond? | Scientist disposition | May confirm, accept, dispute, defer, mark not material, or mark corrected. |
| Is a detector objectively wrong? | Independent adjudication | A bare scientist disagreement is not a false-positive judgment. |

A scientist answer resolves intent within its scope. It does not redefine realized computation. If the intended population is all eligible participants but the code analyzes complete cases, both remain and the mismatch can be assessed.

## 2.7 Model boundary

The model MAY:

- extract explicit claim wording from exact bounded source spans;
- propose Scientific Contract fields from bounded evidence packets;
- identify ambiguity and formulate a MaterialQuestion;
- explain the explicit conditional consequence of a plausible answer;
- map a parser-unresolved relationship when exact source evidence supports the mapping; and
- summarize canonical records without strengthening their meaning.

The model MUST NOT:

- roam through the repository looking for unspecified scientific mistakes;
- convert implicit scientific inference into authoritative meaning through confidence alone;
- mutate observed computation;
- admit, suppress, disposition, or adjudicate a Finding;
- decide that a finite counterevidence protocol is complete;
- hide unknowns, unsupported paths, or coverage gaps;
- invent absent lineage; or
- select or fit a replacement analysis.

A model-derived assertion may support a Finding only when it is explicit source extraction, tied to an exact span, independently checkable, and verified by a non-model mechanism. Variable roles, biological units, causal roles, timing rules, and scientific invariants require corroboration.

## 2.8 Publication surface and selection envelope

The publication surface is the report, notebook, manuscript, table set, figure set, or rendered artifact treated as the final source of scientific claims. Selection follows this precedence:

1. explicit user target or active Claude Science document;
2. declared final build or workflow target;
3. explicit task, project configuration, or repository statement;
4. unique direct report-generation and lineage evidence; and
5. filename and modification-time signals only as supporting evidence.

The controller auto-selects only when one candidate has materially stronger explicit evidence. If materially plausible candidates remain, it asks one batched MaterialQuestion. Inventory and safe parsing may continue while waiting. Without an answer, candidate audits remain separate and publication materiality remains unassessed.

The selection envelope includes every operation that could have selected, rejected, filtered, tuned, compared, or shaped the final result: model alternatives, thresholds, exclusions, feature selection, subgroup search, diagnostics used to change models, alternative contrasts, and outcome-dependent rejection decisions.

Whole-project audit means complete inventory plus relevance classification, deep inspection of final-claim backward slices, deep inspection of the selection envelope, and explicit disclosure of everything else. It does not mean sending every file through a model.

## 2.9 Audit state machine

```text
CREATED
 -> PLANNED_AND_DEADLINED
 -> SNAPSHOTTED
 -> INVENTORIED
 -> PUBLICATION_SURFACE_RESOLVED | PUBLICATION_SURFACE_UNRESOLVED
 -> STATIC_GRAPH_BUILT
 -> CLAIMS_EXTRACTED
 -> RELEVANT_SLICES_BUILT
 -> SEMANTICS_PROPOSED
 -> QUESTIONS_PENDING (optional; deadline paused)
 -> SEMANTICS_RESOLVED
 -> SEMANTIC_LOCKED
 -> VERIFIED_OR_REPRODUCTION_REQUESTED
 -> DETECTED
 -> ADMITTED_AND_GROUPED
 -> COVERAGE_CALCULATED
 -> REPORTED
 -> COMPLETE_WITHIN_PLAN | PARTIAL | FAILED_WITH_ARTIFACTS
```

Every transition creates a durable stage record. The scheduling cutoff stops new optional work; the hard deadline terminates eligible child work, checkpoints records, and renders a partial report. Partial is a normal terminal state when deadline, host model availability, evidence, or support boundaries prevent completion. A resume action creates a linked run segment and never rewrites the original elapsed-time history.

## 2.10 Semantic lock

The lock contains accepted assertions, explicit unknowns and conflicts, flattened effective contracts, structured final claims, scientist answers and authority scopes, publication scope, repository and policy digests, parser and extractor versions, detector inputs, and schema version.

After lock, detector execution, admission, grouping, coverage, and rendering run without Claude. Any material source, semantic, detector, or policy change produces a new lock digest and targeted invalidation.

## 2.11 Deterministic controller responsibilities

The controller:

- validates records and cross-record references;
- resolves source locations against the snapshot;
- enforces user-visible deadlines and propagates child deadlines;
- enforces execution privilege levels and dependency-isolation policy;
- records external evidence retrievals and environment reconstruction;
- resolves publication-surface precedence and unassessed materiality;
- enforces authority scope and model assertion eligibility;
- determines question materiality;
- schedules work under resource and elapsed-time policy;
- indexes detector applicability;
- runs finite detector-specific counterevidence checks;
- enforces causal-contract and graph-scope prerequisites;
- applies maturity and output permissions;
- applies all five Finding-admission conditions;
- checks wording against prohibited inferences;
- groups graph-reachable descendants;
- calculates actual coverage; and
- renders reports entirely from canonical records.

## 2.12 Storage architecture

```text
.sc-referee/
├── config.yaml
├── answers.yaml
├── dispositions.yaml
└── runs/<run-id>/
    ├── audit-plan.json
    ├── publication-surfaces.jsonl
    ├── asset-identities.jsonl
    ├── external-evidence.jsonl
    ├── environment-reconstructions.jsonl
    ├── reproduction-requests.jsonl
    ├── causal-contracts.jsonl
    ├── repository-snapshot.json
    ├── observed/*.jsonl
    ├── proposed/*.jsonl
    ├── resolved/*.jsonl
    ├── semantic.lock.json
    ├── detector-manifests/*.json
    ├── detector-results/*.jsonl
    ├── findings.jsonl
    ├── conditional-concerns.jsonl
    ├── material-questions.jsonl
    ├── disclosures.jsonl
    ├── dispositions.jsonl
    ├── adjudications.jsonl
    ├── coverage.json
    ├── performance.json
    ├── audit.json
    ├── audit.db
    └── report.html
```

JSON, JSONL, and safe YAML are canonical. SQLite is a generated graph and query index. Large text or artifacts may be content-addressed and referenced by digest.

## 2.13 Interfaces

The standalone CLI exposes staged commands such as `init`, `inventory`, `plan`, `extract`, `claims`, `questions`, `resolve`, `lock`, `verify`, `request-reproduction`, `import-evidence`, `detect`, `report`, `rerun`, and `diff`.

The Claude adapter uses equivalent typed local tools. The local tool layer is a façade over core APIs, not an alternate source of truth.

## 2.14 Deployment shapes

The default shape is local or SSH-adjacent. The repository snapshot is read-only; `.sc-referee/` and isolated audit-owned environments are writable. Safe inspection and auditor-owned verification use bounded sandboxes. Project-authored code requires explicit authorization. HPC analyses import traces, logs, manifests, checksums, and environment evidence; version one emits ReproductionRequests instead of submitting jobs.

## 2.15 Architectural invariants

1. No model assertion silently becomes an observed fact.
2. No implicit model inference becomes a material Finding premise without corroboration.
3. No unknown or conflict is converted to known for convenience.
4. No unsupported path becomes `no_issue_detected_within_coverage`.
5. No experimental detector produces a Finding.
6. No Finding retains a reversing unknown or incomplete decisive counterevidence check.
7. No uncertain item is counted or rendered as a Finding.
8. No scientist disposition erases evidence or creates an objective false-positive label.
9. No zero-finding report implies correctness.
10. No audit mode escalates automatically or exceeds its original user-visible hard deadline.
11. No project-authored code executes automatically, and no repository content grants execution or network permission.
12. No version-one audit submits an HPC job or silently runs a full workflow.
13. No unrecorded external resource becomes a material audit premise.
14. No model-invented causal relation becomes a material Finding premise.
15. No production path performs open-ended LLM issue discovery.
16. No production runtime imports benchmark answer-side code.


## 2.16 Evaluation architecture and trust separation

The `sc-referee-eval` package is answer-side and must remain dependency-isolated from production code. It owns workflow generation, blind agent assignments, answer-side evidence, benchmark labels, fixture records, qualification reports, and capability-matrix generation.

The initial qualification panel uses two model-provider families: Claude Code with Claude Opus 5 and Codex with GPT-5.6 Sol. Each exact run is pinned by model ID, agent version, prompts, tools, environment, and transcript. The model names may be updated only through a versioned adjudication protocol; historical records are immutable.

The evaluation flow is:

```text
workflow snapshot
 -> four blind Stage-1 agent reviews
 -> frozen review records
 -> two fresh Stage-2 scientific adjudications
 -> deterministic evidence and disagreement checks
 -> benchmark label or ambiguity exclusion
 -> frozen label
 -> Stage-3 detector comparison
 -> qualification report and capability matrix
```

Agent agreement is evidence, not authority. Material disagreement excludes a case from positive and verified-good labels. The production auditor never imports the label-building code or answer-side records.
