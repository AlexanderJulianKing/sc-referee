# Multiple-testing code slice 1.1 delta design — 2026-08-25

**Status:** build-ready delta design; design and documentation only in this session

**Version:** detector/check/adapter `1.1.0`, development lane only

**Normative base:**
[`MULTITEST-CODE-SLICE-1.0-DESIGN-2026-08-24.md`](MULTITEST-CODE-SLICE-1.0-DESIGN-2026-08-24.md),
Revision 2.3, `sha256:8adddfaca6729e4cf7e87ba0044c295b848d29eba37ae7003a5a6e4c4888a303`

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
labels honest, admit one exact display-only ternary, and retain every correction, hierarchy,
resampling, locality, and row-completeness safety wall outside those forms.

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
3. `_hierarchy_guard` retains every 1.0 control node and residual execution-prevention edge. It
   subtracts only the exact display `IfExp` proved by section 4; every nonmatching or unresolved
   control form still abstains.
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
new accepted ADR before behavior changes. It must record these closed admissions, the exact ternary
exception, the two relabels, the Envelope-11 protocol, and the preserved guard invariants. It must not
amend or reinterpret ADR-0077, any qualified grant, or any GrantPin.

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

No wording v2 is needed. A1-A7 and the ternary exception resolve only existing slots:
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
4. the outer target is one simple module binding admitted by A3/ordinary `Assign` rules.

The resolver stores the rows and container kinds immutably. It does not flatten all cells into a
family. A table proves an exact contract-outcome factor only when all rows have one common arity, the
iteration target is a list/tuple of that arity containing distinct simple `Name` stores and no
`Starred`, and the ordered position-0 projection is byte-for-byte equal to the ordered contract
outcome list. The factor is exactly `N`; the remaining positions bind their row constants for that
expanded member but never identify the family.

Only a direct iteration over the bound table name is admitted for family expansion. `enumerate`,
`zip`, slicing, concatenation, `sorted`, `reversed`, a comprehension-derived iterable, a table alias
whose identity is unresolved, a reordered/set-equal projection, or any position other than zero
returns `test-battery-cardinality-unresolved`. A position-0 projection unequal to the contract cannot
prove a family; if calls otherwise resolve, operand/family mapping still returns
`test-operand-lineage-unresolved`.

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

A4 resolves only the path slot. It does not inline the helper as proof of test calls, data selection,
or p-value lineage.

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
function, async function, and lambda; import aliases; function and class names in the enclosing
scope; `ExceptHandler.name`; and every `MatchAs.name`, `MatchStar.name`, and `MatchMapping.rest`
capture. A same-name `global`, `nonlocal`, or `Del` occurrence disqualifies the admission. Bindings in
literal-false branches, uncalled helpers, handlers, match cases, and nested scopes still count. The
census never ignores a binding because it is a `BinOp` or appears unreachable.

The Decimal is constructed from the literal's source token text after removal of permitted numeric
underscores. If source text is unavailable, use `Decimal(repr(value))`; `Decimal(float)` is forbidden.
The conventional-literal product rule then computes `literal * Decimal(N)` exactly and abstains
`unresolved-decision-threshold` when that product is one of `0.01`, `0.05`, or `0.1`. Any second
binding, dynamic RHS, arithmetic threshold, attribute, subscript, call, alias chain, missing source
identity, or off-set value returns `unresolved-decision-threshold`, unless the unsupported module
statement necessarily stops earlier with `analysis-scope-structure-unsupported`.

Thus a module-level `ALPHA = 0.05` may be admitted, while
`ALPHA = ALPHA / len(OUTCOMES)` is never silently ignored. The latter script must abstain, including
when it implements a correct hand Bonferroni threshold; it can never become a candidate.

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
section 3.7 and the unchanged completeness equality.

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

## 4. Exact verdict-ternary carve-out

### 4.1 Admitted AST and parent shape

The hierarchy guard may exempt one `ast.IfExp.test` for a family position only when every condition
below is proved after closed loop and X4 expansion:

1. The node is exactly `ast.IfExp(test=COMPARE, body=BODY, orelse=ORELSE)`.
2. `BODY` and `ORELSE` are direct `ast.Constant` nodes whose values have type `str`. Their bytes are
   never read, matched, compared, interpreted, or used as evidence.
