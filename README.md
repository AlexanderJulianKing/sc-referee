# sc-referee development alpha

**Program version:** 0.3.0.dev0  
**Starter version:** 0.1.0  
**Architecture baseline:** sc-referee specification 0.5.0-draft plus accepted 0.6.0 ADR overlay  
**Current schema release:** sc-referee schemas 0.18.0  
**Immutable schema baseline:** sc-referee schemas 0.5.0

This repository is an implementation-facing overhaul of **sc-referee**, a conservative
scientific-analysis auditor with repository-scoped Codex skills named `$method-contract` and
`$scientific-audit`.
Compatibility with an earlier public GitHub implementation is intentionally not a design input.

It contains:

- the complete v0.5 architecture and immutable schema baseline under `reference/`;
- the accepted local v0.18.0 deterministic-calculation-observation schema release, with immutable
  v0.5.0 through v0.17.0 predecessors;
- a narrower, implementation-ready Milestone 0 plan;
- an executable Python package with its accepted schemas embedded as runtime resources;
- a complete walking-skeleton audit path;
- a first arbitrary-repository static `audit` path with deterministic replay;
- a separate claimless `method-contract` path that freezes one human-authorized closed profile
  before coding and binds it to a later audit only through an exact parent lock and unchanged task;
- repository-scoped `.agents/skills/method-contract` and `.agents/skills/scientific-audit` Codex
  skills;
- a repository-contained `plugins/sc-referee` Codex plugin package carrying exact copies of those
  skills and declaring the installed CLI as its deterministic core;
- a separately built `evaluation/` answer-side package whose code is excluded from the production
  wheel, reconciles review panels and immutable file-span evidence without admitting unverified
  labels, builds allowlisted blind-review workspaces with explicit leak-scan limits, projects
  experimental outputs for evaluation only, and deterministically compiles exact case outcomes and
  problem-cluster metrics;
- two isolated, non-executing static-qualification verifiers: the exact bounded direction profile
  and the exact cross-surface analysis-method profile. Both use frozen detector/verifier identities,
  immutable raw-byte proof records, distinct static control kinds, proof-family-stratified metrics,
  and fail-closed Stage-3/report replay. The second profile also binds the exact scientist question,
  human Answer, ScientificContract, and accepted requirement assertion. These mechanisms are local
  evidence infrastructure and do not qualify or promote either detector;
- one generic, manifest-bound deterministic-calculation registry with eight independently
  removable bounded modules: complete-family Benjamini-Hochberg, replicate-level single-cell
  sensitivity, declared effect-size relevance, categorical design integrity, namespaced R
  method/response compatibility, Scanpy selection/test reuse, donor-level eQTL sign/support, and
  arithmetic-background Hi-C loop strength. They read only explicitly selected immutable material
  inputs under finite limits, preserve unsupported premises, and cap demonstrated mismatches at
  Disclosure. Their practical public-feature parity boundary and exact omissions are published in
  [`docs/implementation/PRACTICAL_PARITY_MATRIX.md`](docs/implementation/PRACTICAL_PARITY_MATRIX.md);
- one fixture-only deterministic claim/result-agreement test double;
- one linked conditional concern, one material question, and one opaque-boundary disclosure;
- local schema validation, JSONL storage, a rebuildable SQLite index, snapshotting, and static HTML rendering;
- project-local content-addressed parser, static-graph, and bounded-lineage caching, stable audit
  diffs, and linked pause-aware deadline accounting;
- one replayable public performance measurement through each completed general or linked semantic
  lock, explicitly excluding post-lock and unmetered resource usage;
- public observed/control, data, decision, execution, and environment records plus typed WorkItem
  and Answer records with fail-closed migrations;
- disabled, synthetic-test-only v0.14 project-execution scaffolding retained for possible post-MPP
  work; it is not a production capability, and process success or output bytes would not imply
  scientific correctness;
- proposed external ReproductionRequests for selected Claims whose project-execution origin is
  missing, with no execution or scheduler authority;
- bounded tiered identity for enormous or unavailable data: an end-to-end regression audits and
  replays a 10-billion-byte sparse asset after reading only 12,288 sampled bytes, without copying
  it, calling it fully identified, or executing project code; a second path preserves an exact
  root SHA-256 manifest declaration as repository-supplied identity without claiming the target
  bytes were independently verified;
