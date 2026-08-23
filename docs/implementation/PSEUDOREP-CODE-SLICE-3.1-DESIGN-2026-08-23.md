# Pseudoreplication code slice 3.1 delta design

**Date:** 2026-08-23

**Status:** Accepted for build under Fable's executive authority

**Base:** `docs/implementation/PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md`

**Lane:** development only; detector/check/adapter `3.1.0`

**Production boundary:** the qualified `2.1.0` binding, installed pin, wording-v1 profile, and
Finding eligibility are unchanged.

## 1. Scope and evidence boundary

This document is a delta. Every 3.0 predicate, guard, precedence rule, bound, abstention code,
prose-exclusion rule, and tripwire remains normative unless this document names an exact change.
The adapter may inspect only frozen contract fields, CSV bytes, Python AST structure, resolved API
identities, and deterministic controller records. Markdown, reports, comments, docstrings, printed
labels, and string meaning are never evidence or suppressors.

Observed: envelope 8 ran development detector `3.0.0` over twelve fresh cases and produced two of
six positive candidates, zero of six negative candidates, zero qualified Findings, and replay
equality on all twelve. Its two family-C negatives stopped on designed S1 and S2 guards. Across the
80 envelope-2-through-envelope-8 cases, 3.0 classifies 29 of 39 positives as candidates and zero of
41 negatives as candidates. Inference: H1-H7 below should classify 33 of 39 positives and zero of
41 negatives. These rules were authored after the cases were opened and are development evidence,
not blind qualification evidence.

## 2. H1: 3.x-local D1-double-prime correction

The 3.1 adapter owns a byte-local CSV parser copied from the 3.0/shared parser. It must not import or
mutate the shared `_parse_csv` implementation used by the withdrawn report profile or the qualified
2.1 lane. Encoding, newline, field, row, column, header, missing-unit, multiplicity, and ordering
bounds remain byte-identical to 3.0.

For every column `C` other than the authorized unit and contract group columns:

1. If `distinct(C) > U`, exclude `C` from composite candidacy exactly as in 3.0.
2. Otherwise form `(unit, C)` pairs. A within-unit index is now exactly: the pairs are unique and
   every declared unit repeats (`R == U`). Delete the `distinct(C) <= M` condition.
3. A candidate column with unique pairs that is not a within-unit index remains a possible
   composite-key component and causes
   `unique-nonindex-authorized-unit-composite-key-possible`.

False-accusation analysis: removing `distinct(C) <= M` can classify a previously suspicious regular
index as an index. It cannot create a composite-key accusation. The remaining `R == U` requirement
keeps the closed label-collision control unsupported. The independently measured 86-case delta is
one CSV-gate transition only: `19d0834b0899d12792f3` leaves the gate. It must then abstain on S5;
it is not a candidate.

## 3. H2: closed lambda inside an inlined helper

An `ast.Lambda` is admitted only while checking a helper selected by unchanged X4 inlining and only
when all of these hold:

1. its arguments have no defaults, positional-only arguments, keyword-only arguments, `*args`, or
   `**kwargs`;
2. every loaded name is one of its own parameters or a module-closed name: registered import alias,
   literal constant, closed constant sequence, unshadowed registered builtin, exception constructor,
   helper name, or `__file__`;
3. its body contains no nested lambda, named expression (`:=`), store context, `yield`, `await`,
   function definition, or class definition; and
4. its parameter names are added to the helper free-name walk's local-name set only for that lambda
   body. They create no value edge outside it.

Any violation retains `helper-closure-or-nested-definition-unsupported`. A lambda whose body loads a
tracked frame from its enclosing helper fails condition 2 and abstains. Once admitted, the lambda's
enclosing aggregation or guard API is still visible to the full-program S1-S5 and operand scans.
Expected transitions: positive `bba60d967342fbbd2832` becomes a candidate; negative
`0b9b803536c12e3870eb` advances and abstains on
`aggregation-on-test-operand-path`.

## 4. H3: pure output helper with If/Return bodies

Extend `_pure_output_helper_parameter` from one expression return to this exact body grammar:

1. the unchanged sole-parameter, no-default, no-decorator parameter gate passes;
2. after docstrings are excluded, every top-level statement is `ast.If` or `ast.Return`, the last
   top-level statement is `ast.Return`, and every `Return` has a value;
3. `If` bodies and `else` bodies recursively contain only `If` and valued `Return` statements;
4. the union of every `If.test` and every `Return.value` contains only the existing closed output
   expression AST classes and every loaded name is exactly the sole parameter.

