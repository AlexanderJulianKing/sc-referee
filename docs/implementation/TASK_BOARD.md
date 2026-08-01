# Implementation task board

Tasks are ordered by dependency. A coding agent should complete the first pending prerequisite rather than selecting the most interesting detector.

## Status legend

- ✅ Implemented and verified in this starter.
- 🟡 Partially implemented or provisional; finish before treating it as production-ready.
- ⬜ Not implemented.

## Current delivery phase

Experiments 0030 and 0031 closed practical feature parity inside the overhaul's stricter evidence
boundary. Experiment 0032 added public documentation, local plugin distribution, and
clean-checkout verification. Experiment 0033 fixes the authorized 0.3.0 release identity,
authorship, AI acknowledgment, and completed merge gate. Experiment 0034 follows an independent
fresh-context documentation review by completing the direct interaction example and narrowing
plugin wording to the actual method-contract profile. The 0.3.0 overhaul is now on `main`; this
follow-up changes no detector authority or schema meaning. Post-MPP functionality work is ordered
in `docs/implementation/POST_MPP_PRODUCT_BACKLOG.md`; its L01 regression corpus ledger is the first
pending prerequisite.

## Epic A — Baseline and quality gates

- ✅ **A01** Pytest, Ruff, mypy, schema validation, demo, and replay pass locally, and both hosted
  push and pull-request matrices pass on Python 3.11, 3.12, and 3.13.
- ✅ **A02** Machine-readable overlay version, baseline identities, and baseline digests are present.
- ✅ **A03** All vendored immutable v0.5 and accepted v0.6.0 schemas and examples validate offline.
- ✅ **A04** CI generates and uploads the walking-skeleton report and validation log on Python 3.11.
- ✅ **A05** Record architecture conflicts in the schema-gap register before coding around them.

## Epic B — Controller primitives

- ✅ **B01** State transitions are wired into the walking-skeleton controller and persisted as
  append-only public v0.6.0 `AuditRun` state records.
- ✅ **B02** The pausable user-visible deadline enforces normative mode cutoffs and hard deadlines
  with injectable-clock partial-run coverage for both the synthetic and arbitrary-repository
  controllers.
- ✅ **B03** Stable semantic digests and canonical JSON normalization exist.
- ✅ **B04** Deadline, host-limit, cancellation, pre-snapshot failure, and post-snapshot controller
  failures propagate through durable public v0.6.0 `AuditRun` and `StageResult` records. Pre-lock
  bundle and cancellation-coverage gaps remain explicit.

## Epic C — Canonical storage

- ✅ **C01** Canonical JSON replacement and locked JSONL append use file/directory fsync, reject torn or noncanonical records, and pass injected-crash tests.
- ✅ **C02** Disposable SQLite rebuild includes record-reference edges, source-location tables, and source/target/path/digest query indices.
- ✅ **C03** A schema-valid StorageManifest binds canonical files and verifies exact SQLite projection; its self-reference-free digest profile is explicitly proposed in implementation ADR-0001.
- ✅ **C04** Deletion and rebuild of SQLite is covered without canonical record loss.

## Epic D — Snapshot and parsing

- ✅ **D01** Immutable snapshotting covers symlinks, special files, excluded audit roots,
  localized read failure, and safe in-repository destinations. Public v0.6.0 `FileRecord` records,
  identity linkage, unreadable-link handling, and negative invariants pass.
- ✅ **D02** A byte-read policy emits schema-valid full-digest, immutable-external, manifest,
  weak-fingerprint, and unidentified AssetIdentity records; weak identity limits only dependent
  conclusions and is reported as a non-accusatory coverage limitation. An end-to-end audit and
  replay regression uses a 10-billion-byte sparse scientific-data asset, reads only 12,288 sampled
  bytes, does not materialize or fully digest it, still parses the independent source/report, and
  proves embedded project code is not executed. Experiment 0008 additionally recognizes one
  closed root-level SHA-256 checksum-manifest profile: it preserves the repository-declared target
  digest and exact manifest line without claiming target-byte verification. Conflicting, unsafe,
  nested, malformed, or over-budget manifests fail locally, and a computed full digest wins.
- ✅ **D03** Stage-boundary monitoring records live workspace divergence while all parsing and detection remain bound to the immutable initial snapshot.
- ✅ **D04** Python AST/token inspection emits exact source-spanned operation and artifact records; the first bounded mean-difference path is independently verified from safe CSV reads without executing project code, and unknown calls remain opaque.
- ✅ **D05** The walking-skeleton Claim is deterministically rebuilt from an exact Markdown directional span and repository-derived lineage; fixture-assembled claim text, direction, and scalar values are ignored.
- ✅ **D06** Python and Markdown emit schema-valid parser coverage records for normal, malformed, unreadable, and explicitly opaque constructs.
- ✅ **D07** Experiment 0009 inventories exact headers from fully captured CSV/TSV files without
  inspecting row values or inferring types or scientific meaning. It reuses one unambiguous static
  Artifact to preserve input/output/intermediate evidence, otherwise leaves role unknown. Invalid
  headers become opaque, over-budget tables remain structurally unavailable, all promoted records
  validate and replay, and the generated capability matrix exposes only this narrow no-detector
  envelope.
- ✅ **D08** Experiment 0010 imports consistent terminal rows from a fully captured root default
  Nextflow `trace.txt` as weak external Execution assertions. It executes no project code, binds no
  imported row to Claim lineage, and grants no Finding or clean-control authority. Exact byte,
  row, field, and opaque-boundary ceilings fail closed; malformed, nonterminal, over-budget, and
  mutated traces localize without suppressing unrelated audit evidence, and replay is exact.
- ✅ **D09** Accepted ADR-0033 parses bounded strict-UTF-8 `.R` sources through pinned
  Tree-sitter-R and, when available, an isolated non-evaluating base-R parse-data helper. Separate
  ParserResults preserve exact direct/namespaced call spans and localized disagreement; dynamic
  dispatch, dataflow, formulas, package behavior, execution, and scientific meaning remain
  explicit unknowns.
- ✅ **D10** Accepted ADR-0034 parses bounded strict-UTF-8 nbformat-v4 `.ipynb` files as inert JSON.
  It preserves exact cell and saved-output semantic pointers, literal execution counts, localized
  structural failures, and project-local parser-cache behavior without starting a kernel,
  rendering content, or treating saved output as reproduced evidence. The separate D12 bridge can
  parse exact Python/R cell syntax, and D13 can transport independently verified bytes to existing
  exact static adapters. D14 adds only the selected-container founder-question scope; Claims,
  general scientific interpretation, and runtime order remain unavailable.
- ✅ **D11** Accepted ADR-0035 parses bounded strict-UTF-8 `.qmd` sources without invoking Quarto,
  Pandoc, kernels, filters, extensions, or project code. Exact front-matter, prose, literal-engine
  cell, option, evaluation-declaration, and collision-free document-chunk locations are preserved;
  YAML, rendering, runtime, artifact lineage, Claims, and scientific meaning remain opaque. The
  separate D12 bridge can parse exact Python/R cell syntax and D13 can transport independently
  verified cell bytes. D14 adds only the selected-container founder-question scope without
  changing the other limits.
- ✅ **D12** Accepted ADR-0036 re-extracts and digest-verifies at most 200 exactly declared Python
  or R cells from bounded Jupyter/Quarto parents, then delegates their bytes to the existing static
  parsers without execution. Child ParserResults and Python Operations retain exact notebook-cell
  or document-chunk locations and collision-free descendant-cache scopes. Conflicting/unsupported
  languages, cross-cell state, output provenance, Claims, and runtime meaning remain explicit
  unknowns.
- ✅ **D13** Accepted ADR-0037 independently re-extracts and verifies cell bytes before exposing
  them to the immutable scientific-check context. Same-path cells retain distinct source
  identities; evidence reconstructs exact notebook-cell or absolute Quarto chunk citations. One
  existing bounded Python static adapter can consume such a cell under its unchanged grammar, but
  ADR-0037 alone grants no scope. Quarto prose, notebook markdown, cross-cell state, and outputs
  remain unavailable.
- ✅ **D14** Accepted ADR-0038 admits one exact containment scope: a verified active-or-unspecified
  cell inside the full-digest selected notebook or Quarto source Artifact can support the existing
  founder-orientation scientist question. The scope path is FileRecord to selected Artifact to
  PublicationSurface. It does not establish execution, primary-versus-sensitivity role, output
  lineage, intent, correctness, detector eligibility, or a Finding. Unselected cells and Quarto
  cells explicitly marked `eval: false` remain unscoped.
- ✅ **D15** Accepted ADR-0039 admits one exact separate-source scope: Python parser `0.15.1`
  recognizes a uniquely bound source-parent `Path` root and a safe literal report writer. Exactly
  one statically reachable producer can connect the source FileRecord to the exact full-digest
  selected report Artifact and PublicationSurface. Unused, competing, dynamic, absolute,
  parent-traversing, and non-source-root writers remain unscoped. The join supports only the
  existing founder-orientation scientist question and compatibility Disclosure; execution,
  primary-analysis status, numerical causality, detector eligibility, and Findings remain unknown.

## Epic E — Walking-skeleton semantics

- ✅ **E01** Public v0.6.0 scalar, interval, vector-summary, and table-cell `ObservedResult`
  variants validate with explicit epistemic slots. The runtime emits the bounded verified scalar
  directly, replay preserves unknowns, and public v0.5 migration invents no observed evidence.
