# Multiple-testing 3.3 terminal-presentation and helper-record consumer design — 2026-08-30

**Status:** build-ready design, Revision 0  
**Target:** detector/check/adapter `3.3.0`, development lane only  
**Predecessor:** multiple-testing `3.2.0` AP recognition over the `3.0.0` record model and
`3.1.0` question/attestation layer  
**Authority:** frozen scientific-requirement contract profile `1.2.0`; no prose-derived
authority  
**Scope:** two proof-only admissions: terminal presentation controls and one exact
single-call-site helper-returned record consumer  
**Implementation in this session:** none

## 0. Evidence basis, corrected trigger attribution, and prototype/final fidelity

This design is based on:

- the sealed-then-opened E16 evidence and recon in
  `MULTITEST-RECALL-RECON-E16-2026-08-30.md`;
- direct inspection of the five E16 positive sources and all fifteen E16 adapter outcomes;
- instrumented execution of the real 3.2 analyzer and the frozen
  `code_csv_multiple_testing_dataflow_v3.py` hierarchy guard;
- every opened envelope case from E10 through E16, all 50 open-corpus cases, the cumulative
  3.0/B5/3.1/AP safety populations, and a reproduced twelve-case hierarchy fixture set; and
- the strict executable shadow, generated fixtures, canonical results, and self-verifying replay
  under `evaluation/development/multitest-code-slice-v3_3/prototype-sweep/`.

The evidence population is exactly **155 source cases**: **105 opened cases** from E10–E16 plus
**50 corpus cases**. The first 140 are the frozen 3.2 evidence population; E16 adds fifteen. The
prototype additionally executes **203 fixtures**, of which **183** are correct-analysis
adversaries or controls.

### 0.1 Trigger attribution is observed, not inferred

The E16 recon correctly identified the presentation family but marked the particular control
nodes as inferred. `instrument_results.json` resolves that uncertainty using the real 3.2 guard:

| Case | Frozen first reason | First tracked control | One-control probe |
|---|---|---|---|
| E16 P2 `7a43fa7b50f1b99e5034` | `hierarchical-gatekeeping-present` | line 54, the `significant` Name used as the test of the verdict `IfExp` | skipping only that expanded control reaches candidate/`none`, `N=6` |
| E16 P4 `9ced761b41ef93485acf` | `hierarchical-gatekeeping-present` | line 96, `result["p_value"] < ALPHA` in the presentation `If` | skipping only that control reaches candidate/`none`, `N=7` |

The terminal `sum(1 for ...)` expressions in P2 and P4 are **not** their first hierarchy
triggers. P4's direct-p terminal count is already accepted by the frozen terminal-membership
route. P2's count is downstream of the verdict-string transport. Version 3.3 therefore does not
define a broad “terminal count means safe” rule. It proves the exact verdict/presentation
production and separately revalidates the terminal count's total consumers.

The executed P3 ladder is:

| Rung | Real 3.2 outcome |
|---|---|
| sealed source | `unresolved-pvalue-consumer` |
| dict comprehension changed to an explicit loop, helper retained | `pderived-conclusion-family-incomplete` |
| strict single-call helper-record surrogate under section 5 | candidate/`none`, `N=5` |

Thus P3 is not a hierarchy exemption. It requires a bounded helper-return and record-consumer
proof.

### 0.2 Executed projection

The strict combined sweep observes exactly three source movements:

```text
E16:P2:7a43fa7b50f1b99e5034 -> candidate none, corrected_positions {}, N=6
E16:P3:5a9c5b4377c33916d672 -> candidate none, corrected_positions {}, N=5
E16:P4:9ced761b41ef93485acf -> candidate none, corrected_positions {}, N=7
```

All 140 earlier evidence rows are outcome-identical. All other twelve E16 rows are
outcome-identical. Corpus score remains `0/25` correct candidates and `19/25` misstep
candidates. Retro recall becomes E10 `5/6`, E11 `6/6`, E12 `6/6`, E13 `4/6`, E14 `4/6`, E15
`3/6`, E16 `4/6`.

Executed none-flip is:

```text
corpus-correct                 0 / 25
opened negatives               0 / 63
all correct fixtures           0 / 183
cumulative-v3 correct          0 / 62
B5 expression variants         0 / 63
3.1 laundering-adjacent        0 / 16
AP correct                     0 / 13
frozen hierarchy fixtures      0 / 12
new terminal/helper correct    0 / 17
```

The canonical executed artifacts are:

```text
instrumentation  sha256:03c7aa815b8728bf9452afe666f9738e9501f345903ce7ef7fe3f520c320134f
results          sha256:be9ddd1ea4b8bd27faff92392865cbb76f14fbf6b162f847523fe5900d1bd7ad
manifest         sha256:10e94f5a056e50662bfc65bfafc2ebec0ea519a4c7bef1f5269caddf6523bf5f
```

The 43-file manifest binds 432,595 bytes. The builder must pin these values and must not regenerate
the design evidence.

### 0.3 Prototype-to-final direction

The shadow is intended to implement the closed grammars in sections 4 and 5 at design fidelity.
It never classifies a family: it proves an exact control exclusion or exact helper-record graph,
then asks the unchanged 3.2 analyzer to classify the result. Production uses graph facts, not
source rewriting or monkeypatching.

Fidelity remains asymmetric at integration boundaries. A final implementation may be stricter;
none-flip from a looser shadow transfers in the safe direction, but a positive movement does not.
The final implementation must independently re-demonstrate P2, P3, and P4. A final abstention on
one of those three pinned candidates is a section-17 stop just as a candidate on any pinned
noncandidate is. Neither the grammar nor an oracle may be changed toward the other.

## 1. Decision and hard boundary

Version 3.3 adds two narrow value proofs and no scientific classification rule:

1. **Terminal-presentation proof.** One p-derived control is removed from the hierarchy set only
   when its complete owner production is one of the exact shapes in section 4, all downstream
   consumers are terminal, no test/fold/store can depend on it, and it cannot prevent any slice
   node from executing.
2. **Helper-record consumer proof.** One exact single-call-site helper computes a registered test
   and its conclusion adjacently, returns one flat literal record, and is collected by one exact
   complete-family comprehension. Section 5 proves every p/conclusion consumer before exposing
   the equivalent record graph to the unchanged analyzer.

After either proof, the existing 3.2/3.0 machinery alone decides candidate, covered, or abstain.
Version 3.3 adds no test API, correction form, threshold, family-position source, row-mask route,
reader, reducer, record mutation, conclusion polarity, or wording rule.

The following remain outside this delta:

- any p-derived control that can gate a test, correction, family container, fold, store, output
  branch multiplicity, early exit, or unresolved consumer;
