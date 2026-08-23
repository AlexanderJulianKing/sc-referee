# Pseudoreplication code slice 3.0: operand-identity-first development lane

Status: **Draft for maintainer review; not authorized for build**

Decision provenance: **Fable, under executive authority granted by Alex 2026-08-21; 2026-08-23**

Depends on:

- `docs/implementation/PSEUDOREP-CODE-SLICE-DESIGN-2026-08-22.md`;
- `docs/implementation/PSEUDOREP-CODE-SLICE-2.3-DESIGN-2026-08-23.md`;
- `docs/implementation/PSEUDOREP-CODE-SLICE-2.4-DESIGN-2026-08-23.md`; and
- `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`.

This document is a recognition-predicate delta. It does not authorize a production-pin change,
qualification, envelope, commit, or installation. The qualified production binding remains the
byte-frozen 2.1.0 lane and wording-v1 profile installed after Envelope 5. Slice 3.0 may replace only
the explicit `development` binding created by slice 2.4.

## 0. Observed state, decision input, and projection labels

### 0.1 Observed in the repository

- The code-lane denominator is the 68 scripts in Envelopes 2 through 7: 33 adjudicated positives
  and 35 adjudicated negatives. Envelope 1 is excluded from this denominator because it was authored
  for the withdrawn report-first experiment, although its Python fixtures remain useful regression
  material.
- The 2.3 development ledger records 19/27 retrospective positive candidates and 0/29 negative
  candidates over Envelopes 2 through 6
  (`evaluation/development/pseudorep-code-slice-v2_3/DEVELOPMENT_LEDGER.json`). Envelope 7 adds 2/6
  positive candidates and 0/6 negative candidates
  (`evaluation/development/blind-envelope-7-2026-08-23/AUDIT_RESULTS.json`). Thus the opened-corpus
  2.3 total is 21/33 positives and 0/35 negatives.
- Historical blind first contact remains 9/33 positives: 0, 1, 2, 4, 0, and 2 in Envelopes 2 through
  7. No later replay changes that historical measurement.
- The ten adjudicated family-C negatives in Envelopes 3 through 7 are two per envelope. The two
  existing designed resampling guards are `be94cec09f73d4a3036a` and
  `b12c6fd59e338b7b156e`; the other eight named in section 8 were previously protected first by
  incidental shape/admission codes.

### 0.2 Maintainer-provided strategy evidence

Fable reports an independent long-tail analysis over all 68 cases: 19/24 historical blind misses
were stopped off the candidate operand path, idiom deltas cleared roughly one case while new
envelopes introduced roughly four idioms, and eight of ten family-C controls depended first on
incidental shape codes. These are maintainer-provided decision inputs, not claims independently
recomputed by this document.

### 0.3 Meaning of outcome labels below

`Observed` describes committed bytes or committed result records. `Projected 3.0` is a static
re-trace against this unbuilt predicate. It is not blind evidence and must be verified by the build.
The honest projected opened-corpus result is **27/33 positives and 0/35 negatives**. The six projected
positive misses are `9d44076b46746ce05758`, whose separate `scipy.stats.pearsonr` call is intentionally
stopped by S3, plus the five unit-summary outputs intentionally stopped by S5:
`045708a55a9f3e2ec449`, `2d47b05c996177f2afd7`, `34b1ade6d028cfda2a75`,
`71939b3441556e9e02b6`, and `367e084ddc8f997786f1`. Historical first-contact recall remains
**9/33**; it must not be relabelled 27/33.

## 1. Normative scope and terms

### 1.1 Selected source scope

The selected source remains one root `analysis.py`, under the existing project-surface exclusion and
size limits. Project-authored code is parsed but never imported or executed. Module scope is selected
for a flat script; otherwise the selected `main` body and module-level definitions reachable under
unchanged X4/X4a helper inlining form the value graph.

S1, S2, S3, S4, S5, the accepted-reader census, and the registered-test census inspect the entire selected
module: module statements, `main`, every function body, and every class body whether called or not.
Other project `.py`, `.ipynb`, and `.R` analysis surfaces retain the existing coverage census; an
accepted reader or a call under S1/S3 there causes abstention rather than being ignored. No prose from
any surface is inspected.

### 1.2 Value-level node and member edge

A **value-level node** is an AST expression result plus its exact member identity. Dict keys, list and
tuple positions, destructuring positions, subscripts, helper actual/formal bindings, helper returns,
and loop-container literal keys are separate edges. A whole container is the union of its member
edges; reading a closed literal member follows only that member.

### 1.3 Operand backward slice

For one positional test argument, its **operand backward slice** is the least fixed point of value
edges from the argument back to a reader result. It includes only definitions that can produce that
argument value. Merely reading the same frame elsewhere does not put that other statement on the
slice. Unknown aliasing, a cycle, a dynamic key that could select more than one member, or an
unresolved helper on the slice emits `unresolved-call-on-operand-slice`.

### 1.4 On-path, off-path, and unconditional admission

An operation is **on the operand path** exactly when its result or store target is a node on either
operand backward slice or the reader-to-operand lineage. Everything else is **off-path**.

Off-path syntax is admitted unconditionally. There is no R1 statement admission, descriptive-call
registry, print grammar, control-flow-body grammar, whole-program definition ceiling, or generic
unregistered-component-consumer rule in 3.0. Off-path code can still cause abstention only through:

1. the accepted-reader census (P4);
2. S1 dependence-aware API census;
3. S2 large-resampling inference census;
4. S3 statistics-API census;
5. S4 multiple candidate census; or
6. S5 unit-level-summary census.

The existing 1 MiB source limit, 50,000-AST-node limit, X4 helper depth/recursion rules for helpers
that reach an operand, other-analysis-surface census, and deterministic resource limits remain. A
limit failure abstains; it never admits a partial slice.

### 1.5 Literal and authorized group domain

A **literal** is an AST `Constant` of the required primitive type or a closed module constant that
resolves recursively to that primitive type without a call. The **authorized group domain** is the
two nonempty byte strings established by the unchanged contract-bound CSV gate for the authorized
group header. Source literals and closed constants match those bytes exactly; no case folding,
Unicode normalization, semantic synonym, or prose interpretation is permitted.

## 2. Ordered candidate predicate

The development adapter produces exactly one evaluation candidate if and only if P1 through P5 all
hold. Preliminary source/resource failures still abstain. Within the scientific predicate, evaluate
P1, P4, the syntactic S4 census, test/slice construction, and the reasons in the precedence order in
section 6. Predicate order dominates source position.

### P1. Unchanged contract-bound CSV gate

Reuse the complete 2.3 CSV gate byte-for-byte, including:

- the exact contract path, authorized unit header, authorized group header, CSV byte/row/column/field
  limits, header checks, and two-value group domain;
- `N > U`, nonempty unit values, repeated unit values, both group levels present, and group constancy
  within each declared unit;
- D1-double-prime from 2.3: for a candidate column `C`, `(unit, C)` pairs are a within-unit index if
  the pairs are unique, `distinct(C) <= M`, and every declared unit repeats (`R == U`); a unique pair
  column failing that definition emits `unique-nonindex-composite-key-possible`; and
- the v2 non-inference: `The declared unit column may be one component of a composite key.`

The known nested-value-set residual and closed label-collision control remain exactly as documented
in 2.3 sections 3.3 and 3.4. Slice 3.0 does not revisit that accepted coverage limit.

### P2. Exact value-level raw-row operand identity

Both positional arguments of exactly one registered two-sample call must independently resolve to:

```text
authorized_reader -> authorized CSV frame -> rows where frame[G] == GROUP_LITERAL -> frame[V]
```

The following all must hold:

