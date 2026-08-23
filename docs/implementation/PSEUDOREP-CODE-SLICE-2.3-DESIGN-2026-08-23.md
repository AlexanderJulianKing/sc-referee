# Pseudoreplication code slice 2.3 design — 2026-08-23

- **Status:** Accepted for build with reviewed edits
- **Decision provenance:** Fable, under executive authority granted by Alex 2026-08-21
- **Decision date:** 2026-08-22
- **Normative base:**
  `docs/implementation/PSEUDOREP-CODE-SLICE-2.2-DESIGN-2026-08-22.md`
- **Governing ADR:**
  `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md`
- **Proposed identity:** check, adapter, grammar, and separate code-lane detector `2.3.0`
- **Evidence:** frozen contract, CSV structure, Python AST/dataflow, and established API names only
- **Prose evidence:** forbidden
- **Project-authored-code execution:** forbidden

## 0. Observed result, inference boundary, and overfit warning

### 0.0 BUILD-NOTES

- The code-lane Finding wording is versioned. The existing v1 profile id, constants, summary,
  non-inferences, slot schema, and digest are byte-frozen for the installed qualified `2.1.0`
  lane. G2 creates a separate `-v2` profile used only by detector/check lane `2.3.0`; it does
  not mutate `_CODE_DEPENDENCE_NON_INFERENCES` or
  `CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST`.
- G1 subscript stores, helper-return members, destructuring positions, inlined-parameter
  bindings, and step-19 precedence are explicit graph requirements, not implementation
  discretion. The build also follows guard-only aliases from the reducer's immediate target
  through inlined helper parameters and returns before testing sink reachability; without that
  final closure, the required four-helper matrix case stopped at
  `unsupported-expression-on-path` instead of the resampling guard.
- G6 reader shape is censused report-wide/on every code path before authorized-reader lineage
  ranking. An off-path `read_csv(..., parse_dates=...)` is an accepted second reader and cannot
  be hidden by its path position.
- Normal-path replay preserved every section-11 candidate/negative classification but exposed
  three stale narrative first reasons: `19824e...` stops at the unchanged 16-definition ceiling,
  `23cc44...` at the unchanged multiple-candidate guard, and `be94ce...` at the strengthened G1
  resampling guard. These are expected-outcome corrections, not new admissions.
- The 155-case regression ledger and four-case execution plan receive an expected-identity refresh:
  only the active dependence component version/manifest digest, ledger digest, and plan digest
  change from 2.2 to 2.3. Case selectors, expected applicability, assessment ceilings, and expected
  zero-Finding projections do not change.
- Ambiguity resolves to abstention and is logged here during the build; never toward conviction.

### 0.1 Observed Envelope 6 result

Envelope 6 is opened and burned. Its frozen detector `2.2.0` result is **0/6 positive
candidates, 0/6 negative candidates, zero Findings, replay 12/12, closure 94/94, and
blind-label/role agreement 12/12**. Project lifetime after scoring is **170 blind cases,
zero false accusations, and seven blind catches**. The frozen result is recorded in
`evaluation/development/blind-envelope-6-2026-08-22/CUSTODY_LOG.md:180-181` and the
case-level observations in
`evaluation/development/blind-envelope-6-2026-08-22/AUDIT_RESULTS.json`.

The retrospective `2.2.0` replay over the 56 opened code-lane cases from Envelopes 2-6 is
**18/27 positive candidates and 0/29 negative candidates**. Envelope 1 is not part of that
56-case count.

### 0.2 Observed blockers and inferred effect

The following statements distinguish observed bytes from proposed behavior:

- **Observed:** Envelope-6 negative `b12c6fd59e338b7b156e` implements a hand-rolled cluster
  bootstrap. `N_RESAMPLES = 10000` is defined at `analysis.py:26`, is bound as the helper
  default at line 67, controls `range(n_resamples)` at line 97, and resamples arrays stored
  in the plain `blocks` dictionary at lines 85-102. Its percentile result reaches output at
  lines 194-207. The existing resampling guard does not connect the default or container
  members, and the case currently stops on a shape-level
  `unregistered-component-consumer`.
- **Observed:** positive `03ee21366b62d03a9b26` has 14 repeated does, 6-9 kit rows per doe,
  and `kit_number` values bounded by the maximum multiplicity. Positive
  `5b1e03e13ef7e2e727dc` has 18 repeated infants, 4-5 visits per infant, and `age_weeks`
  values bounded by the maximum multiplicity. The old byte-identical-tuple D1' rule calls
  both columns unique non-index columns and stops at the CSV gate.
- **Observed:** the remaining benign shapes are `.to_numpy` vector materialization, a
  two-member dictionary comprehension over the contract group domain, a closed module
  list, `read_csv(parse_dates=[...])`, and exact same-column date/type conversion. Positive
  `9d44076b46746ce05758` also calls `stats.pearsonr` on tracked rows at `analysis.py:91`;
  that call is an unchanged real guard, not a benign shape.
- **Inferred from a source-byte trace, not a qualification result:** G1-G7 yield
  **19/27 positive candidates and 0/29 negative candidates** on the 56 opened cases. Only
  `92c016654c6c93979fff` completes a newly admitted positive path. The two D1 changes remove
  a CSV gate but meet later unchanged code walls. No opened case earns blind credit.

### 0.3 Overfit caveat

Every G rule below was authored after inspecting opened misses. Blind first-contact positive
candidate counts across the five code-lane envelopes were **0, 1, 2, 4, 0**. The projected
19/27 retrospective recall is development coverage, not evidence that `2.3.0` will generalize.
Qualification requires a fresh frozen envelope; this document does not create one.

## 1. Boundary and unchanged rules

This is a delta. Every 2.2 rule not explicitly replaced below remains normative, including:

1. contract profile `1.1.0` and byte-exact authorized CSV path, unit header, group header,
   and exact two-value group domain;
2. root `analysis.py` naming-convention admission and alternate-analysis scan;
3. one accepted authorized reader and no additional accepted reader anywhere in scope;
4. the closed selection, `ttest_ind`, p-result sink, and operand-path grammar;
5. the full-program aggregation, tracked-mutation, dependence-aware, registered-test,
   multiple-candidate, resampling, and unregistered-component-consumer guards;
