# Multiple-testing code slice 2.1 recall-delta design — 2026-08-25

**Status:** build-ready design, Revision 1a; implementation amendment records no behavior change

**Version:** detector/check/adapter `2.1.0`, development lane only

**Normative base:**
[`MULTITEST-CODE-SLICE-2.0-DESIGN-2026-08-25.md`](MULTITEST-CODE-SLICE-2.0-DESIGN-2026-08-25.md),
Revision 2, `sha256:575fb90bd6a4ac0433d9a552bb47008e2cfd3ec3ca13eab0566d51a4b106dae4`.
Unless this document names a delta, every 2.0 predicate, registry, order, reason, limit, invariant,
and test remains normative by value.

**Authoritative recall evidence:**
[`MULTITEST-RECALL-RECON-CORPUS20-2026-08-25.md`](MULTITEST-RECALL-RECON-CORPUS20-2026-08-25.md),
`sha256:ea510d3fe7dd793f9f222f9d715d85571edcfdca76bdd605b99af4cd3626c3ff`, read and
executed against the repository at `47fb5f9`. The full
[`FINDINGS-PLAYBOOK.md`](FINDINGS-PLAYBOOK.md),
`sha256:9bcb66dff193956d63b37ff6dad289e6a459dc6adc16208102483939ce0f520a`, governs
the evidence and false-accusation standard.

The executable recon is
`evaluation/development/multitest-recall-recon-corpus20/`; its canonical source-set digest is
`sha256:45c28cb35dc5a4cebca8e9ad640110fcc64e858f5511e49f09b974df6b0944e1` over 115
non-cache files. The harness and corpus-wide prototype builder are respectively
`sha256:dd168126a3b3e24138ffa2266b22220f10959c56de7442d1b429d506189fb154` and
`sha256:904bcf01e15dfa02d46b00658241b2b0fd4fcb9199e1a64e823a47bdbea47162`.
Every available ladder rung was executed before this design was written.

## 1. Decision and non-negotiable boundary

Version 2.1 is a value-grammar recall delta inside the 2.0 architecture. It adopts exactly R1,
R2/R3b, R4, R5, R6, R7, R9, R10, R11, R12, R13, R14, R15, R16 in both required locations, and
R18. Each admission recognizes a finite transport, binding, row-identity, record, presentation, or
family-position edge that the executed recon isolated. It does not add a test API, correction API,
correction method, threshold value, reader, group split, statistics exemption, or sink.

The following 2.0 surfaces remain unchanged by value:

- the whole-module registered-test-call, correction-terminal, statistics-prefix, and repeated-
  construct censuses;
- the dynamic-execution and API-rebinding censuses;
- recognized correction APIs, methods, defaults, return projections, input-determined coverage,
  manual adjusted-p grammar, and correction classifications;
- the source-text Decimal threshold grammar, syntax-wide A5 binding count, `{0.05}` raw-family
  narrowing, product rule, and order-12/order-13 transform partition;
- operand authorization and the exact complete-row equality proof;
- all hierarchy/control nodes and early-exit prevention edges, except the two exact R2/R3b
  statement-rendering exclusions defined in 3.9;
- extremum, export, upstream, family-collection, partition, resampling, sensitivity, dead/live
  conditional, outcome-mutation, and unresolved-consumer guards; and
- the rule that every unclassified forward edge abstains `unresolved-pvalue-consumer`.

The load-bearing 2.0 invariant therefore survives: every correction name is seen globally; every
family p consumer is accounted; and unrecognized p or threshold arithmetic cannot be crossed. No
admission may be implemented by skipping a consumer, interpreting prose, accepting a semantically
similar call, or choosing a favorable reaching definition.

### 1.1 Deliberately skipped and declined proposals

R8 and R17 are skipped. In the executed ladders they unlock only rungs inside bin-C cases and do
not change the adopted 17/19-case oracle. Their outcome/table and threshold-table surfaces remain
under the 2.0 normalizers and threshold guard.

Recognizing `P < ALPHA / K` as manual Bonferroni **coverage** is declined. It changes the
correction surface rather than transporting already-proved evidence, could convict a correct hand-
subfamily threshold, and requires a future policy ADR. It is the standing candidate for that
review; 2.1 does not partly implement, infer, or special-case it. Such threshold arithmetic retains
`unresolved-decision-threshold`.

## 2. Identity, authority, wording, and isolation

### 2.1 Versioned identities

```text
check:authorized-complete-family-correction-over-code-test-battery@2.1.0
adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1@2.1.0
detector:bounded-code-csv-multiple-testing-conflict@2.1.0
method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
```

Only the development binding advances. Versions `1.0.0`, `1.1.0`, and `2.0.0` remain registered
and explicitly importable for historical replay. Maturity stays `question_only`, production
Finding permission stays false, and the development controller emits zero Findings.

### 2.2 Contract and wording

Contract profile `1.2.0`, its group-column plus ordered outcome-family authority, validators,
canonical values, seven error categories, and historical `1.0.0`/`1.1.0` records are byte-
unchanged. No new evidence slot is needed. The wording profile remains byte-identical:

```text
method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v1@1.0.0
sha256:80c4bb3c0afd75b290ab02a195e5285528f982554ab46b373e63072232902259
```

The same slots are resolved. Presentation text remains non-evidence; no wording v2 is justified.

### 2.3 Frozen-lane isolation

The 1.0/1.1/2.0 MT modules, qualified pseudoreplication `3.1.0`, complete-domain, GrantPins,
grants, qualification records, threshold policies, metric sets, Finding objects, wording objects,
`method_conflict_grant_pins.py`, and all `code_csv_dependence_dataflow*.py` remain byte-untouched.
The 2.1 implementation uses versioned copies and no private cross-version import.

Frozen 2.0 implementation anchors are:

```text
dataflow    sha256:5f25aeab3e6c600794275918f9affcd19c33f877f770a6e3d7665fe8c33d5883
adapter     sha256:8441c22502197d09855cbe0dac891bc7ba027185b8745aac9a4c708f28d738f6
detector    sha256:ba2507973937f1a95b800df48823c43c17d3a7b89df6ebc8892c8e675f6217b5
integration sha256:508222f2a55345cd8f6c911fe7367f240e21c580300390bdc13e3ef8e8b02550
```

The existing open-corpus adapter replay record is frozen at
`sha256:c4a37b778de2a41d265080441d8ce38003c6ef4c75bb272bde957306dc79773c`.
The build adds a 2.1 record without rewriting the frozen 1.1/2.0 entries.

### 2.4 ADR amendment

ADR-0079 receives a narrow 2.1 amendment recording the finite transports below, the paired
hierarchy/conclusion treatment of R2/R3b, R12/R15 safety obligations, full R16 requirement, R8/R17
deferral, and the declined Bonferroni-coverage policy. It must state that the admissions do not
establish scientific meaning from display text and do not change correction recognition.

The amendment must separately record that `MASK.sum()` in 3.3 is a design-time extension beyond
the recon's summarized R9 grammar. It exists only because the required spec-25 recall case counts
each pre-bound group mask for display before reusing it in `.loc`. The extension is closed to a
no-argument/keyword read whose result flows only through numeric presentation to a registered sink;
it cannot feed selection, a test, a correction, a family container, a decision, or control.

## 3. Closed 2.1 admission grammars

Terms used below are structural:

- `P` is one exact family-position p origin under 2.0 section 4.5.
- `D` is one recognized decision under 2.0 sections 4.7/4.8 after threshold validation.
- `PSEQ` and outcome sequences retain the separate 2.0 section-4.6 and 4.2 grammars.
- `DISPLAY_STRING` is an `ast.Constant` string that is nonempty, NUL-free, and at most 256 UTF-8
  bytes. The limit is measured from bytes; the content is never read, tokenized, matched, or
  compared.
