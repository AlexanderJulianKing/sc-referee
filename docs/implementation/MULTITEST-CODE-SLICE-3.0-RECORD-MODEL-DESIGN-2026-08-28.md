# Multiple-testing code slice 3.0 record-model design — 2026-08-28

**Status:** commissioned build-ready design, Revision 1a; implementation is not authorized by this
document until adversarial design review and the ADR-0079 amendment in section 2.4 are accepted  
**Target:** detector/check/adapter `3.0.0`, development lane only  
**Predecessor:** multiple-testing code slice `2.3.0`  
**Authority:** frozen scientific-requirement contract profile `1.2.0`; no prose-derived authority  
**Scope:** one record-model architecture layer plus the narrow D14-A cardinality admission  
**Implementation in this session:** none

## 0. Evidence basis, terminology, and observed/inferred boundary

This design follows `FINDINGS-PLAYBOOK.md` and the 2.0 inversion boundary: whole-module syntactic
censuses establish FA-critical presence facts, backward and forward slices establish value
identity, and every unresolved edge on either slice abstains. It does not restore a whole-module
statement grammar.

The evidence set is:

- the opened-corpus recon under
  `evaluation/development/multitest-recall-recon-corpus20/`;
- the E12 record/table ladders under
  `evaluation/development/multitest-code-slice-v2_2/e12-ladders/` and the E12 recon;
- the E13 and E14 executed ladders under
  `evaluation/development/multitest-recall-recon-e13/` and
  `evaluation/development/multitest-recall-recon-e14/`;
- all sealed-then-opened adapter results for envelopes 10 through 14; and
- the installed 2.3 source and its frozen replay/oracle tests; and
- the strict executable 3.0 shadow models, 48 named fixture sources, all-125-case sweep, and
  canonical results under
  `evaluation/development/multitest-code-slice-v3_0/prototype-sweep/`.

The following are **observed**:

1. the installed 2.3 adapter outcomes pinned in sections 12 and 13;
2. E14 P2 becomes `candidate/none` when only its second record-result pass is removed;
3. E14 P4 reaches `unresolved-pvalue-consumer` after only the selector dispatch is replaced by one
   direct uniform API;
4. E14 P5 reaches `correction-family-lineage-unresolved` after that same dispatch simplification;
5. E12 P5 reaches `pvalue-family-collection-unresolved` after the 2.2 presentation ordering fix;
6. E12 N1 and N2 are correct analyses stopped by the DataFrame p-table wall; N1 uses complete
   default-method `multipletests`, and N2 uses a hand-Sidak threshold;
7. D14-A moves exactly E14 P3 from `test-battery-cardinality-unresolved` to
   `unresolved-decision-threshold` in its executed prototype and moves no corpus row; and
8. the corpus remains `0/25` correct candidates and `19/25` misstep candidates in 2.1, 2.2, and
   2.3; and
9. the Revision-1a strict prototypes execute all four new models plus D14-A over all 125 pinned
   cases, 39 correct adversaries, and nine positive controls. They produce the exact section-12/13
   outcomes, including the one newly exposed safe E14 N9 hierarchy reason, with none-flip counts
   `0/25`, `0/45`, and `0/39`.

The shadow results are **executed observations**, not production-adapter results: the models import
the frozen 2.3 analyzer, apply only the section-5-to-9 structural admissions, and retain adapter
pins such as E10 N7. They close the design-evidence blocker and are normative build oracles. A 3.0
builder must still execute the public adapter gates and may not replace one with a different
conservative reason merely because the case remains a noncandidate; disagreement is a section-17
stop.

Terms used below:

- `N` is the exact authorized outcome count and exact performed-family count.
- `POS` is one integer in `0..N-1`, mapped order-equal to the contract outcome list.
- `P(POS)` is the registered `.pvalue` member for that family position.
- `AP(C, POS)` and `REJECT(C, POS)` are an adjusted p-value and reject decision from one already
  recognized correction `C` whose ordered input positions include `POS`.
- `D(POS, ORIGIN, OP, THRESHOLD)` is one normalized decision with its p/reject origin, comparison
  direction, and the unchanged threshold proof.
- `DISPLAY(X)` is a value admitted only by the existing presentation grammar while retaining the
  structural provenance `X` (for example `D` or `P`); `DISPLAY` without an argument is p-free.
  Display bytes are measured but never interpreted.
- `UNRESOLVED` is absorbing. No union, merge, alias, record, DataFrame, or dispatch rule may drop
  it.

## 1. Decision and hard boundary

Version 3.0 adds one coherent symbolic record graph. It admits:

1. ordered per-outcome record collections constructed as exact Dict, Tuple/List wrapper, or
   already-accepted R4 dataclass/namedtuple records, including exact record-field stores, a
   decision-flag fold, and at most two equivalent conclusion emissions for one member;
2. exact family-position selection from those collections by literal/static slice or a closed
   outcome-table flag, before a correction or `strict_subset` claim;
3. one statically resolved table-selector dispatch from each authorized outcome to exactly one of
   the two registered two-group APIs; and
4. a bounded pandas DataFrame row-table representation of the same record graph.

Version 3.0 also adopts D14-A, the exact singleton projection-binding generator from the E14 recon.

The design does **not** admit:

- a Dict keyed by outcomes as a family-record collection;
- parallel scalar/NumPy p arrays, including corpus `spec-39` and `spec-50`;
- arbitrary object records, methods, properties, nested containers, dynamic keys, or inferred field
  meanings;
- arbitrary DataFrame semantics, row filters, joins, sorting, grouping, indexing, or mutation;
- opaque or data-dependent API dispatch;
- more or fewer than one registered family test per authorized position;
- new zip write-back forms beyond unchanged R16;
- hand correction `p < ALPHA/K`;
- a proper-subset manual multiplier; or
- any correction, threshold, hierarchy, row-completeness, export, extremum, resampling, or
  correction-terminal weakening.

Off-record code remains admitted only while it is off every operand, p, record, correction,
decision, hierarchy, and conclusion slice. Any unresolved consumer, store, container, record,
DataFrame operation, dispatch edge, or escape on those slices abstains.

## 2. Identities, contract, evidence, wording, and frozen isolation

### 2.1 Versioned identities

The versioned identities are:

```text
check_id       check:authorized-complete-family-correction-over-code-test-battery
check_version  3.0.0
detector_id    detector:bounded-code-csv-multiple-testing-conflict
detector_version 3.0.0
adapter_id     adapter:authorized-complete-family-correction-over-code-test-battery:code-csv-v1
adapter_version 3.0.0
grammar_id     bounded-code-csv-multiple-testing-conflict-v1
grammar_version 3.0.0
```

The stable check/detector/adapter IDs preserve historical registry addressing; the versions and
implementation/grammar digests distinguish 3.0. The active development binding advances to 3.0.0.
Versions 1.0, 1.1, 2.0, 2.1, 2.2, and 2.3 remain explicitly registered for frozen replay only.
No 3.0 identity resolves on a qualified lane.

### 2.2 Contract and evidence profile v2

Contract profile `1.2.0` is unchanged:

```text
material_input_path
group_contrast_column
ordered outcome_columns
family_member_rule = one-two-group-test-per-named-outcome-column
correction_scope = complete-authorized-family
```

The family-member rule requires one registered two-group test for each named outcome. It does not
require one uniform API. The existing evidence profile cannot truthfully represent a mixed family:
`registered_test_api` is singular and its validator requires a uniform identity. Version 3.0
therefore creates `code_csv_multiple_testing_evidence_v2` with:

```text
registered_test_apis_by_position: ordered list[str] of length N
registered_test_api_set: sorted unique list[str]
```

Every entry is exactly `scipy.stats.ttest_ind` or `scipy.stats.mannwhitneyu`. The ordered list is
order-equal to `outcome_columns`; the set is derived from it and is never an inference source.
`performed_count` remains exactly `N`. All other v1 evidence fields and invariants remain. The v1
projection class and every historical byte remain untouched.

### 2.3 Wording profile v2

The v1 wording says “matching `{TEST_API}` calls” and defines `TEST_API` as a uniform API identity.
The mixed-family admission therefore forces a new wording profile; it is not safe to put a list in
that slot. Create:

```text
method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v2
profile_version = 2.0.0
```

Its title, severity rationale, next action, and non-inferences are byte-equal to v1. Its summary is
v1 with the API/count sentence replaced as follows and every later reference to registered
`.pvalue` members replaced by the API-neutral phrase “registered family p-value results”:

```text
In `analysis.py`, static analysis maps every named outcome to exactly one registered two-group
test call, for {PERFORMED_COUNT} calls in all.
```

This remains true for both the registered `.pvalue` member and an already-supported position-1
p-result projection. It does not imply that every registered result object exposes the same Python
attribute.

The `TEST_API` slot is deleted. All other slots remain: `CSV_PATH`, `GROUP_COLUMN`,
`OUTCOME_COLUMNS`, `AUTHORIZED_COUNT`, `PERFORMED_COUNT`, `CORRECTED_COUNT`, and
`UNCORRECTED_COUNT`. The profile has its own semantic digest from day one. It retains verbatim the
non-inference that absence of a recognized correction in the analyzed source does not establish
that no correction was applied. Neither API-selector tokens, field keys, record labels, DataFrame
column names, format strings, comments, nor report text enter wording.

The v1 wording objects are byte-untouched and remain bound only to historical versions. The new v2
wording is development-only until a future qualification expressly pins it.

### 2.4 Required ADR-0079 amendment

Before implementation, ADR-0079 must record:

1. removal of API uniformity as an accusation precondition under the already-frozen
   `one-two-group-test-per-named-outcome-column` rule;
2. the exact dispatch proof in section 8 and the one-call-per-position invariant;
3. evidence profile v2 and wording profile v2;
4. the record, positional-subset, duplicate-emission, flag-fold, and DataFrame boundaries;
5. D14-A as a cardinality/value normalization only;
6. retirement of `mixed-test-api-family` in 3.0 and its non-comparability across versions; and
7. the unchanged exclusions for zip write-back, proper-subset factors, and `ALPHA/K`.

This is a candidate-surface and wording change, not an implementation convenience. A build against
an unamended ADR stops.

### 2.5 Frozen 2.3 anchor and isolation

The following 2.3 bytes are frozen:

```text
dataflow v2_3     sha256:70d8fd3c8f61e8726379c582e420700ea3babd0c45468e22b6f5b6f3b05dff28
adapter v2_3      sha256:e5c2a05e87fdec206460ccf73343e4dd158a7c311979208939f217a97f603023
detector v2_3     sha256:9de2e519e600546e2e57d4b29f0894375dcdd9455bdbf51bc951390a79f56e82
integration v2_3  sha256:dfd23cdc5c87b894bff5ff147d77a3ee8418cd2a06cc9ba9af18bfebbcf4a1e7
2.3 design        sha256:4cfed92169acd51154fd110c351a23421454501e090aaf9c2ed662b8a4feb5e5
```

The older replay anchors remain frozen, including:

```text
adapter_replay_records_v2_1.json
  sha256:7c37669c8ccfdb0b754aa03ee1dbcee1dac78fa4bb44105e17c5d1886aaed502
E12 adapter_replay_records_v2_2.json
  sha256:f8b7808b3baee264e9c496e2e899686af235e72c37b9647ce4255d10adbb02d8
E13 adapter_replay_records_v2_3.json
  sha256:d171c40e0715ff2b0f4c65bb667e817b78575ea1f2d73a8bc9af0869d3143489
```

Version 3.0 is implemented by copies named `_v3`; no v2.3, older MT, dependence,
qualified pseudoreplication, GrantPin, grant, qualification, threshold-policy, metric-set, or v1
wording byte is edited. The two-registry differential must again prove that no qualified GrantPin,
grant, qualification record, metric-set record, threshold reference, or Finding byte derives from
a development-lane-inclusive digest.

## 3. Whole-module censuses and ordered pipeline

### 3.1 Registries restated by value

The registered family APIs remain exactly:

```text
scipy.stats.ttest_ind
scipy.stats.mannwhitneyu
```

The recognized correction APIs remain exactly:

```text
statsmodels.stats.multitest.multipletests
statsmodels.stats.multitest.fdrcorrection
scipy.stats.false_discovery_control
sc_referee.calculation_checks.bh.benjamini_hochberg
```

The correction terminal-name census remains exactly:

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

The statistics-prefix registry remains byte-equal to 2.3:

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

The repeated-construct, dynamic-execution, API-rebinding, alternate-file, reader, hierarchy/
prevention, correction-terminal, and statistics-prefix censuses remain whole-module and syntactic.
They run on the untouched parsed tree before any normalization or symbolic record construction.

### 3.2 Call census after the policy change

The call census still visits every registered call in every helper and branch. It produces two
separate receipts:

1. a **syntactic occurrence census** containing every registered call node and every uncalled or
   dead conservative instance; and
2. an **execution-instance plan** mapping exactly one registered call to every `POS`.

Ordinary unrolled, loop, comprehension, X4, literal-false, and uncalled-helper rules are unchanged.
Section 8 adds one dispatch production. A registered call may not disappear merely because it is
inside a dispatch: each source call must be owned by one dispatch arm, and each table row selects
exactly one arm. A registered call outside the `N` owned instances remains
`extra-registered-test-outside-authorized-family`. Fewer than `N` resolvable instances remains
`authorized-family-test-census-incomplete` or `test-battery-cardinality-unresolved` under the
existing split.

### 3.3 Ordered integration

The required order is:

1. parse and bounds;
2. authority/CSV/source-envelope checks;
3. untouched-tree dynamic, rebinding, correction, statistics, repeated-construct, reader, and
   hierarchy/prevention censuses;
4. untouched-tree registered-call census plus section-8 dispatch plan;
5. D14-A and the existing X4/D2/D6/D13 normalization sequence, with the global census still tied
   to source occurrences;
6. backward operand identity and row-completeness proofs for every planned `POS`;
7. local registered p-root proof for every call;
8. build the section-4 symbolic record graph from the normalized slice without mutating the AST;
9. total forward accounting through records, positional subsets, corrections, DataFrames,
   decisions, and sinks;
10. extremum, recognized correction, correction-terminal, off-grammar transform, direct-threshold,
    hierarchy/resampling/partition/inference, and conclusion-family guards in the unchanged 2.3
    relative order; and
11. classify `none`, `strict_subset`, or `complete` and project v2 evidence.

Direct-P comparisons remain exclusive to the threshold order. Record or DataFrame reconstruction
must not move arithmetic into the off-grammar transform order or mark it as a correction.

## 4. Symbolic record graph and common invariants

### 4.1 Graph objects

The record graph is a side table, not rewritten project code. Its objects are:

```text
RecordId       = (source construction key, POS, occurrence ordinal)
FieldKey       = literal str | literal int | accepted R4 field name
Record         = ordered map FieldKey -> Value
Collection     = ordered tuple[RecordId] with exact source provenance
Subset         = ordered tuple[RecordId] derived by section 7
DataFrameTable = ordered tuple[RecordId] plus ordered static column keys
```

An occurrence ordinal preserves multiplicity only. It is never a matching field, evidence value,
family-position substitute, or deduplication key. Equal source/field shapes at two positions remain
two records.

`Value` is the closed lattice `Outcome(POS)`, `P(POS)`, `AP(C,POS)`, `REJECT(C,POS)`,
`D(POS,...)`, `DISPLAY(X)`, closed non-p scalar, `OPAQUE_NONP`, one exact nested `RecordId`, or
`UNRESOLVED`. `OPAQUE_NONP` is permitted only when a complete backward slice proves no family p,
registered/correction result, decision, or dynamic record key reaches the value, and no forward
consumer reaches a test, correction, decision, hierarchy control, record identity, or p-derived
field. It exists so descriptive means, operand Series, and similar off-p record members do not
contaminate a p field. An unresolved provenance edge is not `OPAQUE_NONP`.

Merges are component-wise union. A merge involving `UNRESOLVED`, two different p positions in one
p/decision field, raw and adjusted p in one decision field, or incompatible decision polarity is
unresolved; it never chooses the more accusation-supporting origin.

### 4.2 Family-position ownership

Every record must have exactly one `POS`. Position is proved by one of:

1. the exact expanded complete-outcome loop/comprehension occurrence that constructs it;
2. an exact contract outcome value in one static field, order-equal to the authority;
3. an unchanged R16 family-position mapping; or
4. section 7's exact subset mapping from an already proved collection.

If more than one route exists, all routes must agree. An absent, dynamic, duplicate, or conflicting
position abstains `record-family-lineage-unresolved`. Field names such as `p`, `p_raw`,
`significant`, `primary`, or `outcome` have no semantic force. P lineage and position establish
their roles.

### 4.3 Any-unresolved-flow-abstains invariant

A 3.0 candidate asserts no recognized complete-family correction and raw conclusions. The assertion
is sound only because all three obligations hold:

1. whole-module censuses see every registered test, correction name, statistics call, dynamic
   execution form, rebinding, and execution-prevention control;
2. every family p root and every p-derived record/flag/table value has all consumers accounted for;
   an unknown call, field, mutation, alias, row operation, container, store, export, or escape
   abstains; and
3. all arithmetic on p or thresholds still passes through the unchanged order-12/order-13
   grammars, source-text Decimal rules, product rules, and single-binding-anywhere proof.

Record and DataFrame admissions are transports only. They do not recognize a correction, threshold,
test API, group split, or conclusion by spelling.

### 4.4 Bounds

The source, AST, and helper ceilings remain `1 MiB`, `50,000` nodes, and `16` definitions. New
bounds are:

- `N <= 64` for record-graph construction;
- at most `16` fields per record and `32` static DataFrame columns;
- nesting depth at most two, only under section 6.3;
- at most two p-derived conclusion emissions per `POS`;
- at most `4N + 64` record/field stores; and
- at most `8N + 128` graph edges.

Exceeding a bound abstains `dataflow-definition-ceiling-exceeded`; it never truncates.

## 5. D14-A — exact singleton projection-binding generator

D14-A applies only to a `DictComp` with exactly two non-async generators:

1. generator one already satisfies the complete authorized-outcome iteration grammar, has no
   filters, and contributes factor `N`;
2. generator two has no filters and iterates one literal List or Tuple display containing exactly
   one flat two-element row;
3. its target and row are both Tuple or both List, have exactly two elements, and the target
   elements are distinct simple Names;
4. each row element is exactly `FRAME[OUTCOME_NAME]`, where `OUTCOME_NAME` is generator one's name
   and each `FRAME` independently proves one complete authorized group operand;
5. the two bound names are loaded only in the comprehension payload and only through existing
   registered-test or recognized numeric-presentation consumers; and
6. symbolic bindings evaluate once, eagerly, in source order. No textual substitution may
   duplicate projections.

Any second row, third generator, filter, async form, kind mismatch, call/arithmetic component,
unknown frame, extra load, or failed row proof retains the ordinary cardinality/operand reason.
The untouched census sees the original registered call. D14-A contributes factor one only for the
second generator.

D14-A intentionally does not place E14 P3's Dict-keyed record map in section 6. It therefore moves
that case once, from `test-battery-cardinality-unresolved` to
`unresolved-decision-threshold`, exactly as the executed recon pinned. The five D14-A adjacent
refusal fixtures and the correct whole-family hand-Bonferroni control remain required.

## 6. Record accumulation, field stores, flags, and duplicate emissions

### 6.1 Admitted construction productions

A family record collection is admitted only through one of:

```text
COLL = []
for COMPLETE_OUTCOME_BINDING:
    ...
    COLL.append(RECORD)

COLL = [RECORD for COMPLETE_OUTCOME_BINDING]
```

The comprehension is one non-async generator with no filters. The loop is an already-admitted
complete family loop. `append` has exactly one positional argument and no keywords. The collection
has one empty-List binding before the builder, one builder site, exactly `N` appended records, and
no other mutating receiver call. Tuple/set/dict builders, `extend`, `insert`, `+=`, concatenation,
and generator materialization are refused by this production.

`RECORD` is one of:

1. a Dict display with `1..16` unique literal string/integer keys, no unpacking, and independently
   classified values, including exact `OPAQUE_NONP` descriptive fields;
2. a Tuple display with `1..16` fields;
3. an R4 dataclass/namedtuple construction under its unchanged field-only schema; or
4. the exact one-wrapper form in 6.3.

A List display is a collection, not a record, except as the wrapper matching kind in 6.3. A direct
helper return is allowed only after unchanged X4 expansion makes one of the productions above
visible. No opaque cross-function record or collection flow is admitted.

### 6.2 Schema and homogeneity

After all allowed stores, every one of the `N` records must have the same record kind, ordered field
keys, and field count. The p/decision roles may differ only by position and by recognized correction
coverage. `None`, a closed scalar, or DISPLAY may occupy a non-p/absent-adjustment field, but a
field that is p-derived at one position and an unrelated scalar at another is unresolved unless the
branch is the exact raw/adjusted `p_used` fold in 6.5.