6. the directional R1/R2 graph, member-sensitive edges, helper-inlining bounds, loop
   normalization, reconstruction rules, and 16-definition ceilings;
7. E6 project-file refusals, replay projection, zero-false-accusation standard, and
   abstention on ambiguity; and
8. the permanent prohibition on report text, Markdown, comments, docstrings, printed prose,
   or any other prose as evidence, admission, suppression, or corroboration.

In particular, **`unregistered-component-consumer` is not relaxed**. G1 strengthens an
inference-sibling guard before any printing idiom can be considered. G2 changes a CSV
classification and adds a non-inference. G3-G7 admit only closed structural forms while all
unchanged whole-program guards still run on the complete expanded graph.

## 2. G1 — resampling guard reachability

### 2.1 Purpose and precedence

G1 is implemented and tested before G2-G7 may be used to widen an admitted descriptive
shape. The resampling census remains a whole-program R2 sibling guard at predicate step 19,
before R1 admission. It scans the fully expanded program and must emit
`resampling-inference-sibling-present` even if some node in the same resampling/output path
would otherwise emit `admission-call-off-list` or `unregistered-component-consumer` later.

G1 adds no candidate evidence. It can only convert an existing shape abstention into the
stronger safety abstention `resampling-inference-sibling-present`.

### 2.2 Closed trip-count resolver

For one `for` loop or comprehension, resolve a static trip count only through these forms:

1. an integer literal `N`, excluding `bool`;
2. a simple module constant `NAME = N`, with exactly one definition and no later store or
   deletion;
3. `range(N)` where `N` resolves by row 1, row 2, or row 4;
4. a helper parameter whose effective binding resolves to row 1 or row 2, including an
   omitted parameter bound to an X4/X4a literal or closed-module-constant default; or
5. an inlined fresh name that is the alpha-renamed image of row 4.

The argument-to-parameter map is the existing X4 1:1 binding. Positional or keyword override
dominates a default. If the effective argument, default, module name, or range argument is
ambiguous, non-integer, boolean, reassigned, arithmetic, attribute-derived, subscript-derived,
or otherwise outside rows 1-5, the trip count is unresolved. G1 does not evaluate Python.

A resolved count is inferential when it is **at least 50**. Existing numpy/random `size`
forms remain recognized at the same threshold. The threshold comparison is on the exact
resolved integer.

### 2.3 Guard-only tracked-container graph

Build a separate `resampling_container_graph` after helper inlining and before the sibling
census. It is used only by G1 and never promotes a value into the reader-selection-test
candidate path.

1. A plain `dict`, `list`, or `tuple` member is `resampling_tracked` when its value is a
   tracked selection, the reader component, a reader-derived array, or another
   `resampling_tracked` member.
2. Exact literal-key dict stores, integer-index list/tuple members, list/dict/set
   comprehensions, and `append` into a uniquely bound plain list create member edges. The
   construction must already be visible to the AST graph; G1 does not admit the construct
   for any other purpose.
3. A repeated body's subscript store `ARRAY[INDEX] = VALUE` defines the base `ARRAY` for the
   guard's repeated-output set. This guard-specific store collector follows a simple-name
   base through nested subscripts; a dynamic/attribute base is conservatively unresolved and
   cannot be used to complete G1.
4. Reading one known member follows that edge. Iterating the container, a `.values()` view,
   a `.items()` view, concatenating its members, or selecting a member through a loop target
   counts as consuming tracked data if any reachable member is `resampling_tracked`.
5. A dynamic key, alias escape, unknown mutation, whole-container call, unsupported
   comprehension, or unresolved member follows the conservative union of all members for
   this guard. It does not become an R2 operand; any existing structural refusal remains.
6. Member sensitivity is preserved: an unrelated literal-only member does not by itself
   taint a known literal-key read.

### 2.3a Derived-value closure

The guard's derived-value closure is not limited to simple-name assignments. It follows,
without executing source:

1. R3 literal-key and literal-position container member edges, including helper-return dict,
   tuple, and list members;
2. matching positions in tuple/list destructuring assignments;
3. X4/X4a/X5 synthesized helper-return assignments;
4. actual-to-formal and formal-to-alpha-renamed inlined-parameter bindings; and
5. the guard-specific subscript-store base definition in section 2.3(3).

An unknown member or destructuring shape cannot complete G1, but every unchanged unknown-call
or unregistered-consumer abstention remains available. A required regression places the trip
count, tracked container, reducer, and output sink in four different eligible helpers; the
fully inlined/member-sensitive graph must still emit
`resampling-inference-sibling-present`.

### 2.4 Exact resampling-sibling predicate

Emit `resampling-inference-sibling-present` when all checks hold:

1. a loop, comprehension, or registered numpy/random draw has a resolved trip count or size
   at least 50 under section 2.2 and the unchanged registered draw rules;
2. its body consumes the reader component, a tracked selection, a reader-derived array, or a
   `resampling_tracked` container/member under section 2.3;
3. a value defined or mutated by the repeated body reaches `mean`, `std`, `nanmean`,
   `nanstd`, `median`, `nanmedian`, `quantile`, `nanquantile`, `percentile`, or
   `nanpercentile` under the existing exact reducer resolution; and
4. that reducer result reaches an accepted p/result output sink under the shared sink table.

The body may live in an inlined helper. The trip-count definition, data container, reducer,
and sink may span distinct eligible helpers as long as the member-sensitive graph connects
them. Predicate-step order dominates earliest source position. Within predicate step 19,
`resampling-inference-sibling-present` has unconditional priority over
`unregistered-component-consumer`, regardless of either node's physical source position.

### 2.5 Required `b12c6fd59e338b7b156e` trace

The regression fixture copies the exact code shape at
`evaluation/development/blind-envelope-6-2026-08-22/cases/b12c6fd59e338b7b156e/project/analysis.py`:

- module constant `N_RESAMPLES = 10000` at line 26;
- default `n_resamples=N_RESAMPLES` at line 67;
- group selections materialized into `blocks` at lines 85-91;
- `range(n_resamples)` at line 97;
- resampled concatenations through `blocks[...]` at lines 101-102; and
- percentile output at lines 194-207.