- `REGISTERED_SINK` means the unchanged 2.0 `p_result_eligible` sink grammar.
- “unconditional” means a statement in the same lexical statement list, not nested in `If`,
  `IfExp`, loop, comprehension, `Try`, `With`, `Match`, handler, `else`, `finally`, lambda, or a
  different helper expansion.

Anything outside the productions below follows the unchanged 2.0 path and exact reason. Similarity
is not equivalence.

### 3.1 R12 — nearest preceding straight-line definition

R12 replaces the single-definition lookup only for an on-slice `Name` load with a closed segmented
reaching-definition proof:

1. The load and all eligible stores are in one lexical statement list or one deterministic X4-
   expanded copy of such a list.
2. An eligible store is an unconditional `Assign` or `AnnAssign` to one `Name`, or one leaf of a
   same-kind List/Tuple destructuring target whose value arity is statically exact. Chained targets,
   starred targets, `AugAssign`, `NamedExpr`, attribute/subscript targets, and delete are ineligible.
3. The chosen definition is the unique eligible store with the greatest source position strictly
   before the load and after the preceding eligible store. Its RHS is resolved under the ordinary
   backward/forward grammar; R12 does not make a new value form legal.
4. No store, delete, alias mutation, unresolved escape, `global`, `nonlocal`, or closure use of that
   Name occurs between the chosen store and load. Exact direct loads are not aliases merely because
   they share a value.
5. Every binding of the tracked Name in the parsed module must be classifiable. If any binding is
   conditional, loop-carried, in a comprehension, in a called or uncalled helper other than the
   current X4-expanded frame, or otherwise outside items 1-4, the Name does not use R12 anywhere.
   The ordinary exact abstention fires.

Thus repeated explicit blocks such as `ctl = ...; p = TEST(...); ...; ctl = ...; p = TEST(...)`
can be sliced per segment. R12 never assumes a branch outcome or loop iteration.

Three load-bearing adversaries execute separately:

- `correct-r12-store-inside-called-helper` refuses the tracked helper store;
- `correct-r12-conditional-store` refuses a store in either arm of an `If`; and
- `correct-r12-loop-carried-store` refuses a store in a `For`/`While` body.

Each must abstain at its ordinary earliest ambiguity/lineage/consumer reason and never become a
candidate. A test that calls a private reaching-definition helper without executing the public
analyzer does not satisfy this gate.

### 3.2 R11 — exact counted `while` family normalization

A `while` contributes the same finite family mapping as direct ordered iteration only when all
conditions hold:

1. In the immediately enclosing statement list, the nearest preceding binding is exactly
   `INDEX = 0`, with an unshadowed integer literal zero.
2. The test is exactly `INDEX < len(SEQUENCE)`, or `INDEX < LENGTH_NAME` where `LENGTH_NAME` has
   exactly one immutable module binding `LENGTH_NAME = len(SEQUENCE)`. In either form `len` is
   unshadowed, has one positional argument and no keywords, and `SEQUENCE` resolves by section 4.2
   order-equal to the complete contract family of length `N`. No other integer constant or length
   arithmetic is admitted.
3. The body has no `break`, `continue`, `return`, `raise`, `yield`, `await`, nested loop, mutation of
   `SEQUENCE`, or binding of `INDEX` except the final statement.
4. The final body statement is exactly `INDEX += 1`; the literal is integer one and the operator is
   `ast.Add`. There is no `else`.
5. Every on-slice family member read in the body is an exact literal-field projection from
   `SEQUENCE[INDEX]`, and every indexed P/container store uses the same `INDEX`. The body contains
   exactly one normalized registered family call.
6. `INDEX` has no load or store outside the initializer, test, admitted projections/stores, and
   increment until the loop ends.

Reversed comparisons, `<=`, nonzero starts, other steps, data-dependent exits, dynamic length,
separate counters, or a summary loop sharing an unresolved counter remain cardinality/control
abstentions. Each loop is proved independently; two counted loops do not share one proof.

### 3.3 R9 and R10 — row-preserving operand edges

#### R9: pre-bound same-frame group mask

R9 admits only:

```text
MASK = FRAME[GROUP_COLUMN] == GROUP_VALUE
MASK = GROUP_VALUE == FRAME[GROUP_COLUMN]
FRAME.loc[MASK, OUTCOME]
```

`MASK` has one usable reaching definition in the same lexical/X4 frame; the comparison is exactly
one `ast.Eq` with one comparator; `FRAME`, `GROUP_COLUMN`, `GROUP_VALUE`, and `OUTCOME` resolve under
the unchanged authority grammar; and the `.loc` receiver is identity-equal to the comparison's
frame after exact Name aliases. `MASK` has no rebind, mutation, store, delete, boolean combination,
on-slice transform, or unresolved escape. Other loads are off the operand slice only when they
cannot mutate or feed back into `MASK`; the sole additional closed read-only use is
`MASK.sum()` with no arguments/keywords whose result proceeds only through numeric presentation to
a registered sink, as in spec-25. Negation, `BoolOp`, `isin`, inequality, a mask from another frame,
bare boolean subscript, and any extra predicate remain refused. The final computed row-index set
must still equal every authorized row for that group.

#### R10: `.to_numpy(dtype=CLOSED)`

R10 treats `.to_numpy` as the existing no-argument row-identity edge only in these additional
shapes:

- one positional `CLOSED_DTYPE` and no keywords; or
- no positional arguments and exactly one `dtype=CLOSED_DTYPE` keyword.

There is no starred or `**` argument. `CLOSED_DTYPE` is either unshadowed bare `bool`, `float`,
`int`, or `str`, or a resolver-proved string constant that is NUL-free and at most 64 UTF-8 bytes.
The dtype string is measured and structurally resolved, never interpreted for scientific meaning.
Any `copy`, `na_value`, dynamic dtype, extra argument, or unsupported keyword is not R10. R10 does
not remove or alter an upstream row mask.

### 3.4 R4 — local field-only dataclass/namedtuple records

A local record schema is reconstructable only through one of two closed declarations:

1. **Dataclass.** One class with no bases, keywords, metaclass, duplicate declaration, or nested
   class. Its sole decorator is unshadowed `dataclasses.dataclass`/an exact import alias, either bare
   or called with no arguments. After an optional docstring, its body contains only simple-Name
   `AnnAssign` fields, each unique, with no value or a closed non-p scalar default. `ClassVar`,
   descriptors, properties, methods, `__post_init__`, comprehensions, calls, and arbitrary class
   statements disqualify the schema.
2. **Namedtuple.** One simple Name assignment to exact `collections.namedtuple`/an exact import
   alias with exactly two positional arguments and no keywords: the typename is one closed string
   equal to the bound Name, and fields are a whitespace/comma-separated closed string or List/Tuple
   of unique public identifier strings. `rename`, `defaults`, subclassing, and dynamic fields are
   refused.

Construction is a direct call to that schema using either exact arity positional arguments or one
keyword per field, never both, with no starred/`**` value. Every field maps to exactly one source
expression. Access is exact `RECORD.FIELD`; stores/deletes to a record attribute, alias mutation,
unknown attributes, method calls, and unresolved escape fail reconstruction. A sequence of such
records remains subject to the unchanged PSEQ family-position and mutation rules. R4 transports
field identity; it does not bless a p transform or decision.

### 3.5 R15 — precise record-member origins

R15 is the only flow-reducing admission. It replaces conservative whole-record p-origin union with
the selected field's origins only when all conditions hold:

1. The record is either a 2.0 Dict display with no unpacking and unique literal string/integer keys,
   or one exact R4 record construction.
2. Its binding and, for a family record, its outcome-position mapping are unique under the
   PSEQ/outcome grammars. The accessed key/field is literal and exists exactly once.
3. The record is constructed in one unconditional statement or one admitted unconditional family
   builder insertion. There is no conditional, duplicate, later, alias, attribute, subscript, or
   unresolved store/delete that might affect any field before the access.
