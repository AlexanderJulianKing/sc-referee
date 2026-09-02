# Multiple-testing recall reconnaissance: envelope 18 (2026-09-02)

Post-hoc, unblinded analysis of the four missed positives in `blind-envelope-18-2026-09-01`,
detector `code_csv_multiple_testing 3.4.0` (development lane) at repo `f85d4f45`. Sealed result:
recall `2/6`, `0/9` accusation candidates, `0` Findings in 30 bundles, replay `15/15`, one true
clearance (N1 `covered/complete` 5/5 on a role-map negative). Scoring is complete and
`AUDIT_RESULTS.json` is sealed, so the case sources were read for this recon only after the fact.

Everything below separates **observed** (a sealed audit row, an executed analyzer run, or a real
pipeline run recorded here) from **inferred** (a hypothesis that still needs its own build-time
proof). Nothing in this document changes production behavior; it is analysis only.

## 0. Provenance

| Evidence | SHA-256 |
|---|---|
| E18 `AUDIT_RESULTS.json` | `8aad260515d0d79ad282e56d4e03970ee531b2f865f7b88d02b4004f1667cb45` |
| E18 `ROLE_MAP.json` | `cd830c2a79ea80f4fe310d8db09893b29c74fdf25d33975c713d9161feff3d92` |
| `code_csv_multiple_testing_dataflow_v3_4.py` | `f690db88677a9f79a3a162dc7dff907d8c377a28c1d2b02095f6fadea62ed789` |
| `code_csv_multiple_testing_dataflow_v3_3.py` | `c82510238b422af746299e9e1c418a0474107d1b57d119fd7dc5685e037edd2e` |
| `code_csv_multiple_testing_terminal_presentation_v3_3.py` | `d1b9463235494ae54d4c5d2bbc3eb4f0d1b73568a4c5625993dd87dbee4b5c78` |
| `code_csv_multiple_testing_correction_model_v3_4.py` | `b42ca5fbbc31c8faca5d84627c403a6586d6ef48648051f941593913a9cc292a` |

Two independent measurement paths were used for every claim in section 2.

1. **Direct analyzer.** `analyze_code_csv_multiple_testing_dataflow` from
   `code_csv_multiple_testing_dataflow_v3_4`, called with the same inputs the prototype harness
   builds (`evaluation/development/multitest-code-slice-v3_4/prototype-sweep/harness.py`,
   `inputs`/`classify`), with the case's `profile_1_2_0.json` supplying the authorized family. The
   direct path reproduces all six sealed E18 positive rows exactly.
2. **Real pipeline.** `e18-tools/run_probes_mi.sh` with `MI=data.csv`, which freezes a method
   contract with the CLI and then audits, reading the outcome out of
   `audit/semantic.lock.json`. Probe projects are copies of a case's `project/` plus its
   `profile_1_2_0.json`, with `analysis.py` replaced by the rewrite under test. Probes live under
   `/tmp/e18-recon-probes` and are not committed.

First-trigger attribution was done by line-level tracing of the shipped analyzer, capturing the AST
node held in the guard's own frame at the line that returns the reason. Every trigger named below
is a captured frame value, not a reading of the source by eye.

## 1. Per-case disposition

| Role | Case | Author idiom (observed) | Detector outcome (observed) | Class |
|---|---|---|---|---|
| P1 | `42eec1feec0db6195a00` | Unrolled per-outcome blocks, `if p < ALPHA: print(<literal>) else: print(<literal>)`, no correction | candidate `none`, N=4 | CAUGHT |
| P2 | `5a9277448db34379ce78` | Loop over a declared-outcome table, verdict `IfExp` whose arms are `"...".format(ALPHA)` calls, printed | abstain `hierarchical-gatekeeping-present` | over-broad guard |
| P3 | `d1b1fc47ccdabd0c2f22` | Group split by a **float** literal (`salt_pct == 2.0`), record list comprehension, presentation loop | abstain `test-operand-lineage-unresolved` | narrow true refusal |
| P4 | `3fbb9d061e69e42758bd` | Helper returns a list of record dicts, presentation loop with `If` assigning literal verdicts | candidate `none`, N=3 | CAUGHT |
| P5 | `464d36cd2013ca4791d9` | Dict-of-records keyed by column, Holm over 2 of 7 primaries, nested store `results[column]["p_adjusted"]` | abstain `pvalue-family-collection-unresolved` | narrow true refusal, three walls deep |
| P6 | `2d2f5dd68825c378126b` | `csv.DictReader` reader, hand Bonferroni (`min(p*8, 1.0)`) on a **set**-selected subset of 3 of 8 | abstain `authorized-reader-lineage-unavailable` | narrow true refusal, two walls deep |

