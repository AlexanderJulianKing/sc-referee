# Multiple-testing code slice 1.1 delta design — 2026-08-25

**Status:** build-ready delta design; design and documentation only in this session

**Version:** detector/check/adapter `1.1.0`, development lane only

**Revision:** 2, incorporating the 2026-08-25 read-only-consumer closure review

**Normative base:**
[`MULTITEST-CODE-SLICE-1.0-DESIGN-2026-08-24.md`](MULTITEST-CODE-SLICE-1.0-DESIGN-2026-08-24.md),
Revision 2.3, `sha256:ac3306f3e58248ac03fee9c75f06d7a9f8a045547ae84f85baae56ecc98fb651`

**Recall evidence:**
[`MULTITEST-RECALL-RECON-E10-2026-08-25.md`](MULTITEST-RECALL-RECON-E10-2026-08-25.md)
and the executable single-construct fixtures under
`evaluation/development/multitest-recall-recon-e10/`

**Opened-envelope evidence:**
`evaluation/development/blind-envelope-10-2026-08-24/AUDIT_RESULTS.json` at commit `0abb544`

This document is normative only for the `1.0.0` to `1.1.0` delta. Every clause of the frozen 1.0
design remains normative unless this document replaces it explicitly. If a delta clause and the 1.0
design conflict, this document governs only the named clause; silence means byte-for-byte semantic
inheritance. The recall recon diagnoses the observed gaps but does not itself authorize a broader
grammar.

The Envelope-10 result was `0/6` first-contact recall, `0/9` false accusations, zero Findings, and
`15/15` deterministic replay. The objective of 1.1 is not to force those positives through. It is to
narrow seven demonstrated unresolved source idioms to closed structural proofs, make two abstention
labels honest, close the inherited mutable-flat-sequence hole, and retain every correction,
hierarchy, resampling, locality, and row-completeness safety wall.

## 1. Decision and non-widening boundary

The 1.1 analyzer admits A1 through A7 exactly as closed in section 3. Each admission converts one
previously unresolved syntax family into a smaller, mechanically proved value or lineage form. There
is no similarity fallback, name-shape inference, prose interpretation, execution, constant folding
outside the enumerated grammars, or tolerance for a partially resolved family.

The following invariants are absolute:

1. `_correction_terminal_census` is copied without semantic change. Its callee-terminal registry,
   full-module reach, alias resolution, and abstention precedence do not shrink.
2. `_off_grammar_transform_guard` blocks every p-derived `BinOp` and `Call` it blocked in 1.0. The
   only change is that two exact, still-blocking scalar shapes receive the honest reason in section
   5.2. No node moves from abstention to correction classification `none` through this guard.
3. `_hierarchy_guard` is copied byte-for-byte and retains every 1.0 control node and residual
   execution-prevention edge. There is no 1.1 hierarchy carve-out: every `IfExp` form still abstains.
4. Complete selected-group row equality is unchanged. A7 proves one previously unsupported spelling
   by applying the existing row-set proof; it does not exempt a mask or weaken equality.
5. The order-12 local registered `.pvalue` requirement, correction input/return grammars, decision
   product rule, family census, API uniformity, extremum guard, statistics-prefix census, and all
   resampling guards are unchanged.
6. Unsupported paths remain abstentions. An admission helper must return either a complete proof or
   one closed reason; it must never return a partial value that downstream code treats as evidence.

The analyzer still makes the 1.0 non-inference that absence of a recognized correction in the
analyzed source does not establish that no correction was applied. A development candidate remains a
contract/code conflict localized to the checked source and CSV, never a correctness certificate or a
claim about runtime behavior.

Because this delta changes candidate eligibility and abstention meaning, implementation requires a
new accepted ADR before behavior changes. It must record these closed admissions, the named
inherited-flat-sequence mutation fix, the two relabels, the deferred ternary decision, the
Envelope-11 protocol, and the preserved guard invariants. The inherited 1.0 flat-sequence setup path
is not silently treated as trusted: section 3.1 adds the same whole-module immutability proof used by
the new A1 route. The ADR must not amend or reinterpret ADR-0077, any qualified grant, or any
GrantPin.

## 2. Identities, authority, wording, and isolation

### 2.1 Versioned identities

The semantic IDs remain stable and their versions advance:

```text
check:authorized-complete-family-correction-over-code-test-battery@1.1.0
adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1@1.1.0
detector:bounded-code-csv-multiple-testing-conflict@1.1.0
method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
```

The stable development binding ID points to check `1.1.0`, adapter `1.1.0`, and detector `1.1.0`.
There is exactly one active binding for this check in the development projection and none in the
ordinary projection. The 1.0 source modules, manifests, audit records, and Envelope-10 custody
artifacts remain immutable historical inputs; they are not silently reidentified as 1.1.

The candidate ID, dimension, comparison form, three canonical operands, four semantic roles, role
bindings, and positive meaning are unchanged from 1.0. The check's `maturity_tier` remains
`question_only`, `production_finding_permitted` remains false, and the development controller emits
zero Findings.

### 2.2 Contract and projection invariance

Scientific-requirement contract profile `1.2.0` is byte-unchanged. Its five-field
`authorized_test_family` authority, authority snapshot, group-domain derivation, ordered outcome
family, family size `N`, and derived uniform test API retain the 1.0 meaning. No contract migration,
schema change, new role, new slot, or new material is introduced.

The `MultipleTestingDataflowFacts`, evidence-span roles, normalized observation, canonical operands,
receipts, and candidate projection retain their exact field sets and validators. New syntax may
produce existing facts; no new fact is inferred from table labels, annotation text, verdict text, or
identifier spelling.

The HEAD-captured 1.0/1.1 contract goldens required by the 1.0 design remain byte-identical. The 1.1
build must rerun, not regenerate, all canonical value, manifest, lock, Answer, digest, and seven
error-string category goldens, including the real populated pseudoreplication 1.1 authority profile.

### 2.3 Wording profile decision

The existing Finding wording profile remains exactly:

```text
method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v1@1.0.0
sha256:80c4bb3c0afd75b290ab02a195e5285528f982554ab46b373e63072232902259
```

No wording v2 is needed. A1-A7 resolve only existing slots:
`CSV_PATH`, `GROUP_COLUMN`, `OUTCOME_COLUMNS`, `AUTHORIZED_COUNT`, `PERFORMED_COUNT`,
`CORRECTED_COUNT`, `UNCORRECTED_COUNT`, and `TEST_API`. The two new reasons never enter a Finding.
The title, summary, validators, severity rationale, next action, and non-inferences remain
byte-identical.

### 2.4 Dual-registry and qualified-lane isolation

The ordinary and development registries retain the 1.0 dual-registry protocol. Updating the active
development module legitimately changes the development module/check/adapter/detector manifests,
the development binding, the lane-inclusive registry digest, and downstream audit-lock fields that
directly bind that digest. Nothing else may derive from that churn.

The two-registry differential gate from 1.0 section 8.1 is rerun for 1.1. It proves byte equality and
non-derivation for every qualified `GrantPin` field, canonical grant, qualification record,
metric-set record, threshold-policy reference, and qualified Finding object. The qualified
pseudoreplication `3.1.0` and complete-domain modules, bindings, detectors, wording profiles,
qualification records, grants, pins, cases, and outcomes are untouched. In particular, these frozen
pseudoreplication digests remain literal test values:

```text
adapter implementation: sha256:6900611a3ef6c06be5740df14333eac5d789c6c93165b8826c796a8b4de87170
recognition grammar:     sha256:69256d48b46f16d7c144e01d5b4509470e9b187bf3db4f7e259d782459c2d476
finding profile v2:     sha256:1dad7c14985fbfb89a7f8fe24a5e7f36d07a7c9fc6f76b4d14951cc71337c04a
wording profile v1:     sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288
```

No edit is permitted to `code_csv_dependence_dataflow*.py`, a qualified adapter or detector,
`method_conflict_grant_pins.py`, or either pseudoreplication wording profile.

## 3. Exact A1–A7 admissions

All limits below are inclusive. Each resolver operates on the bounded AST after docstring removal
and preserves the 1 MiB, 50,000-node, 16-definition, recursion, and X4 ceilings from 1.0. Failure to
prove every stated condition returns the pre-existing reason named below, except where section 5
defines an honest relabel.

### 3.1 A1 — nested constant outcome table

A module setup value may be an outer `ast.List` or `ast.Tuple` with `1..16` rows when:

1. every row is an `ast.List` or `ast.Tuple` with `1..8` elements;
2. every element is an `ast.Constant` admitted by the existing scalar grammar: `None`, `bool`,
   `int`, a finite `float`, or a nonempty NUL-free UTF-8 string of at most 128 bytes; complex values
   are refused;
3. there is no `Starred`, comprehension, name lookup, unary or binary expression, call, attribute,
   subscript, dict, set, or deeper container; and
4. the outer target is one simple module binding admitted by A3/ordinary `Assign` rules and passes
   the whole-module immutable-sequence condition below.

The whole-module immutable-sequence condition copies A2 condition 4 by value for sequences and
applies both to A1 nested tables and to the inherited 1.0 flat `List`/`Tuple` setup path. Starting at
the selected module binding, form a
transitive alias closure from only exact `ALIAS = BOUND_NAME` name-identity assignments. Scan every
statement and expression in the parsed module, including literal-false branches, uncalled helpers,
handlers, nested scopes, and module/main bodies. Refuse the setup value if the original name or any
alias has any of these uses:

- a call to receiver attribute `append`, `remove`, `pop`, `insert`, `extend`, `clear`, `sort`,
  `reverse`, or `__setitem__`;
- any receiver call or positional/keyword argument passage outside the closed read-only-consumer
  grammar below and not proved through unchanged X4 expansion, which is an unresolved escape;