- ✅ **E02** Locked Claim and ScientificContract records validate against public v0.6.0 schemas.
- ✅ **E03** Comparison-orientation normalization exists with a hard-negative fixture.
- ✅ **E04** Material-unknown propagation produces questions and conditional concerns instead of Findings.
- ✅ **E05** Semantic-lock digest and model-free replay exist.

## Epic F — Detector and admission

- 🟡 **F01** The fixture-only manifest is now hash-loaded into an explicit nonpublic qualification envelope; real detector qualification records remain Phase 8 work.
- ✅ **F02** The first detector exercises applicable, insufficient-semantics, and negative coverage states.
- ✅ **F03** Every finite check is independently executable, evidence-linked, and records completed, unavailable, or counterevidence outcomes.
- ✅ **F04** Finding admission is a generic controller service; detectors return candidates and Finding drafts but cannot self-admit.
- ✅ **F05** Contradiction, hard-negative, unknown-orientation, and unresolved-unit fixtures exist.
- ✅ **F06** Admission mutation tests force every material premise through unknown, conflicted, and refuted states and verify that none becomes a Finding.
- ✅ **F07** Accepted ADR-0040 freezes one real-path experimental detector candidate. It requires
  a human review requirement, agreeing selected-report and exact static-source operands, the
  full-digest selected-output graph, and ten completed finite checks. Matching, unsupported,
  weak-identity, ambiguous, and per-check counterevidence controls suppress the candidate. It is
  unqualified, permits only Disclosure output publicly, and cannot emit a production Finding.
- ✅ **F08** Accepted ADR-0041 and immutable schema v0.16.0 add a separate exact
  `bounded_analysis_method_conflict_v1` static qualification profile. Its evaluator-owned verifier
  independently derives the report/source operands, selected-output writer, and human review
  authority from immutable inputs; missing identity, ambiguity, unsupported dataflow,
  counterevidence, and drift fail closed. Static fixture, Stage-3, report, canonical storage,
  migration, packaging, and replay paths pass local controls without executing project code. This
  completes the qualification mechanism only; answer-blind cross-provider evidence and promotion
  remain pending.
- 🟡 **F09** Experiment 0026 remains the immutable, superseded v0.1 readiness history. Experiment
  0027 now freezes the final modular detector `0.2.0`, exact method binding, independent adapter
  and verifier dependency closure, schema-v0.17 typed profile, six portfolio roles, and Stage-1/2/3
  prompts before any v0.2 case assignment. The one-time builder reproduces the committed directory
  byte-for-byte and refuses replacement. Separate evaluation CLI commands now freeze, assign,
  independently verify, and byte-replay the typed path while preserving the historical v0.1
  commands. The freeze contains no case, label, reviewer identity, transcript, detector output,
  threshold, qualification, or promotion claim. Exact no-replace assignments and authenticated
  two-provider captures remain the external portion of F09.
- ✅ **F10** Accepted ADR-0042 consolidates the method-check extension boundary around an explicit
  digest-bound registry, isolated adapter identities, a generic typed conflict evaluator, and an
  implementation-independent qualification engine. Coordinated schema v0.17.0, three unlike
  extension shapes, and the current founder profile's complete fixture/Stage-3/report/storage/
  RO-Crate replay path pass without controller, Finding-admission, or public-schema special cases.
  The detector remains experimental and unqualified; a new external portfolio is F09's remaining
  evidence boundary.
- ✅ **F11** Accepted ADR-0043 uses that extension boundary for two independent question-only
  expected-count checks: background construction and focal-target handling. Exact selected-report
  declarations, co-occurrence, conflicting/partial hard negatives, human Answer comparison, and
  byte-replay pass on the preserved Hi-C development case. The checks have no detector binding,
  qualification, Finding permission, execution claim, or answer-key-derived production authority.

## Epic G — Reporting

- ✅ **G01** Assessment counts are generated from records.
- ✅ **G02** Self-contained autoescaped HTML is rendered from the audit bundle.
- ✅ **G03** Coverage denominators are derived from the canonical file inventory, exact parser results, deeply inspected source paths, extracted claims, and detector results; uninspected paths and the missing selection envelope are explicit rather than folded into negative coverage.
- ✅ **G04** Report rendering enforces assessment counts, non-certification policy, bounded Finding language, conditional wording, linkage, and type-specific impact fields.
- ✅ **G05** Finding, concern, disclosure, and claim cards include internal source navigation and bounded escaped evidence excerpts.

## Epic H — End-to-end acceptance

- ✅ **H01** `sc-referee demo` executes the complete synthetic walking-skeleton path.
- ✅ **H02** `sc-referee replay` regenerates derived records with model access absent.
- ✅ **H03** A forced post-lock deadline checkpoints a schema-valid partial bundle, SQLite index, HTML report, terminal state, and explicit unevaluated detector coverage. The pre-lock bundle schema gap is registered.
- ✅ **H04** Normalized Finding, ConditionalConcern, MaterialQuestion, Disclosure, and DetectorResult records replay byte-for-byte.
- ✅ **H05** Every local Milestone 0 gate passes across Python 3.11–3.13, and clean hosted push and
  pull-request matrices pass on all three versions.
- ✅ **H06** `export-ro-crate` creates a deterministic attached RO-Crate 1.3 ZIP from an
  integrity-verified audit without changing native bundle, report, semantic-lock, or canonical
  record bytes. It excludes disposable SQLite, requires explicit declared package author/license
  metadata, publishes without replacement, emits a schema-valid `ROCrateExport`, and passes an
  offline closed-profile validator from the built wheel. The digest profile is recorded in
  Experiment 0006; external third-party validation is not claimed.
- ✅ **H07** `generate-capability-matrix` projects a closed, canonical, independently digested
  parser/profile/detector/qualification/version manifest set into a public `CapabilityMatrix`.
  The bundled release set contains 15 narrow entries, including ADR-0033's three separate
  detector-free DESeq2, edgeR, and limma-voom call inventories. The two prior attached detectors
  are joined by ADR-0040's cross-surface analysis-method detector; all three are experimental,
  unqualified, and Finding-ineligible, while the other 12 entries have no detector. ADR-0034's
  Jupyter and Quarto entries are structural inventory only. ADR-0036 adds one separate detector-free
  container-cell static-language bridge with partial operation extraction and semantic modeling
  explicitly not started.
  Qualification records and tested/inferred versions remain empty. Mutation,
  unresolved-reference, canonicalization, overwrite, and installed-wheel reproduction tests pass.

## Epic I — First general-project product slice

- ✅ **I01** `sc-referee audit` snapshots and inventories an arbitrary repository, statically
  parses supported Python, Markdown, R Markdown, bounded `.R`, bounded nbformat-v4 notebook, and
  bounded Quarto paths and exact declared Python/R cells without executing project code, and
  localizes parser failures, unsupported scientific source types, and opaque operations.
- ✅ **I02** The general audit emits a schema-valid partial-evidence bundle, self-contained report,
  disposable SQLite index, semantic lock with zero model calls, and model-free replay.
- ✅ **I02a** General runs display and bind their execution-disabled deadline policy, check
  cancellation and host/deadline signals at durable stage boundaries, preserve pre-lock journals,
  and emit integrity-verifiable post-lock partial reports.
- ✅ **I03** An explicitly selected Markdown surface promotes only exact deterministic directional
  literals into final Claim records with draft all-unknown ScientificContracts and partial
  aggregate lineage: report origin is evidenced while result/computation/input/execution/semantic
  origins remain explicitly incomplete. Experiment 0011 now schedules its separate exact mechanical
  detector on these Claims, but missing result/writer evidence abstains and no Finding is emitted.
- ✅ **I04** Accepted ADR-0003; a repository with no publication-like artifact completes with an
  unresolved empty-candidate surface, one linked open question, explicit unavailable coverage,
  zero detector targets, and deterministic replay.
- ✅ **I05** Public WorkItems, bounded proposed SemanticAssertions, scope-bound scientist Answers,
  exact-snapshot linked resume segments, explicit pre-lock states, post-lock rejection, conflict
  preservation, structured resolution of all 17 ScientificContract dimensions, and model-free
  replay pass controller and CLI tests. Omitted dimensions remain unknown and observed lineage is
  never inferred from scientist intent.
- ✅ **I06** Active experiment 0002 independently recomputes one exact filtered mean-difference
  profile from immutable Python/CSV snapshot bytes, emits a public ObservedResult, and binds it to
  a uniquely aligned literal Claim with `partial` lineage. Nonaligned claim objects abstain, typed
  publication resolution preserves the observed evidence and replay is identical. Experiment 0011
  may schedule the result only with exact static report-writer flow; no detector is qualified.
- ✅ **I07** Accepted ADR-0005/schema 0.8.0 publishes six independent Claim lineage grades plus
  public DataAsset, Variable, AnalysisDecision, SelectionEnvelope, Execution, and Environment
  records. The fail-closed v0.7→v0.8 migration, typed reference/report/coverage checks, JSONL,
  SQLite, replay, and bounded runtime promotion pass. Auditor verification remains distinct from
  missing project execution, and scientist Answers change only semantic origin.
- ✅ **I08** Exact Python/Markdown ParserResults use a content-addressed, project-identity-bound
  cache below `.sc-referee/`; unchanged inputs hit, changed or removed inputs invalidate only their
  parser key, weak inputs remain uncached, cross-repository reuse and unsafe symlink boundaries are
  rejected, and a digest-bound non-certifying `sc-referee diff` reports stable path changes.
- ✅ **I09** Linked semantic interaction segments persist one digest-bound deadline ledger. Each
  resume receives a fresh plan, prior segments remain linked, only explicit scientist-wait time is
  paused, pre-lock hard deadlines terminate durably, and post-lock expiry retains partial coverage.