- any arbitrary “last statement” or lexical-position inference;
- general helper-return inlining, helpers with multiple call sites, mutable/nonlocal behavior,
  conditional returns, nested records, or unresolved consumers;
- E16 P5's library-subset cardinality and policy question;
- E16 P6's name-set-selected partial manual correction/`None`-sentinel flow;
- factors other than contract `N`, unrecognized correction calls, and every 3.2 residual; and
- changes to the 3.1 question/attestation trust rule or envelope scoring.

## 2. Identities, contract, frozen surfaces, wording, and ADR obligation

### 2.1 Development identities

The new identities are:

```text
check_id         check:authorized-complete-family-correction-over-code-test-battery
check_version    3.3.0
detector_id      detector:bounded-code-csv-multiple-testing-conflict
detector_version 3.3.0
adapter_version  3.3.0
binding_id       method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
```

Only the development binding advances. Versions 1.0, 1.1, 2.0–2.3, and 3.0–3.2 remain registered
for replay. Qualified pseudoreplication `3.1.0`, its GrantPin, grants, qualification records,
metric sets, threshold policies, wording profiles, and `method_conflict_grant_pins.py` remain
byte-untouched.

Contract profile `1.2.0` is unchanged. `N`, the group column, ordered outcome family, and
authorized CSV snapshot come only from that contract and existing structural proof.

### 2.2 Frozen 3.2 anchor

The build pins these current bytes before creating any versioned copy:

```text
dataflow v3_2             sha256:38f74309c4ba082dceb335d95691401b7f9b780958d1c0b82bdb63e496fc29c2
record model v3_2         sha256:919a82cd90391358aa6102db0870ba7af64190949b7bf057c261088611a4e32f
correction model v3_2     sha256:b7c182a9bac2e6e3eb015c2902e607201a5bfdca5f0889413b1145911d30b239
adapter v3_2              sha256:24945b3db1b9ee9a6d6b1e53983cbef0783a7395bd3c53287828fd2d3be0d91b
integration v3_2          sha256:f845dc1f03f7e337fb6ba00bef811a7d319f857cf5ee9643f28c524c846387ea
detector v3_2             sha256:3805178737607d4dbf1769286d2b10eb84f408efc566bc5a2af892d9c6bee5da
scope questions v3_2      sha256:fa183fc97a899109b7c000b0ad28f2d2020c443e591daa34cbbaed3172d7464e
scope attestations v3_2   sha256:8f1ae9e4d02189d40bfe078e4dbf46e446af44433c876abc5b02081dc8ecfd9c
3.2 design                sha256:81e5db51d8f93983497baa7c121dc28ac7dbd3e959dc4961696b87f7e27641bf
3.2 prototype results     sha256:4a512d5e2cf007192430f3d0abacfd614535e2e23348245d4bc8ce8b9f07d80c
3.2 prototype manifest    sha256:3a88349d481cd55378c42723cef3a022672ecfc119fcf723aac05f88d581888e
corpus replay v2_1        sha256:7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502
```

The 3.2 adapter must replay all 155 source inputs through its historical path without byte drift.
The new 3.3 comparison rows are additive. Frozen corpus replay records and all earlier comparison
rows are never regenerated.

### 2.3 Wording and evidence

Wording profile v2 is unchanged. The three movements use the already-defined candidate/`none`
classification and existing slots. No new visible string is required.

Evidence for a terminal proof records only node type, source span, normalized production kind,
owner identity, exact consumer spans, execution-prevention result, family position, and structural
sink identity. Evidence for a helper proof records helper/call spans, exact call-site count,
position map, p/conclusion record-node identities, and consumer spans. It does not record display
text as evidence or infer meaning from a local, field, function, comment, report, Markdown, or
format-string spelling.

String displays are structural only: `ast.Constant` string, nonempty, no NUL, at most 256 UTF-8
bytes. The cap is measured; the bytes are never matched to words such as “significant”,
“direction”, “result”, “primary”, or “corrected”. Format text is never read. Literal record keys
may identify the same structural field edge, but key text never supplies p/conclusion semantics;
lineage does.

### 2.4 ADR-0079 amendment

This delta changes candidate eligibility by removing exact controls from an abstention guard. The
development binding cannot advance until ADR-0079 records:

1. the corrected P2/P4 trigger attribution in 0.1;
2. the three exact terminal productions and total-consumer/execution-prevention proof in section
   4;
3. the exact helper-record graph in section 5;
4. that the hierarchy registry remains global and only proved node occurrences are excluded;
5. that classification, correction recognition, row completeness, and wording remain unchanged;
6. the executed three-row movement set and zero-none-flip populations;
7. the question-census correction in section 11; and
8. the prototype/final asymmetric stop rule.

## 3. Unchanged global censuses, guard universe, and ordered integration

### 3.1 Whole-module censuses stay whole-module

The registered-test, correction-terminal, statistics-prefix, repeated-construct,
dynamic-execution, API-rebinding, and outcome-sequence-mutation censuses run on the untouched AST
before either 3.3 value proof. No surrogate or exclusion can hide a census fact.

Registered family APIs remain exactly:

```text
scipy.stats.ttest_ind
scipy.stats.mannwhitneyu
```

Recognized correction APIs remain exactly:

```text
statsmodels.stats.multitest.multipletests
statsmodels.stats.multitest.fdrcorrection
scipy.stats.false_discovery_control
sc_referee.calculation_checks.bh.benjamini_hochberg
```

Correction terminal slots remain exactly:

```text
multipletests
fdrcorrection
false_discovery_control
multicomp
fdr_correction
p_adjust
padjust
bonferroni
holm
sidak
benjamini*
```

Statistics prefixes remain exactly:

```text
scipy.stats
statsmodels
pingouin
pymer4
bambi
gpboost
merf
linearmodels
sklearn
pymc
numpyro
stan
cmdstanpy
rpy2
lifelines
```

Dynamic execution remains the closed list `exec`, `eval`, `compile`, `__import__`,
`importlib.import_module`, module-receiver `getattr`/`setattr`, and mutation through `globals()` or
`locals()`. API rebinding remains Store to an attribute of a resolved registered/statistics module
or a local Store/definition shadowing an actually live imported API identity or alias.

### 3.2 The hierarchy universe remains global

The control registry continues to include, over the whole module:

- registered-test arguments, correction arguments, conclusion operands, and family-container
  insertions;
- `ast.If.test`, `ast.IfExp.test`, `ast.While.test`, loop iterable/condition nodes,
  `ast.Assert.test`, `ast.Match.subject`, `match_case.guard`, and boolean short-circuit operands
  feeding one of those nodes; and