## 2. Per-miss first-trigger analysis

### 2.1 P2 `5a9277448db34379ce78`, `hierarchical-gatekeeping-present`

**First trigger.** Captured in the frame of `_hierarchy_guard`
(`code_csv_multiple_testing_dataflow_v3_3.py:14037`) at the line that returns the reason: the owner
is the `IfExp` at `analysis.py:48-52` and the tracked control expression is `p_value < ALPHA`.

```python
        verdict = (
            "significant difference at p < {}".format(ALPHA)
            if p_value < ALPHA
            else "no significant difference at p < {}".format(ALPHA)
        )
```

The guard walks every control expression and admits one only if it matches one of five enumerated
presentation exemptions. The applicable exemption is `_terminal_rendering_ifexp`
(`dataflow_v3_3.py:14327`), whose very first condition requires both arms to be **bare string
constants**:

```python
        if not (
            isinstance(node.body, ast.Constant)
            and isinstance(node.body.value, str)
            and isinstance(node.orelse, ast.Constant)
            and isinstance(node.orelse.value, str)
```

The same predicate appears twice more: `_mt_v21_display_string` (`dataflow_v3_3.py:15164`), used by
the `If`-statement lane `_mt_v21_terminal_rendering_if` (`dataflow_v3_3.py:13862`), and
`_display_string` (`code_csv_multiple_testing_terminal_presentation_v3_3.py:123`), used by the 3.3
terminal-presentation proof's own `IfExp` lane at line 799. A `.format(...)` call in either arm
fails all three.

**Evidence (rewrites, one construct changed per rung).**

| Rung | Only change | Direct analyzer | Real pipeline |
|---|---|---|---|
| P2-r0 | sealed source | abstain `hierarchical-gatekeeping-present` | `unsupported`, abstain `hierarchical-gatekeeping-present` |
| P2-r1 | both `IfExp` arms become bare string constants | **candidate `none`, N=6** | **`applicable`, `no_recognized_family_correction`, N=6, corrected `[]`** |
| P2-rB | both arms become f-strings instead | abstain `hierarchical-gatekeeping-present` | not run |
| P2-rC | `IfExp` rewritten as an `If` statement, arms still `.format(...)` | abstain `hierarchical-gatekeeping-present` | not run |

Observed detail: on the sealed source the 3.3 terminal-presentation proof yields nothing
(`prove_terminal_presentation` returns `None`; `_terminal_ifexp_positions` is empty), and on the
constant-arm rewrite it still yields nothing. The admission that flips P2-r1 comes entirely from the
frozen `_terminal_rendering_ifexp` exemption inside `_hierarchy_guard`.

**Disposition: MISLABELED / over-broad guard.** The reason asserts a property of the program, that a
hierarchical gate is present. P2 has no gate. The `IfExp` selects between two display strings, is
assigned to `verdict`, and reaches only `print`. It cannot skip a test, suppress an emission, or
change what runs. What separates P2 from the caught P4 is string formatting, not study design. Both
programs judge every declared outcome on its own raw p-value at 0.05 with no correction, and both
would be candidates if the verdict text were a plain literal.

