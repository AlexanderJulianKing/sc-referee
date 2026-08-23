# Pseudoreplication code slice 2.0 design — 2026-08-22

- **Status:** Accepted and frozen for Envelope 4
- **Freeze acceptance provenance:** Fable, under executive authority granted by Alex 2026-08-21,
  2026-08-22
- **Direction decision provenance:** Fable, under executive authority granted by Alex 2026-08-21
- **Decision date:** 2026-08-22
- **Normative bases:**
  `docs/implementation/PSEUDOREP-CODE-SLICE-DESIGN-2026-08-22.md` and its accepted 1.1, 1.2, and
  1.3 delta designs
- **Governing ADR:**
  `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`
- **Proposed identity:** check, adapter, recognition grammar, and separate experimental code-lane
  detector `2.0.0`
- **Evidence:** frozen contract, CSV structure, Python AST/dataflow, and established API names only
- **Prose evidence:** forbidden
- **Project-authored-code execution:** forbidden

## 0. BUILD-NOTES

- **2026-08-22, pre-build wording closure:** W1 admits exactly `FRAME[LITERAL_COLUMN]` as a read on a
  tracked or reader-derived frame; stores through `.loc`, `.iloc`, `.at`, or ordinary subscripts remain
  mutations. W2 restores the X1-selected module scope for flat scripts. W3 lowers the closed large-
  resampling threshold from 100 to 50. Provenance: Fable, under executive authority granted by Alex
  2026-08-21.
- Ambiguities discovered during the build are recorded below and implemented only as abstentions. This
  section cannot authorize a wider conviction predicate than the normative sections.
- **2026-08-22, retired 1.x emissions:** the three retired descriptive-shape reasons are not emitted by
  2.0. Existing tests were kept active and converted to directional R1/R2 expectations; no test was
  retired or skipped in this build.
- **2026-08-22, nested test result:** a registered test nested in an attribute, dict, tuple, list, or
  output call is censused as the test node itself. It does not overwrite the enclosing assignment's
  member graph with a field-insensitive test-result label. This is the narrower R3 reading and preserves
  exact p-member propagation.
- **2026-08-22, read-only column projection:** a literal/closed-header projection immediately on exact
  `groupby(...)` or admitted read-only `drop_duplicates(...)` is classified as structural access only;
  the underlying call and aggregate/drop-duplicate label remain visible to every R2 scan. Any route from
  the projected result to an operand still abstains.
- **2026-08-22, D7 reason precedence:** the design fixed `15b07ef7670800ba88e0` at
  `two-group-row-selection-unavailable` while keeping the named-aggregate controls at
  `aggregation-on-test-operand-path`. The implementation applies the former only when both selected
  missing-header values arise from the same direct pandas `.mean()` aggregation; every `.agg(...)`,
  helper-carried, mixed, or unresolved form takes the aggregation/unsupported branch. This changes only
  the outward abstention reason and cannot create a candidate.
- **2026-08-22, shared integration closure:** advancing the exact code-lane subject-version gate in
  `scientific_checks/integration.py` changes the content-addressed dependency closure of the founder
  semantic adapter even though no founder source byte or founder rule changes. The invariant test pins
  the resulting closure digest and separately retains byte-identity assertions on founder core sources;
  this is identity accounting for the section 13 integration change, not a founder grammar change.
- **2026-08-22, active release assertions:** exact-identity tests that formerly named the pre-2.0
  dependence check and adapter now pin the generated 2.0 manifests. Unrelated complete-domain and
  multiple-testing identities remain unchanged; no assertion was removed.
- **2026-08-22, regression inventory refresh:** the 155-case development ledger advances only the
  active dependence component from check `1.3.3` to `2.0.0` and refreshes the byte digest of
  `source:dependence-recognition-stage5-tests` after its exact shared-closure assertion changed. Case
  selectors, roles, expected applicability, assessment ceilings, and qualification exclusions are
  unchanged; the ledger and execution-plan digests were mechanically recomputed.
- **2026-08-22, G1 NumPy validation order:** every `numpy.*` call is checked by the closed section-5.3
  arity/keyword grammar before generic aggregation handling, both before and after the candidate test.
  An invalid reducer can no longer inherit post-test descriptive admission. Exact valid
  `numpy.mean(SELECTION)` remains read-only when it does not enter a protected slice.
- **2026-08-22, G2 GroupBy receiver closure:** projected and chained receivers rooted at `groupby`,
  `resample`, `agg`, `aggregate`, or `pivot_table` remain grouped receivers. Their `mean`, `sum`,
  `describe`, and every other closed GroupBy terminal are never R1-admitted; the complete call remains
  visible to R2. A later separately registered read-only formatter on the already reduced result—such as
  `round`, `reset_index`, or `sort_values` without `inplace`—is not itself reclassified as a GroupBy
  terminal. The existing post-test descriptive-aggregation exception follows an inline terminal through
  one closed assignment expression to its output sink; this preserves the reviewed output-only path in
  `2d47b05c996177f2afd7` without admitting the same terminal before the test.
- **2026-08-22, G3 whole-scope mutation census:** tracked `.loc`, `.iloc`, `.at`, ordinary-subscript,
  and statically explicit `inplace=True` stores suppress regardless of whether they occur before or
  after the candidate test. Source order does not turn a tracked-frame store into description.
- **2026-08-22, G4 flat-helper coverage limit:** the built 2.0 analyzer does not expand helpers in an
  X1-selected flat module scope. Any remaining flat-script helper call that consumes the reader
  component or an operand selection abstains as an unresolved/off-list component consumer. This is a
  deliberate narrower implementation than section 3's expanded-program definition; no flat helper is
  treated as pass-through, and future support requires a new reviewed delta.
- **2026-08-22, G5 integration and tooling disclosure:** `scientific_checks/integration.py` adds the
  unique root `analysis.py` file-record fallback when the publication surface is unresolved and adds
  the 2.0 code-lane subject binding; it is not a one-line version-only change. Its exact bytes are pinned
  in the active test as `sha256:8e421eddddc6cf4f14f10723b3973a29525f1521f156e4e8439129cd158280d1`.
  `evaluation/development` was added to Ruff's exclude list because it contains frozen evidence and
  intentionally nonconforming authored fixtures; active source and test paths remain linted.
- **2026-08-22, G7 tripwire closure:** the no-prose end-to-end test instruments helper expansion, the
  reader forward closure, test-argument backward slicing, R1 admission, and container-member
  propagation in addition to adapter inspection and the analyzer entry point.

## 1. Boundary and observed reason for the change

This is a delta. Every base and 1.1–1.3 rule not explicitly replaced below remains normative.
In particular, code slice 2.0 does **not** change the contract profile `1.1.0`, authority fields,
authorized-path equality, bounded CSV parser, D1', single-reader rule, alternate-analysis scan,
reader or test allowlists, group-row selection grammar, aggregation/dependence registry, sibling guards,
p-result sink requirement, Finding wording, production pin, or prohibition on project execution.

Envelope 3 is opened development evidence and earns no future blind credit. Its frozen result was one
evaluation candidate among six positives, zero candidates among six negatives, zero Findings, replay
equality 12/12, closure equality 84/84, and blind-label/role agreement 12/12
(`evaluation/development/blind-envelope-3-2026-08-22/CUSTODY_LOG.md:147-148`;
`evaluation/development/blind-envelope-3-2026-08-22/AUDIT_RESULTS.json:1-404`). The sole positive catch,
`a28f42e4bd1fe1c5e048`, is the first blind catch in project history. The other five positives failed
before the unchanged operand-path predicate on syntactically varied validation, descriptive, formatting,
or helper-output code. After those superficial walls were removed in diagnosis, all six negative
programs still had a substantive CSV or code guard. The inference to verify is that closed
reachability—not further idiom enumeration—can admit irrelevant descriptive code without weakening
the operand path.

The 1.0–1.3 detector modules and manifests remain immutable history. A build uses a new 2.0 detector
module and versioned manifest record. Nothing in this design qualifies or installs a Finding pin.