4. The record does not escape to an unresolved call/container and no key expression is p-derived.
5. The selected member has a uniquely resolved value. Other fields may carry other family values,
   but are ignored only for this exact access.

If any condition fails, the analyzer retains the 2.0 conservative union of origins. It must not
drop origins, select the apparently convenient field, or return an empty origin set. The executed
`correct-r15-unresolved-store-retains-conservative-origins` fixture introduces an unresolved store
to a sibling field and must retain the conservative origins and the existing abstention. This rule
is what clears spec-35's descriptive mean subtraction without concealing its `p_value` member.

### 3.6 R14 — stored member decision transport

R14 recognizes a stored decision only when a pre-existing family-record position receives one
already-recognized decision:

1. The target is exact `RECORD[FIELD]` or `RECORDS[OUTCOME][FIELD]`, where `FIELD` is one literal
   string/integer and the record/family position is uniquely reconstructed by 3.4/3.5 plus the 2.0
   outcome grammar.
2. For every affected family position, there is exactly one reaching store to that member before
   every load. A store may be in an exact normalized family/subfamily loop. Its only admitted
   control is a literal `OUTCOME in CLOSED_SUBSET` or `OUTCOME not in CLOSED_SUBSET` membership,
   including the equivalent one-statement `continue`, when section 4.2 resolves the result
   independently for every contract position and the combined branches/loops yield exactly one
   store per position. No runtime-dependent conditional, duplicate, alias, dynamic-key, attribute,
   unresolved, or post-load store is admitted.
3. The RHS already resolves, without R14, to one raw comparison, recognized reject member, or
   recognized adjusted-p comparison for that same family position.
4. Loads of the member are transports only. Every load is forward-accounted to the same member's
   registered sink, exact terminal rendering, or another admitted identity edge.

R14 creates no threshold, reject decision, correction coverage, or family membership. It only
preserves the family position of a decision proved elsewhere. A stored value from an unknown
adjuster or unresolved helper remains the ordinary correction/p-consumer abstention.

### 3.7 R16 — complete two-pass zip transport and family-position mapping

R16 lands as one indivisible rule in both the hierarchy exclusion and family-position/conclusion
mapping. Implementing only one half is a design regression.

An admitted loop is exactly a non-async `for TARGET in zip(ARG_1, ..., ARG_k)` with unshadowed
`zip`, `k >= 2`, no keywords/starred arguments, no `else`, and no `break`, `continue`, early exit,
or mutation of any argument. Every argument must resolve; one unknown argument refuses the loop.
Each argument is exactly one of:

- an outcome sequence order-equal to the contract family;
- a finite outcome table whose first literal field is order-equal to the contract family;
- a `PSEQ` with unique ordered family positions;
- a recognized correction return with unique ordered family positions; or
- a List/Tuple/list-comprehension sequence of decisions or DISPLAY_STRING values whose source
  decisions reconstruct one unique ordered position per family member.

All family-bearing arguments must have length `N`, unique positions, and the identical ordered
position tuple `(0, ..., N-1)`. Every outcome argument must be order-equal to the contract list.
`TARGET` is an exact same-arity List/Tuple destructuring target of unique Names. The target leaf for
each argument inherits that argument's per-position abstract value inside the body. Direct loads of
those leaves may use only the unchanged identity/presentation/decision/sink transports; an
unresolved consumer refuses the forward slice.

This removes the 2.0 requirement that a zip include a recognized correction return, but it does not
remove the correction census or consumer proof. The loop iterable is excluded from hierarchy only
after the complete mapping above succeeds. The conclusion census uses the same mapping so each
decision/P member is credited to its exact family position. This dual implementation admits
spec-07 and spec-45; transport-only exclusion without position mapping would strand them at
`pderived-conclusion-family-incomplete` and fails the gate.

### 3.8 R1 and R13 — literal presentation formatting

#### R1: literal percent formatting

R1 admits exactly `FORMAT % PAYLOAD` where `FORMAT` is a DISPLAY_STRING `ast.Constant`, the
operator is `ast.Mod`, and `PAYLOAD` is its direct right operand. `PAYLOAD` may be one expression or
one List/Tuple display of expressions. That direct payload display is presentation, not a PSEQ or
family record, but every element is still independently walked by the forward consumer proof.

The result must reach only registered sinks through the 2.0 rendering transports: exact identity
assignment, nested literal presentation formatting/f-string, and literal presentation
concatenation. Any call, arithmetic use, comparison, container retention, store, return, control,
or unresolved consumer outside those transports restores the ordinary p-container/manual/
consumer guard. The format bytes are bounded but never inspected for conversion tokens or meaning.

#### R13: presentation join

R13 admits exactly `SEPARATOR.join(ITERABLE)` when `SEPARATOR` resolves to a DISPLAY_STRING and the
call has one positional argument, no keywords/starred arguments. `ITERABLE` is one finite
List/Tuple display or one non-async, one-generator, no-`if` List/Generator comprehension over an
R16-mapped family sequence. Every element is an R1 percent rendering, f-string, literal `.format`,
`str(P)`, pure R5 helper result, or DISPLAY_STRING. Every embedded P/decision remains independently
position-mapped and forward-accounted. The join result must proceed solely through the R1 sink-only
transports. Dynamic separators, filters, sorting, sets, nested generators, calls returning elements,
or any nonpresentation consumer are not R13.

### 3.9 R2/R3b — statement-form terminal rendering in both registries

One `ast.If` is terminal rendering only if its test contains exactly one family-position decision
under the unchanged threshold grammar, it has no `elif`, and both `body` and `orelse` contain
exactly one statement in one of these two shapes:

1. **Assigned form:** each arm is an `Assign` with one simple-Name target, both target spellings are
   equal, and each value is a DISPLAY_STRING. Every load of that selected Name and every exact
   identity alias bound from it is totally accounted to the same member's registered sink through
   only the 2.0 rendering transports. There must be at least one such sink load.
2. **Direct-sink form:** each arm is one `Expr(REGISTERED_SINK(...))`; both calls resolve to the
   same sink kind and the same static target, every registered payload in both calls is a
   DISPLAY_STRING, and there are no p values, calls, containers, or dynamic values in either
   payload. The static target is the unchanged sink registry's canonical destination: for `print`,
   both calls omit `file` or resolve `file` to the same exact target; for a receiver sink, both
   receivers resolve through exact identity aliases to the same binding. An unresolved target,
   different sink kind, or different static target is not this form.

The classifier is called in **both** places:

- the whole-module hierarchy registry excludes exactly the admitted `If`; and
- the conclusion census credits the test's exact decision position and sink kind.

If the two calls disagree, the build stops: excluding hierarchy without crediting the conclusion
recreates the recon's `pderived-conclusion-family-incomplete` wall. `AnnAssign`, multiple/chained
targets, missing `else`, non-string arms, calls in assigned values, compound arms, different assigned
Names, conditional execution of scientific work, a test/correction/container gate, a second
emission branch, choosing between sink calls or destinations, or any unaccounted selected-string
consumer remains
`hierarchical-gatekeeping-present` or `pvalue-control-dependence-unresolved` by the unchanged
registry. The assigned form is the sole exception to R12's conditional-store refusal, and only for
the selected DISPLAY_STRING Name: it does not make either arm a usable numeric, p, operand,
threshold, family-container, or correction definition.

### 3.10 R5 — pure p-presentation helper

R5 is an X4 presentation transport, not a general helper exemption. A helper qualifies only when:

1. it is one unique top-level synchronous simple-name function satisfying unchanged X4 limits,
   with exactly one required positional formal designated `PFORMAL`, no default, variadic,
   decorator, recursion, closure, `global`, `nonlocal`, or nested definition;
