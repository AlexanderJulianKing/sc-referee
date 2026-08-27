# Multiple-testing E14 recall recon — executed ladders

Status: recon complete; no production change authorized  
Date: 2026-08-27  
Detector under study: `code_csv_multiple_testing` `2.3.0`, development lane  
Repository evidence commit: `073b0ba8b17f9417910f58869247620a2c71e019`  
Scope: sealed Envelope 14 plus frozen opened/corpus/FA evidence; analysis only

## 0. Provenance and result reproduced

This recon follows `docs/implementation/FINDINGS-PLAYBOOK.md` and the executed-ladder form of
`MULTITEST-RECALL-RECON-E13-2026-08-26.md`. The detector, adapter, tests, contracts, registries,
frozen envelopes, and prior replay records were read-only. All new executable material is under
`evaluation/development/multitest-recall-recon-e14/`.

Frozen inputs:

| Evidence | SHA-256 |
|---|---|
| `FINDINGS-PLAYBOOK.md` | `9bcb66dff193956d63b37ff6dad289e6a459dc6adc16208102483939ce0f520a` |
| E13 recon | `d99c63caf70e2d1b1ff209c1d6ac747c17c73b911fe7616aaf1e8a3bdc34d6db` |
| 2.3 dataflow | `70d8fd3c8f61e8726379c582e420700ea3babd0c45468e22b6f5b6f3b05dff28` |
| 2.3 adapter | `e5c2a05e87fdec206460ccf73343e4dd158a7c311979208939f217a97f603023` |
| E14 `AUDIT_RESULTS.json` | `921804b0c8407f9460e1a8b898b527a13ef16b9ca703a04d09c757950ef7b045` |
| E14 `ROLE_MAP.json` | `b9f56f863be69882b07d98423d55691bd4f1bafec1bfa41a83edd080a951e69e` |

The sealed result was reproduced: first-contact recall `1/6` (P1 only), negative candidates `0/9`,
Findings `0`, and replay equality `15/15`. The first validation fact for 2.3 is also reproduced:
**zero of the fifteen E14 rows abstained `authorized-reader-lineage-unavailable`**. The local-reader
path admission mined from E13 did not recur as a wall. The arrival moved earlier to census and
collection structure.

Observed and inferred claims are separated below. “Observed” means a sealed audit row, real 2.3
adapter rung, or executed frozen-analyzer sweep. A proposed grammar remains a recon proposal until
an adversarial design review accepts it.

## 1. Headline and untouched-tree census diagnosis

The five positive misses are:

| Role | Case | Sealed 2.3 outcome |
|---|---|---|
| P2 | `4fc0f5c1ef2d0e2cd5b6` turkey bedding | abstain `pvalue-family-collection-unresolved` |
| P3 | `502687d9137dab93ff99` biofilm coupons | abstain `test-battery-cardinality-unresolved` |
| P4 | `cccde3c60f936e077f80` deer condition | abstain `authorized-family-test-census-incomplete` |
| P5 | `5e33841b96d85ffe67be` ORS trial | abstain `authorized-family-test-census-incomplete` |
| P6 | `94786af7eca95fff6d78` room attendants | abstain `unresolved-manual-correction-present` |

The untouched-tree census was executed directly in `census.py`; `census_results.json` records all
fifteen rows. The eight `authorized-family-test-census-incomplete` outcomes are not one idiom:

1. **P4 and P5 — table-selected API dispatch.** Each closed outcome-table row contains a test
   selector. One helper loop branches between `scipy.stats.ttest_ind` and
   `scipy.stats.mannwhitneyu`. The global census refuses a registered call beneath that live
   conditional. Both actual families are non-uniform: P4 is six Welch plus one Mann–Whitney; P5 is
   five Welch plus one Mann–Whitney. Even exact dispatch resolution would reach the unchanged
   `mixed-test-api-family` guard before candidate classification.
