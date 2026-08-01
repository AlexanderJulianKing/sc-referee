# 0. Product charter

## 0.1 Purpose

**sc-referee** is a coding-agent skill and deterministic audit system for inspecting a bioinformatics or statistical workflow in a project directory or notebook workspace. Its purpose is to identify and localize narrowly demonstrated scientific-analysis issues, preserve scientifically material unknowns, and disclose the boundaries of what the system could inspect.

The primary interaction is `/scientific-audit` in Claude Code or an equivalent Claude Science workspace. The deterministic core remains usable as a standalone CLI after semantic records have been created.

The product is for scientists who used a coding agent to create or modify an analysis and want a publication-oriented review of what the code and report actually do. It does not select or apply a replacement analysis.

### Project identity and lineage

The public project name is **sc-referee**. The repository, primary Python distribution, and CLI use `sc-referee`; the Python import namespace uses `sc_referee`. The user-facing Claude command remains `/scientific-audit` because it describes the action directly.

The name continues the identity of the original `sc-referee` prototype created for the Claude Life Sciences hackathon. This specification describes a rearchitecture: the original single-cell emphasis becomes a broader, conservative system for localizing subtle scientific-analysis mistakes across bioinformatics and statistical workflows.

## 0.2 Problem statement

A workflow can execute successfully and still answer the wrong scientific question. Common failures include:

- a reported claim disagreeing with the computed result or uncertainty;
- an outcome being used to choose a model, threshold, filter, or subgroup;
- use of the wrong population, estimand, adjustment set, comparison, denominator, background set, or controls;
- failure to identify a measurement or error model from the available data;
- omission of batch effects, nuisance variables, repeated measures, kinship, site, or other dependence;
- a global fit statistic hiding a group-specific offset or residual pattern;
- unsupported assumptions about label orientation, scale, timing, calibration, or a scientific invariant;
- ignored missingness, transport, measurement, or calibration uncertainty; and
- claims without complete computational and semantic lineage.

These failures depend on scientific meaning and relationships among task text, data, code, outputs, and report language. Ordinary linters, unit tests, and workflow engines do not generally detect them.

The known issue classes are not exhaustive. However, publication-critical review cannot safely delegate open-ended scientific error discovery to an LLM. Version one therefore handles the open world by preserving unknown semantics, unsupported operations, opaque boundaries, unavailable evidence, detector gaps, and uninspected paths. New issue classes enter production through explicit detector development and validation, not through free-form model suspicion.

## 0.3 Product goals

sc-referee will:

1. inventory an entire project while deeply inspecting final-claim paths and their selection envelope;
2. parse supported Python, R, notebook, document, shell, Snakemake, and Nextflow surfaces into one operation representation;
3. connect report claims to results, operations, decisions, inputs, environments, and scientific contracts;
4. represent scientific meaning as typed, provenance-bearing assertions with explicit unknown and conflict states;
5. ask the scientist only questions whose plausible answers can materially change the assessment;
6. apply versioned deterministic detectors with executable applicability and counterevidence contracts;
7. reserve `Finding` for demonstrated issues and use distinct records for conditional concerns, material questions, and disclosures;
8. group downstream effects under one graph-supported root cause;
9. create a semantic lock from which detection and reporting rerun without Claude;
10. enforce user-visible elapsed deadlines, never escalate mode automatically, and return a useful partial report when its deadline expires; and
11. expose detector, parser, lineage, evidence, and execution coverage without implying correctness.

## 0.4 Non-goals

sc-referee will not:

- certify that an analysis, manuscript, or scientific conclusion is correct;
- emit a global pass badge, publication-ready state, or risk score;
- search a repository with an open-ended LLM prompt for unspecified scientific mistakes;
- infer undocumented scientific meaning and silently treat it as fact;
- select, fit, or apply a replacement analysis;
- exhaustively symbolically execute arbitrary Python, R, shell, compiled code, or remote systems;
- silently run project-authored analysis code, submit an HPC job, run a complete workflow, or mutate the user's active software environment;
- equate successful execution with scientific validity;
- treat unsupported or unavailable paths as negative detector results; or
- hide uncertainty merely to make the report look complete.

## 0.5 Primary users

### Scientist who used a coding agent

The scientist needs a direct answer to five questions:

1. Which reported claims demonstrably require correction?
2. Which analysis choices could be problematic only under a stated unresolved condition?
3. Which scientific meanings must be clarified before review can continue?
4. Which claims lack complete lineage or reproducibility evidence?
5. Which parts of the workflow were unsupported, opaque, unavailable, or outside validated detector coverage?

### Analysis author or research software engineer

The author needs exact source locations, root-cause paths, machine-readable records, deterministic reruns, and stable audit diffs after code changes.

### Methodologist or reviewer

The reviewer needs bounded finding language, visible premises and non-inferences, detector maturity, finite counterevidence checks, coverage boundaries, and durable scientist responses.

### Detector developer

The developer needs explicit operation and semantic contracts, positive and verified-good fixtures, ambiguity cases, counterevidence cases, held-out evaluation, and strict promotion criteria.

## 0.6 Design principles

### P-001 — Evidence compiler