**What a narrow admission would need to prove.** That the two arms are display values whose own
inputs are not p-derived, so that the conditional still chooses only between renderings. Concretely,
for `Call` arms of the form `<literal str>.format(*args)` and for `JoinedStr` arms: every argument
or formatted value has empty `_p_origins` and carries no decision position, the literal template
satisfies the existing length and NUL bounds, and the assigned name's every load still reaches a
registered sink through `_mt_v2_rendering_load_reaches_sink`.

**Frozen-lane rule that owns it.** `_mt_v21_display_string` (`dataflow_v3_3.py:15164`) and the
inline constant test at `_terminal_rendering_ifexp` (`dataflow_v3_3.py:14330-14334`), with the
mirror predicate `_display_string` (`terminal_presentation_v3_3.py:123`). Widening any of them is a
narrowing of an abstention gate, so it converts abstentions into analyzer progress and every gated
negative population has to re-prove.

**Observed FA surface for that widening.** A syntactic census over every opened envelope case with a
`ROLE_MAP` (E6 through E18) finds exactly three cases carrying a p-threshold conditional whose
display arms are not bare constants: E18 P2 (the positive above), E15 N8 `0aa1af228c91fde5f909`, and
E6 N1 `2e97fd3e2ab5729b7f9c`. E15 N8 currently abstains `test-battery-cardinality-unresolved`, a
wall that sits before the hierarchy guard, so the widening would not by itself move it; it must
still be re-proved. E6 N1 predates the `profile_1_2_0.json` format and is outside the 3.4 evidence
population. This census is a syntactic proxy (it matches a comparison against an `alpha`-named name
or a 0.05/0.01/0.1 literal), so treat the count as a lower bound on the surface, not a safety proof.

### 2.2 P3 `d1b1fc47ccdabd0c2f22`, `test-operand-lineage-unresolved`

**First trigger.** Captured in `_resolve_family_operands` (`dataflow_v3_3.py:11524`): the call is
`stats.ttest_ind(low['ph'], high['ph'])` and **both** `left` and `right` series resolutions are
`None`. The operands trace back to:

```python
DATA_FILE = "data.csv"
GROUP_COLUMN = "salt_pct"
LOW_SALT = 2.0
HIGH_SALT = 3.0
...
    low = data[data[GROUP_COLUMN] == LOW_SALT]
    high = data[data[GROUP_COLUMN] == HIGH_SALT]
```

The group mask parser is `_mask` (`dataflow_v3_3.py:7628`), which reads the comparator through
`resolver.string(node.comparators[0])`. `_Resolver.string` (`dataflow_v3_3.py:475-492`) returns a
value only for `str` constants, and `_Resolver.constants` is declared `dict[str, str]`
(`dataflow_v3_3.py:456`, populated at `7159`). `LOW_SALT` is bound to the float `2.0`, so the mask
never parses, the series never resolves, and the operand lineage refuses.

The CSV holds the group column as the text tokens `2.0` and `3.0` (`data.csv` header
`container_id,salt_pct,...`, first rows `C01,2.0,...` and `C02,3.0,...`), and the profile's
`group_contrast_column` is `salt_pct`. So the code is correct at runtime under pandas' numeric
dtype; the detector simply has no rule that connects a float literal to a CSV text token.

**Evidence.**

| Rung | Only change | Direct analyzer | Real pipeline |
|---|---|---|---|
| P3-r0 | sealed source | abstain `test-operand-lineage-unresolved` | `unsupported`, abstain `test-operand-lineage-unresolved` |
| P3-r1 | `LOW_SALT`/`HIGH_SALT` become the string literals `"2.0"`/`"3.0"` | abstain `hierarchical-gatekeeping-present` | `unsupported`, abstain `hierarchical-gatekeeping-present` |
| P3-r2 | mask indexing changed to `data.loc[...]`, float literals kept | abstain `test-operand-lineage-unresolved` | not run |

P3-r2 is the control: the two-step boolean-mask shape is not the problem. P1, which is caught, uses
the same `data[data[GROUP_COL] == GROUP_A]` shape with string group values.