2. **N1, N2, and N3 — repeated throwaway target in a table comprehension.** Their correct analyses
   use `[helper(... ) for column, _, _ in OUTCOMES]`. The installed exact table-binding grammar
   requires distinct target names, so the repeated `_` prevents the comprehension factor from
   resolving. The untouched census records one helper-body test instance rather than authorized
   counts four, five, and six. This is a separate correct-analysis recognizer limitation, not the
   positive P4/P5 idiom.
3. **N6 — real stage gate.** The family helper is called only after an overall screen and an early
   return. The untouched census refuses the live conditional with
   `authorized-family-test-census-incomplete`. This is the intended scientific-gate protection,
   not a cardinality syntax omission.
4. **N7 and N8 — no registered family.** The untouched census resolves zero registered calls. N7
   imports upstream values; N8 uses an unregistered custom permutation procedure. Their `0 < N`
   result is exact and must remain an abstention.

Thus “census incomplete in 8/15” does not justify one broad census relaxation. Six of those eight
rows are correct negatives, and two positives are protected by the separate uniform-API rule.

## 2. Executed mutation ladders

`ladders.py` starts with each sealed `analysis.py` and changes one named construct per rung.
Every row below ran through the real development-lane 2.3 adapter, including contract construction
and audit. `ladder_results.json` is the compact pin; the script also emits source hashes,
authorized counts, corrected positions, candidate-record counts, and Finding counts.

### 2.1 P2 — turkey bedding, `4fc0f5c1ef2d0e2cd5b6`

| Rung | Only mutation | Observed adapter outcome |
|---|---|---|
| P2-r0 | sealed source | abstain `pvalue-family-collection-unresolved` |
| P2-r1 | delete the second pass over the stored results | candidate `none` |
| P2-r2 | delete the now-unused `results.append(...)` | candidate `none` |

The first loop already emits one raw decision for every member. The second loop reads a boolean
verdict folded into the record and emits every conclusion again. Removing only that second pass
is sufficient; the collection insertion itself is accepted when it has no second consumer.

Decision: **bin C**. This is the deferred record-flag/duplicate-emission surface. A general fold
would need to prove record identity, exact member ownership, same decision polarity, and total
consumer equivalence across both emissions. That is within the standing deferred record-flag
family in the 2.3 design section 12.4, not a local collection tweak.

### 2.2 P3 — biofilm coupons, `502687d9137dab93ff99`

| Rung | Only mutation | Observed adapter outcome |
|---|---|---|
| P3-r0 | sealed source | abstain `test-battery-cardinality-unresolved` |
| P3-r1 | inline the singleton `for u, h in [(uncoated[outcome], hydrophilic[outcome])]` binding | abstain `unresolved-decision-threshold` |
| P3-r2 | delete the non-p direction ternary conservatively joined through the record | abstain `hierarchical-gatekeeping-present` |
| P3-r3 | refactor the two print branches to the already-admitted assigned-verdict/single-emission form | candidate `none` |

The first wall is narrow: the second generator is a one-row binding device, not an additional
scientific iteration. However, clearing it alone does not catch the case. The installed record
origin proof conservatively joins the `difference` field with p provenance, exposing its numeric
direction comparison as `unresolved-decision-threshold`. After that non-p control is removed, the
multi-statement/dynamic-p print branch remains a real hierarchy wall. Only an existing admitted
single-emission form reaches a candidate.

Decision: **bin A for the first wall only**, D14-A below. The proposed delta deliberately pins P3
one wall deeper as an abstention. The record-field and compound second-emission refinements are not
smuggled into it; they require their own guard review and polarity fixtures.

### 2.3 P4 — deer condition, `cccde3c60f936e077f80`

| Rung | Only mutation | Observed adapter outcome |
|---|---|---|
| P4-r0 | sealed source | abstain `authorized-family-test-census-incomplete` |
| P4-r1 | change the one Mann–Whitney table selector to Welch | abstain `authorized-family-test-census-incomplete` |
| P4-r2 | replace the now-dead selector branch by the direct Welch call | abstain `unresolved-pvalue-consumer` |