It must abstain **first** as `resampling-inference-sibling-present`, even when
`to_string(float_format=lambda ...)`, `.map`, and the other printing forms at lines 160-172
are independently treated as admitted R1 output shapes. A regression that produces a
candidate or stops only on a printing shape fails G1.

## 3. G2 — replace the D1' within-unit-index rule

### 3.1 Unchanged CSV preconditions and notation

The contract/CSV checks before D1 remain unchanged. Let:

- `N` be the CSV data-row count;
- `U` be the number of distinct nonempty byte values in the authorized unit column;
- `R` be the number of authorized-unit values occurring in at least two rows;
- `M` be the maximum row multiplicity of one authorized-unit value; and
- `distinct(C)` be the number of distinct byte values in another CSV column `C`.

The adapter still requires `N > U`, group constancy within the declared unit column, and
every other existing CSV row/field/header/domain limit.

Candidate columns remain restricted before the uniqueness test: `C` is neither the
authorized unit column nor the contract group column, and `distinct(C) <= U`.

### 3.2 Replacement definition

For each candidate `C`, compute whether every `(unit_value, C_value)` pair is unique across
all rows. `C` is a `within_unit_index` **if and only if all three checks hold**:

1. every `(unit_value, C_value)` pair is unique;
2. `distinct(C) <= M`; and
3. every declared unit repeats, expressed exactly as `R == U`.

Abstain `unique-nonindex-composite-key-possible` if some candidate `C` has unique
`(unit_value, C_value)` pairs and is not a `within_unit_index` under checks 1-3. Candidate
columns without unique pairs are neither an index nor a composite-key suppressor.

The prior requirement that sorted tuples of `C` values be byte-identical for every unit is
deleted. Empty fields remain ordinary byte values for the existing CSV parser; no imputation,
date parsing, numeric coercion, ordering inference, or semantic name inference is added.

### 3.3 Verified 62-envelope differential

A static CSV-only differential over all 62 opened envelope cases changes exactly two D1
outcomes:

| Case | Column | `U` / `R` / `M` | `distinct(C)` | Pair unique | Old D1' | G2 |
| --- | --- | --- | ---: | --- | --- | --- |
| `03ee21366b62d03a9b26` | `kit_number` | 14 / 14 / 9 | 9 | yes | unique non-index; abstain | within-unit index; continue |
| `5b1e03e13ef7e2e727dc` | `age_weeks` | 18 / 18 / 5 | 5 | yes | unique non-index; abstain | within-unit index; continue |

Every other CSV gate outcome is unchanged. This is a development verification against opened
bytes, not blind evidence.

The closed label-collision control remains an abstention. With rows `(A, north)`,
`(A, south)`, `(B, north)` for unit and `site`, `U=2`, `R=1`, `M=2`, and
`distinct(site)=2`. Unit/site pairs are unique but `R != U`, so `site` is not an index and
the adapter emits `unique-nonindex-composite-key-possible`.

### 3.4 Declared residual and Finding non-inference

G2 has a known zero-FA coverage residual: when every declared unit repeats, the `(unit, C)`
pairs are unique, `distinct(C) <= M`, but value sets differ or nest across units, G2 treats
`C` as an index. For example, units with `C` sets `{1, 2}` and `{1, 2, 3}` satisfy the new
rule even though `C` could be a composite-key component. This residual is accepted as a
coverage limit; G2 does not prove that the declared unit header is the complete scientific
unit.

Add this exact bounded sentence only to the versioned v2 code-lane Finding non-inferences:

> The declared unit column may be one component of a composite key.

It appears in the v2 fixed non-inference list, not in the title or evidence slots. The v1
profile remains byte-identical. The Finding remains a frozen-contract-versus-code conflict and
does not assert statistical invalidity or that the contract author selected the correct
scientific unit.

## 4. G3 — selection-preserving `.to_numpy`

### 4.1 Exact operand-path forms

Treat `.to_numpy` as a transparent identity edge only when its receiver is an already
recognized, nonaggregated selection/identity value from the single authorized reader and its
entire call matches one of these forms:

1. `SELECTION.to_numpy()`;
2. `SELECTION.to_numpy(dtype=DTYPE)`; or
3. `SELECTION.to_numpy(DTYPE)`.

`DTYPE` is exactly one of:

- an unshadowed builtin name `bool`, `float`, `int`, or `str`;
- a string literal of at most 64 bytes with no NUL; or
- one closed module string constant with the same byte limit.

Rows 2 and 3 are mutually exclusive. No star argument, `**` keyword, second positional
argument, extra keyword, call-valued dtype, attribute dtype, or nested `.to_numpy` is
accepted. A whole reader frame, grouped value, aggregate, unknown value, or value already
carrying an operand-provenance refusal is not a selection and is not repaired by this rule.

The derived value preserves reader identity, selected group literal, selected value header,
selection kind, origins, and every aggregation/mutation/consumer label. The `.to_numpy` call
adds one definition/member edge but no new scientific evidence role.

### 4.2 R1 form

The same three call shapes are read-only in R1 descriptive positions. The result remains a
derived value under the directional graph. Existing `out`, `copy`, `na_value`, positional
order, unsupported dtype, and protected-path checks remain abstentions.

## 5. G4 — dictionary comprehension reconstruction

### 5.1 Exact comprehension

Extend 2.2 section 5 only for this assignment shape:

`CONTAINER = {LEVEL: VALUE for LEVEL in ITERABLE}`

It is reconstructable only if:

1. the outer node is one `Assign` or `AnnAssign` to one simple `Name`;
2. the `DictComp` has exactly one synchronous generator, no `if` clauses, and no additional
   generator;
3. the target is one `Name` and the key is exactly a load of that target;
4. `ITERABLE` is a literal list/tuple or G5 closed module list/tuple whose resolved sequence
   contains exactly the two distinct contract group-domain strings, in either order;
5. the target does not collide with a tracked/import/helper/builtin/module-constant name;
6. `CONTAINER` has one definition, no alias or whole-container escape, no mutation other than
   its synthetic two-member construction, and only literal contract-key reads afterward; and
