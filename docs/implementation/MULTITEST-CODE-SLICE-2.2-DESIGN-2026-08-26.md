# Multiple-testing code slice 2.2 recall-delta design — 2026-08-26

**Status:** build-ready design, Revision 0a

**Version:** detector/check/adapter `2.2.0`, development lane only

**Normative base:**
[`MULTITEST-CODE-SLICE-2.1-DESIGN-2026-08-25.md`](MULTITEST-CODE-SLICE-2.1-DESIGN-2026-08-25.md),
Revision 1a, `sha256:d468fba746b6eb741f5cc47abc6bd5e5e529ff3e63988f80ec8c3a8c208e4165`.
Unless this document names a delta, every 2.1 predicate, registry, order, reason, limit,
invariant, and test remains normative by value.

**Authoritative recall evidence:**
[`MULTITEST-RECALL-RECON-E12-2026-08-26.md`](MULTITEST-RECALL-RECON-E12-2026-08-26.md),
`sha256:a970de7ab1951ab077c8f9a3ba8b823a846dffc87be9950c8322aada9d225071`,
committed at `22ed5e2` and manifest-refreshed at `2a99497`. The complete
[`FINDINGS-PLAYBOOK.md`](FINDINGS-PLAYBOOK.md),
`sha256:9bcb66dff193956d63b37ff6dad289e6a459dc6adc16208102483939ce0f520a`,
governs the evidence and false-accusation standard.

The envelope-12 custody pins used here are:

```text
AUDIT_RESULTS.json raw bytes sha256:8a7a9f6b7a8fafab6588531952dfd2ef2882d38633fdbb6783969018abb60292
ROLE_MAP.json raw bytes      sha256:a277faf488c981ccaa4cbc85b8727e2ab5c79eb08995e2723630a145daeeb09c
analysis.py source-set       sha256:fda78bdfba5579e8748717f0d9ade95deb8475fccdc0b184f427595472316999
```

The source-set digest is SHA-256 over the sorted `sha256sum` lines for the fifteen
`cases/*/project/analysis.py` files. Prose in those projects is context only and never detector
evidence.

## 1. Decision and hard boundary

Version 2.2 adopts exactly four recon changes:

1. **D2:** normalize registered family-test calls from an unconditional subexpression into one
   analyzer-internal statement binding per proved dynamic occurrence;
2. **D3:** admit `len(X)` as the manual-correction family size only when `X` is proved to be the
   immutable contract outcome table;
3. **D5:** resolve membership decisions against one immutable, closed set of contract outcome
   headers, without ever treating the set as an ordered sequence; and
4. **D6:** run the unchanged closed terminal presentation/verdict-helper transformer a second
   time after X4 helper inlining.

D2, D3, D5, and D6 are finite value proofs. They add no API, correction method, threshold,
reader, group split, sink, evidence slot, or prose channel. D1 and D4 are withdrawn in section 10.

The following 2.1 surfaces remain unchanged by value:

- all whole-module registered-test, correction-terminal, statistics-prefix, repeated-construct,
  dynamic-execution, API-rebinding, hierarchy, and execution-prevention censuses;
- the registered test APIs and exact call-count requirement;
- recognized correction APIs, method defaults, return positions, input-determined coverage,
  correction classifications, and the exact manual-adjusted-p grammar;
- the order-12/off-grammar versus order-13/direct-threshold partition, source-text Decimal rule,
  syntax-wide A5 binding rule, raw-family `{0.05}` narrowing, and product rule;
- operand identity, group selection, and complete-row equality;
- total forward accounting of every family p-value consumer;
- extremum, export, upstream-value, family-collection, hierarchy/control, partition,
  resampling, sensitivity, dead/live branch, outcome-mutation, and statistics guards; and
- the rule that every unresolved call, transform, container, store, alias, or escape on a p slice
  abstains rather than being treated as absence of correction.

The 2.0/2.1 load-bearing guarantee therefore remains the candidate premise: the untouched global
censuses establish the closed syntactic presence facts; backward and forward slices establish
identity and total consumer accounting; and hand arithmetic that is not exactly recognized cannot
be crossed. D2 normalizes an internal graph but supplies no global census evidence. D3 proves one
integer identity. D5 answers one membership question but supplies no order. D6 recognizes only
the already-reviewed presentation/verdict forms.

## 2. Identity, contract, wording, isolation, and ADR record

### 2.1 Versioned identities

```text
check:authorized-complete-family-correction-over-code-test-battery@2.2.0
adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1@2.2.0
detector:bounded-code-csv-multiple-testing-conflict@2.2.0
method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
```

Only the development binding advances. Versions `1.0.0`, `1.1.0`, `2.0.0`, and `2.1.0` remain
registered and directly importable for historical replay. Maturity remains `question_only`,
production Finding permission remains false, and the development controller emits no Findings.

### 2.2 Contract and wording

Contract profile `1.2.0`, its group-column plus ordered outcome-family authority, validator,
canonical values, seven error categories, and historical records are byte-unchanged. D3 and D5
consume only the already-authorized ordered outcome headers; they do not create authority.

No evidence or wording slot changes. The wording identity remains byte-identical:

```text
method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v1@1.0.0
sha256:80c4bb3c0afd75b290ab02a195e5285528f982554ab46b373e63072232902259
```

Presentation text remains non-evidence. A wording v2 is neither needed nor permitted by this
delta.

### 2.3 Frozen-lane isolation and 2.1 anchors

The 1.0/1.1/2.0/2.1 MT modules, qualified pseudoreplication `3.1.0`, complete-domain lane,
GrantPins, grants, qualification records, threshold policies, metric sets, Finding objects,
wording objects, `method_conflict_grant_pins.py`, and every
`code_csv_dependence_dataflow*.py` remain byte-untouched. The 2.2 implementation is made by
versioned copies and has no private cross-version import.

The frozen 2.1 replay anchor pins:

```text
dataflow     sha256:19036239ff85ed725d82de2d447bf214bda075101e7574935f6c3465c8dc960a
adapter      sha256:e47b6a409c91675530f594375de060ee5190e8e1331c680d3c6b9384167104f8
detector     sha256:78ab2993054cc4b0ec3abb8f1905f627511aa0d66fe8bdf95de235f11bc91153
integration  sha256:9caa6f7b0743816abf9ebe51f562741d3722847697969fa243131b3af68e0317
2.1 design   sha256:d468fba746b6eb741f5cc47abc6bd5e5e529ff3e63988f80ec8c3a8c208e4165
corpus replay `adapter_replay_records_v2_1.json`
             sha256:7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502
```

The anchor imports those exact 2.1 components, never the active development binding, and replays
the historical E10, E11, E12-baseline, PROBE/NEGSIM, ladder, adversary, and 50-case corpus inputs.
Canonical 2.1 bytes must remain equal.

### 2.4 Required ADR-0079 amendment

The build appends a narrow 2.2 note to
`ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md`. It records:

- D2/D3/D5/D6 as the only admissions, including the untouched-tree census boundary;
- D2's simple-statement and evaluation-count invariants;
- D3's contract-table-only target;
- D5's membership-only, never-ordered semantics and module-wide immutability obligation;
- the exact off-slice `sorted(OUTCOME_SET)` presentation read as a design-time extension beyond
  the recon summary, governed like 2.1's `MASK.sum()` extension and never usable for order,
  cardinality, PSEQ, or family-position evidence;
- `analysis-scope-structure-unsupported` gaining a second 2.2 predicate for failed D5 set
  stability, with the explicit rule that 1.1, 2.0, and 2.2 uses of this string denote different
  predicates and must never be compared across detector versions;
- D6 as the same transformer invoked twice, with no grammar change and an idempotence gate;
- the covered/complete FA-3 and FA-5b outcomes as safe removals of conservative abstentions;
- D1's withdrawal and D4's measured regression from `19/25` to `16/25` corpus catches and from
  the `14/18` projected opened floor to `13/18`; and
- the lesson that presentation-helper **inlining** can manufacture correction/decision evidence,
  while the closed transformer is the safe transport because it never inserts the helper's
  numeric body into the p slice.

The ADR note does not retroactively alter 2.0 or 2.1 meaning.

## 3. Pipeline and common structural terms

Let `T0` be the bounded AST parsed from the untouched `analysis.py` bytes. Let `S` be the
analyzer-internal slice scope produced by the unchanged 2.1 execution-scope selection and finite
normalizers.

The 2.2 order is:

1. parse `T0`, construct the full resolver, and run **every whole-module census on the UNTOUCHED
   `T0`**;
2. select the execution scope and run the unchanged counted-loop, outcome-iteration,
   comprehension, first presentation pass, embedded-helper, and X4 machinery until registered
   calls and their dynamic outcome occurrences are finite;
3. apply D2 once to that post-X4, pre-record-expansion scope;
4. apply D6's second terminal transformer pass to the same post-X4 scope;
5. preserve the resulting occurrence map through all remaining normalizers;
6. run the unchanged destructuring, record, loop, resolver, CSV-row, and engine stages, with D3
   and D5 available only at their named queries; and
7. run the unchanged ordered guards and produce either the first closed reason or one candidate
   fact.

Generated analyzer nodes never feed back into a whole-module census, the A5 binding count, API
rebind scan, outcome-mutation scan, source size/node count, evidence quote, or source digest.
Every generated node retains its original source occurrence and family-position provenance.

Terms used below are structural:

- `CALL` is a call whose callee resolves through the unchanged registry to the one uniform
  registered family-test API.
- `P` is the registered `.pvalue` origin of one proved `CALL` and one family position.
- `N` is the exact authorized outcome-family cardinality, at least three.
- `OUTCOME_TABLE` is the exact closed table in section 5.
- `OUTCOME_SET` is the exact frozen membership oracle in section 6.
- `DISPLAY_STRING` is the unchanged nonempty, NUL-free `ast.Constant` string of at most 256 UTF-8
  bytes. Only the byte count/NUL/nonempty properties are measured; text is never interpreted.
- A **simple statement** for D2 is exactly one `ast.Assign` with one target or one
  `ast.AnnAssign` with a simple target and a non-`None` value. It is a direct element of the
  current finite statement list, not nested in `If`, `IfExp`, `While`, `For`, comprehension,
  `Try`, `With`, `Match`, handler, `else`, `finally`, lambda, generator, or Boolean
  short-circuit region.

Similarity to a production is not equivalence. A failed production follows the unchanged 2.1
abstention path; it never supplies partial evidence.

## 4. D2 — statement-level family-call normalization

### 4.1 Exact production

D2 applies only after the existing closed outcome/comprehension expansion has proved the dynamic
multiplicity of each source call and unchanged X4 expansion has exposed its registered `CALL`, but
before record/record-loop expansion can clone a nested call. For one D2 simple statement `STMT`:

For a comprehension-expanded occurrence, the post-expansion anchor is the enclosing simple
`Assign`: every admitted occurrence is eager and strictly below that `Assign`'s `EXPR`. The source
comprehension itself is not reclassified as a simple statement and no call beneath a remaining
comprehension is eligible.

```text
STMT := TARGET = EXPR
      | TARGET: CLOSED_ANNOTATION = EXPR

ELIGIBLE_CALL := a registered CALL strictly below EXPR
```

`ELIGIBLE_CALL` must satisfy all of these conditions:

1. its source occurrence has one exact multiplicity from the untouched `T0` census plus the
   unchanged closed loop/comprehension factor;
2. after finite expansion, each resulting dynamic occurrence lies in an eagerly evaluated
   expression position—never below `BoolOp`, `IfExp`, `Lambda`, `NamedExpr`, a remaining
   comprehension/generator, a default expression, or another conditional/lazy owner;
3. the simple statement contains no unresolved dynamic expansion, starred/unpacked target,
   augmented assignment, chained target, subscript/attribute target, yield/await, or control
   transfer;
4. the occurrence is not already the direct RHS of a one-target statement binding; and
5. its registered API and source occurrence are the same item already counted by the untouched
   census. D2 never discovers an additional test call.

For every eligible dynamic occurrence, in Python expression traversal order, D2 emits one fresh
analyzer-only simple-Name binding immediately before `STMT`:

```text
__sc_mt22_call_<source-position>_<occurrence> = CALL
```

and replaces only that occurrence in `EXPR` with the fresh Name. The generated name cannot collide
with a parsed binding and is not eligible for A5 or module-constant resolution. Locations on the
binding, replacement, callee, operands, and `.pvalue` projection point back to the original source
nodes; generated text is never evidence.

### 4.2 Evaluation-count and census invariants

D2 must prove a bijection:

```text
proved dynamic CALL occurrences before D2
    == generated CALL bindings after D2
    == engine family-call roots attributable to those occurrences
```

Each occurrence appears exactly once; no call is cloned, dropped, or merged. Normalization may
change the internal graph shape only. It cannot claim that analyzer-generated repetitions were
present in source. Failure to prove the bijection returns `test-battery-cardinality-unresolved`.

The whole-module registered-call count remains the count over `T0`, with the unchanged conservative
dead-branch and helper rules. In particular, the P3 comprehension's one source call retains its
proved factor of six; D2 yields six internal statement bindings, not the 24 clones formerly
created by later record expansion. The global evidence still describes the original source call
and factor.

The normalizer is never applied to a live conditional, short-circuit, exception, match, loop, or
helper body whose multiplicity has not already been closed. It supplies neither execution order
nor a new call-count proof. Other eager calls in `EXPR` remain ordinary consumers and are still
visited by the total forward slice.

### 4.3 D2 refusal outcomes

- a conditional/lazy or unresolved occurrence returns `test-battery-cardinality-unresolved` when
  it is needed to establish the family;
- a successfully bound `CALL` whose operand or p consumer is unresolved reaches the ordinary
  `test-operand-lineage-unresolved`, `pvalue-family-collection-unresolved`, or
  `unresolved-pvalue-consumer` guard; and
- any mismatch with the untouched census retains the earlier census reason.

D2 itself never converts an unresolved consumer into a recognized consumer.

