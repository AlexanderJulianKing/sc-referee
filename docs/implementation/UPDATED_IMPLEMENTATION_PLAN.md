# Updated implementation plan

## Status and authority

This document applies accepted implementation ADRs over section 11 of the immutable v0.5
architecture baseline. Accepted ADR-0017 defines the evidence-first `0.6.0` minimum proud product
(MPP) and moves built-in project-code execution beyond that boundary. It changes sequencing and
public capability scope without changing the meaning of any accepted record or schema.

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

Status: satisfied locally by accepted ADR-0002 and public schema release v0.6.0. Hosted CI and
W3ID deployment remain external gates and do not block the local Phase 2 implementation evidence.

## Phase 2.5 — General static product slice

Implement:

- an arbitrary-repository `audit` command that never executes project code;
- whole-repository inventory with safe Python and Markdown inspection;
- common observed Operation and Artifact promotion;
- explicit unsupported-parser, opaque-boundary, and detector-gap disclosures;
- publication-surface selection or a preserved material question;
- exact literal Claim extraction only from an explicitly selected supported report;
- draft all-unknown ScientificContracts and missing lineage for those literals; and
- model-free replay of the complete static lock.

Status: implemented locally for repositories with at least one fully identified publication-like
artifact. Accepted ADR-0003 now permits a truthful unavailable PublicationSurface and
CoverageRecord when no such artifact exists, without fabricating evidence or detector targets.
Active experiment 0002 also reconstructs one exact filtered mean-difference ObservedResult from
immutable Python/CSV bytes and binds only a uniquely aligned literal Claim with partial lineage.
Its exact source-level report flow now covers direct expressions, bounded module aliases,
zero-parameter straight-line renderers, a uniquely called single-result renderer, and a uniquely
called renderer with exactly one result plus constant-only positional presentation arguments. One
such argument may bind the output Artifact only through a direct safe relative string and an
unmodified `Path(parameter).write_text/write_bytes` receiver. Required positional parameters may
also be bound by exact non-positional-only keywords with complete duplicate-free binding. The
same source edge may cross one uniquely bound formatter only when it is the writer's direct payload
and contains exactly one bounded return expression, optionally followed by a strictly linear chain
of uniquely bound, uniquely consumed top-level assignments within the shared eight-edge ceiling.
The
measurement scale and project-execution edge remain unresolved; static dataflow never proves that
the report writer ran or produced the snapshotted bytes. No general-project detector is eligible in
this phase.

## Phase 3 — Model-assisted semantic packets

Add Claude integration only for bounded tasks:

- final publication-surface candidate ranking;
- explicit claim extraction;
- proposed scientific semantics;
- material-question drafting.

All model outputs remain proposed evidence until controller validation. Model usage is host-managed and constrained by the audit wall-clock deadline, not by an auditor-imposed call or token quota.

Exit gate: locked records reproduce the same detector result with the model disabled.

Implementation order:

1. define typed work-packet and proposed-record envelopes;
2. validate source references and prompt/work-packet digests;
3. add scientist Answer authority and immutable resume segments;
4. lock accepted semantics while preserving every unresolved dimension;
5. expose the same transitions through a typed local protocol; and
6. forward-test the repository-scoped Codex skill against fresh mixed-project fixtures.

Status: steps 1–6 are implemented by accepted ADR-0004 and public schema release v0.7.0 for
publication-surface selection and structured scientist resolution of bounded ScientificContract
dimensions. The process-isolated CLI round-trip passes, and an independent fresh-context agent
completed the mixed-repository question/proposal/answer/lock/replay path. A repository-contained
Codex plugin now packages that exact skill and passes local validators. The qualification
environment reports its user-scoped installation enabled with a byte-identical cache. Fresh-task
plugin discovery remains separate.

## Phase 4 — Core detector expansion

Add detector families one at a time, each with positive, verified-good, hard-negative, ambiguous, unsupported, and counterevidence fixtures:

1. population/comparison/estimand mismatch;
2. denominator or control-set mismatch;
3. explicit dependence mismatch;
4. orientation/scale/timing mismatch beyond scalar direction;
5. lineage completeness.

Exit gate: no detector is exposed as validated before the qualification framework and pilot corpus exist.

## Phase 5 — Additional analysis surfaces

Current bounded source-connectivity status:

1. ✅ Jupyter nbformat-v4 cell/output inventory under ADR-0034;
2. ✅ R Markdown front matter/prose/fenced-R-chunk inventory under ADR-0021;
3. ✅ dual non-evaluating `.R` syntax/call inventory under ADR-0033;
4. ✅ Quarto front-matter/prose/literal-engine-cell inventory under ADR-0035;
5. shell;
6. Snakemake;
7. configured Nextflow beyond the existing default-trace importer.

The completed items are inventory boundaries, not general language or workflow support. Notebook
and Quarto cell operations/Claims, R dataflow/formulas, rendering, and runtime semantics remain
unavailable.

Parser failures must remain localized and create coverage records.

## Phase 6 — Bounded evidence acquisition, caching, and external reproduction requests