2. after an optional docstring, its body is exactly one `Return`;
3. the return expression is one of: `str(PFORMAL)`; an f-string whose only tracked values are direct
   `PFORMAL` formatted values; R1 literal percent formatting of `PFORMAL`; literal-string `.format`
   with direct `PFORMAL` payloads; or an `IfExp` whose test is one direct comparison of `PFORMAL`
   with a bare finite numeric display cutoff and whose two arms are each DISPLAY_STRING or one of
   those p-formatting forms, with **at least one arm required to be a p-formatting form of
   `PFORMAL`**;
4. no returned expression performs numeric arithmetic, invokes a nonpresentation call, returns a
   boolean/number/container, or refers to another tracked value; and
5. each call has exactly one positional actual with one family-position P origin and no keywords,
   and every returned value is totally consumed only by admitted presentation/sink transports.

The qualifying helper's display comparison is not a scientific conclusion. The caller must
separately have a recognized family decision. Its display cutoff is not entered into the order-13
threshold set only because at least one selected arm renders the p value itself. An `IfExp` whose
**both** arms are DISPLAY_STRINGs is not R5 p presentation: it is verdict-shaped terminal rendering,
and its cutoff enters the unchanged order-13 permitted-set, source-Decimal, product, and binding
rules before it can be credited as a conclusion. Thus an `N = 5` helper selecting two constant
verdict strings at `p < 0.01` stops `unresolved-decision-threshold` because
`Decimal("0.01") * 5 == Decimal("0.05")`.
The helper-internal `IfExp` is excluded from hierarchy only after this entire R5 proof succeeds and
the separate caller conclusion is proved; an otherwise identical `IfExp` stays in the whole-module
hierarchy registry.
`return hand_holm(PFORMAL)`, `return PFORMAL * N`, `return adjust(PFORMAL)`, or a helper containing
any other statement stays unresolved and blocks the strongest hand-Holm/Bonferroni FA shapes.

All eight R5-shaped corpus helpers already satisfy the new arm condition, so it costs zero projected
recall: `spec-41,43,44` use one DISPLAY_STRING arm and one R1 percent-format p arm;
`spec-46,47,48,49,50` use p-formatting f-string arms on both sides.

### 3.11 R6 and R7 — helper-local threshold and returned-field transports

#### R6: helper-local bare threshold

Within one admitted X4 expansion, a decision threshold Name may resolve to one direct, unconditional
simple-Name `Assign`/`AnnAssign` in that helper whose RHS is a bare source numeric literal. The Name
has exactly one binding event by spelling anywhere in the parsed module, and that event is the
helper assignment; it has no global/nonlocal/closure/escape. The literal passes the unchanged source-text Decimal,
permitted-set, and product rules. Arithmetic, a call, table/destructured value, default argument,
attribute, or second binding remains `unresolved-decision-threshold`. R6 does not relax the
syntax-wide A5 single-binding rule for module values; it supplies the corresponding single local
binding proof in the X4 frame.

#### R7: helper-return field transport

An X4-expanded helper may return one finite same-kind List/Tuple display, 2.0 Dict record, or exact
R4 record whose fields independently resolve to descriptive values, P, D, or DISPLAY_STRING. The
call site must consume it by exact same-kind full-arity destructuring, exact literal key/index, or
exact R4 attribute. Each selected field retains its own origin and family position; descriptive
siblings do not acquire p origins. The return has no starred/unpacked value, dynamic key, duplicate
field, alternate return, or unresolved consumer. R7 creates neither a decision nor correction; it
transports the already-proved P/D/rendering field. This is what allows spec-09 and spec-49 to carry
their p and verdict out of the per-member helper.

### 3.12 R18 — two-element constant display table

R18 admits exactly:

```text
TABLE[int(D)]
```

`TABLE` is a direct List/Tuple display, or one exact immutable Name bound once to it, with exactly
two DISPLAY_STRING elements. `int` is the unshadowed builtin called with exactly one positional
argument and no keywords; `D` is one already-recognized decision for one family position. The
subscript result proceeds solely through admitted presentation/sink transports. R18 credits `D` in
the conclusion census but creates no decision from the strings and never inspects which text is at
index zero or one. Direct boolean indexing, other lengths, nonstrings, computed tables, dynamic
indices, mutation, escape, and any nonpresentation consumer retain the existing hierarchy/family-
collection/consumer reason.

## 4. Ordered integration and unchanged guards

The 2.0 ordered predicate remains the sole first-reason selector. Admissions enter only here:

| 2.0 order | 2.1 addition | Failure remains |
|---:|---|---|
| 7 | R11 exact counted-while cardinality; R12 segmented definitions used by census normalization | Existing census/cardinality and X4 reasons |
| 8-9 | R9 mask, R10 dtype identity, R12 operand bindings | `test-operand-lineage-unresolved`; `selected-group-row-completeness-unproven` |
| 10 | R4/R7/R12/R14/R15/R16 record, return, binding, store, and position transports | `pvalue-family-collection-unresolved`; `unresolved-pvalue-consumer` |
| 12 | R1/R5/R13/R18 presentation edges excluded only from noncomparison transform classification | Existing manual/cast/round reasons |
| 13 | R6 helper-local bare literal; R14 decision RHS; R18 decision input | `unresolved-decision-threshold` |
| 14 | R2/R3b and R16 exact transport exclusions | Existing hierarchy/control/partition/resampling/statistics reasons |
| 15 | R2/R3b, R7, R14, R16, R18 exact family-position conclusion mapping | `pderived-conclusion-family-incomplete` |

All whole-module censuses run before these value admissions. Direct-P comparisons remain exclusive
to order 13. R1/R5/R13 presentation classification may not hide a BinOp/Call that transforms P
numerically. R9/R10 never waive row equality. R12 cannot resolve a conditional store. R15 cannot
discard origins after an unresolved store. R16 is rejected unless both transport and position
mapping prove the same full family.

### 4.1 Guard ownership after the delta

| Guard | 2.1 trigger source | Delta effect |
|---|---|---|
| Test/sensitivity/dead/live branch | Global test census + R11/R12 normalization | R11 only proves its exact loop; every other branch/multiplicity rule unchanged. |
| Correction/statistics/dynamic/API rebind | Whole module | Byte-unchanged; no admission discharges it. |
| Outcome mutation | Backward slice + stability closure | Unchanged. |
| Row/discovery-validation | Operand slice | R9/R10 identity edges feed the same exact row-set equality. |
| Upstream/export/extremum/partition/resampling | Forward/global scopes from 2.0 | Unchanged. |
| Family collection | Forward slice | R4/R7/R14/R16 finite mappings only; all unresolved containers still abstain. |
| Manual/threshold | Forward slice + syntax-wide A5 | Byte-unchanged except R6 supplies one local bare-literal binding to the same grammar. |
| Hierarchy/control | Whole module | Only exact R2/R3b and fully mapped R16 transport are excluded. Assert/match/BoolOp/early-exit residuals remain. |
| Conclusions | Forward slice | R2/R3b mirror, R7/R14/R16/R18 carry exact positions; no position inference. |

## 5. False-accusation analysis per admission

Every fixture below is a correct analysis and must execute through the public 2.1 analyzer. “Corpus
sharing” names labeled-correct open-corpus cases with the exact surface when present, or the closest
guard-bearing near-shape when the exact grammar is absent. No case is removed from the hard gate.