- any second `Store` binding, `AugAssign`, `NamedExpr`, import/function/class/parameter/capture
  binding, `global`, or `nonlocal` for that identifier;
- a `Del` of the name or one of its elements;
- a `Store` or `Del` subscript, including an integer-index assignment or deletion; or
- a slice assignment or deletion.

The closed read-only-consumer allowlist is exact and copied by value. A load of the original name or
an identity alias is permitted only in one of these forms:

1. **Unshadowed builtin consumption.** The call target is an exact unshadowed `ast.Name` in
   `{len, enumerate, zip, sorted, set, tuple, list, reversed, sum, min, max}` and the tracked sequence
   is one direct, non-starred positional argument. `len`, `set`, `tuple`, `list`, `reversed`, `min`,
   and `max` admit exactly that one argument and no keywords. `enumerate` admits the sequence first
   plus an optional `start`, positional or keyword but not both, resolving under the integer-index
   literal grammar in item 4. `zip` admits `1..16` direct positional arguments and only an optional
   `strict` keyword whose value is a bare boolean `ast.Constant`. `sorted` admits the sequence first,
   optional `key=None`, and optional `reverse` as a bare boolean `ast.Constant`. `sum` admits the
   sequence first plus an optional `start`, positional or keyword but not both, that is a bare finite
   non-boolean numeric `ast.Constant`. No `*args`, `**kwargs`, duplicate keyword, or other keyword is
   admitted, and other arguments cannot contain another tracked-sequence load. This permission
   establishes non-mutation only: `enumerate`, `zip`,
   `sorted`, or a copied container still cannot prove family cardinality, order, operands, or rows
   unless a later unchanged predicate independently admits that shape.
2. **Membership.** The sequence is the sole comparator of an exact one-operator `ast.Compare` whose
   operator is `ast.In` or `ast.NotIn`.
3. **Direct iteration.** The sequence is exactly the `iter` expression of `ast.For`, `ast.AsyncFor`,
   or `ast.comprehension`. This permission proves only that acquiring the iterator does not mutate
   the sequence. A loop/comprehension wrapper still has its existing family-proof meaning, and any
   mutation or unresolved escape of a container element bound by that iteration is an alias mutation
   and is refused.
4. **Integer-index read.** The sequence is the `value` of an `ast.Subscript` in `Load` context; the
   slice is not a slice and resolves to a finite in-bounds Python `int` other than `bool` from an
   integer `ast.Constant`, unary `+`/`-` of one, or an exact existing loop/member substitution already
   resolved to one of those values. Arithmetic, calls, attributes, unresolved names, and slices are
   refused. A container-valued row obtained this way remains subject to the mutation/escape scan;
   the permission does not make it an independent family.
5. **Fresh `+` concatenation.** The load is an operand in a finite `ast.BinOp(Add)`-only tree whose
   other leaves resolve to built-in list/tuple literals or other exact admitted literal sequences of
   the matching container kind. The root is the entire RHS of one single-name `Assign` or
   `AnnAssign`; its target is a different identifier outside the transitive alias closure. The new
   name is not added to the identity-alias closure and the concatenation supplies no family proof.
   A concatenation nested inside a call, subscript, return, container element, or larger non-`Add`
   expression is not admitted.
6. **Formatting payload.** The load is a direct `ast.FormattedValue.value` in an f-string; the first
   direct positional payload of an exact unshadowed builtin `format` call with one optional static
   format-spec argument; or a direct positional/keyword replacement payload of `.format` whose
   receiver is a direct string `ast.Constant`. Format text, conversion text, and rendered bytes are
   never read as evidence. No `%` formatting, dynamic receiver, starred payload, or payload returned
   from a helper is admitted by this clause.

Assignment to a new name is otherwise permitted only as the exact identity alias that enters the
closure; all later uses of that alias are subject to the same scan. A call such as
`test_declared_outcomes(DECLARED_OUTCOMES)` remains an unresolved escape unless the unchanged X4
expansion uniquely resolves that project helper and its formal/actual path; X4 must expose every
formal use to this same mutation/escape scan and supplies no new family-cardinality proof. An
attribute/subscript/container store of the sequence, return/yield of it, user-defined or unresolved
call argument outside that X4 case, or any use whose aliasing effect is unresolved remains an
unresolved escape. Failure of this condition stops at order 6 with
`analysis-scope-structure-unsupported`; no frozen copy of the original literal may reach the call
census. The scan runs before `_module_setup_assignment` may return any resolved flat or nested
sequence; no flat-`Tuple`/`List` early return may bypass it. This is the named
**inherited-flat-sequence mutation fix**: 1.0 could freeze a flat module list before a later
`.remove`, `.append`, or alias-then-`.pop` in `main`, creating a false static family count. Version
1.1 closes that inherited route as well as protecting A1.

The resolver stores the rows and container kinds immutably. It does not flatten all cells into a
family. A table proves an exact contract-outcome factor only when all rows have one common arity, the
iteration target is a list/tuple of that arity containing distinct simple `Name` stores and no
`Starred`, and the ordered position-0 projection is byte-for-byte equal to the ordered contract
outcome list. The factor is exactly `N`; the remaining positions bind their row constants for that
expanded member but never identify the family.

Only a direct iteration over the bound table name is admitted for family expansion. `enumerate`,
`zip`, slicing, concatenation, `sorted`, `reversed`, a comprehension-derived iterable, a table alias
whose identity is unresolved, a reordered/set-equal projection, or any position other than zero
cannot supply the order-8 factor. When that table projection is needed to census the family, the
exact first reason is `test-battery-cardinality-unresolved`. In the separate subcase where exactly
`N` explicit or otherwise independently resolved calls establish the order-8 census without the
table, but a call operand is mapped through a non-position-0 or contract-unequal table value, order
10 returns exactly `test-operand-lineage-unresolved`. Tests keep these two subcases separate; no
fixture may accept either reason as an alternative.

Exact literal subscripting of a known row and exact tuple/list destructuring may resolve constants.
No label text, unit text, numeric metadata, or other nonzero-position value is read or compared for
scientific meaning.

### 3.2 A2 — constant-only dictionary

A module setup value may be an `ast.Dict` containing `0..16` entries when:

1. it has no `**` unpack (`key is None`);
2. every key and value is one scalar `ast.Constant` admitted by A1;
3. every key is hashable and unique under Python value equality, including refusal of collisions
   such as `1` and `True`; and
4. the dictionary has one simple module target and no later mutation, alias mutation, rebinding, or
   unresolved escape.

This exact constant dictionary is admitted even when its target is loaded in `main`; that is the
only removal of the old loaded-in-main veto. It supports only exact literal-key lookup after closed
loop/member substitution and exact deterministic iteration using the literal insertion order.
`.get`, views, merging, update, comprehension, unpacking, dynamic subscript keys, and mutation are
not resolved. Dictionary keys never replace the contract outcome list or prove family order.

### 3.3 A3 — annotated setup assignment

An `ast.AnnAssign` is treated exactly like the corresponding admitted `Assign` only when:

1. `simple == 1`, the target is one `ast.Name`, and `value` is not `None`;
2. the RHS satisfies one existing setup-value rule or A1/A2 with identical limits;
3. the annotation contains no `Call`, `Await`, `Yield`, `YieldFrom`, `Lambda`, comprehension,
   `NamedExpr`, or store/delete context; and
4. the target has no second binding or mutation where the selected value grammar requires
   uniqueness.

The annotation is never read as evidence and its spelling is never matched. Admitted structural
annotation nodes are only `Name`, dotted `Attribute`, `Subscript`, `Tuple`, `List`, `Constant`,
`Load`, and the PEP-604 `BitOr` composition of those nodes. An unsupported annotation or RHS returns
`analysis-scope-structure-unsupported`; it is not evaluated or guessed.

### 3.4 A4 — authorized reader path through one helper formal

The full-scope reader census may resolve the sole positional path argument of an otherwise accepted
`pandas.read_csv` or `numpy.genfromtxt` call when that argument is exactly an `ast.Name` denoting a
formal parameter of one unique, synchronous, undecorated top-level helper. This admission requires:

1. the reader call retains every 1.0 API, positional, keyword, CSV-header, parsed-date, and forbidden-
   column restriction;
2. the helper has no positional-only, variadic, keyword-only, recursive, nested, global/nonlocal, or
   unsupported binding shape relevant to this proof;
3. the helper is called at least once by a simple-name call and has no unresolved or indirect call
   site;
4. `_bind_helper_arguments` succeeds independently at every call site, with no starred argument,
   `**` keyword, duplicate binding, missing required argument, or unknown keyword;
5. the selected formal's declared default, when present, resolves to the authorized static path, and
   the value bound at every call site resolves to that same static path;
6. no default or call-site binding resolves to `None`, an unresolved expression, or a different
   path; and
7. the module contains exactly one accepted reader definition after this resolution.

The census counts the reader definition once, not each invocation. Two reader definitions still
return `additional-accepted-reader-present`; zero, an uncalled helper, any `None`, mixed paths, or an
unresolved call returns `authorized-reader-lineage-unavailable`. Unlike the dependence sibling, a
`None` reader result is never tolerated as possibly authorized.

A4 resolves only the reader call's path slot. It creates no reader-rooted frame at the helper call
site and does not inline the helper as proof of a frame, test call, data selection, or p-value
lineage. Frame lineage from a helper return still requires the byte-unchanged 1.0 X4 expansion and
all ordinary row-completeness proofs. In particular, a helper whose body reads the authorized path
and then executes `return frame[frame["qc"] == "pass"]` does not yield a complete frame at its call
site; the complete-family project fixture `correct-helper-reader-row-filter` must abstain exactly
`selected-group-row-completeness-unproven`.