## 2. Reused surfaces and replaced surfaces

### 2.1 Reused byte-for-byte in semantics

The following behavior is reused without widening:

1. base-design sections 3 and 4: contract authority, CSV multiplicity, D1', project inventory, exact
   root `analysis.py`, no prose, and no execution;
2. base-design sections 5.1–5.5: import resolution, static paths, readers, exact two-group row
   selections, and registered `ttest_ind`/`mannwhitneyu` signatures;
3. base-design section 5.3's single-authorized-reader rule, section 5.6's aggregation,
   dependence-aware, mutation, second-test, and unregistered-component-consumer guards, and section
   4.1's alternate-analysis-file guard;
4. base-design section 5.7 and delta X2: a p-result—not a statistic alone—must reach an accepted output
   sink;
5. base-design sections 7 and 8: fact fields, observation roles, title, summary template, limitations,
   and `question_only` ceiling;
6. X1 path forms; X4's interprocedural depth, binding, recursion, default, closure, decorator, async,
   yield, global/nonlocal, and fresh-name rules; and
7. the 16-definition ceiling on each reader-to-operand, component-sibling, and p-result-to-sink path.

### 2.2 Replaced admission layer

The X3/X5/X6/X7 descriptive-shape enumerators and the global “unsupported helper body statement” veto
are replaced by R1. They must not run before R1 and must not remain as a second hidden veto. X4's
interprocedural boundary remains, but helper-body statements inside an otherwise structurally eligible
helper are provisionally expanded and classified by R1/R2 rather than rejected by statement class.

For a helper whose return or side effect reaches a protected operand/result path, X4 still requires a
simple-name call, depth at most two, nonrecursive one-to-one argument binding, supported defaults, no
variadics, no decorators, no async/yield, no closure, and no global/nonlocal. R3 is the only return-shape
extension: one final dict/tuple/list literal may be tracked member by member. A helper used solely for
admitted output may have no explicit return when its call is a standalone expression; assigning the
result of a no-return helper remains unsupported.

## 3. Normative graph definitions

These definitions are controlling.

- **Expanded program:** the selected `main` body, or the X1-selected module scope for scripts without
  `main`, plus each module-level helper body structurally eligible under X4 and expanded with fresh names,
  and the closed X1 module-constant table. No other module statement is part of the expanded program.
  Docstrings, comments, and string contents are absent from evidence and graph labels; literal strings
  remain AST constants only where an API signature needs a value.
- **Definition node:** exactly one `Name`, `Attribute`, `Subscript`, container member, call result,
  parameter, helper return, loop/comprehension target, or mutation target with its exact source span and
  one defining AST node. No other AST category becomes a definition node.
- **Member key:** exactly (a) a literal string/integer dict key, (b) a zero-based tuple/list index, (c) the
  corresponding literal position in destructuring, or (d) a pandas label read on a non-reader aggregate
  in one of these forms: `AGG.loc[LABEL]`, `AGG.at[LABEL]`, or `SERIES[LABEL]`. `LABEL` is an AST
  string/integer `Constant`, a closed module constant resolving to one, or a loop target whose iterable is
  a literal tuple/list of such constants; the latter forks one member edge per resolved label. A `.loc`
  read whose receiver is the reader frame or an unaggregated reader selection remains a section-5.4 R2
  selection, never a descriptive member read. The exhaustive unresolved member forms are a dynamic key,
  slice, starred member, field-insensitive whole-container projection, attribute not registered by
  section 5.7, and a comprehension member that enters a protected slice.
- **Data edge:** the exact edge kinds are definition-to-`Load`, assignment RHS-to-target, identity
  alias-to-alias, receiver/argument-to-call-result, call-result-to-consumer, actual-argument-to-inlined-
  parameter, helper-return-to-call-result, literal-container-member-to-literal-member-read,
  destructured-position-to-target, loop/comprehension/generator iterable-member-to-target, predicate-to-
  controlled-body definition or side effect, and mutation-input-to-store-target. Edges never arise from
  source spelling, comments, docstrings, printed labels, report text, or string contents.
- **Backward slice of a test argument:** the transitive predecessor set from one exact positional
  argument of a registered test call to its authorized reader definition, preserving member keys,
  calls, mutations, aggregations, and unknown nodes.
- **Forward slice of a statement:** the transitive successor set of every definition and value-use node
  contained in that statement. It includes helper parameter/return edges and member edges after
  expansion. It does not treat mere source order or a prose string as an edge.
- **Reaches:** directional def-use membership from a node a statement **defines or writes** to a later
  node. A statement fails R1-a only when one of its definition/store nodes is itself a member of a
  test-argument backward slice, the reader-to-operand path, an accepted p-result-to-sink path, or the
  tracked-frame-store target set; merely reading a protected value is an incoming edge and is not
  “reaching” that value.
- **Protected node:** any node on either test-argument backward slice; any accepted reader call or its
  bound frame; any registered test call or result; any p-result-to-sink path; and any store that may
  mutate the authorized reader component or a value derived from it.
- **Reader component:** the base-design section-4.4 directed def-use component rooted at the single
  base-design section-5.3 authorized reader. Its exact node classes are the reader root, selection,
  identity alias, registered aggregation, registered safeguard, registered test, registered
  dependence-aware call, unresolved/off-list consuming call, member-preserving container, mutation, and
  accepted output-sink use transitively connected to that root.
- **May write:** an AST `Store` or `Del` to a tracked name, attribute, or subscript; an augmented or
  walrus assignment rooted at a tracked value; or passing a mutable tracked value as receiver or
  argument to a call that is not explicitly classified as read-only by sections 5.3 through 5.7.
  Inability to prove read-only behavior is `may write`.

  The preceding two sentences reproduce base-design section 4.4 verbatim. The cited sections are the
  base-design sections; the 2.0 read-only proofs below may extend that closed classification but may not
  replace or weaken the base definition.
- **Tracked-frame store:** exactly an `Assign`, `AnnAssign`, `AugAssign`, `NamedExpr`, or `Delete` whose
  target is a tracked name/attribute/subscript; an AST `Store`/`Del` beneath such a target; or a
  statically resolved in-place/mutating API call on a tracked receiver/argument. A remaining unresolved
  or off-list call is still `may write` under BASE, but is not invented as a concrete store target: R1-b
  and predicate step 19 abstain with `unregistered-component-consumer`. Thus uncertainty never passes as
  read-only and is not misreported as an observed explicit mutation.
- **Admitted statement:** a statement satisfying R1. Admission means only “this statement cannot alter
  or conceal the protected path under the closed graph”; it is not evidence for a candidate.
- **Relevant statement:** a statement with at least one definition/store node that is a member of the
  protected set under the directional `reaches` definition. A statement that only contains a `Load` of
  a protected value is not relevant on that fact alone. A relevant statement is never admitted by R1;
  the unchanged R2 operand/component rules decide it.

Graph construction is deterministic. Definitions and statements are ordered by
`(lineno, col_offset, end_lineno, end_col_offset, canonical_ast_dump)`. Each name definition must be
unique along a protected path. Traversal uses visited node/member identities rather than enumerating
paths. Existing source-byte and AST-node bounds remain; an unresolved edge, alias, call target, or
container member abstains and never falls back to field-insensitive admission.

## 4. R1 — forward-slice admission

### 4.1 Ordered algorithm

After X1 scope selection and provisional X4 expansion, the builder must:

1. census accepted readers and registered tests over the **full** expanded program;
2. build def-use, parameter/return, member, loop, may-write, and sink edges without deleting any AST
   node;
3. form every registered test's two argument backward slices and every p-result forward slice;
4. mark protected nodes and the complete reader component;
5. compute the forward slice of every statement in `main` and every expanded helper;
6. classify a statement as relevant exactly when one of its definition/store nodes is a member of the
   protected set under section 3's directional `reaches` definition;
7. otherwise validate every call in the statement and recursively in its control-flow body against
   section 5; and
8. mark it admitted only when both conditions below hold.