| Rule | Strongest correct-analysis fixture | Unchanged rule that blocks a false candidate | Labeled-correct corpus sharing/near-shape |
|---|---|---|---|
| R1 | `correct-r1-percent-display-plus-hand-holm` formats raw p with `%` but sends P through a hand-Holm numeric helper before its decision. | R1 walks every payload; helper/numeric edge is `unresolved-pvalue-consumer` or manual-transform abstention. | Exact `%`: `spec-02,04,26,28,30,36,38,40,42`. |
| R2/R3b | `correct-r2-branch-selects-correction` has a p decision in an `If`, but one arm calls a correction; `correct-r3b-second-emission-branch` emits different scientific branches; `correct-r3b-different-static-sink-target` uses constant payloads but different destinations. | Nonconstant scientific arms and different sink kinds/targets remain in whole-module hierarchy as scientific control or choosing between sink calls. | Exact admitted form: none; adjacent `If`: `spec-08,12,14,24,26,30,36,38,44,50`. All 13 corpus `If` instances with two `Expr` arms call `print` in both arms. |
| R4 | `correct-r4-record-method-adjusts-p` defines a dataclass method that adjusts p before output. | Any method disqualifies the schema; family record/p consumer remains unresolved. | Exact local dataclass/namedtuple: none. |
| R5 | `correct-r5-hand-holm-helper` returns `hand_holm(p)`/numeric p arithmetic; `correct-r5-preregistered-verdict-cutoff-N5` has a nominal raw `p < 0.05` conclusion plus a two-constant-string helper verdict at `p < 0.01`. | Call/numeric return is outside R5; the two-constant verdict helper enters order 13 and the exact Decimal product rule stops `unresolved-decision-threshold`. | All eight shaped helpers have a p-formatting arm: `spec-41,43,44,46,47,48,49,50`; zero recall cost. |
| R6 | `correct-r6-helper-local-bonferroni-threshold` binds `cutoff = 0.05 / N`. | RHS is not a bare source literal; unchanged order 13 gives `unresolved-decision-threshold`. | Exact helper-local bare decision literal: none; adjacent helper thresholds in `spec-48,50` remain refused where computed/dynamic. |
| R7 | `correct-r7-helper-returns-unrecognized-adjusted-p` returns an unknown adjuster's value beside display fields. | Return field preserves the unresolved call; R7 transports but never blesses it. | Helper returns/presentation: `spec-48,50`. |
| R9 | `correct-r9-prebound-qc-and-group-mask` binds a group equality and then combines it with a QC mask; `correct-r9-mask-sum-does-not-feed-selection` exercises the closed summary read. | BoolOp/additional row mask is outside R9; `.sum()` is admitted only when its result reaches presentation and cannot feed selection/control. | Exact extension: `spec-25`; near-shape masks `spec-14,18,36,40` retain their array/negation reasons. |
| R10 | `correct-r10-dtype-after-validation-filter` applies `.to_numpy(dtype=float)` after a QC subset. | R10 preserves the existing selected rows; completeness still fails. | Exact dtype: `spec-14,18,36,40`, all pinned unchanged. |
| R11 | `correct-r11-while-skips-family-member` adds conditional increment/continue in a counted loop. | Exact loop grammar fails; cardinality/control abstention remains. | Exact admitted counted while: none. |
| R12 | `correct-r12-store-inside-called-helper`, `correct-r12-conditional-store`, and `correct-r12-loop-carried-store`. | Condition 5 refuses the entire tracked Name; ordinary lineage/consumer ambiguity fires. | Straight-line rebinding surfaces: `spec-14,16,36,38,42,44,46,50`; none may resolve a conditional/loop/helper store via R12. |
| R13 | `correct-r13-join-through-unknown-adjuster` joins formatted values returned by an unrecognized p-adjuster. | Each element is walked; unresolved call/correction blocks. | Exact `.join`: `spec-08,12,22,26,30,32,38,40`. |
| R14 | `correct-r14-stores-unrecognized-reject` stores decisions returned by an unknown correction into each record. | RHS must already be recognized; unresolved correction/p consumer survives. | Stored decision records: `spec-12,18,40`. |
| R15 | `correct-r15-unresolved-store-retains-conservative-origins` adds a dynamic/conditional sibling-field store to a p-bearing record. | Tight condition 3 fails; conservative whole-record origins remain and cause the existing abstention. | Finite dict records: `spec-12,22,32`; no unresolved origin may be dropped. |
| R16 | `correct-r16-complete-correction-two-pass-zip` zips outcomes, adjusted p, and reject flags; paired `correct-r16-unknown-zip-argument` adds a dynamic sequence. | Complete recognized correction is a covered negative; one unknown argument refuses transport and abstains. | Exact zip surfaces: `spec-08,10,12,22,24,32,34,40,44,46,50`. |
| R18 | `correct-r18-table-index-hand-sidak` indexes a two-string table with a decision using a computed Sidak threshold. | R18 requires D already pass order 13; computed threshold abstains. | Exact constant-table decision index: none; adjacent indexed correction logic in `spec-08,50` is not R18. |

The existing 2.0 section-7 admission and surviving-guard adversaries all retain their exact first
outcomes. In particular, hand Sidak, off-registry correction, default-method complete correction,
sensitivity duplicate, discovery/validation split, all-NumPy assert/match/short-circuit gates,
execution-prevention residual, label-permutation maxT, extremum, export, upstream p, dynamic p dict,
partition, Decimal product, N=4 bare `0.01`, and statistics sibling fixtures do not change.

## 6. Closed reasons

No reason is added, removed, or relabeled. The 2.1 closed set is byte-equal as a set to 2.0:

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

The 2.0 documented-unreachable argument for `conclusion-output-sink-unavailable` remains. Public-
analyzer emitter fixtures plus that annex must be set-equal to the adapter's closed set. Each 2.1
admission has an exact accepted fixture and at least one exact near-miss fixture asserting its first
reason; a literal in an old-version test cannot satisfy 2.1 coverage.

## 7. Adapter-level open-corpus oracle

The corpus remains the committed 50-case, 25-correct/25-misstep source set at
`evaluation/development/multitest-open-corpus-v1/`, commit
`d7cc94f22dcd99f642b356b47f6ee5d6d62acf26`. Its label and source digests remain the 2.0 pins:

```text
labels raw bytes  sha256:f9d2d33ba3b8247b0d0d65e5f72f765af02bfca6dc932f895010d79129f36f80
analysis source set sha256:7888b72a6ac1ec70830d4041517a977b8ea8ff6c4294a7d13a734ab9af377a2e
```

The 2.1 adapter runs every case twice through the same public harness. Checked-in 2.1 replay records
are regenerated from the approved implementation and then byte-gated; the 1.1 and 2.0 record bytes
remain frozen. The analyzer-only `baseline_1_1.json` remains diagnostic and is not an adapter oracle.

### 7.1 Misstep oracle — 19 candidates, six unchanged abstentions

| Case | Required adapter-level 2.1 outcome | Admission/protection |
|---|---|---|
| `spec-01` | candidate / `none` | R12 + R1 + R2/R3b |
| `spec-03` | candidate / `none` | R1 + mirrored R2/R3b |
| `spec-05` | candidate / `none` | R11 + R1 + mirrored R2/R3b |
| `spec-07` | candidate / `none` | full R16 transport **and** position mapping |
| `spec-09` | candidate / `none` | R6 + R7 |
| `spec-11` | candidate / `none` | mirrored R2/R3b |
| `spec-13` | abstain `test-battery-cardinality-unresolved` | R8 skipped; later per-member computed thresholds also remain refused. |
| `spec-15` | candidate / `none` | R4 |
| `spec-17` | candidate / `none` | mirrored R2/R3b |
| `spec-19` | candidate / `none` | Already candidate in 2.0. |
| `spec-21` | candidate / `strict_subset` | R14 stored member decisions; two recognized Holm members, four raw. |
| `spec-23` | abstain `pvalue-scalar-cast-or-rounding-unsupported` | `round(P)` remains refused. |
| `spec-25` | candidate / `none` | R9 exact pre-bound group masks. |
| `spec-27` | candidate / `none` | R18 + R1 presentation. |
| `spec-29` | abstain `unresolved-decision-threshold` | Per-member threshold selection remains outside order 13; R17 skipped. |
| `spec-31` | candidate / `none` | mirrored R2/R3b |
| `spec-33` | candidate / `none` | Already candidate in 2.0. |
| `spec-35` | candidate / `none` | R15 precise record member origins. |
| `spec-37` | abstain `selected-group-row-completeness-unproven` | First guard remains the unsupported operand selection; dynamic-key p record remains a later guard. |
| `spec-39` | abstain `api-resolution-ambiguous` | B-deferred NumPy container architecture; adapter-level pin. |
| `spec-41` | candidate / `none` | R5 + R1 |
| `spec-43` | candidate / `strict_subset` | R5 + R13; three Holm-covered, three raw. |
| `spec-45` | candidate / `none` | full R16 + R1 |
| `spec-47` | abstain `unresolved-decision-threshold` | R5 legitimately clears the presentation-helper wall and exposes the deeper designed per-member computed-threshold wall. |
| `spec-49` | candidate / `none` | R4 + R5 + R6 + R7 |

