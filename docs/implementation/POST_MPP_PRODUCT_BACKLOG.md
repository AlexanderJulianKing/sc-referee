# Post-MPP product backlog

## Purpose

sc-referee now has a working minimal proud product: it can conservatively inspect an arbitrary
repository, preserve evidence and unknowns, ask bounded scientist questions, run a small set of
deterministic checks, lock the result, and replay it without model access. The next objective is
useful breadth—not a claim that the program can determine whether any scientific workflow is
correct.

This backlog is the current ordering for post-MPP development. Historical experiments and accepted
ADRs remain authoritative for their exact scopes.

## Current baseline

The 0.3.0 baseline contains:

- 20 active question-oriented scientific checks through 26 bounded adapters;
- 10 active deterministic calculation-check families;
- 16 published capability profiles;
- one experimental method-conflict detector binding; and
- zero qualified detectors with production Finding authority.

Those counts describe installed registry entries, not general scientific coverage. Most scientific
checks recognize explicit selected-report language, and many ordinary code-to-report or
cell-to-analysis relationships remain unsupported.

## Development rules

1. Preserve old failures, corrected twins, and independent repositories as permanent regression
   cases. Never replace a difficult case with an easier fixture.
2. Add connectivity or an adapter only for a named evidence gap observed in a frozen workflow or
   independently authored repository.
3. Reuse an existing scientific check when its abstract obligation is unchanged. New wording,
   language, file format, or tool syntax usually requires an adapter—not a new check.
4. Add a new scientific check only after the same atomic choice recurs beyond its design source.
5. No module ships with only a positive fixture. Its regression pack must cover every applicable
   control class below.
6. Questions, deterministic Disclosures, experimental detector candidates, and production
   Findings remain separate authority levels.
7. Unsupported and ambiguous inputs must remain explicit. Broader recognition must not convert
   them silently into negative coverage.
8. The production path remains non-executing. Post-MPP execution stays deferred until a concrete
   scientific need justifies its security and evidence cost.

## Mandatory regression pack

Every new or materially changed check, adapter, parser, scope join, or artifact reader must add the
applicable cases below before it is complete:

- **Positive:** the exact supported issue or unresolved choice is recognized.
- **Corrected twin:** the same workflow with the relevant repair does not produce the issue state.
- **Hard negative:** a close syntactic or scientific lookalike does not trigger.
- **Ambiguous:** competing operands, scopes, or declarations stay unresolved.
- **Unsupported:** an unimplemented representation is reported as unsupported, not coerced.
- **Counterevidence:** every finite suppressor can independently prevent escalation.
- **Removal and sibling isolation:** disabling one module changes only that module's coverage.
- **Mutation:** identity, manifest, source, artifact, or semantic drift fails closed.
- **No execution and no late model access:** project code is not executed and no model call occurs
  after semantic lock.
- **Replay:** semantic records, assessment counts, coverage, and report meaning replay exactly.
- **Independent false-positive control:** at least one unrelated or independently authored
  repository stays question- and Finding-clean for the new path when it is not applicable.

Tests derived from a benchmark answer key may establish development behavior but cannot, by
themselves, qualify a detector or support a public generality claim.

## P0 — Freeze and continuously test what already works

- [x] **L01 — Machine-readable regression corpus ledger.** Create a versioned ledger that names
  every retained synthetic fixture, frozen failed workflow, corrected twin, independent repository,
  expected applicability state, permitted assessment ceiling, and exact source revision.
  - Acceptance: every active scientific-check and calculation-check family maps to at least one
    retained case; answer-side or benchmark-derived cases are labelled and excluded from
    qualification counts.
  - Tests: schema/shape validation, unique IDs, resolvable paths or immutable external revisions,
    complete registry coverage, forbidden qualification leakage, and mutation rejection.
  - Limitation: inventory coverage does not establish scientific representativeness.