**Second wall (observed, not the first trigger).** After P3-r1 the guard trigger captured at
`dataflow_v3_3.py:14037` is the presentation loop's iterator, not a verdict:

```python
    for position, result in enumerate(results, start=1):
        d = result["decimals"]
        verdict = ( ... )
```

The tracked control is `enumerate(results, start=1)`, and `_terminal_family_transport_loop` does not
exempt it because the loop body does more than render (it binds `d = result["decimals"]` first).
So P3 needs at least two deltas, and the second one is close to the E16 recon's terminal-position
proposal for loops.

**Disposition: NARROW TRUE REFUSAL.** The reason names a property of the analyzer's knowledge, not a
property of the program, and that knowledge really is absent: no installed rule maps the float `2.0`
onto the CSV token `2.0`. Nothing false is asserted. The refusal is narrower than it looks, though,
because the missing step is a decimal-token comparison over evidence the analyzer already holds.

**What a narrow admission would need to prove.** That a numeric group literal names exactly one CSV
group token. A safe form: accept `int`/`float` comparator constants only when the literal's exact
`repr`-normalized decimal text equals one of the two `group_values` tokens parsed from the authorized
CSV, when the group column's every non-header cell parses as a finite decimal, and when the two
tokens remain distinct under that normalization. Anything ambiguous (`2.0` versus `2.00` present in
the same column, non-finite values, thousands separators) must keep refusing.

**Frozen-lane rule that owns it.** `_Resolver.string` (`dataflow_v3_3.py:475`) and its
`constants: dict[str, str]` typing (`dataflow_v3_3.py:456`), consumed by `_mask`
(`dataflow_v3_3.py:7628`). Note that `_Resolver.string` is used far beyond group masks, so the
admission belongs in `_mask` (or a new numeric-token helper it calls), not in `_Resolver.string`.

### 2.3 P5 `464d36cd2013ca4791d9`, `pvalue-family-collection-unresolved`

**First trigger.** Captured in the closure `unresolved_record_store` inside
`_pvalue_family_collection_unresolved` (`dataflow_v3_3.py:12484`, returning at `12515`, propagated
at `12529`): the store target is `results[column]["p_adjusted"]` at `analysis.py:74`.

```python
    for column, p_adjusted in zip(PRIMARY_OUTCOMES, primary_p_adjusted):
        results[column]["p_adjusted"] = float(p_adjusted)
```

`results` is a p-record container. The store is a two-level subscript whose **outer** key is the loop
variable `column`, so `_mt_literal_member(target.value.slice)` is `None` and the nested-store lookup
cannot name the member being written. The guard refuses rather than guess.

**Evidence.**

| Rung | Only change | Direct analyzer | Real pipeline |
|---|---|---|---|
| P5-r0 | sealed source | abstain `pvalue-family-collection-unresolved` | `unsupported`, abstain `pvalue-family-collection-unresolved` |
| P5-r1 | the `zip` loop unrolled to two literal-key stores | abstain `pvalue-family-collection-unresolved` | `unsupported`, abstain `pvalue-family-collection-unresolved` |
| P5-r2 | r1 plus the judging loop unrolled to literal-key stores | abstain `correction-family-lineage-unresolved` | `unsupported`, abstain `correction-family-lineage-unresolved` |

**Second wall (observed).** After P5-r1 the same closure refuses on `record["p_used"]` at
`analysis.py:81`, where `record = results[column]` at line 79. That is a store of a **new field**
through a record alias bound from a non-literal subscript, refused at `dataflow_v3_3.py:12503`
because `("record", "p_used")` is not in `record_stores`.

**Third wall (observed).** P5-r2 clears the collection guard and lands on
`correction-family-lineage-unresolved`. That is the library-subset question: `multipletests(...,
method="holm")` is applied to a two-member primary list carved out of a seven-member authorized
family. It is the same family as the E14 P5 rung and the E16 P5 residual, and it is a policy
question about whether a correction over a declared subset counts as a `strict_subset` correction of
the authorized family.