Implement mode deadlines, applicability scheduling, content-addressed project-local caching, safe
bounded metadata and data readers, auditor-owned verification, existing log/trace/output import,
and inert `ReproductionRequest` generation. Large or unavailable data must narrow only dependent
conclusions; samples and fingerprints never become exact verification.

Accepted ADR-0017 makes the production MPP non-executing. It does not install project dependencies,
run project-authored code, or submit HPC work. Accepted ADR-0013/v0.13 and ADR-0014/v0.14 remain
immutable descriptions of a possible future execution boundary, but their executor is disabled and
synthetic-test-only. Deferred ADR-0015 and ADR-0016 are not a scheduled v0.15.0 schema release.

Status: deadlines, bounded tiered identity, project-local caches, safe static environment readers,
auditor-owned verification, and inert ReproductionRequests are implemented locally. An end-to-end
regression audits and replays a project containing a 10-billion-byte sparse data asset after reading
only 12,288 sampled bytes, without copying the asset or executing embedded project code. Experiment
0008 also imports a closed root-level SHA-256 checksum-manifest profile as repository-declared
identity evidence, with exact line provenance and without claiming that the target bytes were
verified. Malformed, ambiguous, nested, and over-budget candidates fail locally. Broader
input/output metadata readers and broader external log/trace import remain incomplete. Experiment 0009
adds exact header-only CSV/TSV inventory for fully captured files, preserving static input/output
edges only when unambiguous while leaving rows, storage types, runtime use, and scientific meaning
unknown. Experiment 0010 imports one exact default Nextflow `trace.txt` profile as weak external
terminal-task assertions; it withholds authenticity, commands, input/output lineage, runtime and
sandbox identity, Claim binding, clean-control use, and Finding authority.

## Phase 7 — First named domain pack

Implement a narrow `profile-bulk-rnaseq` without changing the core record model. Support only declared package versions and operation forms for DESeq2, edgeR, and limma-voom.

## Phase 8 — Evaluation and qualification

Implement answer-blind GeneBench runners, cross-provider agent adjudication, fixture taxonomy, clustered metrics, capability-matrix generation, RO-Crate export, and public qualification reports.

Experiment 0023 confirms that accepted v0.14.0 cannot admit complete non-executing verified-good
or hard-negative controls. Accepted ADR-0022/schema v0.15.0 now implements distinct static control
kinds, a pre-case frozen detector/verifier profile, independent raw-byte rederivation, derived
graph/chronology invariants, and proof-family-stratified metrics. Synthetic mechanism and mutation
tests pass without executing project code. This creates a proof path, not qualification or
promotion authority: real answer-blind cross-provider cases, pilot-informed thresholds, and an
explicit maintainer promotion decision remain mandatory.
Experiment 0024's independent implementation review exposed and verified fixes for snapshot-
candidate deletion and selection-protocol mismatch, so neither can strengthen a proof.

Experiment 0025 separates capability development from qualification. Its inner loop requires
positive, verified-good, ambiguous, and hard-negative mechanism controls; its middle loop freezes,
audits, replays, and only then grades newly generated answer-isolated workflows; and its outer loop
retains authenticated cross-provider review for a later frozen candidate. A shared scientific-
check module may follow only from a recurring abstract obligation with a complete scope join and
must contain no GeneBench identity, answer, path, repository name, or expected number. The first
recurrence batch targets measurement/calibration while retaining LD-aware MVMR as a covered-good
guard. Experiment 0025 admits only the recurring poststratified-misclassification estimator choice
as a question-only check; the four Experiment 0016 source probes remain evaluation-only.

