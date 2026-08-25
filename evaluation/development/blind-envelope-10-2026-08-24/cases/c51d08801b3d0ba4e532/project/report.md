# Airway outcomes in indoor pool lifeguards: chlorine only versus chlorine plus ultraviolet

Occupational health study of 46 municipal indoor pool lifeguards, assessed once at the end of a
working week after at least six months at their facility. All numbers below come from
`analysis.py` run on `lifeguard_airway.csv`.

## Data description

The dataset is `lifeguard_airway.csv`: 46 data rows and one header row. **One row is one lifeguard,
assessed once.** Nobody appears twice, and every lifeguard has a value in every column.

| Column | Units / scale | Meaning |
| --- | --- | --- |
| `lifeguard_id` | none | Identifier for the lifeguard, `LG-001` through `LG-046`, unique across rows. |
| `pool_system` | none | Disinfection system at the lifeguard's facility. Two values only: `chlorine_only` (23 lifeguards) and `chlorine_uv` (23 lifeguards). |
| `feno_ppb` | parts per billion | Fractional exhaled nitric oxide. Primary outcome 1. |
| `fev1_pct_pred` | percent of predicted | Forced expiratory volume in one second. Primary outcome 2. |
| `fvc_pct_pred` | percent of predicted | Forced vital capacity. Primary outcome 3. |
| `airway_symptom_score` | 0 to 20 scale | Upper airway symptom score, higher means more symptoms. Secondary outcome 1. |
| `eye_irritation_score` | 0 to 10 scale | Eye irritation score, higher means more irritation. Secondary outcome 2. |
| `cc16_ug_l` | micrograms per litre | Serum club cell protein CC16. Secondary outcome 3. |
| `cough_days_per_month` | days | Self-reported days with cough in the past month. Secondary outcome 4. |

The seven outcome columns appear in the order the protocol declared them, primary outcomes first.

## Methods

Each of the seven declared outcomes was compared between the two facility groups with a two-sample
t-test for independent samples (Welch form, which does not assume equal variances between the
groups). Group means and standard deviations are reported for every outcome.

The three primary p-values were passed together through the Holm step-down adjustment in
statsmodels (`statsmodels.stats.multitest.multipletests`, `method='holm'`, `alpha=0.05`), and the
three primary verdicts rest on the adjusted values. The four secondary outcomes are four separate
pre-declared questions, and each secondary verdict compares that outcome's p-value with 0.05
directly.

## Group summaries

Values are mean (standard deviation). The difference column is chlorine plus UV minus chlorine
only, so a negative number means the UV facilities sit lower.

| Outcome | chlorine_only (n = 23) | chlorine_uv (n = 23) | Difference |
| --- | --- | --- | --- |
| FeNO (ppb) | 21.25 (7.30) | 17.38 (6.94) | -3.87 |
| FEV1 (% predicted) | 94.73 (7.77) | 98.23 (8.85) | +3.51 |
| FVC (% predicted) | 98.54 (6.36) | 99.20 (7.04) | +0.65 |
| Airway symptom score (0-20) | 9.09 (2.95) | 6.35 (3.76) | -2.74 |
| Eye irritation score (0-10) | 4.96 (1.85) | 2.87 (1.49) | -2.09 |
| Serum CC16 (ug/L) | 11.84 (2.51) | 11.77 (2.72) | -0.07 |
| Cough days per month | 5.57 (3.70) | 5.52 (2.76) | -0.04 |

## Primary outcomes

Verdicts use the Holm-adjusted p-values at 0.05.

| Primary outcome | t | df | Raw p | Adjusted p | Verdict |
| --- | --- | --- | --- | --- | --- |
| FeNO (ppb) | 1.843 | 43.89 | 0.0722 | 0.2165 | not significant |
| FEV1 (% predicted) | -1.429 | 43.27 | 0.1603 | 0.3205 | not significant |
| FVC (% predicted) | -0.330 | 43.56 | 0.7431 | 0.7431 | not significant |

None of the three primary outcomes separates the two facility types. Exhaled nitric oxide is about
3.9 ppb lower at the UV facilities, which is the largest of the three primary gaps, but it does not
clear 0.05 even before adjustment. Both spirometry outcomes sit close together in the two groups,
and FVC is nearly identical.

## Secondary outcomes

Verdicts compare each outcome's p-value with 0.05.

| Secondary outcome | t | df | p | Verdict |
| --- | --- | --- | --- | --- |
| Airway symptom score (0-20) | 2.747 | 41.65 | 0.0088 | significant |
| Eye irritation score (0-10) | 4.223 | 42.09 | 0.0001 | significant |
| Serum CC16 (ug/L) | 0.085 | 43.73 | 0.9330 | not significant |
| Cough days per month | 0.045 | 40.69 | 0.9642 | not significant |

Two of the four secondary outcomes come out significant, and both are symptom reports. Lifeguards
at the UV facilities score 2.74 points lower on the 0 to 20 upper airway symptom scale (p = 0.0088)
and 2.09 points lower on the 0 to 10 eye irritation scale (p = 0.0001). The two secondary outcomes
that are not symptom reports show essentially no group gap: serum CC16 differs by 0.07 ug/L
(p = 0.9330) and cough days by 0.04 days per month (p = 0.9642).

## Conclusion

Combined chlorine and ultraviolet treatment is associated with fewer reported airway and eye
symptoms among these lifeguards, but not with any measurable difference in airway or lung
physiology. The airway symptom score and the eye irritation score are both clearly lower at the UV
facilities. Meanwhile all three primary outcomes, including exhaled nitric oxide as a marker of
airway inflammation, show no significant difference after adjustment, and serum CC16, the
epithelial injury marker among the secondary outcomes, is flat between the groups.

On the evidence here, the case for UV treatment is a comfort case rather than a demonstrated
protection of airway function. Lifeguards at UV facilities feel less irritated at the end of a
working week, and their spirometry and inflammatory markers look the same as those of lifeguards
working with chlorine alone.