**Disposition: NARROW TRUE REFUSAL, three walls deep.** No false property is asserted; the family
collection genuinely cannot be reconstructed member by member under the installed literal-member
rule. But the shape is ordinary and the refusal is expensive: a dict of records keyed by outcome
name, written in a loop, is the modal way to hold per-outcome results.

**What a narrow admission would need to prove.** That the outer key expression enumerates a known
closed set of outcome names. The machinery already exists in the 3.4 correction model: `_complete_rows`
builds a row table for a `for` loop over a resolvable sequence, and `_positions_for`
(`correction_model_v3_4.py:3547`) resolves position sets from it. Extending nested-store resolution
to "outer key is a loop target bound by a resolvable outcome-name sequence, inner key literal" would
close the first wall. Closing the second wall needs the alias case, and note the asymmetry with the
round-3 to round-7 closure: rounds 3 to 7 made record-derived bindings *refuse a classification*;
admitting a store through one has to prove the opposite direction and cannot reuse that work. The
third wall stays blocked behind the subset-correction policy ADR either way, so P5 does not become a
catch from the collection delta alone.

**Frozen-lane rule that owns it.** `_pvalue_family_collection_unresolved`
(`dataflow_v3_3.py:12484-12529`), specifically the nested-store branch at `12504-12515` and the
single-level branch at `12502-12503`.

### 2.4 P6 `2d2f5dd68825c378126b`, `authorized-reader-lineage-unavailable`

**First trigger.** Captured at `dataflow_v3_3.py:9822`, `authorized_path not in readers`. The reader
census `_mt_full_scope_reader_census` (`dataflow_v3_3.py:834`) accepts exactly two APIs: single-argument
`pandas.read_csv` (`865`) and `numpy.genfromtxt` with an exact keyword set (`874`). P6 reads with the
standard library:

```python
import csv
...
def read_data(path):
    """Return the rows of the authored data file as a list of dicts."""
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
```

No `csv` reader appears in the grammar at all, so no reader resolves to the authorized path.

**Evidence.**

| Rung | Only change | Direct analyzer | Real pipeline |
|---|---|---|---|
| P6-r0 | sealed source | abstain `authorized-reader-lineage-unavailable` | `unsupported`, abstain `authorized-reader-lineage-unavailable` |
| P6-r1 | `read_data` returns `pd.read_csv(path).to_dict("records")`, rows stay dicts | abstain `helper-free-name-unbound` | not run |
| P6-r2 | `read_data` returns `pd.read_csv(path)`, `group_values` uses `rows.loc[mask, column]` | abstain `unresolved-manual-correction-present` | `unsupported`, abstain `unresolved-manual-correction-present` |
| P6-r3 | r2 plus pandas `mean`/`std` helpers | abstain `unresolved-manual-correction-present` | not run |
| P6-r4 | r3 plus `HAND_CORRECTED` written as a tuple instead of a set literal | **candidate `strict_subset`, N=8, corrected `(0, 3, 4)`** | not run |

**Second wall (observed).** With the reader fixed, the AP recognizer rejects the hand correction with
`gate: single-fold, fold_count: 0, rejected: [{'line': 87, 'factor': 8, 'positions': None, 'form':
'capped-product'}]`. The factor resolves to 8; the *positions* do not. The cause is the selector:

```python
HAND_CORRECTED = {
    "fruit_weight_g",
    "yield_per_palm_kg",
    "total_soluble_solids_brix",
}
...
        if column in HAND_CORRECTED:
            p_used = min(raw_p * N_COMPARISONS, 1.0)
```

`_positions_for` (`correction_model_v3_4.py:3587-3599`) filters the row table by evaluating the
guard test with `_static_bool` per row, and `_static_bool` resolves membership against `sequences`,
which holds list and tuple literals. A `set` literal is not in it, so the per-row truth value is
`None` and the position set refuses. P6-r4 changes only the brace to a parenthesis and the detector
returns the scientifically correct answer: `strict_subset`, family size 8, corrected positions
`(0, 3, 4)`, which are exactly `fruit_weight_g`, `yield_per_palm_kg`, and
`total_soluble_solids_brix`.

