# Night wrist splinting in mild to moderate carpal tunnel syndrome

A hand therapy service compared night wrist splinting with no splinting in adults with mild to
moderate carpal tunnel syndrome. This report describes the data, the analysis method, and the
results for the five outcomes the protocol declared before recruitment.

## Data

**File:** `carpal_tunnel_splint_trial.csv`, one comma separated file with a header row.

**What one row is:** one adult participant, holding that person's group allocation and their single
end-of-week-six assessment. Each participant was assessed once, so there is exactly one row per
participant and no repeated measures.

**Columns:**

| # | Column | Description |
|---|--------|-------------|
| 1 | `participant_id` | Unique participant label, `P001` through `P066`, in enrollment order. |
| 2 | `allocation` | Group assignment, either `night_splint` or `no_splint`. |
| 3 | `symptom_severity_score` | Declared outcome 1. Symptom severity, 1 to 5 scale, one decimal place; higher is worse. |
| 4 | `functional_status_score` | Declared outcome 2. Functional status, 1 to 5 scale, one decimal place; higher means more difficulty with everyday hand tasks. |
| 5 | `night_awakenings_per_week` | Declared outcome 3. Whole nights in the past week with symptom-related awakening, 0 to 7. |
| 6 | `two_point_discrimination_mm` | Declared outcome 4. Static two-point discrimination at the index fingertip in millimetres, recorded on a 0.5 mm grid; higher means coarser sensation. |
| 7 | `distal_motor_latency_ms` | Declared outcome 5. Distal motor latency of the median nerve in milliseconds, two decimal places; higher means slower conduction. |

Columns 3 through 7 appear in the order the protocol declared the five outcomes. Every participant
has a value for every outcome, and there are no blank cells.

## Design and groups

Sixty-six adults were allocated to one of two groups. Thirty-three wore a neutral-position night
splint on the affected wrist for six weeks (`night_splint`). Thirty-three received the same advice
and ergonomic education without a splint (`no_splint`). All 66 participants were assessed once at
the end of week six, and the same five measurements were recorded for everyone.

## Methods

Each of the five declared outcomes was compared between the two groups with a two-sample Welch
t-test, which compares two independent groups without assuming their variances are equal. For each
outcome the analysis reports the mean in each group, the difference between the group means
(`night_splint` minus `no_splint`), and the p-value.

The protocol fixed the per-outcome significance threshold at 0.01 in advance, before recruitment.
The reason for that value is that 0.01 is the Bonferroni-corrected level for the five declared
outcomes at a conventional family-wise level of 0.05: dividing 0.05 by the five outcomes in the
declared family gives 0.01. Testing every outcome in the family at 0.01 therefore controls the
family-wise error rate across the declared family at 0.05. Because the threshold was set this way in
advance, the analysis applies no further correction of any kind. It simply compares each outcome's
p-value with the fixed value of 0.01, and an outcome counts as significant only when its p-value is
below 0.01.

The full outcome family of five was analysed as declared, in the declared order, with no outcome
added or dropped.

## Results

Group means, the difference between them, and the p-value for each declared outcome, in the declared
order. Verdicts are against the protocol's fixed 0.01 threshold.

| # | Outcome | Mean, `night_splint` (n=33) | Mean, `no_splint` (n=33) | Difference | p-value | Verdict at p < 0.01 |
|---|---------|-----------------------------|--------------------------|------------|---------|---------------------|
| 1 | `symptom_severity_score` | 2.40 | 3.12 | -0.72 | 0.0000085 | Significant |
| 2 | `functional_status_score` | 2.46 | 2.79 | -0.33 | 0.017 | Not significant |
| 3 | `night_awakenings_per_week` | 2.09 | 3.94 | -1.85 | 0.000027 | Significant |
| 4 | `two_point_discrimination_mm` | 5.08 | 5.17 | -0.09 | 0.77 | Not significant |
| 5 | `distal_motor_latency_ms` | 4.58 | 4.67 | -0.09 | 0.60 | Not significant |

Conclusion for each outcome:

1. **Symptom severity score.** The splint group scored 0.72 points lower, and the p-value of
   0.0000085 is below 0.01. This outcome meets the protocol threshold.
2. **Functional status score.** The splint group scored 0.33 points lower, with a p-value of 0.017.
   This p-value falls between 0.01 and 0.05, so it does not meet the protocol threshold of 0.01, and
   the outcome is not significant under the pre-specified rule.
3. **Night awakenings per week.** The splint group woke on 1.85 fewer nights in the past week, and
   the p-value of 0.000027 is below 0.01. This outcome meets the protocol threshold.
4. **Two-point discrimination.** The two groups differ by 0.09 mm, with a p-value of 0.77. The
   groups are effectively the same on this outcome, which does not meet the protocol threshold.
5. **Distal motor latency.** The two groups differ by 0.09 ms, with a p-value of 0.60. The groups
   are effectively the same on this outcome, which does not meet the protocol threshold.

## Clinical interpretation

Six weeks of night splinting was associated with better patient-reported symptoms and with fewer
disturbed nights. The 0.72 point difference on the 1 to 5 symptom severity scale and the reduction
of about 1.85 disturbed nights per week are the kind of change a patient would notice, and both
outcomes clear the pre-specified 0.01 threshold.

Self-reported hand function moved in the same direction, by 0.33 points, but its p-value of 0.017
sits between 0.01 and 0.05 and so does not meet the protocol threshold. This outcome is reported as
not significant. It is a reasonable signal to carry into a future study rather than a result to act
on here.

The two objective measures of nerve status show no group difference worth noting. Two-point
discrimination differed by 0.09 mm, which is smaller than the 0.5 mm grid the caliper is read on,
and distal motor latency differed by 0.09 ms. Over six weeks, night splinting in this sample eased
what patients felt and how they slept without a measurable change in sensory threshold or median
nerve conduction.

Two limitations bear on how far these results carry. Each participant was measured once, at the end
of week six, so the analysis compares end-of-study groups rather than change from baseline within a
person. The study also has no long-term follow-up, so nothing here speaks to whether the symptom and
sleep benefits persist after splint wear stops.
