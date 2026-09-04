# Multiple-testing 3.5 recall-delta design, 2026-09-03

**Status:** build-ready design, Revision 0
**Target:** detector/check/adapter `3.5.0`, development lane only
**Predecessor:** multiple-testing `3.4.0` comprehension/iterator/cap admissions plus audit-fix
rounds 1 to 7 and the frozen-lane performance re-pin, at repo `f23c750c`
**Authority:** frozen scientific-requirement contract profile `1.2.0`; no prose-derived authority
**Scope:** four shipped syntactic admissions in three groups, two specified and unshipped, and no
new scientific classification rule. No new abstention reason: the closed set stays at 61
**Implementation in this session:** none

## 0. Recon inputs, observed trigger attribution, and prototype/final fidelity

### 0.1 Evidence basis

This design is based on:

- the sealed-then-opened E18 evidence in `blind-envelope-18-2026-09-01`, scored recall `2/6`,
  `0/9` accusation candidates, `0` Findings, replay `15/15`;
- `docs/implementation/MULTITEST-RECALL-RECON-E18-2026-09-02.md` sections 2 and 5, whose first
  triggers are captured frame values;
- `docs/implementation/MULTITEST-RECALL-RECON-MANUAL-CORRECTION-2026-09-03.md` section 2.3, which
  supplies delta 5 (added to scope by the custodian after the first four were measured);
- `docs/implementation/MULTITEST-RECALL-RECON-E16-2026-08-30.md` item 1, whose loop form is
  delta 4b;
- direct instrumented execution of the shipped `3.3` hierarchy guard, group-mask frame model,
  reader census, off-grammar transform guard, and the shipped `3.4` correction recogniser;
- every opened envelope case from E10 through E18, all 50 open-corpus cases, and the cumulative
  3.0/B5/3.1/AP/3.3/3.4 safety populations; and
- the strict executable shadow, generated fixtures, canonical results, and self-verifying replay
  under `evaluation/development/multitest-code-slice-v3_5/prototype-sweep/`.

The evidence population is exactly **185 source cases**: **135 opened cases** from E10 to E18 plus
**50 corpus cases**. The first 170 are the frozen 3.4 evidence population; E18 adds fifteen. The
prototype additionally executes **283 fixtures**, of which **199** carry the correct-analysis label
and **245** are the byte-chained frozen 3.4 population.

### 0.2 The five deltas, and which of them can move anything

The brief scoped four deltas from the E18 recon plus one from the manual-correction recon. The
executed sweep splits them in two, and the split is the main finding of this design.

| Delta | Wall it opens | Measured movement | Disposition |
|---|---|---|---|
| 1 | formatted display arms in the three terminal-rendering arm positions | E18 P2 becomes a catch | **shipped** |
| 2 | set literals in the AP selector's per-row truth evaluation | none; it sits behind delta 3 | specified, **not shipped** |
| 3 | standard-library `csv` reader lineage | none; a third wall sits behind it | specified, **not shipped** |
| 4a+4b | numeric group-mask comparator, plus a terminal-position proof for a presentation loop | E18 P3 becomes a catch, E17 N1 becomes a true clearance | **shipped as a pair** |
| 5 | cardinality read of the reconstructed p-record family in a display | E15 P3 becomes a catch | **shipped** |

Deltas 2 and 3 are specified in full in sections 1.2 and 1.3, with their executed grammar proofs,
and are not installed. The reason is measured, not argued, and section 2.4 states it.

### 0.3 Prototype-to-final direction

The shadow implements the closed grammars in section 1 at design fidelity. It never classifies a
family. It proves one exact syntactic production, admits only that production, and asks the
unchanged shipped machinery to classify the result.

Three prototype techniques are development evidence only and are forbidden in production:

1. every production is installed by replacing a named module-level function or bound method for
   the duration of one re-analysis. Production must widen those recognisers in versioned copies,
   never by monkeypatching;
2. delta 4a is installed as a *position-keyed* override of `_Resolver.string`, restricted to the
   comparator spans the 4a grammar admits. Production must add a numeric-token helper consulted at
   the two group-mask comparator sites named in 0.4, and must not widen `_Resolver.string`, which
   is used far beyond group masks;
3. delta 5 is installed by making the off-grammar guard see an empty p-origin set for exactly the
   admitted `len()` nodes. Production must add a sixth admitted form to the guard's `Call` branch.

Fidelity remains asymmetric at integration boundaries. A final implementation may be stricter;
none-flip from a looser shadow transfers in the safe direction, but a positive movement does not.
The final implementation must independently re-demonstrate every pinned movement in section 3. A
final abstention on a pinned candidate is a section-9 stop, exactly as a candidate on a pinned
noncandidate is.

### 0.4 Trigger attribution is observed, not inferred

Two attributions in the E18 recon are corrected here by measurement, and the corrections change
where the build must put its code.

**Delta 4a does not belong in `_mask`.** The recon attributes E18 P3's group-mask refusal to
`_mask` (`dataflow_v3_3.py:7628`) reading its comparator through `_Resolver.string`. An executed
counter on `df33._mask` during the 3.4 re-analysis of E18 P3 records **zero calls**. The frozen
route that actually parses `data[data[GROUP_COLUMN] == LOW_SALT]` for a two-step group slice is
the engine's own `_bare_group_mask_frame` (`dataflow_v3_3.py:11751`) and `_mask_rows`
(`dataflow_v3_3.py:11855`), both of which read the comparator through `self.resolver.string`.
`_mask` and `_pandas_selection` handle the single-expression form `FRAME[MASK][VALUE]`, which
E18 P3 does not use. The build must add the numeric-token helper at those two sites.

**Delta 3 does not reach the second wall the recon names.** The recon reports the AP selector
(`_positions_for` refusing a `set` literal) as E18 P6's second wall, measured on rung P6-r4, which
rewrote the reader *and* the row model to pandas. On the sealed source with only the reader
opened, the second wall is `helper-free-name-unbound`, captured in the helper binder's own frame
at the free name `row`, line 56, in the helper `group_values`. The comprehension target of a
`return`-statement comprehension is not in `local_names`, because `_store_names` is collected over
`body_without_return`. That wall sits *before* the AP selector, so deltas 2 and 3 together cannot
move E18 P6. Section 2.4 records the executed measurement.

## 1. Per-delta grammar and refusal list

