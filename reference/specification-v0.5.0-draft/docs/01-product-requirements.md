# 1. Product requirements

## 1.1 Requirement conventions

Each requirement has a stable identifier. Requirements describe the intended system; they do not imply that the capability has already been implemented.

Priority labels:

- **P0:** required for the first usable vertical slice;
- **P1:** required before a broad public beta;
- **P2:** desirable after the core system is validated.

## 1.2 Functional requirements

### Invocation and scope

**SA-FR-001 — Slash-command invocation (P0).** The system MUST provide a user-invoked `/scientific-audit` skill entry point in Claude Code.

**SA-FR-002 — Whole-project inventory (P0).** One invocation MUST inventory the entire project root, subject to explicit exclusions and security policy.

**SA-FR-003 — Notebook operation (P0).** The system MUST support auditing a notebook-centric workspace without requiring a conventional repository layout.

**SA-FR-004 — Publication-surface resolution (P0).** The system MUST resolve the final publication surface using explicit user or active-workspace selection, declared build targets, explicit task or repository statements, and unique lineage evidence in that order. Filename and modification time MAY support ranking but MUST NOT decide alone. If multiple materially plausible surfaces remain, the system MUST ask the scientist or preserve an unresolved scope conflict.

**SA-FR-005 — Selection envelope (P0).** Deep inspection MUST include all candidate-generating, filtering, thresholding, tuning, comparison, subgroup, and rejection decisions that could have selected a final reported result.

**SA-FR-006 — Narrow internal work units (P0).** Although invocation is project-wide, the controller MUST decompose work into bounded claim-, artifact-, operation-, or question-centered units.

### Languages and workflow surfaces

**SA-FR-007 — Initial language support (P0/P1).** The parser architecture MUST support Python, R, Jupyter, Quarto, R Markdown, shell, Snakemake, and Nextflow through versioned adapters. Python, R, Jupyter, Quarto, and R Markdown are P0; shell, Snakemake, and Nextflow are P1.

**SA-FR-008 — Unified operation IR (P0).** All parsers MUST emit a common observed-operation intermediate representation rather than detector-specific parse trees.

**SA-FR-009 — Opaque operation preservation (P0).** Unsupported or dynamically resolved calls MUST still be represented as opaque operations with known inputs, outputs, source locations, and trust properties where available.

**SA-FR-010 — Rendered report support (P1).** The system SHOULD extract claims and artifact references from rendered HTML. PDF support MAY be provided with explicitly weaker source precision when source documents are unavailable.

### Observed computation and lineage

**SA-FR-011 — Immutable observed facts (P0).** Static or runtime observations MUST be immutable within an audit run. Later scientific explanations may annotate but MUST NOT overwrite them.

**SA-FR-012 — Source precision (P0).** Every material operation, claim, assertion, finding, and lineage link MUST reference exact source locations appropriate to the medium.

**SA-FR-013 — Claim-to-computation lineage (P0).** The system MUST connect each final claim to the result artifact, producing operation, relevant decisions, input assets, and environment evidence or record a precise missing or opaque link.

**SA-FR-014 — Qualitative claim lineage (P0).** Qualitative claims such as model adequacy, robustness, enrichment, or absence of association MUST link to the diagnostics or results that support the wording.

**SA-FR-015 — Lineage grading (P0).** Lineage MUST be assessed separately for report origin, result origin, computational origin, input origin, execution origin, and semantic origin.

**SA-FR-016 — External and HPC evidence (P1).** The system MUST accept workflow traces, scheduler logs, manifests, checksums, environment records, and remote data identifiers when raw or intermediate data are not local.

### Scientific semantics

**SA-FR-017 — Scientific Contracts (P0).** Each material analysis or claim MUST have a Scientific Contract that represents the scientific meaning required for interpretation.