- ✅ **I10** Supported Python list comprehensions promote only exact literal predicates into
  observed partial AnalysisDecision/SelectionEnvelope records; dynamic thresholds remain
  unresolved. Static Python environment declarations produce partial or unavailable project
  Environments, and a Claim with missing project-execution origin produces a proposed,
  nonauthorizing external ReproductionRequest rather than running the project.
- ✅ **I11** Python parser keys now bind exact literal file dependencies as well as the source
  itself. Per-source static graphs and the repository's bounded-lineage plane use versioned,
  project-local descendant keys; exact warm runs skip both computations, report-only changes
  preserve Python descendants, referenced-data changes invalidate the parser and both descendants,
  removal invalidates their index entries, public CacheEntry output refs resolve, and replay
  preserves the records. The aggregate bounded-lineage cache still invalidates as one unit when
  any relevant Python/data dependency changes.
- ✅ **I12** Accepted ADR-0006 projects exactly one public PerformanceRecord for every completed
  general or interaction semantic lock. The record is measured only through semantic lock,
  preserves exact current-segment active/paused time, current-run parser-cache counts, and metered
  snapshot identity reads, counts only controller-observed provider calls, labels all unmetered
  quantities as unknown, and replays byte-for-byte. Reports explicitly deny that it is total run
  duration. A linked-segment regression test also preserves prior SemanticAssertions referenced by
  carried lineage instead of leaving dangling evidence links.
- ✅ **I13** A project-local, nonblocking exclusive writer lease now spans parser and descendant
  cache work. A contending audit continues without cache reads or writes, does not wait against its
  deadline, leaves both mutable indices unchanged, and can be followed by a coherent invalidating
  run and exact warm hit. A symlinked lease target is rejected. Cryptographic authenticity remains
  a separate trust-boundary decision in proposed ADR-0007.
- ✅ **I14** Static Python selection evidence now recognizes exact single-predicate generator,
  set, and dictionary comprehensions plus same-base boolean subscriptions and `.loc` selections.
  Only literal scalar comparators promote partial AnalysisDecision/SelectionEnvelope records;
  dynamic thresholds and compound predicates remain unresolved, runtime selection semantics and
  execution remain unclaimed, no project code runs, and replay is byte-identical.
- ✅ **I15** Accepted ADR-0007 authenticates parser blobs, descendant blobs, and both mutable
  indices with HMAC-SHA-256 under an external high-entropy key. The default provider uses an
  explicit 32-byte environment key for headless/CI or a supported platform credential store;
  absent, invalid, or inaccessible credentials disable persistence without failing the audit.
  Payload/index forgery, key rotation, secret non-persistence, and nested symlink boundaries are
  tested. Active arbitrary same-user processes with credential access remain out of scope.
- ✅ **I16** Static project Environment inspection separates nested Python environment roots and
  reads bounded literal runtime declarations from standardized project metadata, Poetry, Pipenv,
  uv, pixi, setup.cfg, Conda YAML, `.python-version`, and `runtime.txt`. Differing declarations
  remain unresolved, malformed or oversized runtime declarations make identity opaque, dependency
  files remain exact FileRecord references, and no declaration is treated as execution evidence.
- ✅ **I17** Exact conjunctive Python selections now cover multiple comprehension `if` clauses and
  same-base boolean subscriptions joined by `&`. Every fully literal conjunct becomes its own
  partial AnalysisDecision/SelectionEnvelope; any dynamic or unsupported conjunct makes the whole
  compound predicate unresolved. Disjunctions, chained comparisons, runtime semantics, execution,
  rationale, rejected alternatives, and outcome influence remain unclaimed.
- ✅ **I18** An exactly identified publication candidate now reuses a static Artifact only when a
  literal Python `Path` output targets the same logical path and the Artifact carries the exact
  snapshotted digest. Claims retain that source-level writer edge through typed operation refs and
  replay. The edge does not establish that the code ran, that its write argument equals the
  snapshotted bytes, or that it produced the wording; dynamic output paths do not link.
- ✅ **I19** A literal `Path.write_text`/`write_bytes` operation now consumes a supported result
  Artifact only when its single data expression has an exact whitelisted source path to one
  uniquely defined bounded computation call. The linked Claim retains the result producer and
  report writer while result origin stays partial and project execution stays missing. Variable
  aliases, duplicate function bindings, conditional or opaque render expressions, and ambiguous
  report writers abstain; replay remains identical and no Finding path was added.
- ✅ **I20** The same static result flow now crosses one top-level single-assignment alias only
  when the supported function is uniquely bound before the assignment, the alias is bound exactly
  once, and a later top-level writer uses it through the whitelisted render grammar. Reassignment,
  deletion, import/name shadowing, use-before-definition, conditional/nested writers, format
  specifications, and opaque transforms abstain. The parser/cache component is versioned `0.6.0`;
  Claim result origin remains partial and replay emits zero new Findings.
- ✅ **I21** Ordered module-level single-assignment chains now carry a uniquely bound supported
  result through the whitelisted render grammar into a later top-level report writer. Every name
  must have exactly one module binding and consume only earlier accepted aliases; chains stop after
  eight edges. Over-limit, mutated, nested, conditional, and opaque paths abstain. The parser/cache
  component is versioned `0.7.0`; Claim result origin remains partial and replay emits zero new
  Findings.
- ✅ **I22** The bounded result flow now crosses assignments inside one uniquely bound,
  undecorated, synchronous, module-level, zero-parameter renderer when its entire body is a
  straight-line sequence of result-carrying assignments and literal writes. No call site or
  execution is inferred. Parameters, branches, mutation, nested renderers, unrelated statements,
  shadowed render wrappers, and chains beyond eight edges make the whole renderer abstain. The
  parser/cache component is versioned `0.8.0`; Claim result origin remains partial, project
  execution remains missing, replay is identical, and no Finding path was added.
- ✅ **I23** One uniquely bound, undecorated, synchronous renderer with one required positional
  parameter now accepts exactly one later direct module-level call whose positional argument
  resolves to one supported result through the existing bounded alias grammar. The parameter and
  local aliases share the eight-edge ceiling. Missing/multiple/conditional calls, defaults,
  keywords, mutation, transforms, branches, and ambiguous bindings abstain. The parser/cache
  component is versioned `0.9.0`; the edge remains static-only, Claim result origin remains
  partial, project execution remains missing, replay is identical, and no Finding path was added.
- ✅ **I24** The unique renderer-call profile now permits additional required positional
  presentation parameters only when exactly one argument resolves to one supported result and
  every other argument is constant-only under the existing render grammar. Dynamic, defaulted,
  keyword-bound, mutated, output-path, multi-result, no-result, multi-call, branched, and opaque
  forms abstain. The parser/cache component is versioned `0.10.0`; exact public writer/result
  edges and Claims replay, project execution remains missing, and no Finding path was added.
- ✅ **I25** One literal-bound renderer parameter can now resolve the output Artifact when the
  unique call supplies a direct safe repository-relative POSIX string and the unmodified parameter
  is the sole `Path(...)` receiver of at most one parameter-bound supported write. Dynamic/module
  aliases, transformed,
  absolute, traversal, backslash, mutated, keyword, ambiguous-call, and no-result forms abstain.
  Parser/cache component `0.11.0` preserves exact path/result/writer edges and model-free replay;
  project execution and snapshotted-byte production remain missing and no Finding path was added.
- ✅ **I26** The same unique renderer call now reconstructs exact mixed positional/keyword binding
  to required positional parameters. Missing, extra, duplicate, positional-only-by-keyword,
  unpacked, defaulted, keyword-only, variadic, dynamic-literal, multi-result, and ambiguous forms
  abstain. Parser/cache component `0.12.0` preserves exact result/path/writer edges regardless of
  call-site keyword order; replay is identical, project execution remains missing, and no Finding
  path was added.
- ✅ **I27** One uniquely bound top-level static formatter with optional docstring and exactly one
  bounded return may now be the complete payload of one later literal report writer. Required
  arguments bind exactly, one must carry one supported result, and the return stays inside the
  constant/f-string/addition/`str`/`repr` grammar. Multiple calls, aliases, assignments,
  decorators, annotations, defaults, use-before-definition, opaque transforms, and missing/two
  results abstain. Parser/cache component `0.13.0`—not public schema v0.13.0—replays exact writer
  flow without claiming formatter or project execution, and no Finding path was added.
- ✅ **I28** That unique formatter result may now cross exactly one top-level single-name
  assignment with one binding and one module load, when that load is the complete argument of one
  later top-level literal writer. Rebinding, tuple targets, extra loads, multiple writers,
  transformed aliases, writer-before-assignment, and nested/conditional consumers abstain.
  Parser/cache component `0.14.0` records `single_static_formatter_assignment`, replays exact
  public flow, retains missing execution, and adds no Finding path.
- ✅ **I29** That formatter result may now cross one strictly linear top-level single-name
  assignment chain within the shared eight-edge ceiling. Every name has one binding and one load;
  each intermediate feeds exactly one next assignment, and only the terminal feeds one later
  literal writer. Forks, merges, rebindings, repeated loads, multiple writers, unused
  intermediates, nested consumers, and over-limit chains invalidate the whole chain. Parser/cache
  component `0.15.0` records `static_formatter_assignment_chain`, replays exact public flow,
  retains missing execution, and adds no Finding path.

## Epic J — Agent integration

- ✅ **J01** A repository-scoped Codex `scientific-audit` skill has current discovery metadata,
  validated structure, the typed pre-lock workflow, explicit epistemic/execution boundaries, and a
  process-isolated CLI round-trip. An independent fresh-context agent completed a mixed-language,
  adversarial-repository audit through human Answer, semantic lock, and model-free replay without
  executing project code; its two clarity defects were incorporated into the skill and report.