Status: the isolated answer-side package now implements the synthetic 4+2 scientific-label
chronology, immutable evidence admission, accepted Stage-3 candidate/root equivalence, exact
per-DetectorResult opportunity projection, and all twelve accepted deterministic point estimates
plus problem-cluster bootstrap intervals under public schema v0.15.0. Reports independently
recompute metric evidence and disclose agent-panel review without human-expert wording. Accepted
schema v0.12.0 additionally binds eligible fixtures to exact public records and private capture,
packet, transcript, workspace, snapshot, freeze, and chronology evidence. Synthetic positive,
verified-good, scope-verified-good, and hard-negative construction plus Stage-3 proof replay now
pass locally. Accepted v0.15.0 adds independently replayed static-scope verified-good and
hard-negative construction and preserves separate proof-family strata. Real answer-blind corpus
evidence, authenticated external reviewer independence,
calibration, evidence-backed detector capability population, thresholds, and any detector
promotion remain incomplete. Experiment 0007 now generates the public capability matrix from a
closed five-collection release-manifest set. The bundled result deliberately contains only narrow
Python, Markdown, delimited-header, and default Nextflow-trace component profiles plus Experiment
0011's exact cross-profile experimental detector. No detector qualification or tested/inferred
version claim exists.
Experiment 0006 now supplies deterministic attached RO-Crate 1.3 export of integrity-verified
native audit records and reports plus an offline bounded-profile validator; third-party validation
remains unclaimed. An evaluation-private GeneBench-Pro public-package preflight now verifies a pinned
manifest, checksum inventory, runner/agent split, and public-development ceiling without executing
the grader or disclosing answers. The full official initial revision now passes all 77 hashes with
consistent CC-BY-4.0 identifiers; the current MIT-labelled head is rejected for stale LICENSE and
README hashes. Experiment 0012 now prepares one exact Hi-C case workspace containing only task and
staged data while retaining ground truth, config, grader, reference report, snapshot material, and
receipts runner-side. An authorized fresh-context agent produced a byte-reproducible but incorrect
workflow; its frozen audit localized no issue, and Experiment 0013 canonically records all three
answer fields outside tolerance without executing the workflow or grader. This exposes two bounded
requirements captured by accepted ADR-0018: deterministically project exact
question/method evidence from named v0.14.0 records so unresolved analytic choices can produce
non-accusatory questions, and compare reported methods with separately verified authoritative
obligations when such authority exists. The first slice is only the expected/background profile;
pre-analysis contracting uses a distinct claimless mode rather than the existing audit lifecycle.
The hidden public answer/report cannot become production detector input, and no external
authenticated review has run. That first slice is now implemented: the claimless CLI and separate
Codex skill freeze a human-authorized six-dimension profile, later Claim contracts bind its exact
parent lock and unchanged task identity, and the experimental detector covers exact conflict,
covered-negative, ambiguity, unsupported, and finite-suppressor states. Experiment 0014's real
pre-answer GeneBench rerun emits one governing-background question with zero Findings; its isolated
post-lock diagnostic localizes the public-reference conflict without altering production or
becoming metric/promotion evidence. Experiment 0015 reuses the same isolation boundary for three
additional cases: one LD-aware MVMR covered-good result, one directional measurement-error miss,
and one coupled calibration/standardization miss. The evaluation grader now supports only the two
additional exact package contract shapes needed by that pilot. Each failure family still has one
case. Experiment 0016 adds four closed evaluation-only AST probes that localize the exact submitted
source shapes, recognize corrected controls, and preserve unrelated code as unsupported. Fixed-case
numeric ablations recover the released answers after the proposed repairs, but these answer-side
profiles remain outside production manifests. No new method profile, detector, metric, or promotion
claim follows. Experiment 0017 then applies all four profiles to three authorized fresh-context
follow-ups. All twelve checks remain unsupported rather than being force-fit to unrelated errors.
The new workflows miss answer fields through three different one-case method families, so no new
profile or promotion claim follows; the result narrows the next evidence search to recurrence or
a scope-specific requirement established by authoritative repository evidence or a scientist
Answer. Qualification remains external and incomplete.

Experiment 0018 completes the ten-case public-development sweep. The final QTL, CRISPRi/CasRx,
and pulse-admixture workflows all grade outside contract, while every application of the four
existing source profiles remains unsupported. Only one of ten workflows is wholly within its
answer contract. The next milestone is therefore not another answer-key-derived detector: propose
an interactive post-hoc method ledger for existing analyses using the v0.14.0 ScientificContract
dimensions, exact repository evidence, and scope-bound scientist Answers gathered before semantic
lock. Compare only closed values, sets, and step order; preserve unsupported implementation paths
and unanswered questions as unknown. Validate it by re-auditing existing failed workspaces plus
unknown, conflict, false-self-compliance, and covered-good controls before changing production
capability claims. The separate pre-analysis `method-contract` remains an optional preventive
companion, not a prerequisite. Record the behavior and authority change in an ADR; add no schema
unless a concrete value cannot be represented without overloading an existing dimension.
Accepted ADR-0019 governs this implementation cycle.

Experiment 0019 implements the first bounded slice of that decision. The controller now records
closed scientist Answers, preserves explicit unknowns, and deterministically projects exact value,
set, or step-order compatibility through `posthoc_method_ledger_v1`. Evaluation-only AST profiles
over the existing fixed workspaces produce review-scoped conflicts for QTL founder orientation and
pulse-admixture exposure, a covered negative for LD-aware MVMR, and an unresolved CRISPRi/CasRx
method with no invented dimension. These results execute no project code and change no production
capability claim. The false-self-compliance control now passes. Experiment 0020 also completes the
fresh-context skill usability run: audit transport, integrity, conservative interpretation, and
replay pass, but the ordinary raw repository produces no bounded method question because it has no
extracted Claim or contract. Accepted revised ADR-0020 responds with a modular scientific-check
registry that separates method obligations from language/tool adapters and reuses one analysis-
scoped question lifecycle. QTL, pulse-admixture, MVMR, and a removable conformance module now pass
through the same interface. This is not broader Claim extraction or detector promotion. Registry
isolation, manifest drift, hard negatives, role mutation, arbitration, interaction, reporting, and
replay tests pass. Independent fresh-context broad-design review reports no architectural blockers
after revision 2 added a normalized adapter observation, pure reducer, sibling isolation,
capability-limited inputs, actual source subject, typed source-to-analysis join, and schema-gap
stop. A second answer-blind QTL skill run now reaches one exact scientist question with zero
Findings and stops for human authority. The repository owner then selects repair-before-emission;
the linked segment records the structured Answer, produces one exact review-scoped incompatibility
Disclosure with zero Findings, and replays with the same semantic identity and assessment counts.
The ADR-0019/ADR-0020 interaction validation milestone is complete. Experiment 0021 also completes
the first independent non-GeneBench false-applicability screen: six commit-pinned QTL and robust-MR
repositories produce no false question or Finding and replay deterministically. Accepted ADR-0021
and Experiment 0022 then provide the first positive external connector validation. The bounded R
Markdown inventory, MVMR `gencov` method adapter, and exact selected-Artifact scope join recognize
zero covariance in two independent applied repositories and transport one unresolved
sample-overlap question through the ordinary skill. Display-only code remains not applicable, a
mixed public vignette remains ambiguous, and an evaluator-owned mutation proves the provided-
covariance branch. The selected report is now prioritized within the unchanged snapshot byte
budget. No path executes project code, emits a Finding, qualifies a detector, or establishes the
missing sample provenance. The next scientific-check expansion must again begin from an
independently recurring representation rather than looser matching or general R parsing.