## 5. D3 — exact `len(OUTCOME_TABLE)` family size

### 5.1 Closed outcome-table grammar by value

D3 extends only the existing manual-correction `exact_family_size` query. It admits:

```text
len(TABLE_NAME)
```

where `len` is the unshadowed builtin, there is exactly one positional argument and no keywords,
and `TABLE_NAME` resolves through zero or more exact Name-to-Name aliases to one immutable module
binding whose value satisfies all of:

1. the outer value is one `ast.List` or `ast.Tuple` with `1..16` rows;
2. every row is an `ast.List` or `ast.Tuple` with `1..8` elements;
3. every element is an `ast.Constant` closed scalar: `None`, `bool`, non-boolean `int`, finite
   `float`, or a nonempty/NUL-free string of at most 128 UTF-8 bytes;
4. every row has a string in position zero;
5. the position-zero values are unique and **order-equal** to the contract outcome-column tuple;
6. therefore the row count equals `N`; and
7. the existing whole-module container-stability proof establishes no mutation, alias mutation,
   rebinding, deletion, subscript/slice store, unresolved escape, or mutating method on the root or
   any alias anywhere in `T0`.

Outer and row container kinds need not match; each is merely a finite table display under the
already-installed 2.1 table grammar. D3 reads no label/unit/flag field beyond verifying that it is
a closed scalar. Only the exact first-field equality to frozen contract headers establishes table
identity.

The existing recursive Name binding remains available, so this production also accepts:

```text
K = len(TABLE_NAME)
min(1, P * K)
```

provided the unchanged reaching-definition and single-value rules resolve `K` to that exact call.

### 5.2 Deliberate non-admissions

D3 does not admit `len` of a p container, result list, set, filtered table, DataFrame, dictionary,
generator, NumPy array, runtime sequence, table slice, table comprehension, or unrelated
same-length literal. It does not admit a shadowed `len`, extra argument/keyword, `TABLE.shape`,
`TABLE.__len__()`, or arithmetic around the `len` call.

The new table clause is queried only where the 2.1 manual-correction grammar asks whether the
multiplier is the complete family size. It is not a loop-cardinality, resampling-cardinality,
allocation-size, threshold, indexing, or outcome-sequence admission. All former
`exact_family_size` productions remain unchanged.

## 6. D5 — frozen contract-outcome set as a membership oracle

### 6.1 Closed set grammar by value

An `OUTCOME_SET` is either a direct `ast.Set` display at the admitted membership comparison or one
simple Name resolving through exact Name aliases to one module-level `Assign`/closed `AnnAssign`
whose RHS is an `ast.Set`. The set must satisfy:

1. it has `1..N` elements;
2. every element is a direct, nonempty, NUL-free `ast.Constant` string of at most 128 UTF-8 bytes;
3. elements are pairwise distinct;
4. every element is byte-equal to one contract outcome column; and
5. the set may be a proper subset or the complete set, but never contains a noncontract header.

D5 admits `ast.Set` displays only. A `frozenset(...)` call, including a call whose sole argument
is an otherwise admissible List/Tuple/Set display, is not an `OUTCOME_SET` and is refused through
the unchanged unresolved-call/collection path.

For a named set, build the complete alias closure. The root and every alias must have exactly the
initial/alias binding and no other `Store` or `Del`. Refuse any `AugAssign`, subscript/slice store,
destructuring store, rebinding, deletion, or call to any of these attributes on the closure:

```text
add, update, remove, discard, pop, clear,
difference_update, intersection_update, symmetric_difference_update,
__ior__, __iand__, __ixor__, __isub__
```

Passage of the set to a user helper, receiver call, return, yield, container insertion,
attribute/subscript store, or any call not proved read-only is an unresolved escape and refuses the
oracle. One additional read is required by E12 P6 and admitted narrowly: unshadowed
`sorted(OUTCOME_SET)` with exactly one positional argument and no keyword, used wholly off the
test/correction/p/control slices as presentation payload. It proves only that the set was read, not
what order the result has; the returned list is unavailable to D5, outcome normalization, PSEQ,
family cardinality, or family-position mapping. Any on-slice load other than the right-hand
membership operand defined next refuses the oracle. A direct set display has no alias/mutation
surface.

If a named set fails this module-wide stability proof, the analyzer abstains
`analysis-scope-structure-unsupported` before membership folding. This is a proof obligation, not
a best-effort resolver: a potentially mutated set is never used to manufacture correction
coverage or strict-subset evidence.

### 6.2 Membership decision only

D5 answers only this exact comparison:

```text
OUTCOME in OUTCOME_SET
OUTCOME not in OUTCOME_SET
```

The `ast.Compare` has exactly one `ast.In` or `ast.NotIn` operator and one comparator. `OUTCOME`
is the direct loop/table field that the unchanged outcome expansion has already replaced with one
exact contract-header `ast.Constant`. The comparison must be the whole test of one `ast.If` being
folded during that closed expansion; no `BoolOp`, chained comparison, `IfExp`, comprehension
filter, `assert`, `match`, or standalone scientific gate is admitted by D5.

The evaluator performs exact byte membership, applies the `not in` polarity if present, and keeps
only the selected branch for that already-proved outcome occurrence. This allows the existing
manual-correction and raw-conclusion slices to map P6's corrected positions `{0,1}` and raw
positions `{2,3,4}`.

The set is **never** returned through `resolver.sequence`, `resolver.table`, PSEQ, iteration,
`zip`, `enumerate`, `list`, `tuple`, indexing, family cardinality, or family-position mapping.
The one off-slice `sorted` presentation read in 6.1 likewise returns no analyzable sequence. D5 is
a membership oracle, not an ordering or iteration source. Set iteration remains unresolved even
when the members happen to equal the contract family.

## 7. D6 — repeat the identical terminal-helper transformer

### 7.1 One transformer, two calls, no grammar change

Let `TPH` be the installed 2.1 closed terminal presentation/verdict-helper transformer. Version
2.2 does not fork, wrap, broaden, or special-case `TPH`. The pipeline calls the same implementation
twice:

```text
S1 = TPH(S0)                  # existing pre-X4 pass
S2 = unchanged helper/X4 expansion(S1)
S3 = TPH(S2)                  # D6 post-X4 pass
```

The second invocation uses the same helper registry, resolver rules, display limits, origin tags,
and productions as the first. It exists because X4 can expose a helper call that was not present
in `S0`; it does not authorize a new helper shape.

### 7.2 `TPH` grammar restated by value

For a simple-name call `H(A)` with exactly one positional actual and no keyword, `H` must resolve
to the same unique top-level helper used by 2.1. After an optional docstring, `TPH` recognizes only
these installed productions:

1. **Pure p presentation:** one required positional formal, no positional-only/keyword-only,
   default, variadic, decorator, recursion, closure, nested definition, `global`, or `nonlocal`;
   body exactly `Return R`; and `R` is `str(formal)`, an f-string whose tracked formatted values
   are direct formal loads, `DISPLAY_STRING % formal` (or a List/Tuple payload of only the
   formal), `DISPLAY_STRING.format(formal, ...)` with only direct formal positional payloads, or
   an `IfExp` whose test directly compares the formal with one bare finite numeric display cutoff,
   whose arms are presentation strings/p-format forms, and with at least one p-formatting arm.