A helper that reads a tracked frame or any second free name is not pure. It is not used as a sink
edge and normal helper/operand rules decide or abstain. Expected transition: positive
`b0b7a489867c081e3f39` becomes a candidate.

## 5. H4: S5 count-only carve-out

For one origin `groupby(UNIT)` only, S5 does not fire when every terminal reachable from that origin
is in this exhaustive count chain:

- `size()` or `count()`;
- followed by zero or more of `unique()` and `tolist()`;
- with no other reducer or value-column reduction in the same origin's reachable chain.

Any coexistence of `mean`, `median`, `sum`, `std`, `var`, `min`, `max`, `first`, `last`, `agg`,
`aggregate`, `apply`, `transform`, or `value_counts`, including a sibling chain from the same
`groupby(UNIT)` or `drop_duplicates(UNIT)` origin,
fires S5. `drop_duplicates` and loop/dict unit summaries are unchanged. This is a recall carve-out for
printing row counts only; it does not change either test operand. Expected candidates:
`71939b3441556e9e02b6` and envelope-8 positive `a419e5de6ca67cd08773`. The near miss
`groupby(UNIT).size()` plus `groupby(UNIT)[VALUE].mean()` must abstain on S5.

## 6. H5: positional destructuring of an inlined helper return

When X4 inlining produces `TARGET_TUPLE = RETURN_TUPLE`, bind members positionally only if both are
literal `ast.Tuple` nodes of identical length from 1 through 16, every target member is a distinct
plain `Name`, and neither tuple contains a starred member. Each right-hand member is evaluated under
the unchanged value/member/test-result rules and assigned to the matching fresh target. A test
result member remains test-derived and a selection member remains reader-derived. Every other
destructuring form abstains under the existing code.

This cannot create operand identity: it only preserves edges already present in the inlined return.
It does not add a destructured assignment to the p-result sink closure. Therefore
`367e084ddc8f997786f1` advances past tuple value binding and then abstains on the unchanged
`test-result-output-sink-unavailable` rule; it is not counted among the four new candidates.

## 7. H6: contract-domain loop from observed levels

In addition to the 3.0 literal/closed tuple forms, an exact two-value loop may unroll when its iterable
is one of:

- `FRAME[GROUP].unique()`;
- `set(FRAME[GROUP])`; or
- `sorted(FRAME[GROUP].unique())`.

`FRAME` must be the single authorized reader value or an identity alias, `GROUP` must byte-equal the
contract group column, calls must use the exact arities above with unshadowed `set`/`sorted`, and the
CSV group-domain fact must equal the contract's two-value domain. The two bindings are the contract
values in the statically resolved iterable order; for unordered `set`, use contract order. A CSV
domain mismatch, any additional value, any missing value, or an unrecognized frame abstains rather
than unrolling. Loop-target alias, reconstruction, aggregation, mutation, and test guards run after
unrolling exactly as in 3.0. `34b1ade6d028cfda2a75` advances but remains a documented development
miss under unchanged downstream bounds; it is not counted among the four new candidates.

## 8. H7: report-buffer output sink (code structure only)

Despite the historical name, this rule does not read a report. A buffer is recognized only when:

1. `LINES = []` is a unique local definition;
2. subsequent stores to it are calls of exact shape `LINES.append(EXPR)` with one positional argument
   and no keywords;
3. an exact `"\n".join(LINES)` call, with one argument and no keywords, reaches a registered print
   sink, either directly or as the returned value of an H3-pure output helper invoked inside that
   print argument; and
4. p-result member-edge closure reaches at least one appended `EXPR`.

Any reassignment, mutation other than exact append, unresolved alias, nonliteral join separator,
second append receiver, or helper outside H3 does not establish the sink. It abstains through the
unchanged output-sink rule. The buffer is only a p-result sink edge and supplies no scientific fact.
For `19d0834b0899d12792f3`, H1 and H7 advance the analysis, after which the value-column
`groupby("clinic_site").agg(...)` reaches output and S5 returns
`unit-level-summary-sibling-present`.

## 9. Ordered predicate and unchanged guards

The 3.0 order remains normative: CSV gate; source envelope; helper/loop normalization; reader census;
S4 census; guards S1-S5 with their established precedence; operand identity and non-reduction;
row-completeness; output sink; bounds; evaluation candidate. H1 changes only the local CSV predicate.
H2, H5, and H6 preserve AST edges before guards. H3 and H7 add only output edges. H4 narrows S5 only
for count-only unit summaries. Unknown or ambiguous shapes abstain; none is interpreted toward a
candidate.