Mixed Dict/Tuple/R4 records, missing/extra keys, dynamic keys, `**` unpacking, starred tuple members,
sets, arbitrary objects, properties, methods, defaults containing calls, and heterogeneous nesting
abstain `record-family-lineage-unresolved`.

### 6.3 One exact nested wrapper

E14 P2 appends `(LABEL, RESULT_DICT)`. This is admitted only when:

1. the wrapper is Tuple or List of length two through four;
2. exactly one field is one already-proved record constructed for the same singleton `POS`;
3. every other field is closed non-p scalar or DISPLAY;
4. the inner record has no record-valued member;
5. no second outcome/p/decision origin competes with the inner record; and
6. later destructuring or literal indexing uniquely reaches the same inner `RecordId`.

The wrapper is flattened into a namespaced field path. Two record-valued members, depth greater than
two, different positions, dynamic indexing, alias escape, or a p value in both wrapper and inner
record abstains `record-family-lineage-unresolved`.

### 6.4 Exact field stores and mutation closure

One record may receive a field store only as:

```text
ROW[LITERAL_KEY] = VALUE
ROW.FIELD = VALUE              # R4 only if R4 already permits the field
```

`ROW` must be the unique local record name or the unique loop target of a full collection/exact
subset iteration. The target key is static. The store is an unconditional simple Assign after
construction and before every consumer, or lies under a branch that statically folds by a closed
outcome-table value for this `POS`. One reaching definition must exist for each final field and
position. A loop over a proved subset stores only those exact positions.

The following refuse `record-family-mutation-unresolved`: record or collection reassignment;
`AugAssign`; `del`; slice or dynamic-key store; duplicate reaching store; conditional store not
statically folded; loop-carried value; alias mutation; receiver calls; attribute mutation outside
R4; passing a record/collection to an unresolved call; return through an unexpanded helper;
closure/global/nonlocal flow; and any store after a p/flag/table consumer.

### 6.5 Exact raw/adjusted and flag fold

For one `POS`, a `p_used`-like field may resolve only as one statically selected branch of:

```text
AP(C, POS)  for POS in exact correction positions
P(POS)      for every other POS
```

The selector must be a closed outcome-table flag or exact position subset from section 7. Both
branches are built and checked; neither is inferred from field names or prose. If a position could
take both, neither, or an unresolved value, abstain `record-family-lineage-unresolved`.

A decision flag is admitted only as `bool(DECISION)`, `DECISION`, or `REJECT(C,POS)`, where
`DECISION` already passes the unchanged comparison/threshold grammar. `bool` is unshadowed and has
one positional argument. The flag may be stored in construction or by 6.4. It may later be loaded
as a direct truth test, `not FLAG` with branch arms correspondingly inverted, an existing
constant-display IfExp/If rendering, or a display-only aggregate in 6.7.

Two different comparisons, raw and adjusted origins, unknown truth conversion, numeric flag
arithmetic, equality to a non-Boolean, ambiguous negation, overwrite, or a branch whose polarity
cannot be paired with its arms abstains `record-decision-polarity-unresolved`.

### 6.6 Duplicate conclusion emissions

One `POS` may have one or two p-derived conclusion emissions. Two are admitted only when:

1. both independently resolve to the same normalized `D(POS, ORIGIN, OP, THRESHOLD)`;
2. `ORIGIN` is the same raw `P(POS)`, same `AP(C,POS)`, or same `REJECT(C,POS)`;
3. operator direction and threshold source-text Decimal identity are equal;
4. both sinks are otherwise accepted and have no unresolved sibling payload;
5. neither controls a test, correction, collection mutation, store, export, early exit, or a third
   emission; and
6. conclusion evidence records `POS` once, while both source spans remain in audit evidence.

This covers E14 P2's immediate and summary emissions. A corrected p at one site and raw p at the
other, opposite polarity, different threshold, different family position, unresolved clone,
more than two emissions, or one accepted plus one unknown consumer abstains
`record-duplicate-conclusion-ambiguous`. Duplicate emission never changes `performed_count`.

### 6.7 Display-only aggregates

The only aggregate over flags is:

```text
sum(1 for ROW in COMPLETE_COLLECTION if ROW[FLAG])
sum(ROW[FLAG] for ROW in COMPLETE_COLLECTION)
```

The collection must be the complete ordered family, `sum` unshadowed, generator non-async with no
other filter, and the result must flow only by identity/format transport into one accepted display
sink. It supplies no conclusion, correction, family position, or evidence count. Any comparison,
branch, correction argument, store with a second consumer, subset collection, or unknown consumer
returns the node to the hierarchy/consumer guards. This admits E14 P4's final descriptive count
without treating it as scientific evidence.

## 7. Positional-record subset model

### 7.1 Literal/static slices

Given an already proved ordered `Collection` of length `N`, the following are the only slice forms:

```text
COLL[START:STOP]
COLL[:STOP]
COLL[START:]
```

`START` and `STOP` are nonnegative integer literals or single-bound immutable module constants
resolving to such literals. Step is absent or literal `1`. Bounds satisfy
`0 <= START <= STOP <= N`. Python's exact half-open positions are used; no clamping, negative
index, omitted proof, arithmetic, `len` expression, runtime value, reverse, or nonunit step is
admitted. The subset keeps source order and exact `RecordId`s.

A slice of a slice (`COLL[A:B][C:D]`) is explicitly refused even when both individual slices have
literal bounds; it abstains `record-subset-position-unresolved`. A literal integer `COLL[I]` is
admitted as one record only when `0 <= I < N`; it is never by itself
a correction family. Tuple-record field indexing is separately resolved against the record schema.

### 7.2 Closed outcome-table flag filters

One filter is admitted:

```text
[ROW for ROW in COLLECTION if ROW[STATIC_FLAG]]
[ROW for ROW in COLLECTION if not ROW[STATIC_FLAG]]
```

`STATIC_FLAG` must originate solely from a Boolean literal field in the immutable, complete
contract-outcome table and be copied without computation into every record. It may not be
p-derived, assigned conditionally at runtime, inferred from its key spelling, or mutated. The
selected ordered positions are evaluated from the frozen table. A filter on a p decision, missing
value, dynamic key, arbitrary predicate, second generator/filter, or non-record member abstains
`record-subset-position-unresolved` and remains a hierarchy edge where applicable.

This admits E12 P5's two `is_primary` positions. E14 P5 uses the equivalent exact prefix slice.

### 7.3 Correction and strict-subset obligation

A correction input built from records is accepted only when its p sequence is order-equal to the
subset's positions, has no duplicates, and every element is exactly `P(POS)`. Correction return
mapping must return to the same positions through an already-recognized return transport. R16 is
unchanged; 3.0 supplies exact record positions to it but adds no new zip production.

Before a `strict_subset` classification, the engine proves:

1. the base collection contains all `N` positions exactly once;
2. the selected positions are exact under 7.1 or 7.2;
3. the recognized correction covers exactly those positions;
4. every excluded position reaches a raw conclusion; and
5. every included position reaches an adjusted/reject conclusion from that correction.

Off-by-one, duplicate, reordered, dynamic, runtime-p-filtered, or positionless selection abstains
`record-subset-position-unresolved` or `correction-family-lineage-unresolved`; it never defaults to
`strict_subset`.

## 8. Mixed registered-test API family

### 8.1 Exact dispatch grammar

The only mixed-API production is a complete outcome-table loop whose row has one selector value and
whose body contains one If/Elif chain. The table is either the direct immutable module table or an
unchanged X4-expanded helper formal bound at its sole call site to that exact table:

```text
if SELECTOR == STATIC_TOKEN_1:
    RESULT_TARGET = REGISTERED_API_1(OPERAND_A, OPERAND_B, CLOSED_OPTIONS...)
elif SELECTOR == STATIC_TOKEN_2:
    RESULT_TARGET = REGISTERED_API_2(OPERAND_A, OPERAND_B, CLOSED_OPTIONS...)
else:
    raise ...
```

Reversed equality is admitted. Each `STATIC_TOKEN` is a distinct literal str/int/bool appearing in
the immutable outcome table. Tokens are equality keys only: their bytes are not interpreted. Every
table row matches exactly one branch, and every registered-call branch is selected by at least one
table row; an unused registered arm is not silently discarded. The final `else` contains exactly
one Raise and no registered call, p consumer, correction, collection mutation, or sink. There are
no nested conditions, fall-through assignments, prior/after family calls, or branch-local early
exits.

Each branch call is exactly one registered API from section 3.1. All branch calls bind the same
simple result target or the same-kind flat destructuring target. Each selected call's two operands
independently prove the authorized outcome column, group split, and complete rows. API-specific
options remain those already admitted by 2.3. One table row therefore creates exactly one execution
instance and one `P(POS)`.

### 8.2 Refusals and replacement of the uniformity guard

The following abstain `family-test-api-dispatch-unresolved`: selector not from the exact row;
dynamic/nonliteral token; missing/duplicate matching arm; input-derived selection; function object
stored in a table; dict/call dispatch; unregistered or unresolved API branch; unresolved options;
different result targets; operand mismatch; conditional outside the exact chain; or a non-Raise
fallback.

Two registered calls selected for one position, a registered call before/after the chain, or one
branch containing two calls abstains `multiple-registered-tests-for-family-member`. Registered
calls elsewhere still contribute to the global extra-call guard.

The 2.3 `mixed-test-api-family` guard protected four facts: only registered APIs; one call per
position; unambiguous outcome-to-call mapping; and truthful uniform `TEST_API` wording/evidence.
Version 3.0 preserves the first three with the dispatch plan and replaces the fourth with evidence
profile v2 and wording v2. It does not simply delete the guard. `mixed-test-api-family` is retired
for 3.0 and remains meaningful only in frozen pre-3.0 records.

### 8.3 Correction and conclusion handling

After dispatch resolution, all p roots enter the same record, correction, threshold, hierarchy,
and conclusion machinery. Mixed APIs do not change correction coverage. A complete recognized
correction over all mixed positions is `covered/complete`; a recognized exact subset can be a
candidate only after section 7; no correction remains `candidate/none` only after every conclusion
is proved. A statistics call outside the exact family still triggers the unchanged prefix guard.

## 9. Minimal DataFrame p-table model — included

### 9.1 Boundary decision