**Disposition: NARROW TRUE REFUSAL at the first wall, over-narrow recognizer at the second.** The
reader refusal is honest: with no lineage from the operands to the authorized file, the detector
cannot bound the family, and inventing a lineage would be an accusation-safety change. The second
wall is different in kind. The set-literal gap is a container-type omission with no scientific
content; a set and a tuple of the same three names select the same three positions.

**What a narrow admission would need to prove.** For the reader: that a `csv.reader`/`csv.DictReader`
over a `with open(<path>) as handle:` block yields the same row set as the authorized CSV. The
grammar needs the exact shape (single `open` on a resolvable path formal, text mode, no `restkey`,
no `restval`, no non-default dialect or delimiter, materialized by `list(...)` with no filtering),
plus the existing `_mt23_local_reader_paths` formal-parameter resolution so a helper-wrapped reader
still resolves. For the selector: admit `ast.Set` literals of unique string constants into
`sequences` for `in`/`not in` membership only, keeping every other set operation out.

**Frozen-lane rules that own it.** Reader: `_mt_full_scope_reader_census`
(`dataflow_v3_3.py:834-880`) and the check at `dataflow_v3_3.py:9822`. Selector: `_static_bool` and
the `sequences` mapping consumed by `_positions_for` (`correction_model_v3_4.py:3547-3603`).

## 3. What the two catches share

P1 and P4 look nothing alike on the page. P1 is a module-level script with four unrolled per-outcome
blocks and no functions; P4 puts its family in a helper that returns a list of record dicts and then
prints from a loop. Three properties are common to both and absent from at least one miss each.

1. **Every p-derived control's branch values are bare string literals reaching a print sink.**
   Observed by capturing `_mt_v21_terminal_rendering_if`: on P1 it returns a position and
   `frozenset({'builtin_print'})` for each of the four `if p_N < ALPHA:` statements; on P4 it returns
   `None` on the raw tree and a position plus `builtin_print` for each of the three positions after
   the 3.3 helper-record graph inlines `compare_outcomes` (the captured node shows the
   `__sc_inline_...` renaming). P2 fails exactly here.
2. **String-valued group literals.** P1 uses `GROUP_A = "engineered_structural_soil"`, P4 uses
   `RESTORED = "restored"`. P3 fails exactly here with `LOW_SALT = 2.0`.
3. **A grammar-recognized reader and a directly reconstructable family.** Both call
   `pd.read_csv(<path>)` with one positional argument, and both build the family either by unrolled
   blocks (P1) or by `results.append({...})` with a literal p field (P4), which the collection guard
   resolves. P5 fails on the collection, P6 on the reader.

The load-bearing observation is that both catches are the plain uncorrected-family misstep, and so
are P2 and P3. Three of the four E18 misses are not scientifically harder than the catches. They are
spelled differently: a `.format` call in a verdict string, a float in a group constant, a dict keyed
by outcome name.

## 4. The 3.4 admissions did not move any E18 positive

The custodian re-ran the six positives through pristine archives of four detector states. Every
outcome is identical across all four
(`/Users/alexanderking/dev/random_stuff/e18-tools/e18-recon-across-detectors.txt`).

| Role | 3.3 `73eb49b` | 3.4 r4 `6986809` | 3.4 r5 `54e50be4` | merge `f85d4f45` |
|---|---|---|---|---|
| P1 | applicable, `no_recognized_family_correction`, N=4 | same | same | same |
| P2 | abstain `hierarchical-gatekeeping-present` | same | same | same |
| P3 | abstain `test-operand-lineage-unresolved` | same | same | same |
| P4 | applicable, `no_recognized_family_correction`, N=3 | same | same | same |
| P5 | abstain `pvalue-family-collection-unresolved` | same | same | same |
| P6 | abstain `authorized-reader-lineage-unavailable` | same | same | same |