The two necessary and jointly sufficient R1 conditions are:

**R1-a, no protected write:** none of the nodes the statement defines or writes is a member of a
test-argument backward slice, the reader-to-operand path, an accepted p-result-to-sink path, or the
tracked-frame-store target set. The direction is controlling: reading a selection, frame, test result,
p-result, or other protected value for read-only descriptive output does not by itself fail R1-a; a value
defined by the statement that later flows into one of those protected sets does.

**R1-b, closed operations:** every call, attribute read, and subscript read resolves to the exact R1
registry in section 5, an unchanged R2 reader/selection/test/sink, or the unchanged base-design
section-5.6 post-test descriptive-aggregation exception. An R1-admitted local helper is expanded before
this check; after expansion it is no longer a call and is not an unregistered component consumer. Any
call that remains after expansion and is unresolved or off-list and consumes the reader component or a
selection fails `unregistered-component-consumer` regardless of whether its result reaches an output.
A registered R2 call is never relabelled benign and remains in the full-program R2 census. In particular,
pre-test `groupby`/`agg`/`pivot_table` output helpers are not admitted by omission; only the unchanged
base post-test exception can admit a registered descriptive aggregation.

Failure of R1 does not remove the statement. R2 scans it. Only when no more specific unchanged R2 code
applies may the adapter return an R4 admission code.

### 4.2 Control flow

`if`, `for`, `while`, `try`, `assert`, `raise`, and `with` are admitted only when:

1. the header expressions satisfy R1-a/R1-b;
2. every statement in every body, `orelse`, handler, and `finally` block is admitted;
3. no `break`, `continue`, `yield`, `yield from`, `await`, `global`, or `nonlocal` occurs;
4. no body may write a tracked name or tracked-frame store; and
5. every loop target is a fresh local target; it fails `loop-target-aliases-tracked` only when the target
   or a value it defines flows **into** a test-argument backward slice, the reader-to-operand path, an
   accepted p-result-to-sink path, or a tracked-frame store.

An `if missing: raise ValueError(...)` guard therefore may be admitted: the predicate and exception
constructor are read-only, the body terminates, and neither value reaches an operand. A conditional
assignment later consumed by a test is relevant and remains under R2. Source-order placement before or
after the test is irrelevant.

For a `for` or `while`, all possible iterations share the same conservative edges. A target bound to a
tracked selection solely so the loop can print or format it is an admitted read; this is the exact
Envelope-1 P1/P3 case. A target that later flows into an operand fails
`loop-target-aliases-tracked`; also printing that target cannot launder the outgoing operand edge. `try` is admitted only
when all handlers are statically present and admitted; a bare `except`, dynamic exception expression,
or suppressed unresolved exception abstains. `with` does not make an off-list context manager safe;
the context-expression call must independently resolve under R1 or an unchanged R2 sink rule.

A list/dict/set comprehension or generator expression is admitted only when its iterable is
non-protected under directional R1-a (the exact section-5.5 read-only `df.columns` property qualifies), its
target does not flow into a protected set, its element/key/value/filter expressions satisfy R1-a/R1-b,
and it has no async clause. A comprehension that defines a protected operand/member is relevant and R2
must validate it; unresolved iterator membership or aliasing abstains.

### 4.3 Local helpers outside the operand path

A simple-name local helper whose call result and side effects never reach a protected node is analyzed
recursively under R1. It may return a scalar or literal container, or may have no return when called as
a standalone expression. It is admitted only if all bodies and calls are admitted and no value escapes
to a reader, registered test, tracked store, file sink outside the unchanged sink registry, global, or
closure.

This admits zero-return print helpers and validation/descriptive helpers without making helper names or
printed wording evidence. A dynamic callee, callable parameter, method supplied by project code,
decorator, closure, recursive cycle, depth-three call, or unresolved return/side effect abstains.

## 5. Closed R1 call registry

The resolver must establish the exact API identity through accepted static imports and prove that a
builtin is unshadowed. Dynamic import, `getattr`, callable values, star imports, monkey-patching,
subclasses, and name resemblance do not resolve. Arguments and keyword values must themselves have
complete graph edges; no `*args` or `**kwargs` is permitted.

### 5.1 Builtins

The exact builtin names are:

```text
print len int float str round abs min max sum sorted range enumerate zip
set list dict tuple bool isinstance format any all repr divmod
```

Every name in that exact list must be proven to resolve to its unshadowed builtin. `Assign`, `AnnAssign`,
`AugAssign`, import alias, parameter, comprehension/loop target, `FunctionDef`, `AsyncFunctionDef`, and
`ClassDef` binding any listed name sets `builtins_shadowed` and abstains. `print` is the console-output
side effect explicitly allowed here; it is still a p-result sink only under the unchanged base-design
section-5.7 signature. Restating base-design line 699 verbatim: **For `print`, `sep` and `end` may be
literal strings; `file`, star arguments, and dynamic keywords are not accepted.**

`len`, `int`, `float`, `str`, `round`, `abs`, `sum`, `any`, `all`, `repr`, `bool`, and `isinstance` use
their established fixed positional arity; `round` may additionally take one literal integer, and
`isinstance`'s second argument must be a literal builtin type or literal tuple of builtin types. `divmod`
takes exactly two scalar positional arguments. `min` and `max` take one iterable or two-or-more scalar
positional arguments with no keywords; `key=` is forbidden. `sorted` takes one positional iterable,
permits only `reverse=` with a literal boolean, and forbids `key=`. `range` takes one to three closed
integer arguments; `enumerate` takes one iterable and at most one closed integer start; `zip` takes only
positional iterables and no `strict` keyword. `list`/`set`/`tuple` take zero or one iterable; `dict` takes
zero or one literal/member-sensitive mapping or iterable and only literal-name keywords. `format` takes
one value plus one literal format-spec string. The calls must not receive an unresolved project-defined
object. Conversion constructors are value constructors, not identity evidence.

### 5.2 `math`

One exact `math.NAME(...)` or statically imported `NAME(...)` is admitted when `NAME` resolves to a
public callable in Python's established `math` module. The attribute chain has exactly one member after
`math`; names beginning `_`, dynamic members, and values returned by a project helper are excluded.

### 5.3 NumPy read-only functions

The exact reduction names are:

```text
mean nanmean median nanmedian sum nansum average min nanmin max nanmax
std nanstd var nanvar prod nanprod percentile nanpercentile quantile
nanquantile ptp all any count_nonzero
```

The exact elementwise names are:

```text
abs absolute sqrt square exp expm1 log log1p log2 log10 power minimum
maximum clip round around rint floor ceil trunc isfinite isnan isinf sign
```

The exact read-only constructor/combiner names are:

```text
array asarray arange linspace concatenate
```

They must resolve to `numpy.NAME`; aliases resolving to that identity are equivalent. Every listed ufunc
accepts only its semantic operands: unary functions take exactly one positional value; `power`,
`minimum`, and `maximum` take exactly two; `clip` takes exactly three; `round`/`around` take one value and
at most one literal integer. An additional positional `out` argument is forbidden for every listed
ufunc. `out`, `where`, `casting`, `order`, `subok`, `signature`, and `extobj` keywords are forbidden for
all rows.

Reduction arities are closed: ordinary reductions take the data plus at most a literal axis and their
documented literal `ddof` where applicable; percentile/quantile rows take data, a literal/admitted scalar
`q`, and at most a literal axis; median/nanmedian take data and at most a literal axis. Positional or
keyword `out` is forbidden. `overwrite_input` is forbidden, positionally and by keyword, for exactly
`percentile`, `nanpercentile`, `quantile`, `nanquantile`, `median`, and `nanmedian`.
`array`/`asarray` accept one value and at most one literal dtype;
`arange` accepts one to three closed numeric arguments and at most a literal dtype; `linspace` accepts
two closed scalar bounds, at most one closed integer count, and no axis/device; `concatenate` accepts one
literal/member-sensitive sequence and at most one literal integer axis. None accepts `out` positionally
or by keyword.

