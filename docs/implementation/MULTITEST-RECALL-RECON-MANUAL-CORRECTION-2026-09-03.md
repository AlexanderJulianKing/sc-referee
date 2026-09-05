# Multiple-testing recall reconnaissance: the manual-correction family (2026-09-03)

Post-hoc, unblinded analysis of the four still-open positives that abstain on
`unresolved-manual-correction-present` under the merged development detector
`code_csv_multiple_testing 3.4.0` at repo `f23c750c`: E13 P6, E14 P6, E15 P3, E16 P6. All four
envelopes are scored and sealed; their sources were read for this recon only after the fact. This
document is analysis only and changes no production behavior.

It follows the method of `docs/implementation/MULTITEST-RECALL-RECON-E18-2026-09-02.md`: captured
first triggers rather than source read by eye, minimal anchored rewrites that flip the outcome,
both the direct analyzer path and the real pipeline, and **observed** kept separate from
**inferred**.

## 0. Provenance

| Evidence | SHA-256 |
|---|---|
| E13 `ROLE_MAP.json` | `456780e6ab2a5decb7c99d31de9a6e898b7f3936e40bf378932aa51e3cda74cb` |
| E14 `ROLE_MAP.json` | `b9f56f863be69882b07d98423d55691bd4f1bafec1bfa41a83edd080a951e69e` |
| E15 `ROLE_MAP.json` | `56ed6389929f4a322e9ec21de87adabefc409f17192fbbfabd7819dad0385ba4` |
| E16 `ROLE_MAP.json` | `056e2b8ecf1ff0d9a9a2010ea8e4b090e7bd9aeafc943e4e427a1d0b3349826b` |
| E13 P6 `analysis.py` | `413eced1287568684822e44c77c5c65aa6301c1a564ebb7eb2d7e54b3e1484fc` |
| E14 P6 `analysis.py` | `498d02f5a10d29f816413cc67a2d146cdca46596e0c78f797f4322bc5d035f94` |
| E15 P3 `analysis.py` | `db2fbe393c5fda392ba8f13ef1a5176549194559c3fd104737331e72471eba4a` |
| E16 P6 `analysis.py` | `3e7cddffc48c451fc50b069338f94db0d5ae8df6e7a882f37a38bc3e4a6450ff` |
| `code_csv_multiple_testing_dataflow_v3_4.py` | `f690db88677a9f79a3a162dc7dff907d8c377a28c1d2b02095f6fadea62ed789` |
| `code_csv_multiple_testing_dataflow_v3_3.py` | `ddcb29549dda5dcf164848730679027161e34692282cfeaabf84e089db58b857` |
| `code_csv_multiple_testing_dataflow_v3.py` | `0388b4a1d3a28b7549af85362d0d4e7f13ffc2b4807dc129d242c4927870c0d1` |
| `code_csv_multiple_testing_correction_model_v3_4.py` | `b42ca5fbbc31c8faca5d84627c403a6586d6ef48648051f941593913a9cc292a` |
| `multiple_testing_scope_questions_v1.py` | `b6d985b2481d80b174a661411887973bb5cf204b5f9003344119cd134f55a36a` |

Case identities: E13 P6 `d0f9fcd52f47e4d64668`, E14 P6 `94786af7eca95fff6d78`,
E15 P3 `afe47b2a7ea87ed21a69`, E16 P6 `8ff6de728df8f29261aa`.

**Line-number note.** `dataflow_v3_3.py` is not byte-identical to the copy the E18 recon cited: the
ADR-0081 frozen-lane performance re-pin landed between `f85d4f45` and `f23c750c`, and line numbers
in that file moved by roughly fifteen. Every line number below is at `f23c750c`.

Two independent measurement paths were used for every outcome claim.

1. **Direct analyzer.** `analyze_code_csv_multiple_testing_dataflow` from
   `code_csv_multiple_testing_dataflow_v3_4`, called with the inputs the prototype harness builds
   (`evaluation/development/multitest-code-slice-v3_4/prototype-sweep/harness.py`, `inputs`), with
   each case's `profile_1_2_0.json` supplying the authorized family. On sealed source it reproduces
   all four abstentions.
2. **Real pipeline.** `e18-tools/run_probes_mi.sh` with the case's own `MI`, which freezes a method
   contract with the CLI and then audits, reading the outcome out of `audit/semantic.lock.json`.
   Probe projects are copies of the case's `project/` plus its `profile_1_2_0.json`, with
   `analysis.py` replaced by the rewrite under test. Probes live under `/tmp/mc-recon/probes` and
   are not committed.

First-trigger attribution was done by tracing return events in the shipped detector modules and
capturing the frame of the innermost function that returns the final reason. Every trigger named
below is a captured frame value.

One structural fact about the frozen lane matters for reading the traces. The merged detector is a
stack of wrappers: `dataflow_v3_4` runs `dataflow_v3_3`, which runs `dataflow_v3_2`, which runs
`dataflow_v3`, and each layer re-analyses only if the layer below abstained. The engine class
`_MtEngine` exists in two copies, `dataflow_v3.py` and `dataflow_v3_3.py`, with the same predicate
names. Traces below name the `dataflow_v3_3.py` copy, which is the one the 3.4 re-analysis
executes; the identical predicate in `dataflow_v3.py` produces the frozen result first.

