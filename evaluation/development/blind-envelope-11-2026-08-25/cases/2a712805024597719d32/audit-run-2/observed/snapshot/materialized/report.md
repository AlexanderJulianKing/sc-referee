# Smoking and five blood biomarkers in 120 healthy donors

## Question and design

I wanted to know which of five protocol-declared blood biomarkers differ between
current daily cigarette smokers and never-smokers among healthy blood donors.
One hundred and twenty donors each gave a single sample at one donation session:
60 current smokers and 60 never-smokers. Smoking status is the two-level
grouping factor.

Before any measurement was made, our study statistician split the cohort into a
discovery half and a validation half, 60 donors each, with the two smoking
groups evenly represented in both halves (30 smokers and 30 never-smokers per
half). That split was fixed in advance and it is recorded in the data file in
its own column, so the analysis reads the assignment rather than choosing it. I
used the discovery half to screen the five outcomes and the validation half to
decide them. Nothing in this report turns on the discovery half.

The five outcomes were declared in the protocol in this order: plasma
C-reactive protein, white blood cell count, plasma fibrinogen, HDL cholesterol,
serum vitamin C. I keep that order everywhere below.

## Data description

The file `donor_biomarkers.csv` has one header row and 120 data rows. **One row
is one blood donor**: that donor's single donation-session sample, the five
biomarker values measured on it, the donor's smoking status, and the half the
donor was assigned to before measurement. Every donor appears exactly once, and
no cell is missing.

Every column in the file, in file order:

| Column | What it holds |
| --- | --- |
| `donor_id` | Donor identifier, `BD001` through `BD120`, unique per row. |
| `crp_mg_l` | Plasma C-reactive protein in mg/L. Declared outcome 1. |
| `wbc_count_10e9_per_l` | White blood cell count in 10^9 cells/L. Declared outcome 2. |
| `fibrinogen_g_l` | Plasma fibrinogen in g/L. Declared outcome 3. |
| `hdl_cholesterol_mmol_l` | HDL cholesterol in mmol/L. Declared outcome 4. |
| `vitamin_c_umol_l` | Serum vitamin C in umol/L. Declared outcome 5. |
| `smoking_status` | The grouping factor. Two values: `smoker`, `never_smoker`. |
| `study_stage` | The fixed pre-measurement split. Two values: `discovery`, `validation`. |

Counts as read by the script:

| | discovery | validation | total |
| --- | --- | --- | --- |
| `smoker` | 30 | 30 | 60 |
| `never_smoker` | 30 | 30 | 60 |
| total | 60 | 60 | 120 |

## Per-group summary

Across all 120 donors, by smoking group. Spread is the sample standard
deviation.

| Outcome | Group | n | Mean | SD |
| --- | --- | --- | --- | --- |
| `crp_mg_l` | smoker | 60 | 2.512 | 1.253 |
| `crp_mg_l` | never_smoker | 60 | 1.298 | 0.739 |
| `wbc_count_10e9_per_l` | smoker | 60 | 8.155 | 1.835 |
| `wbc_count_10e9_per_l` | never_smoker | 60 | 6.527 | 1.415 |
| `fibrinogen_g_l` | smoker | 60 | 3.273 | 0.530 |
| `fibrinogen_g_l` | never_smoker | 60 | 3.106 | 0.497 |
| `hdl_cholesterol_mmol_l` | smoker | 60 | 1.249 | 0.301 |
| `hdl_cholesterol_mmol_l` | never_smoker | 60 | 1.389 | 0.343 |
| `vitamin_c_umol_l` | smoker | 60 | 41.377 | 13.898 |
| `vitamin_c_umol_l` | never_smoker | 60 | 53.005 | 15.324 |

These summaries are descriptive. They use the whole cohort and they are not the
basis of any conclusion below.

## The two stages