- every `return`, `break`, `continue`, `raise`, and `sys.exit` edge whose evaluation can prevent a
  slice node from executing, including transitive calls into helpers.

Tracked or jointly-derived provenance still yields `hierarchical-gatekeeping-present`.
Unresolvable prevention still yields `pvalue-control-dependence-unresolved`. Section 4 does not
remove a node kind or owner class. It produces a finite immutable set of **specific control-node
occurrences** proved terminal. All other occurrences stay in this universe.

### 3.3 Ordered integration

The 3.3 analyzer order is:

1. run every unchanged adapter precondition and global census on original bytes;
2. run unchanged 3.2 analysis;
3. only when the first reason is `hierarchical-gatekeeping-present`, attempt the section-4 proof
   for the exact first tracked occurrence, then rerun the versioned hierarchy/dataflow engine with
   that occurrence alone in an immutable terminal-exclusion set;
4. only when the first reason is `unresolved-pvalue-consumer`, attempt the section-5 helper-record
   graph proof;
5. submit the proved graph to the unchanged 3.2 record/AP/classification pipeline; and
6. otherwise return the original first reason byte-for-byte.

If a terminal exclusion merely exposes another hierarchy control, that next control is evaluated
normally. Proofs are not iteratively broadened. A source may use both admissions only if each exact
proof independently succeeds and their graph edges do not overlap; no opened case needs the
combined route in 3.3, so overlapping or mutually dependent routes abstain.

## 4. Closed terminal-presentation grammar

### 4.1 Shared definitions

`PFORM(POS)` is only the unchanged direct family-p expression: the registered test's `.pvalue`
member, its proved scalar Name, its proved record field, or the already-admitted identity wrappers
`bool(PFORM)`/`float(PFORM)`. `THRESHOLD` is only the unchanged order-15 threshold grammar,
including source-text Decimal handling, product rule, and A5 single-binding-anywhere rule. Direct-p
comparisons remain exclusive to order 15; terminal proof cannot classify a threshold.

`PCOMP(POS)` is exactly one `ast.Compare` with one operator from `<`, `<=`, `>`, `>=`, one
comparator, and exactly one operand resolving to `PFORM(POS)`. The other operand must later pass
the unchanged threshold grammar. Chained comparisons, Boolean combinations, calls outside the
identity wrappers, arithmetic, and multiple p origins are refused.

`DISPLAY_STRING` is the structural string form in 2.3. `OUTPUT` is an unshadowed `print` call in an
`ast.Expr`; no keywords. In the section-4.3 production its payload contains no nested `ast.Call`:
only constants, proved Names/attributes/subscripts, tuples/lists, and f-string/percent-format AST
may transport values.
No output call is evidence that a conclusion is scientifically valid. It is merely the terminal
consumer required before a hierarchy exclusion is safe.

`TERMINAL(CONTROL)` is true only when all of the following are proved:

1. the control belongs to one exact production in 4.2–4.4;
2. every value produced under the control has a total forward-consumer account;
3. every produced local/field/collection has one reaching binding and no alias, reassignment,
   augmentation, deletion, subscript Store, receiver mutation, or unresolved escape;
4. the owner and every control-reachable statement contain no registered test/correction call and
   no store consumed by a later test, correction, conclusion, family container, AP fold, or record
   fold;
5. neither the control nor a value derived from it reaches a second output branch or changes
   output cardinality;
6. `can_prevent_slice` proves no `return`, `break`, `continue`, `raise`, `sys.exit`, short-circuit,
   exception edge, or unresolved call can prevent any slice node from executing; and
7. every unclassified consumer or prevention relation refuses the exclusion.

The proof is by graph reachability, not line-number-after-test heuristics. Lexical terminality is
insufficient.

### 4.2 Verdict-local record-and-print production (E16 P2)

The admitted production is exactly:

```text
FLAG = PCOMP(POS)
DISPLAY = DISPLAY_STRING if FLAG else DISPLAY_STRING
RECORD_LITERAL[FIELD] = DISPLAY
FAMILY_COLLECTION.append(RECORD_LITERAL)
OUTPUT(... DISPLAY ...)
COUNT = sum(1 for ITEM in FAMILY_COLLECTION if ITEM[FIELD] EQ DISPLAY_STRING)
OUTPUT(... COUNT ...)
```

with these additional conditions:

1. `FLAG` and `DISPLAY` are simple local Names, each with exactly one Store/definition and no
   alias/rebinding/delete/mutation;
2. the `IfExp` body and orelse are both `DISPLAY_STRING`; its sole control effect is choosing one
   value within one output emission for that family member;
3. every `DISPLAY` load is either the exact field value in the one family-record append, an
   argument payload of the same member's `OUTPUT`, or the proved terminal count route below;
4. `FAMILY_COLLECTION` is the same stable, initially empty list already proved to contain exactly
   one complete-family record per `POS`; only exact `.append(RECORD_LITERAL)` constructs it;
5. the count is one `sum` call with one positional argument and no keywords; that argument is one
   synchronous `GeneratorExp`; its element is integer literal `1`; it has one generator, no
   additional `if`, and no nested comprehension;
6. the count filter is one `==` or `!=` comparison between `ITEM[FIELD]` and one
   `DISPLAY_STRING`, in either operand order; the item iterates the exact family collection;
7. `COUNT` is a simple Name with one Store, and every load is a terminal `OUTPUT` payload; and
8. the display-field identity is structural edge identity. Neither field spelling nor string
   content supplies semantics.

An inline PCOMP-to-two-string `IfExp` may replace `FLAG` only if it is otherwise byte-equivalent to
this graph and the threshold still passes order 15. A destructured flag, call-produced display,
nonconstant arm, missing arm, statement `if`, multiple append, alternate collection, or count used
outside output refuses.

### 4.3 Presentation-If production (E16 P4)

The admitted control is one `ast.If` inside a presentation loop over the already-proved complete
family record collection:

```text
for RECORD in FAMILY_COLLECTION:
    if PCOMP(POS):
        [LOCAL = DISPLAY_STRING | DISPLAY_STRING if NON_P_COMPARE else DISPLAY_STRING]*
        OUTPUT(...)
    else:
        [LOCAL = DISPLAY_STRING | DISPLAY_STRING if NON_P_COMPARE else DISPLAY_STRING]*
        OUTPUT(...)
```

Conditions are exact:

1. the loop iterates the stable complete-family collection directly; no filter, slice, zip,
   enumerate, alternate iterable, runtime membership, or loop `else`;
2. the `If.test` is exactly `PCOMP(POS)` and is the occurrence proposed for exclusion;
3. both arms are present and each contains exactly one `OUTPUT` to the same unshadowed static
   target `print`;