## 1. Per-case disposition

| Role | Case | Hand-correction idiom (observed) | First trigger (observed) | Class |
|---|---|---|---|---|
| E13 P6 | `d0f9fc` | `min(p_raw * N_CORRECTED, 1.0)` on 3 of 5 outcomes, `N_CORRECTED = len(CORRECTED_OUTCOMES) == 3` | `_manual_corrections:13009`, `_exact_family_size(N_CORRECTED)` false | true refusal at the frozen factor policy |
| E14 P6 | `94786a` | `min(res["p_raw"] * n_comparisons, 1.0)` on 4 of 8, `n_comparisons = len(CORRECTED_OUTCOMES) == 4` | same site, `_exact_family_size(n_comparisons)` false | true refusal at the same policy, three walls deep |
| E15 P3 | `afe47b` | **none.** No correction of any kind; five raw p-values at 0.05 | `_off_grammar_transform_guard:13477` on `len(results)` in a summary print | mislabeled, over-broad guard |
| E16 P6 | `8ff6de` | `product = r["p_raw"] * n_comparisons` then `p_corrected = min(product, 1.0)` on 2 of 5, factor 5 | `_off_grammar_transform_guard:13427` on the bare product at line 84 | over-narrow fold grammar, then a distinct consumer wall |

## 2. Per-miss first-trigger analysis

### 2.1 E13 P6 `d0f9fcd52f47e4d64668`, five outcomes, three corrected

**Idiom.** The multiplier is the size of the corrected subset, not the size of the declared family.

```python
# analysis.py:36-41
CORRECTED_OUTCOMES = [
    "symptom_severity_score_0_500",
    "worst_abdominal_pain_0_10",
    "bloating_days_per_week",
]
N_CORRECTED = len(CORRECTED_OUTCOMES)
```

```python
# analysis.py:94-99
        if column in CORRECTED_OUTCOMES:
            p_corrected = min(p_raw * N_CORRECTED, 1.0)
            print("  Corrected p-value (x{}, capped at 1) = {:.4f}".format(
                N_CORRECTED, p_corrected))
            print("  Verdict (on corrected p, alpha = {}): {}".format(
                ALPHA, verdict(p_corrected)))
```

**First trigger.** Captured in the frame of `_manual_corrections`
(`dataflow_v3_3.py:12962`) at the line that returns the reason, `13009`:

```
call            = <Call line=95: min(p_raw__mt_76_0 * N_CORRECTED, 1.0)>
api             = 'min'
product         = <BinOp line=95: p_raw__mt_76_0 * N_CORRECTED>
cap             = <Constant line=95: 1.0>
positions       = frozenset({0})
n_node          = <Name line=95: N_CORRECTED>
```

The fold is recognized as a capped product with exactly one p origin. The return is taken by
`if not self._exact_family_size(n_node): return (), "unresolved-manual-correction-present"`.

**AP recognizer.** `analyze_correction_model` (`correction_model_v3_4.py:4486`) reports
`{"gate": "single-fold", "fold_count": 0, "rejected": []}`, which is the value the E18 recon
recorded. The fold does not even reach the `rejected` list. `_resolve_factor`
(`correction_model_v3_4.py:3081-3140`) admits `len(NAME)` only when the sequence's own first
components are order-equal to the contract outcome columns; `CORRECTED_OUTCOMES` holds three of the
five, so the factor resolves to `None`, `_match_product` returns `None`, and `_match_adjustment`
never produces a candidate to reject.

**Evidence (one construct changed per rung).**

| Rung | Only change | Direct analyzer | Real pipeline |
|---|---|---|---|
| r0 | sealed source | abstain `unresolved-manual-correction-present` | `unsupported`, abstain `unresolved-manual-correction-present` |
| r1 | `N_CORRECTED = len(OUTCOMES)` (still module level) | abstain, same site, same captured `n_node` | not run |
| r1b | `N_CORRECTED = 5` (module level) | **candidate `strict_subset`, N=5, corrected `(0, 1, 2)`** | not run |
| r1c | factor written inline as `min(p_raw * len(OUTCOMES), 1.0)` | **candidate `strict_subset`, N=5, corrected `(0, 1, 2)`** | not run |
| r1d | local `n_local = len(OUTCOMES)` in `main()`, used as the factor | **candidate `strict_subset`, N=5, corrected `(0, 1, 2)`** | **`applicable`, `recognized_strict_subset_family_correction`, N=5, corrected `[0, 1, 2]`** |
| r1e | local `n_local = len(CORRECTED_OUTCOMES)` in `main()` (value 3) | abstain, same site | `unsupported`, abstain `unresolved-manual-correction-present` |

r1e is the isolating control. It removes the scope difference and keeps the value, and the refusal
survives, so the factor **value** is load-bearing. r1 and r1d isolate the other half: the same
value 5 written as `len(OUTCOMES)` is refused through a module-level name and admitted through a
function-local one.

