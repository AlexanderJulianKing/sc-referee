# Experiment 0058: Dependence semantic v1 shadow recognizer

- **Status:** Active development shadow; Stages 1-4 remain unregistered and report-only
- **Date:** 2026-08-09
- **Related decisions:** ADR-0062, ADR-0069, Experiment 0057
- **Production impact:** None; v1 is not registered as a scientific check or detector
- **Finding impact:** None; the maximum adverse output is a report-only evaluation candidate
- **Execution impact:** None; project-authored code is never imported or executed

## Decision

Build an additive proof-producing dependence recognizer under
`src/sc_referee/dependence_recognition/`.  The proposing analyzer and bounded data prover will be
untrusted inputs to a smaller certificate kernel.  Only a certificate accepted by that kernel may
later be normalized into the unchanged `DependenceCase` evaluator.

Version 1 has no production delivery-plane integration.  It does not edit or register a
scientific-check manifest, detector, qualification record, or safeguard.  A later shadow harness
and the package-local Stage 4 adapter may project an accepted evaluation as a report-only
candidate, an unresolved unit
definition as a MaterialQuestion payload, an unsupported construct as a non-accusatory abstention,
or a covered case as a coverage note.  None of those projections grants Finding authority.

## Frozen authority channel

The only v1 authority input is the existing `human_method_authorization` channel used by the
declaration adapters, extended inside this recognizer with the exact ordered CSV key columns and
the governed input path and content digest.  It must be `authorized` and bind the exact analysis
target, procedure, independent-unit-definition identity, ordered key columns, and frozen input.
Authority enters the trusted kernel only through a controller-supplied `trusted_authorizations`
tuple built from caller-supplied frozen records.  The analyzer may inspect those records as
untrusted selection hints, but neither it nor its certificate may construct or carry an authority
record.  The kernel looks up exactly one closed authorization by analysis target, procedure, and
independent-unit-definition identity.  Those columns and that input identity must then agree
across trusted authority, case operands, obligation, trusted fact, and lineage.  An absent,
duplicate, malformed, or mismatched trusted authorization refuses the certificate.  Before a
proposal exists, missing or ambiguous hints leave the unit definition unknown.  Candidate columns
may be reported as unresolved choices but are never ranked, selected from their names, or selected
because their values repeat.

The controller's `_procedure_record_allows` check constrains only procedure records that declare a
`resolved_callable`; a procedure record without that field supplies no callable assertion.

## Frozen reader and data envelope

The only certified readers are the two existing default-`csv.DictReader` forms:

1. `csv.DictReader(path.read_text(...).splitlines())`, with line model `splitlines`; and
2. `csv.DictReader(open(path, ..., encoding="utf-8", newline=""))` (or the exact `Path.open`
   equivalent with `newline=""`), with line model `csv_newline`.

Both use the default `excel` CSV dialect.  The prover must enumerate rows under the certified line
model.  A `splitlines` proof abstains if the decoded bytes contain any separator recognized only by
`str.splitlines`: vertical tab, form feed, file/group/record separator, NEL, U+2028, or U+2029.
The trusted fact records whether this complete separator check passed, and the kernel refuses a
`splitlines` fact unless it did.  Because `splitlines()` removes physical separators before the
CSV parser sees them, quoted fields spanning physical lines are reconstructed by the CSV iterator
with `\n`; this model is recorded as `splitlines_rejoined_utf8`, not byte-exact field preservation.
On certified inputs, `str.splitlines` treats `\r`, `\n`, and `\r\n` as separators and every
splitlines-only separator is refused, so `read_text().splitlines()` and raw-decoded-text
`.splitlines()` agree.
The `csv_newline` prover uses `StringIO(text, newline="")`, matching the untranslated-newline
reader model above.  Plain `open()` without `newline=""`, `open(..., newline=None)`, and
`read_text()` universal-newline behavior are not asserted equivalent and are outside v1.
Strict UTF-8, unique nonempty headers, nonempty tables, complete non-ragged rows, exact full-digest
binding, and the duplicated 8 MiB / 100,000-row / 256-field / 64 KiB-field ceilings apply.  Key
comparison is byte-exact after strict UTF-8 decoding: no trimming, case folding, numeric coercion,
dtype inference, NA inference, or sentinel guessing.  An empty or declared-missing key component
abstains.

