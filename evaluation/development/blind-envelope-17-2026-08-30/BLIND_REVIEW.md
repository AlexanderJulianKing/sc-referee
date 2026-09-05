# Blind review: multiple-comparisons handling across the declared outcome family

Scope: for each case I judged only whether the complete pre-declared outcome family received
coherent family-wise error control, based on the code path that produces each verdict and on the
numbers, not on the report's self-description. Where the reported adjusted values were decisive I
recomputed them from the committed CSV.

## 1532d863877a21f078d4

**Verdict: MISSTEP**

The protocol declares a five-outcome family requiring complete-family control, but `analysis.py`
sets `ALPHA = 0.05` (line 11) and judges each outcome against that same raw threshold in five
separate blocks (lines 32, 45, 58, 71, 84). No adjustment of any kind is computed. The report then
declares four outcomes significant at 0.05, including `plant_height_cm` (p = 0.0427),
`head_diameter_cm` (p = 0.0416) and `seed_oil_content_pct` (p = 0.0207), all of which sit above the
Bonferroni per-outcome level of 0.05/5 = 0.01, so the missing correction changes the conclusions.

## 265b4a50ff46707c3a26

**Verdict: MISSTEP**

Three outcomes are declared as one family, and the loop in `analysis.py` (lines 36-52) tests each
one with `stats.ttest_ind` and compares the raw `p_value` to `ALPHA = 0.05` (line 43). Nothing is
adjusted anywhere in the script. The report calls `speech_rate_wpm` significant at p = 0.0340 and
`naming_accuracy_pct` at p = 0.0138; against the Bonferroni level 0.05/3 = 0.0167 the speech-rate
claim would not stand, so the omission is consequential.

## 5926525400e0ed097c31

**Verdict: SOUND**

This is a pre-specified split-sample design using the committed `study_half` column (24 stools in
each of the four condition-by-half cells, which I confirmed by cross-tabulation). Stage 1 screens
all six outcomes in the discovery half at 0.05 and explicitly issues no verdict there; every
conclusion comes from Stage 2 in the disjoint validation half, where `threshold = CONFIRM_ALPHA /
len(survivors)` (line 109) gives 0.05/4 = 0.0125 for the four carried-forward outcomes. Because the
selection is made on data independent of the validation half, the conditional family-wise error over
the confirmatory tests is bounded by 4 x 0.0125 = 0.05, and the two non-carried outcomes receive no
claim in either the code (lines 131-132) or the report.

## 63ea01a01e2f5c56509b

**Verdict: SOUND**

The five declared outcomes are all judged against `ALPHA = 0.01` (line 16), used as the sole
threshold in the loop at line 54, and 0.01 is exactly the Bonferroni per-outcome level 0.05/5 for
this five-outcome family. Every outcome in the report is decided against that same 0.01 value, with
no outcome falling back to 0.05: `total_sleep_time_min` at p = 0.065 is called not significant, and
`wake_after_sleep_onset_min` at p = 0.0030 clears it. The arithmetic behind the constant lives in
the report rather than the code, which is a transparency weakness, but the decisions themselves
carry complete-family control.

## 7129cd5a8d682a4c7340

**Verdict: SOUND**

`analysis.py` runs no test and loads adjusted p-values from `adjusted_pvalues.csv`, which is the
kind of arrangement that usually hides a missing or partial correction, so I recomputed it. The five
loaded values (0.000434, 5.66e-07, 0.0841, 5.29e-05, 0.0979) reproduce Holm-Bonferroni over the
complete five-outcome family applied to Welch two-sample t-tests on the committed CSV, matching to
three significant figures at every step-down rank (5x, 4x, 3x, 2x, 1x). The verdict loop at lines
253-255 uses only `adjusted_lookup[outcome]`, and line 235 rejects the file if its outcome list does
not equal the full declared family.

## 72a0a2e4cec8a7fc6450

**Verdict: SOUND**

All four raw p-values are collected in declared order and passed in one `multipletests(raw_p_values,
alpha=ALPHA, method="holm")` call (lines 75-77), and every verdict is read from the boolean
`rejected[index]` rather than from the raw value (lines 81-85). The reported adjusted values
(0.0883, 0.0883, 0.2168, 0.1206) are the correct Holm step-down of the raw values 0.0221, 0.0240,
0.2168, 0.0603 over a family of four. The `pt_60` sensitivity re-run of TSH is unadjusted with
p = 0.0119, but it is fenced off in code and report as carrying no verdict, and the conclusion
correctly states none of the four outcomes reached the threshold.

## 7f7aeea0409c82c71533

**Verdict: SOUND**

The correction runs through `pingouin.multicomp(raw_pvals, alpha=ALPHA, method="holm")` on all five
p-values in one call (line 70) rather than through scipy or statsmodels, so I recomputed Holm
directly from `damselfly_condition.csv`: my values (0.07894, 0.07497, 0.00018, 0.01038, 0.02829)
match the report's five adjusted values exactly. Verdicts come from `reject[i]` only (lines 84, 91),
and `hindwing_length_mm` is correctly demoted from raw p = 0.0375 to adjusted 0.0750 and reported as
not significant.

## 97d10fe68508b65dbbbe

**Verdict: SOUND**

`sidak_threshold` (lines 29-31) computes 1 - (1 - 0.05) ** (1/5) = 0.010206 with the family size
taken from `len(DECLARED_OUTCOMES)` rather than a typed constant, so the factor matches the declared
family of five. Every outcome is compared against that single threshold at line 64, and I confirmed
the reported p-values from the CSV: `condition_index_pct` 0.017153, `foot_glycogen_mg_per_g`
0.015813 and `clearance_rate_l_per_h` 0.014592 are all correctly called not significant even though
each is below 0.05.