**Second observed fact, not the first trigger.** Instrumenting `_exact_family_size`
(`dataflow_v3_3.py:13023`) on rung r1 shows `self.assignments` holds only bindings from the analysed
scope after helper inlining (`data`, `group_a`, `group_b`, the expanded `p_corrected__mt_76_*`, and
so on) and does not hold module-level `N_CORRECTED`, while `self.contract_table_names` is
`{'OUTCOMES'}`. So the `Name -> len(CONTRACT_TABLE)` recursion never fires for a module-level
constant, although the inline `len(OUTCOMES)` production and the module-level integer literal both
resolve. This is a small implementation gap and it is not load-bearing for this case: closing it
alone leaves the factor at 3 and the refusal in place.

**Disposition: TRUE REFUSAL at the frozen factor policy.** No false property is asserted about the
program. The refusal is the policy line stated in
`docs/implementation/MULTITEST-3.2-CORRECTION-RECOGNITION-DESIGN-2026-08-29.md` section 1: a factor
is a declared-family correction only when its resolved integer equals the contract family size `N`,
and a factor smaller than `N` abstains because it proves no declared-family error control. E13 P6 is
that exact case, factor 3 against a five-outcome contract.

**What a narrow admission would need to prove.** The scientific object here is a Bonferroni fold
whose divisor is the size of the corrected subset rather than the declared family. To classify it
the detector would need a closed grammar for the sub-family factor:

1. `K` resolves under the existing 4.2 productions extended by one form: `len(SUBSET_TABLE)` where
   `SUBSET_TABLE` is an immutable list or tuple display of unique string constants that is a proper
   subset of the contract outcome columns, with a single binding anywhere in the module.
2. `C`, the corrected position set, is derived only by the existing 4.5 routes, and `C` is exactly
   the position set of `SUBSET_TABLE`.
3. `K == len(C)` exactly, and `len(C) < N`. Any other relation between `K`, `len(C)` and `N` keeps
   refusing.
4. Every position outside `C` has an independently proved raw conclusion, as `strict_subset`
   already requires.

Even with all four proved, the classification is the open question. `strict_subset` today means
"factor `N` applied to a proper subset", which is a valid Bonferroni value for those positions.
A factor equal to the subset size is not a valid family-wise value for any reading of the declared
family, so it cannot reuse that classification without changing what `strict_subset` asserts.
**This is a record-meaning change and needs an ADR**, not an implementation ticket.

**Frozen-lane rules that own it.** `_manual_corrections` and `_exact_family_size`
(`dataflow_v3_3.py:12962-13018` and `13023-13052`, mirrored at `dataflow_v3.py:12938`), and
`_resolve_factor`
(`correction_model_v3_4.py:3081`).

**Observed FA surface.** An exact engine-level census over all 135 opened cases with a
`profile_1_2_0.json` (E10 through E18) hooked `_manual_corrections` and logged every capped fold it
examines together with the `_exact_family_size` verdict for that fold's factor node. Twenty-four of
the 135 cases reach `_manual_corrections` at all, fourteen of them negatives. **E13 P6 and E14 P6
are the only two cases in the whole population that present a capped manual fold whose factor fails
`_exact_family_size`.** Not one negative does. The fourteen negatives that reach the function are
E10 N2, E10 N9, E11 N2, E11 N9, E13 N1, E13 N2, E13 N9, E15 N9, E16 N2, E16 N9, E17 N2, E17 N9,
E18 N2 and E18 N9; thirteen of them abstain `unresolved-decision-threshold` on Sidak or
per-comparison alpha designs and E13 N1 abstains `correction-family-lineage-unresolved`. A
syntactic scan of the 50-case open corpus finds no sub-family manual factor. The 111 cases that do
not reach `_manual_corrections` are fronted by an earlier wall and are the re-proof set, not the
direct surface.

### 2.2 E14 P6 `94786af7eca95fff6d78`, eight outcomes, four corrected

**Idiom.** The same sub-family factor, this time bound inside `main()`.

```python
# analysis.py:32-37
CORRECTED_OUTCOMES = [
    "borg_exertion",
    "neck_shoulder_vas_mm",
    "wrist_hand_vas_mm",
    "mean_heart_rate_bpm",
]
```

```python
# analysis.py:84 and 99-104
    n_comparisons = len(CORRECTED_OUTCOMES)
...
        if column in CORRECTED_OUTCOMES:
            res["p_used"] = min(res["p_raw"] * n_comparisons, 1.0)
            res["p_kind"] = "corrected"
        else:
            res["p_used"] = res["p_raw"]
            res["p_kind"] = "raw"
```

**First trigger.** The same site, `_manual_corrections` (`dataflow_v3_3.py:13009`):

```
call      = <Call line=100: min(res__mt_94_0['p_raw'] * n_comparisons, 1.0)>
positions = frozenset({0})
n_node    = <Name line=100: n_comparisons>
```

**AP recognizer.** `{"gate": "single-fold", "fold_count": 0, "rejected": []}`, for the same reason
as E13 P6: `len(CORRECTED_OUTCOMES)` is not a contract-table `len`.

**Evidence.**

