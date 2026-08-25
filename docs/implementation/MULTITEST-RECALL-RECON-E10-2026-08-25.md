# Multiple-testing recall recon after envelope 10 (2026-08-25)

Provenance: isolated Opus recon over the OPENED envelope-10 corpus (scored, committed 4987b47)
plus the detector source at that commit. Every diagnosis below was confirmed by running the
analyzer in-process and by single-variable mutation from a known-candidate baseline. Mutation
fixtures: `evaluation/development/multitest-recall-recon-e10/` (harness.py reproduces the recorded
15/15 reasons; each PROBE_*.py differs from a candidate baseline by one construct). The zero-FA
standard governs every proposal: admissions are narrowings with per-idiom FA analyses; nothing
loosens a correction guard.

## 0. The recorded diagnosis named the wrong function

AUDIT_RESULTS.json originally attributed the dominant reason to "the module-level binder". Wrong:
`_resolver` and `_definition_shadows_builtin` pass on all 15 files. 12/15 fail `_chosen_scope`
(:5973) with `analysis-scope-ambiguous`, which `analyze_code_csv_multiple_testing_dataflow`
RELABELS to `api-resolution-ambiguous` at :7288-7296 for any scope reason outside
`_MT_HELPER_REASONS`. Delta-1.1 item: give it a distinct honest closed reason
(e.g. `module-setup-statement-unsupported`); the mislabel is what misdirected the first diagnosis.
Similarly `float(result.pvalue)` on an uncorrected script abstains
`unresolved-manual-correction-present` via `_off_grammar_transform_guard` - conservative and
correct, but the label misleads (NEGSIM_C).

## 1. Case -> role -> tripping construct -> rule -> proposal

| case | role | first tripping construct | gate + rule | proposal |
|---|---|---|---|---|
| ebbb8a5d | P1 | `with open(DATA_FILE,...)` + `csv.DictReader` | `_v3_full_scope_reader_census` (:736): only `pandas.read_csv(x)` and exact-keyword `numpy.genfromtxt` accepted -> `authorized-reader-lineage-unavailable` | leave as abstention (new value model, not a narrowing) |
| 104493a5 | P2 | `OUTCOME_LABELS = {` dict loaded in main() | `_module_setup_assignment` (:6085) escape refused when name loaded in main -> scope-ambiguous | admit A2 |
| 3ff45fce | P3 | `DECLARED_OUTCOMES = [` (2-tuples) | List branch: `_closed_sequence_elements` (:6173) requires scalar Constants | admit A1 |
| 7296b0e2 | P4 | same (3-tuples) | as P3 | admit A1 |
| c51d0880 | P5 | PRIMARY_/SECONDARY_OUTCOMES tuple lists | as P3 | admit A1 |
| f4cf62ca | P6 | `OUTCOMES = [` 4-tuples; `HEADLINE = [name for name,*_ in OUTCOMES[:3]]` | as P3; comprehension loaded in main | admit A1; leave the derived comprehension as abstention |
| cb2e2072 | N1 | tuple table | as P3 | admit A1 |
| 9be74afb | N2 | tuple table | as P3 | admit A1 |
| b787314c | N3 | tuple table | as P3 | admit A1 |
| 60f96fab | N4 | tuple table | as P3 | admit A1 |
| 8d832104 | N5 | `OUTCOMES: list[tuple[...]] = [` | AnnAssign never matches `_module_setup_assignment` (Assign only) | admit A3 |
| 49079325 | N6 | tuple table | as P3 | admit A1 |
| 6d2fdc67 | N7 | make_data.py `from scipy import stats` -> `statistics-api-imported-outside-analysis-py`; behind it A2 dict + two accepted readers (`additional-accepted-reader-present`) | closed import world (:542) | leave as abstention; FIX THE CUSTODY PROTOCOL: generate data outside the audited project tree so make_data.py never ships in it |
| dfc9f20a | N8 | `for i in range(N_SHUFFLES):` calling helper `welch_t` | `_mt_call_census` (:7530-7545) + `_mt_exact_outcome_factor` None -> `test-battery-cardinality-unresolved` | leave as abstention (resampling loops must not be unrolled) |
| e1bce32a | N9 | tuple table | as P3 | admit A1 |

