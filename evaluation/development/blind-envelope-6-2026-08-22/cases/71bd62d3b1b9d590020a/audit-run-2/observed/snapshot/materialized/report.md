# Two analgesics for canine elbow osteoarthritis: force-platform results

All numbers in this report were produced by `analysis.py` in this directory, run with
`/usr/local/bin/python3 analysis.py` against `pvf_repeated_measures.csv`.

## Aim

Find out whether a new analgesic improves weight-bearing on the arthritic forelimb more than the
established analgesic does, in dogs with elbow osteoarthritis.

## Design

Twenty-four client-owned dogs were enrolled at a veterinary teaching hospital and randomised to one
of two arms, twelve dogs per arm. Each dog kept its assigned drug for the whole study. Every dog
walked over a force platform at five scheduled visits: baseline (week 0, before dosing) and then
weeks 2, 4, 8 and 12. At each visit the recorded outcome was peak vertical force through the
affected forelimb, expressed as a percentage of body weight (%BW). Higher values mean the dog is
putting more weight on the sore limb, so higher is better.

That gives 5 visits x 24 dogs = 120 rows of data, with no missing values and a fully balanced
design. The dog is the unit that was randomised, so the dog is the independent experimental unit
and the effective sample size is 24, not 120.

Observed arm means, in %BW:

| Visit week | established | new | difference (new minus established) |
| --- | --- | --- | --- |
| 0 (baseline) | 59.74 | 60.54 | +0.81 |
| 2 | 62.38 | 65.69 | +3.30 |
| 4 | 63.25 | 68.32 | +5.06 |
| 8 | 64.77 | 70.30 | +5.53 |
| 12 | 66.17 | 70.92 | +4.75 |

## Primary analysis: a dependence-aware mixed-effects model

### Why the repeated visits require it

Each dog appears five times in the file. Those five rows are not five separate dogs. A dog that
bears weight well at baseline tends to bear weight well at every later visit, because the five
measurements share one animal's own build, gait and disease severity. In statistical terms the rows
within a dog are correlated, and correlated rows carry less information than the same number of
independent rows would.

The fix is a random effect for dog. A random effect gives each dog its own offset from the overall
mean, drawn from a single distribution across dogs. Think of it as giving every dog its own personal
starting height on the scale, then asking how treatment moves the dog from that starting height. The
model then splits the variation into a between-dog part and a within-dog part, and the treatment
comparison is judged against the right one.

### The model

```
peak_vertical_force_pctbw ~ C(treatment_arm) * C(visit_week) + (1 | dog_id)
```

Fitted with `statsmodels` MixedLM by REML on all 120 rows: fixed effects for treatment arm, for
visit week entered as a five-level factor, and for the arm-by-week interaction, plus a random
intercept for each of the 24 dogs. The interaction is what lets the two arms sit together at
baseline and then separate over the follow-up, which is the pattern the design expects, since no dog
had received either drug at week 0.

### How much dependence there actually is

| Variance component | Estimate | SD |
| --- | --- | --- |
| Between-dog (random intercept) | 12.987 | 3.60 %BW |
| Within-dog residual | 1.300 | 1.14 %BW |

The intraclass correlation is 12.987 / (12.987 + 1.300) = **0.909**. About 91 percent of the
variation in peak vertical force is differences between dogs rather than change within a dog. With
five visits per dog that gives a design effect of 1 + (5 - 1) x 0.909 = 4.64, so the 120 rows carry
roughly the information of 26 independent observations. This is the concrete reason the row-level
test in the sensitivity section below cannot be the inferential result.

### The model estimate

Treatment effect from the fitted model, new minus established, at each visit. Positive favours the
new drug. Intervals are 95 percent Wald intervals.

| Visit week | Estimate (%BW) | SE | 95% CI | z | p |
| --- | --- | --- | --- | --- | --- |
| 0 (baseline) | +0.81 | 1.54 | -2.22 to 3.83 | 0.52 | 0.600 |
| 2 | +3.30 | 1.54 | 0.28 to 6.33 | 2.14 | 0.032 |
| 4 | +5.06 | 1.54 | 2.04 to 8.09 | 3.28 | 0.0010 |
| 8 | +5.53 | 1.54 | 2.51 to 8.56 | 3.59 | 0.0003 |
| **12 (primary readout)** | **+4.75** | **1.54** | **1.73 to 7.78** | **3.08** | **0.0021** |

The baseline row is a check, not a result: at week 0 the two arms differ by +0.81 %BW with a
confidence interval that comfortably includes zero (p = 0.600), which is what randomisation should
produce before any dog has been dosed.

**Primary estimate: at week 12 the new analgesic gives +4.75 %BW more peak vertical force than the
established analgesic (95% CI 1.73 to 7.78, p = 0.0021).** Both arms improve from baseline. The
model's week main effects put the established arm 6.43 %BW above its own baseline at week 12, and
the new arm rises by that amount plus the 3.95 %BW interaction term, a total of 10.38 %BW.