2. **Constant verdict `IfExp`:** body exactly one `Return IfExp`; its two arms are
   `DISPLAY_STRING`; its loads are the formal plus closed resolver numeric literals; and the
   formal occurs. `TPH` substitutes `A` into the test and marks the result as terminal rendering.
   The decision still passes the unchanged order-13 threshold grammar and product rule.
3. **Optional p display `IfExp`:** body exactly one `Return IfExp`; its test is a direct
   comparison, one arm is a `DISPLAY_STRING`, the other is an f-string containing a direct formal
   formatted value, and no load lies outside the formal plus closed resolver numeric literals.
   It becomes the same tagged p-presentation value as in 2.1.
4. **Two-return p display:** after the optional docstring, body is exactly an `If` with no `else`
   whose sole body statement is `Return`, followed by one `Return`; both return values are only
   `DISPLAY_STRING`/f-string shapes, every Name load in them is the formal, and at least one arm is
   an f-string. It becomes the same tagged p-presentation value.
5. **Two-return constant verdict:** the same two-statement `If`/`Return` plus final `Return`
   shape, with exactly two `DISPLAY_STRING` return values; the helper has exactly one required
   positional formal and no positional-only, keyword-only, default, or variadic parameters.
   `TPH` substitutes `A` into the `If.test` and marks the resulting `IfExp` as terminal rendering;
   the decision remains subject to order 13.

For every production, the call result must still reach only the unchanged total presentation and
registered-sink transports. A numeric/correction call, arithmetic return, boolean/number/container
return, multiple/alternate return outside production 4/5, extra statement, unresolved free Name,
second consumer, store/escape, or nonpresentation consumer is not transformed and follows the
ordinary guard.

This restatement is an inventory of the existing 2.1 transformer, not a new acceptance registry.
If implementation comparison finds that a proposed second-pass production is absent from the
frozen 2.1 `TPH`, the build stops instead of adding it.

### 7.3 Ordering and idempotence obligations

The post-X4 pass occurs after the unchanged helper expansion has exposed nested terminal helper
calls and before final record/loop expansion and `_MtEngine` construction. The resolver is rebuilt
over the current setup plus transformed scope using the unchanged resolver. No pass sees or alters
`T0`.

For every accepted and refused fixture:

```text
canonical_ast(TPH(TPH(S))) == canonical_ast(TPH(S))
```

where `canonical_ast` includes node kinds, fields, constants, source locations, and the two
terminal/presentation provenance markers, but excludes object identity. Running the full D6 stage
again on already-rewritten scope must also leave family-position origins and consumer edges equal.
Failure is a stop-and-report ordering regression.

## 8. False-accusation analysis and six required fixtures

Every fixture below is a correct analysis executed through the public 2.2 analyzer and adapter.
The names are normative. A `covered/complete` result means zero candidate and zero Finding with
recognized correction coverage equal to all `N` family positions. That is stronger and more useful
than an incidental abstention.

| Recon fixture | Strongest correct-analysis shape | Exact expected outcome | Why 2.2 cannot accuse |
|---|---|---|---|
| `FA-2` / `FA-2-conditional-subexpression-family-call` | An otherwise complete family places one registered test in a lazy `IfExp` branch whose test is a closed literal selector, so no earlier scientific hierarchy guard owns it. | Abstain `test-battery-cardinality-unresolved`; zero candidate/Finding. | D2 requires an eager simple-statement occurrence and a call-count bijection. It neither hoists nor treats the conditional call as an established execution. |
| `FA-3` / `FA-3-complete-hand-bonferroni-len-contract-table` | Every one of `N` raw p-values is transformed by `min(1, P * len(OUTCOMES))`, and every conclusion uses the transformed p. | **Covered/complete**, positions `{0..N-1}`; zero candidate/Finding. | D3 proves `len(OUTCOMES)==N`; the unchanged manual Bonferroni grammar maps every origin, so strict-subset/none conflict is impossible. Removal of the former abstention is the intended safe feature. E12 N2/N4/N9 remain protected neighboring family-size/correction shapes. |
| `FA-5a` / `FA-5a-mutated-contract-outcome-set` | A hand-corrected subset is selected by a set initially containing contract headers, then an alias is conditionally `.add()`ed before use. | Abstain `analysis-scope-structure-unsupported`; zero candidate/Finding. | D5's module-wide alias/mutation census refuses the oracle before branch folding. No partial subset map is retained. A separate escape sibling passes the alias to a user helper and has the same exact reason. |
| `FA-5b` / `FA-5b-complete-hand-bonferroni-frozen-set` | A frozen set contains all `N` contract outcomes; membership selects `min(1, P*N)` for every member and all decisions use that p. | **Covered/complete**, positions `{0..N-1}`; zero candidate/Finding. | D5 answers membership but never supplies order. The already-proved loop/table position supplies identity; unchanged manual correction proves complete coverage. Removing an incidental abstention on this correct analysis is the intended safe feature. |
| `FA-6a` / `FA-6a-nested-presentation-plus-unresolved-adjuster` | X4 exposes a nested one-argument display helper, but its actual is returned by an unrecognized adjustment helper. | Abstain `unresolved-pvalue-consumer`; zero candidate/Finding. | The second pass transforms only the outer presentation. Total consumer accounting still reaches the unrecognized call; D6 cannot bless or delete it. |
| `FA-6b` / `FA-6b-nested-presentation-plus-computed-threshold` | X4 exposes nested formatting around a p-value whose scientific verdict directly uses a computed Sidak threshold. | Abstain `unresolved-decision-threshold`; zero candidate/Finding. | `TPH` does not inline or erase numeric structure. The direct comparison stays at order 13. A separate off-grammar p-arithmetic sibling remains `unresolved-manual-correction-present` at order 12. |

Every fixture has one exact first reason or one exact covered/complete classification. Sibling
fixtures are separate rows and no assertion is disjunctive.

Existing correct-analysis neighbors remain pinned: E12 N1/N3 exercise p-bearing record and nested
presentation surfaces; N2 exercises `len(DECLARED_OUTCOMES)` beside correct Sidak arithmetic; N4
uses complete hand Holm; and N9 uses the pre-registered corrected threshold. None is admitted as a
candidate. No opened correct case uses D5's exact correction-membership set, so FA-5a/FA-5b are the
required direct polarity pair rather than substituting a merely similar corpus case.

The following cross-rule adversaries are also required:

- `correct-d2-eager-call-with-unresolved-sibling-consumer`: D2 binds the test exactly once, then
  total forward accounting abstains `unresolved-pvalue-consumer`;
- `correct-d3-unrelated-same-length-table`: `len(OTHER)` is refused and the hand-correction path
  abstains `unresolved-manual-correction-present`;
- `correct-d5-full-set-iteration`: iterating the complete set, directly or through a `sorted`
  result on the family slice, never supplies family order and abstains
  `test-battery-cardinality-unresolved`;