Any array argument must be a tracked selection, an admitted descriptive value, a literal, or a
member-preserving identity of one of those. `numpy.random` outside the exact resampling guard in section
6.2, file I/O, array mutation, constructors not listed above, and dynamic ufuncs are off-list.

### 5.4 SciPy distribution queries

The only admitted method names are `ppf`, `cdf`, `sf`, and `isf` in the exact resolved shape
`scipy.stats.DISTRIBUTION.METHOD(...)`; aliases are limited to the exact base-design section-5.1 accepted
static import forms. `DISTRIBUTION` is
one static public attribute token; there is no `getattr`, returned distribution, frozen distribution
instance, method chain, or project wrapper. Arguments must be literals or admitted descriptive values.
This shape admits `scipy.stats.t.ppf` without registering a new inferential test.

### 5.5 Pandas read-only calls and properties

On a statically tracked pandas `Series`, `DataFrame`, non-reader aggregate, or reader-derived identity,
the exact R1 read-only terminal method names are:

```text
mean std var median min max sum count nunique sem any all describe round head
to_string unique value_counts isna notna items iterrows reset_index sort_values
tolist quantile duplicated drop_duplicates
```

The exact read-only properties are `columns`, `index`, `shape`, `size`, and `dtypes`; only a literal
integer subscript of `shape` is resolved. `std`/`var`/`sem` accept no argument or only `ddof=0|1`;
`round` accepts no argument or one literal integer; `head` accepts no argument or one nonnegative literal
integer; `to_string` accepts no argument or only `index=True|False`; `value_counts` permits only literal
boolean `normalize`, `sort`, `ascending`, and `dropna`; `quantile` takes one literal/admitted scalar `q`;
`reset_index` permits only literal `drop` and `names`; `sort_values` takes one literal column or literal
column list and permits only literal `ascending` and `na_position`; `drop_duplicates` takes no argument or
one literal column/literal column list and permits only literal `keep`. `reset_index`, `sort_values`, and
`drop_duplicates` forbid `inplace` entirely. `isna`, `notna`, `unique`, `items`, `iterrows`, `tolist`,
`duplicated`, `describe`, and all other listed zero-argument terminals take no arguments unless a rule
above says otherwise. No listed call may receive a callable/lambda, dynamic column, unresolved receiver,
star argument, or dynamic keyword.

`drop_duplicates` is R1-read-only only when its result does not reach either test operand; if it does,
the unchanged base-design section-5.6 safeguard/unsupported-path rule decides it. `items` and `iterrows`
may supply a loop/comprehension iterable only under section 4.2's directional target rule. These APIs
remain code facts only and contribute no positive evidence.

The registered R2 aggregation/safeguard rows are exactly the base-design section-5.6 table. The listed
`Series`/`DataFrame` terminals and the preceding `drop_duplicates` row are explicit R1 read-only
classifications when R1-a holds. `groupby`, every `GroupBy`/`Resampler` terminal, `agg`, `aggregate`, and
`pivot_table` are not added to R1; they may use only the unchanged base-design post-test
descriptive-aggregation exception. All R2 labels remain visible, and any value routed to a test operand,
sibling test, mutation, or remaining component consumer suppresses.

### 5.6 Exceptions and strings

The exact exception constructors are:

```text
Exception ValueError TypeError RuntimeError KeyError IndexError AssertionError
FileNotFoundError
```

The exact string methods are:

```text
join format lower upper strip lstrip rstrip replace split rsplit startswith
endswith center ljust rjust zfill title capitalize casefold
```

The receiver must be a literal string, a closed module string constant, or a value already proven to be
`str` by an admitted call. String formatting supplies no semantic evidence. Any exception construction
or string result that reaches a protected slice is relevant and not admitted by R1.

### 5.7 Closed attribute, subscript, and path reads

Outside R3 literal member edges and the base-design R2 selection grammar, the exact admitted attribute
reads are `Path.name`, `Path.parent`, `Path.stem`, and pandas `columns`, `index`, `shape`, `size`, and
`dtypes`. A `Path` receiver must be a closed X1 path object; chained `.parent.parent`, `.parents[...]`,
dynamic attribute access, and every unlisted property abstain. Pandas property reads obey section 5.5
and may not define or write a protected node.

The one additional plain-column read is exactly `FRAME[LITERAL_COLUMN]`, where `FRAME` is a tracked or
reader-derived `DataFrame` name and `LITERAL_COLUMN` is an AST string `Constant` or a closed module string
constant. It is read-only and produces a reader-derived value governed by R1/R2 like every other derived
value. It is not a group-row selection and supplies no positive evidence. A store through
`FRAME[...]`, `.loc[...]`, `.iloc[...]`, or `.at[...]` remains a tracked-frame mutation; a dynamic column,
slice, tuple key, chained receiver, or missing CSV header abstains.

Two exact structural projections are also closed here because their receiver call is already classified
elsewhere: `FRAME.groupby(...)[LITERAL_COLUMN]` and
`FRAME.drop_duplicates(...)[LITERAL_COLUMN]`. `LITERAL_COLUMN` must resolve to a CSV header, and the
whole receiver call must independently pass section 5.5 or remain a registered R2 aggregation. The
projection never removes the aggregation/drop-duplicate label and never supplies positive evidence.

The exact read-only path-call rows are `os.path.join(A, B)`, `os.path.dirname(P)`,
`os.path.abspath(P)`, and `os.path.basename(P)`. `A`, `B`, and `P` must be literal/closed module path
strings or the exact `__file__` token in an X1 static-path form; `join` takes exactly two components and
the other calls exactly one argument. These rows do not add reader-path forms: the whole reader-path
expression must still match X1 exactly and byte-equal the contract path. Every other attribute or
subscript read abstains unless it is an R3 member edge, an exact section-5.5 pandas property, or an
unchanged R2 selection/result access.

## 6. R2 — unchanged protected-path and full-program guards

R1 is a classification layer, not a pruning pass. The builder must run the unchanged base predicate on
the full expanded AST and graph **after** R1 classification. It must include admitted statements in the
reader, registered-test, aggregation, dependence-aware, mutation, sibling, unregistered-call, and sink
censuses. In particular:

1. both accepted test arguments still must be direct exact group-column row selections from the single
   authorized reader and project the same CSV header;
2. no aggregation, safeguard, unknown call, unsupported selection, or mutation may occur on either
   reader-to-argument path;
3. a registered dependence-aware call on the reader component still suppresses;
4. a second raw-row candidate still produces `multiple-rowwise-test-candidates`;
5. a second test on an aggregated frame still produces `aggregated-sibling-test-present`;
6. after helper inlining, any remaining unresolved/off-list call that consumes the reader component or a
   selection produces `unregistered-component-consumer`, whether its result is ignored, stored, or sent
   to output;
7. base-design section 5.3 still requires both argument slices to terminate at one authorized reader and
   refuses every second accepted reader;
8. base-design section 4.1 still refuses statistics imports in another Python file and every `.ipynb` or
   `.R` analysis surface;
9. the D1' CSV composite-key rule is unchanged; and
10. only an accepted p-result path can satisfy the output-sink predicate.

A registered aggregation or safeguard may use the unchanged base-design section-5.6 descriptive
exception only when it occurs after the candidate test and its result reaches solely admitted
descriptive output—never a protected operand, competing test, mutation, or remaining component consumer.
R1 does not remove the source-order condition or add a pre-test exception. The branch supplies no
evidence.

### 6.1 Ordered predicate and reason precedence

The base-design predicate steps 1–12 remain. Replace base steps 13–20 with this order:

13. provisionally expand X4 helpers and build member-sensitive def-use/may-write/call graphs;
14. census readers and all registered tests, build candidate argument and p-result slices, and mark
    protected nodes;
15. compute R1 classification for every statement without deleting nodes;
16. apply direct operand provenance/selection rules and the X4 structural boundary;
17. apply explicit/proven tracked-frame mutation and loop-target-alias guards; conservative call-only
    `may write` labels remain live for step 19;
