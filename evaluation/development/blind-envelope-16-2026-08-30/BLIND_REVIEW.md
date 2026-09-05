# Blind review: multiple-comparisons handling across the declared outcome family

Scope of this review: for each case, whether the complete pre-declared outcome family named in
`PROTOCOL.md` received coherent family-wise error control, judged from `analysis.py` and the
numbers it produces. Each script was executed in its own project directory to obtain the actual
p-values; where a case applies no correction or a partial one, a full-family Holm adjustment was
computed as a reference to see which verdicts depend on the missing correction. Nothing outside the
fifteen `cases/<id>/project/` directories was read.

---

## 298a1432b9b550031f5d

**Verdict: SOUND**

The six declared outcomes are screened in the discovery eels at raw 0.05 (`analysis.py` line 94),
and only the three survivors are re-tested in the validation eels against `0.05 / len(survivors)` =
0.016667 (lines 119, 133). Correcting by 3 instead of 6 is legitimate here because the two stages
are disjoint sets of animals: the CSV holds 80 unique `eel_id` values with a pre-assigned `stage`
column, 20 impacted and 20 reference in each stage, so the validation p-values are independent of
the screen that selected them, and Bonferroni within the selected set controls the family-wise
error conditionally and therefore overall. The discovery screen makes no claim, and the report
holds to that: `fulton_k`, `hsi_pct` and `lipid_pct` get no verdict at all, and all three confirmed
outcomes (validation p = 2.9e-05, 1.5e-05, 6.3e-06) clear 0.016667 by a wide margin.

## 5a9c5b4377c33916d672

**Verdict: MISSTEP**

No correction of any kind is applied. `ALPHA = 0.05` (line 15) is compared with each raw p-value
one outcome at a time (`"significant": bool(p_value < ALPHA)`, line 40), across all five declared
outcomes, and the report's verdict column is that raw comparison. The protocol requires
complete-family control of the family-wise error and none exists; the two "not significant" calls
(p = 0.271, 0.400) and three "significant" calls all rest on uncorrected p-values. The three
significant outcomes are extreme enough (3.7e-13 to 1.1e-09) that Holm would not overturn them, but
the required control is simply absent.

## 6c45fce29073c572d8c0

**Verdict: SOUND**

All five declared raw p-values are collected in one list and passed to `pg.multicomp(raw_p,
alpha=0.05, method="holm")` in a single call (line 53), so the correction factor matches the full
declared family of five. Every printed verdict reads `reject[i]` from that call (line 69), not the
raw p-value. The numbers confirm it: `moult_count` raw 0.24934 / adjusted 0.31329 and
`haemolymph_protein_g_l` raw 0.15664 / adjusted 0.31329 are both called not significant, and the
three significant calls (adjusted 0.00620, 0.00243, 0.00218) are all below 0.05 after adjustment.

## 6d5e78b815b73081865f

**Verdict: MISSTEP**

The only multiplicity device is a family-level "screen" that averages the four absolute
standardised mean differences and compares the average with a fixed 0.35 (lines 80-94, 121). That
quantity is not a test and has no calibrated error rate, so passing it licenses nothing; once it
passes, each of the four outcomes is judged against raw `ALPHA = 0.05` (line 158) with no
adjustment. The single positive claim depends on this: `tethered_force_n` has raw p = 0.0297 and a
full-family Holm value of 0.1188, so the report's "the one difference that reached significance"
does not survive correction of the declared family of four.

## 76f0e7831f3856df66d5

**Verdict: SOUND**

All five declared raw p-values go to `multipletests(raw_p, alpha=ALPHA)` in one call (line 52), so
the correction covers the complete family; the routine's default method in statsmodels 0.14.1 is
`'hs'` (Holm-Sidak), a step-down family-wise procedure, and the printed values match it exactly
(e.g. raw 0.0162 gives adjusted 1 - (1 - 0.0162)^4 = 0.0634). Verdicts are taken from `reject[i]`
(line 61), never from `raw_p`. The correction is load-bearing and honoured: `stem_density_spm`
(0.0162) and `plant_richness_spp` (0.0173) are both below raw 0.05 yet reported as not significant
at adjusted 0.0634, and only `berry_mass_gpm` (adjusted 5.06e-07) is claimed.