Every production below is a syntactic fact about the AST. None of them reads display text,
identifier spelling, comments, reports, or Markdown for meaning. Where a production reads a string
constant it measures the constant's structure only: nonempty, no NUL, at most 256 UTF-8 bytes.

### 1.1 Delta 1: formatted display arms (shipped)

**Frozen-lane rules that own it.** The inline arm test in `_terminal_rendering_ifexp`
(`dataflow_v3_3.py:14330-14334`), the assignment-arm test in `_mt_v21_terminal_rendering_if`
(`dataflow_v3_3.py:13901-13902`) through `_mt_v21_display_string`
(`dataflow_v3_3.py:15179`), and the arm test in `_terminal_ifexp_positions`
(`terminal_presentation_v3_3.py:799-800`) through `_display_string`
(`terminal_presentation_v3_3.py:123`).

**The admitted arm production.** At those three positions only, an arm is a display value when it
is one of:

```text
ARM := Constant(str)                                  -- frozen, unchanged
     | Call(func=Attribute(value=Constant(str), attr="format"), args=ARGVAL+, keywords=[])
     | JoinedStr(values=(Constant(str) | FormattedValue)+)

ARGVAL := Constant(str | int | float)                 -- never bool, bytes, Ellipsis, None
        | UnaryOp(UAdd | USub, ARGVAL)
        | Name in CONSTANTS

CONSTANTS := names bound exactly once, at module level, to a scalar literal, with exactly one
             Store in the whole module and no AugAssign anywhere
```

For the `JoinedStr` form, every `FormattedValue.value` must be an `ARGVAL`, every
`FormattedValue.format_spec` must be `None` or a `JoinedStr`/`Constant` of string constants only,
the concatenated constant text must satisfy the frozen display bound, and at least one
`FormattedValue` must be present. For the `.format` form the template must satisfy the frozen
display bound and at least one argument must be present.

**Two further conditions, both enforced separately.** An admitted arm must carry:

1. an empty `_p_origins`, and
2. no decision position under `_decision_positions_in_expr`.

Everything else in the frozen exemption is unchanged: the test still needs a decision position or
exactly one p-origin, the value must still be bound once to a simple Name, and every load must
still reach a registered sink through `_mt_v2_rendering_load_reaches_sink`.

**Refusal list.** Each of these refuses the admission outright:

| Refused | Reason |
|---|---|
| an argument that is a `Call` | no function calls inside an arm |
| an argument that is an `Attribute`, `Subscript`, `BinOp`, `Compare`, or comprehension | not an `ARGVAL` |
| an argument that is a Name outside `CONSTANTS` | the value is not a module-level constant |
| an argument that is the p-value, or any p-derived value | the p-origin guard |
| `keywords` on `.format`, or a `Starred` argument | closed argument list only |
| `.format` on anything but a bare display constant | the template must be a literal |
| an attribute call other than `str.format` | closed method set |
| the `%` form `"<literal>" % X` | not admitted; the frozen `%` productions are untouched |
| a nested call inside an f-string interpolation | not an `ARGVAL` |
| a non-constant `format_spec` | display spec must be constant |
| the matched print-payload arm test at `dataflow_v3_3.py:13994` | deliberately left frozen |

**Observed narrowing.** The brief allowed an arm to interpolate "the p-value/threshold being
compared". This design admits the threshold, because `ALPHA` is a module-level constant, and
refuses the p-value. Interpolating a p-derived value would give the assigned verdict name a
p-lineage it does not have today, which is a change in analyser semantics rather than a change in
which display spellings are readable. The pinned movement does not need it.

**Observed interaction with the frozen loop normalisation.** After the frozen per-outcome loop
normalisation, a loop-bound label drawn from the declared-outcome table reaches the grammar as a
`Constant`, so `"...".format(label)` is admitted where the un-normalised source has a Name. This
is recorded rather than blocked: the substituted value is a declared-outcome display label, it is
p-free, and the arm remains a display value. The executed fixture
`positive-d1-arm-interpolates-an-outcome-label` pins the behaviour, and
`correct-d1-arm-interpolates-a-data-derived-local` pins that a local bound from the data is still
refused.

### 1.2 Delta 2: set literals in the AP selector (specified, not shipped)

**Frozen-lane rule that owns it.** The membership branch of `_static_bool`
(`correction_model_v3_4.py:3450-3461`), consumed by `_positions_for`.

**The admitted production.** A separate module-level table, consulted only at that membership
branch:

```text
MEMBERSHIP_SET := NAME = { Constant(str) (, Constant(str))* }
```

admitted only when:

1. the binding is a module-level `Assign`/`AnnAssign` with exactly one `ast.Name` target;
2. the value is an `ast.Set` with at least one element and every element a non-bool `str`
   constant;
3. the written elements are already unique, so the source text and the object agree;
4. the name has exactly one Store or Del in the whole module and no `AugAssign`; and
5. **every** Load of the name is the right operand of an `In` or `NotIn` `ast.Compare` with one
   operator and one comparator.

The table is never merged into `sequences`. `_module_sequences` is untouched, so a set can never
become a row-table iterator, an `enumerate` argument, a factor source, or an ordered position
source. Condition 5 is what makes that structural rather than a convention.

**Refusal list.** `ast.SetComp`; `set(...)`; `frozenset(...)`; any non-string element; a written
duplicate; a name used in iteration, `len()`, subscript, or any non-membership position; a name
bound more than once; a binding that is not at module level. All nine are executed as grammar
probes in `instrument_results.json`, and all nine refuse.

### 1.3 Delta 3: standard-library `csv` reader lineage (specified, not shipped)

**Frozen-lane rule that owns it.** `_mt_full_scope_reader_census`
(`dataflow_v3_3.py:834-880`) and the check at `dataflow_v3_3.py:9822`.

**The admitted production.**

```text
READER := with open(PATH, KW*) as HANDLE:
              return list(csv.DictReader(HANDLE))
        | with open(PATH, KW*) as HANDLE:
              return list(csv.reader(HANDLE))

KW := newline=Constant(str) | encoding=Constant(str) | mode=Constant(str) without "b"
```

admitted only when the `with` has exactly one item and exactly one body statement, the context
expression is a call to the unshadowed `open` with exactly one positional argument, the `as`
target is a simple Name, the body statement is a `Return` of `list(...)` with one argument and no
keywords, and that argument is a `csv.DictReader`/`csv.reader` call with exactly one positional
argument that is the `with` handle Name and no keywords. The path resolves through the existing
`_static_path` and `_mt23_local_reader_paths` formal-parameter route, so a helper-wrapped reader
still resolves.

