# Experiment 0059: Multiple-testing semantic v1 shadow recognizer

- **Status:** Stage 4 fix round; unregistered report-only adapter with a blocking grammar limitation
- **Date:** 2026-08-11
- **Authority:** Maintainer blanket approval recorded for the four-stage shadow build
- **Related decisions:** Experiment 0058 and the multiple-testing recon/design memoranda dated
  2026-08-10 and 2026-08-11
- **Production impact:** None
- **Finding impact:** None; the maximum eventual output is report-only
- **Execution impact:** None; project-authored code is parsed as frozen bytes and never imported
  or executed

## Decision

Build an additive proof-producing recognizer under
`src/sc_referee/multiple_testing_recognition/`, following the parallel-counterpart discipline used
for dependence recognition. The analyzer, bounded family prover, and future adapter are outside
the trusted kernel. Stage 1 contains only frozen IR records, bounded AST replay in the certificate
kernel, and hand-built kernel tests. It does not contain an analyzer, data prover, authority-lock
controller path, adapter, scientific-check registration, detector registration, qualification
record, or delivery-plane integration.

The only positive v1 route is visible in one Python module:

1. an ordered family-key projection over one independently proven row domain;
2. one synchronous, unfiltered list comprehension whose element is exactly a registered
   two-argument test call followed by `.pvalue` and whose two argument subscripts use the exact
   comprehension target;
3. one later direct `benjamini_hochberg` call over a literal contiguous narrowing slice of that
   battery;
4. one exact full-family report binding and selected static writer sink in the same module.

There is no v1 absence route. A missing correction anywhere, a correction in another module, or
an unbound hand-typed correction family cannot support a candidate.

## ADR-grade semantic meaning of `F_performed`

For this experiment, `F_performed` means **the supported normal-path expansion of the certified
list comprehension on paths that reach the later correction call**. It is derived without
execution by expanding the kernel-replayed comprehension template against the independently
proven ordered family domain. It does not mean tests that historically executed, completed, were
published, or produced a runtime artifact. If an exception prevents the correction call from
being reached, this experiment makes no historical-execution claim.

This meaning is normative for candidate eligibility and wording. Any implementation or report
that describes the expansion as tests actually performed, or infers runtime completion from it,
violates the experiment contract and must abstain.

## Trusted channels

The certificate may carry only proposed source spans, static identifiers, completeness sets,
evidence references, conservative effects/unknowns, and the asserted exact BH result that the
kernel recomputes. It cannot carry a trusted family fact or authority record and has no fields for
dynamic positions, dynamic result tokens, performed/corrected/reported cardinalities, normalized
slice positions, or precomputed `F_*` collections.

The kernel receives three separate controller-side inputs:

- the exact frozen module bytes, rehashed against the certificate source digest and parsed under
  the closed Python 3.11 AST identity;
- `trusted_family_facts`, looked up exactly once by full input identity, reader model, ordered key
  columns, p-value column, and iterable row domain; and
- `trusted_family_authorizations`, looked up exactly once by analysis target, correction
  procedure, family definition, kernel-recomputed semantic battery construct, iterable row
  domain, ordered key columns, and frozen input identity.

Missing, duplicate, malformed, mismatched, or extraneous facts or authorizations refuse the
certificate. Authority permits only literal `all_rows`; grouping, predicates, primary/exploratory
partitions, or inferred family selection are outside v1. Candidate batteries may later be listed
as unresolved alternatives, but they are never ranked or selected by size, proximity, names, or
repetition.

`battery_construct_id` is a source-location token derived from the frozen source digest and exact
battery assignment span. It is intentionally layout-sensitive and must not be described as a
semantic construct identity independent of source location.

A family-authority lock and controller-side producing channel analogous in discipline to the
dependence authority lock do not yet exist. Both are pre-registration requirements: no analyzer-
constructed or freely injected authority record may substitute for a digest-sealed human-approved
family definition.

## Blocking known limitation: no executable accepted positive

