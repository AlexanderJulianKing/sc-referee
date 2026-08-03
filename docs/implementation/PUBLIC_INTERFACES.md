# Public implementation interfaces

The scaffold exposes narrow interfaces so implementations can evolve without coupling scientific policy to one parser or database.

## Detector

A detector receives immutable locked records and returns a `DetectorResult`. It does not write a Finding directly. Admission is a separate controller operation.

```python
class Detector(Protocol):
    detector_id: str
    detector_version: str

    def evaluate(self, case: LockedDirectionalCase) -> DetectionOutput:
        ...
```

## Finding admission

```python
def admit_finding(result: DetectorResult, context: AdmissionContext) -> Finding | None:
    ...
```

The function must reject unresolved material premises, incomplete counterevidence, uncovered constructs, experimental maturity, or unbounded wording.

## Parser

Parsers emit observed facts and explicit coverage. They do not infer scientific meaning.

```python
class Parser(Protocol):
    def inspect(self, path: Path, run_id: str) -> ParserOutput:
        ...
```

## Record store

Canonical storage is append-only JSONL. Generated indices may be destroyed at any time.

```python
class RecordStore(Protocol):
    def append(self, record: Mapping[str, object]) -> None: ...
    def iter_records(self, record_type: str | None = None) -> Iterator[dict[str, object]]: ...
```

## Model proposal boundary

A model adapter may propose records but cannot admit them as facts.

```python
class SemanticProposalAdapter(Protocol):
    def propose(self, packet: SemanticWorkPacket) -> list[ProposedAssertion]: ...
```

Every prompt template and packet is normalized and hashed. The local controller exposes this
boundary through `resume`, `work-queue`, `work-packet`, and `submit-proposals`. A submitted
SemanticAssertion must remain proposed and cannot claim Finding eligibility or executed-computation
authority.

## Read-only agent status

The first agent boundary is deliberately read-only. `sc-referee status <audit-root> --json`
validates the public bundle, semantic-lock digest, canonical StorageManifest, disposable SQLite
projection, and report contract before returning a typed `AgentAuditStatus` payload. It contains
only run state, coverage state, assessment counts, open question identifiers, integrity state, and
artifact paths; general runs also expose the locked deadline policy. It cannot add evidence or
change semantics.

The public local write boundary is a linked exact-snapshot segment. `sc-referee resume` creates the
new segment and public WorkItems without changing the parent; `--question-id` targets one exact
open question. `submit-proposals` validates model records against the exact packet and immutable
snapshot. `record-answer` constructs a public, self-digested Answer from an existing option and
exact human authority scope. `lock-semantics` closes model submission, persists proposals and
Answers, and completes controller-owned detection and reporting without model access. Unanswered
questions and prior Answers survive subsequent linked segments.

For `scientific_contract` questions, `record-structured-answer` accepts only dimension keys named
by the WorkItem. Each supplied value becomes a separate accepted scientist-declaration assertion
with `scientific_intent` authority and remains Finding-ineligible. Omitted dimensions stay unknown;
these declarations never establish executed computation or lineage.

When two or more fully identified analysis sources, material inputs, or snapshotted analysis
outputs remain plausible, the controller may emit a
`bounded-review-scope-selection-v1` MaterialQuestion. `record-scope-answer` accepts several exact
listed option IDs; single, none, and unknown selections use `record-answer`. These Answers have
`metadata_definition` authority over the exact RepositorySnapshot and define review scope only.
Weak identities, static-only output paths, symlinks, unsafe paths, stale Answers, and digest drift
remain unresolved. Selection never proves execution, source-to-output lineage, scientific intent,
or correctness.

Ordinary audits also bind a release-manifested registry of exact question-only scientific checks.
These checks inspect only their declared immutable report or static-source surfaces, emit
Finding-ineligible observed operands, and may create analysis-scoped MaterialQuestions before
semantic lock. ADR-0028's `within-sequence-transition-path-continuity` check uses the existing
`dependence_structure` dimension to ask whether a retained-state path continues across missing,
masked, filtered, or uncalled intervals. It is separate from ADR-0023's pulse-time exposure
question. Neither check infers hidden states, chooses a governing scientific requirement,
establishes execution, or permits a Finding.