4. every other statement in either arm is a simple `Assign`/`AnnAssign` to one Name, whose value is
   either `DISPLAY_STRING` or an `IfExp` with two `DISPLAY_STRING` arms and a call-free,
   non-p-derived single comparison;
5. every such local has one binding, no alias/mutation/delete, and every load is inside that arm's
   one output payload;
6. the output payload may render already-proved record values but contains no nested call at all;
   in particular it cannot call a test, correction, unresolved consumer, export sink, or
   execution-prevention function;
7. neither branch writes any family record, collection, p, threshold, factor, decision, or value
   used by a later slice node; and
8. the total `TERMINAL` proof in 4.1 succeeds transitively.

Choosing between two sink calls, using different sink kinds/static targets, omitting an arm,
printing twice in one arm, returning a value, or computing a non-display local is not this
production and stays in the hierarchy registry.

### 4.4 Direct terminal-count production

The already-admitted direct-p count remains exact and gains no new conclusion semantics:

```text
COUNT = sum(1 for ITEM in FAMILY_COLLECTION if PCOMP(POS))
OUTPUT(... COUNT ...)
```

It uses the same generator/count binding grammar as 4.2 and must pass `TERMINAL`. Version 3.3
records it so count-to-test, count-to-helper-test, and count-to-early-exit attacks are explicitly
checked, but it does not exclude a new P2/P4 control by itself. A count may never be used as a test,
factor, threshold, selector, family cardinality source, correction argument, return value, or
unresolved-call argument.

### 4.5 Explicit refusal list

Any one of these facts keeps the original hierarchy/unresolved result:

- a registered test or correction anywhere control-reachable under the candidate control,
  including inside a called helper;
- a store under the control consumed by any later test, fold, conclusion, container, or selector;
- `return`, `break`, `continue`, `raise`, `sys.exit`, unresolved exception behavior, or an
  unresolvable prevention relation;
- output in only one branch, different sinks, multiple outputs in a branch, or a second emission
  branch;
- a verdict/count/display value consumed outside the closed transports;
- alias, rebinding, mutation, receiver call, deletion, augmented Store, subscript Store, or escape;
- p arithmetic, unrecognized threshold, correction-shaped call, export, extremum, resampling, or
  hierarchy through another control;
- conditional family construction, incomplete positions, duplicate positions, or a collection
  that is not stable and complete; or
- reliance on identifier spelling, display text, comments, or lexical “after the tests” position.

## 5. Closed helper-returned record consumer grammar

### 5.1 Exact call and collection production

The only admitted helper route is:

```text
def HELPER(FRAME, OUTCOME):
    ... one registered two-group test for OUTCOME ...
    return {LITERAL_KEY: SCALAR_VALUE, ...,
            P_KEY: PFORM(POS),
            D_KEY: PCOMP(POS)}

RECORDS = {OUTCOME: HELPER(FRAME, OUTCOME) for OUTCOME in OUTCOMES}
for OUTCOME, RECORD in RECORDS.items():
    DISPLAY = DISPLAY_STRING if RECORD[D_KEY] else DISPLAY_STRING
    OUTPUT(... RECORD[P_KEY] ... DISPLAY ...)
```

It is admitted only if:

1. `HELPER` is one top-level synchronous `FunctionDef`, resolved by an unshadowed simple Name, with
   exactly two ordinary positional parameters, no positional-only/keyword-only/default/variadic
   parameters, decorators, return annotation, type comment, nested definition, recursion, or
   closure dependency;
2. there is exactly one call site in the module, and it is the value expression of the exact
   comprehension shown; divergent arguments or a second call refuse;
3. the comprehension has one synchronous generator, no `if`, no nested comprehension, one simple
   target Name, the same Name as dict key and helper outcome argument, and iterates a flat
   list/tuple display (or one stable module Name resolving to it) whose scalar literal elements are
   order-equal to the contract outcome list;
4. `FRAME` resolves through the unchanged authorized-reader, group-split, row-completeness, and X4
   machinery; no new reader or row-mask route is created;
5. the helper has an optional docstring, then only simple `Assign`/`AnnAssign` statements and one
   final `Return`; it contains exactly one registered test and no `if`, loop, comprehension,
   `try`, `with`, `match`, lambda, nested definition/class, `global`, `nonlocal`, delete,
   augmented assignment, named expression, await, yield, or early exit;
6. the returned value is one flat `ast.Dict` literal with non-null unique literal string/integer
   keys and scalar values; no nested dict/list/tuple/set, unpack, conditional record, alias, or
   post-construction mutation;
7. exactly one returned field resolves directly to the registered p result, optionally through
   the unchanged identity wrappers, and exactly one field resolves to its direct order-15 decision;
8. every other value is proved by the unchanged dataflow/reducer grammar or ignored as an
   output-only sibling; sibling fields never become p/conclusion evidence;
9. `RECORDS` has one binding, no alias/reassignment/mutation/delete/escape, and its only load is the
   receiver of one exact `.items()` call with no args/keywords in one presentation loop; and
10. family position comes from the comprehension's contract-order outcome key, not runtime dict
    order, source line order, record key spelling, or presentation iteration order.

### 5.2 Total record-consumer proof

The returned p field and decision field are tracked independently but must map to the same
singleton `POS` record occurrence.

For every p-field load outside the helper, the only admitted consumer is an existing terminal
output transport in the one presentation loop. A comparison, correction, store, selector,
container insertion, return, export, or unresolved call refuses.

For the decision field, the only admitted load is the entire test of one `IfExp` with two
`DISPLAY_STRING` arms. That `IfExp` binds one simple display Name exactly once; every load of that
Name reaches the loop's `OUTPUT`. No decision field may gate a statement, test, correction,
container, second output branch, or early exit.

Every collection, record, p field, decision field, display local, and helper-local p binding gets a
total forward-consumer account. An unclassified load is absorbing `UNRESOLVED`; the helper route
does not partially succeed.

### 5.3 Graph lowering and classification boundary

Production represents the proved helper as the same immutable per-position record graph the 3.0
record model already consumes:

```text
for POS, OUTCOME in contract_order:
    [the helper's proved scalar operations with formal bindings substituted]
    RECORDS.append(RECORD(POS, ... P(POS) ..., D(POS) ...))
```

The graph carries a synthetic internal position edge; it does not inject a source key, execute the
helper, or infer from record iteration order. Alpha-renamed helper locals cannot collide with the
caller. The original AST remains the input to global censuses.