| Rung | Only change | Direct analyzer | Real pipeline |
|---|---|---|---|
| r0 | sealed source | abstain `unresolved-manual-correction-present` | `unsupported`, abstain `unresolved-manual-correction-present` |
| r1 | `n_comparisons = len(OUTCOMES)` (factor 8) | abstain `hierarchical-gatekeeping-present` | `unsupported`, abstain `hierarchical-gatekeeping-present` |
| r1b | `n_comparisons = 8` | abstain `hierarchical-gatekeeping-present`, same trigger as r1 | not run |
| r2 | r1 plus the four `load_data` validation `if ... raise` blocks removed | abstain `hierarchical-gatekeeping-present`, new trigger | not run |
| r3 | r1 plus validation blocks plus the per-outcome conclusions loop removed | **candidate `strict_subset`, N=8, corrected `(0, 1, 2, 4)`** | **`applicable`, `recognized_strict_subset_family_correction`, N=8, corrected `[0, 1, 2, 4]`** |

Note that r1 succeeds where E13 P6's r1 fails: `n_comparisons` is bound inside `main()`, so
`self.assignments` holds it and the `Name -> len(CONTRACT_TABLE)` recursion resolves. The two cases
together are a clean natural contrast on the module-scope gap named in 2.1.

**Second wall (observed).** On r1 the hierarchy guard trigger is captured in `_hierarchy_guard`
(`dataflow_v3_3.py:14052`) with `owner` the input-validation `If` inlined from `load_data`:

```python
# analysis.py:47-48
    if df[[c for c, _ in OUTCOMES]].isna().any().any():
        raise ValueError("CSV contains blank outcome cells")
```

Instrumenting `_control_tracked` (`dataflow_v3_3.py:14288`) on that node gives
`p_derived=False, correction_control=False, outcome_headers=['borg_exertion',
'mean_heart_rate_bpm', 'neck_shoulder_vas_mm', ...]`. The control is tracked purely by the
third branch, `len(self._outcome_headers(node, set(), 0)) >= 2`: the inlined column selector names
eight contract outcomes, and the body raises, so the guard treats it as an execution-prevention
control over the family. Nothing p-derived is involved.

**Third wall (observed).** On r2 the trigger moves to the presentation `If` in the conclusions loop:

```python
# analysis.py:126-138
    for i, res in enumerate(results, start=1):
        direction = "higher" if res["difference"] > 0 else "lower"
        if res["significant"]:
            sentence = (...)
        else:
            sentence = (...)
        print(f"  {i}. {res['label']}: {sentence}")
```

The captured `expression` is `res['significant']` and the branch that tracks it is `_p_origins`.
The body binds `sentence` before the print, so `_mt_v21_terminal_rendering_if` does not exempt it.
This is the loop-and-local form of the E16 recon's item 1, already owned by the E18 recon's
delta 1 family.

**Disposition: TRUE REFUSAL at the frozen factor policy, three walls deep.** The first wall is the
same policy line as E13 P6. Behind it sit two hierarchy-guard walls of different kinds: an
outcome-headers input-validation control, and a presentation `If` that binds a local before
printing.

**What a narrow admission would need to prove.** The factor grammar of 2.1, plus, for wall two,
that a control is a data-precondition check and not a family gate: the `If` body contains exactly
one `Raise` and nothing else, the raise is unconditional within that body, there is no `else`, the
control expression has empty `_p_origins`, and every reaching path from the control either raises or
falls through to the identical statement sequence. That last clause is what makes it a precondition
rather than a screen. For wall three, the terminal-position proof the E16 and E18 recons already
specify for presentation `If` statements whose body binds a local before reaching a registered sink.

**Frozen-lane rules that own it.** Factor: as in 2.1. Wall two: `_control_tracked`
(`dataflow_v3_3.py:14288-14304`), specifically the `_outcome_headers` branch at `14294`, consumed by
`_hierarchy_guard` (`14015-14053`). Wall three: `_mt_v21_terminal_rendering_if`
(`dataflow_v3_3.py:13877`).

**Observed FA surface.** For the factor delta, the engine-level census in 2.1 applies unchanged:
zero negatives. For wall two, a syntactic census over the 135 opened cases for an `If` whose body
raises and whose test names the contract outcome table or two or more outcome columns finds five
cases: E14 P6 itself, and the negatives E10 N8, E13 N8, E14 N3 and E16 N6. All four negatives are
fronted by an earlier wall today (`test-battery-cardinality-unresolved`,
`test-battery-cardinality-unresolved`, `authorized-family-test-census-incomplete` and
`authorized-reader-lineage-unavailable` respectively), so the widening would not by itself move
them, and all four must still re-prove. The two negatives that currently abstain
`hierarchical-gatekeeping-present`, E14 N9 and E18 N5, do **not** get that reason from
`_MtEngine._hierarchy_guard`: their captured frame is `dataflow_v3.py:15531`,
`return MultipleTestingDataflowResult(None, model.outcome.reason_or_classification)`, so the reason
is produced by the record-model side table `code_csv_multiple_testing_record_model_v3.py`. That is a
different owner and a separate re-proof obligation. The syntactic census is a proxy and should be
read as a lower bound.