### 3.5 A5 — singly bound named decision literal

At order 15, the non-p operand of a one-operator `<`, `<=`, `>`, or `>=` comparison, in either
operand order, may be an `ast.Name` instead of a bare literal only when all of the following hold:

1. the name's sole binding is one top-level, single-target `Assign` or A3 `AnnAssign` whose RHS is a
   bare finite, non-boolean numeric `ast.Constant`;
2. the entire parsed module contains exactly one binding event for that identifier; and
3. the resulting exact Decimal is in `{Decimal("0.01"), Decimal("0.05"), Decimal("0.1")}` and passes
   the unchanged family product rule.

The binding census is syntax-wide and control-flow independent. It counts every recursive `Store`
target in `Assign`, `AnnAssign`, `AugAssign`, `NamedExpr`, `For`, `AsyncFor`, comprehensions, and
`with ... as`; every positional-only, positional, keyword-only, vararg, and kwarg parameter of every
function, async function, and lambda; `ast.alias` import bindings; function and class names in the
enclosing scope; `ExceptHandler.name`; and every `MatchAs.name`, `MatchStar.name`, and
`MatchMapping.rest` capture. For an `ast.alias`, the bound identifier is `asname` when present;
otherwise it is the first dotted segment for `import package.member`, and the imported member for
`from package import member`. Wildcard imports and import forms already refused by the API resolver
never supply an A5 value, but they are not silently omitted to make the identifier unique. A
same-name `global`, `nonlocal`, or `Del` occurrence disqualifies the admission. Bindings in
literal-false branches, uncalled helpers, handlers, match cases, and nested scopes still count. The
census never ignores a binding because it is a `BinOp` or appears unreachable.

The Decimal is constructed from the literal's source token text after removal of permitted numeric
underscores. If source text is unavailable, use `Decimal(repr(value))`; `Decimal(float)` is forbidden.
The conventional-literal product rule then computes `literal * Decimal(N)` exactly and abstains
`unresolved-decision-threshold` when that product is one of `0.01`, `0.05`, or `0.1`. Any second
binding, dynamic RHS, arithmetic threshold, attribute, subscript, call, alias chain, missing source
identity, or off-set value returns `unresolved-decision-threshold`, unless the unsupported module
statement necessarily stops earlier with `analysis-scope-structure-unsupported`.

A scalar row value obtained by tuple/list destructuring or literal subscripting is not a bare
literal and is not an A5 name binding, even when its ultimate table cell is a permitted number. It
therefore abstains `unresolved-decision-threshold` at order 15. The required fixture is a
per-outcome table such as `OUTCOMES = [("m", 0.01), ...]` followed by
`for name, alpha in OUTCOMES: ... P < alpha`; it must never become a candidate.

Thus a module-level `ALPHA = 0.05` may be admitted, while
`ALPHA = ALPHA / len(OUTCOMES)` is never silently ignored. The latter script must abstain, including
when it implements a correct hand Bonferroni threshold; it can never become a candidate.
The census-only shadowing fixture instead has module `ALPHA = 0.05` and a local
`ALPHA = 0.05 / len(OUTCOMES)` inside `main`; its other structures are chosen to reach order 15, and
its exact first reason is `unresolved-decision-threshold`, never a candidate.

### 3.6 A6 — row-identity-preserving Series cast

An operand Series may pass through exactly one attribute call
`SERIES.astype(DTYPE)` when there is one positional argument, no keywords or starred arguments, and
`DTYPE` passes the copied `_closed_dtype` grammar by value:

- an unshadowed bare `bool`, `float`, `int`, or `str`; or
- a statically resolved NUL-free string of at most 64 UTF-8 bytes.

The returned Series inherits the same reader root, selected row set, outcome header, group value,
and completeness flag. A6 proves only row identity; it does not establish successful runtime casting,
numeric validity, test assumptions, or execution. Frame-wide casts, a second argument, keywords,
dynamic or attribute dtypes, an unclosed callee, or any row-changing call returns
`test-operand-lineage-unresolved`. Row selection before or after the cast must independently satisfy
the unchanged 1.0 selection routes or A7, followed by the unchanged completeness equality.

### 3.7 A7 — exact boolean-mask group split

The operand resolver may recognize either:

```text
FRAME[FRAME[GROUP_COLUMN] == GROUP_VALUE][OUTCOME]
MASKED = FRAME[FRAME[GROUP_COLUMN] == GROUP_VALUE]
MASKED[OUTCOME]
```

including exact identity aliases and the reversed equality operand order, only when:

1. `FRAME` resolves to the one authorized reader-rooted complete frame;
2. the mask is one `ast.Compare`, has exactly one `ast.Eq`, and has one comparator;
3. the column read is an exact subscript of the same frame lineage as the selected receiver and
   resolves byte-for-byte to the contract group column;
4. the other operand resolves to one literal group value derived from the authorized CSV;
5. applying the existing `_mask_rows` value grammar yields exactly the complete authorized-CSV row
   set for that group; and
6. the outer projection resolves to the current contract outcome member.

No boolean-mask subscript is a row-preserving `.query` exemption. A7 is a separate proved group-row
selection whose rows must equal the complete group domain. `&`, `|`, `and`, `or`, `~`, `!=`,
`isin`, a call-produced mask, cross-frame mask, outcome mask, slice, second mask, discovery/validation
predicate, or unresolved value fails operand resolution or returns
`selected-group-row-completeness-unproven` under the unchanged order-10/order-11 distinction.

A7 admits only the exact comparison against the contract group column. Its implementation must
reject `column != group_column` before invoking the copied `_mask_rows` evaluator, or wrap that
evaluator so only the proved group-column branch can return through A7. The permissive non-group
branch that `_mask_rows` uses for other inherited contexts is never exposed to a bare boolean
subscript by A7.

## 5. Honest abstention labels and closed set

### 5.1 Scope relabel

When `_chosen_scope` returns its existing raw `analysis-scope-ambiguous` outcome after A1-A3 have
been applied, the 1.1 entry point returns the new closed reason:

```text
analysis-scope-structure-unsupported
```

This reason means only that the module/main/setup shape is outside the chosen closed analysis scope.
It covers an invalid or nonunique `main`/main guard, unsupported executable module statement,
unsupported loaded setup expression such as P6's `HEADLINE` comprehension, and other raw scope-shape
failures. It does not claim ambiguous API identity. Exact helper-specific raw reasons retain their X4
codes. `_resolver`, shadowing, import, alias, and duplicate API failures still return
`api-resolution-ambiguous`.

### 5.2 Scalar cast/rounding relabel

At order 14, an otherwise off-grammar p-derived call returns the new closed reason:

```text
pvalue-scalar-cast-or-rounding-unsupported
```

only for either of these exact shapes:

```text
float(P)
round(P)
round(P, K)
```

`float` and `round` must resolve to the unshadowed builtins; there are no keywords or starred
arguments; `K` is a bare non-boolean integer `ast.Constant`; and `P` resolves directly, through only
the existing identity/name/member closure, to one registered local `.pvalue`. A nested call,
arithmetic input, adjusted value, dynamic precision, keyword, shadowed callee, NumPy cast, or any
other p-derived call retains `unresolved-manual-correction-present` unless an earlier 1.0 reason
applies.

In particular, `round(P, -1)` is refused: Python parses `-1` as `ast.UnaryOp(USub,
Constant(1))`, not as the admitted bare integer `ast.Constant`. Its exact pinned first reason is
`unresolved-manual-correction-present`.

This is a relabel, not an admission: all three exact shapes still abstain before threshold,
hierarchy, conclusion, and correction classification. The reason does not assert that no correction
exists or infer why the scalar operation was written.

### 5.3 Exact 1.1 reason registry

The 1.1 closed reason set is exactly the 1.0 closed set plus:

```text
analysis-scope-structure-unsupported
pvalue-scalar-cast-or-rounding-unsupported
```

No 1.0 code is removed. `conclusion-output-sink-unavailable` remains in the 1.0 documented-unreachable
annex and closed replay vocabulary; it must not receive a manufactured test path. Both new reasons
must have real, end-to-end emitting fixtures. The adapter's frozen set, analyzer-emitter census, and
documented-unreachable annex must be set-equal.

## 6. Ordered predicate delta

The 1.0 section-5 order remains normative. The only changes are:

| 1.0 order | 1.1 delta | First reason on failure |
|---:|---|---|
| 6 | Apply A1-A3 while choosing setup/scope and resolving constants. Apply section 3.1's whole-module immutable-sequence condition and exact read-only-consumer allowlist to both A1 and the inherited flat-sequence setup route. Relabel only the raw chosen-scope failure. Run the syntax-wide A5 binding census as metadata; it supplies no value until order 15. | `analysis-scope-structure-unsupported`; unchanged `api-resolution-ambiguous` and X4 reasons |
| 7 | Apply A4 to the one-reader full-scope census. | unchanged `additional-accepted-reader-present`; `authorized-reader-lineage-unavailable` |
| 8 | Allow A1's exact position-0 table projection to supply factor `N`; no wrapper or subset admission. | unchanged call-census reasons |
| 10 | Apply A6 and A7 while resolving each registered call's two operands. | unchanged `test-operand-lineage-unresolved` |
| 11 | Compare A7's selected rows to the exact authorized group rows. | unchanged `selected-group-row-completeness-unproven` |
| 14 | Relabel only the exact direct-`P` builtin scalar shapes in section 5.2. All blocked nodes remain blocked. | new `pvalue-scalar-cast-or-rounding-unsupported`; otherwise unchanged correction reasons |
| 15 | Apply A5 to a direct named comparison operand, then the unchanged exact-Decimal product rule. Direct-`P` comparisons remain exclusive to this order. | unchanged `unresolved-decision-threshold` |
| 16 | Run the byte-unchanged 1.0 hierarchy guard, then every unchanged partition, resampling, and statistics-prefix clause. No `IfExp.test` is exempted. | unchanged hierarchy/control reasons |