3. `COMPARE` is one `ast.Compare` with one operator from `Lt`, `LtE`, `Gt`, or `GtE`, one comparator,
   and reversed operand order permitted. Exactly one side resolves through the order-12 graph to the
   direct local registered `.pvalue` member for one family position; the other side passes the
   order-15 literal or A5 threshold grammar.
4. The `IfExp` is either the complete payload argument of one existing 1.0 `p_result_eligible` sink,
   or it is exactly the `FormattedValue.value` of one direct `FormattedValue` with
   `conversion == -1` and no `format_spec`, inside the payload's root `JoinedStr`. No assignment,
   return, container, subscript, call, `.format`, concatenation, boolean wrapper, nested ternary, or
   other parent lies between the `IfExp` and the sink payload.
5. The sink call is one emission of that same member's conclusion. The comparison's sole control
   effect is choosing `BODY` versus `ORELSE`; it does not determine whether the sink executes, which
   sink is called, which member is emitted, or whether another argument is evaluated.
6. That family position participates in no second p-controlled emission branch. The same p-value may
   appear as an ordinary non-control payload, but no other `IfExp`, `If`, match, short-circuit, or
   conditional sink path may use it.
7. The p-value does not control a registered test, correction call, family-container insertion,
   family membership, conclusion threshold other than this comparison, or any other node enumerated
   by the 1.0 hierarchy/control guard.
8. Parentage, p origin, family position, threshold, sink eligibility, single-emission identity, and
   absence of other control effects all resolve uniquely within the inherited bounds.

The comparison remains the member's p-derived conclusion and contributes the existing `conclusion`
and `output_sink` evidence spans. The carve-out removes only this one `IfExp.test` from the hierarchy
failure set; it does not remove the p-value from control tracking globally.

### 4.2 Refused near misses and reason precedence

An assigned ternary such as `verdict = "yes" if P < ALPHA else "no"` remains
`hierarchical-gatekeeping-present`, even if `verdict` is printed later. So do a ternary returned from
a helper, placed in a container, nested in a `.format` call, used as a sink selector, or embedded in
a second emission branch. Non-string branches, a non-direct p-value, reject/adjusted flags, a compound
comparison, a boolean test, nested calls, and any branch that executes code are not admitted.

A uniquely resolved near miss returns `hierarchical-gatekeeping-present`. If the analyzer cannot
resolve whether the p-derived value can prevent or select an enumerated control/emission node, the
existing residual returns `pvalue-control-dependence-unresolved`. Source position does not choose
between these reasons.

The required negative matrix proves that a p-value gating another registered test, a correction, a
family container, or a second emission branch always abstains. A sink-local constant-string choice is
the entire exception; there is no general “display code” exception.

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
| 6 | Apply A1-A3 while choosing setup/scope and resolving constants. Relabel only the raw chosen-scope failure. Run the syntax-wide A5 binding census as metadata; it supplies no value until order 15. | `analysis-scope-structure-unsupported`; unchanged `api-resolution-ambiguous` and X4 reasons |
| 7 | Apply A4 to the one-reader full-scope census. | unchanged `additional-accepted-reader-present`; `authorized-reader-lineage-unavailable` |
| 8 | Allow A1's exact position-0 table projection to supply factor `N`; no wrapper or subset admission. | unchanged call-census reasons |
| 10 | Apply A6 and A7 while resolving each registered call's two operands. | unchanged `test-operand-lineage-unresolved` |
| 11 | Compare A7's selected rows to the exact authorized group rows. | unchanged `selected-group-row-completeness-unproven` |
| 14 | Relabel only the exact direct-`P` builtin scalar shapes in section 5.2. All blocked nodes remain blocked. | new `pvalue-scalar-cast-or-rounding-unsupported`; otherwise unchanged correction reasons |
| 15 | Apply A5 to a direct named comparison operand, then the unchanged exact-Decimal product rule. Direct-`P` comparisons remain exclusive to this order. | unchanged `unresolved-decision-threshold` |
| 16 | Exempt only the fully proved section-4 `IfExp.test` from hierarchy. Run every other hierarchy, partition, resampling, and statistics-prefix clause unchanged. | unchanged hierarchy/control reasons |

No admission changes first-reason precedence. For example, an A1 table around an `enumerate` family
still stops at order 8, an exact `float(P)` still stops at order 14 even if a later correction is
complete, and the named threshold product rule still precedes the display-ternary exception.

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

The accepted 1.0 BL-1 residual also remains: the product rule recognizes only conventional family
alphas in `{0.01, 0.05, 0.1}` and does not infer an arbitrary family alpha.