1. both slices terminate at the same single authorized reader definition from P4;
2. both select the contract group header `G` by equality to a literal/closed constant;
3. the two literals are distinct and their byte set equals the authorized two-value group domain;
4. both project the same literal CSV header `V`;
5. `V` is neither the authorized unit header nor the authorized group header;
6. every operation on each slice is an exact recognized non-reducing edge below; and
7. neither slice contains a P3 reducer, an unresolved call, or an on-slice tracked-frame mutation; and
8. each operand's proven row lineage is exactly all authorized-CSV rows having that operand's group
   literal, and that row set contains at least one repeated authorized-unit value.

The registered candidate APIs remain exact resolved
`scipy.stats.ttest_ind` and `scipy.stats.mannwhitneyu`. Imports and aliases resolve through the
existing established-API resolver. Dynamic imports, dynamic attributes, partial application,
starred arguments, or a test reached only through an unresolved callable abstain.

#### P2.1 Recognized non-reducing slice edges

These are the exhaustive pass-through forms. Omission is not pass-through.

1. Identity binding: simple assignment, annotated assignment without value-changing annotation
   semantics, tuple/list destructuring by exact position, and `frame.copy()` with no arguments.
2. Row selection: `frame[BOOLEAN_MASK]`, `frame.loc[BOOLEAN_MASK]`,
   `frame.loc[BOOLEAN_MASK, COLUMN]`, and the equivalent selection when the mask is named. The
   group-domain proof must include an exact `frame[G] == literal` edge. The adapter evaluates every
   closed mask against the authorized CSV facts and admits the chain only when its selected row-index
   set byte-equals the complete set of CSV row indices for that group literal. A second predicate that
   is statically true for every row in that set is allowed; any predicate that removes a row or cannot
   be evaluated exactly abstains `selected-group-row-completeness-unproven`.
3. Query: `.query()` only under the existing closed equality grammar for literal headers/values;
   dynamic query text abstains.
4. Column projection: `frame[LITERAL_COLUMN]`, `.loc[..., LITERAL_COLUMN]`, and a closed literal
   one-column projection later reduced back to that same member.
5. Vector materialization/casts: `.to_numpy()` with no argument, `dtype=` with a literal/closed dtype,
   or one positional literal/closed dtype, including `.to_numpy(float)`; `.astype(LITERAL_OR_CLOSED_DTYPE)`;
   `numpy.asarray(V)` and `numpy.array(V)` with no `out`, copy callback, or object-producing dynamic
   dtype. Exact one-argument `numpy.log(V)`, `numpy.log1p(V)`, `numpy.sqrt(V)`, and `numpy.exp(V)` with
   no keywords are non-reducing value edges.
6. Row-preserving/read-only transforms: `.sort_values()` without `inplace`, `.reset_index()` without
   `inplace`, and `.rename()` without `inplace`. Their arguments must be literals/closed constants.
   `.dropna()` always lowers row completeness in the 3.0 implementation because no bounded CSV
   nonmissing proof is implemented; a later group selection cannot restore it.
7. Literal/member containers: dict/list/tuple construction, literal-key/position read, exact
   destructuring, and member-sensitive helper return. A dynamic key that could select another member
   abstains.
8. X4/X4a helper return and parameter edges, with unchanged depth 2, nonrecursive expansion,
   deterministic actual/default binding, alpha-renaming, and one expansion per call site. Only helpers
   that reach an operand need expansion; arbitrary off-path helpers are ignored by P2 but remain
   visible to S1-S5.
9. Loop-member reconstruction: `container[key] = selection` followed by `container[LITERAL]` resolves
   that literal member for any literal key. When `key` is a loop target, the iterable must be a closed
   literal/list/tuple or module constant and each iteration is evaluated separately. A selected
   member passes only if its own group literal satisfies checks 2-3; other members do not contaminate
   it unless the whole container or a dynamic key is read.
10. A merge/join edge only when both inputs are identity views of the authorized reader, every left
    and right join-key list contains the authorized unit header, and a closed literal
    `validate="one_to_one"` plus literal join keys prove that the selected value's row lineage is not
    collapsed, duplicated, or replaced. `on=`, or the corresponding `left_on=`/`right_on=` pair, must
    name the unit header on both sides; index-only joins do not qualify. Every other merge/join on a
    slice abstains; a reduced input takes the P3 reason.

`filter on rows` in this design means the closed boolean/query forms in items 2-3, not an
arbitrary call named `filter`. Chained `.parent`, dynamically computed headers, opaque methods,
user-defined transforms not expanded by X4, and every other call on an operand slice emit
`unresolved-call-on-operand-slice`.

#### P2.2 Operand-level repeated-row proof

P1 proves repetition in the full authorized CSV; P2 must separately prove it for each test operand.
For each operand, construct the exact CSV row-index set selected by its complete recognized mask/query
chain. It must byte-equal the full set of authorized-CSV rows whose `G` value is that operand's group
literal, and at least one authorized-unit value must occur more than once in that set. The proof is
performed independently for both operands. A missing row, an unknown predicate truth value, an
untracked row identity, or a selected group with no repeated unit emits
`selected-group-row-completeness-unproven`.

This closes the following false-accusation shape:

```python
last = df[df["visit"] == FINAL_VISIT]
a = last.loc[last[G] == LEVEL_A, V]
b = last.loc[last[G] == LEVEL_B, V]
stats.ttest_ind(a, b)
```

when `last` contains one row per unit. The opened family-C case `245226f0f9f97f6acda2` has this shape
at lines 197-203 and also has an S1 mixed-model sibling. Under the ordered predicate it stops first at
S1; the isolated final-visit raw test stops at P2.2 rather than becoming a candidate.

`.iloc[...]`, `.head(...)`, `.tail(...)`, `.nth(...)`, `.sample(...)`, a mask based on
`.cumcount() == 0`, and `drop_duplicates(subset=UNIT)` can all discard selected-group rows. None is an
admitted row-selection edge, even when its argument is static. They take
`selected-group-row-completeness-unproven` (or the earlier P3 reason when the operation is already on
the closed reducer list). There is no syntax-based exemption for a selector that happens to look like
a final visit or one row per unit.

### P3. No reducing operator on either operand slice

If any of the following contributes a value to either test argument, emit
`aggregation-on-test-operand-path`:

1. `groupby(...)` followed anywhere in the same member path by `agg`, `aggregate`, `apply`,
   `transform`, `mean`, `median`, `sum`, `std`, `var`, `min`, `max`, `first`, `last`, `count`, `size`,
   `nunique`, `prod`, `sem`, `quantile`, or `describe`;
2. frame/series `mean`, `median`, `sum`, `std`, `var`, `min`, `max`, `first`, `last`, `count`,
   `nunique`, `prod`, `sem`, `quantile`, `aggregate`, `agg`, `apply`, or `transform` when its result
   feeds a test operand;
3. `pivot`, `pivot_table`, or `resample` on the slice;
4. `drop_duplicates` whose `subset` contains the authorized unit column, whether the column is named
   directly or by a closed constant;
5. `merge` or `join` with any frame/member derived through a reducer in items 1-4;
6. NumPy `mean`, `nanmean`, `median`, `nanmedian`, `sum`, `nansum`, `std`, `nanstd`, `var`, `nanvar`,
   `min`, `nanmin`, `max`, `nanmax`, `average`, `quantile`, `nanquantile`, `percentile`, or
   `nanpercentile` over a value that feeds the operand; and
7. `head`, `tail`, `nth`, `sample`, `cumcount`, `idxmin`, or `idxmax` when its result, or a mask/index
   derived from its result, selects rows that feed the operand;
8. `rank`, `diff`, `rolling`, `ewm`, or `transform` when its result feeds the operand; and
9. a comprehension or loop that maps more than one reader row/member to one scalar/member, chooses
   one representative per unit/group, or otherwise collapses rows before the test.

`.apply`, `.agg`, and `.transform` are guards even when a particular callback could preserve length.
Items 7-8 are conservatively classified `aggregation-on-test-operand-path`: the former choose rows and
the latter replace values or introduce a window/group transform whose raw-row identity is no longer
the exact P2 value. A `drop_duplicates` on another column is not declared non-reducing: it therefore
abstains `unresolved-call-on-operand-slice`, never passes by omission. A loop/comprehension whose
cardinality effect cannot be proven non-collapsing also takes the unresolved-slice reason.