The unchanged 3.2 analyzer must independently re-prove exact test census, operand identity, row
completeness, threshold, conclusion completeness, record polarity, p consumers, correction
absence/AP, and family classification on this graph. If it does not return candidate/covered, its
reason is returned. A helper proof never classifies directly.

### 5.4 Explicit refusal list

The helper route refuses on:

- multiple or unresolved call sites; divergent frame/outcome arguments; recursion or reentry;
- async/decorator/default/variadic/closure/nested-definition/global/nonlocal behavior;
- any mutation or unresolved receiver/call escape, including mutation of caller or nonlocal state;
- branch, loop, filtered comprehension, conditional Store/return, multiple return, early exit, or
  exception-dependent construction;
- zero or multiple registered tests, unregistered dispatch, mixed/duplicate test for one outcome,
  unresolved operands, or incomplete/duplicate/out-of-order outcomes;
- heterogeneous/nested/unpacked records, dynamic keys, aliases, later stores, slices, filters, or
  alternate collections;
- zero/multiple p fields, zero/multiple decision fields, ambiguous polarity, raw/adjusted merge,
  duplicate conclusion, or conclusion recomputed outside the helper from raw p;
- a p/decision load in any nonterminal consumer; or
- any proof that depends on a function/field/local/display spelling or source prose.

## 6. Classification and closed reasons

### 6.1 Classification is frozen

After admission, classification is exactly the existing 3.2 result:

- raw conclusions for all `N` positions with no recognized correction -> candidate/`none`;
- a proved proper corrected subset with raw conclusions outside -> candidate/`strict_subset`;
- complete recognized correction and corrected conclusions -> covered/`complete`;
- any unresolved graph fact -> the existing abstention reason.

The terminal/helper layers never create corrected positions, change `N`, choose an API, or alter a
conclusion. They only allow frozen analysis to see already-existing raw conclusions.

### 6.2 Closed reason set remains 61

No reason is added, retired, or relabeled. The 3.3 closed set is exactly:

```text
additional-accepted-reader-present
alternate-analysis-file-present
analysis-scope-structure-unsupported
analysis-source-envelope-unavailable
api-resolution-ambiguous
authorized-family-cardinality-below-three
authorized-family-csv-domain-unavailable
authorized-family-test-census-incomplete
authorized-group-domain-not-exactly-two
authorized-reader-lineage-unavailable
authorized-test-family-shape-unsupported
conclusion-output-sink-unavailable
correction-family-lineage-unresolved
dataflow-definition-ceiling-exceeded
dataframe-pvalue-table-unresolved
extra-registered-test-outside-authorized-family
family-pvalue-extremum-reduction-present
family-test-api-dispatch-unresolved
frozen-authority-material-mismatch
helper-argument-binding-unsupported
helper-async-decorator-or-yield-unsupported
helper-body-statement-unsupported
helper-call-site-reentry-unsupported
helper-callee-not-simple-name
helper-closure-or-nested-definition-unsupported
helper-definition-unavailable-or-nonunique
helper-free-name-unbound
helper-global-nonlocal-unsupported
helper-inlining-depth-exceeded
helper-parameter-default-unsupported
helper-parameter-shape-unsupported
helper-recursion-unsupported
helper-return-count-unsupported
helper-return-expression-unsupported
helper-return-position-unsupported
helper-variadic-parameter-unsupported
hierarchical-gatekeeping-present
multiple-family-partition-present
multiple-registered-tests-for-family-member
multiple-testing-code-inspection-exception
pderived-conclusion-family-incomplete
permutation-family-control-present
pvalue-control-dependence-unresolved
pvalue-family-collection-unresolved
pvalue-scalar-cast-or-rounding-unsupported
record-decision-polarity-unresolved
record-duplicate-conclusion-ambiguous
record-family-lineage-unresolved
record-family-mutation-unresolved
record-subset-position-unresolved
resampling-cardinality-unresolved
selected-group-row-completeness-unproven
statistics-api-imported-outside-analysis-py
test-battery-cardinality-unresolved
test-operand-lineage-unresolved
unresolved-decision-threshold
unresolved-inference-sibling-present
unresolved-manual-correction-present
unresolved-pvalue-consumer
upstream-correction-lineage-unresolved
verified-contract-authority-unavailable
```

The build gate asserts `closed reasons == emitting reasons + documented-unreachable annex` using
only 3.3 test files. Terminal/helper refusal uses the already-owning guard's reason. It must not
invent a presentation-specific reason merely to make fixtures legible.

## 7. Load-bearing false-accusation analysis

The accusation-safety invariant is:

> A control is excluded only after total proof that it changes presentation and cannot change
> tests, correction, family construction, conclusion origin, execution, or output multiplicity;
> a helper record is exposed only after every p/conclusion edge is resolved. Global censuses and
> the unchanged classifier then independently prove the scientific claim.

The strongest correct-analysis attacks and their blockers are:

| Admission | Strongest correct-analysis shape | Required blocker |
|---|---|---|
| terminal count | count gates a later registered test | untouched call census and transitive `can_prevent_slice`; `authorized-family-test-census-incomplete` in fixture |
| terminal count | count gates `stage_two()` containing a registered test | helper-transitive call/control closure; census-incomplete |
| terminal count | count triggers `sys.exit` | whole-module execution-prevention edge; hierarchy |
| verdict-local | display local passed to an unresolved call | total consumer failure; hierarchy |
| verdict-local | display chooses a second emission branch | sole-control-effect and same-output-cardinality failure; hierarchy |
| verdict-local | verdict local becomes a correction-fold factor | unchanged correction/forward guard; unresolved manual correction |
| presentation If | branch writes corrected p into record | store/fold consumer and mutation guard; unresolved manual correction |
| presentation If | branch raises | execution-prevention guard; hierarchy |
| presentation If | direction local becomes fold factor | total consumer and correction guard; unresolved manual correction |
| presentation If | owner contains a correction call | global correction census plus owner-subtree refusal |
| helper record | helper called twice with divergent arguments | exactly-one-call-site proof plus exact call census; extra test |
| helper record | helper mutates nonlocal/caller state | branch-free/state-closed helper refusal; unresolved p consumer |
| helper record | outside code recomputes conclusion from raw p | total p-field consumer failure; unresolved p consumer |
| helper record | helper conditionally stores/returns | branch-free construction refusal |
| helper record | comprehension filters outcomes | complete ordered battery proof; census-incomplete |
| helper record | nested record hides corrected/raw origins | flat-literal record refusal; unresolved p consumer |
| helper record | p/decision record flows to unknown consumer | total forward closure; unresolved p consumer |

These blockers do not depend on an analysis being malicious. They are the conservative treatment
of a correct analysis whose correction or staged testing would otherwise be crossed silently.