No admission changes first-reason precedence. For example, an A1 table around an `enumerate` family
still stops at order 8, an exact `float(P)` still stops at order 14 even if a later correction is
complete, and a named threshold must pass the product rule before the unchanged hierarchy guard can
be reached.

## 7. Retained abstentions and explicit residuals

The following are deliberate 1.1 walls:

1. **`csv.DictReader` value model.** No row/value/header lineage is added for `csv.DictReader`,
   `open`, record dictionaries, or row comprehensions. P1 remains
   `authorized-reader-lineage-unavailable`.
2. **Resampling-loop unrolling.** A registered family test or draw inside a resampling loop is not
   multiplied into the authorized family. Unresolved cardinality retains
   `test-battery-cardinality-unresolved` or `resampling-cardinality-unresolved` at its existing
   predicate; the maxT/minP guard is not weakened.
3. **Comprehension-derived subsets.** No comprehension, slice, starred projection, or dynamically
   derived subset becomes an authorized family. In particular, P6's
   `HEADLINE = [name for name, *_ in OUTCOMES[:3]]` remains unsupported and the module stops
   `analysis-scope-structure-unsupported`.
4. **Statistics imports outside `analysis.py`.** The exact 1.0 closed import world remains. The opened
   N7 project still stops `statistics-api-imported-outside-analysis-py`; Envelope 11 fixes custody
   rather than relaxing this guard.
5. **Helper-wrapped family tests and wrapped `.pvalue` returns.** No new X4 admission is part of A1-A7.
   Unsupported helper call census/expansion remains an abstention. The 1.0 helper-`.pvalue` recall
   limitation remains.
6. **`enumerate`/`zip` family wrappers.** No family cardinality or ordered member proof is added.
7. **Scalar p casts/rounding.** Exact `float`/`round` shapes receive an honest reason but remain
   abstentions.
8. **Deferred or dynamically keyed result collections.** No new ordered p-family reconstruction is
   introduced; `pvalue-family-collection-unresolved` retains its 1.0 meaning.
9. **Verdict ternaries.** The proposed display-only `IfExp` carve-out is deferred in full.
   `_hierarchy_guard` is byte-unchanged, so direct sink ternaries, assigned ternaries, and every
   other p-controlled `IfExp` retain the 1.0 hierarchy/control abstention. This was the delta's only
   proposed guard subtraction, the exact proposed shape occurred zero times among the 25 `IfExp`
   nodes in the only blind corpus, and all six E10 positives use the assigned form that would have
   remained refused. Under the standing guards-before-recall rule, no unobserved exception is
   admitted. A later delta may reconsider it only with new observed evidence and a separate review.

The accepted 1.0 BL-1 residual also remains: the product rule recognizes only conventional family
alphas in `{0.01, 0.05, 0.1}` and does not infer an arbitrary family alpha.

## 8. False-accusation analysis and adversarial fixtures

Every fixture below is a complete authorized-family project with real CSV bytes and a real 1.2
contract. Tests invoke the public 1.1 analyzer/adapter; a direct helper-unit result is insufficient.

| Change | False-accusation vector | Required adversarial correct-analysis fixture and outcome |
|---|---|---|
| A1 nested table and inherited flat-sequence immutability | Treating any table position, reordering, slice, or wrapper as the contract family could establish the wrong `N` calls. Freezing a literal before later mutation can claim calls that do not execute or miss extra calls; refusing ordinary read-only consumers suppresses valid baselines before later guards. | `correct-nested-table-nonzero-factor`: a family loop uses a non-position-0 factor and abstains exactly `test-battery-cardinality-unresolved`. `correct-unrolled-nested-table-wrong-operand-slot` independently establishes `N` calls but maps an operand through the wrong table slot and abstains exactly `test-operand-lineage-unresolved`. The mutation matrix returns `analysis-scope-structure-unsupported` for both A1 and inherited flat lists. `closed-sequence-read-consumers` exercises every section-3.1 allowlisted consumer without changing the baseline first result; `correct-sequence-user-callee-escape` passes the sequence to an unresolved project callee and abstains exactly `analysis-scope-structure-unsupported`. |
| A2 constant dict | Treating dictionary keys/order as family authority or ignoring mutation could manufacture a battery. | `correct-constant-dict-mutation-not-setup-proof`: a literal label map is mutated before use and a complete correction follows; abstain `analysis-scope-structure-unsupported`, never classify `none`. |
| A3 AnnAssign | Accepting annotation computation or a dynamic RHS could hide a constructed family. | `correct-annotated-dynamic-family-builder`: annotated `OUTCOMES` has a call/comprehension RHS and a complete correction; abstain `analysis-scope-structure-unsupported`. |
| A4 helper path | Treating unresolved/`None` helper readers as possibly authorized could bind a different CSV or manufacture a complete call-site frame. | `correct-helper-reader-none-default` and `correct-helper-reader-mixed-paths`: one uses a `None` default and one has two call-site paths; both abstain `authorized-reader-lineage-unavailable`. `correct-helper-reader-row-filter` returns `frame[frame["qc"] == "pass"]` and abstains exactly `selected-group-row-completeness-unproven`. |
| A5 named alpha | Ignoring a second binding or treating a row-derived value as a module literal can convict hand Bonferroni code as uncorrected. | Module-scope `correct-hand-bonferroni-alpha-rebinding` returns exactly `analysis-scope-structure-unsupported`. `correct-local-alpha-bonferroni-shadowing` has module `ALPHA = 0.05` and local `ALPHA = 0.05 / len(OUTCOMES)` and reaches exactly `unresolved-decision-threshold`; `correct-alpha-shadowed-helper-parameter` does likewise. `correct-per-outcome-threshold-table` destructures `(name, alpha)` rows and returns exactly `unresolved-decision-threshold`. None may become a candidate. |
| A6 `.astype` | Treating a cast chain as row-preserving could hide row deletion or a different selection. | `correct-astype-after-additional-row-mask`: a structurally visible stage mask precedes the cast and a complete correction follows; abstain exactly `selected-group-row-completeness-unproven`. |
| A7 boolean mask | Equating any boolean subscript with a complete group or exposing `_mask_rows`' non-group branch admits discovery/validation or combined masks. | `correct-boolean-mask-discovery-validation`: group equality is combined with a stage mask; abstain `selected-group-row-completeness-unproven`. A cross-frame mask and a bare non-group-column mask abstain `test-operand-lineage-unresolved`. |
| Unchanged hierarchy | A p-value branch can gate tests, corrections, containers, or emissions; an unobserved display exception would subtract a guard without recall evidence. | `correct-inline-display-ternary`, assigned `PROBE_ternary.py`, correction/container/second-emission ternaries, and all 25 opened-corpus `IfExp` nodes retain their 1.0 hierarchy/control outcomes. A registered-test gate stops at the earlier `authorized-family-test-census-incomplete`; an unresolved control edge remains `pvalue-control-dependence-unresolved`. |
| Scope relabel | Relabeling could accidentally hide true import/API ambiguity. | `unsupported-module-comprehension-scope` returns `analysis-scope-structure-unsupported`; `ambiguous-statistics-alias` still returns `api-resolution-ambiguous`. |
| Scalar relabel | Broadly treating casts as harmless could admit arithmetic correction or transformed decisions. | `correct-hand-bonferroni-inside-float` retains `unresolved-manual-correction-present`; isolated direct `float(P)` and `round(P, 4)` return only `pvalue-scalar-cast-or-rounding-unsupported`; `round(P, -1)` retains exactly `unresolved-manual-correction-present` because `-1` is an `ast.UnaryOp`, not a bare integer `ast.Constant`. |

The build also reruns every 1.0 per-guard adversarial fixture unchanged, including hand Sidak,
off-registry correction, default-method `multipletests`, sensitivity duplicate,
discovery/validation split, all-NumPy omnibus/assert gates, and label-permutation maxT.

The three executable recon near-similar negatives are also pinned after the delta:

| Fixture | Required 1.1 first reason |
|---|---|
| `NEGSIM_A.py` | `correction-family-lineage-unresolved` |
| `NEGSIM_B.py` | `unresolved-manual-correction-present` |
| `NEGSIM_C.py` | `pvalue-scalar-cast-or-rounding-unsupported` |

Only `NEGSIM_C.py` changes reason: its exact direct `float(P)` shape receives the honest scalar
relabel while remaining an abstention. `NEGSIM_B.py` contains a hand-Bonferroni threshold and stays
owned by the unchanged off-grammar transform guard.

## 9. Executable test plan

### 9.1 Recon probe matrix

Every existing `PROBE_*.py` file under
`evaluation/development/multitest-recall-recon-e10/mut/` becomes a checked-in recognizer fixture.
Each test loads its source bytes and authorized CSV/contract facts and executes the 1.1 analyzer. A
test that merely asserts AST shape, fixture text, or an internal helper result does not satisfy this
gate.