### 2.3 E15 P3 `afe47b2a7ea87ed21a69`, five outcomes, no correction at all

**Idiom.** There is no hand correction in this program. Every declared outcome is judged on its own
raw p-value at 0.05, which is the plain uncorrected-family misstep:

```python
# analysis.py:70-72
        # Each declared outcome is its own exposure or health question, so the
        # verdict comes straight from that outcome's own p-value.
        "significant": p_value < ALPHA,
```

The construct that stops the detector is the closing summary line:

```python
# analysis.py:150-154
    n_significant = sum(result["significant"] for result in results)
    print(
        f"{n_significant} of {len(results)} declared outcomes separated the two "
        f"ventilation groups at p < {ALPHA}."
    )
```

**First trigger.** Captured in `_off_grammar_transform_guard` (`dataflow_v3_3.py:13396`) at the
`Call` branch's final refusal, line `13477`:

```
api      = 'len'
terminal = 'len'
node     = <Call line=152: len(results)>
```

`results` is the proved p-record collection, so `self._p_origins(node)` is non-empty and the node
enters the walk. `len` is not a sink call, not a family call, not a recognized extremum, not a
presentation join, not a scalar cast or round, and `_mt_callee_terminal` gives `len`, which is not
in the admitted terminal set `{append, extend, add, format}`. The guard refuses.

**AP recognizer.** `{"gate": "single-fold", "fold_count": 0, "rejected": []}`. There is no fold
because there is no correction. `locate_correction_scope_witness`
(`multiple_testing_scope_questions_v1.py`) also returns `None` for this case under the qualifying
reason, while it returns a `manual-adjusted-p-arithmetic` witness for the other three misses. So the
reason `unresolved-manual-correction-present` is emitted with nothing in the program for it to point
at, and even the question layer declines to raise the scope question.

**Evidence.**

| Rung | Only change | Direct analyzer | Real pipeline |
|---|---|---|---|
| r0 | sealed source | abstain `unresolved-manual-correction-present` | `unsupported`, abstain `unresolved-manual-correction-present` |
| r1 | `len(results)` becomes `len(DECLARED_OUTCOMES)` inside the same f-string | **candidate `none`, N=5** | **`applicable`, `no_recognized_family_correction`, N=5, corrected `[]`** |
| rC | r1 plus one re-added `print(f"rows: {len(results)}")` | abstain, same site, node `len(results)` at the new line | not run |

r1 is a one-token change in one display string. rC re-adds the construct in an unrelated print and
the refusal returns, so the single `len()` is load-bearing.

**Disposition: MISLABELED, over-broad guard.** The reason asserts a property of the program, that
an unresolved manual correction is present. E15 P3 contains no correction of any kind: no product,
no divided threshold, no correction call, no correction terminal, and no scope witness. What the
guard actually found is an unaccounted-for consumer of the p-record collection, and `len()` of that
collection is not a p transform at all. It reads the collection's cardinality, which the analyzer
already knows exactly, and the value reaches only a print. Nothing about the number of records can
change any p-value, any threshold, or any conclusion.

**What a narrow admission would need to prove.** That the call is a cardinality read of a fully
reconstructed family collection, used only for display. Concretely: the callee resolves to the
unshadowed builtin `len`, there is exactly one positional argument and no keywords, the argument is
a `Name` whose reaching binding is the proved p-record collection itself and not an alias or a
filtered copy, the collection's reconstructed position set is exactly `0..N-1`, and the call's every
load reaches a registered sink through the existing
`_mt_v2_rendering_load_reaches_sink` route without entering any comparison, arithmetic, subscript,
threshold, or record store. A `len()` over a filtered comprehension, over an alias, or feeding
anything other than a display payload keeps refusing. Note that the admitted value is a constant the
analyzer can already compute, so admitting it adds no new value route; it removes an unaccounted-for
consumer.

**Frozen-lane rule that owns it.** `_off_grammar_transform_guard` (`dataflow_v3_3.py:13396-13478`),
specifically the `Call` branch's terminal allow-list at `13471-13477`, mirrored at
`dataflow_v3.py:13372`. Widening it narrows an abstention gate, so every gated negative has to
re-prove.

**Observed FA surface.** Rather than a syntactic proxy, this was measured directly. A hook on
`_off_grammar_transform_guard` logged the full inventory of p-derived `BinOp` and `Call` nodes the
guard walks, for all 135 opened cases. Only 21 cases reach the guard at all, thirteen of them
negatives, and **E15 P3 is the only case in the whole population whose p-derived inventory contains
a `len()` call**. The thirteen negatives that reach the guard are E10 N2, E10 N9, E11 N2, E11 N9,
E13 N2, E13 N9, E15 N9, E16 N2, E16 N9, E17 N2, E17 N9, E18 N2 and E18 N9; they are the re-proof
set. A syntactic scan of the 50-case open corpus finds one candidate, `spec-22`, whose `len(rows)`
is measured **not** p-derived and whose analysis never reaches the guard
(`authorized-family-test-census-incomplete`).

### 2.4 E16 P6 `8ff6de728df8f29261aa`, five outcomes, two corrected

**Idiom.** The fold is split across two statements, and the raw and corrected p-values are later
selected by a `None` sentinel.