Column binding, had this shipped: for `csv.DictReader` the header row becomes the dict keys and no
other key source is admitted; for `csv.reader` the header row must be consumed either by an
unpacking assignment of the first row into names, or by integer index constants into the row
sequence. Any other spelling refuses.

**Refusal list.** `restkey`; `restval`; an explicit `delimiter`, `dialect`, `quotechar`, or any
other reader keyword; binary mode; a reader that is not materialised by `list(...)`; a filtered or
transforming comprehension in place of `list(...)`; more than one `with` item; more than one body
statement; an `open` keyword outside the admitted set; a reader over a handle other than the
`with` target. All nine are executed as grammar probes and all nine refuse. The E18 N6 reader,
which iterates `csv.DictReader(handle)` inside a `for` rather than materialising it, is refused by
the same grammar: the executed probe records zero admitted paths on that source.

### 1.4 Delta 4: numeric group selectors and the presentation-loop terminal proof (shipped as a pair)

Delta 4a alone reaches only a different abstention on E18 P3, which the ordering rule turns into
no public change at all. The two productions ship together.

#### 1.4a Numeric group-mask comparator

**Frozen-lane rules that own it.** `_bare_group_mask_frame` (`dataflow_v3_3.py:11751`) and
`_mask_rows` (`dataflow_v3_3.py:11855`), both of which resolve the comparator through
`self.resolver.string`. See 0.4: this is a measured correction to the recon's attribution.

**The admitted production.** At those two comparator positions only:

```text
GROUP_COMPARATOR := Constant(int | float) | UnaryOp(UAdd | USub, GROUP_COMPARATOR)
                  | Name bound exactly once at module level to such a literal
```

admitted only when all of:

1. the mask is an `ast.Compare` with one `ast.Eq` operator and one comparator, whose other side
   is a `Subscript` reading the contract group column;
2. every non-header cell of the group column in the authorized CSV parses as a finite decimal
   under `repr`-normalisation;
3. the two contract `group_values` tokens normalise to two *distinct* decimal texts;
4. the literal's own `repr`-normalised decimal text equals exactly one of those two tokens; and
5. the value is not a `bool`, not non-finite, and its text carries no thousands separator,
   underscore, or surrounding whitespace.

The admitted value is the CSV token, so everything downstream sees the same string the frozen
path would have seen for a string-spelled group constant.

**Refusal list.** `!=` and every operator other than `==`; a comparator that is a call, an
attribute, a subscript, or arithmetic; a `bool`; a non-finite float; a token column that is not
wholly decimal; two group tokens that collapse to the same normalised text (`2.0` and `2.00`);
a literal matching neither token or both; a mask on a column that is not the group column. All
eight are executed as grammar probes and all eight refuse, and a ninth probe records that the
production refuses outright when the group column is not decimal.

`!=` is refused deliberately, and this is a narrowing of the brief. `_mask` and its two engine
siblings return *the value the group equals*; admitting `!=` would require returning the other
group token, which means reading the binary group domain inside a predicate that does not have
it, and it would silently depend on the domain being exactly binary. The pinned movement does not
need it.

#### 1.4b Terminal-position proof for a presentation loop

**Frozen-lane rule that owns it.** `_terminal_family_transport_loop`
(`dataflow_v3_3.py:14121`), the `For` exemption consulted by `_hierarchy_guard`
(`dataflow_v3_3.py:14036`). The production adds a sixth presentation exemption; it removes no
existing one.

**The admitted production.** A `for` loop's own iterator control is exempt when all five hold:

```text
1. shape       the owner is an `ast.For`, not `ast.AsyncFor`, with no `orelse` and a non-empty body;
               the iterator is a bare Name, `enumerate(NAME)`, or `enumerate(NAME, start=<int literal>)`
               over a bare Name, with `enumerate` unshadowed.
2. no edge     no node under the loop is a Return, Break, Continue, Raise, While, Try, Match,
               Assert, With, AsyncWith, AsyncFor, Global, Nonlocal, Lambda, Yield, YieldFrom,
               Await, FunctionDef, AsyncFunctionDef, or ClassDef, and no call under it resolves to
               `sys.exit`.
3. terminal    no registered test API call, no recognised correction API call, and no `.pvalue`
   position   attribute read occurs at any source position at or after the loop's own position.
4. no escape   for every name the loop binds, including its target, every Load of that name after
               the loop's end that lies outside the loop is dominated by a Store of that name
               outside the loop and after the loop's end.
5. renders     at least one statement in the loop body is an `ast.Expr` whose call is a registered
               sink under `_registered_sinks`.
```

Condition 3 is the E16 recon's terminal-position idea, stated as a position comparison rather than
as a reachability claim. It is what makes the exemption safe: a control that cannot precede any
test or correction cannot gate one. Condition 2 stops the loop suppressing anything after itself.
Condition 4 stops the loop from being a screen whose survivors a later stage reads. Condition 5
stops the exemption applying to a loop that does no presentation at all.

The exemption applies to the **loop's own iterator control**. Every `If`, `IfExp`, comprehension,
and boolean control inside the body is still a separate entry in the guard's control list and is
still judged on its own frozen exemptions.

**Refusal list.** A loop followed by a registered test; an early `return`; a `break`; a
`continue`; a binding that escapes; a loop that renders nothing; an iterator that is a call other
than the two `enumerate` forms; a non-literal `start`; an `async for`; a loop with an `orelse`.
Six of these are executed as named fixtures against the admission census.

### 1.5 Delta 5: cardinality read of the reconstructed family (shipped)

**Frozen-lane rule that owns it.** `_off_grammar_transform_guard`
(`dataflow_v3_3.py:13396-13478`), specifically the `Call` branch's terminal allow-list at
`13471-13477`.

**The admitted production.**

```text
CARDINALITY := len(COLLECTION)
```

admitted only when all of:

1. the callee resolves to the unshadowed builtin `len`, there is exactly one positional argument
   and no keywords;
2. the argument is a bare `ast.Name`;
3. `_p_sequence` of that Name is exactly the contract-order position tuple `0..N-1`, so the
   argument is the fully reconstructed p-record family and not an alias, a filtered copy, or a
   partial collection;