## 8. Executable fixture matrix

### 8.1 Four positive controls

| Fixture | Expected |
|---|---|
| `positive-terminal-verdict-record-print` | candidate/`none`, `N=6` |
| `positive-terminal-direction-if-print` | candidate/`none`, `N=7` |
| `positive-terminal-count-output` | unchanged candidate/`none`, `N=7`; proves the existing count route remains admitted |
| `positive-helper-record-single-call-comprehension` | candidate/`none`, `N=5` |

The first, second, and fourth are the exact E16 P2/P4/P3 sources. A final candidate is asserted
exactly once with zero Findings.

### 8.2 Seventeen new correct-analysis adversaries

| Fixture | Exact outcome |
|---|---|
| `correct-terminal-count-gates-later-test` | `authorized-family-test-census-incomplete` |
| `correct-terminal-count-sys-exit` | `hierarchical-gatekeeping-present` |
| `correct-terminal-count-gates-helper-test` | `authorized-family-test-census-incomplete` |
| `correct-presentation-if-record-store` | `unresolved-manual-correction-present` |
| `correct-presentation-if-raise` | `hierarchical-gatekeeping-present` |
| `correct-presentation-local-rebound-into-fold` | `unresolved-manual-correction-present` |
| `correct-terminal-verdict-unresolved-consumer` | `hierarchical-gatekeeping-present` |
| `correct-terminal-verdict-second-emission-branch` | `hierarchical-gatekeeping-present` |
| `correct-terminal-verdict-rebound-fold-factor` | `unresolved-manual-correction-present` |
| `correct-presentation-owner-correction-call` | `hierarchical-gatekeeping-present` at the unchanged order |
| `correct-helper-record-multiple-call-sites-divergent` | `extra-registered-test-outside-authorized-family` |
| `correct-helper-record-mutates-nonlocal-state` | `unresolved-pvalue-consumer` |
| `correct-helper-record-conclusion-recomputed-from-raw-p` | `unresolved-pvalue-consumer` |
| `correct-helper-record-conditional-store` | `unresolved-pvalue-consumer` |
| `correct-helper-record-comprehension-filter` | `authorized-family-test-census-incomplete` |
| `correct-helper-record-nested-record` | `unresolved-pvalue-consumer` |
| `correct-helper-record-unresolved-consumer` | `unresolved-pvalue-consumer` |

### 8.3 Twelve reproduced hierarchy fixtures

The build checks these exact rows against both 3.2 and 3.3:

```text
frozen-gate-numpy-omnibus-assert                 hierarchical-gatekeeping-present
frozen-gate-match-subject-and-guard              hierarchical-gatekeeping-present
frozen-gate-bool-short-circuit-assert            hierarchical-gatekeeping-present
frozen-gate-rendering-unresolved-consumer         hierarchical-gatekeeping-present
frozen-gate-rendering-second-branch               hierarchical-gatekeeping-present
frozen-gate-rendering-call-arm                    hierarchical-gatekeeping-present
frozen-gate-early-return                         hierarchical-gatekeeping-present
frozen-gate-early-break                          hierarchical-gatekeeping-present
frozen-gate-early-continue                       hierarchical-gatekeeping-present
frozen-gate-early-raise                          hierarchical-gatekeeping-present
frozen-gate-early-sys-exit                       hierarchical-gatekeeping-present
frozen-gate-unresolved-execution-prevention       pvalue-control-dependence-unresolved
```

This includes `assert`, `match`, short-circuit, early-exit, and the execution-prevention residual.
No control kind is silently lost when the hierarchy guard is versioned.

### 8.4 Cumulative populations

The final implementation executes all **203** rows, not fixture-shaped assertions:

| Population | Rows |
|---|---:|
| frozen 3.0 original | 48 |
| audit fix R1 | 14 |
| audit fix R2 | 4 |
| audit fix R3 | 5 |
| B5 field/expression grid | 63 |
| 3.1 laundering-adjacent | 16 |
| AP 3.2 | 20 |
| reproduced hierarchy | 12 |
| new terminal positives/adversaries | 13 |
| new helper positive/adversaries | 8 |
| **total** | **203** |

All frozen expected outcomes remain exact. All correct rows remain noncandidates. The prior B1–B5,
merge, mutation, laundering, AP-consumption, answer-removal, and false-clearance gates remain
active even when no new 3.3 predicate touches their source.

## 9. Adapter oracle — all opened cases

### 9.1 E16 fifteen-row oracle

The real 3.3 adapter must produce:

| Role/case | 3.2 outcome | 3.3 pinned outcome |
|---|---|---|
| P1 `c89a2a4259f96b413be8` | candidate/`none`, `N=4` | byte-identical |
| P2 `7a43fa7b50f1b99e5034` | `hierarchical-gatekeeping-present` | candidate/`none`, positions `{}`, `N=6` |
| P3 `5a9c5b4377c33916d672` | `unresolved-pvalue-consumer` | candidate/`none`, positions `{}`, `N=5` |
| P4 `9ced761b41ef93485acf` | `hierarchical-gatekeeping-present` | candidate/`none`, positions `{}`, `N=7` |
| P5 `7be23db36040f5be1df2` | `test-battery-cardinality-unresolved` | byte-identical |
| P6 `8ff6de728df8f29261aa` | `unresolved-manual-correction-present` | byte-identical |
| N1 `76f0e7831f3856df66d5` | covered/`complete`, positions `{0,1,2,3,4}` of 5 | byte-identical |
| N2 `f0214d4b77f589655ac3` | `unresolved-decision-threshold` | byte-identical |
| N3 `6c45fce29073c572d8c0` | `unresolved-manual-correction-present` | byte-identical |
| N4 `b1b81b953f324b7e4f75` | `extra-registered-test-outside-authorized-family` | byte-identical |
| N5 `298a1432b9b550031f5d` | `extra-registered-test-outside-authorized-family` | byte-identical |
| N6 `6d5e78b815b73081865f` | `authorized-reader-lineage-unavailable` | byte-identical |
| N7 `9155ca1dd76fa5c630b1` | `authorized-family-test-census-incomplete` | byte-identical |
| N8 `8b9b2171434ddd20b63f` | `test-battery-cardinality-unresolved` | byte-identical |
| N9 `a5a32dcc59d4f3acd943` | `unresolved-decision-threshold` | byte-identical |

The movement set must equal `{E16:P2, E16:P3, E16:P4}` exactly. All nine negatives remain
noncandidates; N1 remains true covered/complete.

### 9.2 E10–E15 historical oracles