```python
# analysis.py:82-92
    for r in results:
        if r["column"] in SAFETY_OUTCOMES:
            product = r["p_raw"] * n_comparisons
            p_corrected = min(product, 1.0)
            r["p_corrected"] = p_corrected
            print("{:<24s} p_raw={:.6g} x {} = {:.6g} -> capped at 1 -> "
                  "p_corrected={:.6g}".format(
                      r["column"], r["p_raw"], n_comparisons,
                      product, p_corrected))
        else:
            r["p_corrected"] = None
```

```python
# analysis.py:97-106
    for r in results:
        if r["p_corrected"] is not None:
            p_used = r["p_corrected"]
            basis = "corrected p"
        else:
            p_used = r["p_raw"]
            basis = "raw p"
```

The factor here is correct: `n_comparisons = len(OUTCOMES)` is 5, the full declared family.

**First trigger.** Captured in `_off_grammar_transform_guard` at the `BinOp` branch, line `13427`:

```
node     = <BinOp line=84: p_raw__mt_57_0 * n_comparisons>
terminal = 'format'
api      = None
```

The product is p-derived and is not in `self.manual_multiplications`, because
`_manual_corrections` only registers a `BinOp` that appears **inside** the `min(...)` call. Here
`min(product, 1.0)` takes a `Name`, so no fold is recognized, and the naked product reaches the
guard.

**AP recognizer.** `{"gate": "single-fold", "fold_count": 0, "rejected": [{"line": 84, "factor": 5,
"positions": null, "form": "bare-product"}]}`, which is the value the E18 recon recorded. The factor
resolves to 5; the positions do not. Instrumenting `_positions_for` (`correction_model_v3_4.py:3547`) and
`_complete_rows` (`3368`) shows why: for the owner of the line-84 statement,
`_complete_rows` returns `None`, because that loop is `for r in results:` over the record collection
rather than over the outcome table, so no row table can be built. The same instrumentation shows
`_complete_rows` succeeding with 5 rows for the record-constructor loop at line 57 and
`_positions_for` returning `(0, 1, 2, 3, 4)` there.

**Evidence.**

| Rung | Only change | Direct analyzer | Real pipeline |
|---|---|---|---|
| r0 | sealed source | abstain `unresolved-manual-correction-present` | `unsupported`, abstain `unresolved-manual-correction-present` |
| rC | split kept, the bare `product` removed from the print | abstain, same site, same node | not run |
| r2 | fold written inline as `min(r["p_raw"] * n_comparisons, 1.0)`, `product` local removed | abstain `unresolved-decision-threshold` | `unsupported`, abstain `unresolved-decision-threshold` |
| r3 | r2 plus the `None` sentinel replaced by `if r["column"] in SAFETY_OUTCOMES:` | **candidate `strict_subset`, N=5, corrected `(0, 1)`** | **`applicable`, `recognized_strict_subset_family_correction`, N=5, corrected `[0, 1]`** |

rC is the isolating control: keeping the two-statement split but not printing the product leaves the
refusal at the same node, so the wall is the split fold shape and not the display of the product.
r3's corrected positions `(0, 1)` are exactly `oil_content_g100g` and `acrylamide_ug_kg`.

**Second wall (observed).** On r2 the trigger is `_decision_threshold_guard`
(`dataflow_v3_3.py:13634`) at line `13654`:

```
comparison = <Compare line=97: __sc_mt_record_72_0['p_corrected'] is not None>
```

The guard walks every p-derived `Compare` and refuses at `13653-13654` when the operator is not one
of `Lt`, `LtE`, `Gt`, `GtE`. `is not` is `ast.IsNot`, so the sentinel comparison is refused before
any threshold reasoning happens.

**Disposition: OVER-NARROW FOLD GRAMMAR at wall one, distinct consumer gap at wall two.** Wall one
has no scientific content. `product = p * N; p_corrected = min(product, 1.0)` and
`p_corrected = min(p * N, 1.0)` are the same arithmetic on the same values with the same factor,
already proved to be exactly `N`, and the detector returns the scientifically correct answer as soon
as the two statements are merged. Wall two is different in kind: a `None` sentinel really is a
second, data-independent route by which a position can take either the raw or the corrected value,
and the guard has no rule that folds it.

**What a narrow admission would need to prove.**

For wall one, that a two-statement fold is one fold. A safe form: a simple assignment whose target
is a local `Name` with exactly one reaching store and no other store anywhere in the expanded owner,
whose value is exactly `P(POS) * K` or `K * P(POS)` under the unchanged 4.1 and 4.2 productions,
whose every load is either the sole product argument of one admitted `CAP` production or a display
payload reaching a registered sink, and where the local does not escape the owner, is not stored
into a record, is not compared, and is not rebound. The product node and the cap call are then
registered together as one `_MtCorrection`, and the product enters `manual_multiplications` so the
off-grammar guard skips it exactly as it does today for the inline form. Anything else, a second
store, an aug-assign, a load into arithmetic, a load into a comparison, keeps refusing.