The system compiles source material through observed facts, proposed semantics, resolved semantics and unknowns, detector results, admitted assessments, and coverage records. No stage may be skipped.

### P-002 — Epistemic types, not badges

A demonstrated issue, a conditional possibility, an unanswered scientific question, and a coverage limitation are different record types. They are not one generic finding with different confidence labels.

### P-003 — “Finding” means demonstrated

A Finding is a narrowly worded issue that follows from the persisted evidence under a validated detector contract. If a knowledgeable scientist can accept every stored fact and still reasonably deny the exact sentence, it is not yet a Finding.

### P-004 — Unknown means unknown

Missing scientific meaning remains a typed unknown or conflict. It does not inherit a package default, model guess, naming convention, or convenient assumption.

### P-005 — Scoped authority

The scientist is authoritative about intended scientific meaning. Static and runtime observations are authoritative about realized computation. Report text is authoritative about what was written. These authorities can conflict without overwriting one another.

### P-006 — False-positive asymmetry

Falsely accusing a correct analysis is the most serious product failure. The system recovers usability through questions, conditional concerns, disclosures, and abstention rather than through a lower-confidence finding tier.

### P-007 — Claim-centric inspection

The whole project is inventoried. Deep semantic work follows final claims backward and includes operations that could have selected or shaped those claims.

### P-008 — Static first, execution by privilege level

Static inspection precedes execution. Safe inspection and auditor-owned verification may run automatically under policy. Project-authored code requires explicit authorization, and version one does not submit HPC jobs or silently run full workflows. Dependency reconstruction occurs only in isolated audit-owned environments.

### P-009 — Deterministic replay

After semantic lock, detector execution, admission, root grouping, coverage calculation, and report rendering run without an LLM.

### P-010 — Coverage is an output

Every audit states what was covered, partially covered, unsupported, unavailable, opaque, or uninspected. Absence of a finding has meaning only inside that envelope.

### P-011 — Root causes over warning floods

One root cause lists all materially affected claims, models, figures, tables, and decisions. Textually repeated symptoms do not inflate the finding count.

### P-012 — Extensibility through validated detectors

Future issue classes are developed from benchmark failures, scientist reports, and uncovered semantics. A production detector requires an applicability contract, finite counterevidence protocol, fixtures, evaluation evidence, and a maturity ceiling.

### P-013 — User-visible deadlines

The hard clock measures elapsed time visible to the scientist, including model, tool, queue, installation, and sandbox latency. Only time awaiting a scientist response pauses the clock. Quick, standard, and publication modes never escalate automatically.

### P-014 — Free inquiry, recorded evidence

Claude may use its host-provided network and tools to retrieve relevant evidence. The deterministic controller records any external resource that affects the audit. Repository-authored code has a separate network boundary and cannot obtain permission from repository text.

### P-015 — Causal layers, not invented graphs

Causal review separates claim intent, target estimand, identification assumptions, estimator implementation, and reported claim. A causal graph is optional and may be partial. Claude-generated causal structure cannot become a material Finding premise without authoritative corroboration.

### P-016 — Durable public identity

Canonical schemas use immutable W3ID identifiers under `https://w3id.org/sc-referee/schema/`. The descriptive `/scientific-audit` command is intentionally decoupled from package and repository identity.

### P-017 — Portable canonical records

JSON and JSONL are canonical. Editable scientist records may use safe YAML. SQLite is a generated, disposable query index whose deletion and rebuild cannot alter audit meaning.

### P-018 — Declared parser limits

Python parsing uses CPython `ast` plus `tokenize`; R uses Tree-sitter-R and a non-evaluating base-R parse helper when available. Parser failure, version limits, and disagreement are explicit coverage outputs.

### P-019 — Immutable run snapshots

Each run audits one immutable initial snapshot. Live workspace edits mark the workspace as diverged but never enter the current run. A linked follow-up run may reuse unaffected cached work.

### P-020 — Independent detector promotion

Detector authors may develop experimental components, but validated and publication-grade maturity require tier-specific independent scientific review recorded in a durable qualification report.

## 0.7 Success definition

Success is measured separately across:

- false-accusation rate on independently verified-good workflows;
- precision of demonstrated findings;
- recall and localization of adjudicated material root causes;
- correct conversion of unresolved premises into questions or conditional concerns;
- accurate affected-claim lineage;
- coverage honesty and abstention quality;
- deterministic replay and incremental invalidation; and
- user-visible elapsed time, resource use, and useful work completed before the configured deadline.

A workflow with zero findings is not considered proven correct. A gold workflow is expected to have zero demonstrated findings, while legitimate disclosures may remain if evidence is intentionally unavailable or opaque.

## 0.8 Initial scientific scope

The long-term profile surface includes general statistics, bulk RNA-seq differential expression, single-cell RNA-seq, statistical genetics and GWAS, variant calling, survival analysis, proteomics and metabolomics, and imaging.

Version one should prove the architecture with general statistical workflows and a deliberately narrow bulk RNA-seq profile before making publication-grade claims across every domain. Parser support, semantic-profile coverage, detector availability, detector validation, and publication-grade maturity are reported independently.