Development now follows Experiment 0025's two-corpus discipline: frozen prior failures are the
regression corpus, and newly generated answer-isolated workflows are the development challenge
corpus. Run targeted cases while a capability is changing and a complete ten-case sweep only at
stable checkpoints. A wrong answer with a different cause is a negative recurrence result, not
permission to widen a grammar. Independent reviewer qualification begins only after the candidate
capability and its positive, good, ambiguous, hard-negative, and unrelated-repository controls are
frozen.

The first run of this loop produced an apparent order recurrence that failed counterevidence
review. A fresh carrier workflow weighted observed assay-class distributions to the target roster
before applying one fixed linear ancestry-specific calibration mapping. Because the same linear
inverse governs every cell, calibration and weighted averaging commute; reversing only those
steps cannot explain its answer mismatch. The temporary step-order module was removed, and that
representation remains a hard negative for any future order-only question.

Further finite inspection isolated a different recurring obligation: the benchmark reconstruction
uses nonnegative constrained joint calibration separately within post-strata, whereas the fresh
workflow jointly calibrates the standardized aggregate. The task does not state which estimator
governs. The shared registry now contains one exact, Markdown-only, question-only
`poststratified-misclassification-estimator` module that asks the scientist to choose or retain the
unknown. It contains no benchmark identity or answer, produces no Finding, and passes controlled
positive, matching, conflict, ambiguous, hard-negative, removal, sibling, replay, and six
independent-repository false-question checks. This is development capability, not detector
qualification. The concurrent Wright-Fisher run made a different error choice, while the new MVMR
guard attempt did not yield a persistent artifact.

The fixed carrier residual is now causally closed. Nonnegative joint calibration inside each
post-stratum moves all five outputs within contract, while a cellwise unconstrained reverse control
reproduces the original two failures exactly. The repaired report reaches the existing estimator
question and both audits replay byte-identically with zero Findings. This validates the question on
one fixed case; it does not select the governing estimator or qualify a detector.

The next loop admits a second narrow `measurement_model` question for classifier-derived ordered
copy number. A fresh answer-isolated structural workflow explicitly used posterior expected copy
count as continuous dosage, matched two of four answer fields, and still missed both numeric
tolerances; the result is therefore a covered representation control, not evidence of whole-
workflow correctness. The earlier structural workflow used integer classifier outputs as dosage,
establishing the recurring abstract choice, but its report does not contain a complete supported
declaration connecting that representation to the downstream quantitative exposure. The shared
`classifier-derived-copy-dosage-representation` module recognizes only explicit Markdown
declarations. Accepted ADR-0024 later adds direct continuous calibration as a third finite
representation after structural ablations show it is not equivalent to posterior class
expectation. The module asks the scientist to select hard state, posterior expectation, direct
continuous calibration, or retain the unknown, and never emits a Finding. Controlled ambiguity,
nearby hard negatives, removal,
interaction/replay, six independent repositories, and the MR-tutorial sibling pass with zero false
questions. The older hard-call report remains `unsupported` until a typed source-to-analysis join
or an explicit report declaration exists. Calibration pooling or stratification remains a separate
unsupported policy.

The third loop adds a narrow `adjustment_set` question for a recoverable technical grouping. A
fresh answer-isolated ambient-state eQTL workflow explicitly reported that no unit-level ambient or
technical group was observed or reconstructed and omitted such a covariate. It reproduced
byte-identically, locked before grading, and later missed the answer-side tolerance. The evaluation
reference reconstructs a donor technical-contamination group from a unit-level summary and adjusts
for it, establishing a concrete alternative without granting the answer key production authority.
The shared `recoverable-technical-group-adjustment` module recognizes only exact selected-Markdown
declarations of reconstructed-group inclusion or explicit non-reconstruction/omission. It asks the
scientist which treatment governs or retains the unknown, and never infers that a grouping is real,
confounding, or scientifically required. Controlled Answers, ambiguity, QC-only, observed-batch and
biological-group hard negatives, removal, sibling isolation, eight unrelated/sibling workflows,
semantic lock, and replay pass with zero Findings and no project execution.

The fixed ambient-state residual is now causally bounded by a 2-by-2. Corrected-marker count scale
alone and recovered-group inclusion alone remain outside tolerance; their combination is within.
Every report reaches only the existing technical-group question and replays byte-identically with
zero Findings. A finite decomposition found several target-equivalent state rules, so marker
composition, scale, and threshold remain unsupported rather than becoming a case-specific check.
The group question is relevant but cannot certify the state rule or attribute the entire miss.