All 90 adapter rows are byte-identical to their frozen 3.2 results. The gate compares canonical
rows, not only state/reason. It retains the known adapter/source distinction for E10 N7:
`statistics-api-imported-outside-analysis-py` at adapter level. No analyzer-only replay may replace
the adapter oracle.

Retro candidate recall after applying 3.3 to opened bytes is:

```text
E10 5/6
E11 6/6
E12 6/6
E13 4/6
E14 4/6
E15 3/6
E16 4/6
```

These are development projections and never rescore sealed first-contact envelopes.

## 10. Open-corpus oracle — all 50 cases

Every adapter row is byte-identical to the 3.2 comparison row. The frozen
`adapter_replay_records_v2_1.json` bytes remain untouched. Version 3.3 adds a comparison row set
equal to 3.2:

```text
labeled correct: 25, candidates 0
labeled misstep: 25, candidates 19
movements: 0
```

The adapter-level exception remains corpus spec-30: `api-resolution-ambiguous` at adapter level,
even though the source analyzer exposes a later manual-correction reason. The corpus gate is
adapter-level.

## 11. Interaction with 3.1 questions and attestations

The no-attestation correction-scope question census through E16 is **25**, not 22:

```text
opened 16
corpus  9
total  25
```

The 3.2 population through E15/corpus had 22. E16 adds scope questions on P6, N2, and N3. E16 N9
has a qualifying reason but no structural witness, so emits no scope question.

E16 P2, P3, and P4 carried **no correction-scope MaterialQuestion under 3.2**. The sealed records'
MaterialQuestion on those cases is the unrelated publication-surface question. Consequently the
executed 3.3 census is `25 -> 25`, removed set empty. This corrects the tentative expectation that
their questions “should resolve”: their MT ambiguity resolves to candidates, but there is no MT
scope question to remove, and 3.3 must not delete an unrelated public record.

All attestation trust asymmetry is unchanged. A B answer cannot use a terminal/helper proof to do
anything the answer-removed analyzer cannot do. Existing answer-removal equivalence, false-clearance,
four-record-type, scoring-isolation, and no-carry-forward gates remain byte-identical.

## 12. Determinism, idempotence, ordering, and prose tripwire

### 12.1 Determinism and idempotence

Terminal exclusions are immutable sorted source-position identities plus node-type/owner digests.
Applying the proof twice yields the same set; an already-excluded node cannot create a second
exclusion. Equal source positions in different owners never collide.

Helper graph lowering uses ordered contract positions and alpha-renamed local graph identities.
Applying it twice recognizes the already-normalized graph and makes no change. Record occurrence
multiplicity and the 2.3 ordinal rules remain intact; an ordinal is bookkeeping only, never an
evidence value or position substitute.

Global censuses always see original bytes. Section-4 proof precedes section-5 proof only in the
fixed order in 3.3; overlapping graphs abstain. The 3.2 AP transformer order and second-pass
idempotence are untouched.

Identical project bytes, contract, registry, CSV snapshot, and attestations produce byte-identical
module rows, evidence, questions, disclosures, concerns, Findings, lock bytes, and replay records.
No timestamp enters identity or classification.

### 12.2 Prose/evidence tripwire

Every new predicate is run against paired mutations that:

- add/remove comments, docstrings, reports, and Markdown containing every fixture label and guard
  phrase;
- rename noncallee identifiers and literal record fields to correction-like and presentation-like
  spellings;
- replace display strings with same-byte-length arbitrary strings;
- alter format text without changing value-lineage AST; and
- rename a true callee slot as the paired positive control for the global terminal census.

Candidate/abstention bytes must stay identical for prose/noncallee/display mutations. Deleting a
load-bearing structural literal or changing a callee terminal must change the appropriate proof,
which is the positive control. The 256-byte string cap is measured; no string payload is inspected
for scientific words.

## 13. Reuse map and file-by-file build plan

### 13.1 Frozen files copied, never edited

The 3.2 modules in 2.2 are byte-frozen. The build creates versioned 3.3 files following the 3.2
registry pattern. In particular, the original
`code_csv_multiple_testing_dataflow_v3.py` and every dependence dataflow file remain untouched.

### 13.2 New versioned production files

The build adds:

- `src/sc_referee/scientific_checks/code_csv_multiple_testing_terminal_presentation_v3_3.py` —
  section-4 graph proof and immutable exclusion set;
- `src/sc_referee/scientific_checks/code_csv_multiple_testing_helper_record_v3_3.py` — section-5
  graph proof;
- `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_3.py` — versioned copied
  hierarchy integration; the only guard change is accepting the explicit proved-occurrence set;
- versioned `record_model_v3_3.py` and `correction_model_v3_3.py` wrappers/copies as required by
  registry identity, with 3.2 behavior otherwise byte-equivalent;
- `code_csv_multiple_testing_adapter_v3_3.py` and
  `integration_multiple_testing_v3_3.py`;
- `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3_3.py`; and
- versioned scope-question/attestation wrappers only if registry identity requires them; their
  classification and public-record behavior remain byte-equivalent.

Production must not monkeypatch `_MtEngine._control_tracked` and must not rewrite source text. The
prototype techniques are development evidence only.

### 13.3 Narrow shared edits

Allowed shared edits are limited to:

- development binding/registry entries for 3.3 while retaining historical registrations;
- scientific registry and capability-ledger entries;
- package exports/import dispatch;
- ADR-0079 amendment and generated registry/ledger/manifest bytes; and
- `docs/AGENTIC_SKILL.md` only if a version display must advance, with no attestation-flow change.

No GrantPin, qualified binding, qualified Finding path, wording template, contract profile, scoring
rule, or pseudoreplication file changes.

### 13.4 Tests and artifacts

Add versioned tests for:

- all section-4 and section-5 grammar productions/disqualifiers;
- the exact P2/P3/P4 adapter movements;
- all 105 opened rows and 50 corpus rows;
- all 203 fixtures and closed-reason set equality;
- hierarchy occurrence identity, helper alpha-renaming, idempotence, and ordering;
- prose tripwire and output identity;
- frozen 3.2 adapter/detector/integration/replay anchors; and
- qualified-lane differential nonderivation.

The checked-in prototype artifacts in this commission are frozen design evidence, not test
expectations derived from production code.

## 14. Validation plan and executable gates

### 14.1 Prototype evidence gate

From repository root, the builder runs:

```bash
PYTHONPATH=src:evaluation/development/multitest-code-slice-v3_3/prototype-sweep \
  .venv/bin/python evaluation/development/multitest-code-slice-v3_3/prototype-sweep/verify.py
```

The verifier must reproduce `instrument_results.json` and `results.json` byte-for-byte and verify
every manifest digest. Required values are:

```text
cases                           155 (105 opened + 50 corpus)
frozen prior rows identical     140
movements                       exactly E16 P2/P3/P4
fixtures                        203
correct fixtures                183
opened-negative candidates      0/63
corpus-correct candidates       0/25
all-correct-fixture candidates  0/183
question census                 25 -> 25, removed {}
```

### 14.2 Final implementation gates

The build must execute and pass:

1. the real-guard attribution test at the exact P2/P4 source positions;
2. the three positive movements with exact `N`, classification, positions `{}`, one candidate,
   and zero Findings;
3. the complete E16 fifteen-row adapter oracle and exact movement-set equality;
4. byte identity for all 90 E10–E15 rows and all 50 corpus rows;
5. all 203 fixtures with exact expected outcomes;
6. none-flip `0/25`, `0/63`, `0/183`, plus every named subset in 0.2;
7. question census `16 opened + 9 corpus = 25`, no removed MT question, unrelated publication
   questions untouched;
8. the 61-reason closed-set gate scoped only to 3.3 tests;
9. all prior E10–E16, corpus, PROBE/NEGSIM/ladder, record, AP, question, attestation, and replay
   anchors;
10. frozen 3.2 implementation and result digests;
11. development-only binding and qualified-lane byte/non-derivation differential; and
12. deterministic replay equality, including 15/15 envelope replay and attested runs.

### 14.3 Quality and generated-file order

After the final source/test edit, regenerate registries, ledger, and manifest in that order, then
run fresh:

```bash
ruff check .
ruff format --check .
mypy src
pytest
python scripts/validate_starter.py
```

No suite-green claim may precede the final manifest-covered edit.

## 15. Residuals and honest read

### 15.1 Deliberate residuals

The following stay abstentions:

- E16 P5: correction library receives a proper subset while the declared family has six outcomes;
  cardinality/policy remains `test-battery-cardinality-unresolved`;
- E16 P6: exact hand fold applies under a name-set selector with `None` sentinel and second-loop
  consumption; the 3.2 question remains the safe result;
- factors unequal to `N`, proper-subset policy not structurally proved, unrecognized libraries,
  zip write-back outside the frozen grammar, and DataFrame correction routes outside 3.0/3.2;
- general helper-return records, multi-call helpers, conditional helpers, nested/heterogeneous
  records, recomputed conclusions, and presentation decisions outside sections 4–5; and
- every staged/gated analysis covered by the hierarchy fixture population.

### 15.2 What 3.3 buys

On opened E16 bytes, the full delta moves the plain uncorrected loop families P2 and P4 and the
adjacent helper-record family P3. E16 retro recall is therefore `4/6`, up from the sealed first
contact `1/6`. This is evidence that the two shape families are recognizer walls, not a forecast
that future authors will use them at the same rate.

Corpus recall remains `19/25`; the hard correct-case gate remains `0/25`. The delta does not spend
false-accusation budget to reopen the six corpus residuals.

### 15.3 E17/E18 arrival and promotion arithmetic

The live promotion window is E17+E18 and requires at least **7 catches out of 12**. That can be
`4+3`, `3+4`, `5+2`, or stronger. Retro-applying 3.3 to E16 gives `4/6`, but sealed E16 remains
`1/6` and cannot be rescored. The evidence supports terminal loop presentation as a recurring
idiom and helper-return records as a plausible arrival, but does **not** yet support a prospective
claim of four catches per envelope. Fresh cases can move to earlier or different walls, as prior
arrival curves did.

E17/E18 therefore measure first contact without a recall gate per envelope. The cumulative
promotion arithmetic is reported honestly after both. Remaining likely misses include subset
policy, name-selected partial folds, unregistered correction paths, and helper/record graphs beyond
the exact closure here.

## 16. Scoring and public-record isolation

Questions are not catches; disclosures, concerns, covered outcomes, and Findings remain distinct.
Blind envelopes provide no attestations. Version 3.3 does not alter envelope scoring, promotion
arithmetic, role maps, or sealed audit bytes. The three retro candidates are development evidence
only. No new route can create a Finding without the unchanged candidate adapter and wording
requirements.

## 17. Stop-and-report rule

Stop and report a design regression rather than changing a grammar, reason, or oracle if any of
the following occurs:

1. P2, P3, or P4 does not reach its exact pinned candidate under the final strict implementation;
2. any other evidence row moves or any E16 negative becomes a candidate;
3. corpus correct candidates exceed `0/25`, opened-negative candidates exceed `0/63`, or any
   correct fixture becomes a candidate;
4. a count-to-test/helper-test/sys.exit fixture crosses the hierarchy/census guard;
5. a verdict/display value reaches a fold, store, unresolved call, second emission, or early exit
   while its control is excluded;
6. a helper with divergent call sites, nonlocal mutation, conditional construction, nested record,
   outside raw-p conclusion, incomplete family, or unresolved consumer is admitted;
7. global censuses observe normalized/surrogate rather than original bytes;
8. the versioned hierarchy copy drops `assert`, `match`, short-circuit, early-exit, or unresolved
   prevention behavior;
9. the unchanged 3.2 classifier is bypassed or a 3.3 proof assigns a classification/corrected
   position;
10. question census differs from 25 or a non-MT MaterialQuestion is removed;
11. closed reasons differ from 61 or a surviving reason is relabeled;
12. display text, identifier spelling, comments, reports, or Markdown change a predicate;
13. any frozen 3.2 file/result, corpus replay record, prior comparison row, qualified lane,
    GrantPin, wording object, or scoring byte changes outside enumerated registry noise;
14. applying either proof twice changes graph/exclusion bytes;
15. prototype replay, adapter replay, answer-removal equivalence, or deterministic output differs;
    or
16. a required quality gate cannot pass after generated files are finalized.

Conservative abstention on an unpinned shape is acceptable. Conservative abstention on a pinned
P2/P3/P4 positive is a stop in the other direction, not permission to loosen the design.

## 18. Revision log

### Revision 0 — 2026-08-30

- instrumented the real 3.2 hierarchy guard and replaced the E16 recon's inferred count-trigger
  attribution with observed P2 verdict-`IfExp` and P4 presentation-`If` positions;
- designed the exact terminal verdict, presentation-If, and terminal-count productions with total
  consumer and execution-prevention closure;
- designed the exact single-call-site helper-returned flat-record consumer proof;
- executed all 155 evidence cases and 203 fixtures, pinning exactly three movements and all
  none-flip counts;
- retained frozen 3.2 classification, global censuses, 61 reasons, wording, contract, qualified
  lane, questions/attestations, and scoring; and
- recorded the evidence-based `25 -> 25` question census and E17/E18 promotion arithmetic.