For wall two, that a `None` sentinel is a static partition and not a data-dependent selector. The
grammar would need: the sentinel field has exactly two reaching stores in the expanded owner, one
under the branch that establishes `C` and one under its complement, the `C`-branch store is the
admitted `ADJUSTED` production and the complement store is exactly the literal `None`, the selecting
comparison is `FIELD is None` or `FIELD is not None` on that same field with no other operand, and
the two arms of the selection bind the corrected origin for `C` and an independently proved raw
`P(POS)` for the complement. The position sets must be complementary and disjoint with union
`0..N-1`, which is the existing section 5.2 requirement. This is close to but not the same as the
`_complete_rows` work: the partition here is established by a store in an earlier loop and read in a
later one.

Also worth recording as a third, smaller item: `_positions_for` refuses this case's own fold because
the correcting loop iterates the record collection rather than the outcome table. Merging the fold
inline is what lets the record-constructor loop at line 57 supply the row table instead. A direct
admission for `for r in <proved p-record collection>:` as a row-table source would remove that
dependency, and it is the same shape the E18 recon flagged for this case.

**Frozen-lane rules that own it.** Wall one: `_manual_corrections`
(`dataflow_v3_3.py:12962-13018`) and the `BinOp` branch of `_off_grammar_transform_guard`
(`13411-13427`), plus `_match_adjustment` and `_match_product`
(`correction_model_v3_4.py:3179-3252`). Wall two: `_decision_threshold_guard`
(`dataflow_v3_3.py:13634-13681`), specifically the operator-kind check at `13653-13654`. Row table:
`_complete_rows` (`correction_model_v3_4.py:3368`) and `_positions_for` (`3547-3603`).

**Observed FA surface.** For wall one, no negative among the 135 opened cases has its first trigger
at `_off_grammar_transform_guard:13427`, and the p-derived node inventory measured in 2.3 finds a
bare p-derived product outside an accepted fold only in E16 P6. A syntactic scan for the
split-then-cap shape over the 135 opened cases and the 50-case open corpus finds only E16 P6. For
wall two, the surface is much larger in the guard as a whole: fourteen of the 81 opened negatives
abstain `unresolved-decision-threshold`, and thirteen of them have their first trigger captured at
`13677-13678`, the check that the threshold literal is in the permitted set. Those are Sidak and
per-comparison alpha designs, a different branch from the operator-kind check at `13653-13654` where
E16 P6 lands, so the direct surface for the sentinel admission is zero. The thirteen still have to
re-prove, because the widening lets a program past a refusal that used to fire first.

## 3. What the four have in common, and where they part

All four were designed as the same misstep family: a declared family of tests is judged without
family-wise error control, with the correction either absent or applied to only part of the family.
The detector abstains on all four with one reason string, and that single string covers three
unrelated causes.

1. **A frozen policy line** (E13 P6, E14 P6). The correction is located, the positions are
   located, and the factor is refused because it is the subset size rather than `N`.
2. **A guard whose reason does not describe what it found** (E15 P3). There is no correction at
   all. The guard found an unaccounted-for consumer of the record collection and reported it as a
   manual correction.
3. **A fold grammar that reads one spelling** (E16 P6). The correction is written across two
   statements instead of one.

The load-bearing observation matches the E18 recon's. Two of the four are not scientifically harder
than the cases the detector already catches. E15 P3 is the plain uncorrected family, the same shape
as E13 P1 and E16 P1, and one token in a print string is the whole difference. E16 P6 is a correct
partial Bonferroni with the right factor, and a line break is the whole difference. The other two,
E13 P6 and E14 P6, are genuinely a different scientific object: a correction whose divisor does not
match any reading of the declared family.

The scope-question layer separates the same way. E13 P6, E14 P6 and E16 P6 each produce a
`manual-adjusted-p-arithmetic` correction-scope witness, so a reviewer sees a `MaterialQuestion` and
a linked `ConditionalConcern` on the sealed run. E15 P3 produces no witness, so its abstention is
silent as well as mislabeled.

## 4. Grouped deltas, ranked by measured yield

The E18 recon inferred that these four are probably two or three distinct deltas. **Measured: they
are three, and one of the three splits into two independent pieces.** Ranking is by yield against
the still-open misses, all of it measured on the merged detector through both paths.

### Delta A. `len()` of a proved p-record collection reaching display only

Yield **1 measured** (E15 P3), through both paths, from a one-token rewrite. Smallest delta in the
list: one terminal added to one allow-list in `_off_grammar_transform_guard`, guarded by the
cardinality-read conditions in 2.3. Direct FA surface measured at zero: E15 P3 is the only case
among 135 whose p-derived node inventory holds a `len()`, and only 21 cases reach the guard at all.
It also fixes a reason that is currently false about the program it is applied to, which is worth
something independent of recall. **Implementation, not policy. Rank 1.**

### Delta B. One fold written as two statements

Yield **0 alone, 1 when paired with delta C** (E16 P6). The rewrite that flips wall one is
mechanical and the detector then returns the correct `strict_subset` N=5 corrected `(0, 1)` once
wall two is also cleared. Direct FA surface measured at zero; the split-then-cap shape appears in no
other opened case and in no corpus case. **Implementation, not policy. Rank 2**, on the
understanding that it buys nothing by itself.