**SA-FR-018 — Core contract dimensions (P0).** Contracts MUST support target and analysis populations, unit of analysis, exposure or treatment, outcome, estimand, comparison, timing, scale and orientation, adjustment set, denominator or universe, control set, dependence structure, measurement model, missingness, transport, calibration, selection process, and uncertainty target as applicable.

**SA-FR-019 — Explicit causal semantics (P0).** The system MUST classify material claim intent as descriptive, associational, predictive, causal, or ambiguous and MUST support target estimands, identification strategies, treatment, outcome, target population, effect scale, time zero, adjustment-set roles, and optional causal structure without assuming that every analysis is causal.

**SA-FR-020 — Typed semantic states (P0).** Every material semantic dimension MUST be explicitly `known`, `unknown`, `conflicted`, or `not_applicable`.

**SA-FR-021 — Provenance-bearing assertions (P0).** Semantic meaning MUST be represented as fallible assertions with subject, predicate, object, semantic role, authority scope, epistemic status, evidence, source references, and provenance.

**SA-FR-022 — Hierarchical contract authoring (P1).** The authoring model SHOULD support study-, cohort-, analysis-, and claim-level inheritance. The locked form MUST materialize a complete contract for each claim.

**SA-FR-023 — Scientist questions (P0).** The system MUST ask only questions for which plausible answers can change detector applicability, assessment type, potential impact or publication materiality, root-cause grouping, or affected claims.

**SA-FR-024 — Answer persistence (P0).** Scientist answers MUST be persisted in editable JSON or YAML with respondent, timestamp when available, source, authority scope, and confidence or certainty description when available.

**SA-FR-025 — Conflict retention (P0).** When scientist intent conflicts with code, metadata, artifacts, or report text, the system MUST notify the scientist and retain both assertions. Scientist authority resolves intended scientific meaning but does not redefine observed execution.

### Claims and scientific issue detection

**SA-FR-026 — Structured claims (P0).** Report claims MUST be represented as structured propositions including subject, population, comparison, estimate or direction, magnitude, scale, uncertainty, time, and causal or associational wording when applicable.

**SA-FR-027 — Known issue classes (P0/P1).** The detector framework MUST support the known issue classes listed in the product charter. Initial P0 detectors SHOULD prioritize claim/result agreement, population or estimand mismatch, denominator or control mismatch, dependence or repeated measures, orientation/scale/timing assumptions, and lineage completeness.

**SA-FR-028 — Scientific risks requiring judgment (P0).** The system MUST be able to report scientifically plausible conditional risks that depend on domain judgment, provided the missing premise and resolving evidence are explicit.

**SA-FR-029 — Unsupported and unknown behavior (P0).** Unsupported operations, unknown semantics, unavailable execution evidence, opaque dependencies, and detector coverage gaps MUST be reported independently from scientific findings.

**SA-FR-030 — No open-ended model issue discovery (P0).** The production audit MUST NOT perform an open-ended language-model search for unspecified scientific errors. Future issue classes MUST enter through explicit coverage gaps, scientist reports, benchmark analysis, and validated deterministic detector development.

**SA-FR-031 — Detector manifests (P0).** Every detector MUST declare applicability, required records, accepted assertion classes, supported operations and versions, domains, assumptions, abstention rules, permitted output types, maturity, a finite counterevidence protocol, wording constraints, coverage rules, limitations, implementation digest, and tests.

**SA-FR-032 — Detector result states (P0).** Every scheduled detector-target pair MUST produce one explicit state: finding candidate, conditional-concern candidate, material-question candidate, disclosure candidate, no issue detected within coverage, not applicable, insufficient semantics, unsupported path, execution evidence unavailable, or detector error.

**SA-FR-033 — Counterevidence search (P0).** Before a candidate finding is admitted, the controller MUST perform and record every applicable check in the detector's finite, versioned counterevidence protocol. A decisive unavailable check MUST block finding admission.