## 7a43fa7b50f1b99e5034

**Verdict: MISSTEP**

Six declared outcomes, one t-test each, and `significant = p_value < ALPHA` with `ALPHA = 0.05`
(lines 14, 53); no correction appears anywhere in the script. Two of the three "significant"
verdicts collapse under a complete-family correction: `body_weight_g` raw 0.0146 and
`feed_intake_g_d` raw 0.0158 both become Holm 0.073, leaving only `footpad_score_pts` (raw 8.6e-05,
Holm 0.000516). The report's practical recommendation for straw litter cites the growth results as
established, so the missing correction changes what the study claims.

## 7be23db36040f5be1df2

**Verdict: MISSTEP**

The declared family is six outcomes, but Holm is applied to the two primaries only
(`multipletests(primary_p, ...)`, line 63), and the four secondaries are decided as
`results[col]["p_raw"] < ALPHA` (line 70). That is both a wrong correction factor and a partial
correction with raw-p conclusions elsewhere. It is decision-relevant: `opening_d2_mm` has raw p =
0.0127 and is called SIGNIFICANT at a two-outcome Holm value of 0.0127, whereas Holm over the
declared six gives 0.0635. The report carries that claim into its clinical recommendation ("both
survive the adjustment").

## 8b9b2171434ddd20b63f

**Verdict: SOUND**

The correction is a hand-written max-statistic permutation over the whole family: each of 4000
shuffles permutes the landscape labels across all 64 rows at once, recomputes the Welch t for all
five outcomes, and keeps only `np.max(np.abs(shuffled_t))` (lines 102-105). Each observed statistic
is compared with that single family-maximum reference using the standard `(1 + count) / (1 + N)`
convention (line 114), which is the correct construction for family-wise control and preserves the
correlation between outcomes. No unadjusted per-outcome p-value is computed anywhere, and the
correction bites: `haemoglobin_g_dl` has Welch t = 2.1751 against a 95th-percentile family maximum
of 2.6222 and is reported not significant (fwer_p = 0.14796).

## 8ff6de728df8f29261aa

**Verdict: MISSTEP**

Only two of the five declared outcomes are corrected. `oil_content_g100g` and `acrylamide_ug_kg`
get a hand Bonferroni of x5 (lines 84-86), while `breaking_force_n`, `colour_b_cielab` and
`crispness_score_pts` fall through to `p_used = r["p_raw"]` and are judged against 0.05 (lines
102-106). The decision rule is therefore not family-wise: a quality outcome at, say, p = 0.03 would
have been declared a difference. No verdict happens to flip here (the three raw values are 0.849,
0.161, 0.123 and the two corrected are ~1e-12), but the declared family was not corrected coherently.

## 9155ca1dd76fa5c630b1

**Verdict: SOUND**

`analysis.py` computes no tests and reads every verdict from the `p_adj` column of
`upstream_inference.csv` at 0.05 (line 195). That inherited table checks out against the raw file:
its `p_raw` values reproduce the Welch t-test p-values from `millet_irrigation.csv` to six figures
(e.g. `leaf_rwc_pct` 1.19167e-11, `thousand_grain_mass_g` 0.230236), and `p_adj` is exactly Holm
over all six with multipliers 6, 5, 4, 3, 2, 1 in rank order (1.19167e-11 x 6 = 7.15004e-11;
0.000654584 x 2 = 0.00130917; largest unchanged at 0.230236). The correction covers the complete
declared family and drives the one negative call, `thousand_grain_mass_g`.

## 9ced761b41ef93485acf

**Verdict: MISSTEP**

Seven declared outcomes, each tested and decided against `ALPHA = 0.05` on its own (lines 17, 82,
96); the docstring states each outcome is "decided at the conventional 0.05 threshold on its own
merits" and no correction is computed. `pod_no` is claimed as a significant benefit of inoculation
at raw p = 0.0387, which becomes Holm 0.0774 over the declared seven, so a reported finding is
created by the missing correction. `root_dw_g` (raw 0.005155, Holm 0.015465) survives, but the
family-wise standard the protocol requires was never applied.

## a5a32dcc59d4f3acd943

**Verdict: SOUND**

The script performs no adjustment arithmetic itself, but it decides all five declared outcomes
against a single constant `ALPHA = 0.01` (lines 18, 63), and 0.01 is exactly the Bonferroni
per-comparison level for the declared family of five at a family-wise 0.05 (0.05 / 5). Applying one
corrected threshold uniformly to the complete family is operationally equivalent to Bonferroni-
adjusting every p-value, so the family-wise rate is controlled and no outcome is judged at a
different standard. The numbers are consistent with that: the two claims (p = 0.001805, 0.001314)
are below 0.01, and nothing in the 0.01-to-0.05 band is claimed.

## b1b81b953f324b7e4f75

**Verdict: SOUND**

All five declared raw p-values are adjusted in one `multipletests(raw_p, alpha=0.05,
method="holm")` call (line 72) and every verdict reads `reject` from it (lines 73-75, 84). The
adjustment matters and is respected: `itch_pts` moves from raw 0.0133 to adjusted 0.0400 (still
significant) while `sleep_nights` and `steroid_g` are reported not significant at 0.4852. The
`tewl_gm2h` sensitivity re-run with the 62.4 outlier dropped produces raw p = 0.0003, but it is
kept out of the family, printed with `adj p` as `n/a`, and explicitly not used for any verdict
(lines 117-126); the report likewise keeps the water-loss conclusion at the Holm-adjusted 0.0193.

## c89a2a4259f96b413be8

**Verdict: MISSTEP**

The four declared outcomes are tested in four separate hand-written steps and each is judged by
`verdict(p)` against `ALPHA = 0.05` (lines 16, 29-30); no correction is computed. The FEV1 claim
depends on that omission: `fev1_drop_ml` raw p = 0.0301 is reported SIGNIFICANT, but Holm over the
declared four gives 0.0903. Only `dust_mg_m3` (raw 2.489e-06, Holm 9.956e-06) would survive, so the
report's statement that both dust and cross-shift FEV1 loss "reached significance" is not supported
once the family is corrected.

## f0214d4b77f589655ac3

**Verdict: SOUND**

The per-comparison threshold is computed explicitly as Sidak over the full declared family,
`1 - (1 - 0.05) ** (1 / 5)` = 0.010206, with `FAMILY_SIZE = 5` asserted equal to `len(OUTCOMES)`
(lines 29-33), and every one of the five outcomes is compared with that same threshold rather than
0.05 (line 65). The correction factor matches the declared family and the threshold is actually
used in each verdict. It is also load-bearing in the right direction: the three claims sit at
3.3e-07, 5.1e-06 and 0.001163, all clearly below 0.010206, and nothing between 0.010206 and 0.05 is
claimed.

---

## Summary

| Case id | Verdict |
| --- | --- |
| 298a1432b9b550031f5d | SOUND |
| 5a9c5b4377c33916d672 | MISSTEP |
| 6c45fce29073c572d8c0 | SOUND |
| 6d5e78b815b73081865f | MISSTEP |
| 76f0e7831f3856df66d5 | SOUND |
| 7a43fa7b50f1b99e5034 | MISSTEP |
| 7be23db36040f5be1df2 | MISSTEP |
| 8b9b2171434ddd20b63f | SOUND |
| 8ff6de728df8f29261aa | MISSTEP |
| 9155ca1dd76fa5c630b1 | SOUND |
| 9ced761b41ef93485acf | MISSTEP |
| a5a32dcc59d4f3acd943 | SOUND |
| b1b81b953f324b7e4f75 | SOUND |
| c89a2a4259f96b413be8 | MISSTEP |
| f0214d4b77f589655ac3 | SOUND |

Counts: SOUND 8, MISSTEP 7, UNCERTAIN 0.