18. apply aggregation/unknown/direct-path guards;
19. require exactly one raw-row candidate and apply multiple-candidate, registered dependence-aware,
    aggregated-sibling, section-6.2 resampling-sibling, and remaining-component-consumer guards over the
    full program;
20. if no step-16–19 guard applies, require every nonrelevant statement to be admitted under R1;
21. require an accepted p-result output sink and the unchanged uniqueness/definition ceilings.

Fact, observation, detector, and admission steps then continue unchanged. Predicate-step order dominates
source span. Within one step, the earliest source span wins, then this rank:

1. `tracked-value-mutation`
2. `loop-target-aliases-tracked`
3. `dependence-aware-operator-on-path`
4. `aggregation-on-test-operand-path`
5. `multiple-rowwise-test-candidates`
6. `dependence-aware-sibling-present`
7. `aggregated-sibling-test-present`
8. `resampling-inference-sibling-present`
9. `unregistered-component-consumer`
10. `admission-slice-reaches-operand`
11. `admission-call-off-list`
12. `control-flow-body-unadmitted`
13. the unchanged unknown/expression/path code.

### 6.2 Registered large-resampling inference sibling

This is a full-program R2 guard, not an R1 call admission. A node is labelled
`large_resampling_inference` only when all four closed conditions hold:

1. **Large repeated generator.** The code contains (a) a `for`/comprehension/generator iterator that is
   exact unshadowed `range(...)`, a literal tuple/list, or admitted `numpy.arange(...)`, whose statically
   evaluated cardinality is at least 50; or (b) one statically resolved NumPy random draw whose `size`
   cardinality is at least 50. Cardinality is an integer literal or closed module integer constant; a
   tuple/list size is the product of its nonnegative closed integer members. The exact draw identities are
   `numpy.random.choice`, `randint`, `random`, `random_sample`, `sample`, `ranf`, `standard_normal`,
   `normal`, and `uniform`, plus `choice`, `integers`, `random`, `standard_normal`, `normal`, and `uniform`
   on a direct single-assignment generator returned by `numpy.random.default_rng`. A dynamic bound,
   nonunit/unresolved `range` cardinality, unknown RNG, or unknown size is not a positive resampling label;
   its ordinary unresolved/off-list code still abstains.
2. **Tracked consumption.** The repeated body, comprehension element, or draw-and-index dataflow consumes
   the authorized reader component, a tracked group selection, or a value derived from either. Reading
   only a closed scalar count is insufficient; a tracked data value/member must enter the repeated
   computation.
3. **Collected output and reduction.** Repeated outputs flow through exactly a comprehension result,
   literal list member, `LIST.append(V)`, `ARRAY[INDEX] = V`, or single-assignment scalar accumulator, then
   into one of these exact reductions: `numpy.mean`, `nanmean`, `std`, `nanstd`, `percentile`,
   `nanpercentile`, `quantile`, or `nanquantile`; or pandas `mean`, `std`, or `quantile`. Internal
   append/subscript stores are recognized only to retain this guard edge and are never R1-read-only calls.
4. **Output reach.** The reduction result reaches an accepted console or file output sink under the
   unchanged base-design section-5.7 sink table, directly or through an R3 literal member.

When all four hold anywhere in the full expanded program beside the raw candidate,
`resampling-inference-sibling-present` abstains before R1 admission codes. Printed labels and comments are
irrelevant. The named regression fixture is an off-registry cluster bootstrap implemented **only** with
otherwise listed calls: a literal list comprehension over `range(50)`, tracked cluster/member
selections, replicate-difference arithmetic, `numpy.percentile`, and `print`. It must abstain on this
guard even though no call is off-list.

## 7. R3 — member-sensitive containers

Dict, tuple, and list values are never field-insensitive. The graph records one edge per literal member:

- dict: exact literal key to value;
- tuple/list: zero-based position to value;
- destructuring: corresponding position to target; and
- helper return: each member edge is copied to the call-site container with fresh member identities.

A selection, frame, aggregation, test result, p-result, or unknown value inside a container retains that
label. Reading a literal member follows only that edge; passing, returning, iterating, formatting, or
testing the whole container follows the union of all member edges. Dynamic keys, `.get`, stars,
comprehensions, mutation, alias-ambiguous containers, and nonliteral return containers abstain when they
touch a protected slice.

R3 is not descriptive-return admission. If `{"values": values}` carries a row selection to a test,
that member is on the operand path and R2 validates it. If a returned test dict carries `p_value` to
`print`, that member remains on the result path and must satisfy the unchanged p-result sink grammar.
No sibling member or printed label can make either edge disappear.

## 8. R4 — outward abstention codes

The 2.0 admission layer emits only these four new codes:

```text
admission-call-off-list
admission-slice-reaches-operand
loop-target-aliases-tracked
control-flow-body-unadmitted
```

Two R2 guards added or tightened by this delta emit exactly
`resampling-inference-sibling-present` and `unregistered-component-consumer`; they are not R1 admission
codes. Every base/1.1–1.3 authority, CSV, source-envelope, import, X4 structural, reader, selection, test,
aggregation, mutation, sibling, sink, uniqueness, and resource code otherwise remains unchanged.

The exhaustive retired descriptive-code set is
`descriptive-helper-return-contract-unsupported`, `descriptive-reduction-shape-unsupported`,
`descriptive-target-assignment-unsupported`, and `helper-body-statement-unsupported`. No 2.0 source
branch emits one of these four codes. X4's separate parameter, annotation, default, decorator, closure,
recursion, depth, return-shape, and binding codes remain unchanged.

Ambiguity always resolves to abstention. No R4 code is a Finding, scientific accusation, or evidence
that a statement is harmless at runtime.

## 9. Prose exclusion and Finding wording

The permanent no-prose rule is unchanged. R1/R2/R3 receive the AST with docstrings removed and never
receive comments, Markdown, reports, task prose, prompt text, string-token semantics, or printed-label
text. String constants may occupy API slots or output expressions, but their words cannot create,
suppress, select, rank, or qualify a candidate. The end-to-end prose tripwire must extend through graph
construction, helper expansion, forward slicing, member propagation, call admission, and R2 scans.

For the mutation matrix, an **unrelated string literal** is exactly an AST `Constant` string that does
not occupy a contract-header slot, contract group-value slot, registered-API keyword/value slot, or X1
path slot. The matrix mutates only those constants. Their byte changes, along with comment, docstring,
report, and printed-label wording changes, must leave typed observations byte-identical.

The exact title and summary template remain base-design section 8. In particular, the title is
“Analysis code contradicts the frozen one-row-per-authorized-unit requirement.” It does not say
“pseudoreplication,” does not claim the code ran, and does not claim that the analysis is invalid,
primary, selected, or relied upon.

## 10. Development check: all 26 opened scripts and Batch K

All cases in this section are label-visible development evidence and earn zero blind credit. Expected
Finding count is zero for every row because no 2.0 qualification or production pin exists.

### 10.1 Burned Envelope 1

| Role / case | 2.0 expectation | First reason or complete path |
| --- | --- | --- |
| P1 `45dcad2f6496a0fd5778` | Candidate | Direct reader → two `.loc` selections → `ttest_ind` → p-print path. The pre-test loop target reads each selection for listed reductions/print but defines no node on an operand path, so directional R1-a admits it (`evaluation/development/blind-envelope-2026-08-21/cases/45dcad2f6496a0fd5778/project/analysis.py:7-29`). |
| P2 `88e59abe85a8eea2b8cd` | Candidate | Existing direct path; later means are output-only (`evaluation/development/blind-envelope-2026-08-21/cases/88e59abe85a8eea2b8cd/project/analysis.py:7-28`). |
| P3 `0f721a41bac71a461dd2` | Candidate | Direct reader/selection/test/p-print path; the output-loop target reads selections and never flows into a test argument, so directional R1-a admits it (`evaluation/development/blind-envelope-2026-08-21/cases/0f721a41bac71a461dd2/project/analysis.py:3-28`). |
| N1 `5994e65153b07855b07c` | Abstain | `aggregation-on-test-operand-path`; `groupby(...).agg(...mean...)` feeds the tested selections (`evaluation/development/blind-envelope-2026-08-21/cases/5994e65153b07855b07c/project/analysis.py:41-45,56-59,84`). |
| N2 `e804a86a1e05b781f292` | Not applicable | `no-repeated-authorized-unit` at the CSV gate (`evaluation/development/blind-envelope-2026-08-21/cases/e804a86a1e05b781f292/project/analysis.py:15-29`). |
| N3 `11af5bb3f9b7e8e0b293` | Abstain | `tracked-value-mutation` at the group-column store; mixed-model and aggregated-sibling guards remain independent (`evaluation/development/blind-envelope-2026-08-21/cases/11af5bb3f9b7e8e0b293/project/analysis.py:25-29,69-75,101-118`). |

