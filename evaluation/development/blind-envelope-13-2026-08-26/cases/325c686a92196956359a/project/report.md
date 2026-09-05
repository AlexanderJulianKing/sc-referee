# Two enrichment programmes for captive Asian elephants

Every number in this report is printed by `analysis.py`, which reads
`elephant_enrichment_welfare.csv` from the project root.

## The data

The file `elephant_enrichment_welfare.csv` holds 34 data rows plus a header row.

**One row is one elephant.** Each elephant was on exactly one of the two enrichment
programmes, was watched over a single four-week block, and that whole block was boiled down to one
value per outcome. There are 17 elephants on each programme, drawn from several facilities. There
are no repeated measures and no blank cells.

The columns, in file order:

| Column | Meaning | Unit |
| --- | --- | --- |
| `animal_id` | Study identifier for the individual elephant, unique across the file. | none (text label) |
| `enrichment_group` | Which programme the elephant was on. `scatter_feeding` means forage was spread unpredictably around the habitat during the day. `fixed_station` means forage was put out at set points and set times. | none (text label) |
| `stereotypic_behaviour_pct` | Repetitive behaviour such as weaving or pacing, counted as the share of scan samples in which it was seen. | percent of scan samples |
| `daily_walking_distance_km` | Mean distance walked per day over the block. | kilometres per day |
| `night_recumbent_rest_min` | Mean time per night spent lying down at rest. | minutes per night |
| `faecal_glucocorticoid_metabolites_ng_per_g` | Mean level of faecal glucocorticoid metabolites. These are the leftovers of stress hormones that the body clears into the dung, so they act as a delayed record of how hard the stress system has been working. | nanograms per gram of dry faeces |
| `feeding_bout_duration_min` | Mean total time per day spent feeding, added up across all feeding bouts in the day. | minutes per day |
| `social_proximity_pct` | Share of scan samples in which the elephant was within one body length of another elephant. | percent of scan samples |

The last six columns are the six outcomes declared in `PROTOCOL.md`, in the declared order. They
form one outcome family.

## How the test works

The plain comparison is a two-sample t test between the two programmes, run the same way on each of
the six outcomes. The t statistic is the gap between the two group means divided by how noisy that
gap should be by chance. It is written here as scatter feeding minus fixed station, so a positive
value means the scatter-feeding group scored higher.

Six tests instead of one is the problem. Run six tests on data where nothing is really going on, and
the chance that at least one of them looks impressive by luck is much higher than the 5 percent you
signed up for. So the script builds its own yardstick instead of applying a packaged correction.

The label-shuffling procedure works like this:

1. Compute the six observed t statistics from the real data.
2. Shuffle the 34 programme labels among the 34 elephants at random, keeping 17 labels of each kind.
   The measurements stay attached to their own elephant. Only the labels move.
3. On that shuffled dataset, recompute all six t statistics, take their absolute values, and keep
   **only the single largest one**. Throw the other five away.
4. Repeat steps 2 and 3 **5000 times**. The number 5000 is fixed in advance and written into the
   script, along with a fixed random seed (20260826) so the run reproduces exactly.

That leaves 5000 values. Each one answers the question: if the programme labels meant nothing at
all, how big would the biggest of my six statistics have looked on that occasion? This is the
family-maximum reference distribution. Its 95th percentile is the critical value, and here that
value is **2.847**.

**Why keeping only the maximum controls the family-wise error rate.** The family-wise error rate is
the chance of making at least one false claim anywhere in the family of six. Say the labels really
are meaningless. Making at least one false claim means at least one of the six absolute statistics
crossed the threshold, and that is the same event as the largest of the six crossing it. The
shuffled maxima tell us directly how often the largest of six crosses a given line when labels are
meaningless. Set the line at the 95th percentile of those maxima and the largest of six crosses it
only 5 percent of the time. So the chance of one or more false claims across all six outcomes is
held at 5 percent, no matter how many of the six you go on to test. The threshold is deliberately
higher than a single-test threshold would be, and that is the price of asking six questions.