### Delta C. `None`-sentinel raw/corrected partition

Yield **0 alone, 1 when paired with delta B** (E16 P6). Larger than delta B: it needs a static
two-store partition proof, and although its own branch of `_decision_threshold_guard` carries no
negatives, the guard as a whole carries fourteen of the 81 opened negatives, every one of which
must re-prove. This is the E16 recon's item 4 residual finally reduced to a specific missing proof.
**Implementation, not policy, but it is the riskiest of the implementation deltas. Rank 3.**

### Delta D. Sub-family Bonferroni factor

Yield **2 if admitted** (E13 P6, E14 P6 at wall one), the largest single bucket in this recon, and
**0 without an ADR**. The refusal is the explicit, deliberate policy line of the 3.2 design: a
factor other than exactly `N` abstains, and a factor below `N` proves no declared-family error
control. Classifying a fold whose divisor is the corrected subset's own size cannot reuse
`strict_subset` without changing what that classification asserts, so it needs a record-meaning
decision before any build. Direct FA surface measured at zero: no opened negative presents a capped
manual fold with a non-`N` factor.

E14 P6 additionally needs two hierarchy-guard deltas behind the policy one, so its yield is
conditional on all three. **Policy question first, ADR before implementation. Rank 4 for E13 P6,
rank 5 for E14 P6.**

Two smaller items fall out and should be recorded but not ranked as deltas of their own.

- **D1. Module-level `Name -> len(CONTRACT_TABLE)` as a family-size proof.** Observed gap:
  `_exact_family_size` recurses only through `self.assignments`, which holds in-scope bindings
  only, so `N_COMPARISONS = len(OUTCOMES)` at module level is refused while the same binding inside
  `main()` is admitted and the inline `len(OUTCOMES)` is admitted. Yield 0 on its own. It is a
  correctness wart in the factor grammar and it will be in the way of any sub-family factor work.
- **D2. `for r in <proved p-record collection>:` as a row-table source for `_positions_for`.**
  Observed to be why E16 P6's own fold reports `positions: null` even with the right factor. Yield 0
  on its own; it would remove delta B's dependence on merging the statements.

### What is repeated from earlier recons

Delta C is the E16 recon's item 4 (`Name`-set-selected partial hand correction) reduced to its
actual missing proof. E14 P6's third wall is the E16 recon's item 1 in its `If`-with-local form,
already inside the E18 recon's delta 1. E14 P6's second wall, the outcome-headers input-validation
control, is **new**: it appears in no earlier recon, and the 3.4 module docstring records that
"section 8's outcome-headers reason routing is measured in the design and not applied here", so the
design already knows about the routing question and has not touched the tracking rule.

## 5. Policy versus implementation

| Item | Kind | Gate |
|---|---|---|
| Delta A, `len()` cardinality read | implementation | none beyond the usual re-proof of the 13 guard-reaching negatives |
| Delta B, two-statement fold | implementation | none beyond re-proof |
| Delta C, `None`-sentinel partition | implementation | re-proof of the 14 `unresolved-decision-threshold` negatives |
| D1, module-scope family-size name | implementation | none |
| D2, record-collection row table | implementation | none |
| Delta D, sub-family factor | **policy** | new ADR or an amendment to the 3.2 policy line under ADR-0079; it changes what a correction classification asserts |
| E14 P6 wall two, validation-raise control | implementation, with a wording question attached | the design's own section-8 outcome-headers reason routing is measured and unapplied; deciding to apply it is a reason-set decision |
| E14 P6 wall three, presentation `If` with a local | implementation | already inside the E18 recon's delta 1 |

ADR-0080 does not settle delta D. It governs the question and attestation layer, which is what
already fires on E13 P6, E14 P6 and E16 P6, and it explicitly gives an author answer no power to
create a Finding, a candidate accusation, or a new corrected position. The subset question it asks
is whether a located correction covers the whole family. Delta D asks a different question: whether
a correction whose divisor is smaller than the family is a demonstrable misstep the detector may
classify on its own. That is the record-meaning decision, and it is separate from the
library-subset cardinality question that E16 P5 and E18 P5 sit behind.

## 6. Method note and limits

- Every outcome in the rung tables was measured on both paths where the table says so. Where the
  table says "not run", only the direct analyzer was used; those rungs are controls, and no claim
  in section 4 rests on a "not run" row alone.
- The FA-surface claims for deltas A, B and D are engine-level measurements over the complete
  135-case opened population with a `profile_1_2_0.json`, not syntactic proxies. The claims for
  E14 P6's wall two and for the open corpus are syntactic proxies and are lower bounds.
- A first-trigger measurement can only see the wall a case actually reaches. Cases fronted by an
  earlier wall carry no information about later ones, so every "zero direct surface" statement is a
  statement about the widened site, not a safety proof for the widening. Every widening named here
  narrows an abstention gate and therefore converts abstentions into analyzer progress; the gated
  negative populations named per delta have to re-prove.
- Envelopes E2 through E9 predate the `profile_1_2_0.json` format and are outside the 3.4 evidence
  population; they were not scanned.