| Recon fixture | Required 1.1 outcome |
|---|---|
| `PROBE_nestedtable.py` | candidate, classification `none` (A1) |
| `PROBE_dicttable.py` | candidate, classification `none` (A2) |
| `PROBE_pathparam.py` | candidate, classification `none` (A4) |
| `PROBE_namedalpha.py` | candidate, classification `none` (A5) |
| `PROBE_astype.py` | candidate, classification `none` (A6) |
| `PROBE_boolmask.py` | candidate, classification `none` (A7) |
| `PROBE_query.py` | candidate, classification `none`; unchanged positive control |
| `PROBE_enumerate.py` | `test-battery-cardinality-unresolved` |
| `PROBE_helpertest.py` | `test-battery-cardinality-unresolved` |
| `PROBE_floatp.py` | `pvalue-scalar-cast-or-rounding-unsupported` |
| `PROBE_roundp.py` | `pvalue-scalar-cast-or-rounding-unsupported` |
| `PROBE_ternary.py` | `hierarchical-gatekeeping-present` because the ternary is assigned before the sink |
| `NEGSIM_A.py` | `correction-family-lineage-unresolved` |
| `NEGSIM_B.py` | `unresolved-manual-correction-present` |
| `NEGSIM_C.py` | `pvalue-scalar-cast-or-rounding-unsupported` |

Revision 2 re-verifies the source bytes of all 12 `PROBE_*.py` rows against the section-3.1
consumer grammar. Their `len` uses, direct-assignment `+` copies, direct loop/comprehension
iteration, formatting payloads, and the isolated `enumerate` use are read-only consumers only; none
is an order-6 escape and none gains family evidence from that permission. Therefore all 12 PROBE
outcomes above are unchanged. The three `NEGSIM` outcomes are also unchanged.

Add `PROBE_annassign.py` as the A3 isolated candidate. Each A1-A7 candidate must contain facts for
exactly `N` calls, all `N` conclusion positions, the unchanged registered sink kind, and no
correction positions. There is no ternary candidate in 1.1.

### 9.2 Admission and binder matrices

For A1, cross product list/tuple outer and list/tuple rows, arities 1 and 8, outer lengths 1 and 16,
all scalar kinds, tuple/list target destructuring, and exact position-0 equality. Refuse zero/17
rows, zero/9 cells, ragged family expansion, complex/nonfinite/oversize/NUL strings, nesting,
starred targets, duplicate targets, position-1 family use, slice/reorder, `enumerate`, and `zip`.
The position-1 family-factor fixture asserts only `test-battery-cardinality-unresolved`; the separate
independently censused, unrolled wrong-operand-slot fixture asserts only
`test-operand-lineage-unresolved`.

Run the immutable-sequence matrix twice, once with an A1 nested table and once with an inherited 1.0
flat sequence. It has one executing fixture for each refused mutating attribute: `append`, `remove`,
`pop`, `insert`, `extend`, `clear`, `sort`, `reverse`, and `__setitem__`. It also has one fixture each
for rebinding, `del`, integer-subscript store, slice assignment, unresolved escape to an unknown
call, and the transitive alias case `ALIAS = OUTCOMES; ALIAS.pop()`. Every fixture invokes the public
analyzer and returns exactly `analysis-scope-structure-unsupported`; no one-time frozen literal may
reach order 8. Positive read-only fixtures prove that the scan does not reject the existing closed
iteration/lookup forms.

The positive read-only matrix executes every section-3.1 consumer by value: each unshadowed builtin
and its boundary arities/keywords, both membership operators, all three direct-iteration node kinds,
positive/negative in-bounds integer reads, fresh matching-kind `+` chains assigned to a different
name, direct f-string payload, unshadowed builtin `format`, and literal-string `.format` payload.
Each retains its baseline candidate or later exact abstention; a safe consumer never supplies a new
family fact. Paired negatives cover shadowing, invalid/extra/starred arguments, slice/non-integer/
out-of-bounds reads, concatenation into an alias name or nested under a call, `%` formatting,
dynamic `.format` receiver, direct passage to an unresolved project/imported callee, and a project
helper whose unchanged X4 expansion exposes a mutating or escaping formal use. The last group returns
exactly `analysis-scope-structure-unsupported`. A unique project helper whose unchanged X4 expansion
proves only allowlisted formal uses passes the escape scan but acquires no cardinality admission.

For A2, cover empty/16-entry dicts, every scalar key/value kind, literal lookup after member
substitution, loaded-in-main use, Python-equality collision, duplicate key, `**`, mutation, `.get`,
dynamic lookup, views, and comprehension. Dict key or value prose mutations that preserve structural
slots must not affect facts.

For A3, cover every RHS class admitted for `Assign`, the E10 `list[tuple[...]]` form, string and
PEP-604 annotations, missing value, nonsimple target, call/comprehension annotation, dynamic RHS, and
second binding.

For A4, cover default and explicit authorized path, multiple identical calls, zero calls, `None`
default/actual, mixed paths, unresolved path, indirect call, duplicate helper, starred/`**` call,
unknown keyword, missing formal, two reader definitions, and direct-plus-helper readers. The
dependence sibling's `{None, authorized_path}` behavior is a required differential negative: 1.1 MT
must abstain. Add the helper-body row filter `return frame[frame["qc"] == "pass"]`; A4 may resolve
its path but must not manufacture a call-site frame, and the analyzer must return exactly
`selected-group-row-completeness-unproven`.

For A5, cover all four operators in both operand orders, each admitted literal spelling including
source exponents/underscores, all conventional product-rule hits, and every syntax-wide binding kind
listed in section 3.5. The source-Decimal test must distinguish `Decimal("0.01") * 5` from a
`Decimal(float)` path and fail if the latter is used. The BinOp rebinding and same-name helper
parameter fixtures must execute the analyzer and must never produce facts. Cover each exact
`ast.alias` binding rule. Execute the per-outcome threshold-table fixture and require
`unresolved-decision-threshold`. Execute the census-only module/local `ALPHA` spelling from section
3.5 and require exactly `unresolved-decision-threshold`.

For A6, cover four unshadowed builtin dtypes, closed string dtypes, `.astype(...).to_numpy()`, and
every refused arity/keyword/dynamic/shadowed/frame/row-changing form. For A7, cover direct and aliased
frames, comparison reversal, both derived group values, exact row equality, and every refused mask
operator/composition/cross-frame/stage/subset form. Include a bare boolean subscript over a non-group
column and prove it cannot enter through `_mask_rows`' permissive non-group branch.

### 9.3 Byte-unchanged hierarchy and deferred ternary matrix

Pin the exact UTF-8 function-source segment and AST semantic digest of `_hierarchy_guard` in the
frozen 1.0 module, and require the copied 1.1 function-source segment to be byte-identical. No new
exemption predicate or caller-side skip may bypass it. Execute direct sink-argument and f-string
`IfExp` forms for each 1.0 `p_result_eligible` sink kind, plus assigned, returned, container,
`.format`, concatenated, nested, non-string, compound-comparison, BoolOp, adjusted/reject,
second-emission, sink-selection, conditional-sink, test/correction-argument, and unresolved-parent
forms. Every resolved p-controlled `IfExp` remains `hierarchical-gatekeeping-present`; an unresolved
control edge remains `pvalue-control-dependence-unresolved`; an earlier family-census failure retains
its earlier exact reason.

Run the public 1.1 analyzer over all 25 `IfExp` nodes in the opened blind corpus and prove that each
retains its 1.0 first outcome. `PROBE_ternary.py` remains the assigned-name negative. There is no
positive ternary fixture and no fixture is rewritten into a direct-sink candidate.

### 9.4 P2 and P3 mutation ladders

Run the analyzer, in sequence, on the opened original and every checked-in mutation under `mut/`.
The required 1.1 regression sequence is:

```text
P2 original, P2_m1:
    test-battery-cardinality-unresolved
P2_m2, P2_m3:
    test-operand-lineage-unresolved
P2_m4, P2_m5, P2_m6, P2_m7:
    hierarchical-gatekeeping-present
P2_m8:
    candidate / none

P3 original, P3_s1, P3_s2, P3_s3, P3_s4, P3_s5, P3_s6:
    test-battery-cardinality-unresolved
P3_s7:
    extra-registered-test-outside-authorized-family
P3_s8:
    pvalue-family-collection-unresolved
```

Revision 2 re-verifies every ladder source against the closed consumer allowlist. Direct iteration,
comprehension iteration, `len`, `enumerate`, formatting, and fresh direct-assignment concatenation do
not stop at order 6 and provide no new proof, so every rung above retains its Revision-1 outcome.

This gate proves stacked-wall behavior. It must not be replaced by independent fixtures that omit
the preceding mutations.

### 9.5 Closed guards, reasons, and differential properties

1. Copy every 1.0 exact-reason fixture to the 1.1 public analyzer path. Every emitting non-X4 reason
   gets a real end-to-end fixture; the 17 X4 reasons may remain parametrized. Add real fixtures for
   both new reasons. Assert set equality among the adapter registry, actual emitter fixtures, and the
   unchanged documented-unreachable annex.
2. Run the full 1.0 correction API/return/manual/terminal/extremum/threshold/statistics-prefix,
   resampling, row-completeness, hierarchy, export-sink, and conclusion matrices through 1.1.
3. Differentially generate p-derived `BinOp`/`Call` shapes. Every 1.0 off-grammar abstention remains
   an abstention in 1.1; only exact direct `float(P)`/`round(P[, K])` may change the reason. No result
   may change from abstention to correction classification `none` because of an order-14 change.
   Pin `round(P, -1)` outside the relabel grammar.
4. Differentially generate hierarchy controls. Every 1.0 hierarchy/control abstention remains the
   same abstention in 1.1, with no exception. The copied `_hierarchy_guard` function-source bytes are
   identical to 1.0 and all 25 opened-corpus `IfExp` nodes preserve their outcomes.
5. Differentially generate row masks. The selected row set admitted by A7 must equal one complete
   derived group set; no strict subset accepted by 1.1 may have been refused by the 1.0 equality
   predicate.
6. Pin check/adapter/detector identity `1.1.0`, every detector `ValueError` guard, including an
   out-of-registry operand, and development no-Finding behavior.