Two honest limits. First, the argument above is exact when no outcome differs between programmes.
Extending it to the case where some outcomes do differ is the standard assumption behind this kind
of maximum-statistic test, and it holds when shuffling labels leaves the behaviour of the
no-difference outcomes unchanged, which is reasonable here because every elephant contributes one
independent row. Second, 5000 shuffles is a finite sample of the reference distribution, so the
critical value carries a little simulation noise of its own.

## Results

Group means, from the script's output:

| Outcome | Scatter feeding | Fixed station |
| --- | --- | --- |
| `stereotypic_behaviour_pct` | 5.482 | 7.600 |
| `daily_walking_distance_km` | 7.864 | 7.393 |
| `night_recumbent_rest_min` | 200.059 | 197.118 |
| `faecal_glucocorticoid_metabolites_ng_per_g` | 64.524 | 61.447 |
| `feeding_bout_duration_min` | 487.118 | 404.412 |
| `social_proximity_pct` | 27.465 | 28.541 |

Across the 5000 shuffles the family maximum ran from 0.304 at its smallest to 5.489 at its largest,
with a median of 1.648. The 95th percentile, and so the critical value for every outcome, is 2.847.

Each verdict below compares that outcome's observed statistic against the family-maximum
distribution. No verdict uses an unadjusted per-outcome p-value. The adjusted p-value in the table
is the share of shuffles whose family maximum reached or beat that outcome's observed absolute
statistic, computed with the usual plus-one adjustment in numerator and denominator.

| Outcome | Observed t | Critical value | Adjusted p | Verdict |
| --- | --- | --- | --- | --- |
| `stereotypic_behaviour_pct` | -1.825 | 2.847 | 0.3875 | not significant |
| `daily_walking_distance_km` | 0.979 | 2.847 | 0.9144 | not significant |
| `night_recumbent_rest_min` | 0.182 | 2.847 | 1.0000 | not significant |
| `faecal_glucocorticoid_metabolites_ng_per_g` | 0.474 | 2.847 | 0.9982 | not significant |
| `feeding_bout_duration_min` | 5.588 | 2.847 | 0.0002 | **significant** |
| `social_proximity_pct` | -0.437 | 2.847 | 0.9988 | not significant |

Where each observed statistic stands in the reference distribution:

- `stereotypic_behaviour_pct`: |t| = 1.825, larger than 61.26 percent of the 5000 family maxima.
- `daily_walking_distance_km`: |t| = 0.979, larger than 8.56 percent.
- `night_recumbent_rest_min`: |t| = 0.182, larger than 0.00 percent.
- `faecal_glucocorticoid_metabolites_ng_per_g`: |t| = 0.474, larger than 0.18 percent.
- `feeding_bout_duration_min`: |t| = 5.588, larger than 100.00 percent, meaning it sits above every
  one of the 5000 shuffled maxima.
- `social_proximity_pct`: |t| = 0.437, larger than 0.12 percent.

One of the six declared outcomes reaches the 0.05 family-wise threshold.

## Conclusion

Only feeding time separates the two programmes once the whole family of six outcomes is accounted
for. Elephants on the scatter-feeding programme spent about 83 more minutes a day in feeding bouts
than elephants on the fixed-station programme, 487 minutes against 404, and that gap is larger than
anything the 5000 label shuffles produced by chance. Spreading forage around the habitat gets
elephants working at their food for a much longer stretch of the day, which is the main thing
scatter feeding is meant to do.

The other five outcomes give no support for a difference at the 0.05 family-wise level. Stereotypic
behaviour was lower in the scatter-feeding group, 5.5 percent of scans against 7.6 percent, and it
was the runner-up in the family, but its statistic still sat below the family-maximum threshold, so
this study cannot call it a real difference. Walking distance, night rest, stress-hormone
metabolites, and social proximity were all close between the two groups.

Two cautions on reading this. A "not significant" verdict here means the study did not demonstrate a
difference, not that the two programmes are the same. With 17 elephants per programme and a
threshold raised to cover six outcomes, only a fairly large effect would clear the bar, so a real
but moderate benefit could easily go unrecorded. And the longer feeding time is a behavioural
change, not by itself proof of better welfare. The measures that speak more directly to welfare,
stereotypic behaviour and stress-hormone metabolites, did not separate the groups in this study. A
larger study, or one that follows the same elephants across both programmes, would be the way to
find out whether the extra feeding time carries through to those outcomes.
