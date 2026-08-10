# Experiment 0058: Dependence semantic v1 shadow recognizer

- **Status:** Active development shadow; Stage 1 contract and trusted kernel only
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
and direct tests may project an accepted evaluation as a report-only candidate, an unresolved unit
definition as a MaterialQuestion payload, an unsupported construct as a non-accusatory abstention,
or a covered case as a coverage note.  None of those projections grants Finding authority.

## Frozen authority channel

The only v1 authority input is the existing `human_method_authorization` shape used by the
declaration adapters.  It must be `authorized` and bind the exact analysis target, procedure, and
independent-unit-definition identity.  The internal unit-key binding must name the exact ordered
CSV key columns governed by that authorization.  An absent or mismatched authority leaves the unit
definition unknown.  Candidate columns may be reported as unresolved choices but are never ranked,
selected from their names, or selected because their values repeat.

## Frozen reader and data envelope

The only certified readers are the two existing default-`csv.DictReader` forms:

1. `csv.DictReader(path.read_text(...).splitlines())`, with line model `splitlines`; and
2. `csv.DictReader(path.open(...))` (or the exact builtin-open equivalent), with line model
   `csv_newline`.

Both use the default `excel` CSV dialect.  The prover must enumerate rows under the certified line
model.  A `splitlines` proof abstains if the decoded bytes contain any separator recognized only by
`str.splitlines`: vertical tab, form feed, file/group/record separator, NEL, U+2028, or U+2029.
Strict UTF-8, unique nonempty headers, nonempty tables, complete non-ragged rows, exact full-digest
binding, and the duplicated 8 MiB / 100,000-row / 256-field / 64 KiB-field ceilings apply.  Key
comparison is byte-exact after strict UTF-8 decoding: no trimming, case folding, numeric coercion,
dtype inference, NA inference, or sentinel guessing.  An empty or declared-missing key component
abstains.

The unchanged dependence core requires one complete membership per analyzed observation.  V1
therefore sets `MAX_V1_MEMBERSHIPS = 10_000`.  A larger analyzed frame is not summarized; it records
the named unsupported construct `membership-scale-above-v1-bound`.

## Frozen procedure registry

The trusted v1 registry contains exactly these resolved live callables and argument shapes:

| Resolved callable | Accepted call shape | Registered behavior |
| --- | --- | --- |
| `scipy.stats.ttest_ind` | exactly two positional data arguments; no keywords | row-independent |
| `scipy.stats.mannwhitneyu` | exactly two positional data arguments; no keywords | row-independent |
| `scipy.stats.ttest_rel` | exactly two positional data arguments; no keywords | paired |

Every entry requires an exact SciPy version from a bound requirements or lock-file evidence record.
V1 makes no cross-version stability claim.  If the imported version is not pinned, the callable is
rebound or wrapped, the argument shape differs, or the live callable is outside this table,
procedure semantics are unsupported.  `ttest_rel` discharges
`safeguard:paired-or-blocked-procedure` as present only when its unit operand is bound to the exact
authorized unit key.

## Frozen frame-transform grammar

A certified frame lineage is one digest-bound read, followed by zero or more of these transforms,
and then one registry procedure call:

- identity-preserving variable rebinding or tuple passing;
- `groupby(...).mean()` with grouping columns exactly equal to the authorized unit key; or
- `groupby(...).first()` with grouping columns exactly equal to the authorized unit key.

The two groupby forms establish `safeguard:unit-level-aggregation` as present and therefore support
only a covered negative.  Every filter, merge, sample, slice, apply, other deduplication, loop-built
frame, or other transform is unsupported in v1.  Membership evidence comes only from the exact
digest-bound file consumed by the reader in the same lineage.

## Certificate obligations

The kernel accepts only a closed certificate that discharges all of the following:

1. **O1 — bound file identity:** one relative path, SHA-256 content digest, file record, and
   full-digest asset identity agree across obligation, fact, and lineage.
2. **O2 — certified reader model:** the reader form, default dialect, and runtime line model agree
   across obligation, fact, and lineage.
3. **O3 — well-formed frame:** a nonempty uniquely headed table contains every ordered key column,
   has no ragged or missing key row, and remains within the closed ceilings.
4. **O4 — fact/obligation equality:** trusted facts equal declared facts and used facts, with no
   duplicate, missing, or extraneous fact or obligation.
5. **O5 — fact closure:** path, digest, references, line model, row counts, observations,
   memberships, multiplicities, and repeated-unit identities are internally consistent.
6. **O6 — unit-key multiplicity:** every source observation has exactly one proven unit identity;
   the kernel recomputes exact multiplicities and whether repetition is present.
7. **O7 — key domain:** ordered composite keys are byte-exact, unnormalized, nonempty, and free of
   declared missing values.
8. **O8 — frame lineage:** the proven source frame reaches the registered procedure through only
   the frozen transform grammar; direct and unit-collapsed row domains cannot be confused.
9. **O9 — procedure identity:** exact live callable, two-positional/no-keyword shape, pinned SciPy
   version evidence, procedure binding, row domain, result token, and paired-unit operand agree.
10. **O10 — safeguard completeness:** the seven existing safeguard identities appear exactly once.
    For each, modeled constructs equal the complete syntactic set minus proven-dead constructs.
    `absent` or `not_applicable` requires evidence, no recognized match, and that exact equation;
    recognized aggregation or paired matches require `present` with the exact operand binding.
11. **O11 — noninterference:** no opaque or wildcard effect writes a relevant binding, aliases a
    relevant origin, or may raise while reading a relevant origin; relevant unknowns also block.
12. **O12 — exact affected sink:** every active selected sink binds the same result or Claim, exact
    procedure call, exact procedure-result token, and payload lineage.
13. **O13 — singleton resolution:** the active-sink completeness equation closes and every sink and
    every reaching control path agrees on the one recomputed repetition conclusion.

The certificate additionally requires the exact authorized unit definition, parser and source
identity, evidence spans, safeguard-registry identity, dependency-closure digest, proposed case
digest, report-only output ceiling, and wording ceiling.

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

## Stage boundary

Stage 1 adds only this experiment record, typed IR, the trusted certificate kernel, and hand-built
certificate tests.  It contains no analyzer, CSV prover, adapter, harness, registry integration, or
project-authored-code execution.