Changing data values does not alter the syntactic conditional census. Removing the dispatch makes
the API uniform and reveals the later record-carried significance flag/consumer wall. The sealed
source itself is non-uniform and the 2.0 ordered predicate requires a uniform registered API.

Decision: **bin C**. A selector-aware census would still abstain `mixed-test-api-family`; removing
that guard would be an accusation-policy change. The deeper record flag is also a deferred family.

### 2.4 P5 — ORS trial, `5e33841b96d85ffe67be`

| Rung | Only mutation | Observed adapter outcome |
|---|---|---|
| P5-r0 | sealed source | abstain `authorized-family-test-census-incomplete` |
| P5-r1 | change the one Mann–Whitney table selector to Welch | abstain `authorized-family-test-census-incomplete` |
| P5-r2 | replace the now-dead selector branch by the direct Welch call | abstain `correction-family-lineage-unresolved` |

The actual script both mixes APIs and slices `results[:2]` before Holm correction. The first is the
unchanged API-uniformity guard; the second is exactly the 2.3 section 12.4 positional-record subset
residual. Resolving the dispatch without a position model cannot prove which authorized members
enter correction and therefore cannot support a safe `strict_subset` accusation.

Decision: **bin C**. No selector, API-uniformity, or positional-record policy changes are proposed.

### 2.5 P6 — room attendants, `94786af7eca95fff6d78`

| Rung | Only mutation | Observed adapter outcome |
|---|---|---|
| P6-r0 | sealed source | abstain `unresolved-manual-correction-present` |
| P6-r1 | change the manual multiplier from subset size four to family size eight | abstain `hierarchical-gatekeeping-present` |
| P6-r2 | remove presentation iteration of the membership container | abstain `hierarchical-gatekeeping-present` |
| P6-r3 | change the membership List to the admitted Set oracle | abstain `hierarchical-gatekeeping-present` |
| P6-r4 | add the four remaining outcomes to that correction set | abstain `hierarchical-gatekeeping-present` |

The sealed arithmetic is `min(P * 4, 1)` for four of eight authorized outcomes. The installed
manual grammar admits only the exact authorized family factor `N`. Even after changing that
scientific factor, the script retains a mixed-polarity membership control that the hierarchy guard
does not discard.

Decision: **bin C**, the standing proper-subset manual-factor residual in the 2.3 design section
12.2. Recognizing it changes correction coverage and can manufacture a `strict_subset` candidate;
it requires its own policy ADR. The further hierarchy controls are not evidence for weakening that
guard.

## 3. Proposed narrow delta

### 3.1 D14-A — exact singleton projection-binding generator

D14-A is the sole candidate delta. It changes the factor and symbolic binding proofs for one exact
two-generator comprehension; it does not delete a consumer or hierarchy guard.

An occurrence qualifies only when all conditions hold:

1. The owner is one `DictComp` with exactly two generators. No List/Set comprehension or generator
   expression is admitted. The first generator already satisfies the unchanged exact complete outcome
   iteration grammar, has no `if`, and is not async.
2. The second generator is not async, has no `if`, and iterates one literal `ast.List` or
   `ast.Tuple` display containing exactly one flat row. No Name, call, arithmetic, starred value,
   comprehension, generator, or runtime container can supply that singleton.
3. The second target and the one row are both `ast.Tuple` or both `ast.List`; they have the same
   length, exactly two elements, and both target elements are distinct simple Names. A
   list/tuple-kind mismatch is refused.
4. Each row element is exactly `FRAME[OUTCOME_NAME]`: `FRAME` is a simple Name and the slice is the
   exact first-generator Name proved to range over the contract outcomes. The two FRAME values
   must independently reach the unchanged complete authorized reader/group-split/row-completeness
   proof as the two registered-test operands. No `.loc`, call, attribute computation, arithmetic,
   alias expression, or non-outcome slice is admitted by D14-A itself.