**SA-FR-034 — Conservative admission gate (P0).** A Finding MUST satisfy all five admission conditions: direct entailment of the bounded statement, no unresolved fact that could reverse it, exact validated detector applicability, completed finite counterevidence protocol, and bounded wording reproducible from the semantic lock.

**SA-FR-035 — Evidence-bounded wording (P0).** Finding language MUST NOT assert a stronger conclusion than the admitted evidence supports.

**SA-FR-036 — Root-cause grouping (P0).** Findings MUST be grouped by causal root rather than textual similarity, with all materially affected descendant operations, models, artifacts, figures, tables, and claims enumerated.

**SA-FR-037 — Scientist disposition (P1).** A scientist MUST be able to record `confirmed`, `accepted_risk`, `disputed`, `not_material`, `deferred`, or `corrected_in_later_revision` without deleting the original evidence. Objective false-positive and detector-defect labels MUST be stored in a separate independent adjudication record.

**SA-FR-038 — No remediation selection (P0).** The system MUST NOT select or apply a replacement analysis as part of the audit.

### Coverage and reporting

**SA-FR-039 — Mandatory coverage record (P0).** Every completed or partial audit MUST produce a Coverage Record.

**SA-FR-040 — No correctness status (P0).** The system MUST NOT emit a global status equivalent to “correct,” “valid,” “safe,” or “publication ready.”

**SA-FR-041 — Human-readable output (P0).** The system MUST generate an HTML report with separate sections for demonstrated findings, conditional concerns, material questions, and disclosures, plus claim lineage, coverage, provenance, and performance.

**SA-FR-042 — Agent-readable output (P0).** The system MUST generate a canonical machine-readable audit bundle and normalized per-record JSON or JSONL.

**SA-FR-043 — Exact evidence package (P0).** Every Finding MUST include exact source locations, material premises, logical basis, detector applicability, completed counterevidence checks, explicit non-inferences, affected descendants, detector identity, and coverage limitations. No material premise may remain missing or conflicted.

**SA-FR-044 — Zero-finding wording (P0).** A report with zero admitted findings MUST still state the inspected scope, unresolved semantics, opaque boundaries, unavailable evidence, and detector coverage.

### Reproducibility and execution

**SA-FR-045 — Semantic lock (P0).** The controller MUST create a content-addressed semantic lock that fixes accepted assertions, unresolved unknowns, conflicts, publication scope, and detector inputs.

**SA-FR-046 — Model-free rerun (P0).** Given the same repository snapshot, semantic lock, detector implementations, and policy, detector execution, grouping, coverage calculation, and report rendering MUST rerun without Claude.

**SA-FR-047 — Static-first operation (P0).** Static inspection MUST precede and guide any execution.

**SA-FR-048 — Bounded selected reproduction (P1).** The system MAY perform safe inspection and auditor-owned verification automatically in a sandbox. Execution of project-authored code requires explicit authorization. It MUST NOT silently escalate to full workflow execution or HPC submission.

**SA-FR-049 — Execution provenance (P1).** Every executed command, dependency installation, and controller network retrieval that affects the audit MUST record the initiating work item, purpose, environment or destination, inputs, outputs, resource consumption, exit or retrieval state, and content identities or logs.

**SA-FR-050 — Data identity tiers (P1).** Data assets MUST record identity strength, distinguishing full digest, immutable external identity, manifest identity, weak fingerprint, and unidentified location.

### Runtime and iteration

**SA-FR-051 — Audit modes (P0).** The controller MUST support `quick`, `standard`, and `publication` policies with distinct scheduling cutoffs, user-visible hard deadlines, and enabled work classes. A run MUST NOT escalate mode automatically.

**SA-FR-052 — Hard deadlines and resource policy (P0).** Every audit MUST have a user-visible elapsed scheduling cutoff and hard deadline, sandbox and per-command limits, and data-read policy. Auditor-imposed model-call and token caps MAY be `null`; host subscription, organization, provider, and context limits remain authoritative.