The next validation loop returns to the accepted founder-orientation question with a new
answer-isolated multi-parent QTL workflow. The workflow independently repaired two founder-marker
orientations before HMM emission and placed founder `F5` and position `46.5` cM within the public
answer contract. Its natural selected-report wording exposed only an adapter-connectivity gap: the
existing grammar recognized an unmodified singular form but not explicit `0/1` alleles and plural
`emissions`. The bounded report grammar now accepts those modifiers while preserving the same
operand, question, scientist authority, and question-only ceiling. The unchanged frozen workflow
then produces the founder question, while a plotting lookalike and commit-pinned qtl2, DOQTL, and
tensorQTL remain question-free with deterministic replay. This is covered-good development
evidence, not detector qualification or general HMM validation.

The following loop returns to CRISPRi/CasRx with a new answer-isolated workflow. It matches the
binary target decision but misses both quantitative effects. Finite post-lock mechanism evidence
shows a recurring calibration family, but independent design review rejects a combined
offset/scale/validation choice because those operations are not mutually exclusive. The admitted
`paired-bridge-location-alignment` module therefore asks only whether group-specific additive
offsets from paired bridge measurements govern the follow-up fit, defines the subtraction
direction, and remains question-only. Two independently authored reports instantiate the same
atomic choice; mixed offset-plus-scale, ordinary-centering and QC hard negatives, controlled
Answers, module removal, ten unrelated or sibling workflows, skill usability, lock, and replay
pass without Findings or project execution. Later fixed-case and reverse-control ablations support
the separate CasRx axis choice, so accepted ADR-0025 adds a threshold-independent one-axis versus
simultaneous-two-axis question without changing the bridge module. Multiplicative scale and the
remaining pooled-screen choices stay unsupported.

The next fresh pulse-admixture workflow misses all four graded values while explicitly computing
exposure from eligible called ancestry-A plus ancestry-B length. This is recurrence for the
already accepted `full-map-ancestry-exposure` question, not a new scientific rule. The first
bounded grammar extension recognized its natural denominator/exclusion wording, but later causal
ablation showed that this wording defines the ancestry fraction rather than necessarily the pulse-
time exposure. Accepted ADR-0023 replaces that broad connection with exact v1.1 pulse-time
declarations under `time_definition`. A called-fraction paragraph or QC table cannot answer the
timing question. Chromosome-label harmonization, ancestry-call validity, transition-path
continuity, and numeric-cause attribution remain unsupported by this production module.

The following carrier-screening workflow passes three of five answer fields but misses the
full-roster partner frequency and derived couple risk. Its selected report standardizes completed
partners over ancestry and family-history tier while keeping intake site and collection wave as
testing-selection diagnostics. An earlier independently authored carrier report uses the opposite
explicit policy and includes those named availability variables in direct-standardization cells.
The shared question is therefore the atomic conditioning set for direct cell standardization, not
a rule that all predictors of completion belong in every estimator. The exact selected-Markdown
`direct-standardization-conditioning-set` module presents those two finite operands or retains the
unknown under scientist authority. Complete data, QC-only usage, ordinary covariates, generic
nonrandom-testing prose, IPW/doubly robust methods, and partial or contradictory sets remain
negative or unsupported. Controlled Answers, module isolation, ten unrelated or sibling workflow
audits, a fresh-context skill run, semantic locks, and replays preserve zero Findings and no
project execution. The module cannot choose the scientifically appropriate set, validate
exchangeability or positivity, cover general missing-data estimators, or explain the numeric
mismatch.

Before generating another workflow, causal ablations close both known diagnoses. Expanding only
the frozen carrier workflow's direct-standardization cells to include site and wave moves its two
missed outputs, and therefore all five fields, within contract. In the pulse-admixture workflow,
reversing chromosome-3 ancestry labels repairs both fractions but not either time. Retaining that
repair, connecting successive eligible tracts across intervening uncalled/filtered spans for
transition counting, and using complete chromosome-map length moves all four outputs within
contract. This separates the label cause from the timing cause and exposes the reviewer conflation
fixed by ADR-0023. At that point it did not justify a transition-path module after only one fixed
case. The next two closures are now complete. In CRISPRi/CasRx, a paired-offset-only ablation repairs the neighbor
effect but not the transcript effect; a combined repair moves all fields within contract; and a
one-axis reverse control moves only the transcript effect back outside. Accepted ADR-0025 adds the
atomic, threshold-independent CasRx isoform-axis question without conflating it with assay
alignment. In the structural case, ancestry-stratified direct continuous calibration moves all four
fields within contract, while pooled-direct and stratified-posterior reverse controls remain outside.
Accepted ADR-0024 adds direct continuous calibration as a third dosage representation but keeps
calibration pooling unsupported. The next step is a stable full regression and actual-workflow
false-question checkpoint. Only after that checkpoint passes does the program resume broad answer-
isolated workflow generation or another fixed-failure closure; a new module still requires
independent recurrence and the complete finite control set.