## 10. Development expectation over all 86 opened cases

The complete inventory is six envelope-1 cases plus the 80 envelope-2-through-envelope-8 cases.
Expected aggregate: **33/39 positives are development candidates; 0/41 negatives are candidates**.
Envelope-1 remains 3/3 positives and 0/3 negatives. The 3.0 ledger's 68 cases retain their recorded
outcomes except these exact deltas:

| Case | Label | 3.1 expected first outcome |
|---|---|---|
| `0b9b803536c12e3870eb` | negative | `aggregation-on-test-operand-path` |
| `71939b3441556e9e02b6` | positive | candidate |
| `34b1ade6d028cfda2a75` | positive | `two-group-row-selection-unavailable` after observed-level-loop advancement |
| `367e084ddc8f997786f1` | positive | `test-result-output-sink-unavailable` after return-destructuring advancement |

Envelope 8 expectations are exhaustive:

| Case | Label | 3.1 expected first outcome |
|---|---|---|
| `bba60d967342fbbd2832` | positive | candidate |
| `19d0834b0899d12792f3` | positive | `unit-level-summary-sibling-present` |
| `a419e5de6ca67cd08773` | positive | candidate |
| `b0b7a489867c081e3f39` | positive | candidate |
| `3d5b5ca93c6d7eb502d2` | positive | candidate |
| `a00cb612cc7d8d45aee4` | positive | candidate |
| `d415b84d1e942c483f28` | negative | `multiple-rowwise-test-candidates` |
| `95bf6d32f231a92494c4` | negative | `no-repeated-authorized-unit` |
| `ef9e199c282b9038e4c3` | negative family C | `dependence-aware-sibling-present` |
| `40496ca2298519b8825d` | negative | `additional-accepted-reader-present` |
| `d40847316a2fcdd32de3` | negative family C | `resampling-inference-sibling-present` |
| `472f5d15184e7ee55bb2` | negative | `multiple-rowwise-test-candidates` |

The six K locks remain scored development abstentions: four t-test K cases
`analysis-source-envelope-unavailable`; two binomial K controls
`authorized-group-domain-not-exactly-two`. Qualified-lane findings remain exactly the four installed
envelope-5 findings and are not affected by the 3.1 development identity.

## 11. Test plan

1. Pin H1 with the full CSV boundary matrix, `19d0834b0899d12792f3`, and the closed label-collision
   control; assert the shared/report parser and every 3.0 source byte remain unchanged.
2. H2 positive and negative lambda probes, including a lambda capturing a tracked frame and the
   `0b9b803536c12e3870eb` aggregation guard.
3. H3 direct-return, nested If/Return, bare-return, second-free-name, and tracked-frame-read probes.
4. H4 count-only `size`/`count` plus optional `unique`/`tolist`, and the mandatory size-plus-mean
   near miss.
5. H5 exact tuple binding plus starred, length mismatch, duplicate target, list RHS, and test-result
   adversaries.
6. H6 each of the three exact iterable forms plus domain mismatch, extra value, wrong column, wrong
   frame, keyword, and loop-target-alias probes.
7. H7 direct print, helper-inside-print, append alias, reassignment, wrong separator, keyword, and
   non-p-derived buffer probes.
8. Extend the prose tripwire through the 3.1 CSV predicate, lambda/free-name walk, pure-output helper,
   S5 carve-out, tuple binding, loop resolution, buffer/member propagation, all S1-S5 guards,
   operand/row lineage, sink selection, and detector comparison.
9. Run all 86 opened cases and six K locks through the normal development lane; replay equality;
   qualified-lane checks for four envelope-5 Findings, 108 blind and 155 regression zero Findings;
   FA-halt; retirement count 37; full default gate; Ruff; Mypy.

No test is retired by 3.1.

## 12. File-by-file build list