**SA-FR-053 — Partial completion (P0).** On cancellation, timeout, tool failure, or budget exhaustion, the controller MUST preserve completed records and render a partial report with pending and uninspected work.

**SA-FR-054 — Incremental invalidation (P1).** The controller SHOULD cache content-addressed parse, extraction, semantic, lineage, and detector results and invalidate only affected descendants after a project change.

**SA-FR-055 — Progress visibility (P0).** The agent-facing interface MUST expose current stage, completed high-materiality targets, pending material questions, budget consumption, and major coverage gaps without flooding the user with low-level events.

### Integration and extensibility

**SA-FR-056 — Standalone CLI (P0).** The deterministic controller MUST expose a standalone CLI independent of Claude Code.

**SA-FR-057 — Typed tool API (P0).** The Claude integration SHOULD use a typed local tool boundary, preferably an MCP server, for starting audits, submitting assertions, recording answers, running detectors, and rendering reports.

**SA-FR-058 — Model provider boundary (P1).** Model-assisted extraction SHOULD be isolated behind a provider-neutral interface so that deterministic records and detector behavior do not depend on one model vendor.

**SA-FR-059 — Domain profiles (P1).** Domain-specific operation signatures, semantic extensions, and detectors MUST be packaged as independently versioned profiles.

**SA-FR-060 — Maturity declarations (P0).** Parsers, extractors, profiles, and detectors MUST declare separate maturity or validation status. Parsing support MUST NOT be described as scientific detector validation.

### Evaluation

**SA-FR-061 — Answer-key isolation (P0).** Production audit code and agent workspaces MUST not receive benchmark answer keys or graders.

**SA-FR-062 — Root-cause benchmark labels (P1).** Evaluation records MUST identify the first material scientific divergence and its affected descendants, rather than labeling only final answer correctness.

**SA-FR-063 — Correct-answer review (P1).** Evaluation corpora MUST include apparently correct final answers because invalid workflows can arrive at a correct result accidentally.

**SA-FR-064 — Verified-good fixture behavior (P0).** A `verified_good_fixture`, `scope_verified_good`, or `hard_negative_fixture` MUST produce zero Findings inside its declared negative scope, but MAY produce legitimate coverage, trust-boundary, or reproducibility Disclosures. No fixture label permits a global correctness claim.

**SA-FR-065 — Problem-level splits (P1).** Benchmark train, development, and test splits MUST separate scientific problems rather than randomly separating stochastic workflows from the same problem.

**SA-FR-066 — Distinct assessment records (P0).** The production data model and human report MUST use distinct `Finding`, `ConditionalConcern`, `MaterialQuestion`, and `Disclosure` records. Only `Finding` denotes a demonstrated issue.

**SA-FR-067 — Verified model extraction (P0).** A model-derived semantic assertion MAY support a Finding only when it extracts explicit meaning from an exact source span, is independently checkable, and has passed a non-model verification. Implicit scientific inference requires authoritative corroboration.

**SA-FR-068 — Type-specific impact language (P0).** Severity and publication materiality MUST be reserved for Findings. Conditional concerns, questions, and disclosures MUST use potential-impact, priority, or importance fields. User-facing numerical confidence probabilities MUST NOT be emitted in version one.

**SA-FR-069 — Disposition and adjudication separation (P0).** Scientist disposition MUST be stored separately from independent adjudication. A scientist may dispute a Finding but cannot create an objective false-positive label solely by declaration.


**SA-FR-070 — User-visible elapsed deadline (P0).** The hard audit clock MUST count model latency, tool and process queues, parser time, network retrieval, dependency installation, sandbox startup, command execution, and report rendering. Only time explicitly awaiting a scientist response MAY pause the clock, and no child deadline may exceed the remaining audit deadline.

**SA-FR-071 — Trial mode ceilings (P0).** Default trial cutoff and hard-deadline pairs MUST be 120/300 seconds for quick mode, 480/600 seconds for standard mode, and 1500/1800 seconds for publication mode. A resume action MUST create a linked run segment with a new plan rather than silently extending the original deadline.