5. Loads of the two second-target Names occur only in the comprehension payload. They never occur
   in either generator, a filter, nested lazy owner, assignment target, call other than the already
   sliced registered test/recognized numeric presentation consumers, correction selector, store,
   container escape, or hierarchy control. Any unresolved use takes its ordinary existing reason.
6. The singleton generator contributes factor one. The first generator contributes exactly `N`,
   so the untouched global registered-call census records exactly `N` occurrences. The census
   still runs on the original AST and sees the registered call; it does not run on prototype-
   rewritten bytes.
7. Value normalization creates two symbolic per-occurrence bindings evaluated exactly once, in
   source order, before the comprehension payload. It must not textually substitute and duplicate
   `FRAME[OUTCOME_NAME]` evaluation. The registered call, p origin, family position, operand row
   sets, every forward consumer, correction census, threshold grammar, and hierarchy guard remain
   unchanged.

Every condition is conjunctive. Any second row, third generator, filter, async form, container-kind
mismatch, non-projection component, unknown frame, use outside the payload, or failed row proof
retains `test-battery-cardinality-unresolved`, `authorized-family-test-census-incomplete`, or the
ordinary later first reason. D14-A never treats a general singleton iterable as evidence.

The prototype in `prototypes.py` rewrites only this exact pure-projection surface so the frozen
analyzer can execute the downstream path. It is evidence for classification, not the prescribed
builder architecture: a reviewed build must implement the untouched-census and single-evaluation
obligations above.

### 3.2 False-accusation analysis

The strongest correct neighbor is a complete-family hand-Bonferroni analysis whose result mapping
uses the exact two-generator form and whose conclusions use the already-admitted single-emission
shape. The D14 prototype returns **covered/complete**, never a candidate. Five adjacent fixtures
execute as follows:

| Fixture | Adversarial difference | Observed D14-A outcome |
|---|---|---|
| `D14-A-call-component-refused` | one singleton element is `identity(FRAME[outcome])` | abstain `test-battery-cardinality-unresolved` |
| `D14-A-two-row-generator-refused` | singleton display contains two rows | abstain `test-battery-cardinality-unresolved` |
| `D14-A-filtered-generator-refused` | second generator has an `if` | abstain `test-battery-cardinality-unresolved` |
| `D14-A-container-kind-mismatch-refused` | tuple row destructures into a List target | abstain `test-battery-cardinality-unresolved` |
| `D14-A-arithmetic-component-refused` | one element is `FRAME[outcome] + 0` | abstain `test-battery-cardinality-unresolved` |

The unchanged protections against stronger correct-analysis attacks are:

- a hidden correction in a component is a call and therefore cannot enter D14-A; the global
  correction-name census and unresolved-p consumer rule remain whole-module;
- a selected-row or masked projection must still prove exact authorized group rows, so discovery/
  validation and QC subsets remain `selected-group-row-completeness-unproven`;
- two singleton rows or a dynamic iterable cannot be collapsed to one and therefore cannot hide a
  duplicate/sensitivity family;
- a p stored or passed outside recognized transports still abstains `unresolved-pvalue-consumer`;
  and
- hand arithmetic and decisions still pass through the unchanged order-12/order-13 partition,
  source-text Decimal product rule, single-binding-anywhere rule, and hierarchy registry.

The admission is therefore a value/cardinality proof only. It does not itself make P3 a candidate.

## 4. Executed none-flip checks

`sweep.py` executed baseline 2.3 and D14-A through the real frozen 2.3 analyzer with the same
authority and CSV bytes supplied by the adapter harness. The sealed and mutation ladders ran
separately through the real adapter. The adapter may add an earlier source-envelope abstention; it
cannot convert these analyzer noncandidates to candidates.