- [x] **L02 — One-command corpus regression runner.** Add a test runner that audits and replays the
  ledger's local non-executing cases and compares declared semantic outcomes without relying on
  disposable SQLite or unstable timestamps.
  - Acceptance: one command detects a lost question, new false question, changed output ceiling,
    missing Disclosure, unexpected Finding, replay difference, project execution, or post-lock
    model call.
  - Tests: intentionally mutate each comparison dimension and prove that the runner fails for the
    right reason; include partial and unsupported audits.
  - Limitation: external repositories that are not vendored or available offline require a
    separately pinned preparation step.

- [x] **L03 — Baseline every current module.** Fill the mandatory regression pack for all current
  scientific checks and calculation checks, beginning with modules that presently rely mostly on
  one development workflow.
  - Acceptance: no active module lacks a positive or applicable case, corrected or conformant
    control, ambiguity/unsupported boundary, hard negative, removal check, and replay check.
  - Tests: generated completeness test over the registry and corpus ledger; existing focused tests
    remain and are referenced rather than duplicated.
  - Limitation: some question-only checks may not have a scientifically authorized “correct” arm;
    those retain matching and unresolved controls instead of inventing one.

## P1 — Make ordinary repositories connect to the existing machinery

- [x] **L04 — Publication and input selection ergonomics.** Let the scientist resolve ambiguous
  report, source, input, and output candidates through bounded typed questions instead of editing
  internal records or rerunning discovery by hand.
  - Acceptance: selected identities bind to the immutable snapshot and resume segment; stale,
    conflicting, missing, or unsafe selections remain unresolved.
  - Tests: zero/one/many candidates, stale Answer, path traversal, symlink, digest drift, linked
    resume, cancellation, semantic lock, and replay.
  - Limitation: scientist selection establishes review scope, not execution or scientific
    correctness.

- [x] **L05 — General static scope joins.** Replace check-specific connectivity with reusable typed
  joins from selected publication surface to source, cell, declared inputs, deterministic outputs,
  and imported execution evidence where each edge is independently supported.
  - Acceptance: current founder-orientation, notebook/Quarto-cell, separate-source, calculation,
    and Biermann paths use the common join without changing their outputs.
  - Tests: multiparent and same-path identity, ambiguous producer, unused source, dynamic writer,
    transformed payload, weak identity, unselected artifact, module removal, and byte replay.
  - Limitation: a static writer path does not prove that code ran or produced the snapshotted bytes.

- [x] **L06 — Natural-language adapter expansion.** Broaden existing selected-report adapters to
  natural, independently observed scientific wording while keeping each normalized operand and
  output ceiling unchanged.
  - Acceptance: each grammar expansion is justified by a frozen real example and adds close
    negative, ambiguity, and wording-mutation controls; no adapter keys on benchmark or repository
    identity.
  - Tests: parameterized adapter conformance suite plus corpus-level false-question regression.
  - Limitation: text can establish an explicit declaration, not that the declared method was run.

- [x] **L07 — Python and R source adapters for existing checks.** Add bounded AST-based source
  observations for the highest-value existing questions, prioritizing calculation setup, design
  matrices, selection reuse, multiple-testing families, and method arguments.
  - Acceptance: source adapters emit the same normalized method observation as report adapters;
    disagreement remains explicit and cannot be arbitrated by model confidence.
  - Tests: direct/namespaced calls, aliases allowed by the closed grammar, shadowing, dynamic
    dispatch, formulas, branches, competing calls, parser disagreement, and cross-language
    equivalent controls.
  - Limitation: static calls do not establish runtime values, package behavior, or primary-analysis
    status.

- [x] **L08 — Notebook, Quarto, and R Markdown analysis connectivity.** Extend the existing inert
  cell parsers with bounded same-document scope and dataflow joins needed by L05 and L07.
  - Acceptance: selected active cells can contribute supported observations and exact citations;
    disabled, unselected, cross-cell-ambiguous, or state-dependent paths abstain.
  - Tests: cell reordering, duplicate text, execution-count mismatch, hidden state, conflicting
    language declaration, disabled cells, prose/code disagreement, cache invalidation, and replay.
  - Limitation: saved output remains reported evidence, not reproduced execution evidence.

