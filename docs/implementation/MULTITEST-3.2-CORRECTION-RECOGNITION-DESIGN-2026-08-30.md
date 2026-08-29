# Multiple-testing 3.2 AP(C, POS) correction-recognition design — 2026-08-30

**Status:** commissioned build-ready design, Revision 0  
**Target:** detector/check/adapter `3.2.0`, development lane only  
**Predecessor:** multiple-testing `3.1.0` question/attestation layer over the `3.0.0` record model  
**Authority:** frozen scientific-requirement contract profile `1.2.0`; no prose-derived authority  
**Scope:** exact Bonferroni adjusted-p and divided-threshold recognition, including bounded record
and cross-field transports  
**Implementation in this session:** none

## 0. Evidence basis, terminology, and prototype/final fidelity

This design is based on:

- the approved 3.0 record-model design and cumulative B1–B5 audit record;
- the approved 3.1 question/attestation design and its 16 independent laundering-adjacent
  fixtures;
- all sealed-then-opened adapter evidence from envelopes E10 through E15;
- all 50 cases in `multitest-open-corpus-v1`;
- the frozen 71-row 3.0 fixture matrix; and
- the strict, executable AP shadow, all-140-case sweep, 168-fixture sweep, canonical results, and
  self-verifying replay under
  `evaluation/development/multitest-code-slice-v3_2/prototype-sweep/`.

The evidence population is exactly **140 source cases**, meaning **90 opened envelope cases plus
50 open-corpus cases**. “140 evidence cases” below always includes those 50 corpus cases; it does
not mean 140 plus another 50.

The following are **executed observations** from `results.json`:

1. exactly two source rows move: `E15:P6:81980e878c1bc8cc216b` and `corpus:spec-28`;
2. E15 P6 moves from `unresolved-manual-correction-present` to candidate `strict_subset`, corrected
   positions `{0,1,3}` of `8`;
3. corpus spec-28 moves from `unresolved-decision-threshold` to covered/`complete`, positions
   `{0,1,2,3}` of `4`;
4. E13 P6's factor `3` for contract `N=5` and E14 P6's factor `4` for contract `N=8` remain
   `unresolved-manual-correction-present`;
5. retro recall is E10 `5/6`, E11 `6/6`, E12 `6/6`, E13 `4/6`, E14 `4/6`, and E15 `3/6`;
6. none-flip is `0/25` corpus-correct, `0/54` opened negatives, and `0/152` correct fixtures;
7. every one of the cumulative 71 3.0 fixture rows is outcome-identical, including `0/62`
   correct-fixture candidates; all nine prior positive controls retain their pinned candidates;
8. all 63 rows in the cumulative seven-field by nine-expression B5 grid remain noncandidates;
9. all 16 independent 3.1 laundering-adjacent controls remain noncandidates;
10. all 18 new AP fixtures reach their pinned result; and
11. the no-attestation question census changes from `14/90 + 10/50 = 24/140` to
    `13/90 + 9/50 = 22/140`, removing exactly E15 P6 and corpus spec-28.

The canonical executed result is
`sha256:330be120d69d0e23f857368c1442459e1c07ff32b62d62df4389112aace447ff`; the complete
26-file prototype inventory is bound by manifest
`sha256:e634625bdd441b694f9e6eea6e156697ff357c2ca957c7713a28143524f341cf`.

The prototype implements the closed grammar in sections 4–6, never executes project code, and
uses a structural surrogate only as a proof device: after an exact AP fold and its exact position
map are proved, the fold is replaced by its raw-p identity and the frozen 3.0 analyzer must prove
the remaining family as candidate/`none`. For an exact cross-field fold, the surrogate removes
only the already-proved atomic target store and rewires its loads to the proved raw origin. This
does not make source rewriting a production technique.

Prototype-to-final fidelity remains asymmetric even though the shadow is intended to implement
the design grammar exactly. A final implementation may be stricter at integration boundaries; a
stricter admission cannot create a false candidate that the shadow did not create, so the
none-flip direction transfers. Positive movements do not transfer. The final implementation must
therefore re-demonstrate E15 P6, corpus spec-28, and every new positive control. A final abstention
on either pinned source candidate/covered row is a section-17 stop just as a candidate on a pinned
noncandidate is; neither implementation nor oracle may be tuned toward the other.

Terms:

- `N` is the exact contract outcome count and exact authorized family count.
- `POS` is one integer in `0..N-1`, order-equal to the contract outcome list.
- `P(POS)` is the exact registered `.pvalue` lineage for `POS`.
- `C` is the exact, nonempty ordered set of positions whose p-values pass through one recognized
  correction production.
- `AP(C,POS)` is the adjusted p-value produced for `POS in C` by that production.
- `T(C,POS)` is the divided Bonferroni threshold used for `POS in C`.
- `D(POS,ORIGIN,OP,THRESHOLD)` retains the 3.0 normalized decision meaning.
- `UNRESOLVED` remains absorbing. No AP rule may erase it.

## 1. Decision and hard boundary

Version 3.2 fills the deliberately absent 3.0 section-6.5 `AP(C,POS)` branch. It recognizes only:

1. `P(POS) * N` or `N * P(POS)`, optionally capped at one by the exact productions in 4.3; and
2. a p decision against exact family-alpha division `ALPHA / N` under 4.4.

Those productions may occur as exact scalar bindings, same-owner record-constructor fields,
same-owner literal-key cross-field stores, and exact per-element sequences accepted by the
existing DataFrame section-9 stores. They create no new family-position route, test API, reader,
row mask, container, conclusion, display, correction-call, or helper grammar.

The policy line is exact and deliberate:

> A factor is recognized as a declared-family correction only when its resolved integer value is
> exactly the contract family size `N`.

Thus factor `3` for a five-outcome contract is not a family correction even if three p-values are
adjusted. Factor `N` applied to only `C proper-subset N` is a valid Bonferroni value for those
positions but incomplete family coverage, so it can support `strict_subset`. Factors less than or
greater than `N` abstain: the former proves no declared-family error control, while the latter may
be conservative but does not prove the declared method or exact coverage. The detector does not
infer a different family.

The following remain excluded:

- every factor other than exact integer `N`;
- correction calls outside the frozen correction registry;
- any recognized correction terminal combined with a separate manual fold;
- arbitrary arithmetic, casts, rounding, clipping, powers, Sidak expressions, Holm recurrences,
  or p-value transforms;
- helper-return records and any other opaque cross-function record flow;
- zip write-back beyond unchanged R16;
- DataFrame corrections beyond the already-admitted 3.0 section-9 construction and store forms;
- dynamic or p-derived correction-position selectors;
- AP evidence from names, field spellings, comments, strings, reports, or prompts; and
- any weakening of global censuses, row completeness, hierarchy, resampling, export, extremum,
  mutation, merge, polarity, or total-consumer guards.

## 2. Identities, contract, frozen surfaces, wording, and policy record

### 2.1 Versioned development identities

The new identities are:

```text
check_id         check:authorized-complete-family-correction-over-code-test-battery
check_version    3.2.0
detector_id      detector:bounded-code-csv-multiple-testing-conflict
detector_version 3.2.0
adapter_version  3.2.0
binding_id       method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
```

Only the development binding advances. Versions 1.0, 1.1, 2.0–2.3, 3.0, and 3.1 remain
registered for replay. Qualified pseudoreplication `3.1.0`, its GrantPin, grants, qualification
records, metric sets, threshold policies, wording profiles, and
`method_conflict_grant_pins.py` remain byte-untouched.

Contract profile `1.2.0` is unchanged. `N`, the group column, and the ordered outcome family come
only from that contract plus the existing CSV snapshot proof. `family_member_rule` and
`correction_scope` remain version discriminators, not prose authority.

### 2.2 Frozen 3.1 anchor

The build pins these current bytes before making a versioned copy:

```text
dataflow v3_1         sha256:2cf95b4ba52200374007969d511098571f35381bdbcff5b17f930d9a554d413e
record model v3_1     sha256:7fa5d768e7c6597deb1b61d65a3ebc8bb3cf2fd30a1b5c9cafe4da3338fcd1ff
adapter v3_1          sha256:35e66d27410fff965a02662b020ac86cf69f5bc880a73b2f2cb07a86d822776f
detector v3_1         sha256:92657c3b6edb8bbf2a68953cbc0b7f2673a6d2e422da0c4a9bd8d4049ff2b66f
integration v3_1      sha256:50f9bd11fb419dfdad4254154387ff92d75889d841130fad42fcf46f80ab3913
scope questions v1    sha256:b6d985b2481d80b174a661411887973bb5cf204b5f9003344119cd134f55a36a
scope attestations v1 sha256:64e0b225f34ae22dd1dd5cc01b4bc70c96bbef1d2a51df830aab004267b8b63b
3.1 question oracle   sha256:8d0cda616c0cd312c78722a7f45a2a7c22d1a6f33609d217a65ebed299f1d5e0
3.0 fixture matrix    sha256:ca3bc50a6f1943c15ed7a144bcf316238c4670b58ffd18d4ee6b94b936bd41f5
3.0 design            sha256:e950b6015198c92e7f7f16d30f901be9f131c0145e96524a22df4e33ed6ec166
3.1 design            sha256:e25eb7d1437b27cc5182ab1e1acc153b379e30d4415eee8a51286ff03df87c0f
```

The frozen 3.1 adapter path must replay all 140 source classifications and all 24 question rows
byte-identically. The new 3.2 comparison rows are additive. No frozen corpus replay record is
regenerated.

### 2.3 Wording and evidence

Wording profile v2 is unchanged. AP produces the already-defined `complete` and `strict_subset`
classification data and fills existing `corrected_positions`, `authorized_count`, `performed_count`,
`GROUP_COLUMN`, `CSV_PATH`, and family outcome slots. It needs no new wording slot and reads no
display text. `TEST_API` remains absent from wording v2.

Evidence records the correction production source span, raw-p root span, factor-binding span when
present, normalized form, `N`, `C`, and exact family-position map. It never stores a field spelling
as semantic evidence. Candidate wording remains the installed bounded template and continues to
state only structurally proved facts.

### 2.4 Required ADR-0079 amendment

This delta changes Finding eligibility and correction recognition. Before the development binding
advances, ADR-0079 must record:

1. the exact productions in sections 4.2–4.4;
2. the `factor == N` policy and its scientific rationale;
3. the distinction between `N` as correction factor and `C` as applied positions;
4. the admission of `ALPHA/N`, previously held for its own policy review;
5. the reuse of the 3.0 record/DataFrame graph without new field-name semantics;
6. the B1–B5 cumulative refusal obligation;
7. the two executed source movements and question-census delta; and
8. the fact that the 3.1 B-answer recheck may use AP only after 3.2 ships and only under the
   answer-removal equivalence gate.

No production authority, GrantPin, or qualified lane changes.

## 3. Unchanged global censuses and ordered integration

The whole-module registered-test census, correction-terminal census, statistics-prefix census,
repeated-construct census, dynamic-execution census, API-rebinding census, outcome-sequence
mutation census, and hierarchy/early-exit control set remain unchanged in substance and run on the
untouched AST. AP is a value proof, not a syntactic-census exemption.

The registries are restated by value. Registered family APIs are exactly:

```text
scipy.stats.ttest_ind
scipy.stats.mannwhitneyu
```

Recognized correction APIs are exactly:

```text
statsmodels.stats.multitest.multipletests
statsmodels.stats.multitest.fdrcorrection
scipy.stats.false_discovery_control
sc_referee.calculation_checks.bh.benjamini_hochberg
```

Correction terminal slots are exactly:

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

Statistics prefixes are exactly:

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

The dynamic-execution census remains the closed list `exec`, `eval`, `compile`, `__import__`,
`importlib.import_module`, module-receiver `getattr`/`setattr`, and mutation reached through
`globals()` or `locals()`. API rebinding remains any Store to an attribute of a resolved registered
module or statistics prefix, plus a local binding that shadows a live imported API identity/alias.
No AP identifier can hide one of these syntactic facts.

In particular:

- any registered correction terminal anywhere retains its existing coverage/refusal path;
- an unrecognized correction name caught by the terminal-slot census still abstains;
- an extra or unresolved registered family test still abstains before AP;
- statistics siblings, dynamic execution, rebinding, row-completeness failures, hierarchy gates,
  resampling, exports, and extrema still dominate AP; and
- AP never repairs an earlier operand, family-cardinality, API, or position failure.

The 3.2 order is:

1. parse and run all unchanged global censuses on the original tree;
2. run unchanged helper expansion, reader/operand/row/cardinality/API proofs, and build the 3.0
   record/DataFrame graph;
3. before the record mutation/manual-arithmetic/decision-threshold/conclusion guards finalize,
   attempt the exact AP normalization in sections 4–6;
4. on success, replace the graph value—not source code—with `AP(C,POS)` or `T(C,POS)` and resume
   every unchanged guard over the normalized graph;
5. on any failed AP obligation, discard no provenance and return the same surviving first reason
   that 3.1 would return; and
6. classify only after total forward accounting succeeds.

This integration point explains why the literal-factor control can move from the deeper
`pderived-conclusion-family-incomplete` wall while an unresolved factor retains that exact reason.
AP is not limited to the five 3.1 question-eligible first reasons; it is limited by its structural
grammar and pipeline position.

## 4. Closed AP(C, POS) grammar

### 4.1 Raw p root

`P` in every production must be exactly one `P(POS)` already proved by the 3.0 graph. Admitted
surface forms are:

```text
REGISTERED_TEST_CALL(...).pvalue
LOCAL_P_NAME                         # one reaching identity binding to that member
ROW[LITERAL_KEY]                     # field Value is exactly P(POS)
ROW.R4_FIELD                         # existing admitted R4 field Value is exactly P(POS)
```

The member is the registered `.pvalue` result, never a tuple position inferred for an unsupported
API. Sibling result members remain off-slice. A cast, round, call, arithmetic expression, merge,
container lookup without exact position, dynamic key, alias escape, imported/file-loaded value,
or unresolved helper result is not `P(POS)`.

### 4.2 Exact family-size value

`K` resolves to `N` only by one of these productions:

```text
K ::= INTEGER_LITERAL
    | FAMILY_SIZE_NAME
    | len(CONTRACT_OUTCOME_TABLE)

FAMILY_SIZE_NAME ::= one Name with exactly one Store in the parsed module whose RHS is
                     INTEGER_LITERAL or len(CONTRACT_OUTCOME_TABLE)
```

Requirements:

1. `INTEGER_LITERAL` is an `ast.Constant` whose value is an integer other than Boolean and equals
   `N`; float `N.0`, unary forms, arithmetic, Decimal construction, and calls are refused.
2. `len` is the unshadowed builtin, has one positional argument and no keywords.
3. `CONTRACT_OUTCOME_TABLE` is the exact immutable List/Tuple display already normalized by the
   family-position grammar; its first/outcome component is order-equal to the contract list.
4. The `Name` has one binding **anywhere in the parsed module**: no second Store in another scope,
   rebinding, `AugAssign`, `del`, alias binding, conditional definition, or unresolved escape.
5. A same-length unrelated container is not `N`. Row count alone proves nothing.
6. A Name-to-Name alias is refused. The admitted binding directly contains the integer or exact
   `len` production.
7. The resolved integer must equal contract `N` exactly.

### 4.3 Adjusted-p productions

The complete adjusted-p grammar is:

```text
PRODUCT ::= P * K
          | K * P

CAP ::= min(PRODUCT, ONE)
      | min(ONE, PRODUCT)
      | NUMPY.minimum(PRODUCT, ONE)
      | NUMPY.minimum(ONE, PRODUCT)

ADJUSTED ::= PRODUCT | CAP
ONE ::= source token `1` | source token `1.0`
```

`min` and `len` must resolve to unshadowed builtins. `NUMPY` must be a live, unshadowed import alias
resolving to `numpy`; the terminal slot must be exactly `minimum`. There are exactly two positional
arguments and no keywords. `ONE` is exactly the listed source token, not `True`, `1e0`, unary
arithmetic, a Name, or a computed value.

No other `BinOp` or `Call` is admitted. In particular division of p, addition, subtraction,
power, `max`, `clip`, `float`, `round`, `abs`, `where`, an unrecognized helper, or a library
correction call remains on the existing refusal path.

### 4.4 Divided-threshold productions

The threshold grammar is:

```text
FAMILY_ALPHA ::= bare numeric ast.Constant with source-text Decimal in {0.01, 0.05, 0.1}
               | ALPHA_NAME
ALPHA_NAME   ::= one Name with exactly one Store anywhere, RHS FAMILY_ALPHA literal
THRESHOLD    ::= FAMILY_ALPHA / K
DECISION     ::= P < THRESHOLD
               | P <= THRESHOLD
               | THRESHOLD > P
               | THRESHOLD >= P
```

The Decimal is constructed from the literal's source text, or `Decimal(repr(value))` only if the
source segment is unavailable; never `Decimal(float)`. `ALPHA_NAME` retains the unchanged A5
single-binding-anywhere rule. The division node must be direct: no parentheses containing other
arithmetic, reciprocal, precomputed quotient literal, call, cast, or nested transform. Reversed
operand order changes only the listed comparison operator; it does not change lineage.

This is correction recognition, not a general threshold widening. Any direct-p comparison outside
this exact production remains exclusively on the unchanged decision-threshold path. The existing
source-text product rules and conventional-alpha checks remain in force for every non-AP threshold.

### 4.5 Structural correction positions C

`C` is derived only from an existing exact `POS` route:

1. complete authorized-outcome loop/comprehension expansion;
2. exact immutable contract-outcome membership or an existing closed outcome-table Boolean flag;
3. existing literal/static record subset mapping;
4. unchanged R16 family-position mapping; or
5. an admitted 3.0 DataFrame section-9 static position mask.

The correction production's occurrence is evaluated for every expanded `POS`. Positions for which
the statically folded branch contains the production enter `C`; all others do not. `C` must be
nonempty, unique, ordered, duplicate-free, and a subset of `0..N-1`.

No source label, field name, comment, “primary” spelling, runtime p-value filter, data-dependent
mask, dynamic slice, row order alone, unresolved branch, or inferred subset size contributes.
If the selector cannot be folded for every `POS`, AP fails. A factor of `N` does not itself prove
`C=all positions`.

### 4.6 Single reaching correction fold

A family has exactly one normalized AP source construction key. After unchanged X4 and loop/
comprehension expansion:

- each `POS in C` has exactly one reaching instance of that construction;
- no `POS` has two competing adjusted definitions;
- all instances use the same grammar form, cap policy, factor proof, and raw `P(POS)`;
- the occurrence multiplicity is preserved and never deduplicated;
- a raw constructor field followed by a same-field adjusted store counts as two reaching stores and
  is refused under B4; and
- a second correction expression, even if equivalent, makes the scheme unresolved.

An X4-expanded scalar helper may expose the exact expression only when no record crosses the
helper boundary. A helper-return record, opaque parameter/return, closure, global/nonlocal value,
or unresolved call is cross-function flow and abstains. Source-position equality does not merge
expanded occurrences.

## 5. Record, cross-field, and DataFrame integration

### 5.1 Scalar and constructor fields

An exact scalar binding is admitted as one unconditional simple assignment or one assignment under
the statically folded selector establishing `C`.

A Dict/R4 constructor field may contain `ADJUSTED` only when the record literal/construction is
visible in the same expanded owner as `P(POS)`, the key/field is already accepted by the 3.0 schema,
and there is one reaching definition. Tuple/List record positions may contain the value only at
construction; they cannot be mutated.

### 5.2 Exact cross-field target

The only cross-field store is:

```text
ROW[TARGET_LITERAL_KEY] = ADJUSTED(ROW[SOURCE_LITERAL_KEY], K)
ROW.TARGET_R4_FIELD     = ADJUSTED(ROW.SOURCE_R4_FIELD, K)
```

The record has exactly one local literal/R4 constructor in the same expanded owner. Source and
target roles come from graph values, never their keys. `SOURCE` is exactly `P(POS)`; `TARGET` has
no prior reaching store. The statement is a simple assignment, evaluated once, and lies before
every target consumer. Under a subset branch, its positions equal `C` exactly. Outside `C`, each
conclusion must use an independently proved raw `P(POS)` route; an exact raw/corrected `p_used`
fold must use complementary, disjoint position sets whose union is all `N`.

The correction fold is treated atomically before the generic post-consumer-store guard only after
every AP obligation succeeds. If AP fails, the original store and every provenance edge are
restored to the unchanged mutation/lineage guards. This narrow ordering is what admits the two new
cross-field positive controls without reopening B1, B4, or B5.

### 5.3 Existing DataFrame section-9 boundary

AP may populate an existing section-9 whole-column or exact `.loc` partial store only when the RHS
is an already-reconstructed ordered scalar sequence and every expanded element independently
matches section 4. A partial store's mask positions must equal `C`. Existing `.where` then combines
`AP(C,POS)` with raw `P(POS)` only under its unchanged exact grammar.

Direct pandas/NumPy vector arithmetic, broadcast p correction, dynamic masks, chained indexing,
`.iloc`, apply/map/lambda correction, new DataFrame operations, and every store outside 3.0 section
9 remain `dataframe-pvalue-table-unresolved` or the existing consumer reason. There is no new
DataFrame constructor, row, column, or mask grammar.

## 6. Classification and total forward accounting

After AP normalization, **every** consumer of raw P, adjusted P, threshold, decision, record field,
sequence, and table column is accounted for by the unchanged forward slice.

Classification is closed:

1. `C == {0..N-1}` and every position's conclusion uses `AP(C,POS)`, `T(C,POS)`, or an exact
   derived reject decision: covered/`complete`, corrected positions all `N`.
2. `C` is a proper subset, every `POS in C` concludes from its corrected origin, and every
   `POS not in C` has a proved raw conclusion: candidate `strict_subset`, corrected positions `C`.
3. No recognized correction and all raw conclusions: unchanged candidate `none`.
4. Anything else abstains with the unchanged first reason.

An unused adjusted value, missing outside-C conclusion, corrected/raw consumer mismatch, export,
extremum, third emission, unknown call, unresolved container, or ambiguous record/table route does
not become a candidate. Any position that could take both adjusted and raw, neither, two factors,
two thresholds, two p origins, or conflicting decision polarity is unresolved.

The merge lattice remains component-wise and conservative. `UNRESOLVED`, different p positions in
one field, raw plus adjusted in one decision field, incompatible polarity, or distinct thresholds
never chooses the more accusation-supporting origin.

## 7. Load-bearing false-accusation argument and disqualifiers

The new candidate assertion is sound only if all three obligations hold:

1. global censuses still see every test, registered/terminal correction, statistics call, dynamic
   execution form, rebinding, and execution-prevention control;
2. AP recognizes only exact factor-`N` correction expressions at exact positions and total forward
   accounting cannot cross an unresolved edge; and
3. every old mutation, duplicate-store, alias, receiver, merge, polarity, and cross-function guard
   remains active around the one atomic fold.

The complete AP disqualifier set is:

- factor mismatch, float factor, Boolean factor, same-length unrelated container, factor alias,
  arithmetic/call factor, multiple binding, mutation, `AugAssign`, `del`, conditional binding, or
  escape;
- raw p cast/round/arithmetic, dynamic key, unresolved position, imported/file-loaded lineage, or
  sibling result member;
- record/collection aliasing, receiver call, unresolved-call passage, return escape, closure,
  global/nonlocal flow, helper-return record, or cross-function record construction;
- same-field overwrite, duplicate reaching store, conditional/loop-carried unknown store, dynamic
  store, store after any p/flag/table consumer, or a second correction fold;
- raw/adjusted merge, different-position merge, unresolved merge, distinct threshold merge,
  incompatible polarity, or ambiguous negation;
- correction terminal sibling, off-registry call, zip write-back, DataFrame operation outside 5.3,
  export, extremum, hierarchy, resampling, or unknown downstream consumer; and
- more or fewer than one proved corrected/raw origin for any position.

Strongest correct-analysis attacks and their blockers:

| Admission | Strongest correct shape | Required blocker |
|---|---|---|
| Exact factor `N` | same-sized unrelated table supplies `len(TABLE)` | 4.2 proves order-equal contract table, so `correct-ap-unrelated-same-length-factor` remains `unresolved-manual-correction-present`. |
| Stable factor Name | `FACTOR_ALIAS = FAMILY_SIZE`; later exact full Bonferroni | Name-to-Name alias is outside 4.2; `correct-ap-factor-alias-refused`. |
| Exact product | factor `(4+4)`, call, float, or rebound local | Closed K grammar/single binding refuses; computed and rebound fixtures retain their exact abstentions. |
| Single fold | two equivalent complete Bonferroni stores | Fold multiplicity is two; `correct-ap-two-correction-folds-refused`. |
| Structural C | data-dependent helper chooses corrected positions | C cannot resolve; `correct-ap-unresolved-position-selector`. |
| Cross-field AP | helper returns raw record, caller writes `p_adj = min(p*N,1)` | Same-owner literal-constructor proof fails; all B5 cross-field fixtures remain `record-family-lineage-unresolved`. |
| Atomic store | same field is created raw and then overwritten by hand Bonferroni | Constructor is first reaching store; B4 fixtures remain `record-family-mutation-unresolved`. |
| Downstream transport | exact correction also reaches unknown audit/correction helper | Surrogate/final total forward accounting refuses; `correct-ap-unresolved-correction-consumer`. |
| Existing correction coexistence | complete manual fold plus `multipletests` sibling | Global correction census dominates; `correct-ap-correction-terminal-sibling`. |
| Threshold division | threshold uses unrelated K, rebound alpha, or computed numerator | 4.2/4.4 fails; unchanged `unresolved-decision-threshold`. |

## 8. Cumulative executable fixture matrix

### 8.1 Frozen 71-row matrix

All 71 rows in `evaluation/development/multitest-code-slice-v3/FIXTURE_MATRIX.json` execute in the
3.2 sweep and remain outcome-identical. The load-bearing B1–B5/audit rows are:

```text
B1/B2:
correct-record-p-field-hand-bonferroni-augassign
correct-record-alias-field-hand-bonferroni
correct-record-unresolved-in-place-call
correct-record-update-receiver-call
correct-record-pop-receiver-call
correct-record-p-field-augassign
correct-record-field-delete
correct-record-store-after-p-consumer
correct-record-store-after-append-consumer
correct-record-two-position-field-merge
correct-record-raw-adjusted-decision-merge
correct-record-incompatible-decision-polarity-merge
correct-record-unresolved-decision-merge
correct-record-two-threshold-decision-merge

B3/B4:
correct-record-store-after-flag-fold
correct-record-inline-min-capped-bonferroni
correct-record-inline-bare-multiply
correct-record-inline-len-multiply

B5:
correct-record-cross-field-min-capped-bonferroni
correct-record-cross-field-bare-multiply
correct-record-helper-dict-literal-correction
correct-record-two-field-chained-correction
correct-record-store-new-field-after-flag-fold
```

The eight closure variants are pinned by the alias-field, unresolved-in-place-call, update,
pop, delete, store-after-p-consumer, store-after-append-consumer, and
store-new-field-after-flag-fold rows. The merge-attack family includes the four §4.1 merge rows,
the original `correct-record-raw-adjusted-field-merge`,
`correct-record-duplicate-raw-vs-adjusted-emissions`, and
`correct-record-flag-polarity-inverted`. The sweep also executes all **63** combinations of the
seven B5 field spellings and nine expression near-neighbors. All refuse
`record-family-lineage-unresolved`; field spelling supplies no semantic role.

### 8.2 Sixteen 3.1 laundering-adjacent controls

The sweep executes every row of the independent 3.1 `FIXTURE_MATRIX.json`: six positive witness
controls and ten no-question controls. They are all noncandidates under AP. In particular, a scope
witness is not an AP proof; bare `0.01`, a computed call threshold, file-loaded adjusted p,
unresolved imported helper, unused correction import, non-callee correction renames, report prose,
generic record update, and two correction occurrences remain outside AP.

### 8.3 Eighteen AP-specific fixtures

| Fixture | Executed pin |
|---|---|
| `positive-ap-subset-capped-family-name` | candidate `strict_subset {0,1,3}/8` |
| `positive-ap-subset-bare-product` | candidate `strict_subset {0,1,3}/8` |
| `positive-ap-subset-reversed-product` | candidate `strict_subset {0,1,3}/8` |
| `positive-ap-subset-literal-factor` | candidate `strict_subset {0,1,3}/8` |
| `positive-ap-subset-numpy-minimum` | candidate `strict_subset {0,1,3}/8` |
| `positive-ap-complete-capped-family-name` | covered/`complete {0..7}/8` |
| `positive-ap-complete-division-threshold` | covered/`complete {0..3}/4` |
| `positive-ap-subset-division-threshold` | candidate `strict_subset {0,1}/4` |
| `positive-ap-record-cross-field-complete` | covered/`complete {0..5}/6` |
| `positive-ap-record-cross-field-subset` | candidate `strict_subset {0,1}/6` |
| `correct-ap-unrelated-same-length-factor` | abstain `unresolved-manual-correction-present` |
| `correct-ap-factor-alias-refused` | abstain `unresolved-manual-correction-present` |
| `correct-ap-computed-factor-refused` | abstain `unresolved-manual-correction-present` |
| `correct-ap-factor-rebound-refused` | abstain `pderived-conclusion-family-incomplete` |
| `correct-ap-two-correction-folds-refused` | abstain `unresolved-manual-correction-present` |
| `correct-ap-unresolved-position-selector` | abstain `unresolved-manual-correction-present` |
| `correct-ap-unresolved-correction-consumer` | abstain `unresolved-manual-correction-present`; surrogate exposes hierarchy refusal |
| `correct-ap-correction-terminal-sibling` | abstain `unresolved-manual-correction-present`; global terminal gate blocks AP |

Fixture expectations are design-derived and checked before result serialization. The canonical
sweep records source SHA-256, baseline, outcome, model, positions, gate detail, and surrogate digest
for every row.

## 9. Adapter oracle — all 90 opened cases

The final build runs the real 3.2 adapter over all 90 source cases. The movement set must be exactly
`{E15:P6:81980e878c1bc8cc216b}`. Every “identical” row is byte-semantic equality of state,
reason/classification, corrected positions, authorized count, candidate count, question presence,
and Finding count except for the separately pinned question layer in section 11.