### 10.2 Burned Envelope 2

| Role / case | 2.0 expectation | First reason or complete path |
| --- | --- | --- |
| P1 `e8f97fe750189052f726` | Candidate | Existing 1.3 candidate; R1 subsumes its print-only descriptive helpers (`evaluation/development/blind-envelope-2-2026-08-22/cases/e8f97fe750189052f726/project/analysis.py:23-55,90-92`). |
| P2 `2df3396d80adbb63dffb` | Candidate | Existing 1.2 candidate; descriptive arithmetic and formatting are admitted around the reader/selection/test/p-sink chain (`evaluation/development/blind-envelope-2-2026-08-22/cases/2df3396d80adbb63dffb/project/analysis.py:20-42,61-64`). |
| P3 `ca18f96d45dff1b921ad` | Candidate | R3 follows `thinned`/`unthinned` selections and `result.pvalue` through the returned dict; zero-return `report(res)` is output-only (`evaluation/development/blind-envelope-2-2026-08-22/cases/ca18f96d45dff1b921ad/project/analysis.py:29-48,51-77`). |
| N1 `15b07ef7670800ba88e0` | Abstain | `two-group-row-selection-unavailable`; the tested value header is absent from the authorized CSV (`evaluation/development/blind-envelope-2-2026-08-22/cases/15b07ef7670800ba88e0/project/analysis.py:52-58,73-82`). |
| N2 `5ef43dbf631adcf3daec` | Not applicable | `no-repeated-authorized-unit` at the CSV gate (`evaluation/development/blind-envelope-2-2026-08-22/cases/5ef43dbf631adcf3daec/project/analysis.py:38-75`). |
| N3 `e60c84d0cda3cc465df7` | Abstain | `tracked-value-mutation` at the new-column store after the reader; `smf.mixedlm` remains an independent `dependence-aware-sibling-present` guard (`evaluation/development/blind-envelope-2-2026-08-22/cases/e60c84d0cda3cc465df7/project/analysis.py:48-80,190-193`). |
| N4 `6090fc1b1b6dbfcd6eee` | Abstain | `additional-accepted-reader-present`; raw and summary CSVs are both read (`evaluation/development/blind-envelope-2-2026-08-22/cases/6090fc1b1b6dbfcd6eee/project/analysis.py:21-38`). |
| N5 `d4d95cdd4f4e698d675c` | Abstain | First: `unregistered-component-consumer` at iteration over `wells.groupby(...)`/tracked-block `.append` inside the inlined bootstrap. Independently, `range(N_RESAMPLES)` writes `diffs` and feeds printed `numpy.percentile`, satisfying `resampling-inference-sibling-present` (`evaluation/development/blind-envelope-2-2026-08-22/cases/d4d95cdd4f4e698d675c/project/analysis.py:47-115,213-255,261-274`). |

### 10.3 Burned Envelope 3

| Role / case | 2.0 expectation | First reason or complete path |
| --- | --- | --- |
| P1 `a28f42e4bd1fe1c5e048` | Candidate | Frozen 1.3 candidate: authorized reader lines 20-22, raw selections 37-38, test 46, p-print 70 (`evaluation/development/blind-envelope-3-2026-08-22/cases/a28f42e4bd1fe1c5e048/project/analysis.py:20-22,34-72`). |
| P2 `29893ac47ebe4ca60cce` | Candidate | R1 admits descriptive dict, `stats.t.ppf`, label loop, verdict branch, and formatting; raw selections 46-47, test 53, p-print 103 remain R2 (`evaluation/development/blind-envelope-3-2026-08-22/cases/29893ac47ebe4ca60cce/project/analysis.py:23-39,42-113`). |
| P3 `df67e751158d62c4cbf4` | Candidate | R3 follows each `"values"` member to test lines 43-45; the egg-weight aggregation/loop is output-only and remains visible to R2 (`evaluation/development/blind-envelope-3-2026-08-22/cases/df67e751158d62c4cbf4/project/analysis.py:21-31,34-91`). |
| P4 `045708a55a9f3e2ec449` | Candidate | Raw selections/test/p-print are lines 36-43 and 85; unit-keyed `drop_duplicates`, CI arithmetic, and descriptive loop do not reach the operands (`evaluation/development/blind-envelope-3-2026-08-22/cases/045708a55a9f3e2ec449/project/analysis.py:21-30,33-87`). |
| P5 `2d47b05c996177f2afd7` | Candidate | Missing-column guard is admitted; raw selections/test/p-print are lines 64-74 and 117; per-vine aggregation is print-only and remains an R2-labelled sibling branch (`evaluation/development/blind-envelope-3-2026-08-22/cases/2d47b05c996177f2afd7/project/analysis.py:29-43,58-133`). |
| P6 `d92b542e0bb28fa3c950` | Abstain; honest miss | `admission-call-off-list` at pre-test `df.groupby("week").agg(...)` in `describe_samples`. `summarise_groups` also performs pre-test `groupby().agg` and `pivot_table`. These are registered R2 aggregations, absent from the R1 list, and outside BASE's after-test descriptive exception (`evaluation/development/blind-envelope-3-2026-08-22/cases/d92b542e0bb28fa3c950/project/analysis.py:33-78,128-132`). |
| N1 `0b9b803536c12e3870eb` | Abstain | X4 operand-helper structural gate: `helper-parameter-shape-unsupported` for annotated frame parameters; if annotations are removed in an adversarial twin, `aggregation-on-test-operand-path` fires at the per-volunteer `groupby(...).agg(...)` (`evaluation/development/blind-envelope-3-2026-08-22/cases/0b9b803536c12e3870eb/project/analysis.py:32-39,74-98,123-130`). |
| N2 `5b80f0787b1b6c47048b` | Not applicable | `no-repeated-authorized-unit`; CSV has 44 rows and 44 ewes (`evaluation/development/blind-envelope-3-2026-08-22/cases/5b80f0787b1b6c47048b/project/analysis.py:27-54`). |
| N3 `245226f0f9f97f6acda2` | Abstain | `tracked-value-mutation` at `df["treatment_group"] = pd.Categorical(...)` lines 63-65; the week filter and mixed model remain independent later guards (`evaluation/development/blind-envelope-3-2026-08-22/cases/245226f0f9f97f6acda2/project/analysis.py:38-67,115-147,189-247`). |
| N4 `f4e4d89ac44385a18261` | Abstain | `additional-accepted-reader-present`; lines 36-38 load both raw and per-clinic summary files (`evaluation/development/blind-envelope-3-2026-08-22/cases/f4e4d89ac44385a18261/project/analysis.py:34-38`). |
| N5 `19824e3f6b1e3980872f` | Abstain | First: `unregistered-component-consumer` at `itertools.combinations(idx, n_a)` on reader-derived values. Independently, the closed `N_BOOT` random-index arrays feed printed `mean`/`percentile` reductions and satisfy `resampling-inference-sibling-present`; the raw-row t-test remains visible (`evaluation/development/blind-envelope-3-2026-08-22/cases/19824e3f6b1e3980872f/project/analysis.py:158-234,237-279`). |
| N6 `3c650ec217b884e5f35e` | Abstain | `aggregation-on-test-operand-path`; `groupby(...).agg(mean...)` returns the plant table consumed by `compare_schedules` (`evaluation/development/blind-envelope-3-2026-08-22/cases/3c650ec217b884e5f35e/project/analysis.py:36-64,77-119,122-158`). |