7. Differentially mutate every A1 and inherited flat-sequence binding with each section-3.1 shape.
   A value rejected for mutation/escape can never produce a 1.1 fact even if the original literal
   alone would have matched the contract.
8. Differentially wrap an otherwise identical tracked sequence in every allowed and adjacent
   refused consumer. Allowed consumers preserve the baseline first result and add no fact; refused
   consumers stop `analysis-scope-structure-unsupported`. A project-callee passage changes sides only
   when unchanged X4 expansion proves all formal uses within the same closed allowlist.

### 9.6 Prose tripwire

Extend the 1.0 prose tripwire over every branch introduced or changed here: A1 row/table parsing and
position-0 projection and the shared whole-module immutability/alias/read-only-consumer scan; A2
dict/collision/lookup; A3 target/RHS/annotation grammar; A4 actual/formal/default path binding without
a synthetic call-site frame; A5 syntax-wide binding census including exact `ast.alias` bindings,
source-Decimal construction, row-derived-threshold refusal, and product rule; A6 dtype closure; A7
same-frame group-column mask and row equality; scope relabel; and scalar-transform relabel. The
unchanged 1.0 hierarchy tripwire is rerun, but no new ternary predicate exists in 1.1.

For every new positive and adversarial fixture, mutate comments, docstrings, Markdown, reports, task
text, unrelated strings, output labels, format text, and non-callee identifiers. Add and remove report
and Markdown files. Rename non-callee identifiers to `bonferroni`, `holm`, `sidak`, and
`benjamini_hochberg`. Facts, first reasons, and candidate classification remain invariant under the
same normalization used by the 1.0 tripwire.

Required paired structural controls are:

- alter A1 position 0 while changing only nonzero-position label text in the invariant pair;
- add one exact mutating call through a transitive alias of an otherwise admitted A1/flat sequence;
- replace an unshadowed allowlisted sequence consumer with a shadowed callee, then with an unresolved
  project callee;
- replace an A2 constant value with a call;
- replace an A4 authorized path binding with `None`;
- add the A4 helper-body QC row filter without changing the authorized path;
- add one otherwise dead same-name A5 binder;
- replace a bare A5 threshold with the same numeric cell obtained by row destructuring;
- replace A6's closed dtype with a dynamic expression;
- add a second A7 predicate;
- replace the A7 group column with a non-group column in the same bare subscript shape;
- replace `round(P, 4)` with `round(P, -1)`; and
- move a correction-registry spelling from a non-callee position into the callee terminal slot.

Each structural control must change only its named predicate. The detector never reads display
strings' text, table labels, annotation spelling, or surrounding prose. Mutating only the constant
string branches of any retained `IfExp` must also leave its hierarchy reason invariant.

### 9.7 Opened Envelope-10 replay gate

Check in an end-to-end 1.1 replay over all 15 opened E10 cases using their real project snapshots,
contracts, and authorized CSVs. The normative 15-case oracle runs at the public development
**adapter** level, including project inventory and non-`analysis.py` source scanning; only that level
can produce N7's `statistics-api-imported-outside-analysis-py`. It pins the table in section 10,
repeats the run, and requires byte-identical normalized module-evaluation output for all 15. Existing
scored E10 records are read-only and are not rewritten to manufacture 1.1 results.

The answer-visible analyzer harness is a secondary 14-of-15 diagnostic, not the 15-case oracle. It
reproduces the adapter first reason for the other 14 cases. For N7 it sees only `analysis.py` plus the
authorized CSV and therefore cannot observe `make_data.py`; its exact comparison
`list(pipeline["outcome_name"]) == OUTCOMES` is neither membership nor another allowlisted consumer,
so its pinned analyzer-level reason is `analysis-scope-structure-unsupported`. The normative
adapter-level reason remains `statistics-api-imported-outside-analysis-py` because project inventory
owns the earlier wall.

### 9.8 Pinned 1.0-module replay anchor

Advancing the active development binding must not make the E10 baseline uncheckable. A historical
anchor imports the frozen 1.0 components explicitly rather than resolving the active binding, runs
the frozen 1.0 adapter/project-inventory path over all 15 E10 cases, and compares canonical bytes to
the immutable E10 audit at commit `0abb544`. It pins these literal source/artifact digests:

```text
1.0 dataflow:         sha256:44a4ad39dbcb2c37a2b3532bf0dc85c7144199fb71094a312b55ab8ddf900b1a
1.0 adapter:          sha256:3e8b474432d4c1d7ea1471f7dce4aec42dac4921380ebaf5110d978d62e90aa2
1.0 detector:         sha256:76d7ec5c6ca0a44e2a0842adbfac7494af09429f3ddf20ed6a161f3da212124b
historical E10 design bytes: sha256:8adddfaca6729e4cf7e87ba0044c295b848d29eba37ae7003a5a6e4c4888a303
E10 audit results:    sha256:6bfd70dda4d7977b1ad3e1729722179f03381714c7fef74e9781091752ca6b5b
E10 role map:         sha256:ced43841cb53e3527812e6dc5b4e361e635ca77fc7ca64129cae80d5c226c648
E10 envelope manifest: sha256:a0223468c9ee76d07cb5717f975c4a0e34ec9c44ad64f674ea671c14f5020af2
```

The E10 custody records continue to name the historical `8add...` design bytes and are not rewritten
after the Revision-2.3 header correction; the corrected normative-base bytes are the `ac330...`
digest at the top of this document. The anchor asserts the 1.0 identities and 1.0 module-evaluation
bytes; it neither dispatches through the now-1.1 development binding nor regenerates the historical
audit. The 1.0 analyzer-only harness remains a diagnostic and does not substitute for this
adapter-level anchor.

### 9.9 Registry and repository gates

Rerun the 1.0 deterministic 98-file corpus census and exact API compositions unchanged. Run all 98
opened pseudoreplication scripts, 108 dependence-growth cases, 155 regression cases, all qualified
envelope replays, and both registry projections. No existing qualified case lock is rewritten.

Regenerate capability manifests, the scientific registry resource, maturity ledger, source
manifests, and `MANIFEST.sha256` only after behavior tests pass. Then run freshly, after the final file
change:

```text
ruff check .
ruff format --check .
mypy src
pytest
python scripts/validate_starter.py
```

Only counts from that final full run may be reported.

## 10. Expected post-delta outcomes for all Envelope-10 cases

The exact first-reason oracle for the opened replay is adapter-level; section 9.7 defines the
separate 14-of-15 analyzer diagnostic:

| Role | Case ID | Required 1.1 outcome | First retained wall |
|---|---|---|---|
| P1 | `ebbb8a5dbc2664257144` | `authorized-reader-lineage-unavailable` | `csv.DictReader`/record-row value model remains unsupported. |
| P2 | `104493a5d99796a002c0` | `test-battery-cardinality-unresolved` | A2/A4/A5/A7 resolve earlier idioms; `enumerate(DECLARED_OUTCOMES, start=1)` remains outside the exact family factor. |
| P3 | `3ff45fce2a45e0959fdb` | `test-battery-cardinality-unresolved` | A1/A4/A5/A7 resolve earlier idioms; the helper-wrapped family test remains unsupported. |
| P4 | `7296b0e2cf7faeefca64` | `test-battery-cardinality-unresolved` | The helper itself iterates a formal outcome table; no new helper-family cardinality proof is admitted. |
| P5 | `c51d08801b3d0ba4e532` | `analysis-scope-structure-unsupported` | `dict(PRIMARY_OUTCOMES + SECONDARY_OUTCOMES)` nests the concatenation under a call instead of binding its result directly to a fresh name, so the sequence passage is outside the closed read-only allowlist. |
| P6 | `f4cf62caeb8ad68dc5b3` | `analysis-scope-structure-unsupported` | A1 admits `OUTCOMES`; the module-level comprehension-derived `HEADLINE` subset remains refused. |
| N1 | `cb2e207276a0dc3247bb` | `helper-call-site-reentry-unsupported` | Repeated relevant summary/helper sites do not satisfy the closed X4 expansion; mixed-field p collections and scalar casts remain later walls. |
| N2 | `9be74afbe9659bd50580` | `test-battery-cardinality-unresolved` | The direct test/tuple-result battery cannot be reconstructed through all later result/enumeration structure as exactly `N`; local `.pvalue` and Sidak-threshold guards remain behind this wall. |
| N3 | `b787314c170f8f690060` | `test-battery-cardinality-unresolved` | The per-member registered tests remain helper-wrapped; the off-registry correction guard remains available behind this earlier wall. |
| N4 | `60f96fabb7129d662b23` | `extra-registered-test-outside-authorized-family` | The complete family plus sensitivity rerun yields more than `N` conservative instances. |
| N5 | `8d83210468ecde012e4a` | `test-battery-cardinality-unresolved` | The discovery family and data-dependent carried-forward validation loop cannot resolve to exactly `N`. |
| N6 | `4907932548f745afe942` | `authorized-family-test-census-incomplete` | The registered stage-two battery is under a live stage-one branch; the hierarchy guard remains behind this earlier census wall. |
| N7 | `6d2fdc67ab98bc0e0e6e` | `statistics-api-imported-outside-analysis-py` | The opened project still contains the data generator; historical custody is not rewritten. |
| N8 | `dfc9f20a94ecefc7f7b5` | `analysis-scope-structure-unsupported` | `*OUTCOMES` starred unpacking and using `OUTCOMES` as another object's non-integer subscript key are outside the closed read-only allowlist; the later resampling-loop wall is not reached. |
| N9 | `e1bce32a32e3b2df475e` | `test-battery-cardinality-unresolved` | Helper-wrapped per-outcome tests stop before scalar/threshold guards; the A5 Bonferroni product rule is separately isolated. |

