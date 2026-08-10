# Experiment 0057: Founder-orientation semantic v3 shadow recognizer

- **Status:** Active development shadow; not qualified or promoted for Finding output
- **Date:** 2026-08-09
- **Governing boundary:** ADR-0069 and the frozen founder-orientation v2.2.6 tuple
- **Production impact:** Adds an independent question-only shadow adapter; v2.2.6 remains present
  and byte-identical
- **Finding impact:** None; this experiment does not qualify a detector or authorize a Finding
- **Execution impact:** None; the recognizer remains non-executing and reads only controller-bound
  immutable data bytes

## Decision

Evaluate a proof-producing semantic abstract interpreter alongside founder-orientation v2.2.6.
The analyzer may recognize more compositional Python spellings, but it has no observation authority
by itself. It must emit a closed typed certificate, and a smaller independent kernel must accept
every row-alignment, transform, selector, fold, sink-lineage, path-agreement, noninterference, and
comparison-completeness obligation before the adapter can emit an operand.

The v2 and v3 adapters are independent inputs to the existing scientific-check reducer. If both
are applicable and disagree on the operand or analysis-scope join, the module is ambiguous. An
explicit ambiguity from either adapter also dominates. There is no vote, precedence rule, or
fallback that converts disagreement into an operand. V2 abstention does not manufacture a vote
against a complete v3 certificate.

## Frozen epistemic boundary

- An orientation observation describes the exact report-reaching equality selector and its
  staged-column parity. It does not infer intended biology, approve a repair, establish execution,
  or certify numeric correctness beyond the closed proof.
- Selector recovery is extensional over exactly one predicate and exact numeric false/true values.
  Equality must receive the strictly larger value.
- A parity transform is accepted only when the kernel can justify it over the represented runtime
  domain. In particular, xor-one, absolute-difference-one, and logical-not remain abstentions
  until a separate proof establishes a binary staged-column domain; their Python semantics are
  not complements over arbitrary numeric values.
- Helper bodies are evaluated with call-site abstract arguments. Unsupported recursion, variadic
  dispatch, higher-order use, or unresolved control joins abstain when they can reach the proof
  slice.
- Ordinary opaque constructs outside the certified slice do not invalidate a certificate. The
  v2 module-wide bans for reflection, import substitution, dynamic dispatch, executable
  annotations, star imports, and builtin shadowing remain fail-closed.
- The orientation-from-report-numbers CSV refinement is not enabled. Report arithmetic and staged
  values never choose an orientation or repair an unresolved parity bit.
- Production code execution is prohibited. Only the explicitly admitted digest-bound staged-data
  view is added; sandbox execution evidence is not an analyzer input.

## Implementation identity

The v3 adapter implementation digest binds the complete new semantic dependency closure:

1. `founder_orientation_semantic_adapter.py`;
2. `founder_orientation_semantic.py`;
3. `founder_orientation_certificate.py`;
4. `founder_orientation_semantic_ir.py`;
5. `founder_orientation_csv_domain.py`;
6. `core.py`; and
7. `integration.py`.

The closure also binds the frozen v2/report helpers reused for parsing, hard bans, report
reconciliation, and tokenization. A change to any bound byte changes the adapter identity.

## Development acceptance gates

- each error-bearing founder pilot either produces the repaired operand or records the exact
  fail-closed v3.0.1 abstention introduced by a demonstrated hardening obligation;
- all ten paired pilot controls produce no repaired operand;
- every historical executable wrong-answer counterexample either abstains or agrees with runtime;
- all 27 envelope-10 burned cases and the frozen v2 suite remain green;
- release-manifest, regression-corpus, capability-ledger, and prospective-template derivations
  replay from the changed component inventory; and
- the repository's complete lint, type, test, and starter-validation gates pass.

Passing these development gates does not promote v3 beyond question-only shadow status. Any later
Finding authority still requires the accepted prospective qualification and explicit promotion
process.

## v3.0.1 fail-closed hardening

The v3.0.1 lowering pass makes two analyzer invariants structural. Every evaluated subtree that
cannot be modeled emits an opaque wildcard-write effect over its complete syntactic read set and
invalidates the bindings and origins it may touch. Every selector constructor carries the tracked
condition or index as a parent. Selected-result fields are tracked independently from diagnostic
fields, so comparison completeness is no longer inferred from the same payload lineage offered as
the sink proof.

