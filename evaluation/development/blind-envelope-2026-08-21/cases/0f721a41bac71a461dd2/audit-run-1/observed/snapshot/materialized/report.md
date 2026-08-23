# Supplementary feeding and day-12 nestling mass in great tits (*Parus major*)

## Data description

All measurements are held in `nestling_mass.csv`. One row of that file is one nestling, weighed
and measured a single time on day 12 after hatching. Each row carries that chick's own two
measurements together with the box it was raised in, the feeding treatment that box received, and
the date its brood hatched. No chick appears twice.

The file has six columns:

| Column | Description |
|---|---|
| `nest_tag` | The nestbox the chick was raised in, written as `NB-` plus the box number used in the plot (for example `NB-04`). Sixteen distinct tags appear. |
| `food_treatment` | The feeding treatment applied at that box, either `supplemented` or `control`. |
| `chick_ring` | The ring number of the individual nestling (for example `A1201`), unique across the file. |
| `hatch_date` | The date the brood hatched, as an ISO date. Hatch dates span 2026-04-22 to 2026-05-06. |
| `mass_g_day12` | Body mass of the nestling in grams on day 12 after hatching, to one decimal place. This is the outcome of interest. |
| `tarsus_mm` | Tarsus length of the same nestling in millimetres on day 12, recorded as an index of skeletal size. |

The file contains 64 data rows and one header row.

## Design

Sixteen nestboxes in the long-term study population were used. Eight boxes were allocated to the
supplemented treatment, in which a mealworm feeder was placed within 5 m of the box from hatching
onward and kept stocked; the remaining eight boxes were left unsupplemented and served as
controls. Every box in the study held exactly four surviving nestlings on day 12, and each of
those chicks was caught once, weighed to 0.1 g, and measured for tarsus length before being
returned to the box. This yields 32 supplemented nestlings and 32 control nestlings, 64 day-12
mass measurements in all.

## Comparison performed

Day-12 body mass was compared between the two feeding treatments with a two-sample *t*-test
(`scipy.stats.ttest_ind`, two-sided, equal variances assumed).

The measurements entering the test were the individual `mass_g_day12` values. Every nestling from
a supplemented box contributed its own mass to the first sample, and every nestling from a control
box contributed its own mass to the second sample, so each of the 64 weighings is one observation
in the analysis. The sample size claimed for the test is therefore **N = 32 per group, N = 64 in
total**, with 62 degrees of freedom. No other column was used in the test: `tarsus_mm`,
`hatch_date`, `nest_tag`, and `chick_ring` were carried in the file for record-keeping but did not
enter this comparison.

## Results

Nestlings from supplemented boxes averaged 15.91 g on day 12 (SD = 1.25 g, n = 32). Nestlings from
control boxes averaged 15.43 g (SD = 1.12 g, n = 32). The supplemented chicks were therefore
0.47 g heavier on average, about 3% of mean control mass.

The two-sample *t*-test on these 64 measurements gave *t* = 1.589 with 62 degrees of freedom and
*p* = 0.117.

Individual masses ranged from 13.0 g to 18.6 g across the whole sample, and the two treatment
distributions overlapped broadly over that range.

## Conclusion

Day-12 nestlings in supplemented broods were on average about half a gram heavier than nestlings
in unsupplemented broods, but at the conventional 5% threshold the difference between the two
groups was not statistically significant (*t* = 1.589, *p* = 0.117, N = 32 nestlings per group).
The measured effect of placing a mealworm feeder at the box is in the expected direction and small
relative to the variation in mass among chicks in this population.