ADR-0029 adds one explicit exception to the paragraph-scoped selected-report default. The existing
copy-dosage representation check may bind a finite document span only when the report explicitly
retains a continuous copy index rather than rounding, names a Ridge-learned literal copy target,
and uses calibrated dosage for that exact same literal target downstream. The evidence span is
localized to those connected statements. This is not general cross-paragraph inference and does
not add a pooling or stratification question.

ADR-0030 keeps paragraph scope but adds one finite co-reference form to the existing recoverable-
technical-group check. The same paragraph must explicitly report a technical-proxy summary and its
separation, reconstruct **that** technical group, and include **it** as a categorical covariate in
the primary model. This is not general pronoun resolution and does not validate the proxy, choose
the adjustment set, establish execution, or permit a Finding.

ADR-0031 adds two finite selected-Markdown connectivity forms to the existing ADR-0026 checks. An
evaluator-frozen inline-code `reference_target` or a prespecified primary eligibility rule may map
to the existing adjusted-clonality operand only when it explicitly requires a bounded
purity/copy-adjusted CCF range. A primary/evaluator-owned missing-outcome declaration may map to the
existing baseline-only assessment operand only when it explicitly excludes a post-treatment
endpoint from every assessment predictor set and names inverse-assessment transport. These forms
do not add a target, missingness, or AIPW/IPW requirement; validate either method; establish
execution; or permit a Finding.

ADR-0032 adds two exact selected-Markdown MVMR questions. One records whether a phase-1 union uses
LD-conditional signals with matching phase-2 joint coefficients or marginal signals with matching
phase-2 marginal coefficients. The other records whether the governing effect estimator is
zero-intercept generalized IVW/GLS or a redescending robust M-estimator on LD-whitened residual
innovations. The existing robust-fit covariance-treatment question remains separate and recognizes
one additional explicit lower-Cholesky M-regression form at version `1.1.0`. These interfaces do
not select instruments or estimators, validate LD or pleiotropy assumptions, broaden the
R-Markdown `gencov` adapter, establish execution, or permit a Finding.

## Root checksum-manifest identity experiment

Under Experiment 0008, snapshot capture recognizes only a closed root-level SHA-256 checksum
profile and only when the complete manifest fits the existing byte-read budget. An admitted
`AssetIdentity` records the exact manifest line and the target digest declared there; it does not
claim that sc-referee hashed the complete target. Full target digests outrank declarations, while
malformed, unsafe, duplicate, nested, and unavailable manifests cannot upgrade identity. The
target is not materialized, and any limitation applies only to conclusions that require exact
target-byte verification.

## Bounded delimited-header inventory experiment

Under Experiment 0009, every fully captured regular `.csv` or `.tsv` file is eligible for strict
UTF-8 first-record inspection. ADR-0054 and Experiment 0045 extend that inventory to exact
`.csv.gz` and `.tsv.gz` bytes. Valid unique headers of at most 1,024 columns and 1 MiB produce a
partial DataAsset and Variables containing exact names only. A quoted header may span physical
lines; the bounded unit is one logical CSV/TSV record.

Compressed reads use at most 64 KiB per chunk and one sentinel byte beyond the 1 MiB header limit.
The snapshot extension `x-delimited-read-receipts` records path, content digest, encoding, raw and
logical bytes, chunks, all ceilings, status, and a closed termination reason. The gzip member after
the header is not decompressed or validated. Storage types, observed levels, row shape, row count,
cell values, missingness, units, scientific roles, and meanings remain unknown, and gzip tables do
not yet feed the L09 calculations.

When exactly one existing static Artifact resolves to the same path, its producer/consumer edges
may label the DataAsset input, intermediate, or output. That label is static source evidence and
does not establish execution. Unlinked tables retain unknown role. Weak, manifest, changed,
malformed, ambiguous, non-UTF-8, or over-limit cases fail locally into explicit coverage and never
become Findings.

## Bounded default Nextflow trace-import experiment

Under Experiment 0010, a fully captured root `trace.txt` with the exact default 14-column
tab-delimited Nextflow header is eligible for bounded import. Internally consistent `COMPLETED/0`
and `FAILED/nonzero` task rows produce weak imported Execution records and one partial imported
Nextflow Environment. The trace is rehashed before inspection; byte, row, field, and opaque-row
ceilings are explicit.