**SA-FR-072 — Execution privilege levels (P0).** Automatic execution MUST be limited to safe inspection and auditor-owned verification. Project-authored Python, R, notebook, Quarto, Make, Snakemake, Nextflow, shell, package-build, or custom-binary execution MUST require explicit authorization and remain sandboxed.

**SA-FR-073 — No interactive HPC submission (P0).** Version one MUST NOT submit HPC jobs or automatically run a full workflow. When external execution could materially resolve an audit, the controller MUST emit a `ReproductionRequest` describing the target, evidence need, resource class, security constraints, and expected outputs.

**SA-FR-074 — Network separation and provenance (P0).** Claude MAY use the host-provided network without an auditor domain allowlist. The deterministic controller MAY retrieve external resources when it records purpose, requested and resolved location, retrieval time, content identity when obtainable, redirects, authentication use, cache state, and reproducibility effect. Repository-authored code requires separate explicit network authorization, and repository content MUST NOT grant it.

**SA-FR-075 — Isolated dependency reconstruction (P1).** Standard mode MAY install declared project dependencies automatically only in an isolated audit-owned environment. It MUST NOT mutate the user environment, use `sudo`, install system packages, or install the local project automatically. Unpinned reconstruction MUST be labeled approximate and MUST NOT establish exact version-dependent behavior without independent evidence.

**SA-FR-076 — Publication materiality under scope ambiguity (P0).** When the final publication surface is unresolved, candidate-specific demonstrated issues MAY be retained, but publication materiality MUST remain unassessed and the candidates MUST remain separate. The controller MUST NOT merge candidate reports into one headline audit.

**SA-FR-077 — Layered causal contract (P0).** Every explicitly causal claim MUST link to a typed causal contract that separates claim intent, target estimand, identification strategy and assumptions, covariate roles and timing, implemented estimator, and reported claim. Missing dimensions remain known, unknown, conflicted, or not applicable.

**SA-FR-078 — Causal-structure authority and scope (P0).** A causal graph MAY be absent or partial. Every supplied structure MUST declare `partial_open_world`, `complete_for_named_query`, or `closed_world` scope. Missing edges in an open-world graph are unknown, and a graph-dependent detector MUST ask, condition, disclose, or abstain when required structure is unavailable. Claude-generated causal relations MUST NOT support a Finding without authoritative corroboration or a validated bounded invariant.

**SA-FR-079 — Host-managed model usage (P0).** The default audit MUST impose no sc-referee-specific numeric limit on model calls or tokens. Usage MUST still be packetized, relevant, and recorded. Host usage, rate, context, or subscription exhaustion MUST produce a valid partial audit rather than a lost run.

**SA-FR-080 — External evidence records (P1).** An external resource that materially affects semantic resolution, package-behavior interpretation, detector applicability, or a Finding premise MUST have a durable `ExternalEvidence` record. A mutable live source MUST NOT silently become an unrecorded premise.

**SA-FR-081 — Environment reconstruction records (P1).** Every dependency reconstruction MUST produce an `EnvironmentReconstruction` record distinguishing exact, approximate, failed, timed-out, and skipped states and recording definitions, resolved versions, sources, isolation, and whether any prohibited installation class was attempted.

**SA-FR-082 — Public project identity (P0).** The public project, repository, primary distribution, and CLI MUST use `sc-referee`; the Python import namespace MUST use `sc_referee`; and the Claude action MUST remain invokable as `/scientific-audit`.

**SA-FR-083 — Canonical W3ID schema identifiers (P0).** Published schema `$id` values MUST use immutable versioned paths under `https://w3id.org/sc-referee/schema/`. A movable `latest` path MAY exist for human browsing but MUST NOT be persisted in audit records.