**Stage one, screening.** Using only the 60 discovery donors, I compared
smokers with never-smokers on each of the five outcomes with a Welch two-sample
t-test, which is the standard two-group test for continuous measurements and
does not assume the two groups share a variance. I screened at the conventional
0.05 level, unadjusted, and carried forward every outcome that passed. This
stage sorts candidates from non-candidates. It settles nothing.

| Outcome | Mean difference (smoker minus never) | t | p | Screening result |
| --- | --- | --- | --- | --- |
| `crp_mg_l` | 1.562 | 5.432 | 2.78e-06 | carried forward |
| `wbc_count_10e9_per_l` | 1.633 | 3.594 | 0.000747 | carried forward |
| `fibrinogen_g_l` | 0.286 | 2.476 | 0.0163 | carried forward |
| `hdl_cholesterol_mmol_l` | -0.099 | -1.122 | 0.267 | screened out |
| `vitamin_c_umol_l` | -11.413 | -2.859 | 0.00593 | carried forward |

Four of the five outcomes were carried forward: C-reactive protein, white blood
cell count, fibrinogen, and vitamin C. HDL cholesterol was not.

**Stage two, confirmation.** Using only the 60 validation donors, and none of
the discovery donors, I re-tested just those four carried-forward outcomes with
the same Welch two-sample t-test. Because four tests were run in this stage, I
judged each one against a Bonferroni-adjusted level: the conventional 0.05
divided by the 4 outcomes carried forward, which gives **0.0125**. Splitting the
0.05 four ways this way keeps the chance of at least one false claim across the
whole confirmation stage at 0.05, rather than letting it grow with the number of
tests.

| Outcome | Mean difference (smoker minus never) | t | p | vs. 0.0125 | Confirmation result |
| --- | --- | --- | --- | --- | --- |
| `crp_mg_l` | 0.867 | 3.698 | 0.000498 | below | confirmed |
| `wbc_count_10e9_per_l` | 1.623 | 4.090 | 0.000135 | below | confirmed |
| `fibrinogen_g_l` | 0.048 | 0.324 | 0.747 | above | not confirmed |
| `vitamin_c_umol_l` | -11.843 | -3.276 | 0.00178 | below | confirmed |

Every conclusion in this report comes from this table. The discovery p-values
above are screening figures and I make no claim from them. An outcome that did
not survive screening was never tested in the validation half, so it gets no
significance claim of any kind, in either direction.

## Conclusions, in the declared order

1. **Plasma C-reactive protein (mg/L): confirmed.** In the validation half,
   smokers had higher CRP than never-smokers by 0.867 mg/L (p = 0.000498, below
   the adjusted level of 0.0125).

2. **White blood cell count (10^9/L): confirmed.** In the validation half,
   smokers had a higher count than never-smokers by 1.623 units (p = 0.000135,
   below 0.0125).

3. **Plasma fibrinogen (g/L): not confirmed.** It passed screening, but in the
   validation half the two groups differed by only 0.048 g/L and the test gave
   p = 0.747, well above the adjusted level of 0.0125. The discovery-half signal
   did not hold up.

4. **HDL cholesterol (mmol/L): not confirmed.** It did not pass discovery
   screening (p = 0.267), so it was not carried into the validation half and no
   significance claim is made for it, either way.

5. **Serum vitamin C (umol/L): confirmed.** In the validation half, smokers had
   lower vitamin C than never-smokers by 11.843 umol/L (p = 0.00178, below
   0.0125).

Of the five declared outcomes, three separate smokers from never-smokers in the
validation half: C-reactive protein, white blood cell count, and vitamin C. The
directions match what a clinician would expect, with the two inflammatory
markers raised in smokers and vitamin C lowered. Fibrinogen and HDL cholesterol
do not carry a confirmed difference in this cohort, and I would treat both as
open rather than settled: 60 donors per stage is a small study, and failing to
confirm a difference is not the same as showing there is none.

## Reproducing this

Run `python analysis.py` from the project root. It reads
`donor_biomarkers.csv` and prints the cohort counts, the per-group summaries,
both stages, and the per-outcome conclusions.