## 8. False-accusation analysis and adversarial fixtures

Every fixture below is a complete authorized-family project with real CSV bytes and a real 1.2
contract. Tests invoke the public 1.1 analyzer/adapter; a direct helper-unit result is insufficient.

| Change | False-accusation vector | Required adversarial correct-analysis fixture and outcome |
|---|---|---|
| A1 nested table | Treating any table position, reordering, slice, or wrapper as the contract family could establish the wrong `N` calls. | `correct-nested-table-nonzero-outcome-slot`: a family loop uses position 1 while position 0 is not the ordered contract; abstain exactly `test-battery-cardinality-unresolved`, never candidate. |
| A2 constant dict | Treating dictionary keys/order as family authority or ignoring mutation could manufacture a battery. | `correct-constant-dict-mutation-not-setup-proof`: a literal label map is mutated before use and a complete correction follows; abstain `analysis-scope-structure-unsupported`, never classify `none`. |
| A3 AnnAssign | Accepting annotation computation or a dynamic RHS could hide a constructed family. | `correct-annotated-dynamic-family-builder`: annotated `OUTCOMES` has a call/comprehension RHS and a complete correction; abstain `analysis-scope-structure-unsupported`. |
| A4 helper path | Treating unresolved/`None` helper readers as possibly authorized could bind a different CSV. | `correct-helper-reader-none-default` and `correct-helper-reader-mixed-paths`: one uses a `None` default and one has two call-site paths; both abstain `authorized-reader-lineage-unavailable`. |
| A5 named alpha | Ignoring a second binding can convict hand Bonferroni code as uncorrected. | `correct-hand-bonferroni-alpha-rebinding`: `ALPHA = 0.05; ALPHA = ALPHA / len(OUTCOMES)` with complete-family direct decisions; abstain `analysis-scope-structure-unsupported` or `unresolved-decision-threshold`, never candidate. `correct-alpha-shadowed-helper-parameter` separately reaches the syntax-wide census and must return `unresolved-decision-threshold`. |
| A6 `.astype` | Treating a cast chain as row-preserving could hide row deletion or a different selection. | `correct-astype-after-additional-row-mask`: a structurally visible stage mask precedes the cast and a complete correction follows; abstain exactly `selected-group-row-completeness-unproven`. |
| A7 boolean mask | Equating any boolean subscript with a complete group admits discovery/validation or combined masks. | `correct-boolean-mask-discovery-validation`: group equality is combined with a stage mask; abstain `selected-group-row-completeness-unproven`. A cross-frame mask fixture must abstain `test-operand-lineage-unresolved`. |
| Display ternary | A p-value branch can gate tests, corrections, containers, or multiple emissions rather than merely select one string. | `correct-ternary-gates-registered-test` stops at the earlier order-8 `authorized-family-test-census-incomplete`; `correct-ternary-gates-correction`, `correct-ternary-gates-family-container`, and `correct-ternary-second-emission-branch` reach `hierarchical-gatekeeping-present`; an unresolved parent/control edge returns `pvalue-control-dependence-unresolved`. A guard-level assertion separately proves the registered-test control remains in the hierarchy registry even though order 8 owns its outward reason. |
| Scope relabel | Relabeling could accidentally hide true import/API ambiguity. | `unsupported-module-comprehension-scope` returns `analysis-scope-structure-unsupported`; `ambiguous-statistics-alias` still returns `api-resolution-ambiguous`. |
| Scalar relabel | Broadly treating casts as harmless could admit arithmetic correction or transformed decisions. | `correct-hand-bonferroni-inside-float` retains `unresolved-manual-correction-present`; isolated direct `float(P)` and `round(P, 4)` return only `pvalue-scalar-cast-or-rounding-unsupported`. |

The build also reruns every 1.0 per-guard adversarial fixture unchanged, including hand Sidak,
off-registry correction, default-method `multipletests`, sensitivity duplicate,
discovery/validation split, all-NumPy omnibus/assert gates, and label-permutation maxT.

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

Add `PROBE_annassign.py` as the A3 isolated candidate and
`PROBE_inline_sink_ternary.py` as the exact section-4 candidate. Each candidate must contain facts
for exactly `N` calls, all `N` conclusion positions, the unchanged registered sink kind, and no
correction positions.

### 9.2 Admission and binder matrices