- bounded header-only inventory for fully captured CSV/TSV inputs and outputs, preserving exact
  column names and unambiguous static Artifact roles while leaving rows, types, scientific meaning,
  runtime use, and correctness unknown;
- bounded import of terminal rows from an exact default Nextflow `trace.txt` as weak external
  execution assertions, without authenticating the run, inventing input/output lineage, or using
  the imported rows as Claim or Finding premises;
- dual non-evaluating inspection of bounded strict-UTF-8 `.R` sources: pinned Tree-sitter-R plus
  an optional isolated base-R parse-data receipt record exact direct/namespaced call spans and
  parser disagreement without sourcing or evaluating project code;
- bounded strict-JSON inventory of nbformat-v4 Jupyter notebooks, preserving exact cell and saved-
  output pointers while declining to execute cells, trust outputs, or infer runtime order;
- bounded strict-UTF-8 Quarto source inventory, preserving exact front-matter, prose, literal-
  engine cell, option, and chunk locations without rendering or executing the document;
- a bounded static language bridge that digest-reverifies at most 200 exactly declared Python/R
  notebook or Quarto cells and preserves their cell locations without executing them or inferring
  cross-cell state;
- an immutable cell-aware scientific-evidence boundary that independently re-extracts those bytes,
  keeps same-path cells distinct, and lets an existing exact static adapter cite the proper cell;
- one exact selected-container scope join: a supported founder-orientation shape inside the
  full-digest selected notebook or Quarto source may produce a bounded scientist question, while
  execution, primary-analysis status, correctness, detector eligibility, and Findings remain
  unestablished;
- deterministic attached RO-Crate 1.3 ZIP export of integrity-verified native audit records and
  reports, with declared package authorship/licensing and offline bounded-profile validation;
- a deterministic public capability matrix generated from a closed five-collection release
  manifest set, currently declaring 15 narrow entries including detector-free Jupyter, Quarto,
  container-cell, DESeq2, edgeR, and limma-voom inventories plus exact experimental direction and
  method-contract detectors and the cross-surface analysis-method detector, with no detector
  qualification or tested-version envelope;
- the first real domain-neutral experimental detector: it can expose a deterministic
  qualification-only candidate when an exact static report writer combines a literal directional
  sentence with an oppositely signed auditor-recomputed raw mean difference; it cannot emit a
  production Finding;
- tests, CI configuration, a task board, and coding-agent instructions.

The requirement-by-requirement product gap audit is maintained in
[`docs/implementation/FULL_COMPLETION_MATRIX.md`](docs/implementation/FULL_COMPLETION_MATRIX.md).
It deliberately distinguishes the working vertical slice from the still-missing complete product.

## Start here

A coding agent should read these files in order:

1. [`AGENTS.md`](AGENTS.md)
2. [`docs/implementation/MILESTONE_0_BUILD_SPEC.md`](docs/implementation/MILESTONE_0_BUILD_SPEC.md)
3. [`docs/implementation/UPDATED_IMPLEMENTATION_PLAN.md`](docs/implementation/UPDATED_IMPLEMENTATION_PLAN.md)
4. [`docs/implementation/TASK_BOARD.md`](docs/implementation/TASK_BOARD.md)
5. [`reference/specification-v0.5.0-draft/MASTER_SPEC.md`](reference/specification-v0.5.0-draft/MASTER_SPEC.md)

The implementation overlay records accepted schema evolution and the accepted ADR-0017
evidence-first `0.6.0` MPP boundary. It does **not** weaken scientific, epistemic, security, or
reporting requirements and does not add compatibility work for an earlier public repository.

## Bootstrap

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
sc-referee validate-schemas
sc-referee demo examples/walking-skeleton --output .demo-audit
sc-referee replay .demo-audit/semantic.lock.json --output .demo-replay
sc-referee audit examples/general-static --output .general-audit --mode standard --report report.md
sc-referee status .general-audit --json
sc-referee replay .general-audit/semantic.lock.json --output .general-replay
sc-referee diff .general-audit .general-replay --output .general-diff.json
sc-referee export-ro-crate .general-audit --output .general-audit.zip \
  --author-name 'Declared crate author' \
  --license-uri 'https://spdx.org/licenses/Apache-2.0.html' \
  --license-name 'Apache License 2.0'