The current v1 source grammar admits no executable module on its positive route. The battery
requires expressions of the form `registered_test(x[g], y[g]).pvalue`, but the import-pinned,
straight-line statement set provides no supported way to bind `x` or `y`. Adding assignments or
other data-source statements makes the module unsupported. Consequently, the supported-normal-
path expansion described above is vacuous for every certificate the current analyzer and kernel
can accept: those accepted source texts would encounter unbound test-argument names if executed.

This is a **blocking known limitation**, not a coverage footnote. An executable-grammar extension
that statically binds the registered test arguments to supported data sources is required before
scientific-check registration, blind pilots, qualification, production wiring, or any evaluation
claim. The extension requires its own hostile review and must preserve kernel-derived family
positions and noninterference. Until then, this package remains an unregistered shadow experiment
and no accepted shadow candidate may be represented as evidence that an executable workflow has
the demonstrated relationship.

## Frozen family-fact envelope

`PValueFamilyFact` is a future prover output over CSV bytes. Stage 1 defines and verifies its
closed shape but does not implement the prover. The duplicated ceilings are 1,000,000 source
bytes, 10,000 data rows, 64 columns, 64 KiB per field, and 8 MiB canonical proof-record bytes.
The two reader models and their normalization claims are exactly
`csv_dictreader_splitlines`/`splitlines_rejoined_utf8` and
`csv_dictreader_file`/`byte_exact_utf8`, both with default `excel` dialect. A splitlines fact must
affirm absence of every duplicated splitlines-only separator.

The kernel requires strict alignment among row count, ordered observation tokens, byte-exact
ordered key tuples, unique hypothesis tokens, raw p-value lexemes, canonical exact-decimal
strings, and position-specific p-value tokens. Keys are unique and nonempty. P-values are
untrimmed, finite exact decimals in `[0,1]`. No float conversion, sorting, normalization,
quantization, tolerance, or numerical matching may define family scope.

## Certificate obligations

The Stage-1 kernel implements these eleven closed obligations:

1. **M1 — frozen identity and trusted lookup:** relative source/input paths, lowercase SHA-256
   digests, parser identity, source extent, case digest, exact-one fact, and exact-one family
   authority all agree; facts and authority remain kernel parameters.
2. **M2 — battery completeness equation:** kernel-enumerated syntactic `.pvalue` test-call tokens
   equal the complete set; modeled equals complete minus proven-dead; corrected tokens are a
   nonempty subset of modeled. V1 admits no conditional/dead branch, so proven-dead is empty.
3. **M3 — kernel-side position binding:** the kernel reparses the frozen module, proves the exact
   full ordered key projection and one-generator list-comprehension shape, and derives every
   `TestResultPosition` from ordered trusted hypotheses. Analyzer-supplied positions or dynamic
   result tokens do not exist in the IR.
4. **M4 — authority/domain equality:** authority, case, family obligation, trusted fact,
   projection, battery, correction, and report bind the same semantic battery construct, iterable
   row domain, ordered key columns, correction procedure, and frozen input.
5. **M5 — cardinality and token-multiset relation:** the kernel recomputes `N`, normalizes the
   direct nonnegative literal slice, derives `F_corrected`, and requires
   `0 < len(F_corrected) < len(F_performed)`, multiset inclusion, and exact full-family reported
   token equality.
6. **M6 — p-value-family fact closure:** all arrays align exactly; byte/row/column/field/proof
   ceilings hold; tokens are independently re-derived; keys are unique; missing counts are zero;
   raw and canonical decimal spellings agree exactly.
7. **M7 — correction and report binding:** one later direct BH correction consumes the exact
   battery slice; one full-family `tuple(zip(keys, pvalues))` binding and selected same-module
   writer carry the complete raw family plus the correction result.
8. **M8 — noninterference including sinks:** the kernel derives the full origin/binding slice from
   source, input, row domain, projection, battery, positions, correction, report payload, sink
   token, and sink path. Writes, aliases, relevant raising reads, opaque effects, and relevant
   unknowns refuse.
9. **M9 — supported straight-line singleton:** exactly one projection, battery, correction,
   report binding, and sink occur in source order; loops, branches, functions, wrappers, async,
   try/except, walrus, generators, competing batteries, rebinding, and extra executable module
   statements refuse.