All six positives therefore remain abstentions: the full delta admits **0 of 6 E10 positives
end-to-end**. All nine negatives remain non-candidates. The required outcome is not inferred from the
old first reason; the checked-in 1.1 replay must demonstrate each row.

Revision 2 re-verifies every opened source against section 3.1; the result is this complete consumer
audit:

| Role | Bound-sequence consumer audit | Oracle effect |
|---|---|---|
| P1 | No selected authorized-outcome setup sequence enters the new scan; the mutable local record collection supplies no family proof. | Unchanged reader-lineage reason. |
| P2 | `len`, direct-assignment `+`, `enumerate`, and direct iteration are allowlisted read-only uses. | Unchanged order-8 reason. |
| P3 | `len` and direct loop/comprehension iteration are allowlisted. | Unchanged order-8 reason. |
| P4 | The sole user-defined sequence passage uniquely expands through unchanged X4; its formal is directly iterated without mutation or escape. | Passes order 6 but gains no helper-family count; unchanged order-8 reason. |
| P5 | The `PRIMARY_OUTCOMES + SECONDARY_OUTCOMES` result is nested in `dict(...)`, not directly bound as the allowlist requires. | Corrected from order 8 to `analysis-scope-structure-unsupported`. |
| P6 | `OUTCOMES[:3]` is a slice, not an integer-index read, and feeds a comprehension-derived subset. | Existing `analysis-scope-structure-unsupported` unchanged. |
| N1 | Direct loop/comprehension iteration is allowlisted. | Unchanged helper-reentry reason. |
| N2 | `len` and direct comprehension iteration are allowlisted. | Unchanged order-8 reason. |
| N3 | `zip` and direct comprehension iteration are allowlisted but add no family proof. | Unchanged order-8 reason. |
| N4 | `sorted` and direct loop/comprehension iteration are allowlisted. | Unchanged extra-test reason. |
| N5 | `set`, direct loop/comprehension iteration, and f-string payload use are allowlisted. | Unchanged order-8 reason. |
| N6 | `len` and direct loop/comprehension iteration are allowlisted. | Unchanged incomplete-census reason. |
| N7 | Fresh direct-assignment `+`, direct iteration, `sorted`, and formatting uses are allowlisted, but equality against the whole sequence is not. | Adapter-level statistics-import reason unchanged; analyzer-only diagnostic corrected to `analysis-scope-structure-unsupported`. |
| N8 | Starred unpacking and passage as another object's non-integer subscript key are not allowlisted. | Corrected from order 8 to `analysis-scope-structure-unsupported`. |
| N9 | Direct loop/comprehension iteration is allowlisted. | Unchanged order-8 reason. |

Thus 13 rows retain their Revision-1 first reason and P5/N8 are corrected to the earlier honest scope
reason. No role becomes a candidate.

The nine recon idiom walls and the final collection wall explain that result:

| Positive | W1 table | W2 helper reader | W3 named alpha | W4 ternary (no admission) | W5 float/round | W6 bool mask | W7 helper test | W8 enumerate/zip | W9 astype | Deferred collection / actual first wall |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | n/a | retained `DictReader` variant | A5-capable | assigned ternary retained | p lineage not direct | retained record-row filters | n/a | n/a | n/a | reader unavailable |
| P2 | A2 | A4 | A5 | assigned ternary retained | n/a | A7 | n/a | retained | n/a | cardinality at W8 |
| P3 | A1 | A4 | A5 | assigned ternary retained | relabeled abstention behind W7 | A7 | retained | output-only wrapper | n/a | cardinality at W7 |
| P4 | A1 | direct reader | A5-capable after proof | container/assigned verdict retained | relabeled behind W7 | A7 | retained | output-only wrapper | n/a | cardinality at W7 |
| P5 | A1 syntax parses, but nested-call concatenation escapes | not reached | not reached | not reached | not reached | not reached | not reached | not reached | not reached | scope wall at read-only-consumer closure |
| P6 | A1 | A4 | A5 | assigned/container verdict retained | relabeled behind scope | already `.loc` | retained | n/a | A6 | derived `HEADLINE` scope wall |

“A5-capable” does not claim later reachability; it means the named literal itself is within A5 if
earlier retained walls are independently removed. Envelope 11 still measures first contact on fresh
cases regardless of these opened-case expectations.

The full delta therefore admits none of the six opened E10 positives end-to-end. This is expected:
all six use the assigned verdict form that the deleted design already refused (some later flow
through helpers or containers), and the exact direct-sink form occurs zero times among the corpus's
25 `IfExp` nodes. Envelope 11 nevertheless measures first contact on fresh authors and fresh cases,
without treating the E10 wall profile as a target style.

## 11. Envelope-11 protocol

Envelope 11 is a fresh, class-pure envelope with six blind multiple-testing positives and nine blind
negatives. Authors and custodian are isolated from detector grammar, API registries, wording, E10
source, recon mutations, expected reasons, and analyzer output. Roles, prompts, closure, exact
counterevidence responsibilities, and digest chronology are frozen before first detector contact.

The abstract P1-P6 and N1-N9 role definitions are inherited by value from 1.0 section 11, including
the default-method correction, hand-Sidak, off-registry correction, sensitivity duplicate,
discovery/validation, joint gate, upstream-adjusted-p, maxT, and product-rule negative roles. All
code, data, names, layout, helper choices, and scientific scenarios are fresh. N7's custody is changed
only as section 11.1 requires; its upstream correction is not placed in the audited source tree.

The hard stops are the same as 1.0 section 11, with the class window advanced:

- zero negative candidates (`0/9`);
- zero Findings anywhere, including development cases and every ordinary qualified/regression
  surface;
- byte-identical replay for all 15 E11 cases; and
- zero false accusations in all available class-specific blind cases until 36 exist, then zero in
  the latest 36.

Lifetime class-specific false accusations are reported separately. Every negative records all roles
actually realized, its designed first guard, secondary guards, and the number and exact structural
shapes of family-C analogue negatives. A disputed role is recorded as disputed; it is never silently
reclassified to improve a score.

First-contact recall is reported as positive candidates over six, with every miss and exact first
reason, and has no pass gate. The running class-specific recall tally and trailing-18 requirement
begin only when 18 blind multiple-testing positives exist. E10 contributes six and E11 contributes
six, so E11 alone does not activate that threshold. Fresh E11 results are reported regardless of the
0/6 E10 end-to-end expectation in section 10.

### 11.1 Data-author custody change

Data authors generate or simulate inputs outside the audited `project/` tree. `make_data.py`, a
notebook, shell/R/Python generator, source data, generator environment, and any other generation
artifact must never be copied into `project/` or included in its repository snapshot. The audited
project receives only the frozen final input files that its contract authorizes, the analysis and
ordinary project artifacts permitted by the role, and no hidden generation dependency.

The custodian records the generator and its digest in a separate custody area outside `project/`,
records the final input digest before copying it into the case, inventories `project/` recursively,
and proves the audit snapshot excludes every generator artifact. The detector is not told which file
was a generator and does not relax its outside-`analysis.py` statistics-import census. For an
upstream-adjusted-p negative like N7, any statistics code that created the frozen upstream table is
therefore outside the audited project, while `analysis.py` and its actual accepted readers remain
subject to the unchanged local-lineage and reader guards.

The blind briefing must not hint that authors should avoid assumption checks, simplify helpers, use
specific readers, avoid named constants, inline verdicts, or otherwise conform to the recognizer.

Passing Envelope 11 installs no grant, pin, qualification, production capability, or wording change.

## 12. Reuse and file-by-file build list

### 12.1 Copy/reuse map

| Surface | 1.1 decision |
|---|---|
| 1.0 multiple-testing dataflow/adapter/detector | Copy to new `_v1_1` modules, then apply only this delta. Do not edit the 1.0 files. |
| `code_csv_dependence_dataflow_v3_1.py` and all other dependence dataflow modules | Do not edit. A4 deliberately does not import or copy the sibling's `None` tolerance. |
| 1.0 correction registries, terminal census, manual grammar, threshold/product guard, statistics-prefix registry, resampling and extremum guards | Copy by value; semantic-differential tests enforce unchanged coverage. |
| 1.0 row model and `_mask_rows` value grammar | Copy by value. A7 supplies only the exact same-frame boolean-subscript route into that proof. |
| 1.0 hierarchy registry and `_hierarchy_guard` | Copy byte-for-byte. Add no exception, skip, caller bypass, or semantic change. |
| Contract profile 1.2.0 and lifecycle | Reuse without edits. |
| Finding wording profile v1 | Reuse the exact object and digest; do not create v2. |
| Qualified pseudoreplication/complete-domain surfaces and grant pins | Byte-untouched. |

### 12.2 Planned file changes