**SA-FR-084 — License and third-party provenance (P0).** Original code, schemas, documentation, templates, and original fixtures MUST be released under Apache License 2.0 with `LICENSE`, `NOTICE`, and machine-readable attribution where applicable. Externally derived benchmark or fixture material MUST retain source-specific provenance and MUST NOT be silently relicensed.

**SA-FR-085 — Tiered detector promotion (P0).** Experimental detector release requires maintainer review and required fixtures. Promotion to `validated` MUST require one software maintainer, a qualifying cross-provider agent adjudication panel, the non-negotiable promotion safety gates, and a public qualification report. Promotion to `publication-grade` MUST additionally require an independently assembled corpus or external replication and repeated qualifying adjudication. Agent-only, mixed, and human review bases MUST be disclosed distinctly; agent-only qualification MUST NOT be described as human expert review. Emergency demotion MUST be possible immediately.

**SA-FR-086 — Python runtime compatibility (P0).** The first public implementation MUST support Python 3.11 or newer and SHOULD test supported core packages across Python 3.11 through the currently supported CPython releases. Parser coverage for inspected source syntax MUST be reported separately from the controller runtime version.

**SA-FR-087 — Canonical record storage (P0).** Canonical audit records MUST be versioned JSON or JSONL. Safe YAML MAY be used for editable scientist answers and policy. SQLite MUST be a generated disposable index that can be rebuilt from canonical records without changing audit meaning.

**SA-FR-088 — Python parser stack (P0).** Python extraction MUST use CPython `ast` for semantic structure and `tokenize` for comments, literals, and token boundaries. It MUST NOT import or execute project modules. Syntax rejected by the running interpreter MUST produce localized partial or unsupported coverage rather than silent success.

**SA-FR-089 — R parser stack (P0).** R extraction MUST use Tree-sitter-R for resilient syntax inventory and, when R is available, an isolated helper using `parse(keep.source = TRUE)` and `getParseData()` without sourcing, attaching packages, or evaluating project code. Parser disagreement and unresolved tidy evaluation or dispatch MUST be recorded.

**SA-FR-090 — Static HTML renderer (P0).** The human report MUST be rendered deterministically from canonical records using a self-contained Jinja2 HTML template with explicit autoescaping and strict undefined-variable handling. Core content MUST remain readable without JavaScript and MUST use no required remote assets.

**SA-FR-091 — Sandbox capability contract (P0).** Project-authored execution MUST use a capability-reported rootless OCI backend that enforces read-only project mounts, separate writable audit roots, network denial by default, resource and process limits, restricted device access, and dropped capabilities. When no qualifying backend exists, project execution MUST be unavailable; a restricted subprocess MUST NOT be treated as an equivalent fallback.

**SA-FR-092 — Cache locality (P0).** All source-derived parser, semantic, model, detector, and report caches MUST remain project-local in version one and MUST NOT be shared across repositories. User-global caches MAY contain only tool-owned or public assets, public downloads, isolated dependency environments, and equivalent non-project-derived material.

**SA-FR-093 — Immutable snapshot under workspace mutation (P0).** A run MUST continue against its immutable initial snapshot when the live workspace changes, record `workspace_diverged`, and refuse to mix changed live content into that run. A linked follow-up run MAY reuse unaffected cached work.

**SA-FR-094 — Domain-neutral core slice and first domain pack (P0).** The first architectural vertical slice MUST exercise the complete evidence-compiler path on domain-neutral claim, lineage, population, comparison, denominator, orientation, scale, timing, question, coverage, and replay records. The first named scientific domain pack MUST be a deliberately narrow bulk RNA-seq differential-expression profile and MUST NOT define the general architecture.

**SA-FR-095 — Pinned cross-provider agent reviewers (P1).** Qualification adjudication MUST use at least two distinct model-provider families and independent execution contexts. Every review MUST record the exact model identifier, agent surface and version, reasoning configuration, prompt digests, tool-policy digest, environment digest, transcript digest, and blindness state. The initial reference pair is Claude Code using Claude Opus 5 and Codex using GPT-5.6 Sol, but historical runs MUST remain pinned and future reference models MAY change only through a versioned adjudication protocol.