- `correct-d5-proper-subset-plus-correction-outside-set`: the complete correction census/consumer
  mapping wins; D5 cannot manufacture raw uncovered positions;
- `correct-d6-second-consumer-export`: a transformed display plus `.to_csv`/`numpy.savetxt`/
  `json.dump` p flow remains `unresolved-pvalue-consumer`; and
- `correct-d6-verdict-product-rule-N5`: a nested two-string verdict at literal `0.01` with `N=5`
  remains `unresolved-decision-threshold` using source-text Decimal.

All 2.0 section-7 and 2.1 section-5 adversaries retain their exact noncandidate/candidate outcomes.
In particular, default-method complete correction, hand Sidak/Holm/Bonferroni, off-registry
correction, sensitivity duplicate, discovery/validation split, all-NumPy assert/match/
short-circuit and early-exit gates, label-permutation maxT, extremum, export, upstream p,
partition, resampling, outcome mutation, dynamic p container, and N=4 bare `0.01` do not weaken.

## 9. Ordered integration and closed reasons

### 9.1 Ordered predicate changes

The 2.1 first-reason order remains. The four insertions are:

| Existing order | 2.2 operation | Failure path |
|---:|---|---|
| global census / family normalization | D2 normalizes only after the untouched call census and finite multiplicity proof | `test-battery-cardinality-unresolved`; existing census reasons |
| forward family/correction reconstruction | D3 answers the exact family-size operand in the existing manual correction grammar | `unresolved-manual-correction-present`; `correction-family-lineage-unresolved` |
| forward branch/position reconstruction | D5 folds one exact outcome-membership `If`; position still comes from the ordered outcome loop/table | `analysis-scope-structure-unsupported`; existing hierarchy/collection reasons |
| pre-engine presentation normalization | D6 repeats `TPH` after X4; grammar and order-12/13 treatment unchanged | `unresolved-pvalue-consumer`; manual/threshold/hierarchy reasons |

D2 does not affect the global call-count order. D3 does not make arithmetic thresholds bare. D5
does not create PSEQ or cardinality. D6 does not turn presentation into scientific correction or
conclusion evidence. Direct-P comparisons remain exclusive to order 13.

### 9.2 Guard ownership

| Guard | Trigger source in 2.2 | Delta effect |
|---|---|---|
| Registered tests, sensitivity, dead/live branches | Untouched `T0` census plus existing conservative multiplicity | D2 contributes no syntactic count; its bijection checks the already-proved count. |
| Correction/statistics/repeated/dynamic/API rebind | Untouched `T0` | No effect. |
| Outcome mutation | Untouched tree plus existing alias closure | D3 reuses it; D5 adds its own stricter set closure. |
| Operand and row completeness | Backward slices | No effect. |
| Family collection and total p consumers | Forward slices over normalized scope, mapped to source | D2 exposes a root; D6 exposes presentation only. Unresolved edges still abstain. |
| Manual correction and threshold | Forward slice plus untouched source bindings | D3 proves only `N`; D5 selects a branch. Arithmetic grammar unchanged. |
| Hierarchy/control/prevention | Whole module plus slice provenance | D5 excludes only a membership `If` after exact per-outcome fold; all other controls remain. D6 exclusions are exactly those already installed in 2.1. |
| Conclusions | Forward slice | No new conclusion grammar. D2 preserves origin; D5 preserves the ordered loop position; D6 preserves existing tags. |

### 9.3 Closed reason set

No reason is added, removed, retired, or relabeled. The 2.2 set is exactly:

```text
verified-contract-authority-unavailable
authorized-test-family-shape-unsupported
authorized-family-cardinality-below-three
frozen-authority-material-mismatch
authorized-family-csv-domain-unavailable
authorized-group-domain-not-exactly-two
analysis-source-envelope-unavailable
alternate-analysis-file-present
statistics-api-imported-outside-analysis-py
api-resolution-ambiguous
analysis-scope-structure-unsupported
dataflow-definition-ceiling-exceeded
helper-callee-not-simple-name
helper-definition-unavailable-or-nonunique
helper-parameter-shape-unsupported
helper-parameter-default-unsupported
helper-variadic-parameter-unsupported
helper-argument-binding-unsupported
helper-recursion-unsupported
helper-return-count-unsupported
helper-return-position-unsupported
helper-return-expression-unsupported
helper-global-nonlocal-unsupported
helper-closure-or-nested-definition-unsupported
helper-async-decorator-or-yield-unsupported
helper-body-statement-unsupported
helper-free-name-unbound
helper-inlining-depth-exceeded
helper-call-site-reentry-unsupported
additional-accepted-reader-present
authorized-reader-lineage-unavailable
test-battery-cardinality-unresolved
authorized-family-test-census-incomplete
extra-registered-test-outside-authorized-family
mixed-test-api-family
test-operand-lineage-unresolved
selected-group-row-completeness-unproven
upstream-correction-lineage-unresolved
pvalue-family-collection-unresolved
unresolved-pvalue-consumer
family-pvalue-extremum-reduction-present
correction-family-lineage-unresolved
unresolved-manual-correction-present
pvalue-scalar-cast-or-rounding-unsupported
unresolved-decision-threshold
hierarchical-gatekeeping-present
pvalue-control-dependence-unresolved
multiple-family-partition-present
resampling-cardinality-unresolved
permutation-family-control-present
unresolved-inference-sibling-present
pderived-conclusion-family-incomplete
conclusion-output-sink-unavailable
multiple-testing-code-inspection-exception
```

The documented-unreachable annex for `conclusion-output-sink-unavailable` remains unchanged.
Public-analyzer emitter fixtures plus that annex are set-equal to the adapter closed set. A reason
literal in a 2.1 test cannot satisfy 2.2 coverage.

## 10. Considered and rejected

### 10.1 D1 — DataFrame p-table admission withdrawn

D1 attempted to admit p-bearing `pandas.DataFrame` construction/transport. The executed ladder
moved no projected case. More importantly, a positional DataFrame record model would have to
prove column identity, row order, mutation, filtering, assignment, iteration, and export semantics
before a strict-subset accusation. That is the largest remaining accusation surface, not a small
transport edge. D1 is withdrawn, and any family p-value entering `pandas.DataFrame` retains
`unresolved-pvalue-consumer`.

### 10.2 D4 — presentation-helper inlining withdrawn

D4 inlined presentation helper bodies into the scientific value graph. Execution showed a recall
regression: corpus catches fell from `19/25` to `16/25`, and the projected opened floor fell from
`14/18` to `13/18`. Inlining manufactured numeric comparison/correction evidence from code whose
only role was rendering. Those new nodes then triggered guards that the original p flow did not
justify.

D4 is rejected. No presentation helper body is generally X4-inlined for p evidence. D6 is the safe
equivalent: the existing closed transformer recognizes a finite presentation/verdict shape and
replaces it with the same tagged transport, without inserting its numeric implementation into the
p slice. These withdrawal facts and measurements are recorded in the ADR amendment.