sc-referee validate-ro-crate .general-audit.zip
sc-referee generate-capability-matrix --output .capability-matrix.json
sc-referee validate-capability-matrix .capability-matrix.json
```

Every command that creates an audit or replay requires a new, absent output path. It refuses to
delete, merge into, or overwrite an existing directory so an earlier run remains recoverable.
RO-Crate export likewise creates one absent ZIP without replacement and never modifies the source
audit. Its author and license options describe the exported audit package, are declared rather
than authenticated, and do not establish authorship or licensing of the audited project. The
offline validator checks the bounded sc-referee profile; third-party RO-Crate validation is not
claimed.

Capability generation also creates one absent file without replacement. Parser-supported
versions are never promoted into tested or inferred versions; the bundled matrix leaves both
arrays empty and exposes one explicitly experimental, unqualified detector entry. Its strongest
public assessment output remains below Finding, and `evaluation_finding_candidate` is retained only
as qualification input.

To exercise the agent question flow without changing the completed unresolved run:

```bash
sc-referee audit examples/general-static --output .general-unresolved --mode standard
sc-referee resume .general-unresolved --repository examples/general-static \
  --output .general-interaction
sc-referee work-queue .general-interaction
sc-referee work-packet .general-interaction --work-item-id '<id>'
sc-referee submit-proposals .general-interaction --work-item-id '<id>' \
  --proposal proposal.json
sc-referee record-answer .general-interaction --question-id '<question-id>' \
  --select-option '<answer-option-id>' --actor-id scientist:local
sc-referee lock-semantics .general-interaction
sc-referee status .general-interaction --json
```

The proposal must satisfy the exact digest, source, status, provenance, and authority constraints
in its WorkItem. The local human identifier is declared, not authenticated. An Answer can select
only an existing option within its exact authority scope; neither it nor a proposal can authorize
execution. The CLI prints the selected scheduling cutoff, hard deadline, and disabled execution
policy before an initial audit.

The two demo commands should generate byte-identical normalized detector and assessment records.
Replaying a post-lock interrupted general audit also preserves its recorded deadline or host-limit
coverage disposition rather than relabeling the source run as complete.

## Post-MPP executor scaffold (disabled)

The following commands exist only as synthetic-tested development scaffolding for a possible
future adapter; they are hidden from ordinary CLI help and are not part of the MPP or a supported
project-execution workflow:

```bash
sc-referee request-execution SOURCE_AUDIT --request request.json --output REQUEST_AUDIT
sc-referee authorize-execution REQUEST_AUDIT --work-item-id WORK_ITEM_ID \
  --capability capability.json --launch launch.json --output LINKED_AUDIT \
  --linked-audit-run-id AUDIT_RUN_ID --expires-at UTC_TIMESTAMP \
  --actor-id ACTOR_ID --actor-display-name 'Declared local user'
sc-referee execute-authorized LINKED_AUDIT --capability capability.json \
  --snapshot-root SNAPSHOT_ROOT --podman-executable /absolute/path/to/podman
