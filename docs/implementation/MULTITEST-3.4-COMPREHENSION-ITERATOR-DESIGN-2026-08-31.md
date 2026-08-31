# Multiple-testing 3.4 comprehension, iterator, and cap design, 2026-08-31

**Status:** build-ready design, Revision 0  
**Target:** detector/check/adapter `3.4.0`, development lane only  
**Predecessor:** multiple-testing `3.3.0` terminal-presentation and helper-record proofs over the
`3.2.0` AP recognition, `3.1.0` question/attestation layer, and `3.0.0` record model  
**Authority:** frozen scientific-requirement contract profile `1.2.0`; no prose-derived authority  
**Scope:** three shipped syntactic admissions, one specified and unshipped, and one recorded
reason defect; no new scientific classification rule  
**Implementation in this session:** none

## 0. Evidence basis, observed trigger attribution, and prototype/final fidelity

This design is based on:

- the sealed-then-opened E17 evidence in `blind-envelope-17-2026-08-30`, scored recall `4/6`,
  `0/9` accusation candidates, `0` Findings, replay `15/15`;
- direct inspection of the two missed E17 positive sources and all fifteen E17 adapter outcomes;
- instrumented execution of the shipped `3.3.0` analyzer, the frozen
  `code_csv_multiple_testing_dataflow_v3.py` hierarchy guard, the shipped
  `code_csv_multiple_testing_terminal_presentation_v3_3.py` proof, and the shipped
  `code_csv_multiple_testing_correction_model_v3_2.py` AP recognizer;
- every opened envelope case from E10 through E17, all 50 open-corpus cases, and the cumulative
  3.0/B5/3.1/AP/3.3 safety populations; and
- the strict executable shadow, generated fixtures, canonical results, and self-verifying replay
  under `evaluation/development/multitest-code-slice-v3_4/prototype-sweep/`.

The evidence population is exactly **170 source cases**: **120 opened cases** from E10–E17 plus
**50 corpus cases**. The first 155 are the frozen 3.3 evidence population; E17 adds fifteen. The
prototype additionally executes **245 fixtures**, of which **194** carry the correct-analysis label
and **203** are the byte-chained frozen 3.3 population.

### 0.1 Trigger attribution is observed, not inferred

The E17 recon identified two walls. `instrument_results.json` resolves both against real shipped
code rather than by reading the recon's hypotheses back.

**E17 P3 `a2e031f79e31c80fd900`** (six declared outcomes, dict comprehension over `OUTCOMES`
collecting a helper-returned record, presentation loop printing a verdict per outcome):

| Observation | Value |
|---|---|
| shipped 3.3 first reason | `hierarchical-gatekeeping-present` |
| tracked hierarchy controls before that reason | exactly one |
| first tracked control | line 71, columns 35–54, `result['p'] < ALPHA`, an `ast.Compare` |
| `_p_origins` of that control | **0** |
| `_correction_control_present` of that control | **False** |
| `_outcome_headers` of that control | all **six** contract outcome columns |
| is it a control-registry expression | **True** (the test of the verdict `IfExp`) |

The control is therefore tracked only by the third branch of `_control_tracked`
(`code_csv_multiple_testing_dataflow_v3.py:14249-14254`), the outcome-headers branch. The emitted
reason asserts that hierarchical gatekeeping is *present*. Nothing in the source gates anything:
the comprehension runs every test unconditionally, and the tracked expression is the test of a
two-string `IfExp` whose value is printed. The reason is a false structural claim. Section 8
handles it.

The reason the p-origin count is zero is the same fact that causes the miss. The dict
comprehension is never normalized into the record model, so `results` stays opaque,
`result["p"]` resolves to no p-origin, and the frozen `_terminal_rendering_ifexp` exemption
(which requires exactly one p-origin or a resolved decision position) cannot fire.

The executed P3 ladder is:

| Rung | Shipped 3.3 outcome |
|---|---|
| sealed source | `hierarchical-gatekeeping-present` |
| hand-written explicit loop building the same dict | candidate/`none`, `N=6` |
| strict section-4 comprehension normalization | candidate/`none`, `N=6` |

The middle rung is the load-bearing one: an author who writes the identical computation as three
lines instead of one comprehension is already caught. The wall is spelling, not science.

The 3.3 terminal-presentation route does not reach P3 either. `_dict_field_for_name`
(`code_csv_multiple_testing_terminal_presentation_v3_3.py:532-557`) requires the verdict local to
appear as a value inside a record literal that is appended into a collection inside the same loop.
P3 prints the verdict immediately and appends nothing. The executed probe records
`dict_field_for_name = null` and `v33_admitted_positions = []` on both the sealed source and the
normalized source.

**E17 P6 `b4e507c4b55954752f14`** (seven declared outcomes, hand Bonferroni applied to a
name-set-selected subset of three):

| Observation | Value |
|---|---|
| shipped 3.3 first reason | `unresolved-manual-correction-present` |
| tracked hierarchy controls | **none**; P6 never reaches the hierarchy guard |
| AP factor resolution | `factor == len(OUTCOMES) == 7`, resolved |
| name-set selection predicate | evaluates correctly under `_static_bool` |
| `_complete_rows` on the loop | `None`: `enumerate(OUTCOMES, start=1)` is an `ast.Call`, and the row table requires `isinstance(loop.iter, ast.Name)` (`code_csv_multiple_testing_correction_model_v3_2.py:465-476`) |
| second reaching fold | the cap reassignment `corrected_p = 1.0` inside `if corrected_p > 1.0:` competes with the product, so `_fold_target_is_unique` returns the `single-reaching-fold` refusal |

The executed P6 ladder isolates both blockers:

| Rung | Shipped 3.3 outcome |
|---|---|
| sealed source | `unresolved-manual-correction-present` |
| bare-Name iterator only (`for outcome in OUTCOMES`) | `unresolved-manual-correction-present` |
| `min` cap only (`min(raw_p * N, 1.0)`) | `unresolved-manual-correction-present` |
| both hand rewrites | candidate/`strict_subset`, positions `{0,1,2}`, `N=7` |

Neither rewrite alone moves the case. Both are required, and both are purely syntactic
restatements of the same arithmetic.

### 0.2 Executed projection

The strict combined sweep observes exactly two classification movements:

```text
E17:P3:a2e031f79e31c80fd900 -> candidate none, corrected_positions {}, N=6
E17:P6:b4e507c4b55954752f14 -> candidate strict_subset, corrected_positions {0,1,2}, N=7
```

All 155 earlier evidence rows are outcome-identical. All other thirteen E17 rows are
outcome-identical. Corpus score remains `0/25` correct candidates and `19/25` misstep candidates.
Retro recall becomes E10 `5/6`, E11 `6/6`, E12 `6/6`, E13 `4/6`, E14 `4/6`, E15 `3/6`, E16 `4/6`,
E17 `6/6`.

Executed none-flip is:

```text
all correct fixtures           0 / 194
AP correct                     0 / 13
B5 expression variants         0 / 63
corpus-correct                 0 / 25
cumulative-v3 correct          0 / 62
frozen hierarchy fixtures      0 / 12
new 3.4 correct                0 / 11
opened negatives               0 / 72
3.1 laundering-adjacent        0 / 16
3.3 terminal/helper correct    0 / 17
```

The executed admission census, which records where each extension actually fired across all 170
cases and 245 fixtures, is:

```text
A comprehension normalization   16 admitted spans over 16 rows
C enumerate row table           16 admitted spans over 16 rows
D adjacent if-cap               5 admitted spans over 5 rows
B terminal IfExp (unshipped)    0 admitted spans over 0 rows

comprehension rows:
  E17:P3:a2e031f79e31c80fd900
  corpus:spec-37
  correct-comprehension-corrected-family
  correct-comprehension-gates-later-test
  correct-helper-record-conclusion-recomputed-from-raw-p
  correct-helper-record-conditional-store
  correct-helper-record-multiple-call-sites-divergent
  correct-helper-record-mutates-nonlocal-state
  correct-helper-record-nested-record
  correct-helper-record-unresolved-consumer
  correct-terminal-verdict-rebound-into-name
  correct-terminal-verdict-returned-from-helper
  correct-terminal-verdict-stored-then-printed
  positive-comprehension-dict-helper-record
  positive-comprehension-inline-flat-record
  positive-comprehension-list-form
enumerate rows:
  E17:P6:b4e507c4b55954752f14
  correct-ap-cap-assigns-other-value
  correct-ap-cap-augmented-reassignment
  correct-ap-cap-body-extra-statement
  correct-ap-cap-complete-correction
  correct-ap-cap-guard-not-literal-one
  correct-ap-cap-guard-on-different-name
  correct-ap-cap-non-adjacent
  correct-ap-cap-reassigns-other-name
  correct-ap-cap-with-else
  correct-ap-counter-used-in-decision
  correct-ap-enumerate-complete-correction-min
  positive-ap-cap-min-form-unchanged
  positive-ap-enumerate-no-start
  positive-ap-enumerate-start-one
  positive-ap-enumerate-start-zero
cap rows:
  E17:P6:b4e507c4b55954752f14
  correct-ap-cap-complete-correction
  positive-ap-enumerate-no-start
  positive-ap-enumerate-start-one
  positive-ap-enumerate-start-zero
terminal-ifexp rows: none
```

The executed reason-routing (section 8) relabel set, measured but **not applied**, is:

```text
evidence cases   0 of 170  (none)
fixtures         10 of 245
  frozen-gate-numpy-omnibus-assert
  frozen-gate-match-subject-and-guard
  frozen-gate-bool-short-circuit-assert
  frozen-gate-early-return
  frozen-gate-early-break
  frozen-gate-early-continue
  frozen-gate-early-raise
  frozen-gate-early-sys-exit
  correct-comprehension-keyword-argument-element
  correct-outcome-headers-early-exit
```

The canonical executed artifacts are:

```text
instrumentation  sha256:ee90ff2717d244cffd5faa6372a0fe04f81d28d2c76044ced9317b2756168c86
results          sha256:2bf626534a513e951e1c8a559a2538594f6dbb60e6bfda8e0787e0cd704a3cf2
manifest         sha256:e4236167657801613b79f55b1a57edeef770da4f3fdf0bf261d6f1673ff15790
```

The 52-file manifest binds 611,759 bytes.

The builder must pin these values and must not regenerate the design evidence.

### 0.3 Prototype-to-final direction

The shadow implements the closed grammars in sections 4 through 8 at design fidelity. It never
classifies a family. It proves one exact syntactic production, lowers or admits only that
production, and asks the unchanged shipped 3.3 analyzer to classify the result.

Two prototype techniques are development evidence only and are forbidden in production:

1. the comprehension lowering is executed as a source-span splice that replaces the comprehension
   statement's exact bytes with the equivalent explicit loop, leaving every other byte untouched.
   Production must produce the same normalized record graph as a graph fact beside the existing
   `_normalize_contract_domain_loops`, never by rewriting source text;
2. the iterator and cap admissions are executed by replacing four module-level functions in the
   correction model. Production must widen those recognizers in versioned copies, never by
   monkeypatching. The specified-but-unshipped section-5 production is installed only by the
   instrumentation probe that measures its E16 P4 collision.

Fidelity remains asymmetric at integration boundaries. A final implementation may be stricter;
none-flip from a looser shadow transfers in the safe direction, but a positive movement does not.
The final implementation must independently re-demonstrate E17 P3 and E17 P6 at their exact pinned
outcomes. A final abstention on one of those two pinned candidates is a section-20 stop, just as a
candidate on any pinned noncandidate is. Neither the grammar nor an oracle may be moved toward the
other.

## 1. Decision and hard boundary

Version 3.4 ships three narrow syntactic admissions. It specifies a fourth and does not ship it,
and it records one reason defect without correcting it. Both of those decisions are settled by
executed evidence, not left to taste. Version 3.4 adds no scientific classification rule:

1. **Comprehension normalization (A).** A dict or list comprehension whose single generator
   iterates the contract-order outcome sequence, carries no `if`, and whose element is one closed
   call or one flat literal record of scalars derived from the loop variable, is normalized into
   the same record-model form the equivalent explicit loop already produces: position-tagged
   per-outcome copies carrying p-origins.
2. **Terminal `IfExp` print-only production (B), specified and not shipped.** Section 5 states the
   production in full and records why it stays out of 3.4: it admits zero positions anywhere in the
   evidence, and on E16 P4 its one admitted position collides with the 3.3 single-occurrence
   requirement and destroys a pinned candidate.
3. **`enumerate` row-table iterator (C).** The AP row table admits `enumerate(NAME)` and
   `enumerate(NAME, start=K)` where `NAME` is the contract-order sequence. The outcome element of
   the two-Name loop target binds rows in contract order; `K` never enters position derivation.
   Any use of the counter in the correction or decision path refuses.
4. **Adjacent if-cap fold (D).** The exact two-statement pair `X = A * B` followed immediately by
   `if X > 1.0: X = 1.0` is one fold equivalent to `min(A * B, 1.0)`, admitted only when both
   statements are adjacent in the same block, the guard compares the same Name to the literal one,
   and the reassignment is the sole statement in the if-body.
5. **Outcome-headers reason routing (E), recorded and not applied.** Section 8 documents the
   observed mislabel, enumerates the routing options, executes two of them, and recommends keeping
   the current reason for 3.4 because the specified routing relabels eight genuine gatekeeping
   controls. It does not invent a reason.

After any admission, the existing 3.3/3.2/3.0 machinery alone decides candidate, covered, or
abstain. Version 3.4 adds no test API, correction form, threshold, family-position source,
row-mask route, reader, reducer, record mutation, conclusion polarity, or wording rule.

The following remain outside this delta:

- any comprehension with a filter, multiple generators, a non-contract or reordered sequence, a
  key other than the generator target, a conditional or nested element, a keyword-carrying element
  call, or a collected name that is rebound or mutated;
- any verdict local that is stored, returned, aliased, or rebound anywhere outside the closed print
  transport;
- any iterator other than a bare contract-sequence Name, `enumerate(NAME)`, or
  `enumerate(NAME, start=K)` with `K` an integer literal; any use of the counter in a correction or
  decision path;
- any cap that is non-adjacent, guarded on another Name, guarded against a value other than the
  literal one, carries an `else`, or whose if-body holds any other statement;
- E17 P5's library-subset cardinality and every 3.2/3.3 residual; and
- changes to the 3.1 question/attestation trust rule or envelope scoring.

## 2. Identities, contract, frozen surfaces, wording, and ADR obligation

### 2.1 Development identities

The new identities are:

```text
check_id         check:authorized-complete-family-correction-over-code-test-battery
check_version    3.4.0
detector_id      detector:bounded-code-csv-multiple-testing-conflict
detector_version 3.4.0
adapter_version  3.4.0
binding_id       method-conflict-binding:authorized-complete-family-correction-over-code-test-battery-v1:development
```

Only the development binding advances. Versions 1.0, 1.1, 2.0–2.3, and 3.0–3.3 remain registered
for replay. Qualified pseudoreplication `3.1.0`, its GrantPin, grants, qualification records, metric
sets, threshold policies, wording profiles, and `method_conflict_grant_pins.py` remain byte-untouched.

Contract profile `1.2.0` is unchanged. `N`, the group column, ordered outcome family, and authorized
CSV snapshot come only from that contract and existing structural proof.

### 2.2 Frozen 3.1/3.2/3.3 anchor plan

The build pins these current bytes before creating any versioned copy. Each is asserted in a test
that reads the file and compares the digest, so a stray edit fails the suite rather than the review.

```text
dataflow v3                    sha256:498bf5c22305270fe64ed1ef73b7ac8a7a2637ce4f64520e8d9ca4ac15166618
dataflow v3_2                  sha256:38f74309c4ba082dceb335d95691401b7f9b780958d1c0b82bdb63e496fc29c2
correction model v3_2          sha256:b7c182a9bac2e6e3eb015c2902e607201a5bfdca5f0889413b1145911d30b239
dataflow v3_3                  sha256:c82510238b422af746299e9e1c418a0474107d1b57d119fd7dc5685e037edd2e
record model v3_3              sha256:d9d919b5289c767a39dd62edea8fc17563a6ad76aa627c49e427b6201f81bf4a
correction model v3_3          sha256:de46498474b0043231a66b6adeb779e799b3736afce162b6919dc0eebc516242
terminal presentation v3_3     sha256:d1b9463235494ae54d4c5d2bbc3eb4f0d1b73568a4c5625993dd87dbee4b5c78
helper record v3_3             sha256:f3c5e8fb9ec52f8e2d13a6de11849f63b08a073e4208f9d5936fbcf177c76033
adapter v3_3                   sha256:7c3ce13e3e10fcf012bf4c803f6a5e3bd88aa30146059873710b8a549550efcc
integration v3_3               sha256:edc5b3d94329a15c263dbab167bc623be7f778bca5b867d771f9538642719557
detector v3_3                  sha256:0b7505fb42d191be0916f287eeea72dfc4d579edbc2a367ec413b503e1670e4c
scope questions v3_3           sha256:b060f34c52c64db7f36ca1e2469239e6a6920404ecee87c13e986f526c59ff3b
3.3 design                     sha256:cbc37990e9a713c486bf903cefef03c08ad264e7b6112383330b56a0c3f6c224
3.3 prototype results          sha256:be9ddd1ea4b8bd27faff92392865cbb76f14fbf6b162f847523fe5900d1bd7ad
3.3 prototype manifest         sha256:10e94f5a056e50662bfc65bfafc2ebec0ea519a4c7bef1f5269caddf6523bf5f
3.3 prototype instrumentation  sha256:03c7aa815b8728bf9452afe666f9738e9501f345903ce7ef7fe3f520c320134f
3.3 adapter replay records     sha256:4b42ee3a517bd95591eac9f0d7bb9a497728f9df708c57fc99298d7205df83ce
E17 role map                   sha256:004a87be3448c1736f24ac48d0deb155694ee7da08670d02918ac8e09d4cea9e
E17 audit results              sha256:ca9cb2caf2b4fd0c4047a7758f0351278f7bd66f79f1dacaf6af0754a47b4b6e
```

The 3.3 adapter must replay all 170 source inputs through its historical path without byte drift.
The new 3.4 comparison rows are additive. Frozen corpus replay records and all earlier comparison
rows are never regenerated.

The 3.1 anchors carry forward unchanged from the 3.2 and 3.3 anchor lists: the question oracle, the
answer-removal equivalence gate, the false-clearance gate, the four-record-type gate, and the
scoring-isolation gate all run against 3.4 bytes without modification.

### 2.3 Wording and evidence

Wording profile v2 is unchanged. Both movements use the already-defined candidate/`none` and
candidate/`strict_subset` classifications and existing slots. No new visible string is required by
sections 4 through 7. Section 8 is the only place where a visible reason string can change, and it
is deliberately routed to an already-registered reason.

Evidence for a comprehension normalization records only node type, source span, comprehension kind,
element kind, collected-name identity, generator-target identity, and the contract-order sequence
identity. Evidence for an iterator admission records the loop span, the sequence identity, and the
contract positions derived from sequence order. Evidence for a cap admission records the product
span, the guard span, and the reassignment span. None of these record display text or infer meaning
from a local, field, function, comment, report, Markdown, or format-string spelling.

String displays remain structural only: `ast.Constant` string, nonempty, no NUL, at most 256 UTF-8
bytes. The cap is measured; the bytes are never matched to words. Literal record keys may identify
the same structural field edge, but key text never supplies p or conclusion semantics; lineage does.

### 2.4 ADR-0079 amendment