| File or surface | Planned change |
|---|---|
| New accepted `docs/implementation/ADR-0078-...md` (final number/title assigned before build) | Authorize only the 1.1 identities, A1-A7 grammars, the inherited-flat-sequence mutation fix, relabels, deferred ternary decision, E11 custody/protocol, candidate-surface review, and isolation requirements. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v1_1.py` | Copy the frozen 1.0 module and implement sections 3-6. Do not import private dependence helpers. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v1_1.py` | Copy the 1.0 adapter, set check/adapter `1.1.0`, freeze the exact 1.1 reason set, and retain the observation/fact schema. |
| New `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v1_1.py` | Copy the detector wrapper, set version/entry point `1.1.0`, and retain all four exact guards and operand registry. |
| New `src/sc_referee/scientific_checks/integration_multiple_testing_v1_1.py` | Version the development compilation overlay for the 1.1 observation types without changing the shared qualified compiler. |
| `src/sc_referee/scientific_checks/profiles.py` | Replace only the active development MT module/binding with version 1.1 and retain ordinary/qualified projections unchanged. |
| `src/sc_referee/detectors/method_conflict_registry.py` | Register detector 1.1 alongside historical 1.0 manifest support and dispatch the active development binding exactly. |
| `src/sc_referee/detectors/method_conflict_finding.py` | Permit the exact MT 1.1 development binding to reuse the byte-identical wording v1 object; do not edit that object or any pseudoreplication wording. |
| Development-lane controller dispatch | Select the versioned 1.1 integration overlay only for the development registry. The ordinary controller path remains unchanged. |
| Detector/scientific-check capability manifests and scientific registry resource | Add/freeze 1.1 component manifests, retain historical 1.0 detector material needed for locked validation, and point only the development binding to 1.1. |
| New `tests/test_code_csv_multiple_testing_dataflow_v1_1.py` | Execute all admission, immutable-sequence, unchanged-hierarchy, reason, guard, FA, PROBE/NEGSIM, and ladder matrices. |
| New adapter/detector/integration tests | Pin 1.1 identities, digests, schemas, error guards, candidate projection, and no-Finding ceiling. |
| New `tests/test_multiple_testing_e10_replay_v1_1.py` | Execute all 15 opened cases at adapter level and assert section 10 plus deterministic repeat bytes; separately pin the 14-of-15 analyzer diagnostic and N7 split. |
| New historical 1.0 replay-anchor test | Import the frozen 1.0 modules explicitly, pin the section-9.8 source/artifact digests, and replay the immutable E10 adapter baseline without using the active development binding. |
| Prose-tripwire tests | Add every section-9.6 predicate and paired structural control. |
| Registry/isolation/regression tests | Rerun two-registry non-derivation, qualified byte invariance, old contract goldens, opened corpora, and corpus census. |
| `evaluation/development/multitest-code-slice-v1_1/` | Store answer-visible canonical fixtures and expected first outcomes only; never treat them as blind qualification evidence. |
| Future `evaluation/development/blind-envelope-11-.../` | Implement section 11 after answer-visible gates pass; keep generation artifacts outside every case `project/`. |
| `CAPABILITY_MATURITY_LEDGER.json`, source manifests, `MANIFEST.sha256` | Regenerate deterministically after final source/test changes and before the final full suite. |

The 1.0 dataflow, adapter, detector, design, ADR-0077, and E10 audit results are not edited during the
build. If repository architecture cannot retain historical detector-manifest validation while the
development binding advances, implementation stops and records a design/registry conflict; it does
not overwrite the 1.0 identity.

## 13. Build acceptance checklist

The 1.1 build is acceptable only if:

1. an accepted ADR authorizes this exact delta before behavior changes;
2. every A1-A7 clause and every refused near miss is implemented with no fallback;
3. `_hierarchy_guard` is byte-unchanged, there is no ternary subtraction, and all hierarchy/control
   fixtures retain their 1.0 outcomes;
4. every recon `PROBE`, every `NEGSIM`, and every P2/P3 ladder file executes through the analyzer
   with section-9 outcomes;
5. all 15 E10 projects execute through the 1.1 adapter with section-10 outcomes and byte-identical
   repeat output; the analyzer diagnostic matches 14 and records the exact N7 level split;
6. the closed reason registry equals real emitters plus the documented-unreachable annex;
7. correction-terminal coverage is identical, off-grammar blocked-node coverage never shrinks, and
   row completeness admits only exact group-row equality;
8. A5 counts every binding anywhere, uses source-text Decimal construction, and the hand-Bonferroni
   rebinding fixture never becomes a candidate;
9. both A1 and inherited flat sequences pass the whole-module mutation/alias/escape scan, with every
   section-9.2 refused consumer stopping before census and every allowlisted read-only consumer
   preserving its independently determined baseline outcome;
10. contract 1.2.0, wording v1, all 1.0/1.1 contract goldens, and 1.0 source modules remain unchanged,
    and the pinned 1.0 E10 adapter replay anchor passes independently of the active binding;
11. the ordinary registry contains no MT code binding and the development registry contains exactly
    one active 1.1 binding;
12. every qualified pseudoreplication and complete-domain identity, grant, pin, qualification,
    wording byte, Finding byte, and replay outcome is invariant, with explicit lane-digest
    non-derivation;
13. the prose tripwire covers every new predicate and passes all paired structural controls;
14. Envelope 11 uses external data-generation custody and retains the no-recall-gate protocol; and
15. every repository-required validation command passes after the final file change.

Any failure of the E10 replay oracle, guard differentials, closed-reason equality, contract goldens,
or two-registry isolation is a design regression. The implementation must stop and report it rather
than broaden an admission or weaken a guard.

## 14. Revision 1 changelog

Revision 1 starts from the original design digest
`sha256:655cf3a4411d95651a32797ee3314d53b894713b174009e13662a47bb836c2dc`.
Every behavioral edit below narrows candidate eligibility or preserves a guard; the remaining edits
close definitions, pin first reasons, or strengthen executable gates. No correction, off-grammar,
hierarchy, or row-completeness guard is weakened.

| Review item | Sections changed | Revision 1 disposition |
|---|---|---|
| BL-1 | 1, 3.1, 6, 8, 9.2, 9.5, 9.6, 12, 13 | Added a whole-module mutation/alias/rebinding/deletion/store/escape refusal for A1 and the inherited flat-sequence route. Enumerated all nine mutating attributes and required per-shape plus alias fixtures. Named the inherited-flat-sequence mutation fix in the delta and ADR plan. |
| MJ-1 | 1, 2.3, 7, 8, 9.1, 9.3, 9.5, 9.6, 10, 12, 13 | Deleted the verdict-ternary carve-out in full. `_hierarchy_guard` is byte-unchanged; the zero-of-25 observed exact-shape evidence, guards-before-recall rationale, `0/6` E10 expectation, and fresh-E11 measurement are explicit. |
| MJ-2 | deleted section 4; 6, 9.3 | Removed all former sink-parent, branch, and sole-control exception conditions with the carve-out. No residual ternary admission remains. |
| MJ-3 | 3.5, 8, 9.2, 9.6 | Declared destructured or literal-subscripted row constants ineligible as bare/A5 thresholds and pinned the per-outcome threshold-table fixture to `unresolved-decision-threshold`. |
| MJ-4 | 9.7, 10, 13.5 | Made the 15-case E10 replay an adapter-level oracle; limited the analyzer diagnostic to 14 matching cases and pinned N7's intentional `additional-accepted-reader-present` versus `statistics-api-imported-outside-analysis-py` split. |
| MJ-5 | 3.4, 8, 9.2, 9.6 | Limited A4 to path-slot resolution, prohibited construction of a call-site frame, retained unchanged X4 frame lineage, and added the helper-return QC-filter negative. |
| MJ-6 | 8, 9.1, 13.4 | Added executable `NEGSIM_A/B/C` gates with exact post-delta reasons; only direct-`float(P)` `NEGSIM_C` moves to the honest scalar-cast reason. |
| Minor 1 | 3.6 | Required row selection around A6 to pass an unchanged 1.0 selection route or A7 before completeness equality. |
| Minor 2 | 3.5, 9.2 | Defined concrete `ast.alias` binding names for `import` and `from ... import`, including `asname`, and retained refusal of wildcard/unresolved imports. |
| Minor 3 | 5.2, 8, 9.5, 9.6 | Pinned `round(P, -1)` outside the honest-relabel grammar because its precision is `UnaryOp`, with exact reason `unresolved-manual-correction-present`. |
| Minor 4 | 3.5, 8, 9.2 | Added the census-only module/local `ALPHA` hand-Bonferroni spelling and pinned it to `unresolved-decision-threshold`. |
| Minor 5 | 3.1, 8, 9.2 | Split the non-position-0 factor case (order 8, `test-battery-cardinality-unresolved`) from the independently censused wrong operand slot (order 10, `test-operand-lineage-unresolved`), with no disjunctive oracle. |
| Minor 6 | 9.8, 12, 13.10 | Added an active-binding-independent 1.0 E10 adapter replay anchor with literal 1.0 source and historical artifact digests. |
| Minor 7 | normative-base header and 1.0 design header | Corrected the base design's revision label to 2.3 and updated its pinned digest after that documentation-only correction. |
| Minor 8 | 3.7, 8, 9.2, 9.6 | Restricted A7 to the contract group-column comparison and barred its bare boolean-subscript path from `_mask_rows`' permissive non-group branch. |

## 15. Revision 2 changelog

Revision 2 starts from the Revision-1 design digest
`sha256:2e2aa08afaf6572b03f0827e90c7b141560a5e7751ce265e0c004ce00998d109`.
It removes only Revision 1's unintended refusal of a closed set of read-only sequence consumers.
Every mutation, alias mutation, rebinding, store, deletion, unresolved project-callee passage, and
family-proof restriction remains intact.

| Review item | Sections changed | Revision 2 disposition |
|---|---|---|
| ND-1 | 3.1, 6, 8, 9.1, 9.2, 9.4, 9.5, 9.6, 9.7, 10, 13, 15 | Replaced the open-ended call-argument escape rule with the exact by-value allowlist for unshadowed `len`/`enumerate`/`zip`/`sorted`/`set`/`tuple`/`list`/`reversed`/`sum`/`min`/`max`, membership, direct iteration, integer-index reads, fresh direct-bound `+` concatenation, and formatting payloads. Kept user-defined callees refused unless unchanged X4 proves their formal path. Re-verified all 12 section-9.1 PROBE rows and every section-9.4 ladder rung unchanged; re-verified all 15 opened E10 adapter rows, retaining 13 and correcting P5/N8 to `analysis-scope-structure-unsupported`; corrected N7's analyzer-only diagnostic to that scope reason while preserving its adapter oracle. |