10. **M10 — replay/evidence/basis closure:** replay digest binds parser/source identity and all
    completeness/sink sets; the basis vocabulary is exactly bounded-AST completeness, trusted
    family domain, literal narrowing slice, token-multiset relation, and trusted BH recomputation;
    every evidence identifier is declared at one valid source/data point.
11. **M11 — trusted arithmetic recomputation:** when the proposal asserts BH recomputation, the
    kernel imports the unchanged `benjamini_hochberg` implementation, applies it to the exact
    position-selected decimals, canonicalizes the result, and requires equality with the
    assertion. Numerical recomputation is supplemental and never determines family scope.

## M3 bounded replay grammar

The source grammar is deliberately smaller than general Python. The kernel requires one
`Assign(Name, ListComp)` family projection and one `Assign(Name, ListComp)` battery, each with one
synchronous generator and no filters. For one key column the projection element is
`row["column"]`; for ordered composite keys it is the exact tuple of such subscripts. The battery
element is exactly `registered_test(x[g], y[g]).pvalue`, both subscripts use the generator target,
the resolved callable is in the closed v1 registry, and no keyword arguments exist.

The correction input is exactly `battery[lower:upper]`, where each bound is absent or a
nonnegative integer literal and the step is absent. Negative/reversed slices, aliases,
concatenation, masks, index lists, copied lists, generators, or hand-typed values refuse. Result
tokens are position- and hypothesis-specific, so equal numerical p-values remain distinct tests.

## Output ceiling and wording

Every Stage-1 verified certificate is `report_only`. No delivery plane consumes it. Eventual
wording is limited to the static supported-normal-path relationship: the frozen code expands a
certified ordered family, and its correction call receives a strict position-derived subset while
the report binding names the complete family. It does not establish execution, artifact
provenance, numerical impact, bias direction, scientific invalidity, or a required repair.

## Named coverage gaps reserved for v1

- `loop-built-test-battery-unrecognized`
- `cross-module-correction-unverified`
- `hand-typed-correction-family-unbound`
- `family-definition-unauthorized`
- `per-group-correction-unrecognized`
- `value-predicate-correction-unsupported`

These names are reserved now so later analyzer/adapter stages route uncertainty to abstention
rather than broadening the positive grammar.

## Four-stage boundary

1. **Stage 1:** this experiment record, frozen IR, trusted certificate kernel, and hand-built
   certificate/mutation tests.
2. **Stage 2:** untrusted static proposing analyzer and digest-bound p-value family prover.
3. **Stage 3:** closed family-authority lock, report grammar completion, and package-local
   exception-to-abstention shadow adapter.
4. **Stage 4:** end-to-end hostile fixtures, dependency-closure replay, and qualification
   preparation only.

Stages 1-4 have no scientific-check registry entry, detector entry, qualification manifest,
production Finding route, or execution authority. Any evaluation-only or production delivery
plane requires a later explicit decision.

## 2026-08-11 Stage 2 p-value-domain amendment

Stage 2 adds only the controller-side digest-bound CSV family prover and its tests. It does not
add an analyzer, authority lock, adapter, registry entry, detector entry, Finding route, or
execution authority. The prover accepts only unsigned ASCII fixed-point p-value lexemes of the
form `DIGITS` or `DIGITS.DIGITS`. Scientific/exponent notation, signs, whitespace, underscores,
non-finite values, and values outside `[0, 1]` are unsupported and cause abstention. The raw
lexeme remains byte-exact; its separately derived canonical fixed-point spelling is used only for
trusted arithmetic and never defines family scope.

The Stage-2 API names one p-value column. To retain the frozen Stage-1 family-identity contract
without selecting among candidate keys, the prover uses the complete ordered non-value header as
the composite hypothesis key. It requires at least one non-value column and unique, nonempty key
tuples. Later authority and kernel obligations must match that complete ordered tuple exactly;
extra metadata therefore narrows to abstention rather than being ignored or guessed away.

## 2026-08-11 Stage 3 analyzer amendment