| File | Change | Rough delta |
|---|---|---:|
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter_v3_1.py` | versioned 3.1 adapter and local H1 parser | +780 new-file lines |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow_v3_1.py` | versioned 3.1 dataflow with H2-H7 | +6,700 new-file lines |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v3_1.py` | development detector identity | +20 |
| `src/sc_referee/detectors/method_conflict_registry.py` | register 3.1 detector; keep 2.1 qualified | +4/-1 |
| `src/sc_referee/scientific_checks/profiles.py` | development binding/module becomes 3.1 | +15/-10 |
| `src/sc_referee/scientific_checks/integration.py` | accept exact 3.1 static-source subject | +1 |
| `src/sc_referee/resources/capability-source/detector-manifests/` and derived manifests | record immutable 3.0 plus new 3.1 identity | generated |
| `evaluation/development/pseudorep-code-slice-v3_1/DEVELOPMENT_LEDGER.json` | canonical 80-case E2-E8 ledger and K expectations | ~100 |
| `tests/test_code_csv_dependence_dataflow_v3_1.py` | H1-H7 and adversarial matrix | +500 |
| `tests/test_dependence_code_slice_development.py` | 3.1 imports, 80-case ledger, envelope 8, tripwire | ~50 changed |
| registry, capability, integration, manifest, and qualified-lane tests | pin versions/digests and prove 2.1 isolation | ~80 changed |
| `docs/implementation/ADR-0076-...md` | development-lane 3.1 amendment only | ~10 |
| `MANIFEST.sha256` | ordinary derived resource refresh after green gates | generated |

## 13. BUILD-NOTES

- H1 is implemented only in the versioned 3.1 adapter. Editing the shared/report CSV parser would
  change a qualified semantic input and is forbidden.
- H5 and H6 are coverage advances, not promised candidates. Any downstream ambiguity remains an
  abstention and the final first reasons will be recorded here after the normal-path development run.
- The 3.1 rules are post-opened-case development. A later fresh envelope is required before any
  promotion decision.
- The normal-path replay admitted 33/39 envelope-2-through-envelope-8 positives and 0/41 negatives,
  exactly matching the closed ledger. The separately retained envelope-1 replay admitted its three
  positives and no negatives; `11af5bb3f9b7e8e0b293` now stops first on the stronger full-scope
  `dependence-aware-sibling-present` guard rather than its historical mutation reason.
- H5 was implemented narrowly: positional member binding advances `367e084ddc8f997786f1`, but tuple
  destructuring was not added to the p-result sink closure, so it remains
  `test-result-output-sink-unavailable`. H6 resolves the exact observed-domain loop forms but does
  not infer the later operand selection in `34b1ade6d028cfda2a75`, which remains
  `two-group-row-selection-unavailable`.
- H7's S5 interaction is conservative: an S5 value-summary origin inside an exact closed
  report-buffer helper called from an output sink is treated as output-reaching even when the
  summary's intermediate formatting members cannot be reconstructed. This can only abstain and is
  required for `19d0834b0899d12792f3` to stop on `unit-level-summary-sibling-present`.
- No test was retired by 3.1. The default retirement inventory remains 37 withdrawn report-lane
  items.
- `tests/test_dependence_recognition_scientific_adapter.py` is a retained source in the 155-case
  regression corpus. Its 3.1 binding assertions changed its content digest, so the corpus ledger and
  execution-plan digests were mechanically refreshed. No corpus case, role, selector, expected
  applicability, assessment ceiling, or replay expectation changed; validation still reports 155
  cases and zero Findings in all direct replay cases.
- The bare `.venv` subprocess gate reproduces the previously documented environment-only editable
  import failure: `.venv/bin/python -m sc_referee.cli` cannot see `src`, while
  `PYTHONPATH=src .venv/bin/python` imports the checkout exactly. `docs/QUICKSTART.md` already records
  that workaround. The full default gate is therefore run with `PYTHONPATH=src`; no environment or
  entry-point bytes are changed by 3.1.
- Y1 narrows H6's `FRAME` resolution to the uniquely defined authorized reader name and direct
  `Name = Name` identity aliases. A filtered reader value and a locally constructed DataFrame no
  longer supply the contract-domain loop bindings; both abstain on
  `two-group-row-selection-unavailable`. The exact authorized-reader forms remain candidates. This
  closes a frame-identity leak and adds no conviction surface.
- Y2 closes S5 parity for a uniquely assigned GroupBy receiver: when `g = df.groupby(UNIT)`, both
  `g.size()` and `g[VALUE].mean()` are attributed to the same unit-summary origin, so the value
  reducer dominates the count-only carve-out and returns `unit-level-summary-sibling-present`.
- Y3 extends both prose tripwires through all seven 3.1 predicates named in test-plan item 8: the
  local CSV predicate, lambda/free-name walk, pure-output helper, S5 carve-out, tuple binding,
  observed-domain loop resolution, and output-buffer/member propagation.