### P4. Single authorized reader

The accepted reader forms and exact static path resolver remain unchanged: registered
`pandas.read_csv`, `numpy.genfromtxt`, and supported `csv` module forms. Exactly one accepted reader
definition may appear anywhere in selected scope and its statically resolved project-relative path
must byte-equal the contract path. Every second accepted reader, including one in an uncalled helper
or with `parse_dates`, emits `additional-accepted-reader-present`. Any computed path outside the
existing X1/G6 forms abstains.

Both operand slices must terminate at that one definition. A value loaded by another mechanism or a
summary supplied independently cannot be joined onto the authorized lineage.

### P5. No inference-sibling guard and a reachable p-result output sink

S1-S5 below are full-scope code-fact guards. If none fires, off-path statements are admitted without
further grammar. Generic validation, formatting, plotting, file output, exception handling, dynamic
calls, comprehensions, and helpers off the operand path cannot create or suppress a candidate unless
they meet P4 or S1-S5.

The candidate call must be in the selected module/main reachable call graph, outside a statically dead
closed-literal branch, and its **p-result** must reach one exact p-result-eligible console/file sink
from base design section 5.7 through that section's finite forward def-use grammar. A statistic-only
sink does not satisfy this check. An unused result, a call in an uncalled function, a call after an
unconditional return/raise in the same block, or a call exclusively under `if False`, `if 0`, or
`while False` abstains `test-result-output-sink-unavailable`. A nonconstant branch is possibly
reachable; it is not declared dead merely because static analysis cannot choose the branch.

Reaching the sink is structural code evidence, not evidence that project code executed or that the
result was scientifically selected. The unchanged non-inferences and contract-conflict wording remain
mandatory.

## 3. S1 — dependence-aware sibling anywhere

Emit `dependence-aware-sibling-present` if any resolved call anywhere in selected scope is rooted at
one of these exact API entries:

```text
scipy.stats.ttest_rel
scipy.stats.wilcoxon
statsmodels.formula.api.mixedlm
statsmodels.api.MixedLM
statsmodels.regression.mixed_linear_model.MixedLM
statsmodels.api.GEE
statsmodels.genmod.generalized_estimating_equations.GEE
statsmodels.api.GLMGam
statsmodels.gam.api.GLMGam
pingouin.mixed_anova
pingouin.rm_anova
```

Constructor calls, `from_formula`, `fit`, and every later attribute/method chain rooted at one of
those entries count. Independently of module identity, a `.fit(...)` call also counts when its receiver
chain contains a constructor or `from_formula(...)` call with any of the exact keywords `group_data=`,
`groups=`, `re_formula=`, or `cluster=`. A call rooted under `statsmodels` also counts when its `.fit`
has exact literal `cov_type="cluster"`. Values for the grouping keywords need not be tracked; presence
of the exact keyword shape is the suppressing code fact. Import aliases resolve to canonical identity;
dynamic resolution under one of these roots abstains under S3.

**False-accusation analysis.** S1 only removes Finding eligibility. Its conservative false-negative
mode is an unused dependence-aware helper causing abstention. Its dangerous false-positive mode would
be failing to resolve a mixed/GEE call and then treating a raw illustrative test as the only
inference; the full-scope root-chain census and S3 backstop close the registered cases. Calls named
`mixedlm` on an unrelated non-statistics object do not count unless the explicit `groups=`/
`re_formula=`/`group_data=`/`cluster=` formula-fit shape applies. This broad keyword guard can abstain
on an unrelated user-defined `.fit` using the same parameter name; that is an accepted recall loss,
never a false accusation.

## 4. S2 — large resampling inference sibling anywhere

Emit `resampling-inference-sibling-present` when all four conditions hold:

1. A repeated generator has resolvable cardinality at least **10**. Retain the 2.3 registered
   NumPy/random-draw branch; add `for`, list/set/dict comprehensions, and generator expressions over:
   exact `range`, closed literal/module containers, `numpy.arange`, or exact
   `itertools.combinations`/`itertools.permutations`. Resolve helper parameter defaults and module
   constants. Resolve `range(len(X))` when `len(X)` is known from a literal/member container, the
   authorized CSV row count, a group selection count computed from that CSV, or a registered draw
   shape. Combination cardinality is `n!/(r!(n-r)!)`; permutation cardinality is `n!/(n-r)!`.
   An exact procedure with `C(6, 3) = 20` therefore fires; a nine-trip procedure is the last cardinality
   near miss. Unresolved loop cardinality does not positively label S2 but remains subject to S3 or an
   unresolved operand slice.
2. The repeated body or registered draw indexes, samples, permutes, concatenates, or otherwise draws
   from a dict/list/tuple/Series/array/frame member derived anywhere from the authorized CSV. The 2.x
   requirement that the value carry a particular tracked-name label is deleted. Member edges, helper
   returns, destructuring, actual/formal bindings, and subscript stores are followed.
3. A repeated output reaches exact `mean`, `nanmean`, `std`, `nanstd`, `median`, `nanmedian`, `sum`,
   `nansum`, `count`, `quantile`, `nanquantile`, `percentile`, `nanpercentile`, a count ratio, or a
   sorted-index statistic. A **count ratio** is one of these closed shapes: `len(FILTERED) / len(ALL)`,
   `sum(BOOLEAN_PREDICATE_OVER_OUTPUT) / N`, `numpy.sum(BOOLEAN_PREDICATE_OVER_OUTPUT) / N`,
   `COUNT / N`, or `(COUNT + 1) / (N + 1)`, where `COUNT` is an exact `len`, `count`, `sum`, `nansum`,
   or `numpy.count_nonzero` over the repeated output and `N` is its resolved repeated cardinality.
   Literal `1` is required in both pseudocount positions of the last form. A
   **sorted-index statistic** is `sorted(V)[I]`, `numpy.sort(V)[I]`, or `V.sort_values().iloc[I]`
   where `I` is a literal/closed index or arithmetic from the repeated cardinality.
4. That reduction/statistic reaches an accepted console or file output sink through identity,
   arithmetic, literal member, or X4 helper edges.

Registered NumPy/random draws retain the exact 2.3 identities, including
`numpy.random.default_rng(...).integers/choice/random/standard_normal/normal/uniform`. For scalar
`size=N`, `N` is one factor. For tuple/list `size=(F1, ..., Fk)`, resolve each factor independently
through literal/module constants and helper-default bindings. An unresolved factor contributes the
conservative lower bound 1 and does not erase a resolved factor. A draw is LARGE when any resolved
factor is at least 10. Retain the prior product rule when every factor is resolved; an unresolved
factor is never guessed above 1 merely to make a product cross the threshold. This makes the exact
`size=(n_boot, n_a)` shapes in `19824e3f6b1e3980872f` lines 194-203 and
`2f0d38f48abd53ab90a8` lines 60-73 large from the resolved `n_boot=20000` even though `n_a` is derived
from an aggregate. It also retains the helper-default `range(n_resamples)` shape in
`b12c6fd59e338b7b156e` lines 67-112. All three are mandatory guard-first fixtures.

S2 outranks S3 and any source-position ordering. A bootstrap declared after its output consumer or
split across helpers still takes S2 when the fixed-point graph closes.

**False-accusation analysis.** S2 can conservatively abstain on a large descriptive simulation whose
summary is printed beside the raw test; that is a recall loss, not an accusation. The dangerous miss
is a hand-rolled dependence-aware bootstrap hidden in an ordinary dict or vectorized draw. Dropping
the name-label condition, retaining registered vectorized draws, following member edges, and adding
closed `itertools` cardinalities address the observed forms. Dynamic resampling remains unsupported;
S3 suppresses it when a statistics API is visible, otherwise the boundary is a declared coverage
limit and requires a negative probe before any later widening.