| Case | Exact 3.2 adapter pin | Delta from 3.1 |
|---|---|---|
| `E10:P1:ebbb8a5dbc2664257144` | abstain `authorized-reader-lineage-unavailable` | identical |
| `E10:P2:104493a5d99796a002c0` | candidate `none`, `{}/5` | identical |
| `E10:P3:3ff45fce2a45e0959fdb` | candidate `none`, `{}/6` | identical |
| `E10:P4:7296b0e2cf7faeefca64` | candidate `none`, `{}/3` | identical |
| `E10:P5:c51d08801b3d0ba4e532` | candidate `strict_subset`, `{0,1,2}/7` | identical |
| `E10:P6:f4cf62caeb8ad68dc5b3` | candidate `strict_subset`, `{0,1,2}/5` | identical |
| `E10:N1:cb2e207276a0dc3247bb` | covered `complete`, `{0,1,2,3}/4` | identical |
| `E10:N2:9be74afbe9659bd50580` | abstain `unresolved-decision-threshold` | identical |
| `E10:N3:b787314c170f8f690060` | abstain `unresolved-manual-correction-present` | identical |
| `E10:N4:60f96fabb7129d662b23` | abstain `extra-registered-test-outside-authorized-family` | identical |
| `E10:N5:8d83210468ecde012e4a` | abstain `test-battery-cardinality-unresolved` | identical |
| `E10:N6:4907932548f745afe942` | abstain `authorized-family-test-census-incomplete` | identical |
| `E10:N7:6d2fdc67ab98bc0e0e6e` | abstain `statistics-api-imported-outside-analysis-py` | identical |
| `E10:N8:dfc9f20a94ecefc7f7b5` | abstain `test-battery-cardinality-unresolved` | identical |
| `E10:N9:e1bce32a32e3b2df475e` | abstain `unresolved-decision-threshold` | identical |
| `E11:P1:8726b87ac4ba4c34c0a3` | candidate `none`, `{}/4` | identical |
| `E11:P2:6f08fe90c58e51737a4d` | candidate `none`, `{}/6` | identical |
| `E11:P3:69c5d0aec76eefb67148` | candidate `none`, `{}/3` | identical |
| `E11:P4:dfd35001c5a99ab1486b` | candidate `none`, `{}/5` | identical |
| `E11:P5:114782f595d9c24b923d` | candidate `strict_subset`, `{0,1}/7` | identical |
| `E11:P6:0249919d05de1abc25fd` | candidate `strict_subset`, `{0,1,2}/8` | identical |
| `E11:N1:d1533e4a8bbd10cb727e` | covered `complete`, `{0,1,2,3,4}/5` | identical |
| `E11:N2:d11a7136d1e91ed8e26f` | abstain `unresolved-decision-threshold` | identical |
| `E11:N3:479317f1706d4fb929e5` | abstain `unresolved-manual-correction-present` | identical |
| `E11:N4:10e0cfb0c7ba8d03ec52` | abstain `extra-registered-test-outside-authorized-family` | identical |
| `E11:N5:2a712805024597719d32` | abstain `test-battery-cardinality-unresolved` | identical |
| `E11:N6:1cce7d6b580caa25f597` | abstain `authorized-family-test-census-incomplete` | identical |
| `E11:N7:9bccc428f23dde0d43f0` | abstain `authorized-family-test-census-incomplete` | identical |
| `E11:N8:53c4753f38f9e253d541` | abstain `test-battery-cardinality-unresolved` | identical |
| `E11:N9:08565c720304eb6fd9d3` | abstain `unresolved-decision-threshold` | identical |
| `E12:P1:f9ce4de5e21d9015ecd9` | candidate `none`, `{}/5` | identical |
| `E12:P2:e07a6f2a895079b53b8c` | candidate `none`, `{}/4` | identical |
| `E12:P3:e28a9537b07c74d21838` | candidate `none`, `{}/6` | identical |
| `E12:P4:0ec89f70a9776d1a1931` | candidate `none`, `{}/3` | identical |
| `E12:P5:54667dd7c39067c8c2c8` | candidate `strict_subset`, `{0,1}/7` | identical |
| `E12:P6:68d1a6f5b1ab70f2650a` | candidate `strict_subset`, `{0,1}/5` | identical |
| `E12:N1:45c4b9a19d0a630f1cb0` | covered `complete`, `{0,1,2,3,4}/5` | identical |
| `E12:N2:f256af2f5c5d98f37e65` | abstain `unresolved-decision-threshold` | identical |
| `E12:N3:678e94e79226936fd647` | abstain `unresolved-manual-correction-present` | identical |
| `E12:N4:c37c0fa6e462a22cb6d5` | abstain `authorized-family-test-census-incomplete` | identical |
| `E12:N5:6108263527580cd01608` | abstain `test-battery-cardinality-unresolved` | identical |
| `E12:N6:db193771248850b81b25` | abstain `test-battery-cardinality-unresolved` | identical |
| `E12:N7:190ca375ac7c481c3e08` | abstain `authorized-family-test-census-incomplete` | identical |
| `E12:N8:7fd5f9dcd4097c1e5a03` | abstain `authorized-family-test-census-incomplete` | identical |
| `E12:N9:62aa3748aa0c7c2607d3` | abstain `test-battery-cardinality-unresolved` | identical |
| `E13:P1:686d1432762cd49d9b54` | candidate `none`, `{}/4` | identical |
| `E13:P2:c336be2521785ab6a954` | abstain `extra-registered-test-outside-authorized-family` | identical |
| `E13:P3:4f042d10b3f9a43d1099` | candidate `none`, `{}/3` | identical |
| `E13:P4:ffbe12246cf8a4227210` | candidate `none`, `{}/8` | identical |
| `E13:P5:80091f37c722eba28e18` | candidate `strict_subset`, `{0,1}/7` | identical |
| `E13:P6:d0f9fcd52f47e4d64668` | abstain `unresolved-manual-correction-present` | identical; factor `3 != N=5` |
| `E13:N1:b7d38f6e9284abfd3ee6` | abstain `correction-family-lineage-unresolved` | identical |
| `E13:N2:f65170c644b90c4a893c` | abstain `unresolved-decision-threshold` | identical |
| `E13:N3:c15f507ad59999fd9371` | abstain `unresolved-manual-correction-present` | identical |
| `E13:N4:cfbb5edfd1534e7419fd` | abstain `extra-registered-test-outside-authorized-family` | identical |
| `E13:N5:8f37c5176ab3c0a61e4d` | abstain `test-battery-cardinality-unresolved` | identical |
| `E13:N6:6a102a97a065f9c8879f` | abstain `authorized-reader-lineage-unavailable` | identical |
| `E13:N7:aba768f8d0b3f3548683` | abstain `authorized-family-test-census-incomplete` | identical |
| `E13:N8:325c686a92196956359a` | abstain `test-battery-cardinality-unresolved` | identical |
| `E13:N9:ab70cdb37bb2977d725c` | abstain `unresolved-decision-threshold` | identical |
| `E14:P1:9ed744e25f1f1c55f8ca` | candidate `none`, `{}/5` | identical |
| `E14:P2:4fc0f5c1ef2d0e2cd5b6` | candidate `none`, `{}/6` | identical |
| `E14:P3:502687d9137dab93ff99` | abstain `unresolved-decision-threshold` | identical |
| `E14:P4:cccde3c60f936e077f80` | candidate `none`, `{}/7` | identical |
| `E14:P5:5e33841b96d85ffe67be` | candidate `strict_subset`, `{0,1}/6` | identical |
| `E14:P6:94786af7eca95fff6d78` | abstain `unresolved-manual-correction-present` | identical; factor `4 != N=8` |
| `E14:N1:aabf005414b9ae164c0b` | abstain `authorized-family-test-census-incomplete` | identical |
| `E14:N2:c83b4021527fa98dadf3` | abstain `authorized-family-test-census-incomplete` | identical |
| `E14:N3:2327c03c4ddd02a36b97` | abstain `authorized-family-test-census-incomplete` | identical |
| `E14:N4:f80bac8b4bd7442917c5` | abstain `extra-registered-test-outside-authorized-family` | identical |
| `E14:N5:e987fc7ceafb6acb7a75` | abstain `test-battery-cardinality-unresolved` | identical |
| `E14:N6:1baacbeace56bb5d7b0f` | abstain `authorized-family-test-census-incomplete` | identical |
| `E14:N7:470aaf22deaf023aaae6` | abstain `authorized-family-test-census-incomplete` | identical |
| `E14:N8:c3191c18f72145cde01c` | abstain `authorized-family-test-census-incomplete` | identical |
| `E14:N9:5d5d4e0189d4f2c73f6a` | abstain `hierarchical-gatekeeping-present` | identical |
| `E15:P1:e90debfca9efcf70e758` | candidate `none`, `{}/4` | identical |
| `E15:P2:f616be91eaedbf23fad2` | candidate `none`, `{}/6` | identical |
| `E15:P3:afe47b2a7ea87ed21a69` | abstain `unresolved-manual-correction-present` | identical; correction witness is not AP |
| `E15:P4:6e0ce2fc6d782f351d96` | abstain `test-battery-cardinality-unresolved` | identical |
| `E15:P5:3d2f92807b8138de6463` | abstain `record-family-mutation-unresolved` | identical; partial Holm call/store excluded |
| `E15:P6:81980e878c1bc8cc216b` | **candidate `strict_subset`, `{0,1,3}/8`** | **moved by exact factor-8 AP** |
| `E15:N1:f846b07b1d11131cec4d` | covered `complete`, `{0,1,2,3}/4` | identical |
| `E15:N2:5fb661f1e846196aa832` | abstain `test-operand-lineage-unresolved` | identical |
| `E15:N3:907f9057eb9fc1d88e99` | abstain `unresolved-manual-correction-present` | identical |
| `E15:N4:42f325bec89c5695ea51` | abstain `family-test-api-dispatch-unresolved` | identical |
| `E15:N5:3583dc8b101822cf15b9` | abstain `extra-registered-test-outside-authorized-family` | identical |
| `E15:N6:d29aecb0a61ab4ebc486` | abstain `authorized-family-test-census-incomplete` | identical |
| `E15:N7:9d5848e6aaba7586e0f1` | abstain `authorized-family-test-census-incomplete` | identical |
| `E15:N8:0aa1af228c91fde5f909` | abstain `test-battery-cardinality-unresolved` | identical |
| `E15:N9:7992deeaaf441345c89e` | abstain `unresolved-decision-threshold` | identical |

