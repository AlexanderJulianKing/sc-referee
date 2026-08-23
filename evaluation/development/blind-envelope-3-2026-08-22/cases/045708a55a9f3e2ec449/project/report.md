# Serum cortisol after a four-hour road journey in riding-centre horses

## Data description

The analysis uses one comma-separated file, `cortisol_transport.csv`, holding 60 data rows and one
header row.

**What one row represents.** One row is a single serum cortisol reading taken from the assay plate.
Each horse gave one blood sample, and that sample was read three times on the same plate, so each
horse contributes three rows. The three rows for a horse share the same `horse_id`,
`transport_condition` and `age_years`, and differ in `replicate` and `cortisol_nmol_l`.

| Column | Type | Description |
| --- | --- | --- |
| `horse_id` | text | Identifier of the animal, `H01` through `H20`. Appears three times, once per assay reading of that animal's sample. |
| `transport_condition` | text | Group label, `transported` or `stayed`. Constant within a horse. |
| `replicate` | integer | Which of the three assay readings of that sample the row holds: 1, 2 or 3. Replicate numbers are meaningful only within a horse. |
| `cortisol_nmol_l` | number | Serum cortisol for that reading, in nanomoles per litre, to one decimal place. |
| `age_years` | integer | Age of the horse in whole years at sampling. Constant within a horse. |

## Study setup

Twenty horses kept at a single riding centre were studied. Ten animals (`H01`-`H10`) completed a
four-hour road journey in a standard two-horse trailer and returned to the centre. The remaining ten
animals (`H11`-`H20`) stayed in the home yard over the same period and served as the untransported
comparison group. The horses ranged from 4 to 17 years of age, with a mean age of 11.4 years.

One blood sample was drawn from each horse by jugular venepuncture two hours after the transported
group returned to the centre, so that both groups were sampled at the same clock time and under the
same yard routine.

## Laboratory methods

Blood was collected into plain serum tubes, allowed to clot, and centrifuged; the serum was separated
and held frozen until assay. All samples were assayed together for serum cortisol by competitive
immunoassay on a single plate, which removes any plate-to-plate variation from the comparison.

Each serum sample was assayed in triplicate. Every well was read separately, and each of the three
readings from a sample was recorded as its own row in the data file. All 60 readings were carried
forward to the statistical analysis as individual cortisol observations; no readings were pooled,
averaged or discarded.

## Statistical analysis

Cortisol was compared between the transported and stay-at-home groups with an independent two-sample
t-test, entering every cortisol reading in the table as an individual observation. Descriptive
statistics are means with standard deviations. The 95% confidence interval for the difference in
means and Cohen's d were calculated from the pooled standard deviation. Analyses were run in Python 3
with pandas and SciPy; the script is `analysis.py` at the root of this project.

## Results

A total of **60 cortisol readings** were analysed, 30 from transported horses and 30 from horses that
stayed in the yard.

| Group | n readings | Mean cortisol (nmol/L) | SD | SEM | Range (nmol/L) |
| --- | --- | --- | --- | --- | --- |
| `transported` | 30 | 119.18 | 22.23 | 4.06 | 81.5 to 153.1 |
| `stayed` | 30 | 74.26 | 22.93 | 4.19 | 42.6 to 117.1 |

Transported horses showed a mean serum cortisol 44.93 nmol/L higher than horses that stayed in the
yard (95% CI 33.25 to 56.60 nmol/L). The independent two-sample t-test gave t(58) = 7.705,
**p = 1.9e-10** (p < 0.001). Cohen's d was 1.99, a large effect. The pooled standard deviation was
22.58 nmol/L.

## Conclusion

Road transport raised serum cortisol in these horses. Two hours after a four-hour journey, cortisol
in transported animals was about 45 nmol/L higher than in stablemates that remained in the home yard,
a difference of roughly 60% above the stay-at-home mean and one that reached significance at
p < 0.001. The finding is consistent with an endocrine stress response to trailer transport that is
still detectable two hours after arrival, and it supports attention to journey length and recovery
time in the routine management of horses at this centre.