- ✅ **J02** The CLI exposes integrity-verified status, WorkItem queues and packets, bounded proposal
  submission, public Answer recording, explicit semantic lock/detect/report transitions, and
  model-free replay. MCP is a later transport over this stable local protocol.
- ✅ **J03** The stable protocol is now packaged as a repository-contained Codex plugin. Its
  manifest and embedded `scientific-audit` skill pass the official validators, and repository tests
  require the packaged skill to remain byte-identical to the independently qualified authoritative
  copy. The qualification environment reports `sc-referee@personal` installed and enabled, and its
  Codex cache is byte-identical to the source. After Codex quit and restarted, a fresh task loaded
  `sc-referee:scientific-audit` from that personal cache. No MCP or Claude adapter is claimed. No
  scientific requirement or schema was changed for legacy public GitHub compatibility.

## Epic K — Isolated answer-side evaluation

- ✅ **K01** A separately packaged `sc-referee-evaluation` wheel now reconciles one exact
  BenchmarkFixture/BenchmarkAdjudication/AgentReview packet without entering the production wheel.
  It validates public schemas, exact references and case identity, 4+2 cross-provider participation,
  unique execution contexts, frozen Stage-1 chronology, Stage-2 dissent, and fixture-label
  compatibility. K03 now supplies exact canonical root-cause reconciliation; labels still remain
  withheld until all independent source-evidence gates pass, and ambiguous labels remain excluded.
- ✅ **K02** Exact file-span evidence now resolves against the public RepositorySnapshot,
  FileRecord, and full-digest AssetIdentity chain plus non-symlink materialized bytes, line spans,
  and quoted text. The resolver reconstructs stable FileRecord/AssetIdentity IDs and the complete
  content-addressed snapshot manifest digest, so coordinated byte-and-identity substitution fails.
  `sc-referee-eval` persists a canonical input-digested, self-digested validation report and refuses
  overwrite. Other source media remain unsupported rather than inferred.
- ✅ **K03** Accepted ADR-0008 and immutable schema v0.9.0 add review-local candidate identities,
  exact Stage-2 membership reconciliation, and public `AdjudicatedRootCause` records. Candidate IDs
  are recomputed from closed review content; two fresh provider families must select the identical
  cross-provider Stage-1 set; disagreement, mutation, dissent, missing refs, and legacy v0.8
  positives fail closed. The isolated CLI creates and model-free replays the digest-bound scientific
  label freeze. Canonical JSONL, disposable SQLite, AuditBundle validation, and the static report
  preserve the record without turning it into a Finding or detector score. Positive admission is
  limited to the declared fixture scope and additionally requires immutable source resolution.
- ✅ **K04** A deterministic allowlist builder creates a fresh blind-review workspace containing
  only declared task, data, workflow, report, output, and execution-evidence files. Known
  answer-side paths, full digests, UTF-8/UTF-16 literal markers, embedded raw hidden-file bytes,
  Unicode/newline-normalized hidden text, symlinks, and existing destinations fail closed; the
  runner-side manifest remains outside the workspace and discloses scanner limits.
- ✅ **K05** Digest-bound Stage-1 packets validate exact blind submissions and freeze only after
  two independent reviews from each of two providers. Stage-2 packets expose the frozen review
  projection and explicit answer-side evidence while still hiding detector output, require fresh
  contexts and falsification records, and freeze the scientific adjudication before Stage 3.
  `sc-referee-eval` exposes the workspace, packet, panel-freeze, label-freeze, and case-validation
  operations as fail-closed subcommands. Every CLI freeze now consumes a verified write-once
  capture directory containing the canonical review, exact packet, and digest-matching transcript
  bytes; loose review JSON cannot bypass capture. Synthetic tests exercise the full artifact
  chronology; capture does not authenticate the reviewer and no real review is claimed.
- ✅ **K06** Accepted ADR-0009, ADR-0010, and ADR-0011 plus immutable public schemas v0.10.0 and
  v0.11.0 define qualification-only detector candidates, fresh Stage-3 equivalence reviews, exact
  case outcomes, and deterministic problem-cluster metrics while keeping promotion closed. The
  fail-closed v0.9→v0.10 and v0.10→v0.11 migrations and active runtime schema switch pass locally.
  Experimental Finding-shaped DetectorResults use only the closed
  `evaluation_finding_candidate` state and remain permanently unable to enter production Finding
  admission.
  The Stage-3 implementation builds post-freeze packets, validates write-once fresh
  cross-provider captures, and deterministically reconciles exact candidate/root mappings into
  positive, hard-negative, missed, duplicate-safe, overstated, false-localization, and excluded
  case outcomes. Each new outcome retains one digest-bound projection per exact DetectorResult;
  one result remains one opportunity even when it sources several candidate manifestations. The
  isolated calculator and CLI deterministically compile all twelve accepted ratios and 10,000
  problem-cluster bootstrap replicates. Production report validation independently recomputes the
  input digest, exclusions, public counts, every numerator/denominator/estimate, and every interval;
  mutations fail closed. Canonical JSONL/SQLite, CLI byte replay, AuditBundle validation, wheel
  isolation, and the static report preserve the evidence without granting Finding or promotion
  authority.
  The earlier evaluation-private, write-once `compare-stage3` inventory command reveals and binds
  one exact detector's public AuditBundle only after the scientific-label freeze. It validates the
  fixture snapshot, audit run, result/Finding references, detector version, manifest digest, and
  exact declared scope, but deliberately emits no correctness class or metric; the separate fresh
  Stage-3 panel and reconciler own equivalence. A separate `grade-json` experiment now
  compares one exact canonical JSON
  value through the same reconstructed snapshot manifest without executing project code or
  inferring scientific correctness. The first fixture generator emits only detector/issue-scoped
  `ambiguous_fixture` records from excluded adjudications, with every proof obligation false and
  execution absent; it refuses eligible labels and unresolved public record refs. External reviewer
  invocation and calibration, real positive/verified-good/hard-negative fixture generation, more
  advanced transformed-content leak detection, additional grader profiles, real-corpus label
  admission, independent detector-equivalence captures, and pilot-informed promotion thresholds
  remain.

- 🟡 **K07** Build eligible positive, verified-good, and hard-negative fixture-construction paths
  over exact answer-side evidence, then exercise the complete protocol on an answer-blind external
  corpus. Synthetic construction can validate mechanics but cannot count as reviewer independence,
  real-corpus qualification evidence, or detector promotion. Numeric promotion thresholds remain
  deferred to a later pilot-informed ADR. A capture-only CLI and deterministic generator now emit
  a public-development positive fixture only after the complete 4+2 panel, canonical-root, exact
  snapshot/source, and label-admission checks replay successfully; mutation fails closed and no
  project code executes. Its canonical output and the other isolated evaluation artifacts now use
  atomic create-without-replace, so an existing file, symlink, or concurrent writer cannot be
  overwritten after the preflight check. Accepted ADR-0012 and immutable schema v0.12.0 bind every
  eligible label to exact public record digests plus capture, packet, transcript, workspace,
  snapshot, freeze, and chronology evidence. The control CLI now emits synthetic verified-good,
  scope-verified-good, and hard-negative fixtures only after exact contract/operation review and
  existing execution evidence validate. Clean controls require authorized successful
  project-workflow execution under qualifying rootless OCI; subprocess, auditor, failed,
  network-enabled, unsafe-fallback, unresolved-scope, and evidence-mutation cases fail closed.
  This v0.12 proof is now known to omit the complete linked authorization/lock/artifact closure;
  deferred ADR-0015 or an equally conservative later proof-basis ADR must be implemented before
  any execution-dependent clean control is qualification-eligible. Accepted ADR-0017 does not
  weaken that rule or make the built-in executor an MPP prerequisite.
  Stage 3 replays complete private proof inputs before admission, metrics bind the exact fixture
  digest/status, reports re-resolve bundled public proof inputs, and v0.11 migration invents no
  proof or metric authority. The remaining K07 work is the deliberately external answer-blind
  corpus run with authenticated independent reviewers; synthetic controls are not qualification.
  Accepted ADR-0022 and immutable schema v0.15.0 now add a separate non-executing control family
  for the exact bounded direction detector. Its answer-side verifier independently rederives the
  complete selected-report/raw-table/static-writer closure from immutable bytes, rejects every
  incomplete or ambiguous boundary, and emits distinct static verified-good and hard-negative
  fixtures. Stage 3 enforces label-before-proof-before-detector chronology, metrics and reports
  retain proof-family strata, migration invents no static authority, and project code is never
  executed. These passing synthetic controls establish the mechanism only; they are not real
  cross-provider qualification evidence and do not promote the detector.
  Evaluation-private Experiment 0005 adds a canonical, non-executing preflight for an already-local
  pinned GeneBench-Pro public package. It verifies the exact manifest, 77-file checksum inventory,
  problem/config shapes, visible-input plan, and no-answer-disclosure boundary without importing
  the grader. The full official initial revision passes with consistent CC-BY-4.0 identifiers and
  is admitted only for public-development preparation. The current MIT-labelled head fails closed
  because its LICENSE and README do not match its checksum inventory. Experiment 0012's authorized
  fresh-context Hi-C workflow reran byte-identically but was wrong on all three required values;
  its frozen audit produced no Claim, ObservedResult, DetectorResult, or Finding. Experiment 0013
  canonically records those three outside-tolerance comparisons without executing either workflow
  or reference grader. The real run is public-development coverage evidence, not authenticated
  reviewer qualification or promotion evidence.

