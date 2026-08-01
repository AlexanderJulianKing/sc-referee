# Initial acceptance criteria

These criteria define the first usable vertical slice. They are review gates, not evidence that the eventual product is scientifically validated.

- **AC-01 — Invocation and inventory.** `/scientific-audit` starts a run and inventories the whole in-scope project.
- **AC-02 — Source support.** Python, R, Jupyter, Quarto, and R Markdown source locations are preserved exactly.
- **AC-03 — Publication surface.** The controller identifies the final publication surface or asks one material question when ambiguity remains.
- **AC-04 — Claim lineage.** At least one final quantitative claim links to its result and producing operation.
- **AC-05 — Semantic states.** Scientific Contracts preserve known, unknown, conflicted, and not-applicable dimensions.
- **AC-06 — Answer provenance.** Scientist answers persist with authority scope and provenance.
- **AC-07 — Detector state completeness.** At least four P0 detector families emit candidates, negative-within-coverage, abstention, unsupported, unavailable, and error states.
- **AC-08 — Finding admission.** Experimental detectors cannot emit Findings, and every Finding passes all five admission conditions.
- **AC-09 — Root-cause grouping.** One root Finding can enumerate multiple affected claims without duplicate warnings.
- **AC-10 — Neutral clean report.** A zero-Finding report uses neutral evidence-and-coverage language and contains no pass badge or global risk rating.
- **AC-11 — Model-free rerun.** Detector execution and report rendering rerun without a model from a semantic lock.
- **AC-12 — Partial completion.** A forced timeout produces a valid partial report rather than losing the run.
- **AC-13 — Prompt-injection boundary.** Project content cannot change audit policy through instruction-like text.
- **AC-14 — Verified-good behavior.** A verified-good fixture produces zero Findings.
- **AC-15 — Root localization.** An adjudicated benchmark failure is localized to the relevant source path.
- **AC-16 — Assessment separation.** ConditionalConcerns link to MaterialQuestions and are never counted as Findings.
- **AC-17 — Model evidence eligibility.** Implicit model inference cannot become a material Finding premise without authoritative corroboration.
- **AC-18 — Disposition separation.** Scientist `disputed` status remains distinct from independent false-positive adjudication.
- **AC-19 — No open-ended LLM review.** No production execution path invokes an open-ended model scientific-issue search.
- **AC-20 — Counterevidence auditability.** Every Finding shows the applicable finite counterevidence protocol and the outcome of every check.
- **AC-21 — Type-specific impact.** Severity and publication materiality appear only on Findings; other assessment types use their own impact or priority vocabulary.
- **AC-22 — Coverage honesty.** Uninspected, unsupported, unavailable, and opaque paths remain visible and cannot be interpreted as negative results.
- **AC-23 — Deterministic record union.** Standalone and bundled schema validation use the same canonical referenced schemas.
- **AC-24 — Runtime budget.** Standard mode stops at its configured ceiling and renders completed and pending work.
- **AC-25 — Audit diff.** A localized source change invalidates and recomputes only affected descendants in a cache-warm run.
- **AC-26 — Quick deadline.** A forced quick run stops optional scheduling at 120 seconds and renders by the 300-second user-visible hard ceiling.
- **AC-27 — Standard deadline semantics.** Model and queue latency count toward the 600-second standard deadline; only scientist-answer wait pauses it.
- **AC-28 — Execution separation.** Safe auditor verification runs automatically while project code is blocked without explicit authorization.
- **AC-29 — Network separation.** Claude external retrieval succeeds while project-code network access remains denied by default.
- **AC-30 — External evidence provenance.** A material web or remote premise has a resolvable ExternalEvidence record and digest or version when available.
- **AC-31 — Isolated dependency reconstruction.** Automatic installation leaves the user environment unchanged and labels unpinned reconstruction approximate.
- **AC-32 — No HPC submission.** A material cluster execution need produces a ReproductionRequest and no scheduler submission.
- **AC-33 — Tiered identity.** A large unavailable or weakly identified asset limits only dependent lineage and detector conclusions.
- **AC-34 — Publication ambiguity.** Multiple plausible surfaces remain separated and publication materiality is unassessed until resolved.
- **AC-35 — No auditor model quota.** A run may exceed any illustrative call count but remains bounded by elapsed time and host capacity.
- **AC-36 — Host-limit partial result.** Simulated host model exhaustion yields a checkpointed partial report.
- **AC-37 — Causal contract requirement.** An explicitly causal claim lacks Finding eligibility until its CausalEstimand and IdentificationContract provide all material premises.
- **AC-38 — Graph scope.** A partial-open-world graph cannot establish absence of an omitted edge or adjustment-set sufficiency.
- **AC-39 — Causal authority.** A model-invented causal relation is rejected as a material Finding premise.


