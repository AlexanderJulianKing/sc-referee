# 11. Implementation plan

## 11.1 Implementation philosophy

Build the complete architecture narrowly before broadening domains. The first vertical slice should exercise snapshot, inventory, parsing, claims, contracts, questions, semantic lock, detectors, coverage, and reporting end to end.

A broad collection of shallow detectors would be less valuable than a small number of conservative detectors running through the full evidence architecture.

## 11.2 Proposed repository layout

```text
sc-referee/
├── packages/
│   ├── sc-referee-core/
│   ├── sc-referee-parsers/
│   ├── sc-referee-profiles/
│   ├── sc-referee-claude/
│   └── sc-referee-eval/
├── schemas/
├── detector-fixtures/
├── benchmark-corpus/
├── docs/
├── examples/
└── pyproject.toml
```

The production dependency graph must keep evaluation answer-key code out of core and plugin packages.

## 11.3 Milestone 0 — Specification and package scaffold

Deliverables:

- ratified architecture decisions;
- stable `sc-referee`, `sc_referee`, and `/scientific-audit` identities;
- immutable W3ID schema namespace;
- core package interfaces;
- CI, formatting, type checking, and test harness;
- example audit directory layout; and
- threat-model tests for project-content prompt injection.

Definition of done: the Python 3.11+ packages install independently, dependency constraints are tested, and the existing semantic schemas validate in CI.

## 11.4 Milestone 1 — Control plane and snapshot

Implement:

- `AuditPlan`, `AuditRun`, `WorkItem`, `StageResult`, and `PerformanceRecord` schemas;
- user-visible deadline propagation and linked resume segments;
- immutable repository snapshot, live-workspace divergence detection, and file inventory;
- `AssetIdentity`, `ExternalEvidence`, and tiered large-file identity;
- project exclusions and external-root policy;
- stage checkpoints and partial output; and
- standalone CLI skeleton.

Definition of done: a forced timeout after inventory produces a valid partial bundle and coverage record.

## 11.5 Milestone 2 — Static observed graph

Implement first-class adapters for:

- Python;
- R;
- Jupyter;
- Quarto; and
- R Markdown.

Add `Operation`, `Artifact`, `AnalysisDecision`, `PublicationSurface`, `EnvironmentReconstruction`, `ReproductionRequest`, and `SelectionEnvelope` records. Build source references and a disposable SQLite query index. Python uses CPython `ast` plus `tokenize`; R uses Tree-sitter-R plus a non-evaluating base-R helper when available.

Definition of done: representative projects produce a deterministic lightweight graph with exact source spans and explicit opaque operations.

## 11.6 Milestone 3 — Claims, contracts, and semantic lock

Implement:

- report and notebook claim extraction packets;
- hierarchical Scientific Contract authoring;
- layered `CausalContract` authoring and graph-scope semantics;
- material-question calculation;
- editable answer records;
- scoped conflict resolution;
- source-reference validation; and
- content-addressed semantic lock.

Definition of done: the same locked records produce identical normalized outputs without a model.

## 11.7 Milestone 4 — First detector vertical slice

Recommended first detector families:

1. claim/result agreement;
2. population, comparison, and estimand mismatch;
3. denominator or control-set mismatch;
4. repeated-measures or explicit dependence mismatch;
5. orientation, scale, and timing mismatch; and
6. computational lineage completeness.

The architectural slice is domain-neutral and is first exercised end to end on one or two GeneBench-derived workflows plus synthetic fixtures. Immediately afterward, `profile-bulk-rnaseq` becomes the first named domain pack with deliberately narrow DESeq2, edgeR, and limma-voom operation envelopes. The domain pack must not define the core record model.

Definition of done: detectors have manifests and fixture classes, admission invariants are enforced, and root-cause findings enumerate affected descendants.

## 11.8 Milestone 5 — Reporting and Claude integration

Implement:

- self-contained autoescaped Jinja2 HTML report renderer;
- JSONL and bundle outputs;
- audit diff;
- `/scientific-audit` skill;
- local typed tool server;
- bounded subagents;
- batched material questions; and
- stage-level progress.

Definition of done: an end-to-end audit runs from slash command to report, can be interrupted safely, and can be rerendered from records alone.

## 11.9 Milestone 6 — Budgeting, caching, and sandbox reproduction

Implement:

- applicability indices;
- priority scheduler;
- user-visible scheduling cutoffs and hard deadlines;
- project-local content-addressed source-derived caches and restricted global tool-asset caches;
- dependency invalidation;
- safe metadata readers;
- execution privilege levels, sandbox capability records, and a rootless OCI project-execution backend with no unsafe fallback;
- isolated dependency reconstruction;
- controller network retrieval provenance;
- auditor-owned verification; and
- ReproductionRequest generation.