### 10.3 No other policy movement

The standing declined `P < ALPHA / K` manual-Bonferroni coverage policy remains declined pending a
future ADR. D2/D3/D5/D6 do not alter that decision.

## 11. Adapter-level oracles

### 11.1 Envelope 12 — normative fifteen-row table

The 2.2 adapter executes each project through its committed `profile_1_2_0.json`. The exact oracle
is:

| Role / case | 2.2 adapter outcome | Exact reason/classification |
|---|---|---|
| P1 `f9ce4de5e21d9015ecd9` | abstain | `unresolved-pvalue-consumer` |
| P2 `e07a6f2a895079b53b8c` | candidate | `none` |
| P3 `e28a9537b07c74d21838` | candidate | `none` |
| P4 `0ec89f70a9776d1a1931` | candidate | `none` |
| P5 `54667dd7c39067c8c2c8` | abstain | `pvalue-family-collection-unresolved` |
| P6 `68d1a6f5b1ab70f2650a` | candidate | `strict_subset`, corrected positions `{0,1}` of `5` |
| N1 `45c4b9a19d0a630f1cb0` | abstain | `unresolved-pvalue-consumer` |
| N2 `f256af2f5c5d98f37e65` | abstain | `unresolved-pvalue-consumer` |
| N3 `678e94e79226936fd647` | abstain | `unresolved-manual-correction-present` |
| N4 `c37c0fa6e462a22cb6d5` | abstain | `authorized-family-test-census-incomplete` |
| N5 `6108263527580cd01608` | abstain | `test-battery-cardinality-unresolved` |
| N6 `db193771248850b81b25` | abstain | `test-battery-cardinality-unresolved` |
| N7 `190ca375ac7c481c3e08` | abstain | `authorized-family-test-census-incomplete` |
| N8 `7fd5f9dcd4097c1e5a03` | abstain | `authorized-family-test-census-incomplete` |
| N9 `62aa3748aa0c7c2607d3` | abstain | `test-battery-cardinality-unresolved` |

Exactly three of the 45 opened E10-E12 rows move relative to the committed 2.1 oracles:

1. P3: `test-battery-cardinality-unresolved` -> candidate/`none` by D2;
2. P5: `unresolved-pvalue-consumer` -> `pvalue-family-collection-unresolved` because D6 clears
   only the nested rendering wall and exposes the deeper retained positional-record wall; and
3. P6: `unresolved-manual-correction-present` -> candidate/`strict_subset {0,1}/5` because D3
   proves the multiplier and D5 proves membership positions.

P1's D6 presentation movement remains hidden behind its independent DataFrame p-table consumer,
so its first reason does not move. No negative outcome or first reason moves. The adapter writes a
checked-in 2.2 E12 replay record and replays it twice byte-identically.

### 11.2 Open corpus — all fifty rows frozen

The committed open corpus remains 50 cases, 25 labeled correct and 25 labeled misstep:

```text
root                evaluation/development/multitest-open-corpus-v1/
labels raw bytes    sha256:f9d2d33ba3b8247b0d0d65e5f72f765af02bfca6dc932f895010d79129f36f80
analysis source set sha256:7888b72a6ac1ec70830d4041517a977b8ea8ff6c4294a7d13a734ab9af377a2e
2.1 replay bytes    sha256:7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502
```

At adapter level, every 2.2 per-case replay row—canonical outcome plus exact reason or correction
classification/positions—is byte-identical to the corresponding entry under
`"2.1.0".results` in the frozen 2.1 file. The wrapper's adapter identity is not compared across
versions. The frozen 2.1 file is not regenerated or rewritten, and a redundant re-baseline is not
created.

Required score:

```text
labeled correct candidates:  0 / 25 (hard stop)
labeled misstep candidates: 19 / 25 (unchanged)
```

The three admitted changes are structural holes sampled by fresh E12 authors, not a gain on the
unbiased open-corpus estimate.

### 11.3 Historical opened oracles

- All thirty E10/E11 adapter rows retain their exact 2.1 outcomes, classifications, and first
  reasons, including E10 N7's adapter-only outside-file statistics reason.
- The twelve PROBE baselines and `NEGSIM_C` remain candidate/`none`; `PROBE_roundp`, `NEGSIM_A`,
  and `NEGSIM_B` retain their exact reasons.
- E10 P2/P3 mutation ladders, all corpus20 ladders, the 32 2.0 adversaries, every 2.1 admission/
  refusal fixture, the R12/R15/R5/R3b/R16 adversaries, and all historical contract/detector guards
  retain their exact outcomes.
- The four prior frozen version anchors remain green. Tests keep explicit old-version imports and
  are copied for 2.2 rather than retargeted.

No existing correct analysis may move from abstention/covered to candidate. FA-3 and FA-5b are new
isolated correct fixtures whose movement from conservative abstention to covered/complete is
explicitly expected and safe.

## 12. Residuals

### 12.1 DataFrame p-table value model

P1 still sends family p-values into `pandas.DataFrame`, the same guard protecting E12 N1/N2. A
future design must define positional record-table construction, column/member identity, row order,
copy/alias mutation, column assignment, filtering, iteration APIs, and total export consumers. An
incorrect model can turn a filtered or adjusted table into fake raw complete-family evidence, so
this is a standalone accusation-surface review. Until then, entry into a DataFrame abstains
`unresolved-pvalue-consumer`.

### 12.2 Positional-record subset before strict subset

P5 filters a positional record list before selecting corrected members. The detector may not infer
which contract positions survive a runtime filter. A future positional-record subset model must
slice-prove identity and order before any `strict_subset` conviction. Until then,
`pvalue-family-collection-unresolved`/`correction-family-lineage-unresolved` is correct.

### 12.3 Dominated record-flag fold

P5's unfolded record-flag branch is dominated by the missing positional subset model. It is bundled
with section 12.2 rather than admitted independently; folding the flag alone would expose no safe
position proof.

### 12.4 Zip write-back dual polarity

`zip(record_list, adjusted)` write-back appears in both correct complete-correction and misstep
partial-correction shapes. Any future admission must measure and gate both polarities together.
Recognizing the transport without record identity would enlarge the strict-subset accusation
surface and is forbidden here.

## 13. Executable validation plan

Every fixture executes the public analyzer or adapter. AST/private-helper assertions supplement
but never replace public-path execution.

### 13.1 D2 matrix and ladder

Execute and pin:

- direct statement-bound calls (unchanged control);
- one and multiple calls nested in eager List/Tuple/Dict fields after exact outcome expansion;
- P3's record-comprehension occurrence with a `1 -> 6 -> 6`, never `24`, census/expansion/binding
  count assertion;
- Assign and closed AnnAssign; direct RHS (no rewrite); annotation/target near misses;
- `IfExp`, `BoolOp`, remaining list/set/dict/generator comprehension, lambda, NamedExpr, await,
  yield, Try, conditional body, loop, chained/attribute/subscript/starred/AugAssign refusals;
- unresolved/dynamic multiplicity and a census mismatch;
- a normalized call whose p reaches an unresolved outer call; and
- evidence spans/digests proving generated bindings never appear as source statements.