- **AC-40 — Public identity.** Distribution metadata, CLI help, schema package, and Claude adapter consistently use `sc-referee`, `sc_referee`, and `/scientific-audit` according to their defined roles.
- **AC-41 — Canonical schema namespace.** Every schema `$id` and `$ref` uses the immutable v0.5 W3ID namespace; no audit example persists a `latest` identifier.
- **AC-42 — License package.** Release artifacts contain Apache-2.0 `LICENSE` and `NOTICE` files and flag external benchmark derivatives for source-specific review.
- **AC-43 — Detector qualification.** A validated detector cannot be promoted without one maintainer, qualifying cross-provider agent adjudication, all promotion safety gates, and a public qualification report. Publication-grade additionally requires independently assembled or externally replicated evaluation. The review basis is disclosed.
- **AC-44 — Python compatibility.** Core tests pass on Python 3.11 and a newer supported CPython version, while parser syntax coverage is reported independently.
- **AC-45 — Storage rebuild.** Deleting and rebuilding SQLite from canonical JSON/JSONL produces byte-equivalent normalized deterministic outputs.
- **AC-46 — Python parser behavior.** A fixture is parsed through `ast` and `tokenize` without module import; unsupported syntax produces localized partial coverage.
- **AC-47 — R dual parsing.** Tree-sitter-R remains usable without R, and the isolated base-R helper adds source parse data without evaluating the fixture; disagreement is recorded.
- **AC-48 — Static report safety.** Jinja rendering escapes malicious project HTML, fails on missing required template fields, uses no remote assets, and remains readable without JavaScript.
- **AC-49 — Sandbox capability.** Project execution is denied without a qualifying rootless OCI backend and cannot fall back to a restricted subprocess.
- **AC-50 — Cache isolation.** A source-derived cache entry cannot be written to or restored from a cross-repository global cache.
- **AC-51 — Snapshot coherence.** Editing a live source file during a run marks `workspace_diverged`; the report and detector outputs continue to reference only the original snapshot.


- **AC-52 — W3ID release resolution.** Before a stable schema release, every versioned `https://w3id.org/sc-referee/schema/v0.5.0/` identifier resolves externally to the intended immutable schema, the redirect configuration revision is recorded, and no audit example persists a `latest` identifier.


- **AC-53 — Domain-neutral core slice.** The architectural vertical slice completes inventory through deterministic reporting without relying on bulk RNA-seq-specific record assumptions.
- **AC-54 — First named domain profile.** A narrow bulk RNA-seq profile declares exact DESeq2, edgeR, or limma-voom operations and gaps independently from the core.
- **AC-55 — Pinned blind agent reviews.** A qualification fixture has four valid Stage-1 reviews across two provider families, with all required blindness flags and exact model, prompt, tool, environment, and transcript identities.
- **AC-56 — Fresh falsifying Stage-2 adjudication.** A qualification fixture has at least two fresh Stage-2 adjudications, one per provider family. Each records the strongest innocent explanation, reversing premises, evidence tested, and outcome; neither has access to sc-referee output or detector identity before the label freezes.
- **AC-57 — Disagreement exclusion.** Injecting one unresolved material dissent prevents positive, verified-good, and hard-negative eligibility; majority vote cannot restore it.
- **AC-58 — Fixture proof obligations.** Verified-good, scope-verified-good, hard-negative, positive, and ambiguous examples validate their distinct proof obligations and prohibit global correctness claims. A hard negative also executes cleanly and records both the suspicious pattern and decisive innocent explanation.
- **AC-59 — Agent-only disclosure.** Qualification and capability outputs produced without human review explicitly state agent-panel basis and never use human-expert wording.
- **AC-60 — Capability matrix generation.** The public matrix is generated from manifests, identifies exact versions and gaps, and cannot emit a domain-wide support claim from one component.
- **AC-61 — Finding permission.** Experimental detectors cannot emit Findings; validated and publication-grade detectors can only within their qualified envelope and the identical five-part admission rule.
- **AC-62 — Promotion safety gates.** A promoted qualification record fails validation when any required safety gate is false, when agent-panel or mixed-panel adjudication is absent, or when its declared review basis contradicts its linked approvals.
- **AC-63 — RO-Crate export.** A valid RO-Crate 1.3 export contains the unchanged native audit bundle, report, identities, qualification references, licensing, and content digest.
- **AC-64 — Label-before-detector comparison.** Evaluation records prove that the scientific label was frozen before any Stage-3 reviewer or comparator received sc-referee output.
