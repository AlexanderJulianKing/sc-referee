# Supplementary feeding of orphaned harbour seal pups: diet comparison

## Question

Does the high-fat fish-oil supplemented diet produce heavier pups in care than the centre's
standard diet? We compared body mass between the two feeding protocols.

## The data

Twenty orphaned harbour seal pups were admitted over one season. Ten were assigned the standard
pup diet at admission and ten the high-fat fish-oil supplemented diet. Each pup was weighed once a
week for eight consecutive weeks in care, giving 160 weight records with no missing weighings.

The data file is `seal_pup_masses.csv`, 160 data rows plus a header. **One row is one weekly
weighing of one pup: the body mass recorded for a single pup in a single week of care.**

| Column | Type | Values in this file | Meaning |
|--------|------|---------------------|---------|
| `pup_tag` | string | `HS-101` to `HS-120`, 20 distinct values | Tag identifying the pup that was weighed. |
| `diet_group` | string | `standard`, `supplemented` | The feeding protocol assigned at admission. |
| `week_in_care` | integer | 1 to 8 | Week of care in which the weighing was taken; week 1 is the admission weighing. |
| `body_mass_kg` | decimal | 16.0 to 32.1, one decimal place | Body mass at that weighing, in kilograms. |

Each diet group contributes 80 weight records. Mass is recorded to one decimal place on the
centre's platform scale.

## Analysis

We ran an independent two-sample t-test of `body_mass_kg` between the two levels of `diet_group`,
across every weighing row in the table. The analysis was performed in Python with pandas 2.0.3 and
SciPy 1.9.1; the script is `analysis.py`.

## Result

Sample size: **160 weight records**, 80 per diet group.

| Diet group | Weight records | Mean body mass (kg) | SD (kg) |
|------------|----------------|---------------------|---------|
| standard | 80 | 22.79 | 3.76 |
| supplemented | 80 | 24.84 | 4.06 |

Difference in means (supplemented minus standard): **2.06 kg**.

Two-sample t-test: **t(158) = 3.324, p = 0.0011**.

Mean body mass by week in care (kg):

| Week in care | standard | supplemented |
|--------------|----------|--------------|
| 1 | 18.39 | 19.03 |
| 2 | 19.56 | 20.63 |
| 3 | 20.78 | 21.98 |
| 4 | 22.23 | 24.00 |
| 5 | 23.25 | 25.80 |
| 6 | 24.48 | 27.28 |
| 7 | 26.26 | 29.23 |
| 8 | 27.33 | 30.78 |

## Conclusion

The supplemented diet produced heavier pups. Pups on the high-fat fish-oil supplemented diet
averaged 24.84 kg against 22.79 kg on the standard diet, a difference of 2.06 kg, and the
two-sample t-test gives t(158) = 3.324, p = 0.0011. The gap widens over the eight weeks in care,
from 0.64 kg at the admission weighing to 3.45 kg at week eight. With 160 weight records the study
has ample data to settle the comparison, and we recommend the supplemented protocol for orphaned
harbour seal pups in rehabilitation.
