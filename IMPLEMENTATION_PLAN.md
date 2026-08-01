# Updated implementation plan

## Status and authority

This document narrows the execution order in section 11 of the v0.5 architecture baseline. It does not change product semantics. It supersedes the broad “first prototype cut line” only for implementation sequencing.

## Phase 0 — Baseline and repository scaffold

Deliver:

- installable Python 3.11+ package;
- CI, linting, strict typing, and schema validation;
- canonical repository layout;
- architecture and schema baselines vendored under `reference/`;
- explicit temporary decisions for the six remaining nonblocking open items;
- schema-gap register for prose-defined but unpublished record types.

Exit gate: clean install and all starter tests pass from a fresh environment.

## Phase 1 — Executable walking skeleton

Implement one complete audit path only:

```text
snapshot
→ inventory
→ parse a Python file and Markdown report
→ load a resolved claim contract
→ link one claim to one observed scalar result
→ normalize comparison orientation
→ run one claim/result detector
→ apply the Finding admission gate
→ emit one MaterialQuestion and one Disclosure
→ persist canonical JSONL
→ rebuild SQLite
→ render offline HTML
→ replay without any model call
```

Required test cases:

1. Demonstrated direction contradiction.
2. Hard negative: raw coefficient sign appears contradictory but contrast orientation makes the report correct.
3. Unknown orientation: emits a question and no Finding.
4. Opaque operation: emits a Disclosure and does not invalidate unrelated downstream checks.
5. Forced deadline: returns a partial bundle and explicit coverage.
6. SQLite deletion and rebuild: no canonical information loss.
7. Semantic replay: normalized assessment records are byte-identical.

Exit gate: every case passes in CI and the HTML report counts each assessment type correctly.

## Phase 2 — Real controller and observed-computation records

Promote the provisional `AuditRun`, `StageResult`, `FileRecord`, `Operation`, `Artifact`, and `ObservedResult` shapes through a schema ADR and a public schema release. Replace fixture-only loaders with repository-derived records.

Implement:

- controller state machine;
- work queue and checkpoints;
- immutable snapshot and divergence monitoring;
- deterministic file inventory;
- Python AST/token extraction;
- Markdown claim-span extraction;
- local source-reference validation;
- generated SQLite graph index.

Exit gate: the walking-skeleton records are produced from source rather than preassembled fixture records.

## Phase 3 — Model-assisted semantic packets

Add Claude integration only for bounded tasks:

- final publication-surface candidate ranking;
- explicit claim extraction;
- proposed scientific semantics;
- material-question drafting.

All model outputs remain proposed evidence until controller validation. Model usage is host-managed and constrained by the audit wall-clock deadline, not by an auditor-imposed call or token quota.

Exit gate: locked records reproduce the same detector result with the model disabled.

## Phase 4 — Core detector expansion

Add detector families one at a time, each with positive, verified-good, hard-negative, ambiguous, unsupported, and counterevidence fixtures:

1. population/comparison/estimand mismatch;
2. denominator or control-set mismatch;
3. explicit dependence mismatch;
4. orientation/scale/timing mismatch beyond scalar direction;
5. lineage completeness.

Exit gate: no detector is exposed as validated before the qualification framework and pilot corpus exist.

## Phase 5 — Additional analysis surfaces

Add in this order unless implementation evidence suggests otherwise:

1. Jupyter notebooks;
2. Quarto and R Markdown;
3. R dual-parser path;
4. shell;
5. Snakemake;
6. Nextflow.

Parser failures must remain localized and create coverage records.

## Phase 6 — Runtime, caching, and authorized reproduction

Implement mode deadlines, applicability scheduling, content-addressed project-local caching, safe metadata readers, isolated dependency reconstruction, rootless OCI capability reporting, auditor-owned verification, and `ReproductionRequest` generation.

Full HPC job submission remains out of version one.

## Phase 7 — First named domain pack

Implement a narrow `profile-bulk-rnaseq` without changing the core record model. Support only declared package versions and operation forms for DESeq2, edgeR, and limma-voom.

## Phase 8 — Evaluation and qualification

Implement answer-blind GeneBench runners, cross-provider agent adjudication, fixture taxonomy, clustered metrics, capability-matrix generation, RO-Crate export, and public qualification reports.

## Stop conditions

Pause expansion and revise the architecture when any of these occurs:

- deterministic replay requires hidden model state;
- a hard negative becomes a Finding;
- source references cannot be resolved reliably;
- the ten-minute standard deadline is routinely missed before useful coverage;
- provisional observed-plane records cannot represent a real workflow without semantic overloading;
- two independent implementations interpret an accepted requirement differently.