## 5. S3 — unresolved statistics inference sibling

### 5.1 Closed prefix registry

Resolve imports/aliases and inspect every call under these exact prefixes:

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

`scipy` alone is not a prefix match outside `scipy.stats`. NumPy random draws are governed by S2, not
S3. A call under a prefix emits `unresolved-inference-sibling-present` unless it is:

1. the one registered P2 candidate call;
2. exact `scipy.stats.sem(V)` with one positional value and optional literal `axis`, `ddof`, or
   `nan_policy`, used only as a descriptive scalar; or
3. exact `scipy.stats.t.ppf(P, DF)` with two positional scalar arguments and no keywords, where `DF`
   is derived only from the same candidate operands' lengths/variances, `P` is literal/closed
   arithmetic, and the result reaches only arithmetic/output associated with that same candidate.

Items 2-3 define “recognized descriptive reducer” for S3. They are intentionally narrow. Other
distribution methods, `pearsonr`, `spearmanr`, `linregress`, `f_oneway`, `kruskal`, one-sample tests,
survival/model fits, cross-validation, and dynamically selected statistics calls abstain. A `t.ppf`
call with unrelated inputs or whose result reaches another registered test also abstains.

**False-accusation analysis.** S3 only abstains, but it is the safety backstop for off-registry mixed
models, manual secondary inferential calls, and libraries not understood by the operand grammar. Its
false-negative mode is a hand-written inference using only builtins/NumPy and no large resampling
shape; that remains a declared boundary. Its false-positive/recall cost is a harmless statistics call
anywhere in the module. The narrow same-test `sem`/`t.ppf` exemptions are required by opened positive
fixtures and do not admit an independent inferential call.

## 6. S4, S5, and on-slice mutation

### 6.1 S4 — syntactic registered-test census

Run S4 before and independently of operand resolution. Resolve established API aliases across the
entire selected module and count every syntactic call to registered `scipy.stats.ttest_ind` or
`scipy.stats.mannwhitneyu`, including calls in uncalled helpers, dead branches, containers, nested
expressions, and helpers later expanded for P2. Two or more such resolved call occurrences emit
`multiple-rowwise-test-candidates` even if one or both later lack a valid raw-row operand slice or
output sink. Dynamic calls are not guessed; they remain governed by S3 when under a statistics prefix.

This census can suppress a script containing an unused second raw test. That is a deliberate recall
loss. Its safety purpose is to prevent one resolvable raw-row call from being isolated while another
registered inferential call is ignored because its operand grammar is unsupported.

### 6.2 S5 — unit-level summary sibling anywhere

Emit `unit-level-summary-sibling-present` if both conditions hold anywhere in the selected module,
including uncalled helpers and statically dead branches:

1. code constructs a value with one member/row/scalar per authorized-unit value, or reduces values
   within authorized-unit keys, by any of these exhaustive shapes:
   - `FRAME.groupby(KEYS)` where the literal/closed `KEYS` contain the contract unit header, followed
     by any P3 reducer or by iteration/materialization of the grouped members;
   - `FRAME.drop_duplicates(subset=UNIT)` (including the exact positional unit-header form) followed
     by a value projection or reducer;
   - a loop/comprehension over exact `FRAME[UNIT].unique()`, `set(FRAME[UNIT])`, or a closed alias of
     either, whose body selects `FRAME[UNIT] == loop_target` and stores or accumulates a reduction of
     that unit's rows; or
   - a dict whose keys are values drawn from `FRAME[UNIT]` and whose corresponding values contain a
     reduction of rows selected for that same unit;
2. that unit-keyed result reaches an accepted console/file output sink, or reaches arithmetic whose
   result reaches such a sink. The forward closure follows identity, attribute/subscript/member,
   destructuring, container, loop, X4 actual/formal/return, arithmetic/comparison, formatting, and call
   receiver/argument/result edges. A call consuming the value does not sanitize the lineage; if that
   call's result reaches a sink, condition 2 holds.

The output sinks are every exact structural console/file row in the shared registry in base-design
section 5.7, including its guard-terminal-only file rows; the p-result-eligibility bit is irrelevant to
this suppressor. Exception construction and `raise` are not output sinks for S5. Merely computing a
unit consistency check that can raise therefore does not fire S5. Overall unit counts such as
`FRAME[UNIT].nunique()` also do not fire: they produce one global count, not a unit-keyed summary.

**False-accusation analysis.** S5 only suppresses. It intentionally loses recall when a raw-row test
is printed beside per-unit descriptive output. That loss closes the family-C form in which code
computes unit means and hand-written Welch arithmetic (including a `math.erf` p-value) while also
printing an illustrative raw-row test, even when no registered dependence API or >=10-trip resampling
shape exists. S5 cannot create a Finding. Its declared limit is an off-registry unit-aware procedure
that never materializes a unit-keyed result in one of the four shapes or never sends the result or its
arithmetic to an output sink.

### 6.3 On-slice mutation

`tracked-value-mutation` is narrowed to the operand path. A subscript, `.loc`, `.iloc`, `.at`,
attribute, or `inplace=True` store that changes the reader/frame/selection/member used by either test
argument abstains. The exact G7 same-column date-conversion exemption remains. A mutation wholly
off-path is admitted unless S1-S5 or P4 independently applies.

Guard precedence within the inference stage is:

1. `dependence-aware-sibling-present` (S1);
2. `resampling-inference-sibling-present` (S2);
3. `unresolved-inference-sibling-present` (S3);
4. `multiple-rowwise-test-candidates` (S4);
5. `tracked-value-mutation` on an operand path;
6. `aggregation-on-test-operand-path`;
7. `unit-level-summary-sibling-present` (S5);
8. `selected-group-row-completeness-unproven` (P2.2); and
9. `unresolved-call-on-operand-slice`.

P1 and P4 failures occur before this ranking, and `test-result-output-sink-unavailable` is checked
after exact operand completion. S5 is computed full-scope before operand proof but ranks after the
more specific on-operand P3 reason, so a unit-level primary operand is reported as
`aggregation-on-test-operand-path` while a separate unit-level output sibling still takes S5.
Predicate rank, not source line, selects the first reason.

## 7. Prose exclusion, wording, and lane identity

The permanent no-prose rule is unchanged. The adapter and every slice/guard helper receive Python AST
structure after docstring removal plus contract/CSV facts. They never receive report Markdown,
comments, docstring text, task/prompt bytes, prose strings, printed labels, or inferred intent.
String constants may affect only exact path, header, group-value, API-keyword, format, and structural
literal slots.

A script containing a raw rowwise test on repeated rows whose p-result reaches the required code sink
is a candidate even if comments, docstrings, or report prose call it illustrative, invalid,
disclaimed, or secondary. A result with no qualifying code sink is not a candidate under P5. This is
acceptable only because the record is a bounded frozen-contract-versus-code conflict and retains:

- the title `Analysis code contradicts the frozen one-row-per-authorized-unit requirement`;
- the statement that project code execution is not established;
- the statement that the contract author may be wrong;
- the v2 composite-key non-inference; and
- no assertion of invalid statistics, selection, reliance, numerical effect, or scientific intent.

The development check/adapter/detector identity advances together to 3.0.0 and retains wording-v2.
The 2.1 qualified module, adapter, detector, wording-v1 profile, installed pin, and frozen Envelope-5
source resources remain byte-identical. The ordinary CLI continues to run qualified 2.1.0. Only
`--development-lane` or an envelope-runner lane option runs 3.0, and development remains incapable of
emitting a Finding.

Before a build can change eligibility semantics, ADR-0076 requires an amendment with Fable's decision
provenance. This draft does not make that amendment.

## 8. Family-C guard traces

These are observed code facts and projected first reasons. Every line reference is to that row's
`evaluation/development/blind-envelope-<N>-2026-08-<DATE>/cases/<ID>/project/analysis.py`; no prose
disclaimer participates.