Version 3.0 includes a minimal pandas row-table model. This is justified because the model is a
second storage view of the same finite `RecordId` graph: row order is fixed, column keys are static,
and every p-derived column consumer is total. It is not a general DataFrame evaluator.

The complete DataFrame trigger population is pinned, not sampled: E10 N7; E11 P5 and N3; E12 P1,
N1, N2, N3, and N9; and E14 N3. Their required outcomes are respectively
`statistics-api-imported-outside-analysis-py`, candidate `strict_subset {0,1}/7`,
`unresolved-manual-correction-present`, candidate `none`, covered `complete`,
`unresolved-decision-threshold`, `unresolved-manual-correction-present`,
`test-battery-cardinality-unresolved`, and `authorized-family-test-census-incomplete`. The seven
negative/correct rows must never become candidates; either such candidate withdraws the DataFrame
model rather than broadening or relabeling it. The two positive rows must reach their pinned
candidates. Any other outcome on any of the nine is a section-17 regression.

### 9.2 Construction

One table is admitted as:

```text
DF = pandas.DataFrame(RECORD_COLLECTION)
DF = pandas.DataFrame(LITERAL_ROWS, STATIC_COLUMNS)
DF = pandas.DataFrame(LITERAL_ROWS, columns=STATIC_COLUMNS)
```

For the first form, `RECORD_COLLECTION` already satisfies sections 6 and 7 and contains all `N`
records in order. For the second, `LITERAL_ROWS` is one List/Tuple of exactly `N` same-kind flat
Tuple/List records, `STATIC_COLUMNS` is one same-length List/Tuple of unique literal str/int keys,
and each row has one proved `POS` and independently classified p/scalar/`OPAQUE_NONP` fields.
`POS` for this second form is proved only through section 4.2 route 2 (the complete immutable
outcome-table row mapping); physical DataFrame row order by itself never proves position.
`STATIC_COLUMNS` may occupy the second positional slot or the `columns=` slot, never both. No
`index`, dtype, copy, data manager, `from_records`, dict-of-columns, Series, concat, or third
positional argument is admitted.

The pandas alias must resolve exactly. A table has at most `N` rows and 32 columns. Column names do
not establish meaning; lineage does.

### 9.3 Allowed row-preserving operations

The only whole-table operations are:

```text
DF2 = DF.copy()
DF2 = DF.drop(columns=STATIC_COLUMN_LIST)
DF2 = DF[STATIC_COLUMN_LIST]
```

Each is an unconditional simple assignment with one reaching definition. `copy` has no arguments;
`drop` has exactly the `columns` keyword and no inplace/axis; column projection is a unique static
list with no duplicates. They preserve row order and `RecordId`s. Rebinding the same name is allowed
only as one linear persistent chain of these operations before later consumers; the old version has
no consumer after rebind.

Sorting, row slicing, Boolean row subscript, query, merge/join/concat, groupby, pivot, reset/set
index, explode, sample, head/tail, drop rows, deduplicate, transpose, apply/map over rows, inplace
operation, unknown method, alias, view, or escape abstains `dataframe-pvalue-table-unresolved`.

### 9.4 Column reads and stores

Static column read `DF[LITERAL_KEY]` yields the ordered field values. The only transports are
identity, exact `.to_numpy()`/`.tolist()` with no arguments, existing scalar cast/presentation
rules per element, and correction input reconstruction.

Whole-column store is admitted only as:

```text
DF[LITERAL_KEY] = ORDERED_SEQUENCE
```

The RHS has exactly `N` values mapped order-equal to rows and every value is closed scalar,
`OPAQUE_NONP`, DISPLAY, `AP`, `REJECT`, or `D`. An exact vector comparison
`P_COLUMN < THRESHOLD` (including reversed operand order and the other already-admitted comparison
operators) yields an order-equal sequence of `D` only after every element passes the unchanged
threshold grammar. A two-element literal Boolean-to-DISPLAY `.map(...)` over such a decision
column is presentation only; map keys must be exactly the Boolean constants and values must be
DISPLAY. Partial store is admitted only as:

```text
DF.loc[STATIC_POSITION_MASK, LITERAL_KEY] = ORDERED_SUBSET_SEQUENCE
```

The mask is derived solely from exact contract-outcome membership/static table flags and maps to
section-7 positions. Its only DataFrame spelling is
`DF[OUTCOME_KEY].isin(STATIC_CONTRACT_SUBSET)` with no additional arguments, where the outcome
column is order-equal to the contract and the immutable subset contains unique exact contract
outcome values; an exact elementwise equality to one contract outcome is also admitted. No column
name or subset label supplies this identity by spelling. RHS positions are exactly equal and in
order. A field may first be initialized
to one closed scalar such as `None`/`pandas.NA`, then receive one exact partial store before any
load. Dynamic masks, p-derived masks used for correction/conclusion, duplicate stores, shape
mismatch, scalar broadcast of p, chained indexing, `.iloc` store, or unknown dtype conversion
abstains `dataframe-pvalue-table-unresolved`.

The exact raw/adjusted `Series.where(STATIC_POSITION_MASK, RAW_COLUMN)` form is admitted only when
the receiver contains `AP(C, positions)` at precisely the true positions and the other branch is
`P(POS)` at all false positions. `.astype(float)` may follow only that fully resolved p-used
sequence. This covers E11 P5 and cannot select positions by a runtime p value.

### 9.5 Row iteration and presentation

Full-row iteration is admitted only as:

```text
for ROW in DF.itertuples(): ...
for INDEX, ROW in DF.iterrows(): ...
for VALUE in DF[LITERAL_KEY]: ...
```

There are no arguments, filters, async forms, breaks, continues, mutation of row identity, or
nested iteration. `itertuples` attribute fields and `iterrows` literal subscripts resolve to the
static schema. `INDEX` is display-only and never a family position. Iteration order remains the
contract order.

`DF.to_string(...)` is allowed only as presentation into one accepted print payload. Arguments are
limited to closed literal display options plus one `float_format=` value that is either an already
accepted pure presentation helper or a one-parameter Lambda returning only direct-formal
f-string/percent/`.format` presentation. The callable is never executed by the detector and may
not compare, transform, correct, store, or escape its parameter. It supplies no conclusions.
`.to_csv`,
`numpy.savetxt`, and `json.dump` remain export sinks and any family p flow to them abstains
`unresolved-pvalue-consumer`.

One additional display-only helper form is admitted for nullable adjusted columns: exactly one
parameter, one `if pandas.isna(PARAM): return DISPLAY` followed by one return that directly formats
`PARAM`. It is accepted only when all call sites are p-result-eligible display payloads. It supplies
no decision or correction evidence. Any numeric arm, correction/arithmetic, additional statement,
unknown alias, or second consumer remains unresolved. This is the closed transport needed by E11
P5; it does not treat missingness as a scientific verdict.

P-derived flag masks may select label/display lists only after all per-member conclusions and only
for an accepted sink. They provide no correction positions or conclusion evidence. A p-derived row
mask used for correction, row removal, table reconstruction, test operand, early exit, or scientific
control remains hierarchy/unresolved.

### 9.6 Aliasing, functions, and totality

A DataFrame table may cross a helper boundary only through unchanged X4 expansion. No opaque
parameter/return, closure, module global mutation, attribute storage, container insertion, or
unresolved call is admitted. Every column and row consumer, including non-p sibling fields in a
p-bearing record, is enumerated. Unknown consumers abstain `dataframe-pvalue-table-unresolved` or
`unresolved-pvalue-consumer`; the implementation never assumes a method is descriptive.

## 10. False-accusation analysis and required fixture matrix

### 10.1 Load-bearing argument by new admission

| Admission | Strongest correct-analysis attack | Rule that blocks a false candidate |
|---|---|---|
| Off-slice record noise | A correct analysis builds unrelated arbitrary records beside raw family conclusions. | Only p-derived/on-slice records enter the graph; global correction/statistics/test censuses still see relevant calls. |
| Record construction | One record field contains raw p and another contains a corrected p, with output selecting the corrected field. | Field-specific origins plus total consumer accounting; unresolved/competing origin never collapses to raw. |
| Flag fold | A flag is inverted, overwritten, or produced by an unknown correction and later printed. | Exact `D`/`REJECT` origin and arm-polarity pairing; ambiguity abstains. |
| Duplicate emission | First sink prints raw significance while the second prints a corrected decision. | Both normalized decisions must be identical; raw/adjusted or threshold disagreement abstains. |
| Positional subset | A slice or filter is off by one and omits/duplicates a corrected member. | Exact half-open bounds, order and correction-input equality; no runtime clamping/inference. |
| Mixed dispatch | One outcome is tested twice or an unregistered/custom branch handles one table token. | Whole-module source-call census plus exactly-one selected registered call for every position. |
| DataFrame table | A complete corrected family is stored beside raw p, or a live p-derived mask chooses which rows are corrected. | Field/column origin equality, exact static masks only, total table consumers, hierarchy guard. |
| D14-A | A hidden correction/call is placed in the singleton binding row. | Row components must be direct operand projections; calls/arithmetic fail the cardinality production. |

No fixture is allowed to pass merely because its words say “corrected,” “raw,” “primary,” or
“significant.” All expected outcomes derive from structure and recognized APIs.

### 10.2 Named executed fixtures

Every fixture executes the public 3.0 analyzer or adapter. The **39 correct-analysis fixtures**
below must produce zero candidates and zero Findings.

#### D14-A — 6 correct fixtures

1. `correct-d14-a-whole-family-hand-bonferroni` -> `covered/complete`;
2. `correct-d14-a-call-component-refused` -> `test-battery-cardinality-unresolved`;
3. `correct-d14-a-two-row-generator-refused` -> same;
4. `correct-d14-a-filtered-generator-refused` -> same;
5. `correct-d14-a-container-kind-mismatch-refused` -> same; and
6. `correct-d14-a-arithmetic-component-refused` -> same.

#### Record accumulation — 10 correct fixtures

1. `correct-record-raw-adjusted-field-merge` -> `record-family-lineage-unresolved`;
2. `correct-record-flag-polarity-inverted` -> `record-decision-polarity-unresolved`;
3. `correct-record-conditional-construction` -> `record-family-mutation-unresolved`;
4. `correct-record-loop-carried-store` -> `record-family-mutation-unresolved`;
5. `correct-record-alias-mutation` -> `record-family-mutation-unresolved`;
6. `correct-record-collection-reassigned` -> `record-family-mutation-unresolved`;
7. `correct-record-heterogeneous-schema` -> `record-family-lineage-unresolved`;
8. `correct-record-two-competing-nested-records` -> `record-family-lineage-unresolved`;
9. `correct-record-opaque-cross-function-return` -> an unchanged X4 reason; and
10. `correct-record-duplicate-raw-vs-adjusted-emissions` ->
    `record-duplicate-conclusion-ambiguous`.

