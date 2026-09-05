# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Seeded generator (`SEED = 6`, NumPy `default_rng`). Running it rewrites `lifeguard_airway.csv` byte-for-byte. |
| `lifeguard_airway.csv` | The dataset for the study. 46 data rows plus one header row, 9 columns, no empty cells. |

## What one row represents

One row is one lifeguard, assessed once. The assessment happens at the end of a
working week, after that person has worked at least six months at their
facility. There are 46 lifeguards in total: 23 at municipal pools disinfected
with chlorine alone, and 23 at pools using combined chlorine and ultraviolet
treatment. Nobody appears twice, and every lifeguard has a value for every
outcome.

## Columns of `lifeguard_airway.csv`

| Column | Type | Units / scale | Meaning |
| --- | --- | --- | --- |
| `lifeguard_id` | text | none | Identifier for the lifeguard, `LG-001` through `LG-046`. Unique across rows. |
| `pool_system` | text | none | The disinfection system at the lifeguard's facility. Exactly two values: `chlorine_only` (23 rows) and `chlorine_uv` (23 rows). |
| `feno_ppb` | number, 1 decimal | parts per billion | Fractional exhaled nitric oxide. Observed range 5.7 to 39.7. |
| `fev1_pct_pred` | number, 1 decimal | percent of predicted | Forced expiratory volume in one second, as a percent of the value predicted for that person. Observed range 80.8 to 113.1. |
| `fvc_pct_pred` | number, 1 decimal | percent of predicted | Forced vital capacity, as a percent of the value predicted for that person. Observed range 86.3 to 112.2. |
| `airway_symptom_score` | whole number | 0 to 20 scale | Upper airway symptom score. Higher means more symptoms. Observed range 1 to 15. |
| `eye_irritation_score` | whole number | 0 to 10 scale | Eye irritation score. Higher means more irritation. Observed range 1 to 8. |
| `cc16_ug_l` | number, 1 decimal | micrograms per litre | Serum club cell protein CC16. Observed range 6.5 to 17.2. |
| `cough_days_per_month` | whole number | days | Self-reported days with cough in the past month. Observed range 0 to 12. |

The seven outcome columns appear in the order the protocol declared them:
`feno_ppb`, `fev1_pct_pred`, `fvc_pct_pred` are the three declared primary
outcomes, and `airway_symptom_score`, `eye_irritation_score`, `cc16_ug_l`,
`cough_days_per_month` are the four declared secondary outcomes.

## How the values were produced

`make_data.py` draws each lifeguard's seven values from normal distributions
with a per-outcome group mean and within-group spread. Two hidden per-person
traits tie the outcomes together, the way repeated airway measures on the same
person tend to move together:

- an airway irritation trait, which pushes exhaled nitric oxide, symptom score,
  eye irritation and cough days up and serum CC16 down;
- a lung function trait, which pushes both spirometry columns (`fev1_pct_pred`
  and `fvc_pct_pred`) up together, and which sits slightly lower in people with
  a more irritated airway.

Any draw landing outside the plausible instrument range is redrawn rather than
trimmed to the boundary, so no value piles up on a limit. Scores and day counts
are rounded to whole numbers; the other outcomes keep one decimal.