7. after per-binding substitution, each `VALUE` is a tracked selection/identity, an eligible
   X4 helper call whose complete body can be expanded, or an R1 descriptive value. Unknown,
   dynamic, second-reader, test-result, conditional, lambda, or unsupported-call values
   abstain under their existing narrowest code.

### 5.2 Deterministic normalization and member edges

Before helper expansion and every R2 scan:

1. resolve the two iterable strings and create two copies in iterable order;
2. substitute each load of `LEVEL` in the corresponding `VALUE` and key with that exact
   string literal;
3. alpha-rename every ordinary name introduced by the copied expression with the same
   source-line/binding-ordinal scheme as 2.2 contract-domain loops;
4. create one `reconstruction_container` member edge for each literal key and retain the
   complete member `_Value` labels; and
5. run the unchanged X4 expansion over an eligible helper call in each synthesized member
   assignment. Propagate the reconstruction marker and literal member key to the helper's
   synthesized return assignment.

Literal `CONTAINER[GROUP_VALUE]` reads follow only that member. Reading the whole container
follows the union. A selection, aggregate, tracked frame, test result, unregistered consumer,
or unknown in a member remains visible to R2 and cannot be laundered by reconstruction.

This admits both comprehensions in Envelope-6 positive `92c016654c6c93979fff`:
`wing = {level: data.loc[...] for level in LEVELS}` at `analysis.py:56`, and the print-only
`summary = {level: describe_treatment(wing[level]) for level in LEVELS}` at line 57. The
literal `wing[...]` members feed the registered test at lines 73-75; the complete expanded
descriptive helper remains visible but does not reach an operand. The case is therefore the
one projected new candidate.

## 6. G5 — closed module list and tuple constants

Extend the module resolver with `closed_sequence_constants`:

1. the definition is exactly `NAME = [ELEMENTS]` or `NAME = (ELEMENTS)` at the selected
   module scope;
2. `NAME` has exactly one definition and no later `Store`, `Del`, augmented assignment,
   subscript/attribute mutation, mutating method call, alias escape, or ambiguous may-write;
3. there are 1-16 elements and no nesting, starred element, comprehension, call, unary/binary
   operation, attribute, or subscript;
4. each element is a literal string of at most 128 bytes with no NUL, non-boolean integer,
   finite float, boolean, or `None`; and
5. the resolver stores an immutable ordered tuple plus the original list/tuple kind. It never
   executes or mutates the source value.

Closed sequences may fill only an already enumerated structural slot: a contract-domain loop
or comprehension iterable, G6 `parse_dates`, a registered literal selector, or an existing
X4 constant default/free-name binding. They are not reader/test/group evidence by themselves.
Any subsequent mutation or use in an unregistered component-consuming call retains the
existing abstention.

## 7. G6 — exact `read_csv(parse_dates=[...])` reader

Add reader API identity `pandas_read_csv_parse_dates_v1` with exactly this call shape:

`FRAME = pandas.read_csv(AUTHORIZED_PATH, parse_dates=DATE_COLUMNS)`

All conditions are required:

1. `pandas.read_csv` resolves under the existing accepted import forms;
2. there is exactly one positional argument, and the complete path expression is an existing
   accepted X1 form resolving byte-identically to the contract path;
3. `parse_dates` is the only keyword; there is no `**` keyword;
4. `DATE_COLUMNS` is an inline `ast.List` of 1-16 string literals/closed module string names,
   or one G5 closed module list containing only such strings;
5. the resolved strings are unique, each is present exactly once in the CSV header, and none
   equals the authorized unit header, group header, or either finally selected operand value
   header; and
6. the whole reader call matches this form. No `index_col`, `dtype`, `usecols`, `converters`,
   date parser, nested list, dict, tuple, callable, or second keyword is accepted.

This is reader-shaped for the complete accepted-reader census on every code path before
lineage is ranked. It is an accepted reader only when all six rows above hold, so E1 still
requires it to be the one authorized reader and abstains if any other accepted reader appears
anywhere in scope. An off-path or output-irrelevant call with this exact reader shape counts
just as a bare off-path `read_csv` does. Parsing a date adds no selection, aggregation, unit,
group, or test evidence.

Envelope-6 positive `d89ab3ef408520667cc1` clears its reader shape at `analysis.py:28` under
G6 but remains an honest miss at the later unchanged component-consuming
`groupby(...).agg(...).reindex(...)` chain at lines 49-58.

## 8. G7 — exact same-column auxiliary conversion store

### 8.1 Deferred disjointness check

One subscript store is exempted from `tracked-value-mutation` only after the candidate reader,
two group selections, and both operand value headers are known. All checks below must hold:

1. the target is exactly `FRAME[COLUMN]`, with `FRAME` the simple name bound directly to the
   single authorized reader and `COLUMN` one literal or closed module string constant;
2. `COLUMN` is present exactly once in the CSV header and differs byte-for-byte from the
   authorized unit header, contract group header, and both selected operand value headers;
3. the RHS reads exactly the same `FRAME[COLUMN]`, with no alias, second frame, different
   column, `.loc`, `.iloc`, `.at`, dynamic key, or intervening call; and
4. the complete RHS matches exactly one row in section 8.2.

If no complete candidate operands exist yet, disjointness cannot be proved and the store
remains `tracked-value-mutation`. The exemption is never used to help construct an operand.

### 8.2 Exact conversion forms

Accepted RHS forms are:

1. `pandas.to_datetime(FRAME[COLUMN]).dt.date`, where `pandas.to_datetime` is an accepted
   import-resolved API with one positional argument and no keyword, and `.dt.date` is the
   exact terminal attribute chain; or
2. `FRAME[COLUMN].astype(TYPE)`, where `TYPE` is exactly the unshadowed builtin name `str`,
   `int`, or `float`, with one positional argument and no keyword.

No assignment expression, chained conversion, timezone/localization method, errors/format
keyword, string dtype literal, callable dtype, inplace form, or second store is accepted.
The frame retains its reader root and the converted auxiliary column is a derived read-only
value. Every other subscript store remains governed by the unchanged may-write and
tracked-mutation rules.

Envelope-6 positive `278451c17389f8c72ece` clears the exact
`frame["harvest_date"] = pd.to_datetime(frame["harvest_date"]).dt.date` store at
`analysis.py:25`, but remains an honest miss because its later generator over
`frame["harvest_date"].unique()` reaches the protected reader-derived value and emits
`admission-slice-reaches-operand` under unchanged directional admission.