Positive controls are `positive-record-dict-flag-fold`,
`positive-record-tuple-wrapper-duplicate-emission`, and
`positive-record-r4-raw-family`; each emits exactly one candidate/`none`, zero Findings, and one
conclusion position per member.

#### Positional subset — 6 correct fixtures

1. `correct-record-subset-off-by-one` -> `record-subset-position-unresolved`;
2. `correct-record-subset-negative-bound` -> same;
3. `correct-record-subset-nonunit-step` -> same;
4. `correct-record-subset-dynamic-bound` -> same;
5. `correct-record-subset-pderived-filter` -> `hierarchical-gatekeeping-present`; and
6. `correct-record-subset-correction-position-mismatch` ->
   `correction-family-lineage-unresolved`.

Positive controls are `positive-record-prefix-holm-strict-subset` and
`positive-record-static-flag-holm-strict-subset`, each with pinned corrected positions.

#### Mixed API — 7 correct fixtures

1. `correct-mixed-api-complete-holm` -> `covered/complete`;
2. `correct-mixed-api-unregistered-arm` -> `family-test-api-dispatch-unresolved`;
3. `correct-mixed-api-dynamic-selector` -> same;
4. `correct-mixed-api-double-test-one-position` ->
   `multiple-registered-tests-for-family-member`;
5. `correct-mixed-api-operand-mismatch` -> `test-operand-lineage-unresolved`;
6. `correct-mixed-api-live-scientific-gate` -> `hierarchical-gatekeeping-present`; and
7. `correct-mixed-api-alias-rebound` -> `api-resolution-ambiguous`.

Positive controls are `positive-mixed-api-raw-family` -> candidate/`none` and
`positive-mixed-api-prefix-holm` -> candidate/`strict_subset`.

#### DataFrame — 10 correct fixtures

1. `correct-dataframe-whole-family-default-multipletests` -> `covered/complete`;
2. `correct-dataframe-hand-sidak` -> `unresolved-decision-threshold`;
3. `correct-dataframe-live-panel-gate` -> `hierarchical-gatekeeping-present`;
4. `correct-dataframe-alias-escape` -> `dataframe-pvalue-table-unresolved`;
5. `correct-dataframe-row-sort` -> same;
6. `correct-dataframe-dynamic-loc-store` -> same;
7. `correct-dataframe-raw-adjusted-column-merge` -> same; and
8. `correct-dataframe-export-sibling` -> `unresolved-pvalue-consumer`;
9. `correct-dataframe-isna-helper-hidden-correction` -> `unresolved-pvalue-consumer`; and
10. `correct-dataframe-format-lambda-arithmetic` -> `dataframe-pvalue-table-unresolved`.

Positive controls are `positive-dataframe-raw-family` -> candidate/`none` and
`positive-dataframe-prefix-holm` -> candidate/`strict_subset`.

The existing 22 historical FA fixtures remain exact. The combined noncandidate gate is therefore
`25` labeled-correct corpus cases + `45` opened negatives + `22` historical FA fixtures + `39` new
correct fixtures = **131 executions, zero candidates and zero Findings**. Counts overlap by design
only across source meaning, never by test execution; the gate reports each group separately.

### 10.3 Revision-1a executed trigger-shape census

The strict census contains exactly **41** baseline non-candidates with at least one new-model
trigger: the nine DataFrame cases pinned in 9.1, corpus `spec-22` and `spec-44` with dispatch shapes,
and the remaining record-accumulation shapes. Nine trigger rows move; 32 retain the named wall
below. D14-A's E14 P3 movement is outside this trigger census, giving ten total section-12/13
movements. Every row is recorded canonically in `prototype-sweep/results.json`.

| Case | Trigger | Executed 3.0 shadow outcome | Status |
|---|---|---|---|
| `E10:N1:cb2e207276a0dc3247bb` | record | covered `complete` | surviving coverage |
| `E10:N2:9be74afbe9659bd50580` | record | abstain `unresolved-decision-threshold` | surviving wall |
| `E10:N4:60f96fabb7129d662b23` | record | abstain `extra-registered-test-outside-authorized-family` | surviving wall |
| `E10:N5:8d83210468ecde012e4a` | record | abstain `test-battery-cardinality-unresolved` | surviving wall |
| `E10:N7:6d2fdc67ab98bc0e0e6e` | DataFrame + record | abstain `statistics-api-imported-outside-analysis-py` | surviving adapter wall |
| `E11:P5:114782f595d9c24b923d` | DataFrame + record | candidate `strict_subset {0,1}/7` | movement |
| `E11:N3:479317f1706d4fb929e5` | DataFrame + record | abstain `unresolved-manual-correction-present` | surviving wall |
| `E11:N4:10e0cfb0c7ba8d03ec52` | record | abstain `extra-registered-test-outside-authorized-family` | surviving wall |
| `E11:N8:53c4753f38f9e253d541` | record | abstain `test-battery-cardinality-unresolved` | surviving wall |
| `E11:N9:08565c720304eb6fd9d3` | record | abstain `unresolved-decision-threshold` | surviving wall |
| `E12:P1:f9ce4de5e21d9015ecd9` | DataFrame | candidate `none` | movement |
| `E12:P5:54667dd7c39067c8c2c8` | record | candidate `strict_subset {0,1}/7` | movement |
| `E12:N1:45c4b9a19d0a630f1cb0` | DataFrame + record | covered `complete` | safe movement |
| `E12:N2:f256af2f5c5d98f37e65` | DataFrame + record | abstain `unresolved-decision-threshold` | safe movement |
| `E12:N3:678e94e79226936fd647` | DataFrame + record | abstain `unresolved-manual-correction-present` | surviving wall |
| `E12:N5:6108263527580cd01608` | record | abstain `test-battery-cardinality-unresolved` | surviving wall |
| `E12:N6:db193771248850b81b25` | record | abstain `test-battery-cardinality-unresolved` | surviving wall |
| `E12:N9:62aa3748aa0c7c2607d3` | DataFrame + record | abstain `test-battery-cardinality-unresolved` | surviving wall |
| `E13:N1:b7d38f6e9284abfd3ee6` | record | abstain `correction-family-lineage-unresolved` | surviving wall |
| `E13:N3:c15f507ad59999fd9371` | record | abstain `unresolved-manual-correction-present` | surviving wall |
| `E13:N4:cfbb5edfd1534e7419fd` | record | abstain `extra-registered-test-outside-authorized-family` | surviving wall |
| `E13:N5:8f37c5176ab3c0a61e4d` | record | abstain `test-battery-cardinality-unresolved` | surviving wall |
| `E14:P2:4fc0f5c1ef2d0e2cd5b6` | record | candidate `none` | movement |
| `E14:P4:cccde3c60f936e077f80` | mixed dispatch + record | candidate `none` | movement |
| `E14:P5:5e33841b96d85ffe67be` | mixed dispatch + record | candidate `strict_subset {0,1}/6` | movement |
| `E14:P6:94786af7eca95fff6d78` | record | abstain `unresolved-manual-correction-present` | surviving wall |
| `E14:N3:2327c03c4ddd02a36b97` | DataFrame | abstain `authorized-family-test-census-incomplete` | surviving wall |
| `E14:N4:f80bac8b4bd7442917c5` | record | abstain `extra-registered-test-outside-authorized-family` | surviving wall |
| `E14:N6:1baacbeace56bb5d7b0f` | record | abstain `authorized-family-test-census-incomplete` | surviving wall |
| `E14:N7:470aaf22deaf023aaae6` | record | abstain `authorized-family-test-census-incomplete` | surviving wall |
| `E14:N8:c3191c18f72145cde01c` | record | abstain `authorized-family-test-census-incomplete` | surviving wall |
| `E14:N9:5d5d4e0189d4f2c73f6a` | record | abstain `hierarchical-gatekeeping-present` | safe deeper-wall movement |
| `corpus:spec-02` | record | abstain `correction-family-lineage-unresolved` | surviving wall |
| `corpus:spec-04` | record | abstain `correction-family-lineage-unresolved` | surviving wall |
| `corpus:spec-22` | mixed dispatch + record | abstain `authorized-family-test-census-incomplete` | surviving wall |
| `corpus:spec-23` | record | abstain `pvalue-scalar-cast-or-rounding-unsupported` | surviving wall |
| `corpus:spec-24` | record | abstain `correction-family-lineage-unresolved` | surviving wall |
| `corpus:spec-29` | record | abstain `unresolved-decision-threshold` | surviving wall |
| `corpus:spec-32` | record | abstain `extra-registered-test-outside-authorized-family` | surviving wall |
| `corpus:spec-34` | record | abstain `test-battery-cardinality-unresolved` | surviving wall |
| `corpus:spec-44` | mixed dispatch | abstain `authorized-family-test-census-incomplete` | surviving wall |

`spec-22` and `spec-44` select APIs from input-derived values, so section 8.2 refuses a static
dispatch plan. With no plan, fewer than `N` execution instances resolve and the earlier
`authorized-family-test-census-incomplete` wall remains first. Their global statistics-prefix
census is a second independent wall. This is the build gate that prevents a future implementation
from treating data-dependent API selection as an admitted table dispatch.

## 11. Guard ownership, fail-closed reasons, and closed registry

### 11.1 Guard ownership

| Guard | Trigger source | 3.0 disposition |
|---|---|---|
| Registered test/sensitivity/dead calls | untouched source census plus execution-instance plan | Mixed dispatch changes only exact position mapping; extra/fewer/double calls remain abstentions. |
| Correction terminal/statistics/dynamic/API rebind | untouched whole module | Byte-unchanged registries and substance. |
| Operand and row completeness | backward slices from each selected call | Unchanged. Every mixed branch proves both operands independently. |
| Outcome-sequence mutation | untouched module and alias closure | Unchanged; record/table membership cannot repair an unstable outcome table. |
| Record/collection/DataFrame | forward slice plus symbolic record graph | New exact productions; every unresolved edge abstains. |
| Extremum/export/upstream | forward slice and sinks | Unchanged; record or DataFrame storage does not exempt export/extremum. |
| Correction/manual/threshold | p/record/table slices plus source bindings | Grammar unchanged. Section 7 supplies positions only. |
| Hierarchy/control/prevention | whole-module controls plus backward provenance | Unchanged in substance; record flags/table masks are excluded only after exact static folding or display-only proof. |
| Resampling/partition/inference | global census and slices | Unchanged. |
| Conclusions | total forward slice | Adds exact record/table transports and equivalent duplicate emission; no new threshold or sink kind. |