V3.0.1 also adds live-callable dispatch, normalized selected paths, conservative cross-document
effects, definition-time default and control-transfer abstentions, exact-arithmetic and AST/helper
budgets, and explicit staged-transform domain effects. CSV refinement remains disabled. Because
the five pilot contexts contain the report and workflow but no independently checkable staged CSV
domain, all five former repaired positives now abstain; none is special-cased around the missing
row-completeness, cast, finiteness, or Decimal-context proof.

## v3.1.0 digest-bound staged-data domain proof

V3.1.0 replaces the unresolved compared-column transform effects with explicit certificate
obligations. Each projection participating in the report-reaching equality must identify one exact
CSV reader path, the digest of the single intake-selected material input at that path, its row
domain, its exact column name, and its complete primitive transform sequence. Both equality
operands receive independent obligations even when only one carries `1 - x`.

The controller freezes at most 8 selected material inputs, at most 8 MiB each and 64 MiB total,
only after all of these checks succeed: the path is a bounded regular file in the immutable
snapshot, the repository snapshot lists it in `x-material-full-digest-paths`, its public
`FileRecord` points to one `AssetIdentity`, that identity is `full_digest` over the same file
reference, and re-hashing the materialized bytes reproduces the identity digest. The frozen
inspection context exposes the bytes plus the path, file reference, asset-identity reference, and
digest. It exposes no filesystem or execution handle.

For one obligation, `founder_orientation_csv_domain.py` re-hashes those frozen bytes and uses
strict UTF-8 plus the default `csv.DictReader` grammar under these closed ceilings: 8 MiB, 100,000
data rows, 256 header fields, and 64 KiB per decoded header or data field. A positive fact requires
a nonempty table, a unique header containing the exact named column, no extra or short/ragged row,
and every value in that column to be exactly `"0"` or `"1"`. Whitespace is not normalized. Any
digest mismatch, parse or encoding failure, missing or duplicate column, non-binary value, empty
table, or ceiling overflow produces no fact.

The controller, not the analyzer, attaches prover results to the proposed certificate. The kernel
accepts a discharge only when the trusted fact and obligation have the same path, digest, column,
and row binding and when the obligation is exactly the one recomputed from an active comparison
projection. The kernel requires the supplied fact set to equal the used fact set, rejects duplicate
or extraneous obligations, and requires all columns on one row domain to agree on digest and row
count. No fact leaves the v3.0.1 obligation undischarged, so the adapter abstains.

The v3.1 lowering also closes three non-policy defects exposed when the pilot obligations became
dischargeable: recognized builtin calls no longer manufacture an “unbound name” wildcard effect;
formatted fields on one f-string line receive distinct deterministic tokens instead of overwriting
one another; and exact aggregate/row-count report formatting preserves its existing selector-fold
provenance through `Decimal`, `Fraction`, and ordinary arithmetic. These repairs add no orientation
source. The kernel still requires the same active comparison, selector, fold, selected-result sink,
and noninterference proof, and the CSV fact still discharges only compared-column transform
domains.

### Data versus execution boundary

Reading digest-bound immutable staged **data** is not execution under ADR-0069. The controller and
prover decode inert CSV bytes; no scientist-authored Python, R, shell, notebook, import hook,
formula, macro, or other project code runs. The data proof establishes only that column `K` in the
exact bound bytes contains values from the finite recognized binary string set. It does not
establish that the workflow executed, infer intended biology, infer orientation from observed
counts or rates, or approve a complement.

This is deliberately narrower than the disabled orientation-from-report-numbers “CSV refinement.”
That retired idea used numeric coincidence to resolve orientation and remains prohibited. V3.1.0
uses data only to show that `int`, finite `float`, `Decimal`, and `Fraction` conversion are total on
the compared values and that `1 - x` is a real 0/1 complement. Static source still supplies the
orientation parity, equality, selector, fold, and report-sink proof.

### Fail-closed cases