The unchanged dependence core requires one complete membership per analyzed observation.  V1
therefore sets `MAX_V1_MEMBERSHIPS = 10_000`, plus an independently lower 5,000-distinct-key budget
and a complete proof-record byte budget.  A larger analyzed frame is not summarized; it records
the named unsupported construct `membership-scale-above-v1-bound`.  A domain within that
membership bound but above the distinct-key budget records the separate named unsupported
construct `distinct-key-scale-above-v1-bound`.

## Frozen procedure registry

The trusted v1 registry contains exactly these resolved live callables and argument shapes:

| Resolved callable | Accepted call shape | Supported SciPy versions | Registered behavior |
| --- | --- | --- | --- |
| `scipy.stats.ttest_ind` | exactly two positional data arguments; no keywords | `1.14.0` only | row-independent |
| `scipy.stats.mannwhitneyu` | exactly two positional data arguments; no keywords | `1.14.0` only | row-independent |
| `scipy.stats.ttest_rel` | exactly two positional data arguments; no keywords | `1.14.0` only | paired |

Every entry requires SciPy `1.14.0` from a bound requirements or lock-file evidence record.  An
unpinned version, any other version, a rebound or wrapped callable, a different argument shape, or
a live callable outside this table is unsupported.  There is no fallback based on claimed
cross-version stability.  Although `ttest_rel` is resolved as a known callable, v1 cannot verify
that its positional vectors encode pairs bound to the human-authorized independent-unit key; it
therefore records `paired-procedure-operand-unverified` and does not propose a certificate.

## Frozen frame-transform grammar

A certified frame lineage is one digest-bound read, followed by zero or more of these transforms,
and then one registry procedure call:

- identity-preserving variable rebinding or tuple passing.

The formerly proposed `groupby(...).mean()` and `groupby(...).first()` forms are not executable on
the certified list-bound readers and are dropped from the v1 grammar.  Any aggregation-shaped
construct is opaque and records the named gap `unit-level-aggregation-unrecognized`; recognizing
unit-level aggregation is a future route.  Every filter, merge, sample, slice, apply, other
deduplication, loop-built frame, or other transform is likewise unsupported in v1.  Membership
evidence comes only from the exact digest-bound file consumed by the reader in the same lineage.

The only v1 `covered_negative` route is a digest-bound proof of one row per authorized unit.

## Certificate obligations

The kernel accepts only a closed certificate that discharges all of the following:

1. **O1 — bound file identity:** one relative path, SHA-256 content digest, file record, and
   full-digest asset identity agree across obligation, fact, and lineage.
2. **O2 — certified reader model:** the reader form, default dialect, and runtime line model agree
   across obligation, fact, and lineage.
3. **O3 — well-formed frame:** a nonempty uniquely headed table contains every ordered key column,
   has no ragged or missing key row, and remains within the closed ceilings.
4. **O4 — trusted-channel/obligation equality:** facts and authorizations enter only through
   trusted controller arguments.  The authorization lookup and fact lookup keys must equal the
   complete case and obligation keys, with no certificate-embedded, duplicate, missing, or
   extraneous trusted record, fact, or obligation.
5. **O5 — fact closure:** path, digest, references, line model, row counts, observations,
   per-row ordered key tuples, derived memberships, multiplicities, and repeated-unit identities
   are internally consistent.
6. **O6 — unit-key multiplicity:** every source observation has exactly one raw ordered key tuple;
   the kernel independently derives unit identities, exact multiplicities, and repetition.
7. **O7 — key domain:** ordered composite keys are byte-exact, unnormalized, nonempty, and free of
   declared missing values.
8. **O8 — frame lineage:** the proven source frame reaches the registered procedure through only
   the frozen identity-only transform grammar.
9. **O9 — procedure identity:** exact live callable, two-positional/no-keyword shape, pinned SciPy
   `1.14.0` evidence, procedure binding, row domain, result token, and an exact binding from every
   positional argument to the certified frame-lineage output agree.  The kernel retains its exact
   paired-unit-operand equality check as defense in depth, but no shipped v1 path can discharge it.
10. **O10 — safeguard completeness:** the seven existing safeguard identities appear exactly once.
    For each, modeled constructs equal the complete syntactic set minus proven-dead constructs.
    `absent` or `not_applicable` requires evidence, no recognized match, and that exact equation;
    required-safeguard procedures and aggregation-shaped constructs cannot enter a shipped v1
    certificate.