Definition of done: a changed report paragraph reuses unaffected work; quick, standard, and publication policies enforce their cutoff/deadline pairs; a hard deadline produces a useful partial report; dependency installation never mutates the user environment; and selected commands cannot write outside audit-owned roots.

## 11.10 Milestone 7 — Workflow systems and HPC evidence

Add shell, Snakemake, and Nextflow adapters, safe workflow-definition extraction, scheduler log ingestion, trace and manifest import, environment capture, remote-data identity, and external ReproductionRequest import/export. Version one does not submit scheduler jobs.

Definition of done: a workflow executed on an unavailable cluster can still receive a static lineage and coverage audit without pretending that unavailable execution was verified.

## 11.11 Milestone 8 — Domain profile expansion

Expand profiles in an evidence-driven sequence:

1. bulk RNA-seq;
2. single-cell RNA-seq;
3. association studies and GWAS;
4. variant calling;
5. survival analysis;
6. proteomics and metabolomics; and
7. imaging.

The exact order should follow benchmark coverage and expert availability. Each profile declares separate parsing, semantic, detector, and publication-grade maturity.

## 11.12 Milestone 9 — Evaluation and governance

Implement answer-blind GeneBench runners, workflow generation, cross-provider agent-review orchestration, Stage-1 and Stage-2 adjudication tools, deterministic disagreement and evidence checks, fixture taxonomy, clustered metrics, regression corpus, RO-Crate 1.3 export, generated capability matrix, detector promotion workflow, security disclosure process, and public qualification reports.

Definition of done: a release candidate has held-out verified-good and hard-negative evaluation, frozen cross-provider agent adjudications, false-accusation metrics with clustered intervals, runtime distributions, explicit review-basis disclosure, validated RO-Crate export, and publication-grade claims limited to independently replicated eligible components.

## 11.13 Testing layers

The implementation should include:

- schema and invariant tests;
- parser golden tests;
- graph reachability tests;
- semantic authority tests;
- detector fixtures;
- report count and wording tests;
- prompt-injection and sandbox tests;
- deterministic replay tests;
- incremental cache tests;
- end-to-end repository fixtures; and
- benchmark evaluation.

## 11.14 Engineering constraints

- The core should use strict type checking.
- Public record models should be versioned and serializable.
- Deterministic logic should avoid hidden global state.
- Model prompts and packet builders should be versioned and hashed.
- Source references should survive ordinary refactoring where stable cell or chunk identities exist.
- Parser failure must be localized rather than fatal to the run.
- Report prose should be template-controlled by evidence class.

## 11.15 First prototype cut line

The smallest useful prototype is:

- Python, R, Jupyter, Quarto/R Markdown;
- one publication surface;
- quantitative claims and basic qualitative claims;
- a domain-neutral core slice exercised on GeneBench-derived and synthetic fixtures;
- a separate narrow bulk RNA-seq profile immediately afterward;
- six detector families from Milestone 4;
- static mode plus trivial artifact verification;
- quick and standard budgets;
- machine bundle and HTML report; and
- deterministic rerun after lock.

Shell, workflow engines, broad domain coverage, publication-grade detectors, and remote execution follow after this vertical slice is stable.


## 11.16 Implementation-foundation gates

Before detector implementation, the core must enforce the `sc-referee` and W3ID identities, Apache-2.0 distribution policy, Python 3.11+ runtime, JSON/JSONL canonical storage, CPython AST/tokenize and dual R parser policies, static Jinja2 reporting, rootless OCI sandbox capability, project-local source-derived caching, immutable snapshot divergence behavior, durable detector-qualification infrastructure, and four assessment record types, five-part Finding admission, independently verified literal extraction, finite counterevidence, separate scientist disposition and adjudication, type-specific impact language, no production open-ended LLM issue search, user-visible deadlines, separated execution privileges, provenance-recorded external evidence, isolated dependency reconstruction, publication-surface precedence, and layered causal contracts.


## 11.17 Scientific qualification gates

Before any detector is described as validated, the implementation must support pinned `AgentReview`, `BenchmarkAdjudication`, and `BenchmarkFixture` records; four blind Stage-1 reviews across two provider families; two fresh Stage-2 adjudications with explicit falsification records; deterministic source and counterevidence checks; conservative exclusion of material disagreement; generated capability matrices; explicit agent-only, mixed, or human review-basis disclosure; verified-good controls and cleanly executed hard negatives with decisive innocent explanations; clustered uncertainty reporting; public qualification reports; and RO-Crate 1.3 export of native audit records.