## Historical capability-development record

Accepted ADR-0017 makes the `0.6.0` MPP evidence-first and non-executing. Do not spend the next
implementation cycle on Podman, dependency installation, or project-code launch.
ADR-0015 and ADR-0016 are deferred; `execute-authorized` remains fail-closed before registry or
runtime access, and the existing v0.14 mechanics remain synthetic-test-only historical scaffolding.

Proceed in this order:

1. Broaden bounded inspection of existing inputs, outputs, manifests, summaries, logs, and traces
   without fully reading large data or executing project code. Preserve exact identity grades and
   localize every unsupported or over-budget boundary. The first end-to-end regression now audits
   and replays a project containing a 10-billion-byte sparse data asset after reading only 12,288
   sampled bytes; it does not materialize the asset and proves embedded project code did not run.
   Experiment 0008 imports a narrowly defined root SHA-256 checksum manifest as declared identity
   evidence while explicitly withholding independent target-byte verification. Experiment 0009
   covers exact CSV/TSV headers for fully captured inputs and outputs while preserving unknown row,
   type, runtime, and scientific semantics. Experiment 0010 now imports one exact default Nextflow
   `trace.txt` profile as weak external terminal-task assertions without Claim or Finding authority.
   This acquisition foundation is sufficient to start item 2; broader summaries and trace formats
   remain later evidence adapters driven by concrete detector or corpus needs.
2. ✅ Experiment 0011 implements the first real domain-neutral detector behind the experimental
   maturity ceiling. It requires exact literal Claim/result/Operation/writer alignment and covers
   applicable, covered-negative, positive, hard-negative, ambiguous, unsupported, decisive-
   counterevidence, and mutation cases. Evaluation candidates cannot become Findings.
3. Exercise that detector through the answer-blind evaluation protocol on a real external corpus.
   Do not represent synthetic fixtures, public-development answers, or unauthenticated agents as
   independent qualification. Experiment 0005 now has a full real-package preflight of one valid
   immutable GeneBench revision. Experiment 0012 now prepares one exact
   `hic_sv_masked_loop_strength` workspace with task plus staged data only and keeps all answer-side
   material runner-side. A pre-workflow audit/replay correctly emits no Claims or DetectorResults
   and leaves the gzip inputs explicit as uninspected. An authorized fresh-context agent has now
   produced a reproducible but wrong workflow. Its frozen audit also emitted no Claim,
   ObservedResult, DetectorResult, or Finding; Experiment 0013 records all three numeric fields
   outside tolerance. The concrete gap is method-contract localization: the visible prompt does
   not state the authoritative expected-count model, while the answer-side report shows that the
   workflow's same-distance mean conflicts with a masked condition-specific negative-binomial
   model. Preserve that authority boundary when implementing the next bounded premise. Real
   independent adjudication and Stage-3 comparison remain; keep the stale-checksum head rejected.
   ✅ Accepted ADR-0018 now has an evidence-bound typed ledger and the closed
   `expected_count_background_v1` compatibility detector, with no schema release or execution
   requirement. Exact Markdown Claim, reported-method, and sensitivity grammars produce a bounded
   unresolved-background question before answer access. Human Answers retain their ineligible
   declarations while separate fail-closed controller derivations may establish scoped intent.
   Exact conflicts remain experimental candidates and cannot become Findings; matching, missing-
   authority, unsupported, eight finite suppressor, mutation, replay, and non-Hi-C copy-number
   portability cases pass. A distinct claimless `method-contract` CLI and `$method-contract` skill
   freeze analysis-level intent before coding and bind it to a later Claim only when the parent
   lock and governing task identity verify exactly. Experiment 0014's real GeneBench pre-answer
   rerun asks which background governs with zero Findings; its separate answer-side diagnostic
   localizes the public reference conflict without mutating production or entering metrics or
   promotion. Broader profiles, independent answer-blind review, qualification, and promotion
   remain pending. Experiment 0015 then ran three additional fresh-context, answer-isolated
   GeneBench workflows. Their workspaces were frozen and replayed before grading: LD-aware MVMR
   passed both fields; Wright-Fisher selected the correct locus but missed the selection coefficient
   after treating an average ancient-DNA error as symmetric; and the carrier-risk workflow passed
   both roster frequencies but missed three conditional or standardized quantities after using a
   permissive founder call and uncoupled calibration. The evaluation adapter now handles only the
   exact bounded numeric and mixed required-string/numeric package contracts encountered. These are
   two distinct one-case failure families, not yet a recurring basis for another production method
   profile. Experiment 0016 now confirms the proposed failure descriptions against the unchanged
   source with four evaluation-only AST profiles. Corrected controls pass, unrelated source stays
   unsupported, the Wright-Fisher ablation recovers the released coefficient, and an evaluator-
   owned carrier reconstruction recovers all five released values only after the marker, coupled-
   calibration, and within-cell-order repairs. These profiles remain outside the production
   detector manifest and capability matrix pending independent recurrence and hard negatives.
   Experiment 0017's three authorized targeted follow-ups did not provide that recurrence: all
   twelve existing-profile applications remained `unsupported_path`. Their frozen grades instead
   expose three different one-case method families, with only the ambient technical-group omission
   closely reproduced by a public reference ablation. The evaluation grader now accepts the exact
   encountered single-numeric and integer/numeric composite contracts, but no profile, detector,
   schema, metric, or capability claim changed. Seek recurrence for an exact abstract obligation or
   bind it through exact governing evidence or a scope-bound scientist Answer before adding
   another method profile.
   Experiment 0018 completes the ten-case public-development sweep with the three remaining QTL,
   CRISPRi/CasRx, and population-genetics workflows. All three grades are outside contract, all
   three audits retain zero Findings, and all twelve existing-profile checks again return
   `unsupported_path`. One of ten workflows is wholly within contract; the nine failures span
   heterogeneous method families. The next bounded milestone is therefore a proposed interactive
   post-hoc method ledger over existing v0.14.0 dimensions, not nine case-specific detectors.
   ✅ Accepted ADR-0019 keeps `scientific-audit` primary, permits bounded scientist questions before
   semantic lock, and keeps pre-analysis `method-contract` optional. Re-audits of existing failed
   workspaces plus unknown, conflict, false-self-compliance, and covered-good controls must precede
   any capability claim. ✅ Experiment 0019 implements `posthoc_method_ledger_v1` with its three
   closed comparison forms, canonical pre-lock scientist Answers, explicit unknown retention, and
   fixed-workspace validation. QTL and pulse-admixture produce review-scoped conflict candidates,
   MVMR produces a covered negative, and CRISPRi/CasRx remains unknown. The case-specific source
   profiles remain evaluation-only. A synthetic false-self-compliance control also proves that a
   report claim cannot override contradictory static source. ✅ Experiment 0020 completes the
   authorized fresh-context raw-repository skill run: the independent agent uses the skill,
   preserves answer isolation, interprets coverage correctly, and replays model-free, but the
   ordinary audit creates no Claim, ScientificContract, method assertion, or MaterialQuestion.
   The transport passes while the required scientist interaction path fails before the question
   boundary. ✅ Accepted revised ADR-0020 implements the remedy as one deterministic modular
   scientific-check registry with method-level checks, language/tool adapters, and a shared
   analysis-scoped question path. QTL founder orientation, pulse-admixture exposure, MVMR
   whitening, and a removable conformance module all use the same registry and controller seam;
   no production applicability rule keys on GeneBench identity. Selected-report observations can
   create a bounded scientist question, while an exact unscoped static-source observation may only
   corroborate or suppress that question and never becomes public evidence. Removing the
   conformance module is reported as `not_installed` and leaves substantive module projections
   byte-stable. Do not promote these narrow grammars as detectors. ✅ An independent fresh-context
   broad-design review required a normalized adapter contract, pure check reducer, sibling-module
   isolation, actual source subject, and typed source-to-analysis join. Revision 2 incorporates
   them, and the reviewer's follow-up reports no remaining architectural blockers. ✅ Registry,
   arbitration, interaction, manifest-drift, source-role-mutation, report-surface, and removable-
   module tests pass. QTL, pulse-admixture, and MVMR marker audits replay deterministically; a
   fresh-context QTL skill run reaches the scientist boundary with zero Findings and one exact
   MaterialQuestion. The revised HTML and typed agent protocol expose the observed operand, source,
   finite choices, analysis scope, authority limit, and unknown path. ✅ The repository owner then
   selected repair-before-emission; the linked segment recorded one structured Answer, compiled one
   exact review-scoped incompatibility Disclosure, retained zero Findings, locked with no later
   model access, and replayed with identical semantic identity and assessment counts. ✅ Experiment
   0021 then audits and replays six commit-pinned, independently authored non-GeneBench QTL and
   robust-MR repositories. It passes the false-applicability branch: zero false questions, zero
   Findings, five close-domain `not_applicable` MVMR outcomes, and one method-like `unsupported`
   outcome rather than a coerced operand. ✅ Accepted ADR-0021 and Experiment 0022 now close the
   first positive-connectivity gap without a schema change. A bounded R Markdown format connector,
   closed MVMR `gencov` method adapter, and typed same-Artifact scope join feed the ordinary
   question-only registry. MR-tutorial and loneliness-mediation independently produce the exact
   zero-covariance observation and one scientist question; display-only code safely abstains; the
   unchanged WSpiller vignette preserves its genuine mixed-operand ambiguity; and a controlled
   mutation proves the provided-covariance branch. The external test also exposed and fixed a
   snapshot-ordering defect by prioritizing the explicitly selected surface within the unchanged
   byte budget. A fresh-context skill audit reaches the question and stops. All runs retain zero
   Findings, zero project execution, zero model calls, and deterministic replay. This proves one
   reusable connector seam, not general R/R Markdown support or detector qualification.
