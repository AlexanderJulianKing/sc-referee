# Carcass chilling validation: air chilling versus chlorinated-water immersion chilling

Internal validation report. Single plant, single production day.

## 1. Purpose and design

The plant runs two carcass chilling lines: conventional air chilling and immersion
chilling in chlorinated water. This study compared the two lines on the plant's own
equipment during one production day.

Forty-eight carcasses were sampled, twenty-four from each line, alternating between
the lines through the day. Each carcass was rinsed once in a standard whole-bird
rinse, and all three microbiological outcomes for that carcass were measured from
that single rinse. Carcass surface temperature was recorded on the same carcass at
the end of chilling. The carcass is the unit of the study. No carcass appears twice.

The sampling plan declared four outcomes, in this fixed order:

1. Campylobacter count in the rinse
2. Total aerobic count in the rinse
3. Generic *Escherichia coli* count in the rinse
4. Carcass surface temperature at the end of chilling

## 2. Data description

The analysis input is `carcass_rinse_data.csv`: one header row and 48 data rows,
six comma-separated columns, no missing values.

**One row represents one sampled broiler carcass**, with its chilling method, the
three microbiological counts read from that carcass's single whole-bird rinse, and
that carcass's end-of-chilling surface temperature.

| Column | Unit | What it holds |
| --- | --- | --- |
| `carcass_id` | none | Carcass identifier, `C01` through `C48`. Unique across the file, one identifier per row. |
| `group` | none | Chilling method for that carcass. Exactly two entries: `air` (conventional air chilling) and `immersion` (immersion chilling in chlorinated water). 24 rows each. |
| `campylobacter_log_cfu` | log10 CFU per mL of rinse | Campylobacter count in the whole-bird rinse, base-ten logarithm scale. |
| `aerobic_log_cfu` | log10 CFU per mL of rinse | Total aerobic count in the whole-bird rinse, base-ten logarithm scale. |
| `ecoli_log_cfu` | log10 CFU per mL of rinse | Generic *E. coli* count in the whole-bird rinse, base-ten logarithm scale. |
| `surface_temp_c` | degrees Celsius | Carcass surface temperature recorded at the end of chilling. |

The four outcome columns appear in the declared order given in section 1.

A small number of values sit exactly at a reporting floor (0.40 for Campylobacter,
2.00 for the aerobic count, 0.4 degrees Celsius for temperature), as recorded in
`DATA_DESCRIPTION.md`. Per that file, the values are synthetic and are not
measurements from a real plant.

## 3. The analysis rule

The analysis rule was fixed before the sampling day. It is a gated two-stage
procedure. It protects the family error rate by refusing to look at any individual
outcome unless the outcome set as a whole shows a difference.

**Stage one, the overall screen.** Compute one number directly from the four outcome
columns, using plain arithmetic on the values themselves and no statistical routine.
For each outcome, take the squared difference between the air mean and the immersion
mean and divide it by the pooled variance of that outcome. Sum the four results. The
sum measures how far apart the two chilling methods sit across the whole outcome set.

**Pre-set cut-off: 4.00.** That is the value the sum reaches when the two methods
differ by an average of one pooled standard deviation on each of the four outcomes.
The cut-off was fixed in advance and was not chosen after seeing the data.

**Stage two, the per-outcome comparisons.** Only if the screen reaches the cut-off
are the four per-outcome two-group comparisons performed and reported. If the screen
falls short, the analysis stops at stage one, reports the screen value and the
cut-off, and makes no per-outcome claim at all.

The script `analysis.py` implements both branches and labels which one it took.

## 4. Stage one result

| Outcome | Contribution to the screen |
| --- | --- |
| `campylobacter_log_cfu` | 3.496 |
| `aerobic_log_cfu` | 4.214 |
| `ecoli_log_cfu` | 2.175 |
| `surface_temp_c` | 5.637 |
| **Screen value** | **15.523** |
| Pre-set cut-off | 4.000 |

The screen took the value **15.523**, well above the pre-set cut-off of 4.00.

**Branch taken: the screen passed and the gate opened.** Stage two was therefore
performed and is reported below.

## 5. Stage two results

Four two-sided Welch two-sample t-tests, one per outcome, alpha 0.05, presented in
the declared order.

| # | Outcome | Mean, air | Mean, immersion | Difference (air minus immersion) | t | df | p-value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Campylobacter (log10 CFU/mL) | 2.952 | 1.822 | 1.130 | 6.477 | 44.9 | 6.1e-08 |
| 2 | Total aerobic count (log10 CFU/mL) | 4.651 | 3.418 | 1.233 | 7.111 | 44.4 | 7.5e-09 |
| 3 | Generic *E. coli* (log10 CFU/mL) | 2.256 | 1.509 | 0.747 | 5.109 | 45.4 | 6.3e-06 |
| 4 | Surface temperature (degrees C) | 4.917 | 2.542 | 2.375 | 8.224 | 42.2 | 2.6e-10 |

Within-group standard deviations were 0.556, 0.541, 0.536 and 0.836 on the air line
and 0.650, 0.655, 0.475 and 1.141 on the immersion line, in the same outcome order.

All four outcomes are lower on the immersion line. The three microbiological
reductions are 1.13, 1.23 and 0.75 log10 CFU per mL, and carcasses leave the
immersion line about 2.4 degrees Celsius colder.

## 6. Limits of this study

- One plant, one production day, one rinse per carcass. The comparison holds for
  this line and this day. It is not a general claim about the two chilling
  technologies.
- The two lines were not randomised. Carcasses were assigned by whichever line they
  ran on, so any standing difference between the lines beyond the chilling step is
  bound up with the method effect.
- The three microbiological counts came from the same rinse on the same carcass, so
  they are correlated rather than independent readings.
- Family-wise protection rests entirely on the stage-one gate. No further
  multiplicity adjustment was applied to the four p-values, and the same 48 carcasses
  supplied both the screen and the per-outcome tests.
- Some values sit at a reporting floor, so the counts at the low end are censored
  rather than exact.

## 7. Conclusion

The gate opened and all four declared outcomes favoured immersion chilling in
chlorinated water. Campylobacter, total aerobic count and generic *E. coli* were each
lower on the immersion line, by 1.13, 1.23 and 0.75 log10 CFU per mL, and carcasses
came off that line 2.4 degrees Celsius colder, which also gives a better start on
downstream cold-chain control.

On this evidence the plant should keep the chlorinated-water immersion chilling line
as its primary chilling method. Because the design is a single-day, non-randomised
comparison on one line pair, this result should be confirmed by repeat sampling on
further production days before it is written into the plant's HACCP validation file.