## 9. Ordered predicate, identity, and Finding delta

The 2.2 predicate changes in this order only:

1. select the unchanged X1 module/main scope, scan other project analysis surfaces, and run
   the prose-free instrumentation boundary;
2. resolve existing constants plus G5 closed module list/tuple constants;
3. expand eligible helpers and record effective parameter bindings/defaults for the G1
   trip-count graph;
4. normalize existing 2.2 loops/reconstructions plus G4 comprehensions, then expand eligible
   synthesized member helpers;
5. construct the complete member-sensitive value graph, including G1 guard-only container
   edges and G3 selection-preserving identity edges;
6. census the single authorized reader, including G6, and refuse any additional accepted
   reader;
7. construct the two unchanged group-selection operand backward slices and identify both
   selected value headers;
8. apply G7's deferred exact auxiliary-store exemption; count every other tracked store;
9. apply G2's replacement CSV index/composite-key classification;
10. run every unchanged aggregation, mutation, registered-test, dependence-aware,
    multiple-candidate, sibling, and unregistered-component-consumer guard on the full
    expanded graph;
11. run G1's strengthened resampling guard at existing step 19 precedence;
12. apply the unchanged directional R1 admission, exact p-result sink, definition ceilings,
    replay projection, and candidate construction; and
13. select the Finding wording profile by exact lane identity: v1 for detector `2.1.0`, v2
    only for detector `2.3.0`; if Finding-eligible under a matching installed pin, use the
    unchanged title and bounded evidence slots plus the selected profile's fixed
    non-inferences.

The check, adapter, grammar, and separate code-lane detector identities advance together to
`2.3.0`. A new versioned detector module inherits frozen `2.2.0` behavior and declares the new
identity/implementation digest. Every `1.x`, `2.0.0`, `2.1.0`, and `2.2.0` detector byte and
manifest record remains immutable. Contract schema `1.1.0` does not change.

The installed production pin remains bound to qualified detector `2.1.0`. It is stale against
active `2.3.0`, so every 2.3 candidate is evaluation-only until a fresh qualification record
and an explicitly installed replacement pin exist. This design authorizes neither action.

The exact Finding title remains:

> Analysis code contradicts the frozen one-row-per-authorized-unit requirement

Its bounded slots remain contract path/header bytes, registered API identity, and integers.
No source string literal, comment, docstring, printed label, report byte, or inferred scientific
claim enters the Finding.

### 9.1 Versioned Finding profiles

The build must preserve these v1 public constants and bytes:

- `CODE_CSV_DEPENDENCE_FINDING_PROFILE_ID =
  "method-conflict-finding:code-csv-authorized-unit-requirement-conflict-v1"`; and
- `CODE_CSV_DEPENDENCE_FINDING_PROFILE_DIGEST =
  "sha256:0440fdb918eb04ff975e7129c4152a2d681f3f4203ae8c7a1f8fc9ebf8916288"`.

Create separate constants:

- `CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_ID =
  "method-conflict-finding:code-csv-authorized-unit-requirement-conflict-v2"`; and
- `CODE_CSV_DEPENDENCE_FINDING_PROFILE_V2_DIGEST`, computed from the v2 profile containing the
  exact additional composite-key non-inference sentence.

The title, slot schema, issue class, severity rationale, and next action are unchanged between
v1 and v2. The v2 summary appends the same composite-key limitation in bounded wording; it
does not interpolate a new slot. `draft_method_conflict_finding` selects v1 only when
`binding.detector_version == "2.1.0"` and v2 only when
`binding.detector_version == "2.3.0"`; any other code-lane version is outside this new
wording selection and abstains from drafting rather than falling forward.

Controller profile validation likewise compares the installed pin and produced draft against
the exact profile selected by the binding's detector version. The installed 2.1 pin therefore
continues to validate against v1 even while the live unqualified 2.3 lane uses v2. A mandatory
compatibility test pins the v1 digest above and runs the four qualified Envelope-5 candidates
through a frozen 2.1 audit lane, requiring exactly one v1 Finding for each after the 2.3 build.

## 10. False-accusation analysis

| Rule | Required adversarial scenario | Required outcome and reason |
| --- | --- | --- |
| G1 | The exact `b12c6fd59e338b7b156e` bootstrap, including helper-default trip count, plain dict blocks, and all printing idioms admitted. | Abstain `resampling-inference-sibling-present`; shape admission cannot expose the raw test without the inference sibling. |
| G1 | A module/default count of 49 with the same graph. | G1 does not fire; another existing guard must decide. The threshold is exact and is not rounded. |
| G1 | A 50-trip loop over a literal-only container unrelated to the reader. | G1 does not fire because no tracked/reader-derived member is consumed. |
| G2 | Reused unit labels separated by a `site` column where one unit does not repeat. | Abstain `unique-nonindex-composite-key-possible`; `R != U`. |
| G2 | Every unit repeats but candidate value sets nest. | Declared coverage limit; the code-lane Finding carries the composite-key non-inference sentence. |
| G3 | `.to_numpy(dtype=float)` follows `groupby().mean()` and feeds a test. | Abstain `aggregation-on-test-operand-path`; identity preserves the aggregation label. |
| G3 | Whole-frame `.to_numpy()` or `.to_numpy(float, copy=True)` feeds a test. | Abstain under unchanged operand provenance / structural code; neither matches G3. |
| G4 | One comprehension member is a raw selection and the other is an aggregate. | Abstain `aggregation-on-test-operand-path`; members remain separate and complete. |
| G4 | A key is dynamic, iterable includes a non-domain value, or the whole dict escapes. | Abstain under the closed reconstruction or unregistered-consumer rule; no partial reconstruction. |
| G5 | A module list is appended to, subscript-mutated, aliased to an unknown call, or has 17 elements. | Abstain; it is not a closed sequence constant. |
| G6 | `read_csv` adds any keyword besides exact `parse_dates`, names a unit/group/value column, or a second accepted reader exists. | Abstain under reader-shape or additional-reader guard. |
| G6 | An off-path exact `read_csv(..., parse_dates=[...])` appears beside the authorized reader. | Abstain `additional-accepted-reader-present`; reader census is path-insensitive. |
| G7 | Conversion targets the unit, group, either operand value column, another frame/column, or uses `errors=`/`format=`/`inplace`. | Abstain `tracked-value-mutation`; G7 cannot change an operand or authority-bearing column. |
| unchanged | A tracked-row `stats.pearsonr`, off-registry mixed model, cluster bootstrap, or any other unresolved component consumer remains. | Abstain `unregistered-component-consumer` or the stronger registered sibling guard. |