The checkpoint next closed the frozen TXR1 compound failure. A released-data 2-by-2 shows that the
somatic target representation and missing-outcome estimator are independently material: correcting
only the target leaves all three numeric fields outside contract; correcting only the estimator
leaves benefit and net outside; correcting both passes every field. Accepted ADR-0026 adds two
separate question-only modules, `somatic-clonality-representation` and
`posttreatment-missingness-strategy`, without benchmark thresholds, numeric authority, source
execution, or Finding permission. Original, target-only, estimator-only, and combined reports map
to the four expected operand pairs, retain zero Findings, and replay their semantic locks and HTML
reports byte-for-byte. The post-change repository checkpoint passes `948` tests, Ruff, strict
typing, starter/schema validation, and the walking skeleton. The next loop should take the next
frozen unresolved workflow and again separate demonstrated mechanisms before adding any module.

That next loop produced one admitted recurrence and one still-open representation gap. A fresh
Wright-Fisher workflow correctly polarized the derived allele, fit the requested hidden-state
model, and selected the correct locus, but independently repeated the earlier choice to use an
average of two directional error rates symmetrically. Its selection coefficient again fell outside
tolerance. Accepted ADR-0027 adds the atomic question-only
`directional-measurement-error-interpretation` module under `measurement_model`; it recognizes
explicit symmetric-average or externally constrained direction-specific declarations, but cannot
infer the constraint or select the governing operand. Both separately authored reports now reach
that one question with zero Findings and byte-identical replay. A fresh Hi-C workflow then
reproduced the same-distance expected-count miss on the exact released inputs and failed all three
outputs. Its target-inclusive mean differs from the reference across masking, target exclusion,
covariates, likelihood, dependence, and condition interactions. That representation remains
unsupported as a complete method profile, but ADR-0018's already accepted claimless obligation
branch now surfaces the exact narrower fact that the report's target-exclusion sensitivity changes
all three requested O/E values. It creates one analysis-scoped MaterialQuestion and no Claim,
candidate, or Finding. The grammar binds generic case/control/delta output roles and has a non-Hi-C
positive, covered negative, ambiguity, and hard-negative portability set. The experimental
method-conflict detector remains separate and cannot consume the unsupported reported
representation. Broader incomplete methods, estimator choice, materiality, numeric cause, and
non-Markdown evidence remain unsupported. The resulting full checkpoint passes `969` tests and
the complete clean-wheel handoff verifier without a schema release.

The next targeted recurrence returns to that deliberately deferred transition-path choice. A
second answer-isolated pulse-admixture workflow independently terminates the retained-state path at
masked or uncalled intervals, uses retained callable timing exposure, and repeats the previous
four-field failure with the same error magnitudes. Its locked pre-answer audit asks nothing. A
fresh label-repaired 2-by-2 then varies only path continuity and full-map exposure: neither single
change passes both pulse times, while their combination passes every field. Accepted ADR-0028
therefore adds one domain-neutral, selected-Markdown, question-only
`within-sequence-transition-path-continuity` module under `dependence_structure` and reconnects
only the fresh explicit wording to ADR-0023's separate exposure question. The auditor cannot infer
hidden states, choose either requirement, establish execution, or attribute numeric cause outside
the fixed ablation. Both independent baselines, both repaired reports, four 2-by-2 cells, finite
controls, controlled Answers, module removal, and replay remain zero-Finding. No schema, detector
qualification, execution privilege, metric authority, or public maturity claim changes.
The resulting full checkpoint passes `980` tests and the complete clean-wheel handoff verifier.

A fresh answer-isolated structural-copy workflow next provides a covered-good rather than another
failure: group-specific direct continuous Ridge calibration places all four fields within the
released contract. Its selected report explicitly retains a continuous copy index rather than
rounding, names the copy target and direct model, and uses calibrated dosage for that same target
downstream, but splits those premises across paragraphs. The pre-answer audit therefore asks
nothing. Accepted ADR-0029 advances the existing ADR-0024 dosage check and adapter to `1.2.0` and
adds only one finite document-scoped same-literal-target join. The fresh, posterior, prior direct,
pooled-direct, and stratified-posterior reports project their exact representation operands and
replay byte-identically with zero Findings. The pooled failure does not independently recur, so
pooling versus group-specific calibration remains unsupported. No schema, Finding authority,
execution privilege, numeric authority, detector qualification, or maturity claim changes. The
resulting full checkpoint passes `984` tests and the complete clean-wheel handoff verifier.

A third answer-isolated ambient-state workflow next repeats the prior two-axis interaction under an
independently authored analysis. Its untouched result is outside the exact tolerance. Changing only
the activation-score scale worsens the estimate, and adding only the recovered technical group
comes close but remains outside; only the combined fixed-case change is within. The group-inclusion
reports explicitly connect a separated technical proxy to **that** reconstructed group and include
**it** as a categorical covariate in the primary model. Accepted ADR-0030 advances the existing
technical-group check and adapter to `1.1.0` with one finite paragraph-scoped co-reference form.
The baseline and scale-only reports remain question-free, while group-only and combined reach
exactly the existing adjustment-set question; all four preserve zero Findings and byte-identical
replay. Activation scale, marker definition, threshold, and numeric-cause attribution remain
unsupported. No schema, Finding authority, execution privilege, numeric authority, detector
qualification, or maturity claim changes. The resulting full checkpoint passes `987` tests and the
complete clean-wheel handoff verifier.