| Envelope/case | Observed inference sibling beside raw test | Projected first reason |
|---|---|---|
| E3 `245226f0f9f97f6acda2` | `smf.mixedlm(..., groups=df["animal_id"])` and `.fit(...)` at 129-137; raw final-week test at 197-203. | S1 `dependence-aware-sibling-present`. |
| E3 `19824e3f6b1e3980872f` | Exact `combinations` enumeration at 180-187 and registered draws `size=(n_boot, n_a)`/`(n_boot, n_b)` at 194-203 with closed `n_boot=20000`; raw test at 237-240. | S2 `resampling-inference-sibling-present` through the registered-draw factor rule. The permutation branch's `n` is derived from a reduced lake table, outside S2's closed cardinality sources, so that branch does not close and is not credited as a second guard. This is the hardest control. |
| E4 `23cc44d49100a68655c5` | `smf.mixedlm`/`.fit` at 131-136; two rowwise t-tests at 199-201. | S1 before S4. |
| E4 `0e06da6bdb3963daae4e` | Chained `smf.mixedlm(...).fit(...)` at 99-103 and a 20,000-draw clutch bootstrap at 128-168; raw test at 174-186. | S1; S2 independently holds. |
| E5 `4d64fa6416ee8406f678` | `smf.mixedlm`/`.fit` at 89-90; raw-row test at 140 and a per-cat test at 179. | S1 before S4/P3. |
| E5 `be94cec09f73d4a3036a` | Helper-default `n_boot=N_BOOT`, `N_BOOT=20000`, drives `range(n_boot)` at 70-100; the whole-patient bootstrap reaches percentile/output before raw test at 170. | S2 `resampling-inference-sibling-present`. |
| E6 `71bd62d3b1b9d590020a` | `smf.mixedlm`/`.fit` at 142-143; week-12 and all-row tests at 220-222 and 258-260. | S1 before S4. |
| E6 `b12c6fd59e338b7b156e` | Helper-default `n_resamples=N_RESAMPLES`, `N_RESAMPLES=10000`, drives `range(n_resamples)` over a dict of bench blocks at 67-112; `sum`/count-ratio at 116-131 and percentile/output at 194-207. | S2 `resampling-inference-sibling-present`. |
| E7 `afb8342cc3b86bf0b90e` | `smf.mixedlm`/`.fit` at 79-82; raw test at 135. | S1. |
| E7 `2f0d38f48abd53ab90a8` | Registered draws `size=(n_boot, na)`/`(n_boot, nb)` at 67-73 with closed `n_boot=N_BOOT=20000`; `std`, percentile, `sum`, and `(r+1)/(N+1)` reach output at 87-96 and 136-151; raw test at 100-102. | S2 through the registered-draw factor and count-ratio rules. |

All ten family-C controls above have a designed S1 or S2 first guard under 3.0. S5 separately pins the
hand-written unit-means/Welch-plus-raw-test shape that uses no registered dependence API and stays
below the S2 trip threshold.

Family-C count by envelope is E3=2, E4=2, E5=2, E6=2, E7=2. Envelope 2 predates this family
stratification; its analogous `e60c84...` mixed-model and `d4d95c...` bootstrap negatives are retained
as S1/S2 regression controls but are not retroactively relabelled family C.

## 9. Family-A and family-B traces

### 9.1 Family A: aggregation reaches the test operand

| Case | Observed value path | Projected reason |
|---|---|---|
| `e303f93351acf5df0457` | Worker-level `groupby(...).agg(mean=...)` at `evaluation/development/blind-envelope-4-2026-08-22/cases/e303f93351acf5df0457/project/analysis.py:53-62` feeds selections at 71-74. | `aggregation-on-test-operand-path`. |
| `094fcb05ef85e4f7f406` | Paddock-level `groupby(...).agg(mean_herbage...)` at `evaluation/development/blind-envelope-5-2026-08-22/cases/094fcb05ef85e4f7f406/project/analysis.py:48-58` feeds the test at 72-75. | `aggregation-on-test-operand-path`. |
| `2438210f2abe4b53295f` | Enclosure-level `groupby(...).agg(mean_live_weight_g=...)` at `evaluation/development/blind-envelope-6-2026-08-22/cases/2438210f2abe4b53295f/project/analysis.py:89-102` feeds the test at 115-127. | `aggregation-on-test-operand-path`. |

### 9.2 Family B: a second accepted reader is present

| Case | Observed readers | Projected reason |
|---|---|---|
| `c69bb7590d57d2057ee0` | Authorized raw and summary `pd.read_csv` calls at E4 `analysis.py:238-239`. | `additional-accepted-reader-present`. |
| `4e24fb76c83774381e41` | Weekly and route-summary `pd.read_csv` calls at E5 `analysis.py:28-31`. | `additional-accepted-reader-present`. |
| `88bb5308e2861b9c90c6` | Raw and recipient-summary `pd.read_csv` calls at E7 `analysis.py:96-97`. | `additional-accepted-reader-present`. |

P4 runs before operand identity, so a correct summary-file test cannot be reinterpreted as a raw-file
conflict merely because the raw reader also exists.

## 10. Projected outcome over all 68 opened code-lane cases

Every row below is a post-opening projection requiring build verification. `Candidate` means one
development evaluation candidate and zero Findings.

### 10.1 Envelope 2 — projected 3/3 positives, 0/5 negatives

| Role/case | Projected 3.0 outcome | First reason/evidence |
|---|---|---|
| P1 `e8f97fe750189052f726` | Candidate | Direct `.loc` operands to `ttest_ind` at 46-54. |
| P2 `2df3396d80adbb63dffb` | Candidate | Direct `.loc` operands to `ttest_ind` at 29-42. |
| P3 `ca18f96d45dff1b921ad` | Candidate | X4 reader helper and direct `.loc` operands at 24-34. |
| N1 `15b07ef7670800ba88e0` | Abstain | `aggregation-on-test-operand-path`; litter means feed the test. |
| N2 `5ef43dbf631adcf3daec` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `e60c84d0cda3cc465df7` | Abstain | S1 `dependence-aware-sibling-present`; `smf.mixedlm` at 190. |
| N4 `6090fc1b1b6dbfcd6eee` | Abstain | `additional-accepted-reader-present`; two `read_csv` calls at 37-38. |
| N5 `d4d95cdd4f4e698d675c` | Abstain | S2 `resampling-inference-sibling-present`; registered RNG bootstrap at 80-99 reaches output before raw test at 263. |

### 10.2 Envelope 3 — projected 4/6 positives, 0/6 negatives

| Role/case | Projected 3.0 outcome | First reason/evidence |
|---|---|---|
| P1 `a28f42e4bd1fe1c5e048` | Candidate | Direct group selections, test at 46. |
| P2 `29893ac47ebe4ca60cce` | Candidate | Direct group selections, test at 53; same-test `t.ppf` exemption at 65. |
| P3 `df67e751158d62c4cbf4` | Candidate | Literal dict member `values` carries each selection to test at 43-45. |
| P4 `045708a55a9f3e2ec449` | Abstain | S5 `unit-level-summary-sibling-present`; `drop_duplicates("horse_id")` produces one age per authorized unit and its mean/range reach print at 57-65. |
| P5 `2d47b05c996177f2afd7` | Abstain | S5; `groupby(["Rootstock", "Vine"]).mean()` produces per-authorized-unit lesion summaries that reach `print(per_vine.to_string(...))` at 123-133. |
| P6 `d92b542e0bb28fa3c950` | Candidate | X4 compare helper, direct selections at 83-86; same-test `t.ppf` at 94. |
| N1 `0b9b803536c12e3870eb` | Abstain | `aggregation-on-test-operand-path`; volunteer means feed the test. |
| N2 `5b80f0787b1b6c47048b` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `245226f0f9f97f6acda2` | Abstain | S1; section 8. |
| N4 `f4e4d89ac44385a18261` | Abstain | `additional-accepted-reader-present`; raw and summary readers at 36-37. |
| N5 `19824e3f6b1e3980872f` | Abstain | S2; section 8. |
| N6 `3c650ec217b884e5f35e` | Abstain | `aggregation-on-test-operand-path`; plant means feed the test. |