Expected opened total after the complete edits: **11/12 positives are evaluation candidates, 0/14
negatives are candidates, all 26 emit zero Findings, and replay is equal.** By envelope: Envelope 1 is
3/3 positives and 0/3 negatives; Envelope 2 is 3/3 and 0/5; Envelope 3 is 5/6 and 0/6. The sole opened
positive miss is `d92b542e0bb28fa3c950`. These are development expectations, not blind credit.

### 10.4 Batch K

The root naming gate is unchanged. All four K t-test cases still contain only
`workflow/analysis.py`, so the normal path stops before R1:

| Case | Outcome | First reason |
| --- | --- | --- |
| `0de3a6061d3bb4056306` | Abstain | `analysis-source-envelope-unavailable` |
| `6b2da0c7167dbba3738f` | Abstain | `analysis-source-envelope-unavailable` |
| `e9e2718573bb47f7d17b` | Abstain | `analysis-source-envelope-unavailable` |
| `3ae92d0bb421d6eee99e` | Abstain | `analysis-source-envelope-unavailable` |

Their previously documented independent helper/bucket/transform blockers remain. The two binomial K
controls remain outside this table and stop at `authorized-group-domain-not-exactly-two`.

## 11. Required adversarial traces

1. **`df67e751` container-carried selection.** In `describe_group`, `"values": values` at line 30
   carries the exact group selection to the returned dict. R3 follows only that key through
   `oyster["values"]`/`limestone["values"]` at lines 43-45. It is relevant, never descriptively admitted,
   and R2 can prove the direct raw-row path. The script is a candidate.
2. **`245226f0` intermediate non-group filter.** `last = df[df["week"] == final_week]` at line 198
   reaches both test arguments at lines 200-203. R1 cannot admit it. In the complete script the earlier
   tracked group-column mutation wins. In a mutation-free twin, the exact selection grammar refuses the
   week-filter intermediary and returns `two-group-row-selection-unavailable`; it never becomes a raw
   group-row candidate.
3. **`245226f0` tracked mutation.** The `pd.Categorical` assignment to the contract group column at
   lines 63-65 is a tracked-frame store before every later test. Step 17 returns
   `tracked-value-mutation` before sibling or admission codes.
4. **`19824e3f` illustrative raw test beside lake-level inference.** R1 cannot hide either branch.
   Its first reason is `unregistered-component-consumer` at the remaining off-list
   `itertools.combinations(idx, n_a)` call on reader-derived values. Independently, its random index arrays
   have closed size `N_BOOT >= 50`, consume tracked lake means, and feed `mean`/`percentile` reductions
   that reach output, so section 6.2 also proves `resampling-inference-sibling-present`; the raw-row
   `ttest_ind` remains in the candidate census. A
   script containing **only** the same raw test and its p-output, with no code-visible
   dependence-aware/aggregated/resampling sibling, is a contract-conflict evaluation candidate even if
   printed strings call it “illustrative,” “invalid,” or “do not cite.” This known boundary is accepted:
   prose is permanently unavailable evidence, and the bounded wording truthfully says only that frozen
   one-row-per-authorized-unit authority conflicts with one checked static code/dataflow path. It does
   not call the science invalid or claim the result is primary, selected, or relied upon.
5. **Groupby laundering through a print loop.** For an aggregated groupby value placed in a literal
   label/value tuple, the iterable-member edge propagates aggregation to the loop target. If that target
   or any alias later reaches a test argument, the first outward code is
   `loop-target-aliases-tracked`; the internal aggregation label must also remain on the backward slice.
   Adding a print of the same target does not cut either edge. A variant whose loop target is never used
   by a test may be admitted, but supplies no evidence.

## 12. Test-plan delta

All 1.0–1.3 tests that exercise authority, CSV, D1', reader/selection/test/sink, suppressors, historical
detector immutability, false-accusation halt, and no execution remain active. Retired report-lane tests
remain retired for the documented no-prose reason.

### 12.1 Graph and admission tests

- Def/use positives and refusals for simple assignments, aliases, parameters, returns, loop targets,
  attributes, literal container members, destructuring, whole-container uses, and mutations.
- Directional pairs: a statement/loop target that only reads a protected selection for print must pass;
  the byte-matched variant whose defined target later feeds either test argument must return
  `admission-slice-reaches-operand` or `loop-target-aliases-tracked`. Envelope-1 P1/P3 are mandatory
  normal-path regressions.
- Dict/tuple/list member tests for selection, frame, aggregation, statistic, p-result, unknown, duplicate
  keys, dynamic keys, stars, comprehensions, and member mutation.
- Non-reader aggregate label reads cover literal and closed literal-loop `.loc`, `.at`, and `Series[...]`;
  the same `.loc` spelling on the reader remains an R2 selection. `df67e751`'s
  `egg_weight.loc[diet]` is a named regression.
- Every builtin, NumPy, SciPy-distribution, pandas, exception, and string registry row: one admitted
  output-only probe; wrong module, shadow, dynamic attribute, wrong receiver, forbidden keyword, or
  project-defined object must abstain.
- Builtin adversarials cover every listed-name shadow form, `print(file=...)`, starred/dynamic print
  arguments, and `key=` on `sorted`/`min`/`max`. NumPy adversarials cover positional and keyword `out`
  on every listed ufunc family and positional/keyword `overwrite_input` on the six named
  percentile/quantile/median forms.
- Attribute/subscript probes cover every section-5.7 row and refuse chained `.parent`, `.parents[...]`,
  unknown properties, dynamic labels, and reader-frame label reads outside R2. Comprehension/generator
  probes cover list/dict/set/generator forms over `df.columns` and refuse a target/member later used by a
  test.
- `math.*` exact resolution and refusal of private/dynamic/chained attributes.
- Registered R2 aggregations/safeguards after the candidate test stay visible but do not suppress when
  output-only; the same byte pattern before the test must fail R1, and a value routed to a test or
  competing test must suppress. `d92b542e` is the named pre-test miss.
- If/else, missing-column raise, assertion, verdict ternary, for/while, try/except/finally, and with-body
  positive probes; tracked writes, unresolved handlers/context managers, break/continue, and body
  asymmetry negative probes.
- Zero-return print helpers; assignment from a zero-return helper; depth, recursion, default,
  annotation, variadic, closure, decorator, async/yield, and global/nonlocal boundaries.
- After-inlining probes prove an admitted local helper leaves no call node; a remaining off-list or
  unresolved call consuming a frame/selection returns `unregistered-component-consumer` whether its
  result is printed, stored without later use, or ignored. Passing a mutable tracked value to a call not
  proven read-only is `may write`; an unresolved read-only proof must abstain.

### 12.2 Safety invariance tests

- Differential fixtures prove every base R2 operand/component reason is byte-identical before and after
  adding arbitrary admitted descriptive code.
- A mixed model, GEE, unit aggregation, aggregated sibling test, second raw candidate, second accepted
  reader, tracked mutation, off-registry model/test/bootstrap reaching output, or unsupported operand
  transform remains a refusal regardless of surrounding admitted code.
- Large-resampling tests cover `range` at 49/50, closed constants, literal iterables, comprehensions,
  NumPy module draws, direct `default_rng` draws, scalar/tuple size 49/50, tracked/no-tracked body data,
  every exact mean/std/percentile/quantile terminal, accepted/no output sink, and unresolved bounds. The
  named all-listed-call cluster bootstrap beside a raw test must return
  `resampling-inference-sibling-present`.
- Each of the five section-11 traces is a named regression test. For the groupby-loop laundering probe,
  assert both the outward loop code and retained internal aggregation lineage.
- Statistic-only output still fails the p-result sink. A p-result in a literal container member may
  satisfy the sink only through that exact member edge.
- Definition ceiling 16/17 applies after helper/member expansion on operand, sibling, and result paths.