The accepted residual in G2 is disclosed rather than converted into a scientific conclusion.
The Finding still says only that code contradicts the frozen contract. It does not claim that
rows are statistically invalid, that the declared unit is complete, or that the executed
project produced the output.

## 11. Development check — 56 opened cases

“Candidate” means the code-lane observation completes under the proposed `2.3.0` predicate.
Because no `2.3.0` qualification or production pin exists, all candidates remain
evaluation-only. First reasons follow the ordered predicate in section 9.

### 11.1 Envelope 2 — 3/3 positives, 0/5 negatives

| Role / case | Expected 2.3 outcome | First reason or path |
| --- | --- | --- |
| P1 `e8f97fe750189052f726` | Candidate | Complete path. |
| P2 `2df3396d80adbb63dffb` | Candidate | Complete path. |
| P3 `ca18f96d45dff1b921ad` | Candidate | Complete path. |
| N1 `15b07ef7670800ba88e0` | Abstain | `two-group-row-selection-unavailable`. |
| N2 `5ef43dbf631adcf3daec` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `e60c84d0cda3cc465df7` | Abstain | `tracked-value-mutation`. |
| N4 `6090fc1b1b6dbfcd6eee` | Abstain | `additional-accepted-reader-present`. |
| N5 `d4d95cdd4f4e698d675c` | Abstain | `unregistered-component-consumer`; its earlier tracked-block append remains outside G1's completed resampling path. |

### 11.2 Envelope 3 — 6/6 positives, 0/6 negatives

| Role / case | Expected 2.3 outcome | First reason or path |
| --- | --- | --- |
| P1 `a28f42e4bd1fe1c5e048` | Candidate | Complete path. |
| P2 `29893ac47ebe4ca60cce` | Candidate | Complete path. |
| P3 `df67e751158d62c4cbf4` | Candidate | Complete path. |
| P4 `045708a55a9f3e2ec449` | Candidate | Complete path. |
| P5 `2d47b05c996177f2afd7` | Candidate | Complete path. |
| P6 `d92b542e0bb28fa3c950` | Candidate | Complete path. |
| N1 `0b9b803536c12e3870eb` | Abstain | `helper-closure-or-nested-definition-unsupported`. |
| N2 `5b80f0787b1b6c47048b` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `245226f0f9f97f6acda2` | Abstain | `tracked-value-mutation`. |
| N4 `f4e4d89ac44385a18261` | Abstain | `helper-closure-or-nested-definition-unsupported`. |
| N5 `19824e3f6b1e3980872f` | Abstain | `dataflow-definition-ceiling-exceeded`. |
| N6 `3c650ec217b884e5f35e` | Abstain | `aggregation-on-test-operand-path`. |

### 11.3 Envelope 4 — 3/6 positives, 0/6 negatives

| Role / case | Expected 2.3 outcome | First reason or path |
| --- | --- | --- |
| P1 `5c26014c176bf905c121` | Candidate | Complete path. |
| P2 `5bdfa31a22a40d58e20c` | Abstain | `admission-call-off-list`; unsupported two-column return projection remains. |
| P3 `4f622f87ad3c8a93a2d8` | Abstain | `admission-call-off-list`; named `GroupBy.agg` output lineage remains outside scope. |
| P4 `c07cc7c1a1f9730a3c9f` | Candidate | Complete path. |
| P5 `34b1ade6d028cfda2a75` | Abstain | `two-group-row-selection-unavailable`; group values are data-derived, not a closed contract-domain sequence. |
| P6 `675de846f46beae7d442` | Candidate | Complete path. |
| N1 `540f7dfdf1614ceda57d` | Abstain | `multiple-rowwise-test-candidates`. |
| N2 `9cd65ce93b9b8f846eb8` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `23cc44d49100a68655c5` | Abstain | `multiple-rowwise-test-candidates`. |
| N4 `c69bb7590d57d2057ee0` | Abstain | `additional-accepted-reader-present`. |
| N5 `0e06da6bdb3963daae4e` | Abstain | `helper-closure-or-nested-definition-unsupported`. |
| N6 `e303f93351acf5df0457` | Abstain | `aggregation-on-test-operand-path`. |

### 11.4 Envelope 5 — 6/6 positives, 0/6 negatives

| Role / case | Expected 2.3 outcome | First reason or path |
| --- | --- | --- |
| P1 `0b4876ceca6b0a9aede7` | Candidate | Complete path. |
| P2 `e50e676afb2cd3593234` | Candidate | Complete path. |
| P3 `1975f22bc0022b19331f` | Candidate | Complete path. |
| P4 `2448bea72701b75fce2a` | Candidate | Complete path. |
| P5 `a1541d5c671f3d6d58ce` | Candidate | Complete path. |
| P6 `f1a04b5358a7b9b9d57c` | Candidate | Complete path. |
| N1 `0d274a0eccdb84966940` | Abstain | `aggregation-on-test-operand-path`. |
| N2 `4afe430c936bbe560a5e` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `4d64fa6416ee8406f678` | Abstain | `tracked-value-mutation`. |
| N4 `4e24fb76c83774381e41` | Abstain | `additional-accepted-reader-present`. |
| N5 `be94cec09f73d4a3036a` | Abstain | `resampling-inference-sibling-present`; G1 resolves its helper-default bootstrap count and tracked blocks before the former unregistered-consumer reason. |
| N6 `094fcb05ef85e4f7f406` | Abstain | `aggregation-on-test-operand-path`. |

### 11.5 Envelope 6 — 1/6 positives, 0/6 negatives