One caveat on the arithmetic: MixedLM Wald tests use a normal approximation rather than
finite-sample degrees of freedom. With only 24 dogs, those intervals are slightly narrower than a
small-sample method would give.

### Supporting check at the dog level

Because of that caveat, `analysis.py` also runs a Welch two-sample t-test on the week-12 values with
one value per dog, so the sample size is 24 dogs and the degrees of freedom are finite-sample. New
arm: 12 dogs, mean 70.92 %BW, SD 4.00. Established arm: 12 dogs, mean 66.17 %BW, SD 3.56. Difference
+4.75 %BW (95% CI 1.55 to 7.96), t = 3.07 on 21.7 df, p = 0.0056. This agrees with the primary
model, with an interval a little wider, as expected.

## Secondary sensitivity analysis only: row-level comparison

**This is a sensitivity check, not the inferential result.** It is reported to show how much the
answer would be distorted by ignoring the repeated-measures structure.

A plain Welch two-sample t-test across all 120 visit rows, with dog identity ignored, gives:
new arm mean 67.15 %BW over 60 visit rows, established arm mean 63.26 %BW over 60 visit rows,
difference +3.89 %BW, naive SE 0.876, t = 4.45, p = 2.03e-05.

Two things are wrong with reading that as the study result:

1. **Its sample size is visits, not dogs.** The n of 60 per arm counts 12 dogs five times each. Each
   dog was randomised once, so there are only 12 independent units per arm. Using the intraclass
   correlation of 0.909, the honest standard error for this contrast is about 1.885, which is 2.2
   times wider than the 0.876 printed by the naive test. The naive p-value of 2 in 100,000 is far
   more confident than the data support.
2. **It pools the pre-treatment baseline visit with the post-treatment visits.** At week 0 no dog had
   been dosed and the true arm difference should be zero, so including week 0 drags the pooled
   estimate (+3.89 %BW) below the week-12 effect (+4.75 %BW).

Both problems point the same way: this test is not a valid basis for inference here, and it is
labelled as a sensitivity check in `analysis.py` and in this report.

## Conclusion

In this cohort of 24 dogs with elbow osteoarthritis, both analgesics improved weight-bearing on the
affected forelimb over 12 weeks. The dependence-aware mixed-effects model puts the new analgesic
ahead of the established one by 4.75 %BW at week 12 (95% CI 1.73 to 7.78, p = 0.0021), with the
advantage already visible by week 2 and holding through weeks 4, 8 and 12. The arms were comparable
at baseline. The dog-level week-12 t-test agrees (+4.75 %BW, 95% CI 1.55 to 7.96, p = 0.0056).

Limits worth stating. The study has 24 dogs, so the confidence interval on the effect is wide: the
data are consistent with an advantage anywhere from about 1.7 to about 7.8 %BW. The comparison is
against an active drug, not a placebo, so this says the new drug is better than the comparator, and
it does not separate drug effect from natural change over time within either arm. There is no
adverse-event, dose or owner-reported outcome in this dataset. Finally, these are simulated data
created for this analysis project, not measurements from real animals, so they support no clinical
claim.

## Data description

One CSV file, `pvf_repeated_measures.csv`, holds every repeated measurement. Nothing is averaged or
collapsed. It is generated by `make_data.py` with a fixed random seed (20260822), so re-running the
generator reproduces the file exactly.

**What one row represents:** one visit by one dog. A row is a single force-platform gait trial
summary for one dog at one scheduled visit. Each dog appears on exactly five rows, one per visit.
There are 120 data rows plus a header row, and no missing values.

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `dog_id` | string | none | Identifier for the individual dog, `D01` to `D24`. The same value repeats on the five rows belonging to that dog. This is the grouping variable that makes the rows non-independent, and the random effect in the primary model is fitted on it. |
| `treatment_arm` | string | none | Which analgesic the dog was assigned: `established` (comparator) or `new` (test). Constant across all five rows for a given dog. |
| `visit_week` | integer | weeks since baseline | Scheduled visit time: `0` (baseline, before treatment), `2`, `4`, `8`, `12`. |
| `body_weight_kg` | float, 1 decimal | kilograms | Body weight recorded at that visit, roughly 18 to 42 kg across the cohort, varying only slightly within a dog between visits. Not used in the primary model, because the outcome is already expressed as a percentage of body weight. |
| `peak_vertical_force_pctbw` | float, 2 decimals | percent of body weight (%BW) | Outcome. Peak vertical force through the affected forelimb during the trial, as a percentage of the dog's body weight. Higher means better weight-bearing on the affected limb. |

Design counts: 24 dogs, 12 per arm, 5 visits per dog, 120 rows, fully balanced.

## Files

- `pvf_repeated_measures.csv`: the data, one row per dog-visit.
- `make_data.py`: the generator that produced the CSV, standard library only, fixed seed.
- `analysis.py`: the single root analysis script.
- `DATA_DESCRIPTION.md`: the standalone data dictionary.
- `report.md`: this report.