4. the name has exactly one Store or Del in the analysis scope; and
5. every ancestor of the call, up to and including the enclosing statement, is a display node: an
   `ast.JoinedStr`, an `ast.FormattedValue`, a `"<literal>".format(...)` call, a `print`/`str`
   call, or a registered sink call, and the enclosing statement is an `ast.Expr` whose call is a
   registered sink. The call must additionally satisfy the frozen
   `_mt_v2_rendering_load_reaches_sink` route.

The admitted value is the family size, which the analyser already holds from the contract. The
admission therefore introduces no new value route into the model; it removes an unaccounted-for
consumer of the record collection.

**Refusal list.** A `len()` whose value enters a comparison, arithmetic, a subscript, a
`range(...)` loop bound, a threshold, an assignment to a local, a record store, or a return; a
`len()` over a filtered comprehension or over any Name whose `_p_sequence` is not the complete
contract-order family; a `len()` with keywords or with more than one argument; a shadowed `len`.
Six are executed as named fixtures against the admission census, and the sixth,
`correct-d5-len-bound-to-a-local-first`, is the load-bearing one: storing the value before
printing it is refused, because a stored value is no longer provably display-only.

## 2. Executed sweep

### 2.1 Populations

| Population | Rows | Path |
|---|---:|---|
| opened envelope cases E10-E18 | 135 | direct analyzer |
| open corpus | 50 | direct analyzer |
| lane fixtures chained from 3.4 | 245 | direct analyzer |
| new 3.5 fixtures | 38 | direct analyzer |
| closed-grammar probes (D2, D3, D4a, D4b) | 46 | direct call of the production |
| opened envelope cases E10-E18 | 135 | real pipeline, pre and post |
| custodian probe projects (r1 to r8 oracle rows) | 64 | real pipeline, pre and post |

### 2.2 Pinned artifacts

The builder must pin these values and must not regenerate the design evidence.

**Prototype artifacts.**

```text
results.json             sha256:2a1d93c12ebda184a71171f19f797cd192930ae33a4af2800a7ab8e8730dbdcd
instrument_results.json  sha256:2f10ac8118ed496b63494f3dc431405ea08dd586ed6334a0d955dfaec9ddada1
MANIFEST.json            sha256:ad2a0e077bc04cc83dd36600e4614fd6a8b14398f6dfa39e789ed37017f3b1f6
recall_deltas_shadow.py  sha256:04eefcd85d20b3c3aa552a90a41b8c43f4ae114cfde4c179aca07f92eadfac56
fixture_catalog.py       sha256:08efcdb4b08b1b4a579542dc1c75da70368a49129ec02b3fd161bda5412d9209
sweep.py                 sha256:eee22ae271b9143d22970dd095fd7bbe45f238d5c885a7be5fde57edf2114e5a
instrument.py            sha256:f5b6ba423aa66c94bcc68025575435bd3f74a6126e57257f754b8c206ceb7660
harness.py               sha256:47983e7582aa31cea559b98a680edb6299ac005707ea7c0603a0e7e10c797733
```

The 48-file manifest binds 662,818 bytes.

**Frozen surfaces the build must not touch.** Each is asserted in a test that reads the file and
compares the digest, so a stray edit fails the suite rather than the review.

```text
dataflow v3                  sha256:0388b4a1d3a28b7549af85362d0d4e7f13ffc2b4807dc129d242c4927870c0d1
dataflow v3_3                sha256:ddcb29549dda5dcf164848730679027161e34692282cfeaabf84e089db58b857
dataflow v3_4                sha256:f690db88677a9f79a3a162dc7dff907d8c377a28c1d2b02095f6fadea62ed789
correction model v3_4        sha256:b42ca5fbbc31c8faca5d84627c403a6586d6ef48648051f941593913a9cc292a
terminal presentation v3_3   sha256:d1b9463235494ae54d4c5d2bbc3eb4f0d1b73568a4c5625993dd87dbee4b5c78
comprehension v3_4           sha256:fa706bfd28b370c6111c17ddedff9f8921d4e0c169979b3b9ef013412c6b2b5c
adapter v3_4                 sha256:da7c88f472709146f68b029c073322d579f0ef80d7158d11831bd5f7d18445ed
3.4 prototype results        sha256:2bf626534a513e951e1c8a559a2538594f6dbb60e6bfda8e0787e0cd704a3cf2
E18 audit results            sha256:8aad260515d0d79ad282e56d4e03970ee531b2f865f7b88d02b4004f1667cb45
E18 role map                 sha256:cd830c2a79ea80f4fe310d8db09893b29c74fdf25d33975c713d9161feff3d92
E18 recon                    sha256:84acc7a5d3353429f1e6cdafaa541c7494c89fb672bfd27fa6fcc70af1b2e76d
manual-correction recon      sha256:e4d2b8ad429a774234960be5782395c3ac2858300af1ac1278f908dcf87c49a7
```

The `dataflow v3` and `dataflow v3_3` digests differ from the 3.4 design's anchor list because the
frozen-lane performance re-pin (ADR-0081) rewrote both files with outputs proven identical. The
3.3 result semantics are unchanged; the bytes are not, and the anchor list must carry the current
bytes.

**Required values, reproduced by `verify.py`.**

```text
evidence cases                                185 (135 opened + 50 corpus)
frozen 3.4 prior rows identical               168 / 170
fixtures                                      283
correct-analysis fixtures                     199
frozen 3.4 fixtures unchanged                 245 / 245
movements                                     exactly 4, listed in section 3
opened-negative candidates                    0 / 81
corpus-correct candidates                     0 / 25
all-correct-fixture candidates                0 / 199
retro recall                                  E10 5/6, E11 6/6, E12 6/6, E13 4/6, E14 4/6,
                                              E15 4/6, E16 4/6, E17 6/6, E18 4/6
corpus score                                  0/25 correct, 19/25 misstep, 0 movements
question census                               28 -> 28, removed set empty
admission census                              d1 14, d2 0, d3 0, d4a 20, d4b 9, d5 9
grammar probes                                d2 9/9 refuse and 3/3 admit; d3 9/9 refuse and
                                              2/2 admit; d4a 8/8 refuse plus the
                                              non-decimal-column refusal and 4/4 admit;
                                              d4b 10/10 iterator forms match the grammar
```

### 2.3 Real-pipeline confirmation

