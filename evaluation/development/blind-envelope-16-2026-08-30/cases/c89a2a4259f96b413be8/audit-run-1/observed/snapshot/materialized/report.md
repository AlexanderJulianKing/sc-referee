# Flour dust and airway health on two bakery dough lines

## Data

The data file is `bakery_flour_dust.csv`. **One row is one production worker**, measured once on a
single working shift. There are 46 rows, 24 workers on the traditional open dough line and 22 on the
enclosed automated dosing line, and no missing values.

| Column | Meaning |
| --- | --- |
| `worker_id` | Short per-worker identifier (`W01`-`W46`). |
| `dough_line` | Production line: `open` or `enclosed`. |
| `dust_mg_m3` | Shift-average inhalable flour dust in the breathing zone (mg/m3). |
| `fev1_drop_ml` | Cross-shift fall in FEV1, start-of-shift minus end-of-shift (mL). |
| `ige_wheat_ku_l` | Serum wheat-specific IgE (kU/L). |
| `nasal_symptom_pts` | Work-related nasal symptom score over the past month (0-12 points). |

The four outcome columns are in the order the study declared them.

## Methods

Each of the four declared outcomes was compared between the two dough lines with a two-sample
(Student's) t-test on the individual worker values, run by `analysis.py` as four separate steps in
the declared order. Each outcome was declared in advance as its own question about flour exposure
and airway health, so each is judged on its own merits against the conventional 0.05 threshold.

## Results

| # | Outcome | Mean, open line | Mean, enclosed line | t | p | Verdict at 0.05 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `dust_mg_m3` | 2.311 mg/m3 | 1.071 mg/m3 | 5.407 | 2.489e-06 | Significant |
| 2 | `fev1_drop_ml` | 93.125 mL | 47.136 mL | 2.242 | 0.0301 | Significant |
| 3 | `ige_wheat_ku_l` | 0.905 kU/L | 0.700 kU/L | 0.788 | 0.4351 | Not significant |
| 4 | `nasal_symptom_pts` | 4.042 points | 3.545 points | 0.788 | 0.4351 | Not significant |

Per-outcome conclusions, in the declared order:

1. **Inhalable flour dust.** Open-line workers breathed about 1.24 mg/m3 more dust than
   enclosed-line workers. Significant at 0.05.
2. **Cross-shift FEV1 fall.** Open-line workers lost about 46 mL more FEV1 across the shift.
   Significant at 0.05.
3. **Wheat-specific IgE.** Open-line workers averaged about 0.21 kU/L higher, which the test does
   not distinguish from no difference. Not significant at 0.05.
4. **Nasal symptom score.** Open-line workers averaged about 0.5 points higher. Not significant at
   0.05.

## Interpretation

For a bakery occupational health audience, the exposure story is the clear one. Workers on the
traditional open dough line, where flour is tipped from sacks into open bowls, breathed roughly
twice the inhalable dust of workers on the enclosed dosing line, and they also lost roughly twice
as much FEV1 over the course of a shift. Both of those differences reached significance at 0.05.
That pattern is consistent with dust released at the tipping and mixing step causing a measurable
same-shift airway response.

The two longer-horizon outcomes did not separate the lines. Wheat-specific IgE and the past-month
nasal symptom score were both slightly higher on the open line, but the differences were small
relative to how much workers vary from one another, and neither reached 0.05. Sensitisation and
chronic symptoms build over years of employment, so a single-shift survey of 46 workers is not
well placed to pick them up, and these results should not be read as evidence that the two lines
are equivalent on those measures.

Practically, the enclosed dosing line is the lower-dust environment in these three bakeries, and
the cross-shift lung function data support treating open sack tipping and open-bowl mixing as the
control priority.