A second answer-isolated TXR1 workflow next supplies a conservative negative recurrence. It uses a
third molecular target and a hybrid AIPW assessment model including post-treatment toxicity; both
remain unsupported, and all three numeric fields miss. The evaluator-owned two-by-two shows that
the frozen reference target accounts for most of the fixed-case discrepancy, while excluding
toxicity does not independently repair the workflow. Accepted ADR-0031 therefore adds no new
scientific choice. It advances the two existing ADR-0026 question adapters to `1.1.0` only to
recognize finite explicit report forms for the adjusted-CCF reference target and baseline-only
inverse-assessment transport. Untouched, target-only, missingness-only, and combined reports expose
zero, target, missingness, and both questions respectively; all remain zero-Finding and replay
byte-identically. AIPW versus normalized IPW remains unsupported. No schema, execution privilege,
numeric authority, detector qualification, or maturity claim changes.

A fresh answer-isolated phase-split MVMR workflow next reveals two independent method axes. Its
six LD-conditional signals plus zero-intercept full-covariance GLS miss both requested effects. In
a frozen two-by-two, marginal screening alone and robust LD-whitened fitting alone also miss both;
only marginal screening plus the robust fit passes. Accepted ADR-0032 adds separate question-only
modules for phase-split instrument construction and residual-heterogeneity estimator, while
version `1.1.0` of the existing LD-whitening adapter connects the robust ablation's natural
wording. The fresh workflow, all four cells, the earlier independent robust workflow, and four
public repository controls project only their exact finite operands and replay byte-identically
with zero Findings. The auditor does not choose the passing combination, establish instrument
validity, or broaden ADR-0021's R-Markdown covariance check. No schema, execution privilege,
numeric authority, detector qualification, or maturity claim changes. The resulting full
checkpoint passes `1013` tests, Ruff, formatting, strict typing, and starter/schema validation.
A fresh-context `scientific-audit` skill run reaches exactly those two new questions, retains both
as unresolved, and replays identical semantic records, assessments, coverage, lock digest, and
HTML report with zero Findings, no project execution, and zero model calls. The complete clean-
wheel handoff verifier also passes.

Accepted ADR-0033 next adds the first bounded `.R` source layer. Tree-sitter-R always supplies a
non-evaluating syntax and literal-call inventory; an auditor-owned base-R helper independently
uses only `parse(keep.source=TRUE)` and `getParseData()` when R is available. Both results remain
separate, disagreement is explicit, dynamic behavior remains opaque, caching is initially
disabled, and semantic lock/replay never reruns either parser. Three separately generated
detector-free profiles enumerate only DESeq2, edgeR, and limma-voom call surfaces. They have no
package-version evidence, semantic model, correctness conclusion, question, or Finding authority.
The next R increment must be driven by a recurring scientific obligation rather than filling out
a generic function-name catalogue. The resulting checkpoint passes `1023` tests and the complete
clean-wheel handoff verifier, including installed-resource, whole-audit, and replay controls.

Accepted ADR-0039 now closes the most immediate post-hoc connectivity gap without adding another
scientific vocabulary item. Python parser `0.15.1` recognizes only a uniquely bound
source-parent-relative literal writer. When that writer is the sole producer of the exact
full-digest selected report Artifact and is statically reachable at module scope or through one
exact guarded zero-argument entrypoint, the existing founder-orientation source observation can
join the selected report. The frozen multiparent-QTL workflow now carries its report and source
operands through the already authorized scientist requirement, one exact incompatibility
Disclosure, semantic lock, and replay with zero Findings. Unused, competing, dynamic, absolute,
parent-traversing, and non-source-root writers remain hard negatives. This join proves neither
execution nor primary-analysis status.

The next development loop was defined to freeze this exact post-hoc conflict as an experimental
detector candidate before exposing it to answer-blind labels. It must remain Finding-ineligible
until the accepted cross-provider qualification and maintainer promotion gates are actually
satisfied. Only after the candidate is frozen should new scientific vocabulary or broader lineage
be considered.

Accepted ADR-0040 completes the candidate-freeze portion of that loop.
`detector:bounded-analysis-method-conflict` version `0.1.0` now rechecks one exact human review
requirement, agreeing report/source operands, the full-digest selected-output graph, and ten finite
counterevidence classes. Its local development controls include an exact conflict, matching
covered negative, unsupported check, missing scope identity, one mutation per finite check,
controller integration, and model-free replay. The frozen multiparent-QTL workflow reaches one
evaluation-only candidate with exact report and source citations and zero Findings. The new
cross-surface capability entry raises the matrix from 14 to 15; schema v0.15.0, qualification,
and production Finding authority do not change.