| Role / case | Expected 2.3 outcome | First reason or path |
| --- | --- | --- |
| P1 `03ee21366b62d03a9b26` | Abstain | `unregistered-component-consumer`; G2 clears `kit_number` and G3 preserves operands, but `rows.append(...)` / `stats.sem(weights)` in the tracked descriptive helper remain off-registry. |
| P2 `278451c17389f8c72ece` | Abstain | `admission-slice-reaches-operand`; G7 clears the same-column date store, but the later generator reads the protected reader-derived date selection. |
| P3 `5b1e03e13ef7e2e727dc` | Abstain | `unregistered-component-consumer`; G2 clears `age_weeks`, but the later `pivot_table(...).reindex(columns=...)`/format-helper path remains unsupported. |
| P4 `d89ab3ef408520667cc1` | Abstain | `unregistered-component-consumer`; G6 clears `parse_dates`, then the grouped aggregate/reindex chain remains off the closed lane. |
| P5 `92c016654c6c93979fff` | **Candidate gained by G4** | Both contract-domain dict comprehensions normalize to member edges; raw `wing` members complete the test path and the `summary` members remain print-only. |
| P6 `9d44076b46746ce05758` | Abstain | `unregistered-component-consumer`; G3 preserves `.to_numpy(float)` operands, but `stats.pearsonr` on tracked rows is a real second-inference guard. |
| N1 `2e97fd3e2ab5729b7f9c` | Abstain | `aggregation-on-test-operand-path`. |
| N2 `6dfee3d81dba1754e893` | Not applicable | `no-repeated-authorized-unit`. |
| N3 `71bd62d3b1b9d590020a` | Abstain | `tracked-value-mutation`; G5 resolves its module lists, exposing the existing categorical group-column mutation before the later dependence-aware sibling. |
| N4 `7edfc9aa77704a8a46b8` | Abstain | `additional-accepted-reader-present`. |
| N5 `b12c6fd59e338b7b156e` | Abstain | `resampling-inference-sibling-present` under G1, before printing-shape codes. |
| N6 `2438210f2abe4b53295f` | Abstain | `aggregation-on-test-operand-path`; G5 resolves module lists, then the helper-defined enclosure aggregation reaches both test operands. |

### 11.6 Honest totals

- Opened positives: **19/27 candidates**.
- Opened negatives: **0/29 candidates**.
- Net change from the `2.2.0` retrospective: **+1 positive candidate, +0 negative
  candidates**.
- Positive misses: the three Envelope-4 misses and Envelope-6 P1, P2, P3, P4, and P6.
- G2 changes two CSV gate outcomes but changes zero final candidate outcomes; G3, G5, G6,
  and G7 likewise expose later unchanged guards in their named Envelope-6 cases.

## 12. Batch-K expected locks

Re-freeze the six Batch-K method-contract closures at live check `2.3.0` during a build. This
is a closure-version refresh only; project bytes, contract answers, labels, and expected
outcomes do not change.

| Case | Procedure family | Expected scored outcome | First reason |
| --- | --- | --- | --- |
| `0de3a6061d3bb4056306` | `ttest_ind` | Abstain | `analysis-source-envelope-unavailable`. |
| `6b2da0c7167dbba3738f` | `ttest_ind` | Abstain | `analysis-source-envelope-unavailable`. |
| `e9e2718573bb47f7d17b` | `ttest_ind` | Abstain | `analysis-source-envelope-unavailable`. |
| `3ae92d0bb421d6eee99e` | `ttest_ind` | Abstain | `analysis-source-envelope-unavailable`. |
| `2c458d2b523ea8c1bd90` | binomial control | Abstain | `authorized-group-domain-not-exactly-two`. |
| `556f3545bebb45a3b005` | binomial control | Abstain | `authorized-group-domain-not-exactly-two`. |

The four t-test cases still lack root `analysis.py`; the two binomial cases still lack an
authorized exact two-value group domain. Expected K candidate count is **0/6**.

## 13. Test-plan delta

### 13.1 G1 safety matrix

1. Copy the exact `b12c6fd59e338b7b156e` analysis shape and assert first reason
   `resampling-inference-sibling-present`, including after independent admission of its
   `to_string(float_format=lambda ...)`, `.map`, and formatting calls.
2. Test trip counts through a literal, module constant, helper positional argument, helper
   keyword argument, omitted literal default, omitted closed-module default, and alpha-renamed
   inlined parameter at 49, 50, and 51.
3. Test tracked selections through dict literal members, subscript stores, list append,
   list/dict comprehensions, `.values()`, `.items()`, dynamic-key union, nested plain
   containers, and `np.concatenate`.
4. Pin `ARRAY[INDEX] = VALUE` as defining `ARRAY` in a repeated body's output set, including
   a negative near-miss with a dynamic attribute base.
5. Place trip-count resolution, tracked-container construction, reduction, and sink in four
   distinct eligible helpers; follow helper-return members, destructuring positions, and
   inlined-parameter bindings to the resampling abstention.
6. Put the bootstrap after an earlier unregistered descriptive consumer and require
   `resampling-inference-sibling-present` to dominate regardless of source position.
7. Negative controls: literal-only container, tracked container with no 50-trip loop, 50-trip
   loop with no registered reducer, reducer with no output sink, and unresolved trip count.
8. Assert the guard-only container graph cannot create a reader, selection, operand, test,
   sink, or candidate edge.

### 13.2 G2 CSV matrix

1. Differential-test all 62 envelope CSV/profile pairs: exactly `03ee.../kit_number` and
   `5b1e.../age_weeks` change D1 outcome.
2. Boundary-test `R=U` versus `R=U-1`, `distinct(C)=M` versus `M+1`, unique versus duplicate
   `(unit,C)` pairs, `distinct(C)=U` versus `U+1`, and empty byte values.
3. Preserve the closed label-collision abstention and pin the nested-value-set residual plus
   exact composite-key non-inference sentence.

### 13.3 G3-G7 positive and adversarial matrix

1. G3: all three exact `.to_numpy` forms with every accepted dtype; positional/keyword
   near-misses, stars, extra args/keywords, whole frames, grouped values, aggregate operands,
   and unknown receivers.