For A1, cross product list/tuple outer and list/tuple rows, arities 1 and 8, outer lengths 1 and 16,
all scalar kinds, tuple/list target destructuring, and exact position-0 equality. Refuse zero/17
rows, zero/9 cells, ragged family expansion, complex/nonfinite/oversize/NUL strings, nesting,
starred targets, duplicate targets, position-1 family use, slice/reorder, `enumerate`, and `zip`.

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
must abstain.

For A5, cover all four operators in both operand orders, each admitted literal spelling including
source exponents/underscores, all conventional product-rule hits, and every syntax-wide binding kind
listed in section 3.5. The source-Decimal test must distinguish `Decimal("0.01") * 5` from a
`Decimal(float)` path and fail if the latter is used. The BinOp rebinding and same-name helper
parameter fixtures must execute the analyzer and must never produce facts.

For A6, cover four unshadowed builtin dtypes, closed string dtypes, `.astype(...).to_numpy()`, and
every refused arity/keyword/dynamic/shadowed/frame/row-changing form. For A7, cover direct and aliased
frames, comparison reversal, both derived group values, exact row equality, and every refused mask
operator/composition/cross-frame/stage/subset form.

### 9.3 Exact ternary matrix

Positive tests cover a direct sink argument and the one admitted f-string ancestry for each 1.0
`p_result_eligible` sink kind. They cover all four comparison operators, reversed operands, bare and
A5 thresholds, and all family positions. String contents are varied without changing outcomes; no
test may search them for “significant” or any synonym.

Negative tests independently vary one clause: assigned name, returned value, container insertion,
`.format`, concatenation, format conversion/specification, non-string branch, nested ternary, compound
comparison, BoolOp, adjusted/reject origin, two family origins, second branch sink, sink selection,
conditional sink execution, test/correction argument, and unresolved parent. Each asserts the exact
first reason prescribed in section 8; the registered-test case also asserts the retained guard
classification behind its earlier census stop. The original `PROBE_ternary.py` is the assigned-name
negative and must not be altered into the admitted shape.

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
4. Differentially generate hierarchy controls. Every 1.0 hierarchy/control abstention remains one
   except the exact section-4 shape. Any single structural mutation away from that shape returns to
   hierarchy/control abstention.
5. Differentially generate row masks. The selected row set admitted by A7 must equal one complete
   derived group set; no strict subset accepted by 1.1 may have been refused by the 1.0 equality
   predicate.
6. Pin check/adapter/detector identity `1.1.0`, every detector `ValueError` guard, including an
   out-of-registry operand, and development no-Finding behavior.

### 9.6 Prose tripwire

Extend the 1.0 prose tripwire over every branch introduced or changed here: A1 row/table parsing and
position-0 projection; A2 dict/collision/lookup; A3 target/RHS/annotation grammar; A4 actual/formal/
default path binding; A5 syntax-wide binding census, source-Decimal construction, and product rule;
A6 dtype closure; A7 same-frame mask and row equality; exact ternary parent/control/sink proof; scope
relabel; and scalar-transform relabel.

For every new positive and adversarial fixture, mutate comments, docstrings, Markdown, reports, task
text, unrelated strings, output labels, format text, and non-callee identifiers. Add and remove report
and Markdown files. Rename non-callee identifiers to `bonferroni`, `holm`, `sidak`, and
`benjamini_hochberg`. Facts, first reasons, and candidate classification remain invariant under the
same normalization used by the 1.0 tripwire.

Required paired structural controls are:

- alter A1 position 0 while changing only nonzero-position label text in the invariant pair;
- replace an A2 constant value with a call;
- replace an A4 authorized path binding with `None`;
- add one otherwise dead same-name A5 binder;
- replace A6's closed dtype with a dynamic expression;
- add a second A7 predicate;
- replace one ternary branch's node type from string `Constant` to a non-string `Constant`; and
- move a correction-like identifier from a non-callee position into the callee terminal slot.

Each structural control must change only its named predicate. The detector never reads the display
strings' text, table labels, annotation spelling, or surrounding prose.

### 9.7 Opened Envelope-10 replay gate

Check in an end-to-end 1.1 replay over all 15 opened E10 cases using their real project snapshots,
contracts, and authorized CSVs. It invokes the public development analyzer/adapter, not an internal
predicate, and pins the table in section 10. It then repeats the run and requires byte-identical
normalized module-evaluation output for all 15. Existing scored E10 records are read-only and are not
rewritten to manufacture 1.1 results.

### 9.8 Registry and repository gates

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

The exact first-reason oracle for the opened replay is:

| Role | Case ID | Required 1.1 outcome | First retained wall |
|---|---|---|---|
| P1 | `ebbb8a5dbc2664257144` | `authorized-reader-lineage-unavailable` | `csv.DictReader`/record-row value model remains unsupported. |
| P2 | `104493a5d99796a002c0` | `test-battery-cardinality-unresolved` | A2/A4/A5/A7 resolve earlier idioms; `enumerate(DECLARED_OUTCOMES, start=1)` remains outside the exact family factor. |
| P3 | `3ff45fce2a45e0959fdb` | `test-battery-cardinality-unresolved` | A1/A4/A5/A7 resolve earlier idioms; the helper-wrapped family test remains unsupported. |
| P4 | `7296b0e2cf7faeefca64` | `test-battery-cardinality-unresolved` | The helper itself iterates a formal outcome table; no new helper-family cardinality proof is admitted. |
| P5 | `c51d08801b3d0ba4e532` | `test-battery-cardinality-unresolved` | Primary/secondary subset comprehensions and helper-wrapped tests do not equal one exact contract-family iteration. |
| P6 | `f4cf62caeb8ad68dc5b3` | `analysis-scope-structure-unsupported` | A1 admits `OUTCOMES`; the module-level comprehension-derived `HEADLINE` subset remains refused. |
| N1 | `cb2e207276a0dc3247bb` | `helper-call-site-reentry-unsupported` | Repeated relevant summary/helper sites do not satisfy the closed X4 expansion; mixed-field p collections and scalar casts remain later walls. |
| N2 | `9be74afbe9659bd50580` | `test-battery-cardinality-unresolved` | The direct test/tuple-result battery cannot be reconstructed through all later result/enumeration structure as exactly `N`; local `.pvalue` and Sidak-threshold guards remain behind this wall. |
| N3 | `b787314c170f8f690060` | `test-battery-cardinality-unresolved` | The per-member registered tests remain helper-wrapped; the off-registry correction guard remains available behind this earlier wall. |
| N4 | `60f96fabb7129d662b23` | `extra-registered-test-outside-authorized-family` | The complete family plus sensitivity rerun yields more than `N` conservative instances. |
| N5 | `8d83210468ecde012e4a` | `test-battery-cardinality-unresolved` | The discovery family and data-dependent carried-forward validation loop cannot resolve to exactly `N`. |
| N6 | `4907932548f745afe942` | `authorized-family-test-census-incomplete` | The registered stage-two battery is under a live stage-one branch; the hierarchy guard remains behind this earlier census wall. |
| N7 | `6d2fdc67ab98bc0e0e6e` | `statistics-api-imported-outside-analysis-py` | The opened project still contains the data generator; historical custody is not rewritten. |
| N8 | `dfc9f20a94ecefc7f7b5` | `test-battery-cardinality-unresolved` | Resampling-loop family calls are not unrolled. |
| N9 | `e1bce32a32e3b2df475e` | `test-battery-cardinality-unresolved` | Helper-wrapped per-outcome tests stop before scalar/threshold guards; the A5 Bonferroni product rule is separately isolated. |

All six positives therefore remain abstentions: the full delta admits **0 of 6 E10 positives
end-to-end**. All nine negatives remain non-candidates. The required outcome is not inferred from the
old first reason; the checked-in 1.1 replay must demonstrate each row.

The nine recon idiom walls and the final collection wall explain that result:

| Positive | W1 table | W2 helper reader | W3 named alpha | W4 ternary | W5 float/round | W6 bool mask | W7 helper test | W8 enumerate/zip | W9 astype | Deferred collection / actual first wall |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | n/a | retained `DictReader` variant | A5-capable | assigned ternary retained | p lineage not direct | retained record-row filters | n/a | n/a | n/a | reader unavailable |
| P2 | A2 | A4 | A5 | assigned ternary retained | n/a | A7 | n/a | retained | n/a | cardinality at W8 |
| P3 | A1 | A4 | A5 | assigned ternary retained | relabeled abstention behind W7 | A7 | retained | output-only wrapper | n/a | cardinality at W7 |
| P4 | A1 | direct reader | A5-capable after proof | container/assigned verdict retained | relabeled behind W7 | A7 | retained | output-only wrapper | n/a | cardinality at W7 |
| P5 | A1 | A4 | A5 | helper ternary retained | relabeled behind W7/W8 | already `.loc` | retained | subset/zip retained | A6 | cardinality at W7/W8 |
| P6 | A1 | A4 | A5 | assigned/container verdict retained | relabeled behind scope | already `.loc` | retained | n/a | A6 | derived `HEADLINE` scope wall |