## 2. Deduplicated idiom list (each flips a candidate baseline to abstention alone)

1. non-flat module outcome table (tuple-list 11, dict 2, AnnAssign 1, comprehension 1) - 13/15 -> scope-ambiguous relabel
2. read_csv path via helper parameter with module-constant default - 11/15 -> authorized-reader-lineage-unavailable
3. `p < ALPHA` named constant - 13/15 -> unresolved-decision-threshold
4. verdict ternary `"significant" if p < a else ...` - 13/15 -> hierarchical-gatekeeping-present
5. `float(p)` / `round(p, 4)` - 9/15 -> unresolved-manual-correction-present
6. boolean-mask group split `df[df[col]==v][outcome]` - 9/15 -> test-operand-lineage-unresolved
7. helper-wrapped per-outcome test - ~8/15 -> test-battery-cardinality-unresolved
8. enumerate()/zip() family loop - 9/15 -> test-battery-cardinality-unresolved
9. `.astype(float)` on operand - 3/15 -> test-operand-lineage-unresolved
10. deferred result collection printed in a later loop - most -> pvalue-family-collection-unresolved

Supported today: `.query("group == 'x'")`, `.loc[mask, col]`, `.values`, `.array`, `equal_var=False`.

## 3. Admissions with FA analyses (summarized; full agent text in this doc's git history)

- A1 nested constant table (outer<=16, inner<=8, scalar Constants only): family proof still requires
  `_mt_exact_outcome_factor` position-0 projection; a table whose tested column differs stops at
  test-operand-lineage-unresolved. Fails closed.
- A2 constant-only dict (<=16) incl. removing the loaded-in-main veto for constant dicts: collision
  checks unchanged; label dicts never touch correction guards.
- A3 AnnAssign with identical value rules: zero new runtime semantics.
- A4 reader path through helper parameter: bind via `_bind_helper_arguments`; require called>=1,
  every call site binds the SAME static path, path == authorized_path. Do NOT copy the dependence
  sibling's tolerance of None (real FA vector).
- A5 named decision threshold: DEMONSTRATED FA VECTOR as naively written (ALPHA reassigned by
  BinOp `ALPHA = ALPHA / len(OUTCOMES)` is silently ignored; hand-Bonferroni could be convicted as
  uncorrected). MANDATORY condition: the name has exactly one binding anywhere in the module
  (Assign, AnnAssign, AugAssign, NamedExpr, for/with targets, same-name helper params all counted).
  Exact Decimal from the constant's source segment; product rule keeps its bite.
- A6 `.astype(<closed dtype>)`: cast cannot change row membership; reuse `_closed_dtype` (:3730).
- A7 boolean-mask split: route to the existing `_mask_rows` proof with its exact clauses (single Eq,
  literal value, row-set equality); combined masks/isin/~mask stay refused.
- Verdict-ternary carve-out (largest recall item, most design care): hierarchy guard must keep
  refusing a p-value that gates another test/output; may admit a p-value that only selects a
  display string.

Structural bound: all admissions sit in FRONT of the correction guards
(`_correction_terminal_census`, `_off_grammar_transform_guard`, `_hierarchy_guard`,
row-completeness), which fail closed on anything correction-shaped they cannot resolve
(NEGSIM_A Holm -> correction-family-lineage-unresolved; NEGSIM_B hand 0.05/5 ->
unresolved-manual-correction-present; neither classifies none).

## 4. Ladder finding: stacked walls

P2 needed 8 single edits to reach a candidate; P3 still abstained after 9. Under A1-A3 alone, and
under the top-3 admissions, recall stays 0/6 and all 9 negatives keep abstaining. A delta that
ships only the table admission will measure 0/6 again. Recall is gated by the DEEPEST wall per
file. Suggested order by recall-per-FA-surface: A5(+condition), A6, A7, ternary carve-out, A4,
then A1-A3 (which mainly buy honest reasons), plus the two relabels and the N7 custody fix.
