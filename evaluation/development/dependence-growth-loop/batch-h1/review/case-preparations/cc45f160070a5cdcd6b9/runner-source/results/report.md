# Trace-element dosing and biogas methane content in pilot anaerobic digesters

## Design and unit of analysis

The file `data/input.csv` is the weekly monitoring log of a pilot digester
trial: 96 rows, one row per digester-week gas reading. Twelve independently
seeded and independently operated digesters (D01-D12) were each monitored for
four weeks on the standard maize-silage feed (phase `baseline`) and then for
four weeks after a cobalt/selenium trace-element supplement was blended into
the same feed (phase `amended`).

The weekly rows are repeated measurements drawn from the same vessel and carry
that vessel's own inoculum, sealing and loading history, so they are not
independent of one another. The digester, not the digester-week, is the
independent unit. Each digester was therefore collapsed to a single paired
contrast (its mean methane content across the amended weeks minus its mean
methane content across the baseline weeks) before any test statistic was
computed, so exactly one analysed value per digester enters the comparison and
n = 12.

## Per-digester summary

| digester | weeks (baseline/amended) | mean CH4 baseline (%) | mean CH4 amended (%) | change (pp) |
| --- | --- | --- | --- | --- |
| D01 | 4/4 | 58.90 | 61.25 | +2.35 |
| D02 | 4/4 | 60.15 | 61.95 | +1.80 |
| D03 | 4/4 | 57.45 | 60.50 | +3.05 |
| D04 | 4/4 | 61.20 | 62.75 | +1.55 |
| D05 | 4/4 | 59.60 | 62.15 | +2.55 |
| D06 | 4/4 | 58.25 | 61.10 | +2.85 |
| D07 | 4/4 | 60.75 | 62.80 | +2.05 |
| D08 | 4/4 | 57.90 | 61.15 | +3.25 |
| D09 | 4/4 | 59.05 | 61.75 | +2.70 |
| D10 | 4/4 | 60.40 | 62.60 | +2.20 |
| D11 | 4/4 | 58.55 | 61.75 | +3.20 |
| D12 | 4/4 | 59.95 | 62.40 | +2.45 |

## Test and result

The 12 per-digester changes were tested against a null median of zero with a
two-sided Wilcoxon signed-rank test evaluated on its exact null distribution;
there are no zero changes and no ties among the absolute changes. The 96
weekly readings were never entered as 96 independent observations.

[selected-result] Two-sided Wilcoxon signed-rank test on one paired change per digester (n = 12 digesters, 96 weekly readings collapsed): W = 0.0, p = 0.000488; biogas methane content rose in all 12 digesters, mean change +2.500 percentage points (median +2.500, range +1.55 to +3.25).

Interpretation: with the digester as the unit of analysis, the trace-element
supplement is associated with a consistent gain of about 2.5 percentage points
in biogas methane content; the effect appeared in every digester monitored.
