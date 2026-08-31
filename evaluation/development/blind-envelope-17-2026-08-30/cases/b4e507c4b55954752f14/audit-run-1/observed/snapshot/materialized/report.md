# Sit-stand workstation evaluation

Occupational health team, claims processing site. Internal evaluation summary.

## Aim and conditions

We evaluated height-adjustable sit-stand workstations for desk-based claims processors.
Fifty-six employees doing the same job at the same site took part for twelve weeks. The
two workstation conditions were:

- **fixed desk** — 28 employees continued at their existing fixed-height desks;
- **sit-stand** — 28 employees received a height-adjustable sit-stand workstation together
  with a short training session.

These two conditions are the only comparison in the evaluation. Measurements were taken
over the final working week, from the questionnaires, the chair-and-desk posture logger
and the keyboard software.

## Data

The data file is `workstation_evaluation.csv`. **One row is one employee.** All 56
employees appear exactly once, 28 in each condition, with no missing cells and no extra
rows. The columns are:

| Column | What it holds |
|--------|---------------|
| `employee_id` | employee identifier, `EMP` prefix plus a zero-padded two-digit serial |
| `workstation_group` | workstation condition, either `fixed_desk` or `sit_stand` |
| `neck_shoulder_discomfort_0_10` | neck and shoulder discomfort over the past week, 0 to 10 rating scale, higher is worse |
| `lower_back_discomfort_0_10` | lower-back discomfort over the past week, 0 to 10 rating scale, higher is worse |
| `sitting_time_min` | sitting time during the working day, in minutes |
| `sit_to_stand_changes_per_day` | number of sit-to-stand posture changes per working day, a count |
| `end_of_day_fatigue_0_10` | end-of-day fatigue, 0 to 10 scale, higher is worse |
| `typing_throughput_kpm` | typing throughput, keystrokes per minute during logged work |
| `work_engagement_0_6` | work engagement, 0 to 6 questionnaire scale, higher means more engaged |

Columns three to nine are the seven declared outcome variables, in the order fixed in the
evaluation protocol before the workstations were installed.

## How the comparison was done

All of the analysis is in `analysis.py`. For each of the seven declared outcomes, in the
declared order, the two workstation conditions were compared with an independent
two-sample t-test.

The protocol distinguishes two kinds of outcome, and we treated them differently.

- The **three musculoskeletal outcomes** — neck and shoulder discomfort, lower-back
  discomfort and sitting time — are what the evaluation was commissioned to answer. Their
  p-values were corrected by hand in the script: each raw p-value was multiplied by 7, the
  number of comparisons made in this evaluation, and any product above one was capped at
  one. These three outcomes were judged against the conventional 0.05 threshold using the
  corrected values.
- The **four supporting outcomes** — sit-to-stand posture changes, end-of-day fatigue,
  typing throughput and work engagement — were each judged against the conventional 0.05
  threshold using their own raw p-value, exactly as the test produced it.

## Results

Each outcome below is given in the declared order, with the mean for each condition, the
p-value used to judge it, and the verdict at the 0.05 threshold.

**1. Neck and shoulder discomfort (0-10)** — fixed desk 4.79, sit-stand 3.64.
Raw p = 0.0248; corrected p = 0.1734. **Not significant.**

**2. Lower-back discomfort (0-10)** — fixed desk 4.07, sit-stand 3.25.
Raw p = 0.0845; corrected p = 0.5912. **Not significant.**

**3. Sitting time (minutes per working day)** — fixed desk 371.64, sit-stand 293.04.
Raw p = 0.00000099; corrected p = 0.0000069. **Significant.**

**4. Sit-to-stand posture changes (per working day)** — fixed desk 8.82, sit-stand 17.18.
Raw p = 0.000000000021. **Significant.**

**5. End-of-day fatigue (0-10)** — fixed desk 5.25, sit-stand 4.57.
Raw p = 0.0998. **Not significant.**

**6. Typing throughput (keystrokes per minute)** — fixed desk 209.77, sit-stand 205.41.
Raw p = 0.5863. **Not significant.**

**7. Work engagement (0-6)** — fixed desk 3.89, sit-stand 4.08.
Raw p = 0.4069. **Not significant.**

## Conclusion

The sit-stand workstations changed how employees spent the working day. Employees with a
sit-stand workstation sat about 79 minutes less per working day and made about twice as
many sit-to-stand posture changes, roughly 17 against 9. Both of these differences are
significant on the tests as judged above.

The discomfort ratings moved in the expected direction, with sit-stand employees reporting
about 1.1 points less neck and shoulder discomfort and about 0.8 points less lower-back
discomfort, but neither reached significance once the correction for the seven comparisons
was applied. End-of-day fatigue was also lower in the sit-stand group, by about 0.7 points,
without reaching the threshold. Typing throughput and work engagement were close between
the two conditions, so there is no sign here that the workstations cost the team any
output.

**Recommendation to the employer.** The behaviour change is clear and the productivity
measures show no penalty, so continuing with sit-stand workstations for desk-based claims
processors is reasonable on those grounds. The comfort benefit, which is the outcome the
evaluation was commissioned to answer, is suggested by the data but not established at
this sample size. If the employer wants an answer on discomfort, a larger group or a
longer follow-up would be needed. We would also keep the short training session in any
rollout, since that was part of the condition tested here.