The minimum executed projection is `17/25`; full R16 raises it to the required `19/25`. The hard
ceiling is `20/25` while the designed narrowings stand, because only B-deferred spec-39 is outside
the five deliberate bin-C residuals. These are answer-visible recall numbers, not blind credit.

### 7.2 Correct-case hard oracle

Every labeled-correct case `spec-02,04,06,08,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,
42,44,46,48,50` must abstain or be a covered negative; candidate count is exactly `0/25` and
Finding count is zero. This is a hard stop.

The adapter-level first-reason pins required independently are:

- `spec-12` and `spec-34`: `test-battery-cardinality-unresolved`;
- `spec-14` and `spec-36`: `test-operand-lineage-unresolved` at order 9;
- `spec-18` and `spec-40`: `test-battery-cardinality-unresolved`, unchanged under R10;
- `spec-30`: `api-resolution-ambiguous` at adapter level, even if analyzer-only presentation
  changes would reach a later reason;
- `spec-48`: `unresolved-decision-threshold`, proving R5 does not cross hand Sidak; and
- `spec-50`: remains an abstention; R5/R16 do not discharge its off-registry correction flow.

The `spec-12`/`spec-34` pin is load-bearing. The adapter replay records the following independent
walls even though census order exposes only the first: R12 condition 5 refuses their tracked
conditional/loop-carried bindings; R16 refuses an unresolved zip argument; the census cannot prove
the required multiplicity; and a p-controlled append is a family-container insertion in the
unchanged hierarchy registry. Both are labeled-correct scripts. Their recognized coverage can
present a `strict_subset` candidate surface if a future delta resolves cardinality without all
three later guards, so any such delta requires a candidate-surface review and the unchanged
`0/25` correct-case hard gate; it may not merely update the first reason.

Three correct-case first reasons legitimately move under the complete 2.1 delta while remaining
abstentions:

| Case | 2.0 adapter first reason | Required 2.1 adapter first reason | Cause |
|---|---|---|---|
| `spec-28` | `pvalue-family-collection-unresolved` | `unresolved-decision-threshold` | R1 clears only presentation; the protected threshold is then exposed. |
| `spec-42` | `pvalue-family-collection-unresolved` | `unresolved-manual-correction-present` | R1 clears only presentation; the protected transform is then exposed. |
| `spec-48` | `unresolved-pvalue-consumer` | `unresolved-decision-threshold` | R5 clears only p formatting; hand Sidak remains protected by order 13. |

The corpus-wide R1/R2/R3b prototypes are reference classifiers, not production code. Prototype-
versus-final differential tests require the same admission decision on every applicable AST node
and the same 50-case movements attributable solely to those rules. The executed prototypes moved
correct `spec-28` to `unresolved-decision-threshold` and analyzer-level `spec-42` to
`unresolved-manual-correction-present`, never to candidate. R5 independently moves `spec-48` as
pinned above.

The labeled-misstep residual `spec-47` has the same reason-exposure treatment: its 2.0 adapter
reason `unresolved-pvalue-consumer` moves to `unresolved-decision-threshold` because R5 clears only
the presentation-helper transport and exposes the unchanged bin-C per-member threshold refusal.
It remains an abstention, so this movement changes neither candidate nor Finding eligibility.

## 8. Residuals and deferred work

### 8.1 Five deliberate bin-C cases

| Case | Residual | Protecting unchanged rules |
|---|---|---|
| `spec-13` | Concatenated primary/secondary outcome families plus a per-member computed threshold. | Complete outcome-sequence/cardinality proof and order-13 arithmetic refusal; R8/R17 skipped. |
| `spec-23` | `round(P)` on the decision/reporting path. | `pvalue-scalar-cast-or-rounding-unsupported`. |
| `spec-29` | Per-member threshold selected from a table/role. | A5 bare-literal/single-binding grammar and `unresolved-decision-threshold`; R17 skipped. |
| `spec-37` | Dynamic-key p-bearing Dict plus row-selection form. | Row completeness first; PSEQ dynamic-key/family-collection and total-consumer guards later. |
| `spec-47` | Presentation helper plus per-member Bonferroni-vs-raw threshold selection. | R5 may transport display only; computed/per-member threshold remains refused, and unresolved edges are not dropped. |

### 8.2 Spec-39 B-deferred dependency

Spec-39 is not partially admitted. Its four-refinement dependency list is:

1. R11 proof, independently, for both the test-producing and reporting counted `while` loops,
   including the exact closed `N_OUTCOMES = len(OUTCOME_NAMES)` length binding;
2. R10 positional dtype identity on both operands;
3. R1 percent-format presentation in both passes; and
4. a new reviewed NumPy fixed-container grammar for `numpy.full(N, numpy.nan)` followed by exact
   integer-position p stores/loads and family-position mapping.

Items 1-3 land generally in 2.1, but item 4 is a new p-container surface and is deferred. The
adapter therefore remains `api-resolution-ambiguous`/the pinned earliest adapter reason rather than
claiming partial reachability. This is the one B-deferred case behind the 20/25 ceiling.

## 9. Executable validation plan

Every fixture runs the public analyzer or adapter. AST/private-helper assertions may supplement but
never replace execution.

### 9.1 Admission and refusal matrix

For every production in section 3, execute one exact accepted fixture and one single-edge near miss.
Cross the following load-bearing sets:

1. **R12:** repeated module blocks; same X4 frame; chained/starred/augmented store; helper store;
   conditional store; loop-carried store; store-after-load; alias mutation; unresolved escape.
2. **R11:** exact loop; reversed/`<=` test; nonzero start; dynamic `len`; step other than one;
   early exit; nested loop; nonfinal increment; second counter; separate independently proved loops.
3. **R9/R10:** reversed equality; other frame; negation; BoolOp; `isin`; extra mask; every allowed
   dtype form; shadowed builtin; dynamic/extra dtype argument; upstream QC filter.
4. **R4/R15:** dataclass and namedtuple positional/keyword records; method/property/default-call;
   duplicate field; attribute store; field-specific p/descriptive origins; conditional/dynamic/
   alias store retaining conservative origins.
5. **R14:** raw comparison and recognized reject/adjusted comparisons stored once by exact family
   position; unknown adjuster, conditional/duplicate/dynamic/post-load store.
6. **R16:** outcome + P + decision sequences; table first-field outcome mapping; complete correction;
   no correction; unknown/misaligned/duplicate/short/reordered argument; target arity mismatch;
   transport-only and position-only mutation controls. Either half alone must fail.
7. **R1/R13:** scalar and tuple percent payloads; nested presentation; join over exact mapped
   generator; dynamic format/separator, set/filter/sort, unknown element call, second consumer.
8. **R2/R3b:** both exact shapes and every refused adjacent shape named in 3.9, including same-kind
   sinks with different static targets and different-kind sinks. For each accepted shape,
   independently assert hierarchy exclusion and conclusion-family completeness.