**SA-FR-096 — Blind multi-run adjudication (P1).** A qualification case MUST receive at least four Stage-1 blind reviews, including two independent runs from each of two provider families, followed by at least two fresh Stage-2 scientific adjudications, including one from each provider family. Stage 1 MUST hide other reviews, sc-referee output, detector identity, benchmark grade, answer key, and adjudication notes. Stage 2 MAY use frozen Stage-1 rationales and answer-side evidence but MUST still hide sc-referee output and detector identity until the scientific label is frozen.

**SA-FR-097 — Conservative agent disagreement handling (P1).** Agent agreement MUST NOT be accepted as proof by itself, self-reported confidence MUST NOT affect labels, and simple majority vote MUST NOT override material disagreement. A positive label requires cross-provider agreement on the same bounded root cause plus deterministic evidence checks. A verified-good or hard-negative label requires completion of its positive proof obligations and no material dissent. Any unresolved material disagreement MUST place the case in an ambiguity or insufficient-evidence set, not a positive or verified-good set.

**SA-FR-098 — Benchmark fixture taxonomy (P1).** Evaluation records MUST distinguish `verified_good_fixture`, `scope_verified_good`, `hard_negative_fixture`, `positive_issue_fixture`, and `ambiguous_fixture`. Verified-good labels MUST state exact claim, detector, issue-class, operation, execution, and semantic scope. Hard negatives MUST document the superficially suspicious pattern and the decisive innocent explanation. Multiple materially different defensible implementations SHOULD be included when feasible.

**SA-FR-099 — RO-Crate export (P1).** Version one SHOULD export an RO-Crate 1.3 research object containing the native audit bundle, HTML report, source and data identity manifests, environments, detector manifests and qualification references, execution evidence, licensing, and authorship metadata. Native sc-referee records remain canonical and MUST be included unchanged; W3C PROV mapping is deferred until an identified interoperability consumer requires it.

**SA-FR-100 — Generated multidimensional capability matrix (P1).** Public capability claims MUST be generated from parser, profile, detector, qualification, and version manifests. Each entry MUST identify language, package and tested versions, operation scope, syntax recognition, operation extraction, semantic modeling, detector maturity, qualification basis, strongest permitted output, known gaps, abstention conditions, and inferred compatibility. A domain-wide support or validation claim MUST NOT be inferred from one entry.

**SA-FR-101 — Finding permission by detector maturity (P0).** Both `validated` and `publication_grade` detectors MAY emit Findings, but only inside their declared qualification envelope and only when the same five-part Finding admission rule is satisfied. `experimental` detectors MUST NOT emit Findings. Maturity changes the breadth of qualification evidence, not the logical standard or wording of a Finding.

**SA-FR-102 — Promotion safety gates before numeric thresholds (P1).** Before any detector is promoted beyond experimental, the qualification MUST demonstrate no known high- or critical-severity false accusation in release-blocking fixtures, exclusion of conditional and disputed cases from Findings, verified-good and hard-negative controls, decisive-counterevidence fixtures, problem-cluster-aware uncertainty reporting, separation of public development cases from qualification cases, a regression fixture for every discovered false accusation, exclusion of unresolved adjudication disagreement, and a public qualification report. Universal numeric promotion cutoffs MUST be set only after a pilot corpus through a separate threshold ADR.

**SA-FR-103 — Qualification-basis disclosure (P1).** Every detector manifest, capability matrix entry, qualification report, and public maturity claim MUST identify whether review was agent-only, mixed, or human. Agent-only review MUST name the participating provider families and exact pinned configurations and MUST explicitly state that it is not human expert endorsement.

## 1.3 Quality requirements