Stage 3 adds the untrusted static proposer and controller-side discharge only. The trusted kernel
continues to reparse frozen source and derive positions itself. The shipped source route requires
one of the two certified `csv.DictReader` forms, the complete ordered non-value-column projection,
one exact registered two-argument SciPy test-call comprehension, one correction, one complete
family report binding, and one selected writer sink. The exact test registry remains
`scipy.stats.ttest_ind` and `scipy.stats.mannwhitneyu` under a bound `scipy==1.14.0` requirement.

The correction registry is expanded by maintainer direction to exactly two entries:
`sc_referee.calculation_checks.bh.benjamini_hochberg` and
`statsmodels.stats.multitest.multipletests`. The statsmodels entry requires a unique bound
`statsmodels==0.14.4` requirement and the exact call keyword `method="fdr_bh"`; the repository
entry has no external-package pin. Both are recomputed with the repository's trusted exact-
Decimal BH implementation. No statsmodels or author code is imported or executed.

The kernel recognizes only two correction inputs: the bare full battery (a verified covered route)
and a nonempty literal nonnegative contiguous slice (an adverse route only when it is a proper
subset). Value-predicate comprehensions, including
`[p for p in BATTERY if p < FIXED_DECIMAL]`, are the named gap
`value-predicate-correction-unsupported`; neither analyzer nor kernel may derive their positions
from the independently proven input p-value column because that column does not prove the runtime
test results tested by the authored predicate. Other predicates, aliases, masks, negative bounds,
steps, empty selections, multiple batteries/corrections, helpers, mutation, rebinding, or control
flow abstain. Absence of a same-module correction remains outside scope and is reported as
`cross-module-correction-unverified`; it never supports an absence finding.

When a correction procedure record is present, it authorizes a call only if it declares the exact
`resolved_callable`; omission is not wildcard authority. Kernel replay also rechecks cardinality
by correction-input kind: a slice must select strictly between zero and the trusted family count,
while the bare battery must select exactly the full trusted count.

## 2026-08-11 Stage 4 shadow-adapter amendment

Stage 4 completes only the unregistered package-local shadow build. The
`MultipleTestingRecognitionShadowAdapter` accepts one `FrozenInspectionContext` and orchestrates
the untrusted analyzer, controller-side digest-bound family proof and trusted family-authority
lookup, and the certificate kernel. It never executes project-authored code and has no
scientific-check registration, detector registration, qualification record, production Finding
route, or execution authority.

The adapter projects exactly four report-only payload classes. A verified
`correction_subset` conclusion matching the controller's `evaluation_candidate` outcome may
produce a shadow candidate. A verified `complete_family_correction` conclusion matching the
controller's `covered_negative` outcome may produce a coverage note. An unresolved family
authority produces a material question naming analyzer-discovered candidate battery construct
identities and family-key columns without ranking or selection. Every unsupported,
not-applicable, mismatched, or exceptional path produces a named non-accusatory abstention.
Candidate and coverage projections require an accepted certificate; questions and unsupported
routes do not. The verified certificate and discharged certificate must both bind the analyzer's
exact source path, source digest, and proposed case digest. A proposal/discharge mismatch or a
conclusion/outcome mismatch always abstains.

Every adapter boundary catches `BaseException`, including analyzer, prover/kernel discharge, and
payload projection failures, and converts it to a named abstention. This broad catch is confined
to the shadow `inspect` boundary and is an epistemic fail-closed rule, not a runtime-recovery or
execution privilege. Payload wording is limited to supported-normal-path static relationships;
it may not claim historical execution, numerical impact, bias direction, invalidity, or a
required repair.

The implementation identity is the deterministic SHA-256 closure over exactly
`__init__.py`, `adapter.py`, `certificate.py`, `ir.py`, `pvalue_domain.py`, and
`python_analyzer.py` in the multiple-testing-recognition package plus this Experiment 0059
record. It excludes dependence/founder files, production integrations, registries, and frozen
lanes. Identical frozen inputs must produce byte-identical canonical payloads, including this
closure digest. Any evaluation-only or production registration remains a later explicit
maintainer decision.
