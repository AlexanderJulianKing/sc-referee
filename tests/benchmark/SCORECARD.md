# sc-referee validation scorecard

This is a measurement of the shipped `run_audit(folder, engine="simple")` behavior. The benchmark does not execute `analysis.py` and does not modify engine behavior.

## Summary

- **False alarms:** 0 (correct analyses flagged; required: 0)
- **Catches:** 7 (known issue rows flagged)
- **Abstentions:** 2 (`not_checked` rows)
- **Overall correctness:** 12/12 (100.0%)

A `not_flagged` expectation accepts clear, not-applicable, or explicit abstention; it only fails when the engine attributes a concern to a scientifically valid analysis.

## Verdicts

| Scenario | Invariant | Expected | Actual state | Shipped status | Correct? |
|---|---|---:|---:|---:|:---:|
| `double_dip` | `double_dipping` | flagged | flagged | needs_evidence | yes |
| `external_grouping` | `double_dipping` | not_flagged | not_applicable | not_applicable | yes |
| `pseudoreplication` | `experimental_unit` | flagged | flagged | major | yes |
| `pseudoreplication` | `pairing` | flagged | flagged | needs_evidence | yes |
| `proper_pseudobulk` | `pseudobulk_integrity` | clear | clear | pass | yes |
| `confounded_design` | `confounding` | flagged | flagged | blocker | yes |
| `balanced_design` | `confounding` | clear | clear | pass | yes |
| `normalized_only` | `experimental_unit` | not_checked | not_checked | not_audited | yes |
| `orthogonal_axes_splicing` | `double_dipping` | not_flagged | not_checked | not_audited | yes |
| `uncorrected_pvalues` | `multiple_testing` | flagged | flagged | blocker | yes |
| `wrong_count_model` | `count_model` | flagged | flagged | major | yes |
| `merged_pseudobulk_arms` | `pseudobulk_integrity` | flagged | flagged | blocker | yes |

## Findings

- No correct analysis was flagged: false-alarm count is zero.

- Every known issue in this battery was flagged.

### Coverage gaps / intentional abstentions

- `normalized_only` / `experimental_unit`: your matrix looks already normalized, not raw whole-number counts, and re-testing at the sample level needs the raw counts to add cells up per sample — so I did NOT check pseudoreplication. Provide the raw counts in layers['counts'] or raw.X and re-run.
- `orthogonal_axes_splicing` / `double_dipping`: double_dipping did not evaluate results/splicing.csv: the claim's own producing test is mannwhitneyu, outside this detector's covered marker-test family; coverage is NOT_RUN.

## Scenario ground truth

- `double_dip` — Cluster then test the same expression.
  - `double_dipping` → **flagged**: Same-data selection invalidates marker p-values.
- `external_grouping` — External metadata grouping.
  - `double_dipping` → **not_flagged**: Condition was not learned from expression.
- `pseudoreplication` — Cells tested while donors are replicates.
  - `experimental_unit` → **flagged**: Cell-level claims collapse at donor level.
  - `pairing` → **flagged**: The paired-capable donor structure was omitted.
- `proper_pseudobulk` — Proper donor-by-condition pseudobulk.
  - `pseudobulk_integrity` → **clear**: Aggregation preserves both donor and arm.
- `confounded_design` — Condition perfectly aliases batch.
  - `confounding` → **flagged**: The condition coefficient is not estimable.
- `balanced_design` — Condition crossed with batch.
  - `confounding` → **clear**: Both conditions occur in both batches.
- `normalized_only` — Normalized matrix without raw counts.
  - `experimental_unit` → **not_checked**: A raw-count recompute is impossible.
- `orthogonal_axes_splicing` — Magnitude clustering, isoform-ratio test.
  - `double_dipping` → **not_flagged**: The splicing producer is outside marker-test coverage.
- `uncorrected_pvalues` — Uncorrected p-values.
  - `multiple_testing` → **flagged**: Reported discoveries fail BH correction.
- `wrong_count_model` — Gaussian test on donor pseudobulk counts.
  - `count_model` → **flagged**: A t-test is not a count model.
- `merged_pseudobulk_arms` — Aggregation key merges contrast arms.
  - `pseudobulk_integrity` → **flagged**: Donor-only groups mix both conditions.

## Reproduce

```bash
.venv/bin/pytest -q -s tests/benchmark
```

The pytest session creates each self-contained folder under its temporary directory and prints each relevant finding as soon as that scenario finishes.