4. ✅ Experiment 0023 confirms that v0.14.0 cannot admit the non-executing verified-good and hard-
   negative controls needed by a detector whose complete premise is static. Imported execution is
   limited to `scope_verified_good`, and manufacturing clean evidence would violate ADR-0012 and
   the known linked-execution gap. Accepted ADR-0022/schema v0.15.0 adds distinct static control
   kinds plus a pre-case frozen, independently implemented raw-byte proof path. The schema,
   fail-closed migration, isolated verifier, static fixture construction, Stage-3 chronology,
   proof-family-stratified metrics, report validation, packaging, and mutation tests pass locally.
   Experiment 0024's fresh-context implementation review found and then verified fixes for two
   proof-authority defects: deleted materialized candidates can no longer narrow the committed
   snapshot inventory, and assignments must bind the exact frozen selection-protocol ID and
   digest. The corrected focused review reports no remaining architecture or epistemic blocker.
   This creates no detector qualification or promotion authority; those remain fail closed until
   real answer-blind cross-provider evidence, pilot-informed thresholds, and maintainer approval.
5. 🟡 Experiment 0025 governs the next capability-development loop. Preserve frozen prior failures
   as regression evidence; generate fresh answer-isolated workflows as development challenges;
   freeze, audit, and replay before answer-side grading; and classify each result as an adapter
   gap, scientific-check gap, unsupported representation, unresolved governing requirement, or no
   demonstrated issue. The first recurrence batch targets directional measurement error, coupled
   class calibration/calibration order, and the existing LD-aware MVMR covered-good guard. Do not
   add a shared module unless the same abstract obligation recurs beyond its design source and its
   positive, verified-good, ambiguous, hard-negative, removal, sibling-isolation, replay, and
   no-execution controls pass. If recurrence is absent, retain the source probe as evaluation-only.
   The first carrier-screening rerun initially appeared to recur a calibration/target-population
   weighting-order obligation, but a required counterevidence check rejected the order-only
   classification: one fixed linear ancestry-specific inverse commutes with weighted averaging.
   The temporary step-order module was removed. Further inspection isolated the actual general
   fork: aggregate joint calibration versus nonnegative constrained joint calibration inside each
   post-stratum before standardization. The task does not select between them, so the new
   `check:poststratified-misclassification-estimator` is question-only and scientist-governed. Its
   exact positive, matching, conflict, ambiguous, hard-negative, removal, sibling, audit, replay,
   and six independent-repository false-question controls pass with zero Findings. The Wright-
   Fisher arm remains a negative recurrence for the old exact profile, and the attempted new MVMR
   guard was not persisted. A later one-change ablation causally closes the fixed carrier residual:
   constrained joint calibration inside each post-stratum moves all five fields within contract,
   while a cellwise unconstrained reverse control exactly reproduces the original two failures.
   The repaired report reaches the existing question; both audits replay byte-identically with zero
   Findings. This is fixed-case evidence only, not estimator authority or qualification. The second
   batch initially added the general classifier-derived copy-
   dosage representation choice: integer hard copy state versus posterior expected continuous
   dosage. Accepted ADR-0024 later adds direct continuous calibration as a third representation
   after fixed-case and reverse-control ablations show that it is not equivalent to posterior
   expectation. Pooling or stratification remains a separate unsupported policy.
   A fresh answer-isolated workflow explicitly used the continuous representation and matched the
   carrier count and support code but still missed two numeric tolerances, proving that this one
   covered choice is not a correctness certificate. The exact Markdown-only module is
   question-only, scientist-governed, removable, replay-stable, and false-question clean across
   six independent repositories plus the MR-tutorial sibling. The earlier hard-call report is
   conservatively `unsupported` because it lacks one explicit report-level downstream
   representation declaration; no source-to-report link is invented. The batch remains open for
   another capability family. A third fresh answer-isolated ambient-state eQTL workflow exposed
   an adjustment-set fork: omit an unobserved/unreconstructed technical group, or reconstruct a
   unit-level group from an ambient, contamination, or negative-control summary and include it as
   a categorical covariate. The exact selected-Markdown
   `check:recoverable-technical-group-adjustment` asks the scientist which treatment governs or
   retains the unknown. Matching/conflicting Answers, ambiguity, QC-only, observed-batch and
   biological-group hard negatives, removal, sibling isolation, audit, replay, and eight
   unrelated/sibling workflow controls pass with zero Findings. All three checks remain
   unqualified and cannot establish execution, numerical causality, confounding, or scientific
   correctness. A later ambient 2-by-2 shows that recovered-group inclusion and corrected-marker
   count scale interact: neither one-change arm passes, while their combination does. All three
   audits reach only the existing group question and replay byte-identically with zero Findings.
   Multiple state rules are target-equivalent, so no marker, scale, or threshold check is admitted
   from this one case. A fourth fresh workflow supplies a covered-good founder-orientation recurrence:
   it repaired two founder markers before HMM emission and placed both QTL answer fields within
   contract. Its natural “Founder 0/1 alleles ... before HMM emissions” wording exposed a bounded
   report-adapter gap. The grammar now accepts that explicit modifier/plural variation without
   changing the operand or output ceiling; a plotting lookalike plus qtl2, DOQTL, and tensorQTL
   remain question-free, and the unchanged workflow now produces exactly the existing founder
   question with model-free replay. A fresh-target skill run shows both orientation choices plus
   retain-unresolved, stops without answering, and replays byte-identically. A fifth fresh
   CRISPRi/CasRx workflow matched its binary decision but missed both effect-size tolerances. A
   finite post-lock mechanism review and independent design review rejected a conflated
   offset/scale/validation question and admitted only the atomic
   `check:paired-bridge-location-alignment`. Two independently authored reports expose the same
   additive paired-bridge choice under different surrounding normalization policies. Exact
   positives, coexistence, ordinary-centering and QC hard negatives, removal, sibling isolation,
   controlled Answers, ten unrelated or sibling workflows, semantic lock, replay, and a
   fresh-target skill run pass with zero Findings. Accepted ADR-0025 later adds the separate,
   threshold-independent CasRx one-axis versus simultaneous-two-axis question after fixed-case and
   reverse-control evidence. Global scaling and the remaining pooled-screen choices remain
   unsupported. A sixth fresh pulse-admixture workflow missed all four numeric
   tolerances while explicitly using eligible called A-plus-B exposure. Its natural report wording
   exposed only a bounded connectivity gap in the existing
   `check:full-map-ancestry-exposure`; the adapter now recognizes that exact declaration without
   changing the output ceiling. Later ablation showed that matching the ancestry-fraction
   denominator was semantically too broad: a workflow can use called A-plus-B length for its
   ancestry fraction and full-map exposure for pulse timing. Accepted ADR-0023 narrows version
   `1.1.0` to exact pulse-time declarations under `time_definition`; fraction-only wording is no
   longer a timing operand. Chromosome-specific label harmonization remains outside current
   production coverage.
   A seventh carrier workflow then passed the ancestry and negative-screen quantities but missed
   partner transport and the derived couple risk after standardizing only over ancestry and
   family-history tier. An earlier independent carrier report includes site and collection wave,
   so the atomic recurring choice is the direct-standardization conditioning set—not a universal
   rule that completion predictors must be included. The exact selected-Markdown
   `check:direct-standardization-conditioning-set` asks the scientist to choose include-named-
   availability variables, substantive-risk-strata-only, or retain unknown. Controlled Answers,
   ambiguity, hard negatives including IPW and mixed policies, removal, sibling isolation, ten
   unrelated or sibling audits, a fresh-target skill run, semantic lock, and replay pass with zero
   Findings and no project execution. Both numeric-cause attribution and broader missing-data
   estimators remain unsupported.
   The eighth batch pauses new workflow generation to close these two frozen diagnoses. A one-
   change carrier ablation that adds site and wave to the direct-standardization cells moves all
   five answers within contract, causally supporting the existing question for that case. A
   chromosome-3 label-only population-genetics ablation repairs both ancestry fractions while both
   pulse times still fail; a combined label, transition-path, and full-map-time ablation then moves
   all four answers within contract. The corrected report exposed the fraction/time conflation
   repaired by ADR-0023. Original, label-only, and corrected audits now project the appropriate
   timing operand and replay byte-identically with zero Findings. At that checkpoint, the
   transition-path choice had one fixed-case demonstration but no independent recurrence, so no
   module was added.
   The same batch now closes the CRISPR and structural residuals. Paired-offset-only CRISPR repair
   fixes the neighbor effect but leaves the transcript effect wrong; the combined repair passes all
   fields; and restoring only the high-overlap one-axis CasRx fit moves the transcript field outside
   tolerance. Accepted ADR-0025 adds a separate, threshold-independent, question-only CasRx axis
   module. In the structural case, group-specific direct continuous calibration passes all four
   fields, whereas pooled-direct and group-specific posterior-expectation reverse controls remain
   outside. Accepted ADR-0024 extends the dosage question to three representations and explicitly
   leaves pooling policy unsupported. Exact positives, ambiguity, hard negatives, controlled
   Answers, module isolation, five sibling workflow controls, semantic locks, and replay remain
   zero-Finding. The stable checkpoint then closes the frozen TXR1 failure with a target/estimator
   2-by-2. Target-only repair fails all three numeric fields, estimator-only repair passes toxicity
   but fails benefit and net, and the combined repair passes all fields. Accepted ADR-0026 adds the
   independent `somatic-clonality-representation` and `posttreatment-missingness-strategy`
   question-only modules. Four-cell fixtures and the four actual reports project the expected
   operand pairs; all audits remain zero-Finding and replay lock/report bytes exactly. The full
   post-change checkpoint passes `948` tests, Ruff, strict typing, and starter/schema validation.
   The next two answer-isolated workflows then revisited frozen unresolved families. A fresh
   Wright-Fisher HMM correctly repaired allele orientation and selected the right locus but again
   used an average of two directional error rates symmetrically, missing the coefficient tolerance.
   Accepted ADR-0027 adds the atomic, domain-neutral, question-only
   `directional-measurement-error-interpretation` module. Both separately authored Wright-Fisher
   reports now reach exactly that question and replay byte-identically with zero Findings; the
   check does not infer an error direction or select the correct operand. A fresh Hi-C workflow
   reproduced the same-distance expected-count failure on byte-identical inputs and missed all
   three fields. Its target-inclusive, unmasked arithmetic mean differs from the reference along
   several ScientificContract dimensions and remains an unsupported representation rather than a
   benchmark-specific binary check. ADR-0018's already accepted claimless unresolved-obligation
   branch now connects that exact evidence shape: one conventional task-like Markdown requests
   three role-bound O/E outputs, the selected report declares one target-inclusive same-stratum
   mean, and an exact target-exclusion sensitivity changes the requested values. The result is one
   analysis-scoped question with zero Claims, candidates, or Findings. Missing-premise mutations,
   a non-Hi-C positive/covered-negative/ambiguity/hard-negative portability set, structured human
   Answer scope, capability separation, semantic lock, and replay pass. General incomplete methods,
   governing estimator choice, materiality, numeric causality, and detector eligibility remain
   unsupported. The new full checkpoint passes `969` tests, Ruff, formatting, strict typing,
   starter/schema validation, clean wheel installation, the walking skeleton, general
   audit/replay, interaction flows, eight-entry capability generation, RO-Crate export, and every
   schema migration through v0.15.0.
   A subsequent fresh answer-isolated pulse-admixture workflow independently repeats the earlier
   literal label, path-termination, and retained-callable timing-exposure choices and misses all
   four fields with the same error magnitudes. Its pre-answer audit emits zero questions, exposing
   one ADR-0023 adapter-connectivity gap and the still-missing transition-path representation. A
   fresh label-repaired 2-by-2 proves that preserving continuity and using full-map exposure are
   separate and jointly necessary in this fixed case: neither one-change arm passes both times,
   while the combined arm passes all four fields. Accepted ADR-0028 adds only the domain-neutral,
   question-only `within-sequence-transition-path-continuity` module under
   `dependence_structure`; the exposure adapter gains only explicit natural report forms. Both
   independently authored baselines, both repaired reports, all four 2-by-2 cells, finite controls,
   controlled Answers, module removal, semantic lock, and replay remain zero-Finding. No schema,
   detector qualification, execution privilege, numeric authority, or Finding permission changes.
   The resulting full checkpoint passes `980` tests and the complete clean-wheel handoff verifier.
   A fresh answer-isolated structural-copy workflow then provides a covered-good recurrence: it
   independently uses group-specific direct continuous Ridge calibration and passes all four
   released fields. Its pre-answer audit asks zero questions because the explicit non-rounding,
   named calibration model, and downstream same-target use are split across paragraphs. Accepted
   ADR-0029 adds only a finite document-scoped same-literal-target join to the existing ADR-0024
   dosage adapter, now version `1.2.0`. The unchanged workflow reaches exactly the existing direct-
   continuous question; posterior, direct, pooled-direct, and stratified-posterior controls retain
   their operands and exact replay. The pooled failure did not recur, so no pooling question is
   admitted. No schema, Finding, execution, metric, qualification, or maturity authority changes.
   The resulting full checkpoint passes `984` tests and the complete clean-wheel handoff verifier.
   A third fresh ambient-state workflow then independently repeats the earlier two-axis pattern.
   The untouched workflow, activation-scale-only arm, and recovered-technical-group-only arm all
   remain outside the exact tolerance; only the combined arm is within. The two group-inclusion
   reports state that a technical proxy separated, that the workflow reconstructed **that** group,
   and that it included **it** in the primary model. Accepted ADR-0030 advances only the existing
   technical-group check and adapter to `1.1.0` with one finite paragraph-scoped co-reference form.
   The untouched and scale-only reports remain question-free; group-only and combined expose
   exactly the existing scientist-governed adjustment-set question; all four replay byte-
   identically with zero Findings. The scale interaction remains unsupported, and no schema,
   Finding, execution, metric, qualification, or maturity authority changes. The resulting full
   checkpoint passes `987` tests and the complete clean-wheel handoff verifier.
   A second fresh TXR1 workflow then chooses a third target rule and a hybrid post-treatment AIPW
   assessment strategy, both correctly unsupported, and fails all three numeric fields. A frozen
   target/missingness two-by-two shows that the reference target explains most of the fixed-case
   discrepancy, while excluding toxicity does not repair the workflow and the remaining
   AIPW-versus-IPW difference is not authorized by the task. Accepted ADR-0031 adds no operand: it
   only connects explicit evaluator-frozen adjusted-CCF and primary/evaluator-owned baseline-only
   assessment wording to the two existing ADR-0026 questions. The untouched, target-only,
   missingness-only, and combined reports now produce zero, target, missingness, and both questions
   respectively, with zero Findings and byte-identical replay. No schema, Finding, execution,
   numeric, qualification, or maturity authority changes.
   A fresh phase-split MVMR workflow then fails both requested effects after selecting six
   LD-conditional signals and fitting zero-intercept full-covariance GLS. A frozen two-by-two shows
   that neither a marginal phase-1 union nor a robust LD-whitened fit repairs the workflow alone;
   only their combination passes both fields. Accepted ADR-0032 adds two atomic question-only
   modules for instrument construction and residual-heterogeneity estimator, and advances the
   existing LD-whitening adapter to `1.1.0` for the natural robust-report wording. Four method
   cells, the fresh workflow, the earlier independent robust workflow, and four public repository
   controls produce the exact expected questions with zero Findings and byte-identical replay.
   The passing combination is fixed-case evidence, not a universal MVMR rule. Cross-exposure
   covariance, tuning constants, instrument validity, and broader code recognition remain
   unsupported. No schema, Finding, execution, numeric, qualification, or maturity authority
   changes. A fresh-context skill user reaches exactly the two new questions, leaves both
   unresolved, and reproduces the semantic records, counts, coverage, lock digest, and HTML report
   with zero Findings, no project execution, and zero model calls. The resulting full checkpoint
   passes `1013` tests, Ruff, formatting, strict typing, and starter/schema validation, plus the
   complete clean-wheel handoff verifier.
   Accepted ADR-0033 then closes AC-47's bounded dual-R parser boundary and AC-54's first named
   domain-profile requirement without adding scientific authority. Bounded strict-UTF-8 `.R`
   files now receive independent Tree-sitter-R and optional isolated base-R parse-data records,
   exact direct/namespaced call spans, and an explicit agreement or disagreement receipt. The
   helper parses an isolated copy and never sources or evaluates project code. The generated
   matrix now contains separate detector-free DESeq2, edgeR, and limma-voom call-inventory
   profiles with empty tested/inferred versions and `semantic_modeling: not_started`. The full
   checkpoint passes `1023` tests, Ruff, formatting, strict typing, starter/schema validation,
   editable installation from the archive-hash-pinned dependency, and the complete clean-wheel
   handoff verifier.
   Accepted ADR-0034 then adds bounded non-executing Jupyter notebook connectivity. Strict JSON
   decoding inventories nbformat-v4 markdown, code, and raw cells plus saved outputs under exact
   semantic cell/output pointers, while duplicate keys, unsupported envelopes, invalid siblings,
   and finite ceilings fail locally. Notebook-only audit, selected-surface coverage, authenticated
   cache hit/invalidation, inert project-code markers, semantic lock, replay, exact capability
   generation, and clean-wheel installation are exercised. Saved output remains unauthenticated,
   and notebook cell operation/Claim/scientific-check extraction is deliberately absent. The full
   checkpoint passes `1036` tests, Ruff, formatting, strict typing, starter/schema validation, and
   the complete clean-wheel handoff verifier.
   Accepted ADR-0035 then closes the remaining P0 Quarto source-location gap with bounded inert
   `.qmd` inventory. It preserves exact front-matter, prose, literal-engine executable-cell,
   leading option, evaluation-declaration, and collision-free document-chunk locations without
   rendering or execution. Quarto-only selection, false-question exclusion, authenticated cache,
   semantic lock, replay, capability mutation, and installed-wheel controls pass. Code/YAML
   interpretation, rendered meaning, operations, Claims, artifact lineage, and scientific checks
   remain deliberately absent. The full checkpoint passes `1044` tests, Ruff, formatting, strict
   typing, starter/schema validation, and the complete clean-wheel handoff verifier.
   Accepted ADR-0036 then closes the bounded cell-language adapter gap. Exact unconflicted Python
   and R notebook/Quarto cells are digest-reverified and independently delegated to the existing
   static parsers. Child syntax, calls, and supported Python Operations preserve notebook-cell or
   absolute document-chunk locations; identical cells retain distinct identities and descendant
   cache scopes. Conflicting or unsupported languages and the 200-cell ceiling fail closed.
   Numerical verification and scientific-check contexts exclude virtual cells until cell-aware
   evidence contracts exist. The generated capability matrix contains 14 entries, including one
   separate detector-free container-cell bridge with empty tested/inferred versions and no
   semantic, detector, or Finding authority. The full checkpoint passes `1049` tests, Ruff,
   formatting, strict typing, starter/schema validation, and the complete clean-wheel handoff
   verifier.
   Accepted ADR-0037 then closes the internal same-path evidence collision that prevented safe
   scientific-check transport. An immutable source-location contract separates authenticated
   container identity from independently verified cell bytes, and exact parser-result binding
   reconstructs notebook-cell or absolute Quarto citations. The existing founder-orientation AST
   adapter recognizes its exact shape in a cell, but the observation remains unscoped,
   question-ineligible, and Finding-ineligible. Tampered bridge metadata is rejected locally;
   markers remain inert; semantic lock and replay remain exact. Schema v0.15.0 and the 14-entry
   capability count are unchanged. The full checkpoint passes `1053` tests, Ruff, formatting,
   strict typing, starter/schema validation, and the complete clean-wheel handoff verifier.
   Accepted ADR-0038 then adds the first exact selected-container cell scope join. A unique
   supported founder-orientation AST shape inside the full-digest selected notebook or Quarto
   Artifact now emits the existing question-only scientist prompt and one Finding-ineligible
   observed assertion with an exact cell citation. The same cell in an unselected container and an
   explicitly disabled Quarto cell remain unscoped. Execution, primary-analysis status, output
   provenance, and Findings remain unknown. Schema v0.15.0 and the 14-entry capability count are
   unchanged. The full checkpoint passes `1055` tests, Ruff, formatting, strict typing,
   starter/schema validation, and the complete clean-wheel handoff verifier.
   Accepted ADR-0039 then closes the corresponding separate-analysis-file connectivity gap. A
   uniquely bound source-parent report writer now joins the exact Python FileRecord to the selected
   full-digest report Artifact without execution. The frozen multiparent-QTL workflow carries its
   exact report and source operands through the already authorized scientist requirement, one
   review-scoped incompatibility Disclosure, semantic lock, and replay with zero Findings. Unused,
   competing, dynamic, absolute, parent-traversing, and non-source-root writers remain hard
   negatives. Schema v0.15.0 and the 14-entry capability count are unchanged. The full checkpoint
   passes `1063` tests, Ruff, formatting, strict typing, starter/schema validation, and the complete
   clean-wheel handoff verifier.
   Accepted ADR-0040 then freezes `detector:bounded-analysis-method-conflict` version `0.1.0` over
   that exact path. Its local development portfolio covers an exact conflict, a matching negative,
   a non-allowlisted hard negative, missing full-digest scope, all ten finite counterevidence
   mutations, controller integration, and replay. A fresh real-workflow rerun produces one bounded
   evaluation candidate with `analysis.py` and `report.md` evidence and zero Findings. The
   capability matrix grows from 14 to 15 entries; schema v0.15.0 and production Finding authority
   are unchanged. The full checkpoint passes `1077` tests, Ruff, formatting, strict typing, and
   starter/schema validation.
   Accepted ADR-0041 and immutable schema v0.16.0 then add the separately discriminated static
   profile required to qualify that detector without manufacturing execution evidence. The
   independent verifier rederives the selected report and source operands, unique writer closure,
   and exact scoped human authority from immutable bytes, and fails closed on ambiguity,
   unsupported dataflow, counterevidence, drift, or incomplete identity. The profile is integrated
   through static fixtures, Stage 3, report rendering, JSONL/disposable SQLite, migration,
   packaging, and replay. It remains local mechanism evidence and grants no qualification or
   Finding authority.
