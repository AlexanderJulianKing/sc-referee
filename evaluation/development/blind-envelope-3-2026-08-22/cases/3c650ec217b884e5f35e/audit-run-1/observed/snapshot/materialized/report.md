# Deficit irrigation and soluble solids content of polytunnel strawberries

## 1. Data description

The project contains one data file, `strawberry_brix.csv`. It is comma separated, with
lowercase underscore-joined column names, and holds 144 data rows under a single header row.
The values are invented for this exercise rather than measured in a real trial; they were
produced by `make_data.py` with a fixed seed, and `DATA_DESCRIPTION.md` records how.

**One row of the file is one berry.** Each row is a single ripe berry picked from a single
mother plant, recorded together with the identity, irrigation schedule and polytunnel row of
the plant it came from. Six rows therefore share each mother plant, and the six berries from
one plant are not independent of each other: they carry that plant's root zone, water supply
and genetics in common. The plant, not the berry, is the unit that was assigned to an
irrigation schedule. For that reason the comparison reported below is made on one value per
plant, 24 values in total, and not on the 144 berry rows. Treating the berries as independent
would overstate the sample size six-fold.

The file has six columns.

| Column | Type | What it holds |
|---|---|---|
| `plant_id` | text | Identifier of the mother plant the berry came from, `P01` to `P24`. This is the experimental unit. Each value appears in exactly 6 rows. |
| `irrigation_schedule` | text | Irrigation treatment applied to that plant, `deficit` or `full`. A property of the plant, so it is constant across the plant's six rows. |
| `berry_id` | text | Identifier of the individual berry, the plant identifier followed by the berry number within that plant, for example `P01_B3`. All 144 values are distinct. |
| `soluble_solids_brix` | number | Soluble solids content of that berry in degrees Brix, read on a hand refractometer and recorded to 0.1. This is the response variable. Values run from 5.4 to 10.3. |
| `berry_fresh_weight_g` | number | Fresh weight of that berry in grams, recorded to 0.1 on a bench balance. Values run from 11.2 to 25.1, mean 18.1 g. |
| `polytunnel_row` | integer | Row of the polytunnel the plant sat in, 1 to 4. A property of the plant, so it is constant across the plant's six rows. |

No per-plant summary file is distributed. The reduction from 144 berry rows to 24 per-plant
values is a step of the analysis and is carried out in `analysis.py`.

## 2. Trial layout

Twenty-four strawberry mother plants were grown in a single polytunnel and split evenly
between two irrigation schedules: twelve plants on a deficit schedule and twelve on the
standard full schedule. Irrigation was applied to the whole plant, so the plant is the unit
of randomisation and of replication.

The plants sat in four rows of the polytunnel, six plants to a row. The two schedules are
balanced across those rows, with three deficit and three full plants in each of the four
rows, so schedule is not confounded with position in the tunnel.

At harvest, six ripe berries were picked from each plant and the soluble solids content of
every berry was read on a hand refractometer, giving 6 berries x 24 plants = 144 berry
measurements. Berry fresh weight was recorded at the same time. The six berries from a plant
are subsamples of that plant, taken to reduce the measurement error of the plant's sugar
level, and they do not add replication of the treatment.

## 3. Methods

The analysis is in `analysis.py` and runs in two stages.

**Reduction to the experimental unit.** The function `reduce_to_plant_means` takes the full
berry-level table and returns a table with one row per mother plant. Each row carries the
plant identifier, the irrigation schedule that plant was assigned to, the mean soluble solids
content of that plant's six berries, the standard deviation of those six berries, and the
number of berries contributing. The function first checks that every plant carries exactly one
irrigation schedule label, so the schedule can be attached to the per-plant row without
ambiguity. This step turns the 144-row berry table into a 24-row plant table. Nothing
downstream of it touches the berry rows.

**Two-group comparison.** The comparison is run on the table that the reduction step hands
back, and only on that table. The 12 deficit per-plant means are compared with the 12 full
per-plant means using an independent two-sample t-test with Welch's correction, since the two
schedules are separate sets of plants and their between-plant spreads are not assumed equal
(`scipy.stats.ttest_ind` with `equal_var=False`). The sample size that enters the test is the
number of plants in each group, 12 and 12, not the 72 berries in each group. Means and
standard deviations are reported from the per-plant values for the same reason. A 95 per cent
confidence interval for the difference in schedule means was formed from the same Welch
standard error and degrees of freedom.

The mean within-plant standard deviation of the berries is also reported, as a description of
berry-to-berry variability. It is descriptive only and does not enter the test.

## 4. Results

The reduction step produced 24 per-plant values, six berries behind each.

Per-plant mean soluble solids content, summarised by schedule:

| Schedule | Plants (n) | Mean soluble solids (degrees Brix) | SD between plants (degrees Brix) | Mean within-plant SD (degrees Brix) |
|---|---|---|---|---|
| deficit | 12 | 8.38 | 0.43 | 0.74 |
| full | 12 | 7.60 | 0.83 | 0.87 |

Deficit-irrigated plants averaged 0.78 degrees Brix more soluble solids than fully irrigated
plants (95 per cent confidence interval 0.20 to 1.35 degrees Brix). The Welch two-sample
t-test on the per-plant values gave t = 2.868 with 16.54 degrees of freedom and p = 0.011, on
n = 12 plants per schedule.

Berry-to-berry variation within a plant (mean SD 0.74 and 0.87 degrees Brix) was larger than
the variation between plant means within a schedule (SD 0.43 and 0.83 degrees Brix). Averaging
six berries per plant therefore removed a substantial part of the measurement noise before the
schedules were compared.

Berry fresh weight was lower under deficit irrigation, with per-plant means of 17.3 g against
18.8 g under full irrigation. Fruit size was not part of the study question and was not
formally tested here, but the direction is the one usually seen when water is restricted.

## 5. Conclusion

Deficit irrigation raised the soluble solids content of the fruit. The per-plant means differ
by about 0.8 degrees Brix in favour of the deficit schedule, the difference is unlikely to be
chance variation between plants (p = 0.011 on 12 plants per group), and the confidence
interval excludes zero, though it is wide enough (0.20 to 1.35 degrees Brix) that the size of
the gain is not pinned down closely. Twelve plants per schedule is modest replication, so the
estimate of the effect should be read as approximate.

Two limits are worth stating. First, the sweeter fruit came with smaller fruit, so any gain in
sugar has to be weighed against yield, which this trial did not measure. Second, this is one
polytunnel in one season, and soluble solids respond to light, temperature and cultivar as
well as to water, so the size of the effect should not be carried to other sites or seasons
without further trials.

Finally, the analysis stands on the point made in the data description: the sample size is 24
plants, not 144 berries. Had the berries been treated as independent, the same difference
would have appeared far more precise than the trial can actually support.