| Proposal | Corpus correct | Opened negatives E10–E14 | Historical FA | New D14-A FA |
|---|---:|---:|---:|---:|
| baseline 2.3 | `0/25` candidates | `0/45` candidates | `0/22` candidates | `0/6` candidates |
| D14-A | `0/25` candidates | `0/45` candidates | `0/22` candidates | `0/6` candidates |

The historical FA census is deliberately overinclusive: six normative 2.2 fixtures, fifteen
noncandidate fixtures from the 2.3 design tables, and the implementation's additional unresolved-
escape sibling, for 22 total. D14-A and the baseline each passed all 98 noncandidate executions
(`25 + 45 + 22 + 6`). D14-A alone created exactly one opened movement and zero corpus movements:

```text
E14:P3:502687d9137dab93ff99
  abstain test-battery-cardinality-unresolved
  -> abstain unresolved-decision-threshold
```

This is a safe reason-exposure movement, not a recall catch.

## 5. Next-delta pinned expectations

If D14-A is the entire next delta, the adapter-level red/green oracle is:

| Role | Case | Pinned next-delta outcome | Status and basis |
|---|---|---|---|
| P2 | `4fc0f5c1ef2d0e2cd5b6` | abstain `pvalue-family-collection-unresolved` | red; deferred record-flag/second-emission model |
| P3 | `502687d9137dab93ff99` | abstain `unresolved-decision-threshold` | red; D14-A clears cardinality, then exposes conservative record-field threshold provenance |
| P4 | `cccde3c60f936e077f80` | abstain `authorized-family-test-census-incomplete` | red; mixed table-selected API plus deferred record flow |
| P5 | `5e33841b96d85ffe67be` | abstain `authorized-family-test-census-incomplete` | red; mixed API plus positional-record subset before Holm |
| P6 | `94786af7eca95fff6d78` | abstain `unresolved-manual-correction-present` | red; proper-subset manual factor |

No other opened row moves in the executed prototype. P1 remains candidate `none`; all nine E14
negatives and all E10–E13 rows remain byte-classification-identical. The exact movement set is
therefore `{E14:P3:502687d9137dab93ff99}`. Any future implementation of D14-A that produces a
candidate for P3, moves another opened row, or changes a corpus row is not equivalent to this
recon and must stop for review.

## 6. Bin table and considered-but-not-proposed changes

| Miss | Bin | Proposed delta or residual pointer |
|---|---|---|
| P2 turkey bedding | C | no delta; record-flag/duplicate-emission residual, 2.3 design §12.4 |
| P3 biofilm coupons | A | D14-A exact singleton projection-binding generator; post-delta still abstains at the deeper threshold wall |
| P4 deer condition | C | no delta; non-uniform registered API is protected by 2.0 order 8, with record-flag flow behind it |
| P5 ORS trial | C | no delta; non-uniform API plus positional-record subset, 2.3 design §12.4 |
| P6 room attendants | C | no delta; proper-subset manual factor, 2.3 design §12.2 |

The following ideas were considered and are not proposed:

- **General two-generator comprehension evaluation:** rejected. Calls, multiple rows, filters,
  lazy evaluation, and arbitrary binding expressions can change both call count and operand rows.
- **Table-selector API dispatch:** not proposed. It would at most expose
  `mixed-test-api-family` for P4/P5 unless the uniform-API policy were also weakened. That is not a
  recall-neutral grammar patch.
- **Repeated `_` throwaway binding:** observed in correct N1/N2/N3, but not proposed from this
  positive-miss recon. Target aliasing and placeholder semantics need a separate exact grammar;
  no positive arrival depends on it here.
- **P3 record-key origin refinement or compound terminal branch:** not proposed. The executed
  ladder shows both are independently required after D14-A. Treating dynamic p payloads or a
  branch-local direction assignment as presentation would subtract hierarchy protection.
- **P2 record flag, P5 positional subset, P6 proper-subset factor:** explicitly deferred by the
  standing residual list. DataFrame p tables and zip write-back are likewise untouched.