```

The first command only locks a bounded request. The second currently creates a test-only private,
filesystem-bound authorization after a fresh terminal challenge. The third command refuses before
consuming that authorization or reaching the internal executor. Accepted ADR-0017 defers this
capability beyond the MPP; accepted v0.18.0 adds bounded auditor-owned calculation observations
without granting execution or Finding authority. Before any future production
launch, deferred ADR-0015 and ADR-0016 must be resolved or conservatively superseded. Replay never
relaunches a container or reconstructs authorization. A read-only internal verifier can already reject mutation, links,
noncanonical bytes, open inventory, transcript drift, and broken v0.14 record linkage, but a copied
or consistently fabricated package is still nonauthorizing evidence. A second read-only inspector
strengthens v0.14 linked-evidence replay by checking the exact record/Artifact/AssetIdentity graph,
retained bytes, and source-lock WorkItem/snapshot bindings while preserving the missing public
closure as a limitation. In internal synthetic tests on the future execution path, the local
Linux adapter reads cumulative CPU time and kernel memory/PID peaks directly
from the container cgroup and samples per-process open files every 50 ms with that limitation
recorded. Remote Podman-machine cgroups remain explicitly unavailable. Even complete execution
evidence cannot qualify a clean-control fixture until the deferred ADR-0015 closure contract or an
equally conservative successor is implemented.
The request/authorization commands and internal executor are retained for synthetic mechanism
testing; no real project launch is claimed safe or supported.

General audits cache exactly identified Python and Markdown ParserResults plus versioned
static-graph and bounded-lineage descendants below the audited project's `.sc-referee/` root.
Python entries bind exact literal file dependencies; weak dependencies remain uncached. The diff
command reports identity and count changes between two
integrity-verified audits; it is not a pass/fail or correctness comparison. Linked interaction
segments keep a canonical deadline ledger, give every resume a fresh mode budget, and pause only
while explicitly awaiting a scientist Answer.

Only one audit may write a project's cache at a time. A contending audit does not wait: it runs
with persistent cache reuse disabled and leaves the current cache indices untouched. Accepted
ADR-0007 also HMAC-authenticates every persisted blob and mutable index with a key outside the
repository. CI supplies `SC_REFEREE_CACHE_AUTH_KEY` as URL-safe base64 for exactly 32 key bytes;
interactive macOS/Linux runs use the platform credential store when available. Missing or unsafe
credentials disable persistence without failing the audit. This defends against offline cache
replacement without claiming resistance to an active same-user process with credential access.

General and linked runs also emit exactly one PerformanceRecord measured through semantic lock.
It is replayed from the lock rather than remeasured, and the report labels it as a boundary
measurement—not total run duration. Externally submitted model proposals do not count as
controller-observed provider calls.

The `dev` extra is required for handoff verification because the verifier runs pytest. To verify the complete handoff:

```bash
python scripts/verify_handoff.py
```

## What is implemented now

The synthetic detector path remains the only complete Finding-producing path:

```text
repository snapshot
→ lightweight inventory and Python parsing
→ explicit locked claim and scientific contract
→ result-orientation normalization
→ deterministic detector evaluation
→ Finding admission gate
→ linked ConditionalConcern, MaterialQuestion, and Disclosure
→ canonical JSONL records
→ generated SQLite index
→ self-contained HTML report
→ model-free deterministic replay
```

The new product slice can also inventory an arbitrary repository, safely parse Python, Markdown,
bounded `.R` syntax, bounded nbformat-v4 notebooks, bounded Quarto sources, and exactly declared
Python/R cells, preserve unsupported workflow paths, identify publication candidates, and
extract exact directional literals from an explicitly selected Markdown report. Those literals
receive draft all-unknown ScientificContracts. One active experimental profile can independently
recompute an exact filtered mean difference from snapshotted Python/CSV inputs, emit DataAsset,
Variable, AnalysisDecision, SelectionEnvelope, auditor Execution, and Environment records, and
bind the result to a uniquely aligned claim with six independent lineage grades. It never treats
the column name as a measurement scale or auditor execution as project execution. A later linked segment can
record scope-bound structured scientist intent for any subset of the 17 contract dimensions.
Exact literal conjuncts in Python list/generator/set/dictionary comprehensions and same-base
boolean subscriptions can also become separate partial selection evidence. If any conjunct is
dynamic or unsupported, the compound predicate stays unresolved; disjunctions and chained
comparisons are not promoted. Static syntax never establishes runtime selection semantics,
execution, scientific rationale, alternatives, or outcome influence. Static project Environment
records separate nested environment roots and read bounded literal runtime declarations from
common Python, Pipenv, Poetry, uv, pixi, setup.cfg, Conda, pyenv, and runtime manifests. Conflicts
remain unresolved and malformed declarations become opaque; none proves what executed. A missing
project-execution grade can generate a proposed external trace request, never an automatic run or
scheduler submission.
When a literal Python `Path` write targets the exact selected report path, the report candidate can
reuse that exact-digest Artifact and the Claim retains the source-level writer edge. This is static
path evidence only: it does not establish that the operation ran or produced the snapshotted bytes
or wording, and a dynamic output path does not link. If the writer's single data expression also
contains a whitelisted call to one uniquely defined supported computation, its verified result
Artifact becomes a static writer input and the Claim retains that source-level flow. Result origin
remains partial. Up to eight top-level single-assignment aliases can be followed only with unique,
ordered, unshadowed bindings; over-limit chains, mutation, nested/control-flow paths, execution,
byte production, and claim-specific wording derivation are not inferred. The same bounded grammar
supports one uniquely called straight-line renderer with exactly one result argument and optional
constant-only positional presentation arguments; dynamic/defaulted/keyword arguments, multiple
results, and ambiguous calls abstain. A direct safe relative output-path string at that call may
bind an unmodified `Path(parameter)` writer target. Required parameters may bind by exact complete
keywords; dynamic, transformed, unpacked, duplicated, ambiguous, or unsafe bindings do not.
One uniquely called helper may format the writer payload only when its entire executable body is a
single return inside the same bounded render grammar; arbitrary helper interpretation remains
unsupported. That formatter output may cross one strictly linear top-level assignment chain only
when every name has one binding and one load, each intermediate feeds exactly one next assignment,
and the terminal is the complete payload of one later literal writer. The shared eight-edge limit
still applies; forks, merges, extra loads, and over-limit chains abstain as a whole.
Accepted ADR-0039 also lets one existing question-only scientific adapter use a narrower version of
that evidence when the method code and selected report are separate files. A unique safe literal
writer rooted at `Path(__file__).parent` can connect the exact Python FileRecord to the exact
selected report Artifact. Unused or competing writers, dynamic or unsafe paths, and indirect
entrypoints abstain. The connection supports a bounded scientist question and later compatibility
Disclosure only; it does not prove execution, primary-analysis role, numerical causality,
scientific correctness, or a Finding.
Accepted ADR-0040 freezes the first detector over that complete path. After a human supplies the
review requirement, the detector rechecks the Answer, unique report operand, unique static-source
operand, their agreement, the full-digest selected-output graph, and five classes of explicit
counterevidence. An exact mismatch becomes an experimental evaluation candidate only. It states
only that the two repository declarations differ from the scientist's requirement for this review;
it does not claim execution, numeric causality, historical intent, or universal method
correctness. The detector is unqualified and cannot emit a production Finding.
No production detector is eligible, so the path emits zero Findings and an explicit
`partial_evidence_unavailable` status.

The separately packaged answer-side path now preserves the label-before-detector chronology and
constructs public-development positive, verified-good, scope-verified-good, and hard-negative
fixtures only after replaying their exact panels, captures, packets, transcripts, blind workspaces,
snapshot chronology, public records, and immutable source-evidence gates. Clean controls additionally
require an already-recorded successful authorized project-workflow Execution with a qualifying
rootless-OCI SandboxCapability; construction itself never runs project code. It then
projects a Finding-shaped experimental DetectorResult without granting production authority,
reconciles two fresh Stage-3 provider judgments into one exact outcome per workflow, and retains
one digest-bound projection per DetectorResult opportunity. It calculates all twelve accepted
point estimates and 10,000 problem-cluster bootstrap replicates without model calls. Report
validation independently re-resolves fixture proof records and recomputes every metric input
digest, exclusion, count, estimate, and interval; stored fixture, outcome, or metric mutation fails
closed. This is synthetic protocol evidence, not a qualified detector or a substitute for the
still-missing external answer-blind corpus.

The Codex skill delegates to this deterministic command and summarizes only bundled records. It is
structurally validated, its typed CLI path is exercised end to end, and independent fresh-context
agents completed both the full question/proposal/answer/lock/replay path and the installed-skill
Biermann audit without executing project code. The latter exactly recovered 16,289 reported/testable
discoveries, 770 replicate-level survivors, and a 0.047271164589600345 survival rate while retaining
the result as an underpowered Disclosure with zero Findings and zero model calls.
The same authoritative skill is packaged in a locally validated Codex plugin, with a byte-for-byte
drift test between both copies. The qualification environment reports that package installed and
enabled through its personal marketplace, and the installed cache is byte-identical to the source;
rediscovery in a newly started Codex task has also passed. The core is not yet a production
auditor. Its public detectors are experimental and unqualified; the synthetic walking-skeleton
Finding producer remains a fixture-only test double rather than a public validated capability.

If a repository contains no fully identified publication-like artifact, accepted ADR-0003 permits
the audit to complete with an unresolved empty-candidate surface, a linked open question, explicit
unavailable coverage, and zero dependent detector targets. It never invents a report artifact.

## Governing rule

A `Finding` is a narrowly worded demonstrated issue. Anything that depends on a reversible unknown is a `MaterialQuestion` plus, where useful, a linked `ConditionalConcern`. Unsupported or opaque scope is a `Disclosure`. The absence of Findings is never represented as evidence that an analysis is correct.