### 10.3 Envelope 4 — projected 5/6 positives, 0/6 negatives

| Role/case | Projected 3.0 outcome | First reason/evidence |
|---|---|---|
| P1 `5c26014c176bf905c121` | Candidate | Direct group selections, test at 44. |
| P2 `5bdfa31a22a40d58e20c` | Candidate | X4 compare helper, direct selections at 66-68; unrelated timepoint summary is off-path. |
| P3 `4f622f87ad3c8a93a2d8` | Candidate | X4 compare helper, direct selections at 50-53; summary helper is off-path. |
| P4 `c07cc7c1a1f9730a3c9f` | Candidate | Direct selected vectors, test at 46. |
| P5 `34b1ade6d028cfda2a75` | Abstain | S5; `groupby('dune_name').size()` is keyed by the authorized unit and reaches print at 36. |
| P6 `675de846f46beae7d442` | Candidate | X4 compare helper, direct selections at 29-32. |
| N1 `540f7dfdf1614ceda57d` | Abstain | S4 `multiple-rowwise-test-candidates`. |
| N2 `9cd65ce93b9b8f846eb8` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `23cc44d49100a68655c5` | Abstain | S1 before S4; section 8. |
| N4 `c69bb7590d57d2057ee0` | Abstain | P4; section 9.2. |
| N5 `0e06da6bdb3963daae4e` | Abstain | S1 before S2; section 8. |
| N6 `e303f93351acf5df0457` | Abstain | P3; section 9.1. |

### 10.4 Envelope 5 — projected 6/6 positives, 0/6 negatives

| Role/case | Projected 3.0 outcome | First reason/evidence |
|---|---|---|
| P1 `0b4876ceca6b0a9aede7` | Candidate | Direct selections, test at 39; same-test `t.ppf` at 45. |
| P2 `e50e676afb2cd3593234` | Candidate | Direct selections, test at 64; same-test `t.ppf` at 78. |
| P3 `1975f22bc0022b19331f` | Candidate | Direct selections, test at 51; same-test `t.ppf` at 59. |
| P4 `2448bea72701b75fce2a` | Candidate | Direct selections, test at 47; same-test `t.ppf` at 57. |
| P5 `a1541d5c671f3d6d58ce` | Candidate | Direct selections, test at 48. |
| P6 `f1a04b5358a7b9b9d57c` | Candidate | Direct selections, test at 36; same-test `t.ppf` at 43. |
| N1 `0d274a0eccdb84966940` | Abstain | `aggregation-on-test-operand-path`; subject means feed the test. |
| N2 `4afe430c936bbe560a5e` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `4d64fa6416ee8406f678` | Abstain | S1; section 8. |
| N4 `4e24fb76c83774381e41` | Abstain | P4; section 9.2. |
| N5 `be94cec09f73d4a3036a` | Abstain | S2 on the registered whole-cluster bootstrap. |
| N6 `094fcb05ef85e4f7f406` | Abstain | P3; section 9.1. |

### 10.5 Envelope 6 — projected 5/6 positives, 0/6 negatives

| Role/case | Projected 3.0 outcome | First reason/evidence |
|---|---|---|
| P1 `03ee21366b62d03a9b26` | Candidate | D1-double-prime clears `kit_number`; `.to_numpy(dtype=float)` operands at 86-98. `stats.sem` at 73 is the exact S3 exemption. Per-doe reductions at 48-55 feed only validation/raise and have no S5 output sink. |
| P2 `278451c17389f8c72ece` | Candidate | G7 same-column date conversion remains exempt; direct selections feed test at 73-92. |
| P3 `5b1e03e13ef7e2e727dc` | Candidate | D1-double-prime clears `age_weeks`; direct selections at 136-137 feed X4 test helper at 62-64. Pivot summary is off-path. |
| P4 `d89ab3ef408520667cc1` | Candidate | Accepted `parse_dates` reader and direct selections at 66-69. |
| P5 `92c016654c6c93979fff` | Candidate | Contract-domain loop dict members feed the test at 73-75. |
| P6 `9d44076b46746ce05758` | Abstain | S3 `unresolved-inference-sibling-present` on separate `stats.pearsonr` at 91 before raw test at 101. This is the honest positive miss. |
| N1 `2e97fd3e2ab5729b7f9c` | Abstain | `aggregation-on-test-operand-path`; line means feed the test. |
| N2 `6dfee3d81dba1754e893` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `71bd62d3b1b9d590020a` | Abstain | S1; section 8. |
| N4 `7edfc9aa77704a8a46b8` | Abstain | `additional-accepted-reader-present`; raw and binned readers at 45-46. |
| N5 `b12c6fd59e338b7b156e` | Abstain | S2 on the helper-default dict-container bootstrap. |
| N6 `2438210f2abe4b53295f` | Abstain | P3; section 9.1. |

### 10.6 Envelope 7 — projected 4/6 positives, 0/6 negatives

| Role/case | Projected 3.0 outcome | First reason/evidence |
|---|---|---|
| P1 `aa77af307cf45d44ad2e` | Candidate | X4 load/describe helpers; direct selections at 46-52. Off-path `SystemExit`, formatting, and loop no longer gate. |
| P2 `6d9d7ed878cef263b664` | Candidate | Direct selections, test at 44. |
| P3 `332e02950572d0aba886` | Candidate | X4 reader/summary helpers; direct selections at 43-49. |
| P4 `e0527ba3e1a39416b794` | Candidate | X4 reader/compare helpers; direct selections at 38-40. Off-path group summary is admitted. |
| P5 `71939b3441556e9e02b6` | Abstain | S5; `groupby("tree_id")["canopy_position"].count()` is keyed by the authorized unit and reaches print at 82-84. |
| P6 `367e084ddc8f997786f1` | Abstain | S5; `groupby("cistern_id").size()` is keyed by the authorized unit and reaches print at 54-55. |
| N1 `cfce924fcb9c7c4bdbd2` | Abstain | `aggregation-on-test-operand-path`; patient means feed the test. |
| N2 `912aee5d3e2b3997a652` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `afb8342cc3b86bf0b90e` | Abstain | S1; section 8. |
| N4 `88bb5308e2861b9c90c6` | Abstain | P4; section 9.2. |
| N5 `2f0d38f48abd53ab90a8` | Abstain | S2; section 8. |
| N6 `d85857381a84b3110b9a` | Abstain | `aggregation-on-test-operand-path`; pack means feed the test. |

### 10.7 Totals and K locks

| Partition | Positives projected candidate | Negatives projected candidate | Findings |
|---|---:|---:|---:|
| Envelope 2 | 3/3 | 0/5 | 0 |
| Envelope 3 | 4/6 | 0/6 | 0 |
| Envelope 4 | 5/6 | 0/6 | 0 |
| Envelope 5 | 6/6 | 0/6 | 0 |
| Envelope 6 | 5/6 | 0/6 | 0 |
| Envelope 7 | 4/6 | 0/6 | 0 |
| **All 68** | **27/33 (81.82%)** | **0/35** | **0** |

The six refreshed Batch-K locks remain scored abstentions: four t-test cases lack the required root
`analysis.py` source envelope and two binomial cases do not have the exact two-value registered-test
shape. Expected K development candidates remain 0/6. Qualified behavior is unchanged.

Exactly **six of the 35 opened negatives** stop at the P1 CSV gate with
`no-repeated-authorized-unit`: `5ef43dbf631adcf3daec`, `5b80f0787b1b6c47048b`,
`9cd65ce93b9b8f846eb8`, `4afe430c936bbe560a5e`, `6dfee3d81dba1754e893`, and
`912aee5d3e2b3997a652`. The other 29 reach a code-side guard or operand refusal; no table row treats a
CSV-gate stop as evidence that a code guard worked.