This delta changes candidate eligibility by normalizing a collection form and by widening two AP
recognizers. The development binding cannot advance until ADR-0079 records:

1. the observed E17 P3 and P6 trigger attribution in 0.1, including the zero-p-origin
   outcome-headers finding;
2. the exact comprehension grammar and its lowering in section 4;
3. the exact print-only terminal `IfExp` production in section 5, its executed zero-admission
   result, its executed E16 P4 collision, and the decision not to ship it;
4. the exact `enumerate` row-table admission in section 6 and the counter-opacity rule;
5. the exact adjacent if-cap absorption in section 7 and its equivalence argument;
6. the section-8 observed mislabel, its executed relabel measurement, and the decision to keep
   the current reason in 3.4;
7. that the hierarchy registry remains global and that section 8 changes only which reason is
   emitted, never whether an abstention occurs;
8. that classification, correction recognition, row completeness, and wording remain unchanged;
9. the executed two-row movement set, all none-flip populations, and the admission census; and
10. the question-census delta in section 14 and the prototype/final asymmetric stop rule.

## 3. Unchanged global censuses, guard universe, and ordered integration

### 3.1 Whole-module censuses stay whole-module

The registered-test, correction-terminal, statistics-prefix, repeated-construct, dynamic-execution,
API-rebinding, and outcome-sequence-mutation censuses run on the untouched AST before any 3.4
normalization or admission. No normalization or surrogate can hide a census fact.

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

Correction terminal slots, statistics prefixes, the dynamic-execution list, and the API-rebinding
rule are byte-identical to the 3.3 design's section 3.1. Version 3.4 adds nothing to any of them.

That the censuses run first is not a formality. It is the blocker for the strongest attack on
extension A: a normalized comprehension family that also contains a later gated test. The census
sees the original bytes, counts the extra registered call, and returns
`authorized-family-test-census-incomplete` before any 3.4 predicate runs. The
`correct-comprehension-gates-later-test` fixture executes exactly that.

### 3.2 The hierarchy universe remains global

The control registry continues to include, over the whole module, every node kind listed in the 3.3
design's section 3.2: registered-test arguments, correction arguments, conclusion operands,
family-container insertions, `ast.If.test`, `ast.IfExp.test`, `ast.While.test`, loop
iterable/condition nodes, `ast.Assert.test`, `ast.Match.subject`, `match_case.guard`, boolean
short-circuit operands, and every `return`, `break`, `continue`, `raise`, and `sys.exit` edge whose
evaluation can prevent a slice node from executing.

Version 3.4 removes no node kind and no owner class from this registry. Extension A changes what the
guard *sees* only by giving the record model a resolvable p-origin, which is exactly what the
equivalent explicit loop already does. Extension E changes which reason a tracked control emits, not
whether it is tracked.

### 3.3 Ordered integration

The 3.4 analyzer order is:

1. run every unchanged adapter precondition and global census on original bytes;
2. run the complete unchanged 3.3 pipeline, including its terminal-presentation and helper-record
   proofs, and record its result;
3. if that result is a classification, return it untouched. **No 3.4 admission is attempted**;
4. otherwise re-analyze with the section-4 comprehension normalization in the normalization phase
   and the section-6 and section-7 admissions inside the unchanged 3.2 AP recognition;
5. adopt the re-analysis only if it is itself a classification. If it abstains, return the
   step-2 abstention reason byte-for-byte; and
6. return the reason byte-for-byte. Section 8 records an observed mislabel in that reason and,
   on the executed evidence, recommends against routing it in 3.4.

Steps 3 and 5 are the load-bearing ordering rule, and it was chosen against executed evidence rather
than on principle. An earlier revision of this design ran the comprehension normalization
unconditionally, on the argument that a recognizer whose behavior depends on which failure came
first is a worse recognizer. The sweep refuted that argument on two rows:

| Row | Unconditional 3.4 | Cause |
|---|---|---|
| E16 P3 `5a9c5b4377c33916d672` | candidate/`none` `N=5` becomes `pderived-conclusion-family-incomplete` | normalization resolves the p-lineage, the first reason stops being `unresolved-pvalue-consumer`, and the frozen 3.3 helper-record route that produced the pinned candidate is never attempted |
| E16 P4 `9ced761b41ef93485acf` | candidate/`none` `N=7` becomes `hierarchical-gatekeeping-present` | the section-5 production admits one extra position, so `prove_terminal_presentation` sees two and returns `None`, losing the 3.3 exclusion |

Under steps 3 and 5, every frozen 3.3 classification and every frozen 3.3 abstention reason survives
by construction. The only rows 3.4 can move are abstentions it converts into classifications. That is
a strictly stronger safety property than the version this design started with.

Section 5's disposition follows from the second row and is settled in 5.4.

If a 3.4 re-analysis merely exposes a different abstention, the frozen reason stands. Normalizations
are not iterated toward a candidate.

## 4. Closed contract-order comprehension grammar (extension A)

### 4.1 The admitted production

The admitted statement is exactly one of:

```text
TARGET = {LOOPVAR: ELEMENT for LOOPVAR in SEQUENCE}
TARGET = [ELEMENT for LOOPVAR in SEQUENCE]
```

and it is normalized into exactly:

```text
TARGET = {}                              TARGET = []
for LOOPVAR in SEQUENCE:                 for LOOPVAR in SEQUENCE:
    TARGET[LOOPVAR] = ELEMENT                TARGET.append(ELEMENT)
```

after which the frozen `_normalize_contract_domain_loops` machinery produces the position-tagged
per-outcome record copies it already produces for a hand-written loop. Version 3.4 introduces no new
record-model construct: the normalized graph is the graph the analyzer already knows how to read.

Admission requires all of the following, each a syntactic fact about the AST:

1. the statement is one `ast.Assign` with exactly one `ast.Name` target, or one `ast.AnnAssign` with
   an `ast.Name` target and a value;
2. the value is one `ast.DictComp` or `ast.ListComp` with exactly one generator;
3. the generator is not async, has **no** `ifs`, and its target is one simple `ast.Name`;
4. the generator's iterable is one bare `ast.Name` that resolves to a module-level flat
   list/tuple display of scalar literals, bound exactly once, never augmented, deleted, subscript-
   stored, or mutated through `append`/`extend`/`insert`/`pop`/`remove`/`clear`/`sort`/`reverse`;
5. that resolved sequence is **order-equal** to the contract outcome column tuple. Equal membership
   in a different order is refused;
6. for the dict form, the comprehension key is exactly the generator target Name;
7. `ELEMENT` is either `CALL` or `RECORD`, defined in 4.2;
8. `ELEMENT` loads the generator target at least once, so the family is genuinely per-outcome;
9. `TARGET` differs from the generator target, has exactly one Store or Del occurrence in the whole
   module, and is never augmented, deleted, subscript-stored, or receiver-mutated anywhere else.

### 4.2 The closed element grammar

`SCALAR` is the smallest closure that covers a per-outcome column read and a summary statistic:

```text
SCALAR := Constant (not bytes, not Ellipsis)
        | Name
        | Attribute(value=SCALAR)
        | Subscript(value=SCALAR, slice=Constant | Name)
        | BinOp(SCALAR, op, SCALAR)
        | UnaryOp(op, SCALAR)
        | Tuple(SCALAR*) | List(SCALAR*)
        | Call(func=Name | Attribute(value=SCALAR), args=SCALAR*, keywords=[])
```

`CALL` is one `ast.Call` that is itself a `SCALAR`. `RECORD` is one `ast.Dict` with at least one
entry, every key a non-null literal `str` or `int`, keys unique, and every value a `SCALAR`.

No node anywhere inside `ELEMENT` may be an `ast.Lambda`, `ast.NamedExpr`, `ast.Await`, `ast.Yield`,
`ast.YieldFrom`, `ast.IfExp`, `ast.Starred`, `ast.GeneratorExp`, `ast.DictComp`, `ast.ListComp`,
`ast.SetComp`, `ast.JoinedStr`, or `ast.Slice`, and no `ast.Call` inside `ELEMENT` may carry
keywords. Those are absolute refusals, checked over the whole element subtree.

The element grammar reads no spelling. `compare_settings`, `stats.ttest_ind`, `mean`, and `p` are
all just callees, attributes, and keys; what makes an element admissible is its shape, and what
makes the resulting family a test battery is the unchanged registered-test census.

### 4.3 The lowering is graph-preserving

The normalization must satisfy two properties that the prototype asserts on every execution:

1. **element identity.** The lowered element is the same graph as the original element. The
   prototype re-parses its own lowered element text and compares `ast.dump` against the original
   node; a mismatch raises rather than proceeding. Production, working on graphs, satisfies this by
   construction, but must still assert it.
2. **idempotence.** Applying the normalization to an already-normalized module admits nothing and
   changes no byte. The prototype asserts this on every row.

Everything outside the comprehension statement's own span is untouched. Global censuses, the
threshold grammar's source-text Decimal handling, and every span-derived evidence value therefore
see the same bytes they saw before.

### 4.4 Named disqualifiers

Every row below is an executed fixture. Each asserts that the comprehension admission **does not
fire at all**, measured against the executed admission census, which cannot be satisfied by an
accidental abstention downstream.

| Fixture | Disqualifying fact |
|---|---|
| `correct-comprehension-with-filter` | the generator carries an `if` |
| `correct-comprehension-over-non-contract-sequence` | the sequence is a three-name screening list |
| `correct-comprehension-key-not-loop-variable` | the dict key is `LABELS[outcome]` |
| `correct-comprehension-two-generators` | two generators |
| `correct-comprehension-conditional-element` | the element is an `IfExp` |
| `correct-comprehension-nested-element` | the element contains a nested list comprehension |
| `correct-comprehension-keyword-argument-element` | the element call carries a keyword |
| `correct-comprehension-out-of-contract-order` | the sequence is the contract set reversed |
| `correct-comprehension-target-rebound` | the collected name is rebound by a second comprehension |
| `correct-comprehension-collection-mutated` | the collection is subscript-stored after construction |
| `correct-comprehension-element-ignores-loop-variable` | the element reads one fixed column |
| `correct-outcome-headers-genuine-screen` | the collection is built under a per-outcome screen |
| `correct-outcome-headers-early-exit` | an execution-prevention edge precedes the family |