The task label is not represented as captured command text. Inputs, outputs, task timing,
environment version, platform, dependencies, container/module/scheduler state, sandboxing,
authorization, authenticity, and scientific meaning remain unknown. Imported rows are not bound to
Claim lineage and do not become controller-observed execution, clean-control evidence, output
correctness, detector qualification, or Finding premises merely because they validate. Custom
Nextflow traces and non-Nextflow systems remain unsupported.

## Bounded observed-lineage experiment

Active experiment 0002 runs one auditor-owned filtered mean-difference verifier against immutable
Python and local CSV bytes. It imports no project module and executes no project-authored code. A
public ObservedResult is emitted only when its producing Operation and input/output Artifacts
resolve exactly. Claim binding additionally requires unique exact literal alignment of both
comparison endpoints and the outcome column. The Claim remains `partial` because report generation
and project execution were not observed. This interface neither schedules nor qualifies a
detector. A source-level writer edge may cross the experiment's closed alias grammar or one unique
straight-line renderer call containing exactly one supported result plus constant-only positional
presentation arguments. One direct safe relative string argument may bind an unmodified
`Path(parameter)` output target, and exact complete keyword binding may replace positional binding
for non-positional-only required parameters. Those edges still do not establish that the writer ran or
produced the snapshotted report bytes. One uniquely called top-level formatter may be traversed
only when its entire executable body is a single bounded return expression; it is not executed.
Its result may cross one strictly linear top-level assignment chain only when every name has one
binding and one load, each intermediate feeds exactly one next assignment, the terminal has one
later literal writer consumer, and the shared eight-edge ceiling is preserved. Forks, merges,
rebindings, and extra consumers abstain as a whole.

## Evaluation-only static source-method probes

`sc-referee-eval probe-python-method-shapes` reads one regular non-symlink Python file under an
exact source root and applies one or more closed evaluation profiles. It uses only Python AST
inspection; it does not import or execute the source. Experiment 0016's four profiles cover one
directional-measurement formula, one phased composite-marker expression, one independent scalar
calibration shape, and one aggregate-before-calibration shape. Experiment 0019 adds fixed-
workspace-only founder-orientation-before-emission, full-map ancestry exposure, and LD-covariance-
before-robust-fit profiles. The latter three are one-case validation adapters, not generalized
production support.

Every result binds exact source spans and digests plus an answer-side reference identity. Results
are restricted to `exact_static_conflict`, `covered_negative`, or `unsupported_path`; all are
evaluation-only, metric- and promotion-ineligible, and incapable of producing a production
Finding. The answer-side obligation is not production scientific intent, source existence is not
execution evidence, and a static conflict does not establish numeric causality. Unknown profiles,
unsafe paths, symlinks, partial syntax, and replacement of an existing output fail closed.

`sc-referee-eval compile-posthoc-validation-review` verifies one self-digested source-probe record
and one exact review specification, binds a human Answer to the named public-development case, and
projects a structured Answer through `posthoc_method_ledger_v1`. The Answer's value must exactly
match the selected profile manifest and an allowed existing contract dimension. An `unknown`
Answer must leave profile, dimension, comparison form, and value unset. Output is canonical,
write-once, deterministic for the same timestamp and inputs, and explicitly ineligible for
production intent, historical intent, execution, numeric causality, Findings, metrics, held-out
status, or promotion. This Experiment 0019 interface is an evaluation compiler; it is not the
ordinary production audit path and does not turn the case-specific AST profiles into public
capabilities.

## Claimless method contracting

`sc-referee method-contract <project-root> --task <relative-task-path> --output <new-output>`
creates a separate pre-analysis lifecycle around one exact full-digest task or protocol
`FileRecord`. It inventories the repository but does not parse scientific prose into intent,
create a Claim or publication surface, invoke a model, or execute project-authored code. Without a
profile it freezes an analysis-level draft ScientificContract and one bounded open
MaterialQuestion.

An explicit `--profile <json> --actor-id <scientist-id>` accepts either the complete closed
`expected_count_background_v1` grammar or the four-key `scientific_check_requirement_v1` grammar.
The latter resolves one exact `check_id` and `candidate_id` through the installed digest-bound
registry and freezes the complete check manifest, candidate operand, comparison form, and semantic
dimension. Human declarations remain Finding-ineligible; separate controller derivations require
exact Answer digest, human authority, task identity, scope, profile shape, and registry identity.
The contract remains publicly `draft` because unrelated dimensions stay unknown. Replay is
model-free and claimless.