9. **R5/R6/R7:** exact display helper forms; numeric/call return; alternate/multiple return; helper
   with one/two p-formatting arms; two-DISPLAY_STRING verdict arms at `0.05` and product-rule
   `0.01`/`N=5`; local bare/computed/rebound threshold; tuple/dict/R4 return; mismatched
   destructuring; unresolved returned field.
10. **R18:** exact table/name-bound table; wrong size/type; mutation; direct bool/dynamic index;
    computed threshold; unresolved result consumer.

Every strongest-correct fixture in section 5 asserts its exact first reason or covered-negative
classification and zero candidates/Findings.

### 9.2 Recon ladder gate

Every `.py` file under
`evaluation/development/multitest-recall-recon-corpus20/lad/spec-NN/` becomes an immutable
checked-in 2.1 regression fixture, including `fa_*`, `rung*`, `probe_singlepass`, malformed/parser
near-misses, and alternative branches. A canonical manifest records relative path, raw SHA-256,
source case, construct removed/introduced, expected analyzer classification, and exact first reason.

The oracle groups are:

- all rungs for candidate-oracle cases `01,03,05,07,09,11,15,17,21,25,27,31,35,41,43,45,49`
  reach the candidate state once that rung has no intentionally retained near-miss; original/rung0
  reaches the section-7 candidate under the full delta;
- spec-13 rungs before removal of the R8/R17 walls retain the exact cardinality/threshold reasons,
  while `rung3` is the known-positive candidate control;
- spec-23 stays the exact round reason;
- spec-29 retains threshold reasons until the direct bare-`0.05` control;
- spec-37 retains row, collection, and dynamic-key consumer reasons by rung; its final simplified
  direct-key control may be candidate but original remains residual;
- spec-39 retains the successive while/dtype/format/container walls and never supplies the 2.1
  corpus candidate;
- spec-47 retains presentation/threshold walls until its direct uniform-`0.05` positive control;
- labeled-correct `fa_*`/rung cases 14,18,28,36,40,44,46,48,50 retain their exact abstention or
  covered-negative state; and
- syntactically invalid rungs retain the localized parser/envelope result and never disappear from
  the manifest.

The build records the exact per-file oracle before binding activation. Any discrepancy with section
3 is a stop-and-report design regression, not a reason substitution.

### 9.3 Prototype equivalence

Run the frozen corpus-wide prototype implementations for R1 and R2/R3b from `amend_build.py` and
the corresponding final 2.1 classifiers over the same AST/source corpus. Compare, node by node:

- R1 percent-payload classification;
- R1 percent-result sink-only classification;
- R2/R3b assigned and direct-sink If classification; and
- hierarchy movement plus conclusion credit.

The final implementation may be more explicit internally but must be extensionally equal on every
prototype-applicable recon/corpus node. The final R2/R3b comparison additionally proves the
conclusion-census half absent from the measurement prototype. The combined corpus prototype must
reproduce zero correct candidates.

### 9.4 Existing oracle deltas

1. **Thirty opened envelopes:** all E10/E11 adapter-level rows from 2.0 section 10 remain byte-
   equivalent in classification and first reason. E10 remains P2-P6 candidate with P1 reader
   abstention; E11 remains P1-P4/P6 candidate with P5 unresolved-p consumer. N1-N9 in each envelope
   retain their exact complete/abstention outcomes, including E10 N7's adapter-only outside-file
   statistics reason.
2. **PROBE/NEGSIM:** all 2.0 outcomes remain: the twelve admitted PROBE baselines and `NEGSIM_C`
   are candidate/`none`; `PROBE_roundp` is the round reason; `NEGSIM_A` is
   `correction-family-lineage-unresolved`; `NEGSIM_B` is
   `unresolved-manual-correction-present`. No 2.1 admission is needed to preserve them.
3. **E10 P2/P3 ladders:** all P2 original/m1-m8 remain candidate/`none`; P3 original/s1-s6 and s8
   remain candidate/`none`; P3_s7 remains `extra-registered-test-outside-authorized-family`.
4. **2.0 adversaries:** every section-7.2/7.3 fixture retains its exact outcome. The only new
   candidates are known-misstep recall fixtures whose formerly unresolved edge is one section-3
   admission.
5. **1.1 gates:** historical tests keep explicit 1.1 imports. Nothing is retargeted to make 2.1
   coverage. 2.0 tests likewise keep explicit v2 imports.
6. **Correct open-corpus reasons:** all remain noncandidates, but the blanket first-reason equality
   assertion has exactly three carve-outs: `spec-28` moves to `unresolved-decision-threshold`,
   `spec-42` moves to `unresolved-manual-correction-present`, and `spec-48` moves to
   `unresolved-decision-threshold`, as pinned in 7.2. Misstep residual `spec-47` likewise moves from
   `unresolved-pvalue-consumer` to `unresolved-decision-threshold` when R5 exposes its deeper
   designed per-member-threshold wall. No other correct-case first reason may move.

Every legitimate change is a recall gain on a labeled/known misstep: the 17 newly reached corpus
cases plus the two R16 cases. The three correct-case movements above expose a later protective
guard and remain abstentions; no labeled-correct case loses an abstention/covered-negative state.

### 9.5 Prose tripwire

The 2.0 tripwire remains and is extended over every section-3 predicate and every isolated ladder/
adversary fixture. Independently mutate comments, docstrings, reports, Markdown, task text,
annotations, unrelated strings, output labels, format text, and non-callee identifiers; add/remove
report and Markdown files. Rename non-callee identifiers through `bonferroni`, `holm`, `sidak`, and
`benjamini_hochberg`. Facts, first reason, and classification remain byte-equal.

For presentation rules, preserve AST shape while changing every string's bytes and length within
the bound; results remain equal. Cross the exact 256-byte accepted and 257-byte refused shapes.
Only length/NUL/nonempty properties are measured. No conversion token, verdict word, semantic
substring, case, or report phrase is inspected.

Paired structural controls change one slot at a time: Constant format to call, percent right-
operand to retained container, constant If arm to call, same target to different target, single
sink kind/static target to a different sink kind/target, single sink consumer to second consumer,
pure helper return to arithmetic/call, the sole p-formatting IfExp arm to a second constant verdict
arm, bare local threshold to BinOp, exact group Eq to BoolOp, dtype-only call to extra keyword,
straight store to conditional store, field literal to dynamic key, complete zip argument to
unknown/reordered argument, and two-element table to dynamic/three-element table. The two-constant-
arm helper control must reach order 13 rather than disappear from the p slice. Each mutation changes
its named predicate. Deleting a load-bearing structural literal from a positive control changes the
result.

### 9.6 Closed set, replay, isolation, and quality gates

- Public analyzer emitters plus the documented-unreachable annex are set-equal to the 2.1 closed
  reasons; every non-X4 reason has a real exact fixture and X4 reasons use the retained parametrized
  module.
- Explicit frozen 1.0, 1.1, and 2.0 adapters execute historical opened cases and compare canonical
  bytes. The 2.0 anchor imports the four files/digests in 2.3 explicitly, never the active binding.
- The 2.1 adapter executes all 30 opened envelopes and all 50 corpus cases twice byte-identically.
- Two-registry differential proves byte equality and non-derivation for qualified GrantPins,
  grants, qualifications, metric sets, threshold references, and Findings.
- Contract `1.0.0`/`1.1.0` goldens, all error strings, deterministic 98-file census, registry
  digests, and frozen replay records remain exact.
- Full suite, `ruff check .`, `ruff format --check .`, `mypy src`, and
  `python scripts/validate_starter.py` pass after registries/ledger/manifests are regenerated after
  the final file change.

## 10. Evidence projection and candidate meaning

Facts, observation schemas, canonical operands, evidence roles, and wording slots are unchanged.
R11/R12 evidence spans retain the actual registered calls and their source segments; R4/R7/R14/
R16 record the exact p root, transport, decision, and family position; R1/R2/R3b/R5/R13/R18 record
structural sink/decision spans without copying or interpreting display text. Global census receipts
remain syntactic coverage evidence.