Two positive controls assert the admission fires and the pinned outcome follows:
`positive-comprehension-dict-helper-record` (the exact E17 P3 source, candidate/`none`, `N=6`) and
`positive-comprehension-inline-flat-record` (a flat literal record element). A third,
`positive-comprehension-list-form`, asserts the list form is admitted and records its residual;
see 4.5.

### 4.5 The list-form residual, stated plainly

The list form is admitted by the grammar and lowers correctly. It does not currently reach a
candidate. The executed `positive-comprehension-list-form` fixture normalizes cleanly and then
abstains at `test-battery-cardinality-unresolved`, because the 3.0 record model resolves a
per-outcome mapping keyed by outcome, not a positional list zipped back to the contract sequence at
presentation time.

Under the section 3.3 ordering rule this residual costs nothing at all. A 3.4 re-analysis that
abstains returns the frozen 3.3 reason byte-for-byte, so an admitted list comprehension that does not
reach a classification leaves the public record exactly as 3.3 left it. The reason recorded above is
what the re-analysis produced internally, not what the detector emits.

Two dispositions are still available, and the reviewer may pick either:

- **Ship both forms** (this design's recommendation). The grammar then proves the syntactic property
  it claims to prove, and the list form's residual is a record-model limit recorded honestly.
- **Ship the dict form only.** Nothing in the evidence moves either way, and the recognizer gains a
  condition that encodes a downstream limitation rather than a property of the source.

Neither disposition changes a movement, a none-flip count, an emitted reason, or the question census.

## 5. Terminal `IfExp` print-only production (extension B), specified and not shipped

**Disposition: extension B is fully specified below and is NOT part of the shipped 3.4 recognizer
set.** The executed evidence in 5.4 is decisive: it admits zero positions on any evidence row, and
on E16 P4 the one position it does admit destroys a pinned 3.3 candidate. The specification is kept
here in full, with its executed disqualifier proofs, so a later delta can pick it up with the
collision already characterized.

### 5.1 What 3.3 already proves

`_terminal_ifexp_positions` admits an `IfExp` with two display-string arms, bound once to a simple
Name inside `main`, whose test is a single p-comparison, provided seven conditions hold: no later
test or helper test is reachable, no later controlled exit is reachable, the verdict has exactly one
Store, every verdict load is either a print payload or the one record-append value, the appended
record's collection carries a proved terminal count for that field, and the collection itself is
terminal-safe.

The fifth condition is implemented through `_dict_field_for_name`, which requires that a record
literal containing the verdict be appended into a collection inside the same loop. A source that
computes the verdict and prints it immediately has no such collection, so `field` is `None` and the
whole production refuses.

### 5.2 The 3.4 addition

When `_dict_field_for_name` returns `None`, the production is admitted if and only if:

1. every one of the six other 3.3 conditions holds unchanged (display-string arms, single-Name
   binding in `main`, single p-comparison test, no later test or helper test, no later controlled
   exit, exactly one verdict Store);
2. **every** load of the verdict local reaches the closed 3.3 print transport (`_reaches_print`);
   and
3. **no** load of the verdict local is stored anywhere. A load is refused if any ancestor before the
   enclosing `ast.Expr` is a `Dict`, `List`, `Tuple`, `Set`, `Assign`, `AnnAssign`, `AugAssign`, or
   `Return`, or is a `Call` that is a method call or any call other than an unshadowed `print`.

Conditions 2 and 3 are separately enforced. Reaching a print is not sufficient: a verdict may be
printed *and* stored, and the store is what matters.

The two collection-specific conditions (`_terminal_count_for_field` and
`_collection_terminal_safe`) are skipped only because there is no collection to prove anything
about. When a collection exists, 3.3's path runs unchanged and both conditions still apply.

### 5.3 Named disqualifiers, proved at grammar level

Each fixture below is a correctly Bonferroni-corrected six-outcome analysis, so a candidate on any
of them would be a genuine false accusation. Because extension B is not installed in the shipped
recognizer set, these three carry no admission-census assertion. Their refusal is proved directly
instead: the executed `terminal_ifexp_refusal_probe` in `instrument_results.json` calls the
section-5 production on each fixture's AST and records that it admits nothing.

| Fixture | Disqualifying fact |
|---|---|
| `correct-terminal-verdict-stored-then-printed` | the verdict is appended to a list before printing |
| `correct-terminal-verdict-rebound-into-name` | the verdict is formatted into a second local |
| `correct-terminal-verdict-returned-from-helper` | the verdict is produced by a helper `return` |

### 5.4 Why extension B is not shipped

Two executed facts, in order of weight.

**It regresses E16 P4.** `prove_terminal_presentation` requires that the whole module yield exactly
one admitted terminal position and exactly one occurrence; otherwise it returns `None` and no
exclusion is made. On E16 P4 the frozen 3.3 proof admits one `If` position and zero `IfExp`
positions, which satisfies that requirement and produces the pinned candidate. The section-5
production admits one additional `IfExp` position on the same source. The executed
`extension_b_collision_probe` records:

| Observation | E16 P4 `9ced761b41ef93485acf` |
|---|---|
| 3.3 admitted `If` positions | `((96, 11, 96, 36),)` |
| 3.3 admitted `IfExp` positions | `()` |
| section-5 admitted `IfExp` positions | `((82, 35, 82, 60),)` |
| outcome without extension B | candidate/`none`, `N=7` |
| outcome with extension B | `hierarchical-gatekeeping-present` |

A pinned 3.3 candidate is lost. That alone settles the disposition.

**It moves nothing.** Across all 170 evidence cases and all 245 fixtures, the section-5 production
admits zero positions on any row the shipped pipeline abstains on. Under extension A, E17 P3's
`result["p"]` resolves to a p-origin and the frozen `_terminal_rendering_ifexp` exemption in the
hierarchy guard accepts the verdict `IfExp` before the 3.3 terminal-presentation proof is ever
consulted. The 3.3 proof is reached only when that frozen exemption fails, and wherever it fails in
this evidence, `_structural_p_roots` also fails to resolve the p, so the section-5 branch refuses
for an unrelated reason. The executed `dict_field_probe` records `v34_admitted_positions = []` on
both the sealed and the normalized E17 P3 source.

So the specified production has zero measured upside and one measured regression. It is specified
and not shipped.

The shape it covers is real but unwitnessed: a compute-verdict-print-immediately source whose p
resolves structurally but not through `_p_origins`. A later delta that wants it must first decide
what `prove_terminal_presentation` should do when more than one position is admissible, which is a
3.3 design question rather than a 3.4 grammar question. This design does not answer it.

Sections 4, 6, and 7 each carry a pinned movement. Section 5 does not, and its absence changes no
number anywhere else in this design.

## 6. `enumerate` row-table iterator (extension C)

### 6.1 The admitted production

`_complete_rows` currently requires `isinstance(loop.iter, ast.Name)`. Version 3.4 adds exactly one
alternative:

```text
for COUNTER, OUTCOME in enumerate(SEQUENCE):
for COUNTER, OUTCOME in enumerate(SEQUENCE, start=K):
```

admitted only when:

1. the callee is the unshadowed simple Name `enumerate`;
2. there is exactly one positional argument and it is a bare `ast.Name`;
3. keywords are either absent, or exactly one `start=` whose value is an integer literal (never a
   Name, never a bool);
4. that Name resolves through the unchanged `_module_sequences` to a stable flat literal sequence;
5. the loop target is an exact two-element tuple or list of distinct simple Names;
6. the sequence length equals the contract family size; and
7. the sequence elements, read in order, equal the contract outcome column tuple.

Position derivation is unchanged. Positions come from the index of each element **in the sequence**,
exactly as they do for a bare-Name iterator. `K` is never consulted, which is why `start=0`,
`start=1`, and an absent `start` all produce the identical row table and the identical corrected
positions. Three positive fixtures assert exactly that.

### 6.2 The counter is opaque

The counter name is bound in every row to a distinguished object that is neither a `bool` nor any
contract outcome string. Every structural predicate that can read a row value tests for one of
those two things:

- `_static_bool` returns the row value only when it is a `bool`, and otherwise `None`. `None`
  propagates to `_positions_for`, which returns `None`, which refuses the fold. So a branch guarded
  on the counter refuses.
- the contract-order check compares row values against outcome strings. The counter never matches.

The counter therefore cannot select positions, cannot supply a factor, and cannot gate a fold. This
is a structural property of the binding, not a lint against the identifier.

Two correct-analysis fixtures exercise it. `correct-ap-counter-used-in-decision` branches the
correction on `position <= 3`; `correct-ap-counter-used-as-factor` multiplies the raw p by
`position`. Both stay at `unresolved-manual-correction-present`.

The first of those two is the more informative row, and the admission census shows why. The
`enumerate` row table **is** admitted on it: the iterator is exactly the admitted form. The refusal
happens one layer down, when `_static_bool` reads the counter binding out of the row, finds neither
a `bool` nor an outcome string, and returns `None`. That is the property this design wants. The
iterator admission does not decide anything about the correction; it only makes the row table
readable, and the frozen machinery then refuses on its own terms.

### 6.3 Named disqualifiers

| Fixture | Disqualifying fact |
|---|---|
| `correct-ap-enumerate-over-non-contract-sequence` | enumerates the three-name subset |
| `correct-ap-enumerate-over-zip` | the argument is `zip(...)`, not a bare Name |
| `correct-ap-enumerate-single-target` | the target is one Name unpacked in the body |
| `correct-ap-enumerate-nonliteral-start` | `start=N_COMPARISONS` is not an integer literal |
| `correct-ap-enumerate-reversed-sequence` | the argument is `list(reversed(OUTCOMES))` |

Each asserts the `enumerate` admission does not fire.

`correct-ap-enumerate-complete-correction-min` is the load-bearing false-accusation control: the
same `enumerate(OUTCOMES, start=1)` loop applying the hand fold to **all seven** outcomes must reach
covered/`complete` with positions `{0,…,6}`, not a strict-subset candidate. A position-derivation
error in extension C would show up here as an accusation against a correct analysis. It does not.

## 7. Adjacent if-cap fold (extension D)

### 7.1 What is already admitted

`_match_adjustment` already recognizes `min(RAW * FACTOR, 1)` and `numpy.minimum(RAW * FACTOR, 1)`
as a capped product, and the bare product `RAW * FACTOR` as an uncapped one. Version 3.4 changes
neither.

### 7.2 The admitted pair

The two-statement pair

```text
X = A * B
if X > 1.0:
    X = 1.0
```

is one fold equivalent to `min(A * B, 1.0)`. It is admitted only when:

1. the first statement is one `ast.Assign` with a single `ast.Name` target `X` and an
   `ast.BinOp` value whose operator is `ast.Mult`;
2. the second statement is the **immediately following** statement in the **same** block;
3. the second statement is an `ast.If` with no `orelse`;
4. its test is one `ast.Compare` with one operator and one comparator, in one of exactly four
   forms: `X > 1`, `X >= 1`, `1 < X`, `1 <= X`, where the Name is `X` and the literal is numeric one
   (never a bool);
5. its body holds exactly one statement, an `ast.Assign` with a single `ast.Name` target `X` and a
   numeric-one literal value.

All four comparison forms compute `min(X, 1.0)` exactly. The `>=` and `<=` forms assign `1.0` when
`X` is already `1.0`, which is a no-op.

### 7.3 What the admission changes, exactly

Three things, and nothing else:

1. the cap reassignment is excluded from the competing-assignment set in the single-reaching-fold
   proof, so the pair counts as one fold rather than two;
2. the cap `ast.If` is transparent in `_positions_for`. It is not a family-position selector: it
   chooses between `A * B` and `1.0` for the *same* position, which is what `min` does. Every other
   `ast.If`, and every `Try`, `While`, `Match`, and `With`, behaves exactly as under 3.3;
3. the surrogate lowering drops the whole cap statement together with its fold, exactly as
   `min(A * B, 1.0) -> RAW` drops it. Without this the surrogate would retain
   `if RAW > 1.0: X = 1.0`, whose `1.0` reads as a second decision threshold and abstains at
   `unresolved-decision-threshold`. This was observed during design and is why the rule is stated
   rather than assumed.

Nothing else about the correction model moves. Factor resolution, name-set selection, transport
proofs, conclusion consumption, and classification are untouched.

### 7.4 Named disqualifiers

| Fixture | Disqualifying fact |
|---|---|
| `correct-ap-cap-non-adjacent` | a `print` sits between the product and the cap |
| `correct-ap-cap-guard-on-different-name` | the guard tests `raw_p`, not `corrected_p` |
| `correct-ap-cap-guard-not-literal-one` | the guard tests against `ALPHA` |
| `correct-ap-cap-body-extra-statement` | the if-body also prints |
| `correct-ap-cap-with-else` | the `if` carries an `else` arm |
| `correct-ap-cap-assigns-other-value` | the reassignment writes `0.999` |
| `correct-ap-cap-augmented-reassignment` | the reassignment is `corrected_p -= 0.0` |
| `correct-ap-cap-reassigns-other-name` | the reassignment writes `raw_p` |

Each asserts the cap admission does not fire, and each stays at its baseline abstention.

`positive-ap-cap-min-form-unchanged` asserts the frozen `min` spelling still reaches
candidate/`strict_subset` `{0,1,2}` of 7 **without** the cap admission firing, which proves 3.4 did
not accidentally re-route the frozen path.

`correct-ap-cap-complete-correction` is the equivalence proof and the load-bearing
false-accusation control: the if-cap applied to all seven outcomes reaches covered/`complete`
`{0,…,6}` of 7, the identical result the `min` spelling produces
(`correct-ap-enumerate-complete-correction-min`). Two spellings of the same arithmetic produce the
same coverage record. That is the whole claim of extension D, executed.

## 8. Outcome-headers reason routing (extension E)

### 8.1 The observed defect

`_control_tracked` returns `True` on three disjunctive branches: a resolved p-origin, a correction
control, or two or more outcome headers read from a reader-rooted frame. When only the third branch
matches, the analyzer has proved that a control expression *reads outcome columns*. It has **not**
proved a p-origin, a correction dependence, or any execution-prevention edge. Emitting
`hierarchical-gatekeeping-present` on that evidence asserts a gate that was never demonstrated.

E17 P3 is the observed instance: one tracked control, zero p-origins, no correction control, six
outcome headers, and no gate anywhere in the source.

The scope of the correction is deliberately narrow, and its attribution rule is deliberately
conservative. One analyzer call can run the hierarchy guard more than once: the frozen 3.2 pass
runs it, and a 3.3 re-analysis under a proved terminal exclusion runs it again. Attributing the
emitted reason to the first tracked control of the first pass would be a guess about which pass
produced the reason. The routing therefore applies only when:

1. the returned reason is `hierarchical-gatekeeping-present`;
2. at least one control was tracked during the call; and
3. **every** tracked control, across every guard invocation in that call, is a control-registry
   expression with zero p-origins, no correction control, and at least two outcome headers.

Condition 3 can only under-route. A call in which any tracked control carried a p-origin, a
correction dependence, or arrived through the boolean short-circuit loop or an execution-prevention
edge keeps `hierarchical-gatekeeping-present` unchanged, because on those paths the analyzer has
either proved p-dependence or `can_prevent_slice` has proved that evaluation can suppress a slice
node. `correct-outcome-headers-early-exit` executes the execution-prevention case and keeps the
original reason.

### 8.2 The choice, and what each option costs

This design does not create a reason. The three options are:

**Option 1: route to `pvalue-control-dependence-unresolved`.** This reason is already in the closed
61 and is already emitted for the unresolved execution-prevention residual. It says what the
analyzer knows when only the outcome-headers branch matched: a control that may depend on p-values
could not be resolved.

The prototype executed option 1 in parallel with option 2 on every row. What it measured changed
the recommendation:

- **zero** of the 170 evidence cases relabel. E17 P3, the row that motivated the correction, becomes
  a candidate under extension A and no longer abstains at all;
- **ten** fixture rows relabel, and **eight** of them are frozen gatekeeping controls:
  `frozen-gate-numpy-omnibus-assert`, `frozen-gate-match-subject-and-guard`,
  `frozen-gate-bool-short-circuit-assert`, `frozen-gate-early-return`, `frozen-gate-early-break`,
  `frozen-gate-early-continue`, `frozen-gate-early-raise`, and `frozen-gate-early-sys-exit`. The
  other two are `correct-comprehension-keyword-argument-element` and
  `correct-outcome-headers-early-exit`.

Those eight fixtures exist to prove that a genuine screen-then-test gate keeps its reason. Each one
really does gate: an `assert`, a `match`, a short-circuit, or an early `return`/`break`/`continue`/
`raise`/`sys.exit` sits under a control the guard tracked. For them,
`hierarchical-gatekeeping-present` is the accurate claim and `pvalue-control-dependence-unresolved`
is a downgrade.

The condition set in 8.1 cannot separate those eight from E17 P3. Both classes have a registry
control with zero p-origins, no correction control, and two or more outcome headers. The
discriminator that would separate them is not a property of the control expression at all: it is
whether the control's owner subtree contains a registered test and whether `can_prevent_slice`
holds for any exit edge under it, which is 3.3's `TERMINAL` conditions 4 and 6. Adding that proof is
a real design item, not a routing tweak, and it is out of scope here.

**Option 2: keep `hierarchical-gatekeeping-present` and record the mislabel as a residual.** The
public record stays byte-identical everywhere, and the eight frozen gatekeeping controls keep their
accurate reason. The cost is that a source like E17 P3 would have been reported as
gatekeeping-present in a real deployment, which is a false structural claim in an abstention.

**Option 3: add a new reason.** Accurate and non-broadening, and it is the option a clean-sheet
design would take. It requires a new-reason stop per standing rules: the closed set moves from 61 to
62, and the reason registry, the question classification map, the closed-set gate, the wording
profile review, and the unreachable-reason annex all move with it. It also still needs the
execution-prevention and test-census proof described above, because without it the new reason would
be applied to the same eight gatekeeping fixtures. This design does **not** take option 3
unilaterally and does not pre-write the reason string.

**Recommendation.** Option 2 for 3.4, on the executed evidence. Option 1 as specified in 8.1 is too
coarse: it relabels eight genuine gates and zero real evidence rows, which is the wrong trade in
both directions. The accurate correction needs a terminality proof on the control's owner subtree,
and that belongs in a delta that can execute it against the full gatekeeping population. Recording
the defect and its measured blast radius is the useful output of section 8; changing the string is
not.

The prototype executes options 1 and 2 side by side and keeps both. Every row records `outcome`
(option 2, reason unchanged, and the value every gate in this design is computed on) and
`outcome_with_reason_routing` (option 1). Choosing between them changes no other number in this
design.

## 9. Classification and closed reasons

### 9.1 Classification is frozen

After admission, classification is exactly the existing 3.3/3.2 result:

- raw conclusions for all `N` positions with no recognized correction -> candidate/`none`;
- a proved proper corrected subset with raw conclusions outside -> candidate/`strict_subset`;
- complete recognized correction and corrected conclusions -> covered/`complete`;
- any unresolved graph fact -> the existing abstention reason.

The shipped admissions never create corrected positions, change `N`, choose an API, or alter a
conclusion. They let frozen analysis see a family and a fold that a different spelling of the same
program already exposes.

### 9.2 Closed reason set remains 61

No reason is added, retired, or relabeled. The 3.4 closed set is byte-identical to the 3.3 set
enumerated in the 3.3 design's section 6.2. Section 8 option 1 changes which of those 61 is emitted
on a specific proved branch; it does not change the set.

The build gate asserts `closed reasons == emitting reasons + documented-unreachable annex` using
only 3.4 test files. Every 3.4 refusal uses the already-owning guard's reason. No admission may
invent a shape-specific reason to make a fixture legible.

## 10. Load-bearing false-accusation analysis

The accusation-safety invariant is:

> A comprehension is normalized only after proving it is the exact contract-order per-outcome
> collection an explicit loop would build; an iterator is admitted only after proving rows come from
> the contract sequence and the counter is inert; a cap is absorbed only after proving it computes
> `min(p * F, 1.0)` on the same position. Global censuses run on original bytes and the unchanged
> classifier then proves the scientific claim independently.

The strongest correct-analysis attacks and their blockers:

| Admission | Strongest correct-analysis shape | Required blocker | Executed fixture |
|---|---|---|---|
| comprehension | a normalized family plus a later p-gated confirmatory test | untouched whole-module test census on original bytes | `correct-comprehension-gates-later-test` |
| comprehension | a screened subset collected by a filtered comprehension | no `ifs` in the generator; contract-order sequence equality | `correct-comprehension-with-filter` |
| comprehension | a per-outcome screen that really does gate the test | admission refuses; the guard keeps its reason | `correct-outcome-headers-genuine-screen` |
| comprehension | an execution-prevention edge before the family | `can_prevent_slice`; the guard keeps its reason | `correct-outcome-headers-early-exit` |
| comprehension | a correctly Bonferroni-corrected comprehension family | unchanged threshold and classification: covered, not accused | `correct-comprehension-corrected-family` |
| comprehension | the collection is mutated after construction | single-Store and no-mutation proof on the collected name | `correct-comprehension-collection-mutated` |
| terminal `IfExp` (specified, not shipped) | a verdict printed and also stored | total-consumer and no-store proof, run at grammar level | `correct-terminal-verdict-stored-then-printed` |
| terminal `IfExp` (specified, not shipped) | a verdict rebound into a summary local | every load must be a print payload | `correct-terminal-verdict-rebound-into-name` |
| terminal `IfExp` (specified, not shipped) | a verdict produced by a helper `return` | the production requires one in-scope Store | `correct-terminal-verdict-returned-from-helper` |
| enumerate | the counter selects which outcomes get corrected | opaque counter binding; `_static_bool` returns `None` | `correct-ap-counter-used-in-decision` |
| enumerate | the counter supplies the correction factor | opaque counter binding; factor resolution refuses | `correct-ap-counter-used-as-factor` |
| enumerate | a complete correction misread as a strict subset | positions from sequence order; covered/`complete` | `correct-ap-enumerate-complete-correction-min` |
| enumerate | enumerating a screening subset | contract-order sequence equality | `correct-ap-enumerate-over-non-contract-sequence` |
| enumerate | `enumerate(zip(...))` hiding a second sequence | bare-Name argument only | `correct-ap-enumerate-over-zip` |
| cap | a cap that is really a second fold | adjacency, same-Name guard, literal-one, sole-statement body | `correct-ap-cap-non-adjacent`, `correct-ap-cap-guard-on-different-name` |
| cap | a cap-shaped branch that writes a different value | numeric-one reassignment only | `correct-ap-cap-assigns-other-value` |
| cap | a cap-shaped branch that writes a different name | reassignment target must be the folded Name | `correct-ap-cap-reassigns-other-name` |
| cap | a complete correction misread as a strict subset | the if-cap and `min` produce identical coverage | `correct-ap-cap-complete-correction` |

These blockers do not depend on an analysis being malicious. They are the conservative treatment of
a correct analysis whose correction, staged testing, or screening would otherwise be crossed
silently.

## 11. Executable fixture matrix

### 11.1 Positive controls

| Fixture | Expected |
|---|---|
| `positive-comprehension-dict-helper-record` | candidate/`none`, `N=6` (the exact E17 P3 source) |
| `positive-ap-enumerate-start-one` | candidate/`strict_subset` `{0,1,2}` of 7 (the exact E17 P6 source) |
| `positive-ap-enumerate-no-start` | candidate/`strict_subset` `{0,1,2}` of 7 |
| `positive-ap-enumerate-start-zero` | candidate/`strict_subset` `{0,1,2}` of 7 |
| `positive-ap-cap-min-form-unchanged` | candidate/`strict_subset` `{0,1,2}` of 7, cap admission not fired |
| `positive-comprehension-inline-flat-record` | comprehension admission fires; census residual stands |
| `positive-comprehension-list-form` | comprehension admission fires; record-model residual stands |

### 11.2 Forty-two new rows, three orthogonal gates

Every new fixture carries three independent labels, because conflating them is how a fixture set
stops proving anything:

- `correct_analysis`: the source is a scientifically correct analysis. **Eleven** rows carry it.
  These may never reach `candidate`. Reaching `covered` is allowed and is the desired answer.
- `refused_admission`: the named extension must not fire at all, asserted against the executed
  admission census rather than against a downstream classification.
- `admitted`: the named extension must fire.

An adversary is proved by its admission census being empty for its extension. That cannot be
satisfied by an unrelated abstention, which is exactly the failure mode a
"must not become a candidate" assertion has when the base source is itself a misstep.

The census gate is also checked for non-vacuity. A disqualifier fixture whose shipped 3.3 baseline
is already a classification would have an empty census for free, because section 3.3 attempts no
admission on a classified row. The sweep fails on any such fixture, so every disqualifier assertion
in this design is exercised.

The three section-5 fixtures are the one exception, and they carry no census label at all: extension
B is not installed, so a census assertion on them would be vacuous by construction. Their refusal is
proved directly against the specified grammar by `terminal_ifexp_refusal_probe`.

### 11.3 Cumulative populations

The final implementation executes all **245** rows, not fixture-shaped assertions:

| Population | Rows |
|---|---:|
| frozen 3.0 original | 48 |
| audit fix R1 | 14 |
| audit fix R2 | 4 |
| audit fix R3 | 5 |
| B5 field/expression grid | 63 |
| 3.1 laundering-adjacent | 16 |
| AP 3.2 | 20 |
| reproduced hierarchy (B1–B5, gatekeeping set) | 12 |
| 3.3 terminal positives/adversaries | 13 |
| 3.3 helper positive/adversaries | 8 |
| new 3.4 comprehension | 16 |
| new 3.4 terminal `IfExp` (specified, not shipped) | 3 |
| new 3.4 iterator | 11 |
| new 3.4 cap | 10 |
| new 3.4 reason routing | 2 |
| **total** | **245** |

The 203 frozen 3.2/3.3 rows are additionally asserted **unchanged**: the sweep fails if any of them
moves. That is the cumulative probe matrix requirement. It covers the twelve reproduced gatekeeping
fixtures (`assert`, `match`, short-circuit, early return/break/continue/raise/`sys.exit`, and the
`pvalue-control-dependence-unresolved` execution-prevention residual), the B5 expression grid, the
3.1 laundering-adjacent set, the AP consumption set, and the nine 3.3 bypass probes. All of them
keep refusing.

## 12. Adapter oracle for all opened cases

### 12.1 E17 fifteen-row oracle

The real 3.4 adapter must produce:

| Role/case | 3.3 outcome | 3.4 pinned outcome |
|---|---|---|
| P1 `1532d863877a21f078d4` | candidate/`none`, `N=5` | byte-identical |
| P2 `265b4a50ff46707c3a26` | candidate/`none`, `N=3` | byte-identical |
| P3 `a2e031f79e31c80fd900` | `hierarchical-gatekeeping-present` | candidate/`none`, positions `{}`, `N=6` |
| P4 `d82542509694adf4716c` | candidate/`none`, `N=4` | byte-identical |
| P5 `f3217e701e0f2452afab` | candidate/`strict_subset` `{2,3}`, `N=8` | byte-identical |
| P6 `b4e507c4b55954752f14` | `unresolved-manual-correction-present` | candidate/`strict_subset`, positions `{0,1,2}`, `N=7` |
| N1 `e2d8b1bdf4baa671a1b4` | `test-operand-lineage-unresolved` | byte-identical |
| N2 `97d10fe68508b65dbbbe` | `unresolved-decision-threshold` | byte-identical |
| N3 `7f7aeea0409c82c71533` | `unresolved-manual-correction-present` | byte-identical |
| N4 `72a0a2e4cec8a7fc6450` | `extra-registered-test-outside-authorized-family` | byte-identical |
| N5 `5926525400e0ed097c31` | `test-battery-cardinality-unresolved` | byte-identical |
| N6 `de2f4a189ac35b4e8bb1` | `authorized-family-test-census-incomplete` | byte-identical |
| N7 `7129cd5a8d682a4c7340` | `authorized-family-test-census-incomplete` | byte-identical |
| N8 `bb51d22437d7c3562b62` | `test-battery-cardinality-unresolved` | byte-identical |
| N9 `63ea01a01e2f5c56509b` | `unresolved-decision-threshold` | byte-identical |

The movement set must equal `{E17:P3, E17:P6}` exactly. All nine E17 negatives remain
noncandidates and, under section 8 option 2, byte-identical; under option 1 the executed relabel
set in 0.2 is the complete list of reason changes.

### 12.2 E10–E16 historical oracles

All 105 adapter rows are byte-identical to their frozen 3.3 results. The gate compares canonical
rows, not only state and reason. It retains the known adapter/source distinction for E10 N7
(`statistics-api-imported-outside-analysis-py` at adapter level) and refuses any 3.4 admission that
crosses it. No analyzer-only replay may replace the adapter oracle.

Retro candidate recall after applying 3.4 to opened bytes is:

```text
E10 5/6
E11 6/6
E12 6/6
E13 4/6
E14 4/6
E15 3/6
E16 4/6
E17 6/6
```

These are development projections and never rescore sealed first-contact envelopes. Sealed E17
remains `4/6`.

## 13. Open-corpus oracle for all 50 cases

Every adapter row is byte-identical to the 3.3 comparison row. The frozen
`adapter_replay_records_v2_1.json` bytes remain untouched. Version 3.4 adds a comparison row set
equal to 3.3:

```text
labeled correct: 25, candidates 0
labeled misstep: 25, candidates 19
movements: 0
```

The adapter-level exception remains corpus spec-30: `api-resolution-ambiguous` at adapter level,
even though the source analyzer exposes a later manual-correction reason. The corpus gate is
adapter-level, and the sweep refuses any 3.4 admission that crosses it.

## 14. Interaction with 3.1 questions and attestations

### 14.1 The census delta is real and must be pinned

The no-attestation correction-scope question census through E17 is **28**:

```text
opened 19
corpus  9
total  28
```

The 3.3 population through E16/corpus had 25. E17 adds scope questions on P6, N2, and N3, exactly
mirroring E16's P6/N2/N3 pattern.

Applying 3.4 moves E17 P6 to a candidate. Its correction-scope MaterialQuestion is therefore
removed, because the ambiguity it asked about is resolved:

```text
before  opened 19  corpus 9  total 28
after   opened 18  corpus 9  total 27
removed E17:P6:b4e507c4b55954752f14
```

This is the intended 3.1 behavior and the first time this delta family has actually exercised it:
the 3.3 census was `25 -> 25` with an empty removed set. A reviewer comparing 3.4 to 3.3 should not
read `28 -> 27` as a regression. A question is not a catch, and resolving a question into a
demonstrated candidate is the layer working.

E17 P3 carried no correction-scope question under 3.3, because `hierarchical-gatekeeping-present`
is not a qualifying reason. Its removal set contribution is empty.

### 14.2 Attestation asymmetry is unchanged

All attestation trust asymmetry is unchanged. A B answer cannot use a 3.4 admission to do anything
the answer-removed analyzer cannot do. Existing answer-removal equivalence, false-clearance,
four-record-type, scoring-isolation, and no-carry-forward gates remain byte-identical.

## 15. Determinism, idempotence, ordering, and prose tripwire

### 15.1 Determinism and idempotence

The comprehension normalization is keyed by immutable sorted source-position identities. Applying it
twice admits nothing the second time and changes no byte; the prototype asserts this on every row
that admits at all. The lowered element is proved graph-identical to the original element.

The iterator and cap admissions are pure predicates over the AST. They hold no state between calls.
The prototype asserts that a second full analysis of the same normalized bytes produces the
identical classification **and** the identical admission census.

The section 3.3 ordering rule is itself deterministic: it branches only on whether the unchanged 3.3
pipeline returned a classification, which is a function of the original bytes alone.

Global censuses always see original bytes. Record occurrence multiplicity and the 2.3 ordinal rules
remain intact; an ordinal is bookkeeping only, never an evidence value or position substitute.

Identical project bytes, contract, registry, CSV snapshot, and attestations produce byte-identical
module rows, evidence, questions, disclosures, concerns, Findings, lock bytes, and replay records.
No timestamp enters identity or classification.

### 15.2 Prose and evidence tripwire

Every new predicate is run against paired mutations that:

- add and remove comments, docstrings, reports, and Markdown containing every fixture label and
  guard phrase;
- rename the collected name, the generator target, the counter, the folded name, and every literal
  record key to correction-like and presentation-like spellings;
- rename the element callee to a correction-like spelling while leaving it unregistered;
- replace display strings with same-byte-length arbitrary strings;
- alter format text without changing value-lineage AST; and
- rename a true callee slot as the paired positive control for the global census.

Candidate and abstention bytes must stay identical for prose, non-callee, and display mutations.
Deleting a load-bearing structural literal or changing a callee terminal must change the appropriate
proof, which is the positive control. The 256-byte string cap is measured; no string payload is
inspected for scientific words.

Extension C deserves an explicit note here. `enumerate` is matched as an unshadowed builtin callee,
`start` as a keyword argument name in the Python grammar, and the counter as a binding position in a
tuple target. None of those is a spelling judgment about the author's identifiers. The counter may
be called anything; it is inert because of what it is bound to.

## 16. Reuse map and file-by-file build plan

### 16.1 Frozen files copied, never edited

The 3.3 modules in 2.2 are byte-frozen. The build creates versioned 3.4 files following the 3.3
registry pattern. In particular `code_csv_multiple_testing_dataflow_v3.py`,
`code_csv_multiple_testing_dataflow_v3_2.py`, `code_csv_multiple_testing_correction_model_v3_2.py`,
`code_csv_multiple_testing_dataflow_v3_3.py`, and every dependence dataflow file remain untouched.

### 16.2 New versioned production files

The build adds:

- `src/sc_referee/scientific_checks/code_csv_multiple_testing_comprehension_v3_4.py`: the
  section-4 grammar proof and the normalized record-graph construction;
- `src/sc_referee/scientific_checks/code_csv_multiple_testing_correction_model_v3_4.py`: a
  versioned copy of the 3.3 correction model whose only changes are the section-6 row-table
  admission, the section-7 cap absorption in the single-reaching-fold proof and `_positions_for`,
  and the section-7 surrogate drop;
- `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_4.py`: versioned copied
  integration implementing the section 3.3 ordering rule. It runs the unchanged 3.3 pipeline first,
  returns any classification untouched, and only then re-analyzes with the comprehension
  normalization in the normalization phase, adopting that result only when it classifies. Section 8
  applies no routing;
- versioned `record_model_v3_4.py` and `helper_record_v3_4.py` wrappers as required by registry
  identity, with 3.3 behavior otherwise byte-equivalent;
- `code_csv_multiple_testing_adapter_v3_4.py` and `integration_multiple_testing_v3_4.py`;
- `src/sc_referee/detectors/bounded_code_csv_multiple_testing_conflict_v3_4.py`; and
- versioned scope-question and attestation wrappers only if registry identity requires them; their
  classification and public-record behavior remain byte-equivalent.

Production must not monkeypatch `_complete_rows`, `_fold_target_is_unique`, `_positions_for`,
`_surrogate_bytes`, or `_terminal_ifexp_positions`, and must not rewrite source text. The prototype
techniques are development evidence only, as stated in 0.3.

### 16.3 Narrow shared edits

Allowed shared edits are limited to:

- development binding and registry entries for 3.4 while retaining historical registrations;
- scientific registry and capability-ledger entries;
- package exports and import dispatch;
- the ADR-0079 amendment and generated registry/ledger/manifest bytes; and
- `docs/AGENTIC_SKILL.md` only if a version display must advance, with no attestation-flow change.

No GrantPin, qualified binding, qualified Finding path, wording template, contract profile, scoring
rule, or pseudoreplication file changes.

### 16.4 Tests and artifacts

Add versioned tests for:

- every shipped grammar production in sections 4, 6, 7, and 8, and every named disqualifier,
  asserted against the admission census and not only against a classification;
- that the section-5 production is absent from the shipped recognizer set, that E16 P4 keeps its
  pinned candidate, and that the specified section-5 grammar still refuses all three named store
  shapes when called directly;
- the ordering rule in 3.3: a row the unchanged 3.3 pipeline classifies is returned untouched, and a
  3.4 re-analysis that abstains returns the frozen reason byte-for-byte;
- the exact E17 P3 and P6 adapter movements with exact `N`, classification, positions, one
  candidate, and zero Findings;
- all 120 opened rows and 50 corpus rows;
- all 245 fixtures and closed-reason set equality;
- the graph-identity and idempotence properties in 15.1;
- the equivalence of the if-cap and `min` spellings on a complete correction;
- the counter-opacity property, asserted directly on `_static_bool` and `_positions_for`;
- the section-8 routing scope, including that short-circuit and execution-prevention returns keep
  `hierarchical-gatekeeping-present`;
- prose tripwire and output identity;
- frozen 3.1/3.2/3.3 adapter, detector, integration, and replay anchors; and
- qualified-lane differential nonderivation.

The checked-in prototype artifacts in this commission are frozen design evidence, not test
expectations derived from production code.

## 17. Validation plan and executable gates

### 17.1 Prototype evidence gate

From the repository root, the builder runs:

```bash
PYTHONPATH=src:evaluation/development/multitest-code-slice-v3_4/prototype-sweep \
  .venv/bin/python evaluation/development/multitest-code-slice-v3_4/prototype-sweep/verify.py
```

The verifier must reproduce `instrument_results.json` and `results.json` byte-for-byte and verify
every manifest digest. Required values are:

```text
cases                           170 (120 opened + 50 corpus)
frozen prior rows identical     155
movements                       exactly E17 P3 and E17 P6
fixtures                        245
correct fixtures                194
opened-negative candidates      0/72
corpus-correct candidates       0/25
all-correct-fixture candidates  0/194
question census                 28 -> 27, removed {E17:P6:b4e507c4b55954752f14}
reason-routing relabels         0 evidence cases, 10 fixtures (measured, not applied)
terminal-IfExp admissions       0 (extension B is not shipped)
admission census                comprehension 16, enumerate 16, cap 5, terminal-IfExp 0
```

### 17.2 Final implementation gates

The build must execute and pass:

1. the real-guard attribution test at the exact E17 P3 control position, asserting zero p-origins,
   no correction control, six outcome headers, and registry membership;
2. the two positive movements with exact `N`, classification, positions, one candidate, and zero
   Findings;
3. the complete E17 fifteen-row adapter oracle and exact movement-set equality;
4. byte identity for all 105 E10–E16 rows and all 50 corpus rows;
5. all 245 fixtures with their exact admission-census and classification gates, including the
   non-vacuity check that every disqualifier fixture has an abstaining 3.3 baseline;
6. every none-flip population in 0.2;
7. the question census `19 opened + 9 corpus = 28` before, the pinned removed set after, and no
   removal of any non-MT MaterialQuestion;
8. the 61-reason closed-set gate scoped only to 3.4 tests;
9. all prior E10–E17, corpus, PROBE/NEGSIM/ladder, record, AP, question, attestation, and replay
   anchors;
10. frozen 3.1/3.2/3.3 implementation and result digests from 2.2;
11. development-only binding and qualified-lane byte and non-derivation differential; and
12. deterministic replay equality, including 15/15 envelope replay and attested runs.

### 17.3 Quality and generated-file order

After the final source and test edit, regenerate registries, ledger, and manifest in that order,
then run fresh:

```bash
ruff check .
ruff format --check .
mypy src
pytest
python scripts/validate_starter.py
```

No suite-green claim may precede the final manifest-covered edit.

## 18. Residuals and honest read

### 18.1 Deliberate residuals

The following stay abstentions:

- E17 P5's library-subset cardinality question and the whole `test-battery-cardinality-unresolved`
  policy family;
- comprehensions with filters, multiple generators, reordered or non-contract sequences, conditional
  or nested elements, keyword-carrying element calls, or rebound and mutated collections;
- the list-comprehension record-model residual in 4.5: the form normalizes and then abstains at
  `test-battery-cardinality-unresolved`;
- an element that itself contains a registered test resolves through the global census, not through
  the record model: `positive-comprehension-inline-flat-record` executes to
  `extra-registered-test-outside-authorized-family`, which is a census fact and not a 3.4 gap;
- iterators other than a bare contract-sequence Name or the two admitted `enumerate` forms;
- any use of the enumerate counter in a correction or decision path;
- caps that are non-adjacent, differently guarded, differently valued, or accompanied by other
  statements;
- every 3.2 and 3.3 residual: name-set-selected partial folds outside the admitted grammar,
  unregistered correction paths, general helper-return records, multi-call helpers, nested records,
  and conclusions recomputed outside the helper; and
- every staged or gated analysis covered by the reproduced hierarchy population.

### 18.2 What 3.4 buys

On opened E17 bytes the delta moves both remaining misses. E17 retro recall is therefore `6/6`, up
from the sealed first contact `4/6`. E11 and E12 already stand at `6/6` retro, so this is the third
retro-complete envelope, not a first.

It should be read narrowly. Both movements are spelling walls. E17 P3 used a dict comprehension
where a three-line loop was already caught. E17 P6 used an `enumerate` where a bare iterator was
already read, and an `if`-cap where `min` was already folded. The science in both cases was already
within the frozen recognizers' reach. Version 3.4 does not extend what the detector understands
about multiple testing. It extends which spellings of the same program the detector can read.

Corpus recall remains `19/25`; the hard correct-case gate remains `0/25`. The delta does not spend
false-accusation budget to reopen the six corpus residuals.

The admission census in 0.2 shows how narrow the shipped reach is. Across 170 evidence cases, the
comprehension normalization fires on exactly two rows, one of them the pinned E17 P3 and the other a
corpus row that does not move; the `enumerate` and cap admissions fire on exactly one evidence row
each, the pinned E17 P6. Every other admission in the census is a fixture the design authored to
test itself.

### 18.3 E18 arrival and promotion arithmetic

The live promotion window is E17+E18 and requires at least **7 catches out of 12**. Sealed E17
scored `4/6`, so **E18 needs at least 3/6**. That is the arithmetic; retro-applying 3.4 to E17 gives
`6/6`, but sealed E17 remains `4/6` and cannot be rescored.

The prospective read is genuinely uncertain. Across E16 and E17 the misses concentrate in
collection and iteration spelling rather than in scientific content, and each delta that closes a
spelling family has moved the retro number without predicting the next envelope. E16 retro reached
`4/6` and sealed E17 then arrived at `4/6`. That is one matching pair, which is weak evidence for a
prospective claim about E18.

What stays uncatchable, in rough order of how likely it is to arrive:

- the library-subset cardinality policy (E16 P5, E17 P5 shape), which is blocked on an ADR, not on a
  recognizer;
- unregistered correction libraries and hand folds outside the admitted product and cap forms;
- helper-returned record graphs beyond the exact 3.3 closure;
- DataFrame-resident p tables and `zip` write-back routes outside the frozen grammar; and
- any genuinely gated design, which the detector will keep abstaining on by construction.

E18 measures first contact without a per-envelope recall gate. The cumulative promotion arithmetic
is reported honestly after it lands.

## 19. Scoring and public-record isolation

Questions are not catches; disclosures, concerns, covered outcomes, and Findings remain distinct
record types. Blind envelopes provide no attestations. Version 3.4 does not alter envelope scoring,
promotion arithmetic, role maps, or sealed audit bytes. The two retro candidates are development
evidence only. No new route can create a Finding without the unchanged candidate adapter and wording
requirements.

Section 14 is the only place where a public record changes: one correction-scope MaterialQuestion
is removed because the ambiguity it asked about resolved into a demonstrated candidate. Section 8
records an observed mislabel and recommends against changing any reason string in 3.4, so it
changes no public record. Both must appear in the ADR-0079 amendment.

## 20. Stop-and-report rule

Stop and report a design regression rather than changing a grammar, reason, or oracle if any of the
following occurs:

1. E17 P3 or E17 P6 does not reach its exact pinned candidate under the final strict implementation;
2. any other evidence row moves, or any E16 or E17 negative becomes a candidate;
2a. any row the unchanged 3.3 pipeline classifies changes at all, or a 3.4 re-analysis that abstains
    returns a reason other than the frozen 3.3 reason. E16 P3 and E16 P4 are the named regressions
    this rule exists to catch;
3. corpus correct candidates exceed `0/25`, opened-negative candidates exceed `0/72`, or any correct
   fixture becomes a candidate;
4. a comprehension with a filter, a non-contract or reordered sequence, a conditional or nested
   element, a keyword-carrying element call, or a rebound or mutated collection is admitted;
5. a normalized comprehension family hides a later gated test from the whole-module census;
6. the section-5 production is installed in the shipped recognizer set, or a verdict value reaches
   a store, a return, a second binding, or an unresolved call while it admits that control in any
   later delta;
7. the enumerate counter reaches a correction factor, a family-position selector, a threshold, or a
   fold guard;
8. an `enumerate` over anything other than the bare contract-order sequence Name is admitted, or a
   non-literal `start` is admitted;
9. a non-adjacent cap, a cap guarded on another Name, a cap guarded against a value other than the
   literal one, a cap with an `else`, or a cap whose body holds another statement is absorbed;
10. the if-cap spelling and the `min` spelling of the same complete correction produce different
    corrected positions or different classifications;
11. global censuses observe normalized rather than original bytes;
12. the versioned hierarchy copy drops `assert`, `match`, short-circuit, early-exit, or unresolved
    prevention behavior, or any section-8 routing is applied to a source whose control can prevent a
    slice node or whose owner subtree contains a registered test;
13. the unchanged 3.3/3.2 classifier is bypassed, or a 3.4 proof assigns a classification or a
    corrected position;
14. the question census differs from `28` before or `27` after, its removed set differs from
    `{E17:P6}`, or a non-MT MaterialQuestion is removed;
15. closed reasons differ from 61, or a surviving reason is relabeled;
16. display text, identifier spelling, comments, reports, or Markdown change a predicate;
17. any frozen 3.1/3.2/3.3 file or result, corpus replay record, prior comparison row, qualified
    lane, GrantPin, wording object, or scoring byte changes outside enumerated registry noise;
18. applying any admission twice changes graph, exclusion, or census bytes;
19. prototype replay, adapter replay, answer-removal equivalence, or deterministic output differs;
    or
20. a required quality gate cannot pass after generated files are finalized.

Conservative abstention on an unpinned shape is acceptable. Conservative abstention on pinned E17 P3
or E17 P6 is a stop in the other direction, not permission to loosen the design.

One open reviewer decision is recorded rather than resolved here, and the builder may not close it:
the section-8 reason-routing option in 8.2. If the reviewer does not decide, the builder ships
option 2, which is the byte-identical choice, and reports the residual. The section-5 disposition is
settled by executed evidence, not left open: it is not shipped.

## 21. Revision log

### Revision 0, 2026-08-31

- instrumented the shipped 3.3 hierarchy guard, terminal-presentation proof, and AP recognizer, and
  recorded the E17 P3 outcome-headers-only trigger (zero p-origins, six outcome headers) and the
  E17 P6 double blocker as observations;
- executed both mutation ladders, showing that the P3 wall is comprehension spelling and that the P6
  wall requires both the iterator and the cap rewrite;
- designed the closed contract-order comprehension grammar and its graph-preserving lowering;
- specified the print-only terminal `IfExp` production, executed it, measured that it admits zero
  positions and that its one E16 P4 admission destroys a pinned 3.3 candidate, and did not ship it;
- replaced an unconditional normalization order with a frozen-result-first order after the sweep
  showed the unconditional order losing the E16 P3 and E16 P4 pinned candidates;
- designed the `enumerate` row-table admission with an opaque counter binding, and the adjacent
  if-cap absorption with its three exact consequences including the surrogate drop;
- enumerated the outcome-headers reason-routing options, executed two of them, measured that the
  specified routing relabels eight frozen gatekeeping controls and zero evidence rows, and
  recommended keeping the current reason without inventing a new one;
- executed 170 evidence cases and 245 fixtures, pinning exactly two movements, every none-flip
  count, and the admission census; and
- pinned the `28 -> 27` question-census delta, retained frozen classification, global censuses, 61
  reasons, wording, contract, qualified lane, and scoring.