A later `sc-referee audit ... --method-contract-lock <lock>` accepts only a digest-valid resolved
parent lock whose governing task bytes are unchanged. Expected-count profiles bind to applicable
Claims. Atomic scientific-check profiles automatically answer only one exact matching
analysis-scoped question from a `prior_scientist_record`; a missing target remains
`not_applicable`. The parent contract does not establish execution, numeric correctness, or
general method adequacy. The separate `$method-contract` skill drives this lifecycle;
`$scientific-audit` remains post-hoc.

## Exact selected-output writer question scope

Under accepted ADR-0039, ordinary `sc-referee audit <project> --report <report.md> --output <new>`
can connect one exact Python source observation to the selected report when the parser establishes
all of the following without execution: a uniquely bound `Path(__file__).parent` root, one safe
literal `write_text` or `write_bytes` target, identity merge with the full-digest selected report
Artifact, exactly one producer Operation, and one direct module or exact guarded zero-argument
entrypoint path.

The only current consumer is the existing founder-orientation scientific check. It may combine the
source path with the selected report observation, ask which closed requirement governs the review,
and preserve both citations in a later exact compatibility Disclosure. A scientist Answer remains
review-scoped and does not establish historical intent. More than one writer, an unused writer,
dynamic or unsafe path construction, source/report identity disagreement, or divergent scope paths
abstains. This interface never executes project code and does not establish execution, authorship,
primary-analysis role, numerical causality, scientific correctness, detector qualification, or a
Finding.

Accepted ADR-0040 attaches one experimental detector to the completed founder-orientation path.
After a human Answer resolves the review requirement, the detector requires identical report and
static-source operands, replays the full-digest writer graph, and completes ten finite checks. An
exact mismatch produces an internal `evaluation_finding_candidate` for qualification testing; a
match produces a bounded covered negative. Either result is limited to this review. The detector's
public manifest permits only Disclosure output, its production-Finding flag is false, and no
execution, numerical-cause, historical-intent, universal-method, or broader scientific claim is
made.

## Selected feature-identifier identity question and evaluation candidate

Accepted ADR-0058 adds one isolated v13 calculation module for an explicitly declared comparison
between a complete selected CSV/TSV identifier column and a complete selected H5AD `var/` string
dataset. Both artifacts must be named full-digest material inputs. The module performs exact,
order-insensitive set comparison within finite byte, row, column, axis, and text ceilings; it does
not normalize identifiers or execute project code.

An unequal comparison emits one `feature_identifier_identity_requirement` MaterialQuestion rather
than an adverse Disclosure. The scientist may select exact equality, different identifiers
permitted, an alternate mapping, or retained unknown. Only an exact human equality Answer permits
the experimental detector to emit `evaluation_finding_candidate`. The shared non-maturity
admission checks must pass, but production admission still rejects the candidate because the
detector is experimental, unqualified, and explicitly denies production Finding permission.
Conformant comparisons need no question or adverse detector assessment; malformed, duplicate,
ambiguous, unsupported, or over-budget inputs abstain with localized coverage.

This interface demonstrates at most a review-scoped conflict between two exact selected identifier
sets and the human equality requirement. It does not establish corruption, producer lineage,
historical intent, which side is authoritative, repair direction, biological meaning, numerical
impact, publication invalidity, or general data-integrity coverage.

## Post-hoc unresolved expected-count obligation

An ordinary `sc-referee audit ... --report <selected-report.md>` can emit a claimless,
analysis-scoped expected-count MaterialQuestion under ADR-0018's bounded
`expected_count_unresolved_obligation_v1` profile. Every premise must be exact and fully captured:
one conventional `task.md`, `prompt.md`, or `question.md` requests three role-bound mean
log2(observed/expected) outputs; no complete supported expected-count declaration exists in the
inspected Markdown; the selected report states one enumerated target-inclusive same-stratum mean;
and one exact target-exclusion sensitivity changes at least one requested value.

The question asks which complete `expected_count_background_v1` profile governs. It neither
chooses an estimator nor describes the demonstrated difference as material. It creates no Claim,
detector candidate, or Finding and executes no project code. A human Answer produces only
analysis-scoped Finding-ineligible intent declarations because the reported partial method remains
outside the complete conflict-detector grammar. Missing, ambiguous, equal-value, misbound, or
complete-profile cases abstain. The capability matrix lists this question path separately with no
detector reference.