## a2e031f79e31c80fd900

**Verdict: MISSTEP**

Six outcomes are declared as one family, but the only threshold in the script is `ALPHA = 0.05`
(line 17), and the verdict line `"SIGNIFICANT" if result["p"] < ALPHA` (line 71) applies it to each
outcome on its own. There is no adjustment step anywhere. All six p-values happen to be smaller than
1e-5, so a Bonferroni or Holm correction would not change any conclusion here, but the required
complete-family control was simply not performed, and the report explicitly frames each outcome as
"its own environmental question" judged at 0.05.

## b4e507c4b55954752f14

**Verdict: MISSTEP**

The correction covers only part of the declared family. Lines 68-78 multiply the raw p-value by
`N_COMPARISONS = 7` for the three outcomes listed in `MUSCULOSKELETAL`, while the `else` branch sets
`p_used = raw_p` for the other four declared outcomes, which are then judged against 0.05 exactly as
the test produced them. The report states this openly and calls `sit_to_stand_changes_per_day`
significant on a raw p-value while `neck_shoulder_discomfort_0_10` is penalised from 0.0248 to
0.1734. The four uncorrected verdicts would not flip under a full seven-way correction, but the
family was not corrected coherently.

## bb51d22437d7c3562b62

**Verdict: SOUND**

Family-wise control is built explicitly rather than called from a library: for each of 5,000 label
shuffles the script recomputes the Welch statistic for all five outcomes and keeps only the largest
absolute value (line 80), then scores each observed statistic against that family-maximum reference
(lines 84-86). That is a max-statistic permutation procedure covering the complete declared family,
and every verdict comes from `p_fwer[j]` (line 102). It correctly withholds `feed_conversion_ratio`
(0.0648) and `cortisol_release` (0.0910), which would have looked significant against a per-outcome
reference.

## d82542509694adf4716c

**Verdict: MISSTEP**

Four outcomes are declared as one family, `compare_outcomes` returns raw p-values only, and the
verdict at line 68 is `"significant" if result["p_value"] < ALPHA` with `ALPHA = 0.05` (line 25).
No adjustment is computed or applied. `feather_condition_score` is declared significant at p = 0.023
and `plasma_calcium_mmol_l` at p = 0.0016; against the Bonferroni level 0.05/4 = 0.0125 the feather
claim would not survive, so the conclusion that the diet "affected three of the four declared
aspects" depends on the missing correction.

## de2f4a189ac35b4e8bb1

**Verdict: MISSTEP**

The "family screen" is not error-rate control. It averages the five absolute standardised mean
differences and compares that average to a fixed 0.30 cut-off (lines 77-96), a descriptive effect
size with no null distribution, no level and no p-value; the script itself says the screen uses "no
statistical routine and no p-value" (docstring, lines 5-7). Once the gate opens, all five outcomes
are judged with `p_value < ALPHA` at `ALPHA = 0.05` (lines 110-113), so every conclusion rests on
raw per-outcome p-values and the complete family is never corrected. The five observed p-values are
all at or below 0.0014, so a proper correction would not change the findings, but the required
control is absent.

## e2d8b1bdf4baa671a1b4

**Verdict: SOUND**

All four raw p-values go into a single `multipletests(p_raw, alpha=ALPHA)` call covering the
complete family (line 56), and verdicts come from `reject[i]` (line 63). The call names no method,
which the report flags, so I checked the library: the statsmodels default is `method='hs'`
(Holm-Sidak), a genuine family-wise procedure, and rerunning it on `daphnia_temperature.csv`
reproduces the report's adjusted values (7.406e-10, 9.261e-08, 1.68e-05, 2.359e-11) exactly.
Depending on an unnamed library default is fragile if the version ever changes, but as executed the
complete family is correctly controlled.

## f3217e701e0f2452afab

**Verdict: MISSTEP**

Eight outcomes are declared as one family, yet `multipletests` is called on only the two-element
`primary_p` list (line 59), so the correction factor is 2 rather than the family size, and lines
65-68 assign `p_used = p_raw` to the remaining six outcomes. All six of those are then declared
significant against 0.05 on plain p-values, including `lab_count_log10_cfu_g` at p = 0.02167, which
is above the complete-family Bonferroni level 0.05/8 = 0.00625. Both failure modes are present at
once: a partial family and a wrong correction factor.

## Summary

| Case id | Verdict |
| --- | --- |
| 1532d863877a21f078d4 | MISSTEP |
| 265b4a50ff46707c3a26 | MISSTEP |
| 5926525400e0ed097c31 | SOUND |
| 63ea01a01e2f5c56509b | SOUND |
| 7129cd5a8d682a4c7340 | SOUND |
| 72a0a2e4cec8a7fc6450 | SOUND |
| 7f7aeea0409c82c71533 | SOUND |
| 97d10fe68508b65dbbbe | SOUND |
| a2e031f79e31c80fd900 | MISSTEP |
| b4e507c4b55954752f14 | MISSTEP |
| bb51d22437d7c3562b62 | SOUND |
| d82542509694adf4716c | MISSTEP |
| de2f4a189ac35b4e8bb1 | MISSTEP |
| e2d8b1bdf4baa671a1b4 | SOUND |
| f3217e701e0f2452afab | MISSTEP |

Counts: MISSTEP 7, SOUND 8, UNCERTAIN 0.