## P2 — Broaden useful deterministic scientific coverage

- [x] **L09 — Generalize the eight current calculation checks beyond capsules.** Separate their
  normalized scientific inputs from repository-specific filenames, headings, and fixture layouts.
  Start with multiple-testing families, design integrity, single-cell replicate sensitivity, effect
  relevance, and selection reuse.
  - Acceptance: each check works on at least two materially different layouts through separate
    adapters while the calculation core remains unchanged.
  - Tests: reordered columns, alternate safe identifiers, missing and duplicate IDs, extra rows,
    units, NA representations, thresholds, over-budget inputs, and cross-adapter equivalence.
  - Limitation: a deterministic recomputation is authoritative only for the exact declared
    calculation and independently verified inputs.

- [ ] **L10 — Large single-cell and tabular artifact support.** Add bounded, chunked readers for
  concrete high-value formats encountered by the corpus, prioritizing sparse H5AD, Zarr, Parquet or
  Arrow, and compressed delimited summaries without loading whole multi-million-cell datasets.
  - Acceptance: material-read budgets are declared and measured; over-budget projects complete
    with localized partial coverage; selected summaries can feed L09 when their identities and
    semantics are exact.
  - Tests: sparse and dense layouts, malformed metadata, duplicate features/cells, chunk-boundary
    mutations, compression bombs, huge synthetic shapes, weak identity, cancellation, and bounded
    bytes/memory assertions.
  - Limitation: format support does not imply support for every assay, layer, normalization, or
    biological unit stored in that format.
  - Completed tranche: ADR-0053 and Experiment 0044 add exact selected dense/CSR/CSC H5AD
    inventory with 1 MiB chunks, a separate 64 MiB decompressed-read ceiling, deterministic read
    receipts, million-scale logical-shape coverage, duplicate-axis handling, and cancellation/
    deadline checkpoints. The 16 MiB exact physical-file boundary remains unchanged.
  - Completed tranche: ADR-0054 and Experiment 0045 add first-logical-record inventory for exact
    `.csv.gz` and `.tsv.gz` files with 64 KiB chunks, a 1 MiB header ceiling plus one sentinel
    byte, deterministic read receipts, quoted-newline coverage, and cancellation/deadline checks.
  - Completed tranche: ADR-0055 and Experiment 0046 feed exact `.csv.gz` and `.tsv.gz` bytes into
    all seven table-consuming L09 families after complete bounded validation. Reads use 64 KiB
    chunks, an 8 MiB per-input decoded-content ceiling plus a sentinel byte, a 64 MiB aggregate
    logical ceiling, separate physical and decoded identities, deterministic receipts, and
    cancellation/deadline checkpoints. Parquet/Arrow, Zarr, and large physical-file paths remain
    pending and require concrete corpus demand before implementation.

- [ ] **L11 — Recurrence-driven scientific-check loop.** Continue frozen answer-isolated challenge
  workflows, but classify each miss before coding: connectivity gap, adapter gap, genuinely new
  atomic scientific choice, unsupported representation, or absent governing authority.
  - Acceptance: new checks require independent recurrence and the mandatory regression pack;
    one-case probes remain evaluation-only.
  - Tests: controlled repair and reverse control where feasible, sibling-module isolation, and
    regression of every earlier workflow touched by the change.
  - Limitation: passing a repaired benchmark workflow does not prove the repair is universally
    correct.
  - Completed loop: ADR-0056 and Experiment 0047 froze three independent ScienceAgentBench task-70
    authors as clean development controls after the proposed donor-adjustment omission did not
    recur; no check was added.
  - Completed loop: ADR-0057 and Experiment 0048 add the Disclosure-only selected sequence-record
    boundary check after three independent task-12 authors repeated one exact join-every-line
    mistake and a fresh corrected author did not. The v12 grammar requires selected exact bytes,
    inert AST, and exact path flow; it contains no benchmark identity or answer authority.