The D2 transformer has a structural idempotence test even though it is invoked only once: applying
it again to already-bound direct RHS calls produces the same canonical scope.

### 13.2 D3 matrix

Cross:

- List and Tuple outer tables; List and Tuple rows independently;
- direct table Name, exact aliases, and `K = len(TABLE)`;
- every admitted scalar type and bounds `16` rows/`8` fields, plus `17`/`9` refusals;
- wrong order, duplicate/missing/extra/noncontract first fields; empty/NUL/129-byte/nonfinite/
  complex/dynamic cells;
- unrelated same-length sequence/table, p/result containers, set, dictionary, DataFrame, filtered
  table, slice, comprehension, direct literal, shadowed `len`, keywords, and arithmetic;
- root/alias mutation, rebinding, deletion, store, and unresolved escape; and
- partial and complete manual correction, with FA-3 pinned covered/complete.

Assert D3 cannot be called as a loop, resampling, allocation, index, or threshold cardinality
oracle.

### 13.3 D5 matrix

Cross:

- direct and Name-bound set, aliases, one-member/proper-subset/complete sets;
- exact `in` and `not in` polarity for every family position;
- duplicate, empty, extra/noncontract, dynamic/Name element, NUL, and 129-byte refusals;
- every named mutator, Store/Del/AugAssign, alias mutation, and unresolved escape;
- chained comparisons, BoolOp, IfExp, comprehension, assert/match, non-outcome subject, and dynamic
  subject refusal;
- attempted family iteration through `for`, `sorted`, `list`, `tuple`, `zip`, `enumerate`,
  indexing, and `len`, none of which receives D5 order/cardinality; plus the exact P6 off-slice
  `sorted(set)` presentation read as a non-evidentiary accepted control;
- proper-subset manual correction yielding P6's exact `{0,1}/5`; and
- FA-5a abstention and FA-5b covered/complete.

An independent test asserts the D5 oracle is absent from every resolver sequence/table method.

### 13.4 D6 matrix and idempotence

Run every `TPH` production in section 7 through both placements: directly visible before X4 and
revealed only after X4. Cross all installed parameter, body, return, arm, display-bound, sink-only,
threshold, second-consumer, numeric-call/arithmetic, and unresolved-free-name refusals. Assert:

- pass one and pass two call the same classifier object/production table;
- no production exists in 2.2 that is absent from frozen 2.1 `TPH`;
- one pass after X4 produces the same canonical AST as two passes after X4;
- origin, family position, source location, consumer set, and first reason are stable after the
  second idempotence invocation;
- P1's nested helper clears while its DataFrame wall remains;
- P5 moves exactly one wall deeper; and
- FA-6a/FA-6b plus the export/product-rule adversaries retain their pinned abstentions.

### 13.5 Recon ladders and prototype condition

Check in the recon's per-wall ladder rungs under
`evaluation/development/multitest-code-slice-v2_2/e12-ladders/` with a canonical manifest containing
relative path, raw SHA-256, source case/role, one changed construct, expected analyzer and adapter
outcome, exact first reason/classification, and position set where applicable.

Required ladders are:

- P1: nested helper and DataFrame walls independently and jointly varied; D6 alone retains the
  DataFrame abstention, while the direct no-DataFrame known-positive control is a candidate;
- P3: original subexpression call, exact statement-bound control, D2-normalized projection, and
  every lazy/conditional refusal;
- P5: nested formatting helper -> record flag -> positional subset, showing D6 reaches but does
  not cross `pvalue-family-collection-unresolved`; and
- P6: `len(OUTCOMES)` and frozen-set membership varied independently, with only the joint admitted
  rung producing `strict_subset {0,1}/5`.

The recon records executed prototypes but its committed change contains no runnable prototype
artifact. Therefore the conditional prototype-versus-final gate is inactive at repository state
`2a99497`; fixtures and adapter oracles above are normative. If the custodian supplies the original
prototype files before build, their raw digests are pinned and each applicable node/outcome is
compared extensionally with the final D2/D3/D5/D6 classifier. A newly recreated implementation is
not represented as the frozen recon prototype.

### 13.6 Adapter replay gates

1. Execute the exact E12 table in 11.1 twice and byte-gate a checked-in 2.2 record.
2. Execute all 50 corpus cases at adapter level and compare every canonical result row byte-for-byte
   with frozen 2.1 `results`; assert `0/25` correct and `19/25` misstep candidates.
3. Execute the 30 E10/E11 adapter oracle and compare exact prior outcomes/reasons.
4. Execute the 2.1 adapter explicitly over all historical inputs and compare the frozen anchor
   bytes/digests in 2.3.
5. Retain analyzer-level pins as diagnostics; they cannot replace an adapter gate.

### 13.7 Prose tripwire and structural controls

Extend the 2.1 tripwire over every new predicate, ladder rung, and FA fixture. Independently mutate
comments, docstrings, reports, Markdown, task text, annotations, unrelated strings, display labels,
format strings, and non-callee identifiers; add/remove report and Markdown files; rename
non-callee identifiers through `bonferroni`, `holm`, `sidak`, and
`benjamini_hochberg`. Facts, reason, classification, positions, and evidence bytes remain equal.

Specific boundaries:

- D2 reads AST node kinds, API identity, source occurrence, and multiplicity only;
- D3 reads table cells only to enforce the closed scalar grammar and exact first-field equality to
  contract outcome bytes; label/unit/flag semantics are never inferred;
- D5's set strings are structural membership keys only. The detector reads them solely for exact
  equality with the contract column names; it never tokenizes, interprets, orders, or emits their
  text; and
- D6 measures presentation strings only for nonempty/NUL/256-byte bounds. Preserve shape while
  replacing every presentation byte to prove the result is unchanged.

Paired positive controls each change one structural slot: eager D2 occurrence -> `IfExp`; contract
table -> unrelated same-length table; exact set member -> noncontract member; immutable set ->
alias `.add`; membership -> iteration; post-X4 `TPH` call -> numeric helper; one sink consumer ->
export; 256 -> 257 display bytes. Each must change its named predicate. Deleting the registered
callee or contract-header literal from a positive control changes the result.

### 13.8 Closed set, differential, and repository gates

- Public 2.2 emitters plus the documented-unreachable annex are set-equal to section 9.3; every
  non-X4 reason has an exact public fixture and X4 reasons retain the parametrized module.
- Explicit frozen 1.0/1.1/2.0/2.1 anchors execute; no test is retargeted.
- Dual-registry differential proves qualified GrantPins, grants, qualifications, metric sets,
  threshold references, and Findings are byte-equal and do not derive from the development
  lane-inclusive digest.
- Contract `1.0.0`/`1.1.0` goldens, all seven error categories, deterministic corpus/source
  censuses, registry digests, and frozen replay records remain exact.
- Registry resources and capability ledger are regenerated after the final source/test/artifact
  change. `MANIFEST.sha256` follows the repository custodian's committed-tree procedure.