The direct analyzer and the real pipeline agree on every row. The real-pipeline pass runs the
`sc-referee` CLI twice per case, freezing a method contract and then auditing, and reads the
outcome out of `audit/semantic.lock.json`. Both passes run against a pristine `git archive` of
`f23c750c`; the post pass installs the shadow into the shipped 3.4 adapter's own binding.

```text
real-pipeline envelope cases      135
contract or audit failures          0
rows that moved                     4   (the same four the analyzer moves)
applicable modules, pre             46
applicable modules, post            50
negatives gaining a non-complete classification   0

custodian probe projects           64   (e18-tools/build_probes*.py, r1 through r8)
rows that moved                     0
```

The four real-pipeline movements, read out of the sealed lock bytes:

| Case | Pre | Post |
|---|---|---|
| E15 P3 `afe47b2a7ea87ed21a69` | `unsupported`, `unresolved-manual-correction-present` | `applicable`, `none`, `N=5`, corrected `[]` |
| E17 N1 `e2d8b1bdf4baa671a1b4` | `unsupported`, `test-operand-lineage-unresolved` | `applicable`, `complete`, `N=4`, corrected `[0, 1, 2, 3]` |
| E18 P2 `5a9277448db34379ce78` | `unsupported`, `hierarchical-gatekeeping-present` | `applicable`, `none`, `N=6`, corrected `[]` |
| E18 P3 `d1b1fc47ccdabd0c2f22` | `unsupported`, `test-operand-lineage-unresolved` | `applicable`, `none`, `N=5`, corrected `[]` |

The custodian probe count is **64**, not the 71 the brief names. The four builders
(`build_probes.py`, `build_probes_r6.py`, `build_probes_r7.py`, `build_probes_r8.py`) construct
8, 22, 20 and 14 projects, and no two builders use the same probe name, so 64 is the whole
population. All 64 are byte-identical pre and post, which is what the r1 to r8 audit-fix oracle
requires: every false-accusation probe that the round-3 to round-7 closure refuses still refuses,
and the two probes that must stay true accusations still do.

### 2.4 Why deltas 2 and 3 are specified and not shipped

Delta 3 was measured with a **deliberately over-generous** stand-in: any module containing a
`csv.DictReader` or `csv.reader` call is granted the authorized path. That admission is strictly
looser than the section 1.3 grammar, so whatever it cannot reach, the real grammar cannot reach
either.

```text
E18 P6, frozen 3.4                 abstain  authorized-reader-lineage-unavailable
E18 P6, over-generous reader       abstain  helper-free-name-unbound
   captured frame: free name `row`, line 56, helper `group_values`
E18 N6, frozen 3.4                 abstain  authorized-reader-lineage-unavailable
E18 N6, over-generous reader       abstain  test-operand-lineage-unresolved
E18 P6, section 1.3 grammar        1 admitted reader path
E18 N6, section 1.3 grammar        0 admitted reader paths
```

E18 P6's helper is

```python
def group_values(rows, group, column):
    return [float(row[column]) for row in rows if row[GROUP_COLUMN] == group]
```

and the comprehension target `row` is bound inside the `return` expression, which
`_bind_helper_body` does not scan when it collects `local_names` from `body_without_return`. So
`row` is an unbound free name and the helper refuses. That wall sits before the AP selector, which
is where delta 2 lives, so **delta 2 cannot fire on E18 P6 either**. Under the ordering rule an
abstaining re-analysis returns the frozen reason byte-for-byte, so installing deltas 2 and 3 would
change no public byte anywhere in the evidence.

Delta 2 is nonetheless demonstrated correct, so that a later delta can pick it up with the
equivalence already proved. On a pandas rung of E18 P6 that clears the reader and the row model
but keeps the `set` literal:

```text
set literal, without delta 2       abstain  unresolved-manual-correction-present
set literal, with delta 2          candidate strict_subset, N=8, corrected (0, 3, 4)
the same source with a tuple       candidate strict_subset, N=8, corrected (0, 3, 4)
```

Two spellings of the same three-name selector produce the same three positions. That is delta 2's
whole claim, executed.

This mirrors the 3.4 design's disposition of extension B: specified in full, executed, and not
shipped, with the blocking measurement recorded so the next delta starts from it. The difference
is the reason. Extension B was withheld because it *destroyed* a pinned candidate; deltas 2 and 3
are withheld because they can change nothing until a third wall opens.

## 3. Movement set

The sweep observes exactly four movements, and the direct analyzer and the real pipeline agree on
all four.

```text
E15:P3:afe47b2a7ea87ed21a69 -> candidate none, corrected_positions {}, N=5      (delta 5)
E17:N1:e2d8b1bdf4baa671a1b4 -> covered  complete, corrected_positions {0,1,2,3}, N=4  (delta 4)
E18:P2:5a9277448db34379ce78 -> candidate none, corrected_positions {}, N=6      (delta 1)
E18:P3:d1b1fc47ccdabd0c2f22 -> candidate none, corrected_positions {}, N=5      (delta 4)
```

Three are catches. One is a clearance, and it needs its own justification because a false
clearance is held to the same zero standard as a false accusation.

**The E17 N1 clearance is true.** The source calls `multipletests(p_raw, alpha=ALPHA)` once over
all four declared outcomes and reads every verdict off the `reject` vector, printing the raw
p-values for reference only. Its group constants are the integers `GROUP_LOW = 18` and
`GROUP_HIGH = 24`, and the authorized CSV's `temperature_c` column holds exactly the two tokens
`18` (40 rows) and `24` (40 rows). Delta 4a maps each literal onto exactly one token, the operand
lineage resolves, and the frozen classifier then reaches `covered`/`complete` over positions
`{0,1,2,3}` of 4 on its own. Nothing in the movement is an accusation, and the frozen classifier,
not any 3.5 production, made the call. The facts above are recorded as executed values in
`instrument_results.json` under `e17_n1_clearance_facts`.

Nothing else moves. All 181 other evidence rows and all 245 frozen 3.4 fixtures are
outcome-identical, and no frozen classification anywhere is lost.

## 4. None-flip populations

No population gains a candidate. The counts are executed, not asserted.

```text
opened negatives (9 roles x 9 envelopes)          0 / 81
corpus correct-labelled cases                     0 / 25
all correct-analysis fixtures                     0 / 199
new 3.5 correct-analysis fixtures                 0 / 5
frozen 3.4 fixtures that moved at all             0 / 245
frozen 3.4 evidence rows that moved at all        2 / 170   (E15 P3 and E17 N1, both pinned)
negatives gaining a candidate                     0 / 81
real-pipeline negatives gaining a non-complete
  classification                                  0 / 81
custodian probe projects that moved               0 / 64
```