- [ ] **L12 — Natural non-benchmark validation.** Maintain a commit-pinned collection of unrelated
  public repositories and scientist-supplied local projects that exercise supported methods,
  including clean, ambiguous, unsupported, and—when independently demonstrated—positive cases.
  - Acceptance: every broadened capability states the exact adapters and corpus roles supporting
    it; public claims never exceed those tested boundaries.
  - Tests: offline materialization checks, revision drift, license/provenance metadata, answer-key
    isolation, and false-positive budgets by exact module.
  - Limitation: a finite public corpus is evidence of tested scope, not a sample of all science.

## P3 — Turn demonstrated coverage into a dependable product

- [ ] **L13 — Qualify the first production detector.** Complete K07/F09 for one frozen detector
  version using eligible positive, verified-good, ambiguous, hard-negative, removal, and
  counterevidence cases plus authenticated OpenAI/Anthropic review and maintainer approval.
  - Acceptance: the independent evaluator reproduces all labels and metrics from frozen bytes;
    pilot-informed thresholds are accepted in an ADR before production Finding permission changes.
  - Tests: answer-blind chronology, provider/context independence, transcript and packet digests,
    label mutation, metric recomputation, candidate-version drift, and production admission.
  - Limitation: qualification applies only to the exact detector, adapters, versions, and scope in
    the accepted artifact.

- [ ] **L14 — Publish complete capability truth.** Extend the generated capability output to cover
  active question modules, calculation checks, adapters, tested corpus roles, maturity, and output
  ceilings—not only the current 16 profile entries.
  - Acceptance: users can determine what was checked, what was unsupported, and what could produce
    a question, Disclosure, experimental candidate, or Finding.
  - Tests: registry-to-matrix completeness, stale digest/version rejection, unsupported-state
    rendering, removal behavior, installed-wheel reproduction, and schema migration if required.
  - Limitation: because this changes public capability-record meaning, implementation requires an
    accepted ADR and possibly a coordinated schema release.

- [ ] **L15 — Scientist-answer and skill ergonomics.** Add concise question summaries, explain why
  each question was asked, show exact affected evidence and consequences, and guide the scientist
  through unresolved items without allowing the agent to answer for them.
  - Acceptance: a fresh-context Codex user can audit an unfamiliar mixed-language repository,
    resolve or retain unknowns, lock, interpret, and replay using the installed skill.
  - Tests: fresh-context usability fixtures, direct CLI parity, invalid or stale Answers,
    inaccessible evidence, zero-question audits, partial coverage, and non-certifying summaries.
  - Limitation: usability testing with coding agents does not establish scientific validity.

- [ ] **L16 — Optional transport after CLI stability.** Consider MCP or another agent transport only
  when it can be a thin wrapper over the tested CLI protocol and materially improves integration.
  - Acceptance: transport and CLI produce the same canonical records and authority boundaries.
  - Tests: protocol conformance, interruption/resume, malformed client input, and byte-identical
    semantic lock/replay.
  - Limitation: transport work adds no scientific coverage by itself and is lower priority than
    L01–L15.

- [ ] **L17 — Keep project execution deferred.** Revisit authorized execution only after the
  evidence-first product encounters a high-value demonstrated issue that cannot be resolved from
  existing artifacts and bounded inspection.
  - Acceptance: any reactivation starts with the unresolved security/evidence ADRs and has no unsafe
    fallback; it is never an MPP prerequisite.
  - Tests: authorization, rootless OCI capability, immutable inputs, resource enforcement,
    provenance closure, cancellation, network denial, and failure-safe evidence admission.
  - Limitation: execution may be infeasible for very large workflows and is not a substitute for
    static evidence support.

## Immediate sequence

Work on the first unchecked prerequisite, in order:

1. Continue L11 with the next independently recurrent, authority-bounded issue; then
2. Begin L12 natural non-benchmark validation for the exact supported paths.

Do not begin detector promotion, MCP transport, or project execution while these prerequisites are
unfinished. Do not add speculative Parquet/Arrow, Zarr, or large-file support without a concrete
retained consumer.