The exact opened movement count is **one of 90**. The sealed envelope scores are immutable; retro
recall is a development diagnostic, not a rescoring.

## 10. Open-corpus oracle — all 50 cases

The movement set is exactly `{spec-28}`. It is labeled correct and becomes covered/complete, not a
candidate. Therefore corpus misstep recall remains `19/25` and the hard correct-candidate count
remains `0/25`.

| Case | Exact 3.2 adapter pin | Delta from 3.1 |
|---|---|---|
| `spec-01` | candidate `none` | identical |
| `spec-02` | abstain `correction-family-lineage-unresolved` | identical |
| `spec-03` | candidate `none` | identical |
| `spec-04` | abstain `correction-family-lineage-unresolved` | identical |
| `spec-05` | candidate `none` | identical |
| `spec-06` | abstain `unresolved-decision-threshold` | identical |
| `spec-07` | candidate `none` | identical |
| `spec-08` | abstain `extra-registered-test-outside-authorized-family` | identical |
| `spec-09` | candidate `none` | identical |
| `spec-10` | abstain `helper-body-statement-unsupported` | identical |
| `spec-11` | candidate `none` | identical |
| `spec-12` | abstain `test-battery-cardinality-unresolved` | identical |
| `spec-13` | abstain `test-battery-cardinality-unresolved` | identical |
| `spec-14` | abstain `test-operand-lineage-unresolved` | identical |
| `spec-15` | candidate `none` | identical |
| `spec-16` | abstain `authorized-family-test-census-incomplete` | identical |
| `spec-17` | candidate `none` | identical |
| `spec-18` | abstain `test-battery-cardinality-unresolved` | identical |
| `spec-19` | candidate `none` | identical |
| `spec-20` | abstain `unresolved-decision-threshold` | identical |
| `spec-21` | candidate `strict_subset` | identical |
| `spec-22` | abstain `authorized-family-test-census-incomplete` | identical |
| `spec-23` | abstain `pvalue-scalar-cast-or-rounding-unsupported` | identical |
| `spec-24` | abstain `correction-family-lineage-unresolved` | identical |
| `spec-25` | candidate `none` | identical |
| `spec-26` | abstain `correction-family-lineage-unresolved` | identical |
| `spec-27` | candidate `none` | identical |
| `spec-28` | **covered `complete`, `{0,1,2,3}/4`** | **moved by exact `0.05/4` threshold** |
| `spec-29` | abstain `unresolved-decision-threshold` | identical |
| `spec-30` | abstain `api-resolution-ambiguous` at adapter | identical |
| `spec-31` | candidate `none` | identical |
| `spec-32` | abstain `extra-registered-test-outside-authorized-family` | identical |
| `spec-33` | candidate `none` | identical |
| `spec-34` | abstain `test-battery-cardinality-unresolved` | identical |
| `spec-35` | candidate `none` | identical |
| `spec-36` | abstain `test-operand-lineage-unresolved` | identical |
| `spec-37` | abstain `selected-group-row-completeness-unproven` | identical |
| `spec-38` | abstain `authorized-family-test-census-incomplete` | identical |
| `spec-39` | abstain `api-resolution-ambiguous` | identical |
| `spec-40` | abstain `test-battery-cardinality-unresolved` | identical |
| `spec-41` | candidate `none` | identical |
| `spec-42` | abstain `unresolved-manual-correction-present` | identical |
| `spec-43` | candidate `strict_subset` | identical |
| `spec-44` | abstain `authorized-family-test-census-incomplete` | identical |
| `spec-45` | candidate `none` | identical |
| `spec-46` | abstain `correction-family-lineage-unresolved` | identical |
| `spec-47` | abstain `unresolved-decision-threshold` | identical |
| `spec-48` | abstain `unresolved-decision-threshold` | identical |
| `spec-49` | candidate `none` | identical |
| `spec-50` | abstain `pvalue-family-collection-unresolved` | identical |

The frozen `adapter_replay_records_v2_1.json` and every existing comparison row remain raw-byte
immutable. A new 3.2 comparison row records the spec-28 covered movement and the other 49 exact
pins. It is never substituted into a frozen record.

## 11. Interaction with 3.1 questions and asymmetric attestations

### 11.1 No-attestation question census

Question eligibility still requires one of the same five reasons plus the same structural
CorrectionScopeWitness. AP does not add a question reason or wording template. When AP resolves the
source classification to candidate or covered, there is no correction-scope unknown and therefore
no MaterialQuestion for that occurrence.

Exactly these two questions disappear:

```text
E15:P6:81980e878c1bc8cc216b
corpus:spec-28
```

The exact post-3.2 set is 13 opened plus nine corpus rows:

```text
E10:N2:9be74afbe9659bd50580
E10:N3:b787314c170f8f690060
E11:N2:d11a7136d1e91ed8e26f
E11:N3:479317f1706d4fb929e5
E12:N2:f256af2f5c5d98f37e65
E12:N3:678e94e79226936fd647
E13:P6:d0f9fcd52f47e4d64668
E13:N1:b7d38f6e9284abfd3ee6
E13:N2:f65170c644b90c4a893c
E13:N3:c15f507ad59999fd9371
E14:P6:94786af7eca95fff6d78
E15:P5:3d2f92807b8138de6463
E15:N3:907f9057eb9fc1d88e99
corpus:spec-02
corpus:spec-04
corpus:spec-06
corpus:spec-24
corpus:spec-26
corpus:spec-29
corpus:spec-46
corpus:spec-47
corpus:spec-48
```