`_hierarchy_guard` should be copied into v3.0 byte-for-byte unless the builder must accept the new
side-table exclusion interface. If an interface copy is necessary, its control-node enumeration,
provenance test, early-exit set, reasons, and decisions remain extensionally byte-equivalent on all
2.3 fixtures. Any substantive subtraction is out of scope.

### 11.2 New, retired, and surviving reasons

New reasons:

```text
family-test-api-dispatch-unresolved
multiple-registered-tests-for-family-member
record-family-lineage-unresolved
record-family-mutation-unresolved
record-decision-polarity-unresolved
record-duplicate-conclusion-ambiguous
record-subset-position-unresolved
dataframe-pvalue-table-unresolved
```

`mixed-test-api-family` is retired in 3.0 because a resolved mixed registered family is now
admissible. It remains frozen in 1.x/2.x records and must never be compared across versions as the
same predicate. No surviving reason is relabeled. `pvalue-family-collection-unresolved` remains for
unsupported non-record/parallel/dynamic family collections.

The 3.0 closed set has **61 reasons**: the 54-reason 2.3 set, minus the one retired reason, plus the
eight new reasons:

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
family-test-api-dispatch-unresolved
multiple-registered-tests-for-family-member
test-operand-lineage-unresolved
selected-group-row-completeness-unproven
upstream-correction-lineage-unresolved
pvalue-family-collection-unresolved
record-family-lineage-unresolved
record-family-mutation-unresolved
record-decision-polarity-unresolved
record-duplicate-conclusion-ambiguous
record-subset-position-unresolved
dataframe-pvalue-table-unresolved
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

The documented-unreachable annex for `conclusion-output-sink-unavailable` remains. Public v3.0
emitter fixtures plus that annex must be set-equal to this list. A reason literal in an older test
cannot satisfy v3.0 coverage.

## 12. Adapter oracle for all 75 opened envelope cases

Exactly **ten** opened rows move from the active 2.3 classification/reason map. Six are positive
misses becoming candidates; three are correct/negative cases moving safely to covered/deeper
abstention; one is D14-A's positive miss moving one wall deeper. Every other opened row is byte-semantically equal
in outcome, reason/classification, positions, and candidate count.

### 12.1 Envelope 10 — 0 movements, executed shadow recall 5/6

| Role / case | 3.0 adapter outcome |
|---|---|
| P1 `ebbb8a5dbc2664257144` | abstain `authorized-reader-lineage-unavailable` |
| P2 `104493a5d99796a002c0` | candidate `none` |
| P3 `3ff45fce2a45e0959fdb` | candidate `none` |
| P4 `7296b0e2cf7faeefca64` | candidate `none` |
| P5 `c51d08801b3d0ba4e532` | candidate `strict_subset` |
| P6 `f4cf62caeb8ad68dc5b3` | candidate `strict_subset` |
| N1 `cb2e207276a0dc3247bb` | covered `complete` |
| N2 `9be74afbe9659bd50580` | abstain `unresolved-decision-threshold` |
| N3 `b787314c170f8f690060` | abstain `unresolved-manual-correction-present` |
| N4 `60f96fabb7129d662b23` | abstain `extra-registered-test-outside-authorized-family` |
| N5 `8d83210468ecde012e4a` | abstain `test-battery-cardinality-unresolved` |
| N6 `4907932548f745afe942` | abstain `authorized-family-test-census-incomplete` |
| N7 `6d2fdc67ab98bc0e0e6e` | abstain `statistics-api-imported-outside-analysis-py` at adapter level |
| N8 `dfc9f20a94ecefc7f7b5` | abstain `test-battery-cardinality-unresolved` |
| N9 `e1bce32a32e3b2df475e` | abstain `unresolved-decision-threshold` |

### 12.2 Envelope 11 — 1 movement, executed shadow recall 6/6

| Role / case | 3.0 adapter outcome | Movement |
|---|---|---|
| P1 `8726b87ac4ba4c34c0a3` | candidate `none` | unchanged |
| P2 `6f08fe90c58e51737a4d` | candidate `none` | unchanged |
| P3 `69c5d0aec76eefb67148` | candidate `none` | unchanged |
| P4 `dfd35001c5a99ab1486b` | candidate `none` | unchanged |
| P5 `114782f595d9c24b923d` | candidate `strict_subset`, positions `{0,1}` of `7` | **DataFrame movement** from `unresolved-pvalue-consumer` |
| P6 `0249919d05de1abc25fd` | candidate `strict_subset` | unchanged |
| N1 `d1533e4a8bbd10cb727e` | covered `complete` | unchanged |
| N2 `d11a7136d1e91ed8e26f` | abstain `unresolved-decision-threshold` | unchanged |
| N3 `479317f1706d4fb929e5` | abstain `unresolved-manual-correction-present` | unchanged |
| N4 `10e0cfb0c7ba8d03ec52` | abstain `extra-registered-test-outside-authorized-family` | unchanged |
| N5 `2a712805024597719d32` | abstain `test-battery-cardinality-unresolved` | unchanged |
| N6 `1cce7d6b580caa25f597` | abstain `authorized-family-test-census-incomplete` | unchanged |
| N7 `9bccc428f23dde0d43f0` | abstain `authorized-family-test-census-incomplete` | unchanged |
| N8 `53c4753f38f9e253d541` | abstain `test-battery-cardinality-unresolved` | unchanged |
| N9 `08565c720304eb6fd9d3` | abstain `unresolved-decision-threshold` | unchanged |

### 12.3 Envelope 12 — 4 movements, executed shadow recall 6/6

| Role / case | 3.0 adapter outcome | Movement |
|---|---|---|
| P1 `f9ce4de5e21d9015ecd9` | candidate `none` | **DataFrame/duplicate-emission movement** from `unresolved-pvalue-consumer` |
| P2 `e07a6f2a895079b53b8c` | candidate `none` | unchanged |
| P3 `e28a9537b07c74d21838` | candidate `none` | unchanged from 2.2/2.3 |
| P4 `0ec89f70a9776d1a1931` | candidate `none` | unchanged |
| P5 `54667dd7c39067c8c2c8` | candidate `strict_subset`, positions `{0,1}` of `7` | **record/filter/flag movement** from `pvalue-family-collection-unresolved` |
| P6 `68d1a6f5b1ab70f2650a` | candidate `strict_subset`, positions `{0,1}` of `5` | unchanged from 2.2/2.3 |
| N1 `45c4b9a19d0a630f1cb0` | covered `complete`, positions `{0,1,2,3,4}` | **safe DataFrame movement** from `unresolved-pvalue-consumer` |
| N2 `f256af2f5c5d98f37e65` | abstain `unresolved-decision-threshold` | **safe deeper-wall movement** from `unresolved-pvalue-consumer` |
| N3 `678e94e79226936fd647` | abstain `unresolved-manual-correction-present` | unchanged |
| N4 `c37c0fa6e462a22cb6d5` | abstain `authorized-family-test-census-incomplete` | unchanged |
| N5 `6108263527580cd01608` | abstain `test-battery-cardinality-unresolved` | unchanged |
| N6 `db193771248850b81b25` | abstain `test-battery-cardinality-unresolved` | unchanged |
| N7 `190ca375ac7c481c3e08` | abstain `authorized-family-test-census-incomplete` | unchanged |
| N8 `7fd5f9dcd4097c1e5a03` | abstain `authorized-family-test-census-incomplete` | unchanged |
| N9 `62aa3748aa0c7c2607d3` | abstain `test-battery-cardinality-unresolved` | unchanged |

### 12.4 Envelope 13 — 0 movements, executed shadow recall 4/6

| Role / case | 3.0 adapter outcome |
|---|---|
| P1 `686d1432762cd49d9b54` | candidate `none` |
| P2 `c336be2521785ab6a954` | abstain `extra-registered-test-outside-authorized-family` |
| P3 `4f042d10b3f9a43d1099` | candidate `none` |
| P4 `ffbe12246cf8a4227210` | candidate `none` |
| P5 `80091f37c722eba28e18` | candidate `strict_subset`, positions `{0,1}` of `7` |
| P6 `d0f9fcd52f47e4d64668` | abstain `unresolved-manual-correction-present` |
| N1 `b7d38f6e9284abfd3ee6` | abstain `correction-family-lineage-unresolved` |
| N2 `f65170c644b90c4a893c` | abstain `unresolved-decision-threshold` |
| N3 `c15f507ad59999fd9371` | abstain `unresolved-manual-correction-present` |
| N4 `cfbb5edfd1534e7419fd` | abstain `extra-registered-test-outside-authorized-family` |
| N5 `8f37c5176ab3c0a61e4d` | abstain `test-battery-cardinality-unresolved` |
| N6 `6a102a97a065f9c8879f` | abstain `authorized-reader-lineage-unavailable` |
| N7 `aba768f8d0b3f3548683` | abstain `authorized-family-test-census-incomplete` |
| N8 `325c686a92196956359a` | abstain `test-battery-cardinality-unresolved` |
| N9 `ab70cdb37bb2977d725c` | abstain `unresolved-decision-threshold` |

E13 P2 remains `>N`; record duplicate-emission does not collapse duplicate **test calls**. E13 P6
remains the proper-subset manual-factor residual.

### 12.5 Envelope 14 — 5 movements, executed shadow recall 4/6