## 7. Honest read and arrival economics

### 7.1 Corpus and retro projection

The open 50-case corpus has **zero classification movements** under D14-A. Its frozen 2.3 result
therefore remains 0 candidates on 25 correct cases and 19 catches on 25 missteps. Byte identity of
the prior adapter record remains the appropriate future build gate.

E14 retro recall also remains **1/6**, not 2/6. D14-A removes one real cardinality wall, but P3
stops at the next conservative threshold proof. Reporting P3 as “unlocked” would confuse a wall
movement with a candidate.

### 7.2 E15 arrival expectation

The arrival curve does not support an optimistic E15 forecast. E12/E13/E14 first contact was
`2/6`, `3/6`, `1/6`; the dominant wall changed from value/reader idioms to heterogeneous census,
record, policy, and hierarchy surfaces. D14-A is intentionally narrow and does not retro-catch any
E14 miss. A fresh E15 could contain its exact singleton-binding idiom, but the P3 ladder shows that
real authors can carry multiple independent walls behind it. The evidence supports expecting
continued wall diversity and roughly floor-to-mid recall, not a step to `5/6`.

### 7.3 Promotion arithmetic

The trailing window is now exactly **6/18**: E12 `2`, E13 `3`, E14 `1`. When E15 arrives, E12 drops
out, leaving four retained catches. Reaching the `9/18` bar immediately therefore requires E15 to
score **5/6**. The recent `1/6–3/6` funnel and the zero retro catch from D14-A do not support that
as a planning assumption.

Across the next two envelopes, E14 remains in the window, so E15 plus E16 must contribute at least
**8 of 12** catches. Examples are `4/6 + 4/6`, `5/6 + 3/6`, or `3/6 + 5/6`; if E15 is `2/6`, E16
must be `6/6`; if E15 is `1/6` or lower, promotion by E16 is arithmetically impossible. The recent
mean is `2/6`, so a sustained `4/6` average over the next two would be a material, presently
unverified change in the arrival distribution. The hard false-accusation stops remain satisfied,
but they do not substitute for recall.

## 8. Observed, inferred, and requiring review

Observed:

- the sealed E14 adapter table and hard-stop results;
- zero E14 authorized-reader-lineage abstentions;
- the untouched census counts/reasons for all fifteen cases;
- all eighteen real-adapter ladder rungs;
- D14-A's one opened reason movement, zero corpus movements, and `0/25`, `0/45`, `0/22`, `0/6`
  none-flip counts; and
- the promotion arithmetic from the sealed E12–E14 scores.

Inferred from those executions:

- P2 is an instance of the deferred record-flag/duplicate-emission surface;
- P4/P5 cannot become candidates under the current uniform-API contract merely by resolving their
  selector dispatch; and
- D14-A can be specified as a narrow factor/value admission, but it is not an end-to-end recall
  gain on the opened case.

Still requiring adversarial design review before code:

- whether D14-A's symbolic binding and untouched-census obligations are sufficiently closed;
- whether a future repeated-`_` target grammar is worth pursuing on correct cases;
- any record-field, duplicate-emission, selector-dispatch, mixed-API, positional-subset, or
  proper-subset-manual policy; and
- any claimed E15 recall improvement.

## 9. Reproduction artifacts

Run from the repository root with the project environment:

```bash
PYTHONPATH=src:evaluation/development/multitest-recall-recon-e14 \
  .venv/bin/python evaluation/development/multitest-recall-recon-e14/census.py
PYTHONPATH=src:evaluation/development/multitest-recall-recon-e14 \
  .venv/bin/python evaluation/development/multitest-recall-recon-e14/ladders.py
PYTHONPATH=src:evaluation/development/multitest-recall-recon-e14 \
  .venv/bin/python evaluation/development/multitest-recall-recon-e14/sweep.py
```

`MANIFEST.json` pins every recon artifact. These scripts read sealed envelope bytes but never write
under any `blind-envelope-*` directory.