## 11. Honest recall statement and new envelope bar

### 11.1 What may be reported now

- Historical blind first-contact recall over Envelopes 2-7: **9/33 (27.27%)**.
- Historical blind false accusations over their 35 negative controls: **0/35**.
- Projected, post-opening 3.0 replay recall: **27/33 (81.82%)**, subject to build verification.
- Projected trailing-18 replay (Envelope 5-7 positives): **15/18 (83.33%)**; the misses are
  `9d44076...` under S3 and `71939b...`/`367e084...` under S5.

The 27/33 and 15/18 numbers are overfit development projections because every rule was authored after
the case bytes were opened. They predict grammar coverage on those bytes, not fresh blind recall.

### 11.2 Rolling bar

For the next sealed envelope and every later code-lane envelope, freeze 6 positives and 6 negatives
unless a separately accepted protocol changes the case count. At scoring time:

1. replay the frozen development closure over the **18 most recent adjudicated blind-positive case
   bytes** by envelope chronology; prior envelopes remain byte-frozen even though their labels are now
   known;
2. require at least 9/18 evaluation candidates (running recall at least 50%);
3. replay the same closure over the **36 most recent blind case bytes** and require exactly zero
   candidates on every adjudicated negative among them;
4. require each individual envelope in that 36-case window to have zero false accusations; one
   negative candidate is a hard stop regardless of aggregate recall;
5. require zero production Findings because the development lane cannot promote;
6. require replay equality for every scored case; and
7. record, for each envelope, the count of family-C negatives, their IDs, and the first guard that
   stopped each. A family-C candidate is a hard stop.

The rolling-window replay of previously opened bytes is development regression evidence, not renewed
blind first contact. Fresh-envelope recall must still be reported separately.

## 12. Build algorithm

Implement guard infrastructure before operand widening:

1. parse/prose-strip the selected source and run existing project/source limits;
2. resolve imports, module constants, accepted readers, and closed group/header/path literals;
3. run the full-scope syntactic registered-test census S4, without operand or sink filtering;
4. census full-scope S1 calls;
5. build the member-sensitive full-scope resampling graph and census S2;
6. census full-scope S3 calls;
7. build the full-scope unit-keyed result/output graph and census S5;
8. construct value-level backward slices only when the syntactic census contains exactly one
   registered test;
9. apply on-slice mutation, P3 reducers, and unknown-slice refusals;
10. prove P2's two exact raw-row operand identities and both complete selected-group row lineages;
11. prove the candidate p-result's reachable base-section-5.7 output sink;
12. apply P1/P4 facts and construct the existing development observation/candidate projection; and
13. lock the 3.0 development identity and replay projection with production promotion forbidden.

Steps 3-7 may be computed before P1 for testability, but outward reason precedence remains P1, P4,
S1, S2, S3, S4, mutation, P3, S5, P2-row-completeness, P2-unresolved, and output sink. No off-path
admission walk runs after operand proof.

## 13. Test plan

### 13.1 Guard-first safety matrix

1. One test per exact S1 API entry, constructor, `from_formula`, rooted method chain, each of
   `group_data=`, `groups=`, `re_formula=`, and `cluster=` on a fitted-constructor chain, and exact
   statsmodels `.fit(cov_type="cluster")`. An unrelated object merely named `mixedlm` is a near miss;
   an unrelated fitted constructor carrying one of the four grouping keywords conservatively fires.
2. Reproduce all ten family-C controls. Every section-8 case must stop on its projected S1/S2 reason,
   not a shape code. Pin the exact registered-draw shapes from `19824e3f...` and `2f0d38f...` and the
   helper-default/container shape from `b12c6fd...` as separate guard-first regressions.
3. S2 tests for literal/constant/helper-default `range`, `range(len(CSV_DERIVED))`, combinations,
   permutations, vectorized NumPy draws, plain dict/list members, subscript stores, helper/member
   edges, every condition-3 reducer/count-ratio form, sorted-index reductions, and output sinks.
   Cardinality 9 is a near miss; 10, `C(6,3)=20`, and a 49-trip bootstrap fire. For tuple draw sizes,
   pin resolved/resolved, resolved/unresolved, and all-unresolved factor cases.
4. Put the bootstrap after its consumers and split trip count, data member, reducer, and sink across
   different X4 helpers; S2 must retain precedence.
5. One S3 test per closed prefix, including `gpboost` and `merf` and an uncalled helper. Exact same-test `sem` and `t.ppf`
   exemptions pass; `pearsonr`, unrelated `t.ppf`, dynamic attribute, and a statistic returned through
   a container abstain.
6. Verify S4 with registered calls at top level, in uncalled/dead helpers, nested in containers, and
   with one aggregated or otherwise unresolvable operand. Two syntactic resolved calls abstain before
   operand resolution; S1/S2/S3 outrank the outward reason.
7. Verify all four S5 construction shapes, each with direct and arithmetic output reach, plus no-sink,
   global-`nunique`, and exception-only near misses. Pin the hand-written unit-means/Welch arithmetic
   using `math.erf` beside a raw test below the S2 threshold; it must abstain S5. Pin the five projected
   positive recall losses named in section 0.3.

### 13.2 Operand matrix

1. One positive and one near-miss for every P2.1 edge.
2. Accept direct, named-mask, exact complete-group query, `.loc`, `.to_numpy`, `.astype`, exact
   one-argument `numpy.log/log1p/sqrt/exp`, `.sort_values`, `.reset_index`, literal dict/list, X4
   return, and loop-member operands. Pin `.dropna()` before or after group selection as
   `selected-group-row-completeness-unproven` until a bounded CSV nonmissing proof exists.
3. Require both group literals to byte-equal the exact two-value domain, both `V` headers to match,
   both slices to terminate at one reader, both complete selected-group row sets to be preserved, and
   a repeated authorized-unit value in each operand. Test a tautological extra mask as accepted and a
   row-dropping or statically unknown extra mask as refused.
4. `.iloc` and any additional closed/unknown filter that cannot prove the complete group row set
   abstain `selected-group-row-completeness-unproven`. `head`, `tail`, `nth`, `sample`,
   `cumcount==0`, and unit `drop_duplicates` take the earlier P3 reason. Unknown call, dynamic key,
   dynamic query, unresolved alias/helper, merge/join without the authorized unit in both key lists,
   non-one-to-one merge, and unsupported non-unit `drop_duplicates` abstain
   `unresolved-call-on-operand-slice`.
5. One adversarial test for every P3 reducer, including projected/chained GroupBy forms, transforms,
   pivot/resample, reduced merge input, NumPy reduction, unit `drop_duplicates`, and row-collapsing
   loops/comprehensions.
6. Mutation on either slice abstains; the same mutation on a frame/member that cannot reach either
   slice is admitted. G7's exact auxiliary same-column conversion stays pinned.
7. A second reader in top level, an uncalled helper, another analysis surface, or `parse_dates` form
   abstains P4.
8. Require an exact p-result-eligible output sink. Statistic-only output, unused result, uncalled
   helper, statically dead branch, and post-return call abstain `test-result-output-sink-unavailable`;
   an exact p-result sink in a nonconstant possibly reachable branch is accepted.

### 13.3 Off-path and prose invariance

1. Surround a fixed candidate with arbitrary off-path `if/for/while/try/with/raise`, lambdas,
   formatting, plotting, custom calls, validation, file writes, and helpers. The observation bytes
   remain identical unless P4 or S1-S5 is introduced.
2. Extend the no-prose tripwire through import/API census, resampling graph, value-slice construction,
   member propagation, row-lineage proof, sink reachability, S5 propagation, reducer classification,
   observation construction, and detector comparison.
3. Mutate comments, docstrings, unrelated string literals, printed labels, and every Markdown/report
   byte; add/remove reports entirely. Observations remain byte-identical.
