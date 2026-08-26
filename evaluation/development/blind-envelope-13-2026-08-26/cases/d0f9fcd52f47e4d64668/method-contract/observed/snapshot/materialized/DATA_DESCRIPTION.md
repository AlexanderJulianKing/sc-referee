# Data description

File: `ibs_dietary_advice.csv`

Outpatient gastroenterology service evaluation comparing two dietary advice
programmes in adults with irritable bowel syndrome. Sixty-two adults took part,
31 in each programme, and each person was assessed once after six weeks of
follow-up.

**One row = one participant, holding that person's group allocation and their
five protocol-declared outcome measurements taken at the single six-week
assessment.** There are 62 data rows plus a header row. Every cell is filled;
there are no blanks.

## Columns

| Column | Meaning | Scale / unit |
| --- | --- | --- |
| `participant_id` | Study identifier for the participant | Text label, `P001` to `P062`, unique per row |
| `advice_group` | Dietary advice programme the participant received | Two values only: `low_fodmap_advice` (structured dietitian-delivered advice to reduce fermentable carbohydrates) and `standard_healthy_eating` (standard healthy-eating advice) |
| `symptom_severity_score_0_500` | Total symptom severity score at six weeks (declared outcome 1) | Integer, 0 to 500 scale; higher means worse symptoms |
| `worst_abdominal_pain_0_10` | Worst abdominal pain in the past week (declared outcome 2) | Integer, 0 to 10 numeric rating scale; higher means worse pain |
| `bloating_days_per_week` | Number of days with bloating in the past week (declared outcome 3) | Integer count of days, 0 to 7 |
| `stool_consistency_bristol_1_7` | Mean stool consistency over the assessment week (declared outcome 4) | Number to one decimal place, Bristol Stool Form Scale 1 to 7; 1 is hardest, 7 is loosest |
| `quality_of_life_score_0_100` | Disease-specific quality of life score at six weeks (declared outcome 5) | Integer, 0 to 100 scale; higher is better |

Columns appear in this order in the file, and the five outcome columns follow
the order in which they were declared in the study protocol.

## Provenance

The measurements are invented for this exercise, not collected from patients.
They were produced by `generate_data.py` (fixed random seed 20260826), which
draws each outcome from a normal distribution per group, clips values to the
scale limits, and rounds counts and scale scores to their natural precision.
Group sizes are balanced at 31 and 31.
