# Experiment 0059: Multiple-testing semantic v1 shadow recognizer

- **Status:** Stage 1 contract and hand-built trusted-kernel evidence only
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