“A5-capable” does not claim later reachability; it means the named literal itself is within A5 if
earlier retained walls are independently removed. Envelope 11 still measures first contact on fresh
cases regardless of these opened-case expectations.

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
| 1.0 hierarchy registry | Copy by value and add only the explicit section-4 exemption test; all other controls and the residual remain. |
| Contract profile 1.2.0 and lifecycle | Reuse without edits. |
| Finding wording profile v1 | Reuse the exact object and digest; do not create v2. |
| Qualified pseudoreplication/complete-domain surfaces and grant pins | Byte-untouched. |

### 12.2 Planned file changes

| File or surface | Planned change |
|---|---|
| New accepted `docs/implementation/ADR-0078-...md` (final number/title assigned before build) | Authorize only the 1.1 identities, A1-A7 grammars, exact ternary, relabels, E11 custody/protocol, candidate-surface review, and isolation requirements. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v1_1.py` | Copy the frozen 1.0 module and implement sections 3-6. Do not import private dependence helpers. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v1_1.py` | Copy the 1.0 adapter, set check/adapter `1.1.0`, freeze the exact 1.1 reason set, and retain the observation/fact schema. |
| New `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v1_1.py` | Copy the detector wrapper, set version/entry point `1.1.0`, and retain all four exact guards and operand registry. |
| New `src/sc_referee/scientific_checks/integration_multiple_testing_v1_1.py` | Version the development compilation overlay for the 1.1 observation types without changing the shared qualified compiler. |
| `src/sc_referee/scientific_checks/profiles.py` | Replace only the active development MT module/binding with version 1.1 and retain ordinary/qualified projections unchanged. |
| `src/sc_referee/detectors/method_conflict_registry.py` | Register detector 1.1 alongside historical 1.0 manifest support and dispatch the active development binding exactly. |
| `src/sc_referee/detectors/method_conflict_finding.py` | Permit the exact MT 1.1 development binding to reuse the byte-identical wording v1 object; do not edit that object or any pseudoreplication wording. |
| Development-lane controller dispatch | Select the versioned 1.1 integration overlay only for the development registry. The ordinary controller path remains unchanged. |
| Detector/scientific-check capability manifests and scientific registry resource | Add/freeze 1.1 component manifests, retain historical 1.0 detector material needed for locked validation, and point only the development binding to 1.1. |
| New `tests/test_code_csv_multiple_testing_dataflow_v1_1.py` | Execute all admission, ternary, reason, guard, FA, PROBE, and ladder matrices. |
| New adapter/detector/integration tests | Pin 1.1 identities, digests, schemas, error guards, candidate projection, and no-Finding ceiling. |
| New `tests/test_multiple_testing_e10_replay_v1_1.py` | Execute all 15 opened cases and assert section 10 plus deterministic repeat bytes. |
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
3. the exact inline ternary is the only hierarchy subtraction, and all four guard-role negatives
   abstain;
4. every recon `PROBE` and every P2/P3 ladder file executes through the analyzer with section-9
   outcomes;
5. all 15 E10 projects execute through 1.1 with section-10 outcomes and byte-identical repeat output;
6. the closed reason registry equals real emitters plus the documented-unreachable annex;
7. correction-terminal coverage is identical, off-grammar blocked-node coverage never shrinks, and
   row completeness admits only exact group-row equality;
8. A5 counts every binding anywhere, uses source-text Decimal construction, and the hand-Bonferroni
   rebinding fixture never becomes a candidate;
9. contract 1.2.0, wording v1, all 1.0/1.1 contract goldens, and 1.0 source modules remain unchanged;
10. the ordinary registry contains no MT code binding and the development registry contains exactly
    one active 1.1 binding;
11. every qualified pseudoreplication and complete-domain identity, grant, pin, qualification,
    wording byte, Finding byte, and replay outcome is invariant, with explicit lane-digest
    non-derivation;
12. the prose tripwire covers every new predicate and passes all paired structural controls;
13. Envelope 11 uses external data-generation custody and retains the no-recall-gate protocol; and
14. every repository-required validation command passes after the final file change.

Any failure of the E10 replay oracle, guard differentials, closed-reason equality, contract goldens,
or two-registry isolation is a design regression. The implementation must stop and report it rather
than broaden an admission or weaken a guard.