Accepted ADR-0041 and immutable schema v0.16.0 now supply the missing second static qualification
profile without changing the detector. An evaluator-owned verifier independently rederives the
selected Markdown operand, Python source operand, unique literal report writer, and exact human
Question/Answer/ScientificContract/assertion authority from immutable inputs. It does not reuse
the production parser, adapter, detector, or semantic-fact helpers and it executes no project code.
Both static profile variants remain separately discriminated; ambiguous, unsupported, weak-
identity, over-budget, counterevidenced, or drifted inputs fail closed. The new profile traverses
static fixture construction and replay, Stage 3, reports, canonical storage, schema migration, and
packaging under local synthetic and mutation controls. That is mechanism evidence, not detector
qualification.

Accepted ADR-0042 supersedes that unreviewed v0.1 candidate before external qualification begins.
Detector `0.2.0` now consumes explicit content-addressed method-check bindings through one generic
controller dispatch; active report, Python, and R Markdown adapters have isolated identities; and
schema v0.17.0 supplies one closed typed scalar/set/order proof rather than founder-specific public
fields. The independent qualification engine and founder adapter rederive retained-byte operands
without production semantic imports. Report-only, static-only second-language, and step-order
controls prove the extension seam while preserving controller, storage, reporting, admission, and
schema code. The old Experiment 0026 freeze is immutable historical evidence and cannot qualify
`0.2.0`.

The next loop is therefore a new answer-blind qualification portfolio for the final frozen v0.2
digest. Freeze new assignments and local positive, verified-good, ambiguous, hard-negative,
removal, and counterevidence packets before review; then obtain authenticated cross-provider
Stage-1, Stage-2, and fresh Stage-3 records and compute only predeclared clustered metrics. Any
material logic change after labels are visible creates a new version and restarts qualification.
Finding permission still requires explicit maintainer promotion. New vocabulary follows only from
recurring evidence, using the accepted extension boundary rather than editing the controller.

Experiment 0027 now completes the pre-assignment portion of that loop. The committed v0.2 freeze
binds the exact detector, method binding, independent qualification adapter and verifier closure,
typed schema-v0.17 profile, selection rules, six portfolio roles, and Stage-1/2/3 prompt digests.
It deliberately contains no case, label, reviewer identity, transcript, detector output,
threshold, metric, or promotion claim. Exact no-replace assignments and authenticated reviews are
still pending; known Experiment 0026 cases cannot be relabelled as held-out v0.2 evidence.

Experiment 0028 separately forward-tests the `scientific-audit` skill on a non-QTL Hi-C workflow.
A fresh-context user selects the explicitly named report, reaches exactly the existing bounded
expected-count/background question, retains the unknown, executes no project code, records no
model calls, and replays the same locked result with zero Findings. This is portability evidence,
not qualification. The run also fixes the skill's operational language: every eligible file under
the target root is opened for immutable snapshot hashing even when it is not semantically or
deeply inspected. A protocol requiring true byte exclusion must stage an allowlisted workspace
that omits the forbidden files. Its answer-key-informed follow-up then independently validates a
golden masked negative-binomial estimator and compares it with the unchanged flawed report.
Accepted ADR-0043 adds two atomic question-only checks through ADR-0042's registry: expected-count
construction and focal-target handling. Human-authorized answers now yield two exact material
incompatibility Disclosures with deterministic replay. This closes the demonstrated vocabulary
gap without adding a detector binding, Finding permission, execution claim, or benchmark-derived
production authority. Further expansion still requires recurring evidence and hard negatives.

Experiment 0029 then freezes a four-role multiple-testing family before implementation: an exact
complete-family BH mismatch, its identical-raw-family corrected twin, an explicitly preregistered
single-primary hard negative, and an incomplete-family ambiguity. Accepted ADR-0044 and immutable
schema v0.18.0 add a generic deterministic-calculation registry and typed observation rather than
putting BH logic in the controller or overloading method-choice records. The initial bounded
adapter reads only immutable declared report/table bytes, recomputes ordinary BH under finite
limits, and preserves exact operands and finite receipts. Ordinary audit, report, canonical
storage, semantic lock, and replay now distinguish all four roles; malformed and over-budget data
abstain, live workspace drift cannot alter snapshot calculation, registry removal is isolated, and
every case emits zero Findings. The positive is capped at Disclosure because no detector has been
qualified or promoted. This is reusable calculation infrastructure plus one narrow profile—not
broad single-cell or statistical coverage. New modules require their own frozen contract, oracle,
hard negatives, fresh cases, and qualification evidence.

## Post-MPP optional capability — Built-in project-code execution

Reconsider a built-in executor only after the evidence-first MPP, detector qualification, and
real-corpus validation are working. Before any production launch, resolve or conservatively
supersede deferred ADR-0015 and ADR-0016, publish any required forward-only schema, prove trusted
capability origin and closed linked evidence, and run live safety tests on a qualifying rootless
OCI host. There is no unsafe subprocess fallback. This optional capability is not a prerequisite
for static audits, the Codex skill, detector implementation, or external-evidence inspection.

## Stop conditions

Pause expansion and revise the architecture when any of these occurs:

- deterministic replay requires hidden model state;
- a hard negative becomes a Finding;
- source references cannot be resolved reliably;
- the ten-minute standard deadline is routinely missed before useful coverage;
- provisional observed-plane records cannot represent a real workflow without semantic overloading;
- two independent implementations interpret an accepted requirement differently.