4. A prose-only claim of mixed modelling or bootstrap does not suppress. A code-only S1/S2 shape does.

### 13.4 Corpus, lane, and gates

1. Run all 68 opened scripts through the normal audit path with the explicit development lane and
   exact section-10 expectations: 27/33 positives, 0/35 negatives, zero Findings, replay 68/68.
2. Run the six K locks: 0/6 candidates and zero Findings.
3. Run all four Envelope-5 qualified candidates through the ordinary CLI without the development
   flag: exactly one qualified 2.1.0 Finding each, byte-identical wording-v1 behavior and replay.
4. Assert 2.1 qualified adapter/detector/profile bytes and installed pin match their frozen digests;
   a 3.0 development bump cannot alter them.
5. Run the existing 108 blind and 155 regression corpora with zero production Findings and exact
   replay.
6. Run the false-accusation halt, full default gate, Ruff lint/format, mypy, and starter validation.
7. Retire no test. Any expected-reason change must be named in BUILD-NOTES by case and causal rule.

## 14. File-by-file build delta

| File | Planned change | Rough size |
|---|---|---:|
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py` | Replace R1 whole-script admission with value-level operand slicing; implement P2/P3, S1-S5, repeated-row lineage, sink reachability, member/container and guard precedence. | +1,600/-1,000 |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py` | Advance development adapter/check/grammar identity to 3.0.0; preserve contract/CSV and wording-v2 projection. | +25/-15 |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v3_0.py` | New development detector identity over the unchanged bounded comparison shape. | +70 |
| `src/sc_referee/detectors/method_conflict_registry.py` | Register exact 3.0 development detector dispatch only. | +8 |
| `src/sc_referee/scientific_checks/profiles.py` | Advance only the development dependence module/binding from 2.3.0 to 3.0.0. | +20/-15 |
| `src/sc_referee/scientific_checks/integration.py` | Admit exact 3.0 static-file subject identity; no qualified-lane change. | +3/-1 |
| `src/sc_referee/resources/scientific-check-manifests-v1/registry.json` and detector manifest resources | Regenerate dual registry with qualified 2.1 unchanged and development 3.0 added; retain all historical detector manifests. | generated |
| `evaluation/development/pseudorep-code-slice-v3_0/DEVELOPMENT_LEDGER.json` | Record all 68 + K expectations, family labels/counts, zero-Finding and replay requirements. | +1 generated record |
| `tests/test_code_csv_dependence_dataflow.py` | P2/P3 and S1-S5 positive/near-miss/adversarial matrix. | +1,900 |
| `tests/test_dependence_code_slice_development.py` | 68-case/K expected table, first reasons, replay, family-C census. | +250/-80 |
| `tests/test_code_csv_dependence_dual_registry.py` | Freeze qualified 2.1 behavior across development 3.0 bump. | +50 |
| prose tripwire and report-mutation tests | Instrument every new slice/guard entry point and preserve byte-identical observations. | +250 |
| ADR-0076 and this design BUILD-NOTES | Record accepted 3.0 eligibility semantics and any narrow implementation resolution. | +40 |

No contract schema, accepted public schema, production pin, wording-v1/v2 bytes, qualification record,
or qualified registry binding changes in this slice.

## 15. Review disposition

The maintainer review closes the two prior predicate blockers in the conservative direction: P2.2 now
requires complete repeated-unit lineage in both actual operands, and P5 restores the p-result output
sink plus reachable-call requirement. It also lowers S2 to 10, closes registered-draw factor and
count-ratio shapes, adds the S1/S3 model surface, makes S4 syntactic, and adds S5 with its five observed
positive recall losses.

No choice remains open in this draft. It is still **not build authorization** until Fable completes the
requested re-check and explicitly clears implementation.

## BUILD-NOTES — 2026-08-23

Build authorization: **Fable, under executive authority granted by Alex 2026-08-21**, after the
guard/operand re-check confirmed the projected 27/33 positives and 0/35 negatives.

- The implementation is isolated in versioned `*_v3_0.py` adapter/dataflow/detector files. The
  qualified 2.1 binding and every 2.x implementation byte remain unchanged; the unqualified
  development registry alone advances to 3.0.0. This is narrower than the file table's proposed
  in-place edits and preserves the reviewed dual-lane invariant.
- P2.2 reparses the authorized CSV bytes only inside the existing strict UTF-8, header, 512-column,
  2-to-100,000-data-row, and 1-MiB-field limits. Any parse, width, field, or row-bound failure abstains
  `selected-group-row-completeness-unproven`; no new CSV budget was introduced.
- Full-scope accepted-reader census runs before outward S1-S5 reasons, as required by P4 precedence.
  Full-scope S1/S3/S4 censuses run before helper expansion can return a shape refusal, so an uncalled
  or syntactically unsupported helper cannot hide a registered inference sibling.
- X4 output reach admits one exact expression-only formatter helper: one positional parameter, no
  defaults/variadics/decorators, exactly one final return, no calls/attributes/subscripts, and a pure
  constant/operator expression whose only loaded name is that parameter. This closes the reviewed
  `format_p(test["p"])` sink without admitting an unknown output helper. `SystemExit` joins the already
  closed exception-constructor set so an exact validation raise inside a reader helper cannot become
  an operand admission wall.
- The Envelope-7 helper-pseudobulk negative `d85857381a84b3110b9a` stops earlier than the design table:
  its `read_csv(..., dtype=...)` call is outside the unchanged accepted-reader registry, so the narrow
  implementation returns `authorized-reader-lineage-unavailable` rather than widening P4 to reach the
  later aggregate operand. Its expected candidate count remains zero.
- No test was retired. The active development ledger contains all 68 opened cases, all six K controls,
  the 10-member family-C census, exact first reasons, zero-Finding ceilings, and replay requirements.
- Documented future limit only: `34b1ade6d028cfda2a75`, `71939b3441556e9e02b6`, and
  `367e084ddc8f997786f1` are positive recall losses because S5 sees per-authorized-unit row-count
  outputs. A future print-only count carve-out could study those three, but 3.0 implements no carve-out.
- Post-build safety correction, directed by Fable's 2026-08-23 audit: row completeness is monotone.
  The authorized reader begins complete, every selection/identity edge inherits its parent's value,
  and `.iloc`, `.dropna`, or any unresolved row-count edge lowers it permanently. Both the operand
  flag and the bounded CSV repeated-unit proof must hold. Exact last-row-per-unit, pre-selection
  `.dropna`, and post-selection `.dropna` fixtures abstain
  `selected-group-row-completeness-unproven`.
- S2 now evaluates the full module with full-scope sinks and assignments, closed helper defaults and
  actual arguments, same-name random-generator bindings, and helper actual/formal/return edges. S1,
  S2, S3, and S4 are all computed before their fixed precedence is applied; S2 therefore outranks S3
  independently of source position. The called-helper bootstrap regression fires S2.
- The unreachable 2.x R1 entry points and their private read-only/admission helper block were removed
  from the versioned 3.0 closure. The prose tripwire now also instruments operand row-lineage proof,
  call/sink reachability, reducer classification, and detector comparison.
- Documented implementation limits: a literal `.rename` that changes the tracked value-column name
  and the design's one-to-one merge/join operand edge are not implemented in 3.0. Both abstain rather
  than preserving operand lineage. No `.dropna` nonmissing carve-out is implemented.
- Post-verification S2/S5 correction, directed by Fable's 2026-08-23 re-audit: the shared guard sink
  closure follows a reducer or unit-keyed summary through X4 helper returns, caller actual/formal
  bindings, two helper levels, destructuring, and exact literal tuple/list/dict member edges. A
  returned container taints only the member that carries the guarded value; printing a disjoint
  literal member does not satisfy output reachability. Regressions pin direct return-then-print,
  frame-parameter return, two-deep tuple return, and a returned per-unit-summary dict.