| Role / case | 3.0 adapter outcome | Movement/full ladder |
|---|---|---|
| P1 `9ed744e25f1f1c55f8ca` | candidate `none` | unchanged |
| P2 `4fc0f5c1ef2d0e2cd5b6` | candidate `none` | **record flag + equivalent duplicate emissions** from `pvalue-family-collection-unresolved` |
| P3 `502687d9137dab93ff99` | abstain `unresolved-decision-threshold` | **D14-A single reason movement**; Dict-keyed record map stays outside section 6 |
| P4 `cccde3c60f936e077f80` | candidate `none` | **mixed dispatch -> record p/flag -> two equivalent emissions/display aggregate -> candidate** |
| P5 `5e33841b96d85ffe67be` | candidate `strict_subset`, positions `{0,1}` of `6` | **mixed dispatch -> exact prefix slice -> Holm positions/write-back through unchanged R16 -> raw/adjusted flag fold -> candidate** |
| P6 `94786af7eca95fff6d78` | abstain `unresolved-manual-correction-present` | unchanged proper-subset factor |
| N1 `aabf005414b9ae164c0b` | abstain `authorized-family-test-census-incomplete` | unchanged repeated-`_` table binding |
| N2 `c83b4021527fa98dadf3` | abstain `authorized-family-test-census-incomplete` | unchanged repeated-`_` table binding |
| N3 `2327c03c4ddd02a36b97` | abstain `authorized-family-test-census-incomplete` | unchanged repeated-`_` table binding |
| N4 `f80bac8b4bd7442917c5` | abstain `extra-registered-test-outside-authorized-family` | unchanged |
| N5 `e987fc7ceafb6acb7a75` | abstain `test-battery-cardinality-unresolved` | unchanged |
| N6 `1baacbeace56bb5d7b0f` | abstain `authorized-family-test-census-incomplete` | unchanged live stage gate |
| N7 `470aaf22deaf023aaae6` | abstain `authorized-family-test-census-incomplete` | unchanged zero registered family |
| N8 `c3191c18f72145cde01c` | abstain `authorized-family-test-census-incomplete` | unchanged zero registered family |
| N9 `5d5d4e0189d4f2c73f6a` | abstain `hierarchical-gatekeeping-present` | **safe reason exposure** from `unresolved-pvalue-consumer`; its p-derived runtime filter remains a scientific control edge |

The exact opened movement set is:

```text
E11:P5:114782f595d9c24b923d
E12:P1:f9ce4de5e21d9015ecd9
E12:P5:54667dd7c39067c8c2c8
E12:N1:45c4b9a19d0a630f1cb0
E12:N2:f256af2f5c5d98f37e65
E14:P2:4fc0f5c1ef2d0e2cd5b6
E14:P3:502687d9137dab93ff99
E14:P4:cccde3c60f936e077f80
E14:P5:5e33841b96d85ffe67be
E14:N9:5d5d4e0189d4f2c73f6a
```

Movement-set equality is a hard gate.

## 13. Open-corpus oracle — all 50 rows

This table is **adapter-level**. In particular, `spec-30` is pinned
`api-resolution-ambiguous` here even though the analyzer-only diagnostic reads
`unresolved-manual-correction-present`; builders must not substitute the analyzer row for the
adapter oracle.

No corpus row moves. The 3.0 result map is exactly equal to the frozen 2.1/2.2/2.3 comparison map:

| Case | 3.0 outcome | Case | 3.0 outcome |
|---|---|---|---|
| spec-01 | candidate `none` | spec-02 | abstain `correction-family-lineage-unresolved` |
| spec-03 | candidate `none` | spec-04 | abstain `correction-family-lineage-unresolved` |
| spec-05 | candidate `none` | spec-06 | abstain `unresolved-decision-threshold` |
| spec-07 | candidate `none` | spec-08 | abstain `extra-registered-test-outside-authorized-family` |
| spec-09 | candidate `none` | spec-10 | abstain `helper-body-statement-unsupported` |
| spec-11 | candidate `none` | spec-12 | abstain `test-battery-cardinality-unresolved` |
| spec-13 | abstain `test-battery-cardinality-unresolved` | spec-14 | abstain `test-operand-lineage-unresolved` |
| spec-15 | candidate `none` | spec-16 | abstain `authorized-family-test-census-incomplete` |
| spec-17 | candidate `none` | spec-18 | abstain `test-battery-cardinality-unresolved` |
| spec-19 | candidate `none` | spec-20 | abstain `unresolved-decision-threshold` |
| spec-21 | candidate `strict_subset` | spec-22 | abstain `authorized-family-test-census-incomplete` |
| spec-23 | abstain `pvalue-scalar-cast-or-rounding-unsupported` | spec-24 | abstain `correction-family-lineage-unresolved` |
| spec-25 | candidate `none` | spec-26 | abstain `correction-family-lineage-unresolved` |
| spec-27 | candidate `none` | spec-28 | abstain `unresolved-decision-threshold` |
| spec-29 | abstain `unresolved-decision-threshold` | spec-30 | abstain `api-resolution-ambiguous` |
| spec-31 | candidate `none` | spec-32 | abstain `extra-registered-test-outside-authorized-family` |
| spec-33 | candidate `none` | spec-34 | abstain `test-battery-cardinality-unresolved` |
| spec-35 | candidate `none` | spec-36 | abstain `test-operand-lineage-unresolved` |
| spec-37 | abstain `selected-group-row-completeness-unproven` | spec-38 | abstain `authorized-family-test-census-incomplete` |
| spec-39 | abstain `api-resolution-ambiguous` | spec-40 | abstain `test-battery-cardinality-unresolved` |
| spec-41 | candidate `none` | spec-42 | abstain `unresolved-manual-correction-present` |
| spec-43 | candidate `strict_subset` | spec-44 | abstain `authorized-family-test-census-incomplete` |
| spec-45 | candidate `none` | spec-46 | abstain `correction-family-lineage-unresolved` |
| spec-47 | abstain `unresolved-decision-threshold` | spec-48 | abstain `unresolved-decision-threshold` |
| spec-49 | candidate `none` | spec-50 | abstain `pvalue-family-collection-unresolved` |

All 25 labeled-correct cases remain noncandidates; all 19 existing misstep candidates remain
candidates. The six corpus misses remain:

| Miss | Why 3.0 does not move it |
|---|---|
| spec-13 | concatenated subfamilies/cardinality plus per-member threshold; excluded policy surface |
| spec-23 | `round(P)`; unchanged cast/rounding guard |
| spec-29 | per-member threshold table; unchanged threshold grammar |
| spec-37 | unsupported row selection first, then dynamic-key Dict family map; not a section-6 collection |
| spec-39 | NumPy parallel arrays and positional stores; explicitly outside the record graph |
| spec-47 | per-member Bonferroni-vs-raw threshold selection; unchanged policy narrowing |

`spec-50` is labeled correct and uses parallel raw p arrays plus an off-registry correction. The
record model does not admit those arrays, so its first reason remains byte-identical.

The raw bytes of `adapter_replay_records_v2_1.json` and every prior comparison row are immutable.
The build adds a new canonical 3.0 comparison row set whose `results` map is equal to 2.3, while
its adapter/version/digests are correctly new. Regenerating the frozen record is forbidden.

## 14. Ordering, idempotence, replay, and validation plan

### 14.1 Non-mutating graph and transformer order

The untouched tree `T0` feeds all global censuses. Existing transformations retain their 2.3
order. D14-A contributes one symbolic comprehension binding before final outcome expansion and D2
occurrence checking. The new mixed dispatch plan is derived from `T0`; it is not created by
unparsing or branch deletion.

After existing X4, D2, two identical D6 calls, literal destructuring, outcome expansion, R4/R15,
record-loop expansion, and D13 terminal closure, the 3.0 record builder reads the normalized AST and
source-origin markers into side tables. Positional and DataFrame views are side-table transforms.
They never mutate AST identity used by correction/threshold/hierarchy/conclusion guards.

Run each of the following twice and compare canonical bytes:

1. D14-A symbolic normalization;
2. dispatch execution-instance planning;
3. record graph construction, including ordered duplicate occurrences;
4. subset derivation;
5. DataFrame row/column graph construction; and
6. total-consumer accounting.

The second run on the same input changes nothing. Running the record graph over its own canonical
descriptors also changes nothing. Source occurrence multiplicity, field order, row order, and
duplicate emission spans are part of equality; set equality is insufficient.

### 14.2 Ladder and terminal-oracle gates

Every committed rung under the corpus20, E12, E13, and E14 recon roots executes. Existing pinned
expectations remain unless sections 12 or 13 list the source as a movement. In particular:

- E14 P2's source becomes candidate while its no-second-pass and no-collection rungs remain
  candidate;
- E14 P3 source becomes `unresolved-decision-threshold`; later simplification rungs retain their
  existing deeper outcomes/candidate control;
- E14 P4 source becomes candidate only when both exact dispatch and record flag/duplicate-output
  rules agree;
- E14 P5 source becomes `strict_subset {0,1}/6` only when dispatch, positional mapping, unchanged
  R16 transport, and record decision mapping all agree;
- E12 P5 source becomes `strict_subset {0,1}/7`; and
- DataFrame opened/correct controls reach the exact section-12 results.

Any half-implemented mixed dispatch, positional mapping, record flag, correction write-back, or
DataFrame consumer rule is a design regression, not an acceptable partial delta.

### 14.3 Opened/corpus replay gates

The build executes at adapter level:

1. all 75 opened cases twice, with the exact ten-row movement set;
2. all 50 corpus cases twice, with exact result-map equality to frozen 2.3;
3. all 45 opened negatives with zero candidates;
4. all 25 corpus-correct cases with zero candidates;
5. the exact retro recalls `5/6, 6/6, 6/6, 4/6, 4/6` for E10..E14;
6. explicit frozen 1.0/1.1/2.0/2.1/2.2/2.3 adapters over their historical anchors; and
7. a new frozen 2.3 replay anchor importing the four pinned 2.3 modules explicitly, never through
   the active development binding.

The build also reruns the checked-in Revision-1a shadow sweep as a differential gate: exactly 125
case rows, 48 fixture rows, 41 trigger rows, ten movements, the section-10.3 named walls, and
none-flips `0/25`, `0/45`, `0/39`. The production adapter must be outcome-equal to the shadow
oracle; the shadow code is evidence, not a production dependency.

Candidate fixtures emit exactly one evaluation candidate and zero Findings. Covered fixtures emit
zero candidates. Every audit replays byte-identically.

### 14.4 Prose tripwire and identifier channels

The 2.3 tripwire remains and covers every new predicate/fixture. Independently mutate comments,
docstrings, reports, Markdown, task text, annotations, unrelated strings, output labels, format
text, and non-callee identifiers; add/remove report and Markdown files. Rename non-callee names
through correction/API-looking spellings. Classification, facts, positions, and first reasons stay
equal.

Paired structural controls mutate one slot at a time:

- literal record key to dynamic key;
- p-lineage field to unrelated scalar and vice versa;
- same-kind records to heterogeneous records;
- one nested record to two;
- static slice bound to arithmetic/dynamic/off-by-one bound;
- table flag to p-derived flag;
- identical duplicate decision to raw/adjusted or opposite-polarity decisions;
- static API selector token to a call/dynamic value;
- one registered branch call to unregistered or double call;
- DataFrame static column to dynamic column;
- row-preserving table operation to row reorder/filter; and
- p-result sink to export/unknown consumer.