### 12.3 Prose/no-execution tripwire

Instrument `select_code_source_envelope`, the adapter `inspect`, helper expansion, graph construction,
forward/backward slicing, member propagation, R1 call admission, and R2 scans. Fail if any Markdown,
report, comment token, docstring value, task prose, prompt, printed-label text, or free-text model payload
is requested or inspected. Mutating comments, docstrings, reports, printed labels, and exactly the
section-9 unrelated string constants must leave the typed observation byte-identical. Contract-header,
group-value, API-keyword/value, and X1-path constants are separately held fixed. Instrument imports/calls
so no project file is imported or executed.

### 12.4 End-to-end gates

- All 26 opened cases match section 10 through direct analysis and normal `sc-referee audit`, with exact
  first reasons, zero Findings, and replay equality.
- Four K t-test cases match section 10.4; two K binomial controls remain outside the procedure/domain.
- All 108 existing blind and 155 regression cases produce zero Findings from this adapter and preserve
  every unrelated result.
- False-accusation halt, grant/pin drift, historical detector digests, manifest coexistence, production
  demonstration no-execution, and starter binding-grant tests remain active.
- Run the full default gate, changed-surface suite, `ruff check .`, `ruff format --check .`, `mypy src`,
  corpus validators, and `python scripts/validate_starter.py`. The Alex-owned root release-manifest
  refresh remains a disclosed expected failure until release work.

## 13. File-by-file build delta

Files omitted here must not change for the 2.0 build.

| File | Responsibility | Rough logical change |
| --- | --- | ---: |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py` | Replace descriptive shape gates with directional member-sensitive graph, R1 operation registry/control analysis, R2 full-program precedence, and the closed large-resampling sibling guard. | +900 / -420 |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py` | Bump adapter/check/grammar identity; preserve CSV fact and Finding wording. | +12 / -8 |
| `src/sc_referee/scientific_checks/profiles.py` | Register check/adapter `2.0.0` and exact new coverage limits. | +15 / -10 |
| `src/sc_referee/scientific_checks/integration.py` | Add the unique root `analysis.py` fallback for an unresolved publication surface and bind the 2.0 code-lane subject to its static-source observation. | +26 / -8 |
| `src/sc_referee/scientific_requirement_contract.py` | Permit frozen 1.3.3 authority migration to active check `2.0.0`; schema/profile stays `1.1.0`. | +4 / -1 |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v2_0.py` | New experimental detector identity; prior detector files untouched. | new, ~100 |
| `src/sc_referee/detectors/method_conflict_registry.py` | Register exact 2.0 detector class. | +5 / -1 |
| `scripts/build_capability_source_manifests.py` and packaged capability/scientific registries | Add versioned 2.0 records without removing 1.0–1.3 history. | +18 / generated |
| `tests/test_code_csv_dependence_dataflow.py` | Full R1–R4, may-write, operation-registry, directional-flow, and resampling unit/adversarial matrix with every new code. | +1,500 / -300 |
| `tests/test_code_csv_dependence_adapter.py` | Identity, fact stability, authority/CSV integration, and no-prose/no-execution tripwire. | +180 / -20 |
| `tests/test_dependence_code_slice_development.py` | All 26 opened scripts, four K t-tests, two K controls, exact normal-path outcomes and replay. | +280 / -60 |
| `tests/test_capability_matrix.py`, `tests/test_scientific_check_integration.py`, `tests/test_scientific_check_registry.py`, `tests/test_dependence_recognition_scientific_adapter.py` | Exact live/historical identity assertions. | +45 / -20 |
| `evaluation/development/pseudorep-code-slice-v2_0/DEVELOPMENT_LEDGER.json` | Canonical opened/K digests and expected outcomes; zero qualification credit. | new, ~280 |
| `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md` | After review acceptance only, record the reachability amendment/provenance. | +35 |
| `docs/implementation/CAPABILITY_MATURITY_LEDGER.json`, `docs/implementation/PUBLIC_INTERFACES.md`, `docs/implementation/GROWTH-LOOP-STATE.md`, regression plan/ledger | Regenerate or document exact current identity/outcome only. | generated/documentation |

Explicitly unchanged: contract schema/profile `1.1.0`, CSV/D1', report adapter and every report/prose
grammar byte, reader/selection/test/sink allowlists, dependence/aggregation registries, fact fields,
Finding title/summary, generic detector, qualification grants, complete-domain production pin,
execution/security machinery, Slice C, v2 wall grammar, all four historical code-lane detector files,
and burned envelope directories.

## 14. Fresh Envelope 4 protocol

Envelope 4 uses wholly new bytes. Envelope 1–3 prompts, cases, roles, labels, code, outputs, and opened
development results earn no credit and are unavailable to prompt/project authors.

1. Before commissioning, accept the ADR amendment and this design, complete the exact build/test matrix,
   obtain independent safety review, and freeze the full implementation closure. Any closure-byte change
   thereafter burns the envelope.
2. A new isolated prompt-author receives a newly frozen, digested briefing. It has no access to the
   repository, this design, grammar, allowlists, prior prompts/cases, K, or detector output. The briefing
   may require only one root `analysis.py` in Python; it must not mention helpers, reachability,
   containers, APIs, wording, suppressors, or accepted shapes.
3. Freeze twelve prompts in opaque fixed order: six scientific positives requesting repeated authorized
   units whose row values are passed to an independent two-sample test, and six negatives. Negative
   scientific shapes are: per-unit aggregation before testing; genuine one-row-per-unit input;
   dependence-aware or aggregated analysis beside a tempting raw test; correct per-unit summary loaded
   from a second CSV; off-registry dependence-aware primary with illustrative raw test; and helper-defined
   pseudobulk returning the aggregated table.
4. Freeze prompt digests and lengths, then twelve independently authored projects, then contracts and
   labels under the same role/custody isolation as Envelope 3. The builder sees no prompt, case, role,
   label, or detector output before scoring.
5. Run normal reportless `sc-referee audit` twice plus model-free replay for every case. Project-authored
   code remains unexecuted.
6. Pass requires at least **3 of 6 positives** as evaluation candidates, exactly **0 of 6 negatives** as
   candidates, zero Findings across the 108 existing blind cases, 155 regression cases, and all twelve
   envelope cases, and replay equality 12/12. Positive recall is reported as measured and is not required
   to equal 1.0.
7. There is no prompt retry, case replacement, post-freeze grammar edit, suppressor waiver, or partial
   credit toward a production pin. A negative candidate burns the envelope and triggers the false-
   accusation halt. Fewer than three positive candidates burns it for insufficient recall.
8. Open bytes and labels only after scoring and closure verification. Opened cases then become development
   evidence only.

Envelope 4 passing is necessary but not sufficient for Finding promotion. Qualification, accepted ADR
state, exact grant/pin installation, zero-FA review, and release-manifest refresh remain separate steps.

## 15. Observed, inferred, and review-sensitive points

**Observed:** Envelope 3's frozen 1/6 and 0/6 result; the exact analysis ASTs cited above; the existing
R2 registries and ordered predicate; the five positive walls and six negative substantive guards; the
first historical blind catch; and byte-identical replay/closure results.

**Inferred and requiring build verification:** that the graph can conservatively resolve every admitted
control/helper/member edge; that section 10 reaches 11/12 opened positives without changing any negative;
that `d92b542e0bb28fa3c950` remains the one honest positive miss; and that the R1 call registry covers
enough fresh descriptive variation to reach Envelope 4's bar.

**Deliberate coverage limits:** protected helpers retain X4 depth/binding/annotation/recursion limits;
dynamic container keys, dynamic calls, project-defined methods, higher-order functions, inter-file
analysis, and unresolved alias/may-write edges abstain. These limits may reduce recall but cannot be
silently widened during the build.

No build-changing question is left open in this draft. Review may reject or narrow any R1 registry row;
it may not widen R2, read prose, execute project code, weaken zero false accusations, or change the
bounded Finding wording without a new maintainer decision.