Two direct measurements confirm why, and sharpen the claim.

**Admission census.** Running each positive through the shipped 3.4 analyzer under
`recording_admissions()` gives `{'cap': 0, 'comprehension': 0, 'enumerate': 0, 'terminal-ifexp': 0}`
for all six, catches included. Not one of the four 3.4 extension slots fires anywhere in E18's
positive set. (`terminal-ifexp` is in any case a specified-and-not-shipped slot; see
`code_csv_multiple_testing_admission_census_v3_4.py:26-27`.)

**Round-3 to round-7 closures.** The closure predicate `_record_collection_alias_unresolved`
returns `False` on P1, P2, P3, P4, and P6, and **`True` on P5**. That firing is not load-bearing:
P5's frozen 3.3 result is already `abstain pvalue-family-collection-unresolved`, which is the exact
reason the closure lands on, and the 3.4 re-analysis of P5 abstains with the same reason on its own
(measured by calling `_reanalyze_with_v34_admissions` directly). So removing the closure would leave
P5's outcome byte-identical. The accurate statement is that the closures changed no E18 outcome, and
that they fired as a predicate on exactly one positive where they could not change anything.

The four misses are therefore 3.3-era abstentions that the whole 3.4 program left untouched. This is
consistent with 3.4's design intent, which was aimed at the two E17 misses and at the FA routes
Codex demonstrated in rounds 4 to 7, not at these constructs.

## 5. Ranked candidate MT 3.5 recall deltas

The ranking is by measured yield against the still-open misses, recomputed on the merged detector
rather than on each envelope's sealed reason. Running every E13 to E18 positive through the merged
3.4 analyzer gives retro recall E13 `4/6`, E14 `4/6`, E15 `3/6`, E16 `4/6`, E17 `6/6`, E18 `2/6`,
with twelve misses still open:

| Still-open reason | Cases |
|---|---|
| `unresolved-manual-correction-present` | E13 P6, E14 P6, E15 P3, E16 P6 |
| `test-battery-cardinality-unresolved` | E15 P4, E16 P5 |
| `hierarchical-gatekeeping-present` | E18 P2 |
| `test-operand-lineage-unresolved` | E18 P3 |
| `pvalue-family-collection-unresolved` | E18 P5 |
| `authorized-reader-lineage-unavailable` | E18 P6 |
| `record-family-mutation-unresolved` | E15 P5 |
| `extra-registered-test-outside-authorized-family` | E13 P2 |
| `unresolved-decision-threshold` | E14 P3 |

1. **Formatted display arms in the terminal-presentation predicates** (P2-shape). Smallest measured
   delta in the list: one predicate, three call sites, and a demonstrated flip to a correct
   `candidate none` N=6 through the real pipeline. Yield today is one case (E18 P2), but loops that
   print `"...".format(ALPHA)` or an f-string verdict are a common idiom and the census in 2.1 shows
   the FA surface across every opened envelope is two negative cases, one of which is outside the
   evidence population. **Expected yield: 1 measured, plus the largest expected forward yield per
   unit of risk.**
2. **Set literals in the AP selector's `sequences`** (P6 second wall). One container type added for
   membership tests only, demonstrated to take P6-r3 from abstain to the correct `strict_subset` N=8
   corrected `(0, 3, 4)`. It does not by itself catch E18 P6, which is fronted by the reader wall,
   so it pairs with delta 3. **Expected yield: 0 alone, 1 when paired with delta 3.**
3. **Standard-library `csv` reader lineage** (P6 first wall). This is the same reason that cost E13
   P5 and E13 P6 at seal time; E13 P5 is now caught and E13 P6 has moved on to the manual-correction
   wall, so the current measured yield is E18 P6 alone and only in combination with delta 2. It is
   the largest of the four E18 deltas in
   implementation size because the reader grammar is upstream of everything. **Expected yield: 1 when
   paired with delta 2.**