Selector tokens are compared for exact structural equality but never interpreted. Consistently
renaming every selector token leaves results equal. Record/DataFrame keys are literal addressing
channels only; consistently renaming keys and their static accesses leaves results equal. Contract
outcome values remain the sole exception where exact value establishes family position. Display
strings retain the 256-byte measured-never-inspected boundary from 2.1.

### 14.5 Closed set, evidence, differential, and quality gates

- v3.0 emitter fixtures plus the documented-unreachable annex are set-equal to the 61 reasons.
- Evidence v2 validators reject wrong length/order, unregistered APIs, `performed_count != N`,
  duplicate/missing positions, or inconsistent correction counts.
- Wording v2 slot/schema/digest tests prove no `TEST_API` dependency and no text-derived fact.
- Contract 1.0/1.1/1.2 goldens and all seven error categories remain byte-equal.
- The two-registry differential and non-derivation gate from section 2.5 passes.
- Registry/ledger/source manifests are regenerated after the final implementation/test change in
  the repository-prescribed order; the custodian performs any committed-tree manifest follow-up.
- `ruff check .`, `ruff format --check .`, `mypy src`, full `pytest`, and
  `python scripts/validate_starter.py` pass fresh.

## 15. Residuals, honest read, and promotion arithmetic

### 15.1 Explicit residuals

The following remain out of scope:

1. **Zip write-back dual polarity.** Only unchanged R16 applies after positions are independently
   proved. No new zip argument, polarity, or cardinality form is admitted.
2. **Proper-subset manual factor.** E13 P6 and E14 P6 remain
   `unresolved-manual-correction-present`. Recognizing `P*K` for `K<N` can create strict-subset
   accusations and needs its own policy ADR.
3. **`P < ALPHA/K` coverage.** This remains the standing future correction-policy ADR candidate.
4. **Dict-keyed dynamic family maps.** E14 P3 and corpus spec-37 do not enter section 6.
5. **Parallel arrays and positional stores.** Corpus spec-39/spec-50 remain outside the model.
6. **General DataFrame semantics.** Anything beyond section 9 remains fail-closed.

### 15.2 Executed shadow recall

The exact executed-shadow result is:

```text
open corpus:  correct 0/25 candidates; misstep 19/25 candidates (unchanged)
E10 retro:    5/6
E11 retro:    6/6
E12 retro:    6/6
E13 retro:    4/6
E14 retro:    4/6
opened total: 25/30 positive candidates
```

Compared with active 2.3 (`5,5,4,4,1`), 3.0 adds six retrospective positive catches: E11 P5,
E12 P1/P5, and E14 P2/P4/P5. It also makes four safe reason/state movements: E12 N1 becomes
covered, E12 N2 exposes its threshold wall, E14 P3 exposes the D14-A threshold wall, and E14 N9
exposes `hierarchical-gatekeeping-present` after its record transport resolves. Total
classification/reason movements over 75 opened plus 50 corpus cases are **10 of 125**.

### 15.3 E15 arrival expectation

The projection demonstrates that a designed record layer can clear several recurring opened
families at once. It does not establish blind E15 recall. Fresh authors have repeatedly moved to a
new earlier wall after a prior wall was closed. A reasonable planning range is `2/6` to `4/6`, with
`4/6` supported as a known-case capability but not as a first-contact prediction. Envelope 15 must
measure fresh first contact without hints about records, dispatch, DataFrames, or avoided guards.

### 15.4 Promotion arithmetic

The sealed trailing window remains E12 `2/6` + E13 `3/6` + E14 `1/6` = **6/18**. Retrospective
3.0 reclassification does not alter blind credit.

When E15 arrives, sealed E12 drops out; E13+E14 retain four catches. Immediate promotion at the
`9/18` bar therefore requires E15 `5/6`. If E15 scores `4/6`, the window is `8/18`; if `3/6`, it is
`7/18`.

Across E15 and E16, E14 remains, so the two envelopes must contribute at least `8/12`: `4+4`,
`5+3`, `3+5`, `2+6`, or better. The opened 3.0 projection over E12-E14 is `14/18`, which shows the
**recognizer capacity** can exceed a `4/6` average on already-seen record families. The sealed
arrival series `2,3,1` does **not** show that fresh envelopes will average `4/6`. Therefore the
projection supports a 4/6-average engineering target, but not a promotion forecast or an arrival
prior of 4/6.

## 16. Reuse map and file-by-file build list

Shared modules are copied, never edited.

| File/surface | Required 3.0 change |
|---|---|
| ADR-0079 | Append the accepted section-2.4 record/mixed-API/evidence/wording decision. |
| New `code_csv_multiple_testing_dataflow_v3.py` | Versioned 2.3 copy implementing sections 3-11 and D14-A; no dependence-module import/edit. |
| New `code_csv_multiple_testing_adapter_v3.py` | Version 3.0.0, evidence profile v2, 61-reason closed registry. |
| New bounded detector/integration `_v3` modules | Version 3.0.0 development-only wrappers; unchanged operand guards. |
| `method_conflict_finding.py` | Add wording v2 beside byte-frozen v1 and select it only for the exact 3.0 binding. |
| profiles/registry/controller development resources | Register historical 2.3 plus 3.0; advance only active development binding. |
| New `evaluation/development/multitest-code-slice-v3/` | Fixture matrix, development ledger, graph/dispatch/DF oracle manifests; answer-visible only. |
| Frozen Revision-1a prototype sweep | Replay `prototype-sweep/results.json`, all 48 fixture sources, and the 41-row trigger census; production must not import the shadow modules. |
| Open-corpus replay harness | Add explicit 3.0 adapter comparison row; preserve frozen record bytes. |
| E10-E14 replay tests | Add 75-row 3.0 adapter oracle and exact ten-movement assertion; no custody/source/audit edits. |
| New `_v3` test modules | Copy 2.3 suites; add D14-A, record, subset, mixed API, DataFrame, evidence-v2, wording-v2, tripwire, idempotence, set-equality, and frozen-2.3 anchors. Do not retarget old tests. |
| Registry/ledger/source manifests | Regenerate after final change; manifest inventory follow-up follows repository custody rule. |

No project-authored code is executed by the detector. Test/recon harness execution remains an
answer-visible development activity outside the production MPP.

## 17. Build acceptance and stop-and-report conditions

Build acceptance requires, after the final file change:

1. accepted ADR-0079 amendment and exact versioned identities;
2. exact section-3 registries and untouched-tree census receipts;
3. exact D14-A grammar and its one-row movement;
4. exact record graph, ordered multiplicity, mutation closure, flag polarity, duplicate-emission,
   positional-subset, mixed-dispatch, and DataFrame productions;
5. all 39 new correct fixtures noncandidate, all nine positive controls at pinned outcomes, and all
   22 historical FA fixtures unchanged;
6. the 131-execution none-flip gate;
7. all 75 opened rows and exact ten-row movement set plus the 41-row trigger census;
8. E14 P4/P5 full ladders reaching the terminal candidate states, not merely a deeper wall;
9. all 50 corpus rows equal and `0/25` correct / `19/25` misstep;
10. frozen 2.3 component/replay anchors and every prior oracle green;
11. record/dispatch/subset/DataFrame idempotence and total-consumer proofs;
12. evidence-v2 and wording-v2 validation/digest gates;
13. 61-reason set equality with no monkeypatched reachability;
14. prose tripwire and paired structural controls;
15. qualified-lane byte isolation/non-derivation; and
16. fresh repository-required lint, format, type, full-test, and starter-validation gates.

Implementation stops and reports a design regression if any pinned candidate remains an
abstention; any correct/negative becomes a candidate; E12 N1/N2 fail their covered/threshold pins;
the movement set differs; a corpus row moves; one mixed position is double/unknown; a record or
DataFrame consumer cannot be totally accounted; evidence/wording cannot represent mixed APIs
truthfully; or a frozen/qualified byte changes. The builder must not broaden a grammar, weaken a
guard, infer a field meaning, drop a consumer, relabel a surviving reason, edit an oracle, or treat
a deeper abstention as completion.

## 18. Revision log

### Revision 0 — commissioned design

Revision 0:

- defines one closed record graph for list-appended Dict/Tuple/R4 records, exact field stores,
  record flags, and equivalent duplicate emissions;
- defines positional subset identity before strict-subset classification;
- replaces API uniformity with exact registered table-selector dispatch, evidence v2, and wording
  v2 while preserving every former protection;
- includes a minimal bounded DataFrame row-table representation after an explicit FA-boundary
  decision;
- folds D14-A with its executed single movement;
- retains zip write-back expansion, proper-subset factors, `ALPHA/K`, Dict-keyed maps, and parallel
  arrays as residuals;
- pins all 75 opened and 50 corpus cases, exactly nine total movements, six positive retro catches,
  and retro recalls `5/6, 6/6, 6/6, 4/6, 4/6`; and
- specifies frozen 2.3 anchors, 39 new correct fixtures, 131 none-flip executions, idempotence,
  prose, closed-reason, replay, differential, and stop-and-report gates.

### Revision 1a — executed prototype sweep and adversarial-review closure

Revision 1a:

- closes BL-1 with strict executable shadow models for record accumulation, positional subsets,
  mixed registered-API dispatch, and DataFrame p tables, combined with D14-A, over all 125 pinned
  cases and all 48 new fixtures; the canonical replay is `prototype-sweep/results.json`;
- re-pins the design to the executed ten-row movement set. All nine Revision-0 movements are
  confirmed, and E14 N9 is added as a safe reason-exposure movement from
  `unresolved-pvalue-consumer` to `hierarchical-gatekeeping-present`;
- adopts MJ-1's exact 41-row trigger-shape census: nine trigger movements and 32 named surviving
  walls, including the explicit input-derived-dispatch account for `spec-22` and `spec-44`;
- adopts MJ-2 by pinning all nine DataFrame-constructing cases and making every unexpected
  candidate on the seven correct/negative rows a withdrawal condition;
- applies m1 by binding literal-row DataFrame `POS` to section 4.2 route 2, m2 by explicitly
  refusing slice-of-slice, and m3 by identifying the section-13 corpus table as adapter-level and
  documenting the `spec-30` analyzer/adapter split; and
- records executed none-flip counts `0/25` corpus-correct, `0/45` opened negatives, and `0/39` new
  correct fixtures, with retro recall unchanged at `5/6, 6/6, 6/6, 4/6, 4/6`.