2. G4: both Envelope-6 P5 comprehensions; reversed domain order; helper expansion per member;
   mixed raw/aggregate members; test-result member; second-reader member; dynamic/non-domain/
   duplicate key; generator `if`; extra generator; alias, mutation, whole-dict escape, and
   literal-key reads.
3. G5: list and tuple positive forms and every element kind; zero/17 elements, nested/starred/
   computed/call elements, reassignment, subscript mutation, mutating method, deletion, and
   alias escape.
4. G6: exact inline and G5 list `parse_dates`; missing/duplicate/unknown/unit/group/value
   columns; tuple/dict/nested list; any second keyword; second reader; off-path second
   parse-dates reader; wrong or computed path.
5. G7: both exact transforms; each disallowed target column; different frame/column; loc/iloc/
   at target; string dtype, bool, keyword, chained method, second store, unresolved operand
   headers, and conversion whose result reaches a test operand.
6. Preserve a tracked-row `pearsonr` and another off-registry inferential consumer as exact
   `unregistered-component-consumer` controls.

### 13.4 Integration and non-evidence gates

1. Run all 56 opened cases and six refreshed K locks through the normal reportless CLI with
   the expectations in sections 11-12 and complete canonical replay equality.
2. Run the 108 blind and 155 regression corpora with zero Findings. An unqualified 2.3
   identity must not emit under the stale installed 2.1 production pin.
3. Extend the prose tripwire through G1 trip/default resolution, resampling-container member
   propagation, G2 classification, G3 identities, G4 normalization, G5 resolution, G6 reader
   parsing, and G7 deferred mutation classification.
4. Mutating comments, docstrings, unrelated string literals, printed labels, or any
   report/Markdown presence/content must yield byte-identical observations. Structural strings
   are limited to path, CSV header, contract group value, registered API keyword, dtype, and
   G6 date-column slots.
5. Assert old detector and manifest bytes, false-accusation halt, default gate, starter
   validation, Ruff check/format, mypy, and every existing code-lane adversarial suite.
6. Execute no project-authored analysis code in any test, development trace, or CLI path.
7. Assert the exact v1 profile digest from section 9.1 and run all four qualified Envelope-5
   candidates under the frozen 2.1 lane, requiring one v1 Finding each after 2.3 registration.

## 14. Fresh-envelope protocol after a green reviewed build

No envelope is created by the 2.3 build. If `2.3.0` is built, reviewed, and explicitly frozen,
a fresh envelope uses new prompt and case bytes under the existing chronology:

1. freeze the full implementation closure and a new prompt-author briefing before either
   maintainer sees prompt bytes;
2. assign twelve opaque IDs in fixed role order P1-P6,N1-N6 and seal the role map;
3. use an isolated prompt author with no access to detector grammar, opened case bytes,
   diagnoses, or outputs;
4. retain six independently authored positives and six negatives, including a hand-rolled
   cluster bootstrap with helper/default/container structure and a per-unit aggregate path,
   without disclosing detector syntax;
5. run normal reportless audit and model-free canonical replay; and
6. pass only with at least 3/6 positive evaluation candidates, exactly 0/6 negative
   candidates, zero Findings across 108 blind + 155 regression + all 12 fresh cases, and
   replay equality 12/12.

Recall is reported as measured. There is no retry, and no opened/burned case contributes
qualification credit.

## 15. File-by-file build list

| File or family | Proposed change | Rough delta |
| --- | --- | ---: |
| `docs/implementation/PSEUDOREP-CODE-SLICE-2.3-DESIGN-2026-08-23.md` | This delta and later BUILD-NOTES. | +600 |
| `docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md` | Append proposed 2.3 code-lane amendment and provenance after acceptance. | +25 |
| `src/sc_referee/scientific_checks/code_csv_dependence_dataflow.py` | G1 graph/default/member/destructuring reachability and precedence; G3-G7 closed AST/dataflow forms. | +500/-50 |
| `src/sc_referee/scientific_checks/report_csv_dependence_adapter.py` | Replace only the shared D1 CSV index classification; report evidence remains withdrawn and Finding-ineligible. | +35/-25 |
| `src/sc_referee/scientific_checks/code_csv_dependence_adapter.py` | Advance check/adapter/grammar identity to 2.3.0 and project the G2 non-inference. | +8/-5 |
| `src/sc_referee/detectors/method_conflict_finding.py` | Freeze v1 constants/digest; add lane-selected v2 profile with the exact composite-key non-inference sentence; no title or evidence-slot change. | +65/-10 |
| `src/sc_referee/detectors/bounded_code_csv_dependence_conflict_v2_3.py` | New versioned detector identity inheriting frozen 2.2 behavior surface. | +20 |
| `src/sc_referee/detectors/method_conflict_registry.py`, `src/sc_referee/scientific_checks/profiles.py`, `src/sc_referee/scientific_checks/integration.py` | Register and route 2.3.0. | +8/-8 |
| `src/sc_referee/scientific_requirement_contract.py` | Extend authority-only compatibility through frozen 2.2.0 to active 2.3.0. | +3/-3 |
| detector/scientific capability manifests and source-manifest records | Add immutable 2.3 records while retaining every 1.x-2.2 record; deterministically regenerate dependent digests. | mechanical |
| `evaluation/development/pseudorep-code-slice-v2_3/DEVELOPMENT_LEDGER.json` | Canonical 56-case and K expectations from sections 11-12. | +1 canonical JSON line |
| `evaluation/development/pseudorep-code-slice-v2_3/k-method-contracts/` | Six live-2.3 closure-version refreshes; no case/answer edit. | generated |
| `tests/test_code_csv_dependence_dataflow.py` and focused 2.3 tests | G1-G7 positive/boundary/adversarial matrix and G2 differential. | +700 |
| `tests/test_dependence_code_slice_development.py`, registry/manifest/Finding tests | 56/K normal path, replay, tripwire, identity immutability, exact non-inference. | +250/-30 |

No production pin, qualification resource, schema version, release manifest, envelope, commit,
or push belongs to this proposed build list.

## 16. Open build-changing questions

None. The narrow interpretations are fixed above. In particular, G1 precedes printing-shape
admission, G2 knowingly carries the disclosed nested-set residual and fixed non-inference,
G4 admits only a closed two-member contract-domain comprehension, and
`unregistered-component-consumer` remains unchanged.