- Run fresh `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, and
  `python scripts/validate_starter.py`; report exact unfiltered outputs and never claim a change
  absent from the diff.

## 14. Evidence projection and candidate meaning

Facts, observation schemas, canonical operands, evidence roles, and wording slots are unchanged.
D2 evidence cites the original registered call and operand spans, not the generated binding. D3
cites the original `len` expression and exact table binding only as family-size lineage. D5 cites
the membership comparison and exact set binding only as correction-position lineage. D6 cites the
original helper call/sink span and preserves the existing presentation/terminal tags; display text
is not copied as scientific evidence.

A 2.2 candidate still asserts only that the authorized complete family has exactly `N` proved
registered tests and raw conclusions outside complete recognized correction coverage. Absence of a
recognized correction in analyzed source does not establish that no correction was applied. The
detector does not infer correction, preregistration, importance, or meaning from names, reports,
labels, flags, display strings, or set membership labels beyond their exact contract-column
identity.

## 15. Expected score and envelope 13 posture

The honest development expectations are:

```text
open corpus correct:     0 / 25 candidates (hard gate)
open corpus misstep:    19 / 25 candidates (unchanged)
opened E10-E12 floor:   14 / 18 positives (answer-visible regression floor)
blind first contact:     2 / 18 positives (E10-E12; unchanged forever)
blind negatives:         0 candidates in all available class cases (hard gate)
```

The delta gains zero on the unbiased open-corpus estimator. It closes four structural holes
sampled by fresh E12 authors, producing two retrospective E12 candidates, but that does not earn
blind credit. The arrival curve remains the governing uncertainty: new authors have repeatedly
introduced fresh consumer/cardinality idioms faster than narrow deltas clear them. Envelope 13
therefore measures first contact on fresh, class-pure cases under the unchanged hard stops; the
design makes no high-recall forecast and sets no per-envelope recall gate. The trailing blind
window stays `2/18` until future envelopes add first-contact outcomes.

Data generators remain outside the audited project tree. Briefings do not reveal admissions,
guards, prior idioms, or ways to avoid assumption checks. Replay equality, zero negative
candidates, zero Findings, and the available/latest-36 class FA window remain hard stops; first-
contact recall is reported only.

## 16. Reuse map and file-by-file build list

Versioned-copy discipline from the 2.0/2.1 designs governs. Shared historical modules are copied,
never edited.

| File/surface | Required 2.2 change |
|---|---|
| This design | Frozen build specification; no behavior edits during build without reviewed revision. |
| `ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md` | Append the reviewed 2.2 note from 2.4 and section 10; do not rewrite prior decisions. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v2_2.py` | Versioned copy of frozen v2_1 implementing only D2/D3/D5/D6 and the exact pipeline placement. No dependence/private-version import. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v2_2.py` | Version `2.2.0`; unchanged contract/evidence projection; exact closed reason set. |
| New `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v2_2.py` | Versioned detector/check wrapper and unchanged operand/ValueError guards. |
| New `src/sc_referee/scientific_checks/integration_multiple_testing_v2_2.py` | Development-only identities and integration. |
| `scientific_checks/profiles.py` | Retain all historical implementation files; register 2.2 and advance only the active development binding. |
| `detectors/method_conflict_registry.py`, `method_conflict_finding.py`, development controller/resources | Register/dispatch 2.2 beside historical versions; reuse wording v1 only for the exact development binding; no qualified permission. |
| New `_v2_2` test modules | Copy 2.1 test families, retain explicit old imports, and add sections 8/13. Do not retarget old tests. |
| `evaluation/development/multitest-code-slice-v2_2/` | Add the six named FA sources, D2/D3/D5/D6 matrices, E12 ladders, canonical manifest, and development ledger. |
| `evaluation/development/blind-envelope-12-2026-08-26/` replay surface | Add only a 2.2 adapter replay record/oracle; custody/source/audit bytes remain untouched. |
| `multitest-open-corpus-v1` replay harness | Add an explicit 2.2 adapter execution path that compares to frozen 2.1 result rows; do not rewrite `adapter_replay_records_v2_1.json`. |
| New 2.2 oracle/replay tests | E12 15-row table, 50-row equality, E10/E11, PROBE/NEGSIM/ladders/adversaries, and explicit frozen 2.1 anchor. |
| Registry resources, capability ledger, source inventories, release manifest | Regenerate in repository-prescribed order after final implementation/test/artifact changes; custodian refreshes committed-tree manifest as required. |

No-edit surfaces are the qualified lane, GrantPins, wording profiles, contract, historical MT
modules/tests/replay bytes, dependence modules, and the E12 custody/audit record.

## 17. Build acceptance and stop-and-report conditions

Build acceptance requires all of:

1. exact D2/D3/D5/D6 grammars and refusals from sections 4-7;
2. untouched-tree whole-module censuses and D2's exact occurrence bijection;
3. D5 mutation/escape refusal and proof that it is never an order/cardinality source;
4. D6 same-transformer identity and full idempotence;
5. all six recon FA fixtures, with FA-3 and FA-5b covered/complete;
6. exact 15-row E12 adapter oracle with only the three named movements;
7. byte-identical 50-row corpus results, `0/25` correct and `19/25` misstep candidates, without
   regenerating the frozen 2.1 record;
8. unchanged E10/E11, PROBE/NEGSIM, ladder, adversary, and historical oracles;
9. checked-in E12 ladders and, only if supplied, frozen-prototype equivalence;
10. effective prose tripwire and paired structural controls;
11. closed-reason set equality with no synthetic reachability;
12. explicit frozen 2.1 replay and qualified-lane differential; and
13. fresh repository-required lint, format, type, full-test, and starter-validation gates after
    final registry/ledger/artifact generation.

If any correct-case hard gate, adapter oracle, occurrence bijection, D5 immutability proof, D6
idempotence, frozen replay, reason-set equality, or qualified differential cannot pass as written,
implementation stops and reports a design regression. It must not broaden a grammar, weaken a
guard, skip a consumer, relabel a surviving reason, reinterpret a label, rewrite a frozen record,
or adapt the oracle.

## 18. Revision 0a changelog

Revision 0a applies five review clarifications before build. Every item is a narrowing or an
explicit record of an already-required design-time extension; none changes an oracle row.

| Review item | Sections changed | Revision 0a disposition |
|---|---|---|
| `sorted(OUTCOME_SET)` ADR record | 2.4 | Records the exact off-slice presentation read as an extension beyond the recon, with the same disclosure discipline as 2.1 `MASK.sum()`. |
| Reason-string predicate identity | 2.4 | Records D5 set stability as a second `analysis-scope-structure-unsupported` predicate and forbids cross-version comparison of the shared string. |
| D2 post-expansion anchor | 4.1 | Pins the enclosing simple `Assign` and requires every comprehension-expanded occurrence to be eager and strictly below its `EXPR`. |
| D5 container kind | 6.1 | Admits only `ast.Set` displays and explicitly refuses every `frozenset(...)` call. |
| Frozen corpus anchor name | 2.3 | Names `adapter_replay_records_v2_1.json` beside its frozen SHA-256. |