The v3 adapter abstains when the staged path is unresolved, when zero or multiple bound inputs
match it, when a comparison column identity is unresolved, when the path or digest differs between
the static trace and fact, when either compared column lacks an exact binary fact, when any CSV row
or value fails the closed profile, or when the source uses a transform outside the fact-covered
grammar. Non-compared quantitative gating columns are not used to infer orientation and receive no
binary claim from this mechanism.

## v3.1.1 reader-form / line-model binding

V3.1.0 left one obligation implicit. The prover parsed the staged bytes with `csv.DictReader` over
`io.StringIO`, i.e. under `csv`'s own newline model (`\r`, `\n`, `\r\n`). The analyzer, however,
certifies workflows whose reader is `<path-like>.read_text(...).splitlines()` fed to
`csv.DictReader(list_of_lines)`. Python `str.splitlines()` starts a new line on more code points
than `csv` does: the vertical tab `\x0b`, form feed `\x0c`, the information separators `\x1c`,
`\x1d`, `\x1e`, the Next Line `\x85`, and the Unicode line and paragraph separators `U+2028` and
`U+2029`. The prover's row model and the certified reader's runtime row model were therefore two
different parsers whose equivalence was assumed rather than proven. Divergence was only incidentally
safe: a workflow that hit one of these code points produced an extra, short runtime row, whose cast
then raised, so no report was written and reconciliation failed. Nothing tied the prover's row model
to the reader form the analyzer had modeled.

V3.1.1 makes the binding explicit and fail-closed.

- **Reader-form identity in the obligation.** When the analyzer models the staged read it already
  knows the reader form: a `read_text().splitlines()` chain yields the `_InputLines` value, and
  `csv.DictReader` over an open file yields the `_FileHandle` value. It now records one line model
  per staged row domain (`row_line_models`): `splitlines` for the former and `csv_newline` for the
  latter. Any other `csv.DictReader` source stays unknown and abstains as before. The certified
  line model is threaded into each `TransformDomainObligation` (new `line_model` field) and into the
  row-domain digest, so a compared projection's obligation carries the exact model of the reader
  that produced its rows.
- **The prover reproduces the certified model.** `prove_binary_csv_column` takes a required
  `line_model`. For `splitlines` it enumerates rows with `csv.DictReader(text.splitlines())` -- the
  exact runtime construction -- but only after confirming the decoded text holds none of the
  splitlines-only separators listed above; any such separator anywhere in the bytes makes
  `str.splitlines()` and `csv`'s newline model able to disagree, so the prover returns no fact. For
  `csv_newline` it uses `csv`'s newline model over the untranslated text, which handles quoted
  embedded newlines the same way the open-file reader does at runtime. An unrecognized line model
  produces no fact. The proven `CsvBinaryDomainFact` carries the `line_model` it was proven under.
- **The kernel binds fact to obligation.** `verify_orientation_certificate` accepts a discharge only
  when the obligation's `line_model` is recognized and the trusted fact's `line_model` equals it. A
  fact proven under `splitlines` can never discharge a `csv_newline` obligation, or vice versa, and
  an unknown model leaves the obligation undischarged, so the adapter abstains. The domain fact now
  describes the same rows the certified reader actually produces at runtime.

The ragged-row obligation is unchanged and already correct. The prover rejects both a short
`csv.DictReader` row (a missing compared value under `restval=None`) and a long row (extra values
under the `None` restkey), which is at least as strict as a runtime reader that indexes and casts
the compared column directly. A reader that tolerates a ragged row cannot reach a certified
emission: `row.get(col, default)` is an opaque method on the row value that forces a fail-closed
effect, and a `try`/`except` around the cast is an unmodelled statement (and unsupported loop-carried
control) that likewise abstains. The five splitlines pilots continue to certify repaired over their
clean binary CSVs, and the ten paired controls still emit no repaired operand.

The v3.1.1 change touches only the semantic dependency closure (`founder_orientation_semantic.py`,
`founder_orientation_certificate.py`, `founder_orientation_csv_domain.py`,
`founder_orientation_semantic_ir.py`, and `founder_orientation_semantic_adapter.py`); the adapter
and recognition grammar advance to `3.1.1` and the implementation digest rebinds the changed bytes.
The frozen founder-orientation v2.2.6 modules remain byte-identical.
