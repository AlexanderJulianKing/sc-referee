# Iron plus folic acid versus folic acid alone at 28 weeks of gestation

## Question and design

We wanted to know whether pregnant women who had been taking a daily iron plus
folic acid supplement since their first trimester showed better iron status at 28
weeks than women taking folic acid alone under routine care. Ninety-six women
attending our hospital antenatal clinic were assessed at their 28-week visit: 48
on the combined iron plus folic acid regimen and 48 on folic acid alone. The
supplement regimen is the grouping factor and has exactly two levels. Each woman
gave a single blood draw at that visit, and four laboratory markers were measured
from it. Those four markers were named in the study protocol, in a fixed order,
before any sample went to the laboratory: haemoglobin, serum ferritin, transferrin
saturation, and serum hepcidin. This is an observational comparison of two care
groups at one time point, not a randomised trial, so the results describe how the
two groups differ rather than proving that the supplement caused the difference.

## Data description

The data live in `antenatal_iron_study.csv`. One row is one pregnant woman: her
clinic identifier, the four laboratory results from her single 28-week blood draw,
and the supplement regimen she had been on since the first trimester. Each woman
appears exactly once, there are no repeated measurements, and every cell is filled,
so there are no missing values. The file holds 96 data rows plus a header row.

| Column | Units | What it holds |
| --- | --- | --- |
| `participant_id` | none | Clinic identifier for the woman, `ANC-001` through `ANC-096`, unique across the file. |
| `haemoglobin_g_dl` | grams per decilitre | Haemoglobin concentration at the 28-week draw. |
| `ferritin_ug_l` | micrograms per litre | Serum ferritin at the 28-week draw. |
| `transferrin_saturation_pct` | percent | Transferrin saturation at the 28-week draw. |
| `hepcidin_ng_ml` | nanograms per millilitre | Serum hepcidin at the 28-week draw. |
| `supplement_regimen` | none | The woman's regimen, either `iron_plus_folic_acid` or `folic_acid_only`. Exactly these two values. |

The four outcome columns sit in the file in the order the protocol declares them:
haemoglobin, ferritin, transferrin saturation, hepcidin.

## Per-group summary

Spread is the sample standard deviation.

| Outcome | Regimen | n | Mean | SD |
| --- | --- | ---: | ---: | ---: |
| Haemoglobin (g/dL) | iron plus folic acid | 48 | 11.65 | 0.95 |
| Haemoglobin (g/dL) | folic acid alone | 48 | 11.32 | 0.94 |
| Ferritin (ug/L) | iron plus folic acid | 48 | 32.91 | 9.87 |
| Ferritin (ug/L) | folic acid alone | 48 | 24.94 | 10.32 |
| Transferrin saturation (%) | iron plus folic acid | 48 | 23.93 | 6.32 |
| Transferrin saturation (%) | folic acid alone | 48 | 19.53 | 5.06 |
| Hepcidin (ng/mL) | iron plus folic acid | 48 | 12.71 | 3.71 |
| Hepcidin (ng/mL) | folic acid alone | 48 | 10.88 | 4.31 |

## How we tested, and how we corrected

Each of the four outcomes is a continuous laboratory measurement, so each one was
compared between the two regimens with a Welch two-sample t-test, which is the
ordinary two-group test and does not assume the two groups have the same variance.

All four outcomes were declared together in the protocol as one outcome family, so
we treated them that way in the analysis. Testing four things and then reporting
whichever ones look small would give us four chances to be fooled by ordinary
sampling noise, so the four p-values were held together and corrected in a single
pass, using the Holm step-down method at a family-wise level of 0.05. The
correction was supplied by **pingouin**, a specialist third-party Python statistics
package installed from PyPI; the analysis script calls `pingouin.multicomp`, which
returns both the adjusted p-values and the significance flags for the whole family
at once.

Every conclusion below rests on the adjusted p-value, not the raw one. We report
the raw values for transparency, but no outcome is called significant on the
strength of a raw value.

| Outcome (declared order) | Difference in means | Raw p | Adjusted p | Verdict at family alpha 0.05 |
| --- | ---: | ---: | ---: | --- |
| 1. Haemoglobin (g/dL) | +0.33 | 0.0918 | 0.0918 | not significant |
| 2. Ferritin (ug/L) | +7.97 | 0.0002 | 0.0008 | significant |
| 3. Transferrin saturation (%) | +4.40 | 0.0003 | 0.0009 | significant |
| 4. Hepcidin (ng/mL) | +1.83 | 0.0281 | 0.0562 | not significant |

Difference in means is the iron plus folic acid mean minus the folic acid alone
mean, so a positive number means the combined regimen sat higher.

## Conclusions, in the declared order

1. **Haemoglobin.** Women on iron plus folic acid averaged 0.33 g/dL higher, but
   after the family correction the adjusted p-value is 0.0918, above the 0.05
   family level. We do not claim a difference in haemoglobin between the two
   regimens. The gap is small next to the roughly 0.95 g/dL spread within each
   group.

2. **Ferritin.** Women on iron plus folic acid averaged 32.91 ug/L against 24.94
   ug/L on folic acid alone, a difference of about 8 ug/L. The adjusted p-value is
   0.0008, so this difference holds up after correcting the whole family. This is
   the clearest separation of the four markers, which fits ferritin being the store
   marker most directly moved by supplemental iron.

3. **Transferrin saturation.** Women on iron plus folic acid averaged 23.93 percent
   against 19.53 percent, a difference of about 4.4 percentage points, with an
   adjusted p-value of 0.0009. This difference also holds up after correction, and
   it points the same way as the ferritin result.

4. **Hepcidin.** Women on iron plus folic acid averaged 1.83 ng/mL higher. Its raw
   p-value is 0.0281, which would look convincing on its own, but hepcidin was
   declared as part of a four-outcome family, and the correction moves it to 0.0562,
   just above the 0.05 family level. We therefore do not claim a difference in
   hepcidin. This is the one outcome where reading the unadjusted number would have
   changed the answer. The direction is consistent with the iron store findings, so
   it is worth carrying into a larger study rather than treating as settled either
   way.

Taken together, the two markers that reflect iron stores and iron transport,
ferritin and transferrin saturation, separated the two regimens clearly.
Circulating haemoglobin and hepcidin did not separate them at the family level in
this sample. Because the groups were not randomised, women already at higher risk
of anaemia may have been more likely to be put on iron, which would work against
the differences we saw; a randomised comparison would be needed to settle the
causal question.