6. 🟡 Experiment 0027 freezes the v0.2 candidate, independent typed verifier, answer-blind
   selection protocol, six portfolio roles, and review prompts before assignment. Next freeze the
   exact no-replace positive, verified-good, ambiguous, hard-negative, removal, and counterevidence
   cases, then run authenticated cross-provider review and maintainer promotion. Do not change the
   candidate after labels are visible; a logic change creates a new candidate version.
7. ✅ Experiment 0028 adds a fresh-context non-QTL skill portability check. On the answer-isolated
   Hi-C workflow, the initial skill run selects the explicitly named report, produces exactly the
   existing expected-count/background MaterialQuestion, preserves the scientist unknown, emits
   zero Findings, executes no project code, records zero model calls, and replays with the same
   semantic lock, question, counts, coverage, and report. Its answer-key-informed follow-up builds
   and independently reviews a golden estimator, then adds two question-only atomic checks under
   ADR-0043. The unchanged candidate now yields exact observed operands for arithmetic-mean
   construction and focal-target inclusion; two human-authorized answer segments deterministically
   report the corresponding material incompatibilities and byte-replay. They remain Disclosures,
   not Findings, because report text does not prove execution or numerical cause. It also makes
   the whole-root snapshot boundary
   explicit: `uninspected` means no semantic/deep inspection, not no byte access; a protocol that
   forbids hashing an answer-side file must provide an allowlisted workspace that omits it. This is
   local usability and development evidence, not cross-provider qualification, broad Hi-C support,
   or production authority.