The 245 frozen fixtures carry the whole cumulative safety population forward: the 48 frozen 3.0
rows, the r1 to r3 audit-fix rows, the 63-row B5 expression grid, the 16 3.1 laundering-adjacent
rows, the 20 AP 3.2 rows, the 12 reproduced gatekeeping fixtures (`assert`, `match`, short-circuit,
early `return`/`break`/`continue`/`raise`/`sys.exit`, and the `pvalue-control-dependence-unresolved`
execution-prevention residual), the 3.3 terminal and helper adversaries, and the 42 new 3.4 rows.
Every one of them keeps refusing.

The corpus score is unchanged: `0/25` correct candidates, `19/25` misstep candidates, `0` movements.

The correction-scope question census is `28` before and `28` after, with an empty removed set.
E15 P3 carried no correction-scope question under 3.4 even though its reason qualifies, because
`locate_correction_scope_witness` finds no witness in a program that contains no correction at
all. That is the question layer working, and it is why closing delta 5 removes nothing.

## 5. Census

### 5.1 Where each production fires, across 185 evidence cases and 283 fixtures

```text
d1 formatted display arm       14 admitted spans
d2 set selector                 0   (specified, not installed)
d3 csv reader                   0   (specified, not installed)
d4a numeric group comparator   20 admitted spans
d4b presentation loop           9 admitted loops
d5 cardinality read             9 admitted calls
```

### 5.2 Evidence rows, by name

```text
d1 formatted display arm
  E18:P2:5a9277448db34379ce78
d4a numeric group comparator
  E17:N1:e2d8b1bdf4baa671a1b4
  E18:P3:d1b1fc47ccdabd0c2f22
d4b presentation loop
  E17:N1:e2d8b1bdf4baa671a1b4
  E18:P3:d1b1fc47ccdabd0c2f22
d5 cardinality read
  E15:P3:afe47b2a7ea87ed21a69
  E17:N1:e2d8b1bdf4baa671a1b4
d2 set selector                none
d3 csv reader                  none
```

Across 185 evidence cases, the shipped productions fire on **four** rows in total, and every one
of them is a pinned movement. Every other admission in the census belongs to a fixture this design
authored to test itself. That is the measure of how narrow the reach is.

Two productions fire on rows they do not move. On E17 N1 all three shipped productions fire, but
only delta 4a is load-bearing: measured on its own, delta 4a alone takes E17 N1 to the identical
`covered`/`complete` outcome, and deltas 4b and 5 fire on the same source without changing it.

### 5.3 Off-grammar guard reach, measured for delta 5

An executed hook on `_off_grammar_transform_guard` walked its own p-derived inventory for every
opened case in the 3.5 re-analysis lane:

```text
opened cases reaching the guard                    53
of those, negatives                                17
opened cases whose p-derived inventory holds len() 1   (E15:P3:afe47b2a7ea87ed21a69)
```

The manual-correction recon measured 21 and 13 on the shipped lane; the re-analysis lane reaches
the guard more often, which is why the counts differ. The load-bearing number is the same under
both measurements: exactly one case in the whole opened population carries a p-derived `len()`.

## 6. Retros

Retro candidate recall, computed by applying 3.5 to opened bytes. These are development
projections; they never rescore a sealed first-contact envelope.

| Envelope | Sealed | 3.4 retro | 3.5 retro | Delta |
|---|---|---|---|---|
| E10 | 0/6 | 5/6 | 5/6 | - |
| E11 | 0/6 | 6/6 | 6/6 | - |
| E12 | 2/6 | 6/6 | 6/6 | - |
| E13 | 3/6 | 4/6 | 4/6 | - |
| E14 | 1/6 | 4/6 | 4/6 | - |
| E15 | 2/6 | 3/6 | **4/6** | delta 5 |
| E16 | 1/6 | 4/6 | 4/6 | - |
| E17 | 4/6 | 6/6 | 6/6 | - |
| E18 | 2/6 | 2/6 | **4/6** | deltas 1 and 4 |

The sealed column is read from each envelope's own `AUDIT_RESULTS.json` `first_contact_recall`
field; the 3.4 column is the frozen 3.4 prototype result extended to E18 by the shipped analyzer.

Retro recall over the nine opened envelopes moves from `40/54` to `43/54`, three catches. Sealed E15 stays `2/6`
and sealed E18 stays `2/6`; neither can be rescored, and the E17+E18 window arithmetic is
unchanged at `6/12`.

The clearance movement does not enter this table. E17 N1 is a negative, so it changes recall
nowhere; what it changes is that one more correct analysis is now positively cleared rather than
left unresolved.

### 6.1 What stays a miss

Eleven of the 54 opened positives still abstain under 3.5, down from fourteen under 3.4:

| Still-open reason | Cases |
|---|---|
| `unresolved-manual-correction-present` | E13 P6, E14 P6, E16 P6 |
| `authorized-reader-lineage-unavailable` | E10 P1, E18 P6 |
| `test-battery-cardinality-unresolved` | E15 P4, E16 P5 |
| `extra-registered-test-outside-authorized-family` | E13 P2 |
| `unresolved-decision-threshold` | E14 P3 |
| `record-family-mutation-unresolved` | E15 P5 |
| `pvalue-family-collection-unresolved` | E18 P5 |

Three of these are policy questions rather than recogniser gaps. The two
`test-battery-cardinality-unresolved` cases and E18 P5's third wall are the same
library-subset-correction question the E14, E16 and E18 recons all reach, and it is blocked on an
ADR, not on a grammar. The three remaining `unresolved-manual-correction-present` cases are the
sub-family Bonferroni factor question that the manual-correction recon ranks as its own delta.

E18 P6 is the case this design measured and could not move. It needs three deltas, not two: the
reader grammar in 1.3, the comprehension-target binding inside a helper `return`, and the AP
selector in 1.2. Closing the first two without the third buys nothing, and closing any one of them
alone buys nothing at all.

## 7. False-accusation surface, per delta

The accusation-safety invariant is:

> A display arm is admitted only after proving its every interpolated value is a literal or a
> module-level constant and carries no p-lineage; a numeric group comparator is admitted only
> after proving it names exactly one of the two CSV group tokens under an unambiguous decimal
> normalisation; a presentation loop's iterator is exempted only after proving that nothing
> testable follows the loop, that it can suppress nothing, and that nothing it binds escapes it;
> a cardinality read is admitted only after proving its argument is the complete reconstructed
> family and its value reaches only a display sink. Global censuses run on original bytes, and
> the unchanged classifier then proves the scientific claim independently.

### 7.1 Delta 1

Every arm the production admits is a display value whose own inputs are p-free. The conditional
still chooses only between two renderings, and the frozen exemption's other six conditions are
unchanged, so the verdict name must still be bound once and every load must still reach a
registered sink.

The strongest correct-analysis attack is a genuinely gated design that happens to format its
verdict strings. Delta 1 does not touch what makes such a design refuse: the gate is a different
control, and the widened arm predicate is only consulted on the control that owns the arms. E18 N5
is that attack drawn from real sealed evidence. Its two-stage screen-then-validate design keeps
abstaining `hierarchical-gatekeeping-present`, and the executed admission census on it is zero for
every production: the widened predicate never even fires, because N5's arms are already bare
constants and its gate is a filtered comprehension over p-values.

The second attack is a correctly corrected family with formatted arms, and the executed answer is
worth stating exactly. Two fixtures carry it: E18 N1's complete `multipletests` family with
`.format` arms, and a complete hand Bonferroni built on the E18 P2 base with `.format` arms. Both
abstain at `hierarchical-gatekeeping-present` under 3.4, because the formatted arms break the same
exemption they break on E18 P2. Under 3.5 both reach `covered`/`complete`. So on the exact shape
that would be a false accusation, delta 1 does not produce a candidate; it produces a coverage
record. That is the desired direction, and it is the one gate a widening of this kind has to pass.

The third attack is an arm that smuggles a p-derived value into the display. Two separate
conditions block it: the syntactic `ARGVAL` rule refuses anything but a literal or a module-level
constant, and the lineage guard refuses any arm with a p-origin or a decision position.

The recon's syntactic census over every opened envelope with a `ROLE_MAP` found three sources
carrying a p-threshold conditional whose display arms are not bare constants: E18 P2, E15 N8, and
E6 N1. The executed sweep supersedes that proxy with a direct measurement: across all 185 evidence
rows the delta-1 production fires on exactly the rows listed in section 5, and E15 N8 keeps its
frozen `test-battery-cardinality-unresolved` reason, which sits before the hierarchy guard.

### 7.2 Delta 4a

The production reads two things the analyzer already holds: the two group tokens parsed from the
authorized CSV, and the module's own literal. It refuses unless the group column is wholly decimal,
the two tokens stay distinct under `repr` normalisation, and the literal matches exactly one of
them. That is the whole safety argument: an admitted comparator names one existing group, so the
frame model sees exactly what it would have seen for the string spelling of the same group.

The strongest attack is an ambiguous column, where `2.0` and `2.00` are both present. The executed
grammar probe `ambiguous-normalised-tokens` refuses it, as do the non-decimal, thousands-separator,
no-matching-token, and both-tokens cases. `!=` is refused outright, so a negated mask can never
select a group by elimination.

E17 N1 is the load-bearing observation here and it runs the other way: it is a *negative* whose
group constants are the integers `18` and `24`, and admitting them takes it from
`test-operand-lineage-unresolved` to `covered`/`complete` over all four declared outcomes. That is
a true clearance of a correct analysis, not an accusation. Section 3 pins it, and section 4 records
that no negative anywhere gains a candidate.

### 7.3 Delta 4b

This is the widest of the shipped productions, because the hierarchy guard is the gate that
protects against screen-then-test designs. Three conditions carry the safety argument, and each
answers a different attack.

The screening attack is a loop that computes survivors which a later stage tests. Condition 3
refuses it: a registered test call at or after the loop's position disqualifies the loop outright.
E18 N5 is that design in sealed evidence, and the executed run records that the production never
fires on it.

The suppression attack is a loop that returns, breaks, or raises early and so prevents a later
emission. Condition 2 refuses every execution-prevention node under the loop, and the fixtures
`correct-d4b-loop-early-return` and `correct-d4b-loop-break` execute it.

The escape attack is a loop whose bindings a later stage reads. Condition 4 refuses it unless a
later binding outside the loop dominates the read, and `correct-d4b-binding-escapes-the-loop`
executes it.

The exemption applies to the loop's own iterator control only. Every conditional inside the body
remains a separate control judged on its own frozen exemptions, so a p-gated `if` inside a
presentation loop still refuses.

Two honest caveats about how these refusals are proved. First, the E18 P3 base carries two
presentation loops, so a whole-source admission census cannot say which one refused; the seven
D4b disqualifiers are therefore proved by a per-loop hook on the production itself, recorded in
`instrument_results.json` under `d4b_loop_refusals`, and the mutated loop is absent from every
admitted set. Second, on three of those seven the guard never offered the loop to the production
at all, because an earlier control refused first, so their refusal is proved by outcome rather
than by the production's own answer. To close that gap the iterator grammar is additionally
exercised directly, on ten forms with a stub engine, in `d4b_iterator_grammar`: `sorted(...)`,
`reversed(...)`, `.items()`, `enumerate(list(...))`, `enumerate(zip(...))`, a non-literal `start`,
and a positional second argument all refuse; a bare Name and the two admitted `enumerate` forms
are accepted.

### 7.4 Delta 5

The admitted value is the family size, which the contract already fixes. Admitting it adds no
value route to the model. What it removes is an unaccounted-for consumer of the p-record
collection, which is what the frozen guard was actually refusing on.

The strongest attack is a `len()` that is not display-only: a comparison, a divided threshold, a
loop bound, an index, or an assignment to a local that later code uses. Condition 5 refuses all of
them by requiring an unbroken display ancestor chain to a registered sink, and six named fixtures
execute the refusals. `correct-d5-len-bound-to-a-local-first` is the load-bearing one, because a
stored value is no longer provably display-only.

The second attack is a `len()` over a *filtered* copy of the family, which would report a
screened cardinality as if it were the declared one. Condition 3 refuses it: `_p_sequence` of a
filtered comprehension is not the complete contract-order tuple.

The FA surface was measured rather than proxied. An executed hook on the off-grammar guard walked
its own p-derived inventory for every opened case; section 5 records how many cases reach the guard
at all, how many of them are negatives, and that exactly one case in the whole opened population
carries a p-derived `len()`.