4. **Numeric group-selector literals in `_mask`** (P3 first wall). Demonstrated to clear the first
   wall, but P3 then stops at `hierarchical-gatekeeping-present` on a presentation loop, so it does
   not become a catch without a fifth delta (a terminal-position proof for loops whose body binds a
   local before rendering, which is the E16 recon's item 1 in its loop form). **Expected yield: 0
   alone, 1 when paired with a loop terminal-position proof.**
5. **Nested and alias record stores in the collection guard** (P5 walls one and two). Two deltas of
   real size, and P5 still stops at `correction-family-lineage-unresolved` afterwards, which is a
   policy question and not an implementation one. **Expected yield: 0 without the subset-correction
   ADR.**
6. **The manual-correction family that 3.4 did not reach** (E13 P6, E14 P6, E15 P3, E16 P6). This is
   the largest single bucket of still-open misses, four cases. It is ranked last here only because
   E18 supplies no evidence about three of them: the AP model reports `fold_count: 0, rejected: []`
   for E13 P6, E14 P6, and E15 P3, meaning no candidate fold is recognized at all, and E16 P6 reports
   `rejected: [{'line': 84, 'factor': 5, 'positions': None, 'form': 'bare-product'}]`, whose loop
   iterates the record collection (`for r in results:`) rather than the outcome table, so no row
   table can be built. **Inferred, needs its own first-trigger recon before any build:** these four
   are probably two or three distinct deltas, not one.

## 6. Does E18 repeat the open items from E16 and E17?

There is no standalone E17 recon document. The E17 miss analysis lives in
`docs/implementation/MULTITEST-3.4-COMPREHENSION-ITERATOR-DESIGN-2026-08-31.md` section 0.1, which
attributed E17 P3 to the hierarchy guard on a verdict `IfExp` and E17 P6 to `_complete_rows`
requiring `isinstance(loop.iter, ast.Name)` plus a competing cap fold. Both are closed: on the
merged detector E17 scores `6/6` retro.

Against the E16 recon's four delta candidates:

| E16 recon item | State on the merged 3.4 detector | Does E18 repeat it? |
|---|---|---|
| 1. Terminal-presentation proof for the hierarchy guard (P2/P4-shape loops with summary counts) | E16 P2 and P4 are now caught | **Partly.** E18 P2 is the same guard and the same scientific shape, but a different first trigger: the arms are formatted strings, not a summary count. E18 P3's second wall is the loop form of the same item. |
| 2. Helper-returns-record consumer proof (E16 P3-shape) | E16 P3 is now caught; E18 P4 is caught through exactly this route (the helper-record graph inlines `compare_outcomes`) | **No, it is working.** |
| 3. Library-subset cardinality (E16 P5-shape), pending a policy ADR | E16 P5 still abstains `test-battery-cardinality-unresolved` | **Yes.** E18 P5's third wall is the same question in its `correction-family-lineage-unresolved` form: Holm over 2 declared primaries inside a 7-member authorized family. |
| 4. Name-set-selected partial hand correction (E16 P6-shape) | E16 P6 still abstains `unresolved-manual-correction-present` | **Yes, and E18 P6 is a near-twin**, hand Bonferroni with a cap on a name-selected subset. E18 P6 adds two new specifics: it is fronted by the stdlib reader wall, and its selector is a `set` literal, which is a one-line gap the E16 case does not have. |

So E18 repeats E16's items 3 and 4, supplies a sharper variant of item 1, and confirms item 2 is
closed.

## 7. Scoring context

Window E17 + E18 = `4/6 + 2/6 = 6/12`; the promotion threshold of `7/12` was not reached. Hard stops
all held: `0/9` accusation candidates, `0` Findings in 30 bundles, replay `15/15`, and `0` FA across
all 135 available class-specific blind cases. N1 resolved `covered/complete` 5/5 on a role-map
negative, so the clearance is true and the zero-false-clearance record stands. The blind reviewer
again flagged `6/6` positives as MISSTEP with 1 FA (N6), which is the fourth consecutive envelope
with the same asymmetry: full human recall with one false accusation against partial detector recall
with none.