A 2.1 candidate still asserts only that the authorized complete family has exactly `N` proved
registered tests and raw conclusions outside complete recognized correction coverage. Absence of a
recognized correction in analyzed source does not establish that none was applied. The detector
does not infer correction, preregistration, importance, or meaning from names, reports, labels, or
display strings.

## 11. Expected score and future blind evaluation

The adapter-level open-corpus oracle is:

```text
labeled correct:  0 / 25 candidates (hard gate)
labeled misstep: 17 / 25 minimum from executed ladders
full R16:        19 / 25 required design outcome
designed ceiling:20 / 25 while the five bin-C protections remain
```

The 19/25 value is an answer-visible regression target, not a promotion estimate. Envelope 12 (or
the next unused envelope number at build time) measures first-contact recall on fresh cases under
the unchanged blind protocol and hard stops from 2.0 section 12: zero negative candidates, zero
Findings, byte-identical replay, and zero FAs in the available/latest-36 class window. First-contact
recall is reported with no per-envelope pass gate; the trailing-18 statistic uses only original
first-contact outcomes. Briefing does not hint at any admission or avoidance shape.

## 12. Reuse map and file-by-file build list

Section 12 of the 2.0 design governs versioning: shared modules are copied, never edited.

| File/surface | Required 2.1 change |
|---|---|
| `ADR-0079-MULTIPLE-TESTING-CODE-SLICE-2.0-INVERSION.md` | Append the reviewed 2.1 delta decision from 2.4; do not rewrite 2.0 policy. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v2_1.py` | Versioned copy of frozen v2 implementing only sections 3-6. No dependence/private-version import. |
| New `src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v2_1.py` | Version `2.1.0`; unchanged schemas/projection; closed-set equality. |
| New `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v2_1.py` | Versioned detector/check wrapper and unchanged operand/ValueError guards. |
| New `src/sc_referee/scientific_checks/integration_multiple_testing_v2_1.py` | Development-only integration and identities. |
| `scientific_checks/profiles.py` | Retain 1.0/1.1/2.0 implementation files; add 2.1 and advance only active development binding. |
| `src/sc_referee/detectors/method_conflict_registry.py` and `method_conflict_finding.py` | Register 2.1 beside historical versions and allow only the exact dev binding to reuse wording v1; no qualified permission. `method_conflict_grant_pins.py` is not edited. |
| Development controller/resources | Dispatch 2.1 only in development; update lane-inclusive digest/locks only where directly derived. |
| New `_v2_1` unit modules | Copy v2 test families, then add exact admission/near-miss, R12/R15 adversaries, reasons, detector guards, integration, prose, and isolation gates. Do not retarget old tests. |
| `evaluation/development/multitest-code-slice-v2_1/` | Checked-in answer-visible accepted/adversarial fixtures and role ledger. |
| `evaluation/development/multitest-recall-recon-corpus20/` | Preserve authoritative evidence; add only a canonical ladder-oracle manifest if needed, without rewriting source rungs. |
| `multitest-open-corpus-v1/adapter_replay.py` and records | Add explicit v2.1 adapter path and byte-gated 2.1 records; retain frozen 1.1/2.0 records and analyzer diagnostic. |
| New 2.1 opened-envelope/recon tests | Section 9.4 thirty-row oracle, PROBE/NEGSIM/P2/P3, every corpus20 ladder rung, and frozen 2.0 replay anchor. |
| Registry resources, capability ledger, source manifests, `MANIFEST.sha256` | Regenerate after the final implementation/test/artifact change in the repository-prescribed order. |

The qualified lane, GrantPins, wording profiles, contract, 1.0/1.1/2.0 MT modules/tests/replay bytes,
and dependence modules are no-edit surfaces.

## 13. Build acceptance and stop-and-report conditions

Build acceptance requires all of the following after the final file change:

1. exact implementation of every finite grammar and refusal in section 3;
2. executed section-5 adversaries, especially all three R12 stores and R15 conservative fallback;
3. paired R2/R3b hierarchy/conclusion and paired R16 transport/position mapping gates;
4. exact 19-candidate/six-abstention adapter-level misstep oracle and `0/25` correct candidates;
5. byte-gated regenerated 2.1 adapter records with frozen 1.1/2.0 entries;
6. every recon ladder file executed with its manifest result;
7. R1/R2/R3b prototype-versus-final equivalence;
8. unchanged 30-row opened-envelope, PROBE/NEGSIM/P2/P3, 2.0 adversary, and historical anchors;
9. effective prose tripwire and structural positive controls;
10. closed-reason set equality and no synthetic reachability;
11. qualified byte equality/non-derivation and contract goldens; and
12. fresh repository-required lint, format, type, full-test, and starter validation gates after
    registry/ledger/manifest regeneration.

If any adapter oracle, correct-case hard gate, frozen replay, dual R2/R16 proof, or qualified
differential cannot pass as written, implementation stops and reports a design regression. It must
not broaden a grammar, weaken a guard, drop a consumer, relabel a reason, alter a correct label, or
adapt the oracle.

## 14. Revision 1 changelog

Revision 1 closes two candidate-surface gaps and corrects oracle/authority documentation. BL-1 and
MJ-1 are strict narrowings. MJ-2 and the oracle correction add no admission. The `MASK.sum()` shape
already existed in the initial design; this revision discloses its design-time extension beyond the
recon summary and adds its ADR/FA obligations rather than enlarging it further.

| Review item | Sections changed | Revision 1 disposition |
|---|---|---|
| BL-1 — R5 verdict cutoff bypass | 3.10, 5, 7.2, 9.1, 9.5 | Requires at least one IfExp arm to format `PFORMAL`; routes two-constant verdict arms through the unchanged order-13 grammar; adds the N=5 `0.01` adversary and records zero corpus recall cost. |
| MJ-1 — R3b sink choice | 3.9, 5, 9.1, 9.5 | Requires identical sink kind and canonical static target in both direct-sink arms; different calls/destinations remain hierarchy. |
| MJ-2 — correct cardinality hazards | 7.2 | Pins `spec-12` and `spec-34` to `test-battery-cardinality-unresolved`, records all four later walls, and names the future strict-subset candidate hazard. |
| Minor 1 — R9 provenance | 2.4, 3.3, 5 | Records `MASK.sum()` as an intentional design-time extension for spec-25, closed to nonfeeding sink-only presentation, for the ADR amendment. |
| Minor 2 — duplicate files | No design section | No design edit: the custodian had already removed and committed the sixteen name-space-2 duplicates before this revision. |
| Minor 3 — correct-case reason movements | 7.2, 9.4 | Replaces blanket first-reason stability with the exact `spec-28`, `spec-42`, and `spec-48` abstention movements; all other correct-case reasons stay pinned. |

## 15. Revision 1a changelog

Revision 1a applies the supervisor's section-13 disposition for one reason-exposure conflict. It
changes no grammar, guard, candidate surface, Finding eligibility, or implementation behavior.
The built 2.1 adapter was also re-audited over all six residual misstep cases: `spec-13`, `spec-23`,
`spec-29`, `spec-37`, and `spec-39` retain their Revision-1 abstention reasons; only `spec-47`
exposes a deeper designed abstention.

| Disposition | Sections changed | Revision 1a result |
|---|---|---|
| `spec-47` reason exposure | 7.1, 7.2, 9.4 | Updates the adapter pin from `unresolved-pvalue-consumer` to `unresolved-decision-threshold`: R5 clears its presentation-helper wall and exposes the unchanged bin-C per-member threshold refusal. The case remains an abstention. |
| Six-residual adapter audit | 7.1, 7.2, 9.4, 15 | Re-executes `spec-13`, `spec-23`, `spec-29`, `spec-37`, `spec-39`, and `spec-47`; the first five retain their pins and none becomes a candidate. |