**SA-NFR-001 — False-accusation minimization.** Precision of demonstrated findings is the primary scientific quality objective. Uncertain cases MUST be represented as conditional concerns, material questions, disclosures, or abstentions rather than lower-confidence findings.

**SA-NFR-002 — Determinism.** Normalized deterministic outputs MUST be byte-equivalent for identical locked inputs, excluding explicitly non-semantic timestamps and transport metadata.

**SA-NFR-003 — Timeliness.** The default standard policy MUST stop optional scheduling after eight minutes and impose a ten-minute user-visible elapsed hard deadline, pausing only while awaiting a scientist response. This remains a trial service objective to be measured, not an unvalidated performance guarantee.

**SA-NFR-004 — Early value.** High-materiality claim contradictions and lineage failures SHOULD be evaluated before lower-value coverage expansion.

**SA-NFR-005 — Explainability.** Every admitted finding and abstention MUST be inspectable without relying on hidden model reasoning.

**SA-NFR-006 — Extensibility.** New issue classes, domains, operation signatures, and record extensions MUST be addable without changing the semantics of published record versions.

**SA-NFR-007 — Failure isolation.** A parser, detector, model call, or reproduction failure MUST not invalidate independent completed work.

**SA-NFR-008 — Security.** Static analysis MUST avoid executing project code. Safe inspection, auditor-owned verification, dependency reconstruction, and explicitly authorized project-code execution MUST use distinct privilege levels and sandbox policy.

**SA-NFR-009 — Portability.** The deterministic core SHOULD run locally and in remote or HPC-adjacent environments without requiring Claude Code.

**SA-NFR-010 — Auditability.** All accepted semantics, scientist answers, policy choices, tool versions, detector digests, and execution events MUST be retained in durable records.

**SA-NFR-011 — Accessibility.** The HTML report SHOULD be keyboard navigable, readable without color alone, and usable when scripts are disabled for core content.

**SA-NFR-012 — Interoperability.** The system SHOULD support export mappings to W3C PROV concepts and research packaging formats without making RDF the canonical internal store.

**SA-NFR-013 — Data minimization.** Model work packets SHOULD include only the source and metadata needed to resolve a target semantic question or claim.

**SA-NFR-014 — Testability.** Every detector MUST include positive, verified-good negative, ambiguous, unsupported-path, and counterevidence fixtures. Every parser MUST include malformed and opaque-construction fixtures.

**SA-NFR-015 — Stable identity.** Record and graph identities SHOULD be content-derived where practical to support incremental reruns and audit diffs.

## 1.4 Initial acceptance criteria

The first usable vertical slice is acceptable only when all of the following are demonstrated on representative repositories:

1. `/scientific-audit` initiates a project-wide inventory.
2. Python, R, Jupyter, Quarto, and R Markdown source locations are preserved.
3. The controller identifies or asks for the final publication surface.
4. At least one final quantitative claim is linked to its result and producing operation.
5. Scientific Contracts preserve known, unknown, conflicted, and not-applicable dimensions.
6. Scientist answers are persisted with authority scope and provenance.
7. At least four P0 detector families emit the expanded candidate, negative, abstention, unsupported, unavailable, and error states.
8. Experimental detectors cannot emit Findings, and every Finding passes all five admission conditions.
9. One root cause can list multiple affected claims without duplicate warnings.
10. A zero-finding report uses neutral evidence-and-coverage language and contains no pass badge or global risk rating.
11. Detector execution and report rendering rerun without a model from a semantic lock.
12. A forced timeout produces a valid partial report rather than losing the run.
13. Repository content cannot change audit policy through prompt-like text.
14. A verified-good fixture produces zero admitted issue findings.
15. A benchmark failure with an adjudicated root cause is localized to the relevant source path.
16. Conditional concerns link to material questions and are not counted as Findings.
17. Implicit model inference cannot become a material Finding premise without corroboration.
18. Scientist `disputed` status remains distinct from independent false-positive adjudication.
19. No production execution path invokes an open-ended LLM scientific-issue search.