8. Extend the common evidence path only from another concrete, independently recurring method
   representation. General R dataflow, formulas, package behavior, rendered R Markdown/Quarto,
   notebook/Quarto prose or cell dataflow, Claims, runtime semantics, and broader
   workflow/scheduler traces remain unsupported. Do not infer workflow correctness, document
   reproducibility, or general bulk RNA-seq support from these inventory slices.
9. ✅ Experiment 0029 freezes the first recovered single-cell feature controls before detector
   implementation: one complete-family BH mismatch, its identical-raw-family corrected twin, one
   preregistered-primary hard negative, and one incomplete-family ambiguity. An evaluator-owned
   exact-decimal oracle, no-replace builder, answer isolation, and content manifest pass. Accepted
   ADR-0044 and immutable schema v0.18.0 add the generic parallel calculation-check registry and
   typed `DeterministicCheckObservation` instead of a BH controller special case. The first bounded
   adapter recognizes only an explicit complete-family BH contract, reads the selected full-digest
   CSV/TSV without executing project code, and retains exact reported/recomputed counts and
   mismatch indices. The positive produces a Disclosure, the corrected twin is conformant, the
   one-primary case is inapplicable, and the incomplete-family case asks one bounded question; all
   have zero Findings and deterministic audit/report/storage/semantic-lock/replay. Malformed,
   over-budget, workspace-drift, and registry-removal tests fail closed or isolate the module.
   The immutable v0.17 qualification freeze cannot be rebuilt against the changed active manifest
   set and now fails closed rather than being rewritten. Natural wording, alternate identifiers or
   procedures, broad table shapes, independent external validation, detector qualification, and
   production Finding authority remain absent.
10. ✅ Experiments 0030 and 0031 plus accepted ADR-0045 and ADR-0046 establish practical public-
    feature parity from the compact
    Biermann capsule. The separate finite material-input budget, selected-only dense-H5AD
    inventory, exact selected-artifact calculation context, closed sensitivity declaration, and
    optional one-CPU PyDESeq2 engine are implemented without porting the old controller. The
    ordinary production audit exactly reproduces 16,289 matched/testable reported discoveries,
    770 replicate-level survivors, 0.047271 survival, and 0.381669 powered fraction. It emits one
    Disclosure and zero Findings, records unresolved producer/dependence semantics, executes no
    project code, makes zero model calls, and replays the observation exactly. Synthetic positive,
    all-survive corrected, biological-replicate hard-negative, unresolved-unit, column mutation,
    unsupported/unselected H5AD, duplicate-feature, material-boundary, and module-removal controls
    pass. Modular v3-v8 calculation releases add declared effect relevance, categorical design
    integrity (confounding/required adjustment/pairing/aggregation), exact namespaced R
    method/response compatibility, bounded Scanpy selection reuse, donor-level oriented eQTL sign,
    and exact-distance arithmetic Hi-C loop strength. Their positive, corrected, hard-negative,
    ambiguity, mutation, nonexecution, and removal controls pass, and the broadened registry
    reproduces and replays the Biermann observation exactly. Remaining work is product polish,
    natural non-capsule validation, broader adapters, scientist-answer ergonomics, capability-
    claim publication, and any separately justified Finding qualification; no Finding promotion is
    proposed here.
    A separate immutable v9 maintenance release replaces only the optional PyDESeq2 import
    boundary after a clean `.[dev]` install exposed a mypy failure when that extra was absent. The
    optional dependency still fails locally to unsupported, the v2 manifest remains unchanged,
    and `test_optional_recompute_dependency_failure_is_localized` covers the no-extra path.

Further Python lineage profiles are justified only when they unblock a named detector premise or
real validation case. Branches, DAGs, dynamic runtime semantics, and over-budget calculations remain
unsupported rather than approximated.
Keep the generated multidimensional capability matrix synchronized with exact manifests; do not
populate detector, qualification, tested-version, or inferred-compatibility fields without their
required source evidence.
Do not propose numeric promotion thresholds until real pilot evidence exists.
The hosted Python matrix is satisfied. Live platform credential-store smoke tests, W3ID
deployment, final release identity, and independent cross-provider detector qualification remain
external or later gates. The documentation phase must preserve those limits rather than presenting
the draft pull request as a published or detector-qualified release.

## Immediate next task

Follow `docs/implementation/POST_MPP_PRODUCT_BACKLOG.md` in dependency order. Start with L01, the
machine-readable regression corpus ledger, then implement the one-command L02 runner before
broadening connectivity or scientific coverage. Every subsequent feature must retain the mandatory
positive, corrected, hard-negative, ambiguous, unsupported, isolation, mutation, no-execution, and
replay controls described there.