Accepted ADR-0043 adds two independent atomic selected-Markdown checks alongside that complete-
profile obligation. One records an explicit choice between a same-stratum arithmetic mean and a
negative-binomial-model prediction; the other records explicit inclusion or exclusion of the
focal target in its own expected-count background or model training. Each emits one exact
Finding-ineligible observed assertion and one bounded question. They may co-exist with each other
and with the broader question. Partial, lookalike, sensitivity-only, or conflicting declarations
abstain.

A human Answer to either atomic question may produce the existing report-only material
compatibility Disclosure. It still cannot produce a Finding: there is no static-source binding,
execution proof, numerical-cause proof, qualification profile, or production Finding permission.
The checks do not nominate a scientifically correct estimator and do not import a benchmark answer
key into production authority.

## RO-Crate export

`sc-referee export-ro-crate <audit-root> --output <crate.zip>` accepts only an
integrity-verified completed audit and requires declared export-package author and license
metadata. It emits a deterministic attached RO-Crate 1.3 ZIP containing the unchanged native
bundle, report, semantic lock, storage/identity records, and every storage-manifest-bound canonical
JSON/JSONL file. SQLite, caches, and repository materialization are not canonical and are excluded.
The source audit is not modified and an existing output path or symlink is never replaced.

The public `ROCrateExport.content_digest` follows Experiment 0006's explicit
`canonical-json-file-inventory-excluding-ro-crate-export-v1` profile so the record does not hash
itself. `validate-ro-crate` performs the bounded offline structural and byte-integrity checks and
returns that record. Declared package author/license values are not authenticated and do not
establish authorship or licensing of the audited project; third-party RO-Crate validation is not
claimed.

## Generated capability matrix

`sc-referee generate-capability-matrix --output <matrix.json>` reads the bundled closed release
manifest set by default, or an explicitly supplied `--manifest-root`. The set binds exactly five
canonical collections—parser, semantic profile, detector, qualification, and version—by SHA-256.
Public source records validate against schema v0.15.0, private join/version records use the closed
Experiment 0007 profile, and every reference resolves before output is created.

The generator never converts parser-supported versions to `tested_versions`, never converts code
or fixture presence into detector qualification, and never allows a domain-wide support or
validation claim. The current bundled matrix contains 16 narrow entries: 12 have no detector,
while the direction, expected-count method-contract, cross-surface analysis-method, and selected
feature-identifier entries attach only experimental unqualified detectors.
The no-detector set includes three distinct `.R` call-inventory profiles for DESeq2, edgeR, and
limma-voom plus bounded nbformat-v4 cell/saved-output and Quarto source/cell inventories and one
separate static Python/R container-cell bridge. ADR-0037 lets existing exact static adapters receive
independently reverified cell bytes with truthful cell locations. ADR-0038 admits only one
full-digest selected-container containment join for the existing founder-orientation question; it
adds no capability entry, execution claim, general scientific scope, detector, or Finding
authority. ADR-0039 adds the separate exact selected-output writer scope for that same question and
updates the Python static path inventory to version `0.15.1`. ADR-0040 adds the separate
cross-surface detector entry only after the scope is complete. ADR-0060 and Experiment 0047 advance
that experimental detector to version `0.3.0`, bind all 20 substantive installed checks through
one closed comparison core, and add automatic pre-analysis requirement binding plus an internal
ReviewCase digest. No binding is qualified or permitted to emit Findings. These exact scopes do
not establish package dispatch, workflow validity, cross-cell state, notebook execution, Quarto rendering,
primary-analysis role, or scientific correctness;
container semantic modeling is not started and tested/inferred package versions are empty.
Explicit gaps and abstentions prevent broader negative results or scientific support from being
inferred. Existing outputs and symlinks are not replaced.
`validate-capability-matrix` validates the public schema and requires exact deterministic
reproduction from the bound source set.

## Evaluation-private static qualification proof

`sc-referee-eval freeze-static-profile` freezes accepted ADR-0022's first detector-specific
answer-side verifier, its complete implementation/dependency lock, exact production manifest
envelope, selection protocol, closed grammar, and budgets before case inspection.
`verify-static-case` then inventories immutable `.md`, `.py`, and `.csv` bytes and independently
rederives only the bounded literal-report/raw-two-group-mean/static-writer closure. It imports no
production fact derivation and executes no inspected project code. Unsupported, ambiguous,
incomplete, weakly identified, over-budget, conflicting, or counterevidenced inputs produce an
unavailable proof, not a negative control.