11. **O11 — noninterference:** the kernel-derived origin/binding union includes the input, every
    row domain, frame output, procedure arguments/result, transform tokens, every active sink
    token and payload token, and every sink path.  No effect may write or alias that union.  An
    effect that may raise also blocks when it reads a relevant value or carries a wildcard read;
    relevant unknowns block.  An opaque effect is valid only with a wildcard write and therefore
    blocks the certificate.
12. **O12 — exact affected sink:** every active selected sink binds the same result or Claim, exact
    procedure call, exact procedure-result token, and payload lineage.  Its path must be relative
    and distinct from both the analyzed source path and the bound data-input path.
13. **O13 — singleton resolution:** the active-sink completeness equation closes, dead sinks are
    also syntactically dead, and every sink and reaching path agrees on the repetition conclusion
    recomputed over the analyzed post-transform row domain.  Source-frame repetition is recorded
    separately.

The certificate additionally requires exact unit-definition operands corroborated through the
trusted authorization channel, parser and source identity, parser-reported source extent,
source/data-separated and non-overlapping evidence spans, a replay digest over the source/parser
identity, extent, and all completeness token sets,
closed-vocabulary safeguard bases, cross-referenced evidence declarations, safeguard-registry
identity, dependency-closure digest, proposed case digest, report-only output ceiling, and wording
ceiling.

The replay digest establishes certificate self-consistency only.  The controller recomputes it on
the certificate shipped through the discharge path; it is not an analyzer commitment at that
boundary.  Independent replay by re-parsing the bytes identified by `source_digest` under the
recorded parser identity is future work and is not a v1 property.

A verified certificate is required only for `evaluation_candidate` and `covered_negative`
projections.  `question` and `unsupported` projections are non-accusatory and bypass this kernel;
they must not manufacture a partial certificate.  Unknown or unsupported safeguard states inside
a proposed certificate remain grounds for refusal.

## Wording and non-inferences

An accepted v1 certificate may describe only the static relationship in the inspected source: the
bound rows, authorized unit memberships, exact supported procedure, exact supported safeguards,
and selected sink lineage.  It does not establish that project code executed, that a published
number came from that execution, numerical impact, bias direction, biological truth, global
invalidity, or a required repair.

## Named coverage gaps

- `pandas-frame-model`: every `pandas.read_csv` form and every pandas-only frame semantic is outside
  v1 and must be reported as unsupported.
- `membership-scale-above-v1-bound`: more than 10,000 analyzed observations is outside v1 and must
  be reported as unsupported rather than summarized.
- `distinct-key-scale-above-v1-bound`: more than 5,000 distinct ordered keys, while remaining at or
  below the membership bound, is outside the bounded v1 proof-record envelope.
- `unit-level-aggregation-unrecognized`: aggregation-shaped code over the certified list-bound
  readers is outside v1; unit-level aggregation is a future recognition route.
- `paired-procedure-operand-unverified`: v1 cannot verify that paired-procedure vector positions
  correspond to the human-authorized independent-unit key.
- `universal-newline-reader`: a plain `open()`/`Path.open()` reader without `newline=""`, an
  explicit `newline=None`, or a `read_text()` universal-newline stream is outside the certified
  `csv_newline` model and must be reported as unsupported.
- `unsupported-write-handle`: a write-mode context manager that is outside the closed static sink
  grammar is a writer gap and is never mislabeled as a reader newline gap.

## Stage boundary

Stages 1-4 add this experiment record, typed IR, trusted certificate kernel, bounded CSV prover,
the untrusted static proposing analyzer plus controller discharge, and one package-local shadow
adapter.  The adapter has no scientific-check or detector registration and emits only a report-only
shadow candidate, material-question payload, non-accusatory abstention, or coverage note.  It
catches every exception from the analyzer, prover, kernel, and unchanged dependence evaluator,
including type-invalid proposal failures, and converts it to a named abstention.  The kernel is
not itself required to accept arbitrary dynamically ill-typed Python objects.  Candidate and
covered-negative projection additionally require the kernel conclusion to match the evaluator
outcome; a mismatch records `conclusion-outcome-mismatch`.

The shadow payload binds a dependency-closure digest over only the six
`dependence_recognition` package modules (including the adapter) and this experiment record.
Founder modules, the unchanged dependence core, registries, and production integration files are
deliberately not listed or hashed by this experiment closure.  There remains no registry
integration, detector registration, production Finding path, or project-authored-code execution.
