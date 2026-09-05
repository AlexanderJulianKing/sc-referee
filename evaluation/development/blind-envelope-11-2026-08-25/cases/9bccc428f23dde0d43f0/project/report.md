# Supplementary winter feeding in semi-domesticated reindeer: April condition results

## Question and design

Late winter is when our reindeer lose the most condition, and the herding district
wanted to know whether pelleted supplement at the feeding stations carries animals
through that stretch in better shape. We followed 72 semi-domesticated reindeer from
January to April. Thirty-six were offered pelleted supplement at the feeding stations
over that period; the other thirty-six grazed natural winter pasture only. Feeding
regime is the grouping factor and it has exactly two levels. Each animal was handled
once, in April, and contributes one set of measurements, so there are no repeated
records on the same animal.

Four outcomes were written into the study plan before the winter began, and we keep
them in that declared order throughout: body mass, back fat thickness, serum urea, and
hair cortisol. Body mass and back fat are the direct condition measures. Serum urea
rises when an animal is breaking down its own protein for energy, so a lower value is
the better sign. Hair cortisol grows into the hair over weeks, so a single April hair
sample gives an integrated picture of stress across the whole winter rather than the
stress of the handling day.

## Data description

### `reindeer_winter_measurements.csv`

One row is one reindeer, recorded at its single April handling. There are 72 data rows
plus a header. Ear tags were handed out at capture, so the two feeding regimes are
mixed through the file rather than blocked together.

| Column | What it holds |
| --- | --- |
| `animal_id` | Ear-tag identifier, `RD-1001` through `RD-1072`. One row per identifier. |
| `body_mass_kg` | Live body mass in kilograms at the April handling, from the handling-crush scale. |
| `back_fat_thickness_mm` | Subcutaneous back fat depth in millimetres, measured by ultrasound at the April handling. |
| `serum_urea_mmol_per_l` | Serum urea in millimoles per litre, from the April blood sample. |
| `hair_cortisol_pg_per_mg` | Hair cortisol in picograms per milligram of hair, from the April hair sample. |
| `feeding_regime` | The grouping factor, with exactly two values: `supplemented` and `pasture_only`. |

The four outcome columns sit in the declared order. No cell is empty anywhere in the
table.

### `adjusted_pvalues.csv`

This second file is not raw data. It is the result table carried over from an earlier,
separate stage of the pipeline. It has 4 data rows plus a header. One row is one
declared outcome, and the rows appear in the declared order.

| Column | What it holds |
| --- | --- |
| `outcome` | The name of the declared outcome, spelled exactly as the matching column in the raw file. |
| `p_raw` | The uncorrected p-value that earlier stage started from, before any family correction. |
| `p_adjusted` | The p-value that stage produced after correcting across all four declared outcomes together. |

## Per-group summary

Spread is the sample standard deviation. These figures come from the descriptive pass
in `analysis.py`.

| Outcome | Group | n | Mean | SD |
| --- | --- | ---: | ---: | ---: |
| Body mass (kg) | supplemented | 36 | 78.88 | 7.31 |
| Body mass (kg) | pasture_only | 36 | 70.18 | 8.54 |
| Back fat thickness (mm) | supplemented | 36 | 13.13 | 3.06 |
| Back fat thickness (mm) | pasture_only | 36 | 9.82 | 3.08 |
| Serum urea (mmol/L) | supplemented | 36 | 3.96 | 0.99 |
| Serum urea (mmol/L) | pasture_only | 36 | 6.18 | 1.36 |
| Hair cortisol (pg/mg) | supplemented | 36 | 3.41 | 1.13 |
| Hair cortisol (pg/mg) | pasture_only | 36 | 3.81 | 1.05 |

The routine data checks in the script all passed: 72 rows, 72 unique ear tags, 36
animals in each of exactly two feeding-regime values, all six expected columns in the
declared order, no missing cells, and every outcome inside a plausible range for its
unit (body mass 51.2 to 95.6 kg, back fat 4.8 to 21.5 mm, serum urea 1.49 to 8.48
mmol/L, hair cortisol 0.40 to 5.65 pg/mg).

## Where the statistics come from

I want to be plain about the division of labour here, because it decides how much
weight these conclusions can carry.

No significance test was run in this project. The comparison of the two feeding
regimes was done by an earlier pipeline stage, and that same stage also corrected the
whole family of four declared outcomes for multiple comparisons at the conventional
0.05 family level. Correcting the whole family matters because testing four outcomes
gives four chances to turn up a striking result by luck alone; the correction raises
the bar so that the family as a whole still carries the intended 5 percent error rate.
That correction was applied across all four outcomes together, not one outcome at a
time.

What this project does with the raw file is descriptive and diagnostic only: counts,
group means and standard deviations, and the integrity checks listed above. The
`analysis.py` script then reads `adjusted_pvalues.csv` and takes every significance
verdict straight from the adjusted values it finds there, judged at 0.05. It computes
no p-value of its own, and the group means above are not evidence of a difference on
their own.

So every conclusion below rests entirely on the adjusted values supplied by that
earlier stage. If those values are wrong, or if they were produced from a different
version of the data than the file analysed here, the conclusions go with them. I have
not re-derived them, and nothing in this project could catch such an error.

## Conclusions, in the declared order

**1. Body mass (kg).** Adjusted p = 4.79e-05, which is below 0.05, so this outcome is
called significant. Supplemented animals averaged 78.88 kg against 70.18 kg on pasture
only, a difference of about 8.7 kg in the direction of the supplement.

**2. Back fat thickness (mm).** Adjusted p = 4.79e-05, below 0.05, so this outcome is
called significant. Supplemented animals carried about 13.13 mm of back fat against
9.82 mm on pasture only, roughly 3.3 mm more.

**3. Serum urea (mmol/L).** Adjusted p = 1.84e-10, well below 0.05, so this outcome is
called significant. Supplemented animals sat at 3.96 mmol/L against 6.18 mmol/L on
pasture only. Urea runs lower in the supplemented group, which fits animals that are
not having to break down their own body protein for energy.

**4. Hair cortisol (pg/mg).** Adjusted p = 0.118, which is above 0.05, so this outcome
is not called significant. The two groups are close: 3.41 pg/mg supplemented against
3.81 pg/mg on pasture only. This study gives no evidence that supplementary feeding
changed the winter-integrated cortisol level. That is a failure to demonstrate a
difference, not a demonstration that the two regimes are the same.

Taken together, the three body-condition and metabolic outcomes moved as the district
hoped, while the stress marker did not separate the groups.