`generate-static-control-fixture` replays that exact proof together with the existing 4+2 label
artifacts and emits only `static_scope_verified_good` or `static_scope_hard_negative`. Stage 3
requires the proof to precede production detector dispatch and keeps it outside detector semantic
inputs. Public v0.15.0 metrics and reports preserve static controls as a separate proof family.
These interfaces establish synthetic mechanism evidence only; they do not claim project
execution, general static-analysis adequacy, detector qualification, or Finding permission.

Schema v0.17.0 also publishes `typed_static_method_conflict_v1` for accepted ADR-0042. A profile
binds one installed method check, historical detector version `0.2.0`, closed comparison relation and operand
type, one or two required evidence planes, finite counterevidence predicates, and an explicit
independent qualification adapter by dependency digest. A complete proof contains only the
independently rederived typed observations, exact retained declarations and scope paths, bound
human Question/Answer/ScientificContract/assertion authority, and deterministic comparison.

`sc_referee_evaluation.typed_method_qualification:verify_typed_method_case` is the generic proof
constructor. The founder-orientation instance uses
`sc_referee_evaluation.founder_orientation_adapter:FounderOrientationQualificationAdapter`, which
reads retained bytes without importing the production scientific-check adapters, detector, or
ledger and without executing project code. The superseded v0.16 founder-specific verifier remains
a historical replay baseline only and cannot qualify detector `0.2.0`. No current CLI claim,
qualification metric, promotion, or Finding permission follows from this local interface.

The active v0.3 candidate cannot reuse this v0.2 profile or freeze. Schema v0.18.0 also retains the
deferred numeric-threshold policy that prohibits promotion. The forward-only representation and
independent evidence needed for a v0.3 qualification are recorded as an open schema gap.

`freeze_typed_method_profile` freezes the binding, detector/parser/profile/version manifests,
independent adapter identity, budgets, and selection protocol before assignment.
`verify_registered_typed_method_case` then reads only full-digest candidate bytes from the supplied
immutable snapshot, validates the scope-bound human authority records, verifies the caller-supplied
adapter identity, and constructs the closed typed proof. The separate
`qualification_adapter_registry:registered_qualification_adapter` resolves only explicitly
allowlisted adapters, so adding an adapter does not rewrite or rehash the generic comparison
engine. `revalidate_registered_typed_method_proof` repeats the derivation and requires exact
equality. These evaluator-only interfaces do not execute project code, discover ambient plugins,
import production scientific semantics, or confer Finding authority.

The isolated CLI exposes the same current path as
`freeze-typed-method-static-profile`, `assign-typed-method-static-case`,
`verify-typed-method-static-case`, and `replay-typed-method-static-case`. The assignment contains
only the case identity, selected report, and exact selection-protocol reference; scientific labels
and detector outputs remain separate. The older `*-analysis-method-static-*` commands remain the
immutable v0.16/v0.1 replay surface and cannot accept the typed v0.2 profile.

## Deterministic calculation checks

Accepted ADR-0044 and schema v0.18.0 publish `deterministic_check_observation` as a parallel,
non-executing evidence surface. A content-addressed calculation-check registry dispatches only
packaged manifests to bounded adapters. Each observation binds the check and adapter identities,
applicability, exact input and source references, closed typed operands, comparison outcome,
finite applicability/ambiguity/counterevidence/completeness receipts, limitations, provenance,
and deterministic digest. Its declared output ceiling is enforced independently of the numerical
result; the initial profile is `disclosure_only`, and `production_finding_permitted` is false.

The first module,
`calculation-check:benjamini-hochberg-complete-family-v1`, recognizes one explicit Markdown
contract naming BH/FDR, alpha, a complete CSV/TSV testing-family path, and raw, adjusted, and call
columns. It reads only immutable snapshot bytes under 1 MiB, 10,000-row, and 64-column limits;
requires strict UTF-8, unique headers and `test_id` values, exact finite decimals, and Boolean
calls; recomputes ordinary unweighted Benjamini-Hochberg values with deterministic decimal
arithmetic; and records exact reported/recomputed discovery counts and disagreement indices.
It never imports or executes project-authored code.

