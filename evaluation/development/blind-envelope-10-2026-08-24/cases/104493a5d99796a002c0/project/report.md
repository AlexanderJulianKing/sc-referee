# Conching temperature and dark chocolate quality

## Data description

The analysis reads `chocolate_batches.csv`. **One row is one production batch** of 70 percent dark
chocolate from a single cocoa origin, sampled once after a fixed tempering and resting schedule. The
file holds 60 data rows and no empty cells: 30 batches conched at 50 degrees Celsius and 30 conched
at 65 degrees Celsius.

Every column in the file, in file order:

| Column | Units | Meaning |
| --- | --- | --- |
| `batch_id` | none | Batch identifier, `B001` through `B060`, one per batch, in production order. |
| `conche_group` | none | Conching temperature group. Exactly two values: `conche_50c` and `conche_65c`. |
| `particle_d90_um` | micrometres | Particle size at the ninetieth percentile of the batch particle size distribution. |
| `hardness_n` | newtons | Snap hardness, the peak force in a three-point snap test on the tempered bar. |
| `melt_peak_c` | degrees Celsius | Melting peak temperature of the batch. |
| `gloss_gu` | gloss units | Surface gloss of the moulded bar. |
| `bitterness_score` | score points | Trained-panel bitterness score on a zero to ten scale. |

The last five columns are the five quality outcomes the protocol declared in advance, listed here in
their declared order. Each one is measured once per batch.

## Method

For each declared outcome the analysis compares the two conching groups with a Welch two-sample t
test for independent samples, and calls the difference significant when the p-value falls below the
conventional 0.05 threshold. Standard deviations are sample standard deviations. The script
`analysis.py` walks the five declared outcomes in order and applies the same comparison to each one.

## Group summaries

Mean and standard deviation within each group, 30 batches per group.

| Outcome | `conche_50c` mean +/- SD | `conche_65c` mean +/- SD |
| --- | --- | --- |
| `particle_d90_um` | 23.377 +/- 1.646 | 22.703 +/- 1.621 |
| `hardness_n` | 52.550 +/- 5.921 | 51.793 +/- 6.248 |
| `melt_peak_c` | 32.789 +/- 0.409 | 32.856 +/- 0.446 |
| `gloss_gu` | 96.813 +/- 15.016 | 103.140 +/- 14.756 |
| `bitterness_score` | 4.940 +/- 0.852 | 4.440 +/- 0.905 |

## Results for the five declared outcomes

Differences are the 50 degree group mean minus the 65 degree group mean.

1. **Particle size D90 (micrometres).** Difference +0.673. t = +1.596, df = 57.99, p = 0.1159.
   Not significant at 0.05.
2. **Snap hardness (newtons).** Difference +0.757. t = +0.481, df = 57.83, p = 0.6320.
   Not significant at 0.05.
3. **Melting peak temperature (degrees Celsius).** Difference -0.067. t = -0.609, df = 57.56,
   p = 0.5447. Not significant at 0.05.
4. **Surface gloss (gloss units).** Difference -6.327. t = -1.646, df = 57.98, p = 0.1052.
   Not significant at 0.05.
5. **Bitterness score (0 to 10).** Difference +0.500. t = +2.203, df = 57.78, p = 0.0316.
   Significant at 0.05.

## Conclusion

Conching at 50 degrees instead of 65 degrees left four of the five declared quality outcomes
statistically indistinguishable between the groups. Particle size, snap hardness, melting peak
temperature, and surface gloss all came out with p-values above 0.05, so on this evidence the cooler
conche does not change grind fineness, bar snap, melting behaviour, or finish.

The one outcome that did separate is the trained-panel bitterness score. Batches conched at 50
degrees scored 0.500 points higher on the ten point scale (4.940 against 4.440, p = 0.0316). A cooler
conche therefore leaves the physical properties of the bar where they are and shifts the flavour a
half point toward bitter.

The plant should consider the lower conching temperature, with the flavour change treated as the
deciding factor. The physical quality specifications that drive rework and customer complaints,
namely particle size, snap, melt, and gloss, are unaffected in these 60 batches. Whether a half point
of extra bitterness is acceptable depends on the target product profile, so the sensible next step is
a consumer or expert acceptance check on bars from the 50 degree conche before any line change.