## 8. What the build must prove

The build implements the productions in versioned copies. It may not monkeypatch, and it may not
rewrite source text.

1. **New versioned production files.** A `code_csv_multiple_testing_dataflow_v3_5.py` carrying the
   3.4 ordering rule over a 3.5 re-analysis; versioned copies of the frozen 3.3 dataflow and
   terminal-presentation modules carrying the four widened predicates; and versioned adapter,
   integration, record-model, helper-record, scope-question, and detector wrappers as registry
   identity requires. `code_csv_multiple_testing_dataflow_v3.py`,
   `code_csv_multiple_testing_dataflow_v3_2.py`, `code_csv_multiple_testing_dataflow_v3_3.py`,
   `code_csv_multiple_testing_terminal_presentation_v3_3.py`,
   `code_csv_multiple_testing_correction_model_v3_2.py`,
   `code_csv_multiple_testing_correction_model_v3_3.py`, and every dependence dataflow file stay
   byte-frozen, and each is pinned by a digest test.

2. **Where each production goes.**

   | Production | Site |
   |---|---|
   | D1 | the arm test in `_terminal_rendering_ifexp`, the assignment-arm test in `_mt_v21_terminal_rendering_if`, and the arm test in `_terminal_ifexp_positions` -- three sites, not the shared `_mt_v21_display_string` / `_display_string` predicates, which have twenty other call sites |
   | D4a | a numeric-token helper consulted at the comparator position in `_bare_group_mask_frame` and `_mask_rows`; **not** `_Resolver.string`, and **not** `_mask` |
   | D4b | a sixth `For` exemption in `_hierarchy_guard`, reached through `_terminal_family_transport_loop` or a sibling predicate |
   | D5 | a sixth admitted form in the `Call` branch of `_off_grammar_transform_guard` |

3. **The ordering rule.** A row the unchanged 3.4 lane classifies is returned untouched; a 3.5
   re-analysis that abstains returns the frozen 3.4 reason byte-for-byte. Both directions must be
   tested. The round-3 to round-7 alias closure runs before any 3.5 classification is returned,
   exactly as it does in 3.4.

4. **Executable gates.** Every pinned movement in section 3, with exact `N`, classification,
   corrected positions, one candidate, and zero Findings; the fifteen-row E18 adapter oracle and
   the full E10 to E17 adapter oracles; all 50 corpus rows; all 283 fixtures with their exact
   admission-census and classification gates, including the non-vacuity check that every
   disqualifier fixture has an abstaining 3.4 baseline; every none-flip population in section 4;
   the closed-reason set gate at 61; the question census; deterministic replay; and the frozen
   3.1/3.2/3.3/3.4 anchors.

5. **Grammar-level refusal tests.** The four grammar probes in `instrument_results.json` must be
   re-executed against the production predicates, not against the prototype: D2's nine refusals,
   D3's nine refusals, D4a's eight refusals plus the non-decimal-column refusal, and D4b's per-loop
   refusals.

6. **What must not ship.** D2 and D3 are specified and not installed. If a later delta installs
   them, it must first close the third wall behind D3 (`helper-free-name-unbound` on a
   comprehension target inside a helper `return`), because until then neither production can change
   a public byte.

7. **ADR obligation.** ADR-0079 must record: the corrected trigger attribution in 0.4; each of the
   five grammars and refusal lists in section 1; the executed movement set including the E17 N1
   clearance and why it is true; every none-flip population; the admission census; the retro table;
   the decision not to install D2 and D3, with its executed evidence; and that classification,
   correction recognition, wording, the 61-reason closed set, and the contract profile are all
   unchanged.

## 9. Stop rules

Stop and report a design regression rather than changing a grammar, reason, or oracle if any of
the following occurs.

1. Any sealed negative, in any envelope, gains a `candidate`. A negative reaching `covered` is
   allowed and is the desired answer for a correct analysis; a negative reaching `candidate` is a
   false accusation and is an unconditional stop.
2. Any correct-labelled corpus case or any correct-analysis fixture becomes a candidate.
3. Any row the unchanged 3.4 lane classifies changes at all, or a 3.5 re-analysis that abstains
   returns a reason other than the frozen 3.4 reason.
4. Any pinned movement in section 3 fails to reach its exact outcome under the final strict
   implementation. Conservative abstention on a pinned candidate is a stop in the other direction,
   not permission to loosen the design.
5. Any evidence row moves that section 3 does not name.
6. A new abstention reason is required. The closed set stays at 61. If a production cannot be
   expressed without a new reason, stop.
7. Delta 1 admits an arm carrying a p-origin, a decision position, a call, an attribute other than
   `str.format`, a keyword argument, a starred argument, or a name outside the module-constant
   table; or the widening is applied to the shared `_mt_v21_display_string` / `_display_string`
   predicates rather than to the three named arm positions; or it is applied to the matched
   print-payload arm test.
8. Delta 4a admits a comparator under an operator other than `==`, over a group column that is not
   wholly decimal, or when the two group tokens collapse under normalisation, or when the literal
   matches zero or both tokens; or the admission is placed in `_Resolver.string`.
9. Delta 4b exempts a loop with any execution-prevention node under it, a loop with a registered
   test or recognised correction at or after its position, a loop whose binding escapes without a
   dominating later binding, a loop that renders nothing, or an iterator other than a bare Name or
   the two `enumerate` forms; or the exemption is extended from the loop's own iterator control to
   any control inside its body.
10. Delta 5 admits a `len()` whose value enters a comparison, arithmetic, a subscript, a loop
    bound, a threshold, an assignment, a return, or a record store; or whose argument is not the
    complete contract-order p-record family.
11. D2 or D3 is installed without first closing the third wall behind D3 and re-running every
    population.
12. Global censuses observe anything but the original bytes.
13. The round-3 to round-7 closure is weakened, bypassed, or reordered.
14. Any frozen 3.1/3.2/3.3/3.4 file or result, corpus replay record, prior comparison row,
    qualified lane, GrantPin, wording object, or scoring byte changes outside enumerated registry
    noise.
15. Applying any admission twice changes graph, exclusion, or census bytes.
16. Display text, identifier spelling, comments, reports, or Markdown change a predicate.
17. Prototype replay, adapter replay, answer-removal equivalence, or deterministic output differs.
18. A required quality gate cannot pass after generated files are finalized.