A complete mismatch produces a Disclosure rather than a Finding. A corrected twin is conformant;
an explicitly preregistered single-primary analysis is not applicable; an incomplete or
selected-hits family is ambiguous and may create one bounded `multiplicity_contract` question;
and malformed or over-budget inputs remain unknown/unsupported without a numerical accusation.
The observation, registry evaluation, and resulting assessments are semantic-lock inputs and
replay byte-stably through canonical JSON/JSONL and disposable SQLite projections. Removing the
module removes its observation and associated output without changing the controller.

This is one narrow evidence carrier, not a general multiple-testing auditor. It does not recognize
natural-language variants, arbitrary identifier-column contracts, missing values, weighted,
hierarchical, adaptive, or non-BH procedures, dynamic table construction, runtime use, causal
effect, or universal method adequacy. Human answers are retained as authority for a later audit;
they do not retroactively make an incomplete table calculable or promote any result to Finding.

Accepted ADR-0052 and calculation registry profile v10 add a second evidence layout for all eight
active calculation families. An explicitly selected, fully digested YAML material input may carry
the exact root marker `sc_referee_calculation_contracts: 1` and a bounded list of unique
`check_id`/`contract` mappings. Its filename and directory are not semantic. Each sidecar adapter
normalizes that mapping into the same typed internal contract used by the existing report adapter;
the family evaluator and comparison relation are shared rather than copied.

The sidecar parser accepts strict UTF-8 safe YAML under 256 KiB and 32 contracts. Exact root and
entry keys, mapping-valued contracts, unique check IDs, and the existing selected-material scope
path are mandatory. Unmarked YAML is ignored. An unselected sidecar has no authority, and competing
report and sidecar observations fail closed. Sidecar declarations do not establish execution,
truth, scientific adequacy, or producer lineage. Every v10 calculation remains Disclosure-only and
Finding-ineligible under schema v0.18.0.

Accepted ADR-0055 and calculation registry profile v11 preserve those exact contracts and add a
bounded decoded-input view for exact `.csv.gz` and `.tsv.gz` paths. This is a storage-format
extension only: normalized scientific operands, family evaluators, comparison relations, and
Disclosure-only ceilings remain unchanged.

When complete gzip calculation input is attempted, the repository snapshot extension
`x-delimited-calculation-read-receipts` contains one deterministic object per exact path and
physical digest with:

- physical `content_digest` and separate `logical_content_digest`;
- `status` (`inspected` or `unsupported`) and a closed `termination_reason`;
- measured raw bytes, logical bytes, and decompression chunks;
- raw, decoded-content, logical-read, chunk, and aggregate ceilings; and
- aggregate logical bytes after that read.

The current limits are 64 KiB per chunk, 8 MiB decoded content per input plus one sentinel byte,
and 64 MiB of aggregate logical reads. The controller checks cancellation and its pre-lock deadline
before physical access and between chunks. A malformed or over-budget input is excluded from
calculation authority, so its adapter can only abstain or return unsupported. Replay consumes the
locked result and does not reopen or execute the project.

Accepted ADR-0057 and calculation registry profile v12 add one independent, Disclosure-only
selected record-boundary family. It inspects only exact selected material: one bounded strict-UTF-8
two-line record and selected `.py` source. The record grammar requires an amino-acid-alphabet-only
first line and a non-FASTA-header second line containing text outside that alphabet. The inert AST
grammar requires one empty-string join over the selected record's split lines and an exact direct
or single-call path flow from that record to the read. Merely mentioning the filename does not
bind the source.

The check records the exact two record lines, exact join span, typed operands, finite receipts, and
limitations. A unique path-bound join can produce only a non-accusatory Disclosure; competing
pairs are ambiguous, a unique selected Python parse failure is unsupported, and corrected,
validated, FASTA, sequence-only, dynamic, or unbound forms abstain. It does not establish that the
first line is biologically meaningful, that the code ran, or that any downstream result changed.
It has no model, benchmark identity, qualification, Finding permission, or schema change.

## Bounded H5AD read receipts

Accepted ADR-0053 extends the existing exact selected-H5AD structural inventory from dense integer
`X` datasets to exact AnnData CSR and CSC groups. Sparse arrays remain inside the immutable
selected-material copy, use hard HDF5 links and allowlisted compression, and are scanned without
dense allocation.

When at least one exact selected H5AD is attempted, the repository snapshot extension
`x-h5ad-read-receipts` contains a deterministic object per path with:

- `path` and `content_digest`;
- `status` (`inspected` or `unsupported`);
- `raw_file_bytes`, `logical_bytes_read`, and `read_chunks`;
- `logical_byte_ceiling` and `chunk_byte_ceiling`; and
- a closed `termination_reason`, which is null only for a completed inspection.

The current ceilings are 1 MiB per logical chunk and 64 MiB of decompressed logical reads, in
addition to the unchanged 16 MiB aggregate exact selected-material copy budget. These extension
receipts are controller observations for auditability and replay. They do not establish scientific
meaning, analysis use, experimental unit, or a calculation premise.

## Evaluation-private public-corpus preflight

`sc-referee-eval preflight-genebench-public` verifies an already-local, full-revision-pinned
GeneBench-Pro public package against separately supplied manifest and checksum-inventory digests.
It performs strict metadata parsing, closed-inventory checks, and streamed full-file hashing; it
does not import or execute the package's grader, invoke a model, copy answer-side configuration
into an agent workspace, or emit ground-truth values. Its output is itself answer-side and cannot
enter an agent workspace.

The interface can prepare only `public_development` evidence. It cannot establish held-out status,
scientific correctness, independent review, a qualification metric, a Finding, or redistribution
permission. The pinned official initial revision has consistent CC-BY-4.0 identifiers and passes
all 77 declared hashes; the current MIT-labelled head fails closed because its checksum inventory
does not match its edited LICENSE and README. This interface is governed by evaluation-private
Experiment 0005 and is not a public record or production import dependency.

`sc-referee-eval prepare-genebench-public-case` consumes that exact admitted preflight and one case
identifier. It reruns package verification, creates a full-digest runner snapshot, and emits a
separate agent-eligible `workspace/` containing only derived `task.md` plus the declared visible
data paths. Config, canonical ground truth, grader, reference report, snapshot materialization, and
receipts remain runner-side. The whole output root is not agent-safe; only `workspace/` may cross
the isolation boundary. This evaluation-private Experiment 0012 interface invokes no model or
project code and produces no detector or qualification claim.

`sc-referee-eval grade-genebench-public-numeric` is the evaluation-private Experiment 0013
answer-side boundary. It accepts one terminal integrity-verified audit and resolves only the exact
full-digest `answer.json` from that audit's semantic-lock snapshot. It reruns package preflight and
supports only finite numeric values under closed single- or multi-key absolute-tolerance contracts.
Experiment 0015 permits an optional paired finite minimum/maximum range on each multi-key numeric
field. Experiment 0017 adds the exact legacy single-key form with `answer_field` fixed to `answer`.
Experiment 0018 permits a minimum-only range only in the multi-key absolute-tolerance profile.
That expanded closed shape has comparison-profile identity
`genebench_multi_numeric_absolute_tolerance_v3`; earlier `v2` grade records remain immutable.
New grade IDs bind both grader version and comparison-profile identity so records from different
comparison semantics cannot share one stable identifier.
Maximum-only ranges, one-sided bounds in the other numeric profiles, relative tolerance, optional
keys, and other grader forms still fail closed.

`sc-referee-eval grade-genebench-public-answer` is the package-bound general answer extension. It
accepts either closed numeric contract, Experiment 0015's exact composite of required,
case-sensitive string equality and required bounded numeric absolute tolerance, or Experiment
0017's exact composite of JSON-integer equality and finite numeric absolute tolerance. Integer
fields require a minimum and may add a maximum; optional outer strictness flags must be present as
the exact accepted pair and true. It does not import or execute the package grader or project code.
Both grader commands emit canonical public-development observations only; they cannot become
Findings, labels, qualification metrics, held-out evidence, or promotion evidence.

`sc-referee-eval diagnose-genebench-method-contract` is Experiment 0014's answer-side diagnostic.
It requires an unchanged zero-Finding production audit whose method detector retained
`insufficient_semantics`, then compares its exact reported profile with one explicitly supplied,
digest-identified public-development reference profile in a private evaluation copy. The reference
never enters the production audit. The diagnostic cannot execute project code, invoke a model,
emit a production Finding, enter metrics, establish held-out status, or support promotion.

Canonical JSON and append-only JSONL in the segment are the sole durable state. A conversational or
future MCP adapter must call these transitions rather than emulate them with hidden state.