E13 P6 and E14 P6 keep their questions: each has a positive manual-correction witness, but
`factor != N`, so AP does not prove scope. E15 P5 keeps its question because a partial Holm
call/store is outside AP. A partial AP match that fails uniqueness, factor, position, merge, or
consumer proof keeps the ordinary 3.1 question behavior whenever the surviving first reason and
witness still qualify.

Question ids and evidence digests remain input-determined. The changed source classification means
the two removed question records do not exist; no tombstone or carry-forward answer is created.

### 11.2 B-answer guided recheck ordering

Before 3.2 ships, AP is not an existing check and a B answer cannot invoke it. After the 3.2
development binding ships, AP becomes one of the existing structural checks that a B pointer may
prioritize. All 3.1 asymmetry remains:

- the claimed factor, method, and author's “complete” answer are never resolved values;
- B supplies only a bound source location;
- AP runs with the source, contract, and frozen structural grammar exactly as it would without the
  Answer;
- the source module classification remains byte-identical, per 3.1 Revision 1b; only the receipt
  can record an answer-guided existing proof;
- a failed AP proof yields the existing non-accusatory Disclosure and leaves the question open;
  and
- B alone can never create a candidate, Finding, corrected position, or verified-correct source
  classification.

Every `answer-b-proves-*` fixture gains an AP companion where applicable. Removing the Answer and
invoking AP at the now-known node must yield the same corrected-position set. If guided AP proves
anything the answer-removed AP does not, that is answer laundering and a section-17 stop.

Answer A remains a visibly author-attributed ConditionalConcern, never a tool Finding. Attestation
schema, five digest bindings, all-or-nothing validation, stale/wrong-id refusals, replay rules,
skill-layer behavior, and blind scoring isolation are unchanged.

## 12. Closed reasons, guard ownership, and wording

### 12.1 Closed reason set

Version 3.2 adds and retires **zero** abstention reasons. The closed set remains the exact 61-member
3.0/3.1 set:

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

The documented-unreachable annex for `conclusion-output-sink-unavailable` remains. Emission
fixtures scoped to v3.2 plus that annex must be set-equal to the list. Older-version literals cannot
satisfy the gate.

### 12.2 Guard ownership

| Guard | 3.2 trigger | Disposition |
|---|---|---|
| Test/correction/statistics/dynamic/API censuses | untouched whole module | unchanged; always precedes AP |
| Operand, row, family cardinality, API dispatch | existing backward slices and instance plan | unchanged; AP cannot repair |
| Raw p and record/DataFrame graph | existing forward graph plus exact AP node | one new graph Value; all unresolved edges survive |
| Mutation/alias/store | whole relevant graph | exact AP store is atomic only after proof; every other trigger unchanged |
| Merge/polarity | existing lattice | unchanged and absorbing |
| Threshold/manual correction | source-text Decimal and AP grammar | exact productions normalize; all others retain existing reasons |
| Hierarchy/resampling/export/extremum/inference | existing global/slice guards | unchanged |
| Conclusions | total forward slice | AP origin accepted; sink and completeness grammars unchanged |
| Questions/attestations | post-classification 3.1 layer | two source-resolved questions disappear; trust rule unchanged |

No surviving reason is relabeled. A row may cease to emit a reason only when the exact AP proof
produces an existing classification.

### 12.3 Wording and record-type gates

Wording v2 bytes remain frozen. A covered result is not a Finding. A `strict_subset` candidate uses
the existing detector wording and still must satisfy all Finding prerequisites downstream. AP
creates no new public record type and never converts a MaterialQuestion or author attestation into
a Finding.

## 13. Ordering, idempotence, determinism, and replay

### 13.1 Production order

The AP normalizer consumes the fixed-point graph after existing 2.2 D6 double-transform,
2.3 terminal-clone mapping, and 3.0 record/DataFrame construction. It runs before manual/threshold/
record-mutation reasons finalize. The whole-module censuses always inspect the untouched tree.

An exact cross-field AP store is matched jointly with its raw source, target, position set, and all
conclusion consumers. No component is independently reconciled. Record occurrence order and
position multiplicity remain ordered; an occurrence ordinal is bookkeeping only and never a
factor, key, evidence value, or `POS` substitute.

### 13.2 Idempotence

Applying AP normalization twice to the same graph must yield byte-equal graph values, `C`,
classifications, evidence spans, and errors. An already normalized `AP(C,POS)` is not a new product
and cannot be adjusted again. The second pass finds zero new folds. Reordering exact input maps or
deduplicating occurrences is forbidden.

The prototype replay reruns all 140 cases and all 168 fixtures and compares canonical
`results.json` bytes. The final implementation adds equivalent graph-idempotence tests for every
positive form, including record cross-field and divided-threshold subset forms.

### 13.3 Determinism

No AP identity includes a clock, filesystem traversal order, object id, Python hash order, source
prose, or answer content. Maps and sets serialize by canonical contract position. Decimal values
derive from source text. Same source, contract, CSV snapshot, registry, and attestations bytes yield
byte-identical module outcomes, candidate records, questions, concerns, disclosures, receipts,
locks, and replay rows.

## 14. Validation plan and build gates

### 14.1 Executed prototype gates

The checked-in sweep must remain self-verifying:

1. exactly 140 unique cases: 90 opened and 50 corpus;
2. exact movement set `{E15:P6:81980e878c1bc8cc216b, corpus:spec-28}`;
3. exact classifications/positions from sections 9 and 10;
4. retro recall `{E10:5/6,E11:6/6,E12:6/6,E13:4/6,E14:4/6,E15:3/6}`;
5. none-flip `0/25`, `0/54`, and `0/152`;
6. all 71 cumulative rows outcome-identical, all 63 B5 variants refused, and all 16 laundering
   controls noncandidates;
7. all 18 new fixtures exact;
8. question delta exactly `24 -> 22` with the two named removals; and
9. replay byte equality plus complete MANIFEST digest/size inventory.

### 14.2 Final adapter/oracle gates

The build must execute:

- the 90-row section-9 oracle through the real 3.2 adapter;
- the 50-row section-10 oracle through the same adapter;
- the frozen 3.1 adapter over all 140 cases, byte-equal to its anchor;
- all E10–E15 frozen replay anchors under their frozen versions;
- the 71 cumulative fixtures, 63 B5 expression variants, 16 laundering controls, and 18 AP
  fixtures;
- direct factor mismatch controls at `3/5`, `4/8`, `7/6`, and same-length unrelated `N`;
- every cap ordering, multiplication ordering, direct/bound factor, complete/subset, scalar/record/
  DataFrame admitted production;
- uniqueness after helper/loop expansion, including one source occurrence expanded to `C` and two
  competing occurrences refused;
- all B1–B5 variants and the full merge/polarity family;
- answer-removal equivalence for every B-proves row that reaches AP; and
- exact no-attestation question census and attested 15/15 replay.

### 14.3 Prose/evidence tripwire

For every new predicate, the suite mutates comments, docstrings, report/Markdown files, display
strings, format strings, and non-callee identifiers, including correction-like and field-role
spellings. None may change AP recognition, `C`, outcome, evidence digest, or question eligibility.
The 256-byte presentation caps remain measured and never inspected.

Paired structural controls must change as expected: deleting `* K`, changing `K`, changing the
callee terminal `numpy.minimum`, deleting `/ K`, changing a literal contract outcome in the
selector, or adding a second reaching fold must remove AP or abstain. Contract outcome literals are
read only for exact membership/position equality; arbitrary source strings never enter.

### 14.4 Isolation, closed-set, and quality gates

Required gates also include:

1. v3.2 reason literals plus the unreachable annex set-equal the exact 61-member list;
2. v3.2 question qualifying reasons remain the exact five-member set;
3. wording v2 object/digest byte equality;
4. contract 1.0/1.1 golden bytes and all seven error categories unchanged;
5. frozen 3.1 module/design/oracle digests exact;
6. no GrantPin, grant, qualification, metric-set, threshold-policy, or qualified Finding byte
   derives from the development-lane registry digest;
7. qualified pseudoreplication differential is noise-only and byte-invariant;
8. deterministic registry, corpus-census, replay, manifest, and ledger regeneration; and
9. fresh `ruff check .`, `ruff format --check .`, `mypy src`, full `pytest`, and
   `python scripts/validate_starter.py` after the final manifest-covered edit.

## 15. Reuse map and file-by-file build plan

### 15.1 New versioned files

The builder copies, never edits, the 3.1 modules and adds:

```text
src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_2.py
src/sc_referee/scientific_checks/code_csv_multiple_testing_record_model_v3_2.py
src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_2.py
src/sc_referee/scientific_checks/code_csv_multiple_testing_adapter_v3_2.py
src/sc_referee/scientific_checks/integration_multiple_testing_v3_2.py
src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3_2.py
```

The correction model owns only sections 4–6 and returns an immutable graph delta or refusal. The
dataflow/record copies integrate it without editing v3/v3_1. `_hierarchy_guard` and global registry
values are copied byte-for-byte unless an interface import changes; their substantive decisions
must be extensionally identical.

### 15.2 Narrow shared/integration edits

Expected narrow edits are:

- development binding and versioned manifest/resource registry entries;
- detector/check registration retaining all historical versions;
- versioned adapter/integration dispatch;
- ADR-0079 amendment;
- capability/registry/manifest/ledger regeneration; and
- tests and new 3.2 comparison artifacts.

`multiple_testing_scope_questions_v1.py` and
`multiple_testing_scope_attestations_v1.py` remain byte-untouched unless a new versioned wrapper is
needed to select the 3.2 proof callback. A wrapper may not change their witness grammar, wording,
schema, trust asymmetry, or record types.

### 15.3 Tests and development artifacts

Expected additions include:

```text
tests/test_code_csv_multiple_testing_correction_model_v3_2.py
tests/test_code_csv_multiple_testing_dataflow_v3_2.py
tests/test_bounded_code_csv_multiple_testing_conflict_v3_2.py
tests/test_multiple_testing_opened_oracle_v3_2.py
tests/test_multiple_testing_open_corpus_v3_2.py
tests/test_multiple_testing_scope_questions_v3_2.py
tests/test_multiple_testing_frozen_v3_1.py
tests/test_multiple_testing_prose_tripwire_v3_2.py
evaluation/development/multitest-code-slice-v3_2/...
```

The prototype sweep shipped with this design is an evidence anchor, not production code.

## 16. Residuals and honest read

### 16.1 Explicit residuals

The following remain deliberately uncatchable or unresolved:

1. factor `K != N`, including E13 P6 `3/5` and E14 P6 `4/8`;
2. partial Holm/other library write-back not already proved by existing correction grammars,
   including E15 P5;
3. corrections through unrecognized libraries or helpers;
4. arbitrary casts, rounding, clipping, Sidak/manual Holm arithmetic, and transformed p values;
5. zip write-back outside unchanged R16;
6. DataFrame vector/column corrections outside 3.0 section 9;
7. opaque cross-function record correction, including the cumulative B5 shapes;
8. dynamic correction positions, runtime p filters, ambiguous merges, and multi-fold schemes; and
9. every earlier reader, operand, row, cardinality, API, hierarchy, resampling, export, extremum,
   inference, and incomplete-conclusion wall.

The 3.1 question layer remains the user-facing path for positively located but unresolved scope.
It is not a substitute for AP proof.

### 16.2 What the executed delta buys

The source evidence shows one new misstep catch and one newly proved correct analysis. E15 P6 is
the intended partial-factor-`N` pattern: three of eight positions use exact Bonferroni values and
five use raw conclusions. Corpus spec-28 proves that the same grammar does not accuse a complete
`0.05/4` analysis. Corpus recall remains `19/25`; correct-candidate count remains zero.

The historical partial-hand shapes do not all generalize. Two of the three earlier examples use
factor `|C|`, not `N`, and remain questions. Thus this design does not claim that “manual
correction” as a broad family is solved.

### 16.3 E16/E17 arrival and promotion arithmetic

The sealed E13, E14, and E15 first-contact scores are `3/6`, `1/6`, and `2/6`, totaling `6/18`.
Retro recognition does not rescore them. Once E17 is sealed, the relevant E15–E17 window reaches
the `9/18` half-recall bar only if **E16 plus E17 contribute at least `7/12`** because E15 contributes
two sealed catches.

That arithmetic requires an average of `3.5/6` across E16 and E17; `4/6` plus `3/6` suffices. The
arrival evidence does not justify forecasting that result. Exact factor-`N` AP occurred in one of
the three recent hand-correction misses and one of 18 recent positives. E16/E17 may contain the
shape now that it is a recurring author idiom, but factors, stores, libraries, or positions may
again differ. Envelope scoring remains the only first-contact evidence.

## 17. Stop-and-report rule

Stop and report a design regression rather than widening, relabeling, or re-pinning if any of the
following occurs:

1. the 140-case movement set is not exactly the two rows in section 0;
2. E15 P6 does not reach `strict_subset {0,1,3}/8` or corpus spec-28 does not reach
   covered/`complete {0,1,2,3}/4` under the final strict implementation;
3. any other source row moves, including E13 P6 or E14 P6;
4. any corpus-correct or opened-negative case becomes a candidate;
5. any cumulative 71-row outcome changes, any of its 62 correct rows becomes a candidate, or any
   of its nine positive controls loses its pin;
6. any of the 63 B5 variants or 16 laundering controls becomes a candidate;
7. any new AP fixture misses its exact section-8.3 pin;
8. a factor other than exact `N`, a same-length unrelated container, factor alias, or computed
   factor is accepted;
9. a B1–B5 mutation, duplicate, cross-function, merge, polarity, or post-consumer shape crosses AP;
10. a corrected/raw position is missing, duplicated, inferred by spelling, or dynamically selected;
11. a guided B proof differs from its answer-removed companion;
12. the question census is not exactly `13/90 + 9/50`, with only the two named removals;
13. the 61-reason set, five qualifying reasons, wording v2 bytes, or public record-type discipline
    changes;
14. any frozen 3.1 or qualified-lane byte changes outside an explicitly versioned comparison row;
15. prose, report, display, or non-callee identifier mutation changes evidence;
16. replay is not byte-identical or a manifest/ledger/registry gate is stale;
17. implementation needs a new call, arithmetic, factor, field, position, DataFrame, threshold,
    helper, merge, or consumer admission; or
18. any required lint, format, type, test, starter-validation, isolation, or differential gate
    fails after the final file change.

Conservative refusal is not permission to miss a pinned positive or silently move a reason. Report
the exact source digest, observed result, expected clause, and minimal structural cause.

## 18. Revision log

### Revision 0 — 2026-08-30

Initial commissioned design. It:

- ships the strict executable sweep with the design rather than projecting movements;
- admits only exact factor-`N` Bonferroni products/caps and exact family-alpha division;
- extends AP to same-owner record/cross-field targets and existing bounded DataFrame stores;
- retains the complete B1–B5, merge, closure, and 3.1 laundering refusal surfaces;
- pins exactly two source movements, retro recall, none-flip counts, and the `24 -> 22` question
  delta from executed output;
- leaves all 61 reasons and wording v2 unchanged;
- makes 3.1 B-guided AP available only after shipping and preserves answer-removal equivalence;
- freezes 3.1 and every earlier/qualified lane; and
- states the E16/E17 `>=7/12` promotion arithmetic without treating it as a forecast.
