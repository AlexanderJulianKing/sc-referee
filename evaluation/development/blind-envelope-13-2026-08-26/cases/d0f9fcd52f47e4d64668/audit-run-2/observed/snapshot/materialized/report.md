# Dietary advice for irritable bowel syndrome: six-week service evaluation

## Data

The data file is `ibs_dietary_advice.csv`. **One row is one participant**: it
holds that person's study identifier, the dietary advice programme they
received, and their five protocol-declared outcome measurements taken at the
single six-week assessment. There are 62 data rows plus a header row, 31
participants per programme, and no blank cells.

| Column | Meaning | Scale / unit |
| --- | --- | --- |
| `participant_id` | Study identifier for the participant | Text label, `P001` to `P062`, unique per row |
| `advice_group` | Dietary advice programme received | Two values: `low_fodmap_advice` (structured dietitian-delivered advice to reduce fermentable carbohydrates) and `standard_healthy_eating` (standard healthy-eating advice) |
| `symptom_severity_score_0_500` | Total symptom severity score at six weeks (declared outcome 1) | Integer, 0 to 500; higher means worse symptoms |
| `worst_abdominal_pain_0_10` | Worst abdominal pain in the past week (declared outcome 2) | Integer, 0 to 10 numeric rating scale; higher means worse pain |
| `bloating_days_per_week` | Days with bloating in the past week (declared outcome 3) | Integer count of days, 0 to 7 |
| `stool_consistency_bristol_1_7` | Mean stool consistency over the assessment week (declared outcome 4) | One decimal place, Bristol Stool Form Scale 1 to 7; 1 is hardest, 7 is loosest |
| `quality_of_life_score_0_100` | Disease-specific quality of life at six weeks (declared outcome 5) | Integer, 0 to 100; higher is better |

The measurements are invented for this exercise, not collected from patients.

## Method

Each of the five declared outcomes was compared between the two programmes
with a two-sample Student t-test (equal variances assumed), the same test for
every outcome. `analysis.py` prints group sizes, group means, the t statistic
and the p-value for each outcome.

The first three outcomes, symptom severity, abdominal pain and bloating days,
are the ones the service will quote to commissioners. Their p-values were
corrected by hand in the script: each raw p-value was multiplied by 3, the
number of comparisons in that corrected set, and capped at 1. Verdicts for
those three outcomes are based on the corrected values at the conventional
0.05 threshold. For stool consistency and quality of life the raw p-values are
reported, each with a straightforward significant or not significant verdict at
0.05.

Group sizes were 31 in `low_fodmap_advice` and 31 in `standard_healthy_eating`.

## Results

### 1. Total symptom severity score (0 to 500)

Mean 208.935 with low FODMAP advice against 234.871 with standard healthy
eating, a difference of -25.935 points in favour of the low FODMAP programme.
t = -1.3059, raw p = 0.1966, corrected p = 0.5897.

**Verdict: not significant** (corrected p = 0.5897).

Clinically, a 26-point drop on a 0 to 500 severity scale is smaller than the
50-point change usually treated as a meaningful improvement, and the corrected
p-value gives no support for a real difference in overall symptom burden. This
result should not be presented as evidence that either programme lowers total
symptom severity more than the other.

### 2. Worst abdominal pain in the past week (0 to 10)

Mean 3.774 with low FODMAP advice against 4.903 with standard healthy eating, a
difference of -1.129 points. t = -2.5654, raw p = 0.0128, corrected p = 0.0385.

**Verdict: significant** (corrected p = 0.0385).

Clinically, just over one point lower on a 0 to 10 pain rating scale is around
the size of change patients typically notice, so this points to a real
reduction in worst weekly pain for people given structured advice to reduce
fermentable carbohydrates. It is the strongest of the three commissioner-facing
outcomes.

### 3. Days with bloating in the past week (0 to 7)

Mean 2.774 days with low FODMAP advice against 3.806 days with standard healthy
eating, a difference of -1.032 days. t = -2.2822, raw p = 0.0260, corrected
p = 0.0781.

**Verdict: not significant** (corrected p = 0.0781).

Clinically, one fewer bloating day per week would matter to patients, and the
direction favours the low FODMAP programme. But once the p-value is corrected
for the three commissioner-facing comparisons it sits above 0.05, so this
should be described as a promising signal that this study was not large enough
to confirm, not as an established benefit.

### 4. Mean stool consistency (Bristol 1 to 7)

Mean 4.174 with low FODMAP advice against 3.913 with standard healthy eating, a
difference of 0.261 Bristol points. t = 1.0518, raw p = 0.2971.

**Verdict: not significant** (raw p = 0.2971).

Both group means sit near the middle of the Bristol scale, in the normal stool
range of types 3 to 5, and a quarter-point difference is well inside normal
week-to-week variation. Neither programme appears to shift stool form.

### 5. Disease-specific quality of life (0 to 100)

Mean 74.290 with low FODMAP advice against 67.677 with standard healthy eating,
a difference of 6.613 points in favour of the low FODMAP programme. t = 2.0801,
raw p = 0.0418.

**Verdict: significant** (raw p = 0.0418).

Clinically, roughly seven points higher on a 0 to 100 disease-specific quality
of life score is a modest but patient-relevant gain, covering things like food
worry and daily activity limits. Note that this verdict rests on the raw
p-value, which sits only just below the 0.05 threshold; it was not adjusted for
the other declared comparisons, so it is the least secure of the significant
findings here.

## Conclusion

At six weeks, structured dietitian-delivered advice to reduce fermentable
carbohydrates did better than standard healthy-eating advice on worst weekly
abdominal pain, which stayed significant after correction across the three
commissioner-facing outcomes, and on disease-specific quality of life on its
raw p-value. Bloating days moved in the same direction by about one day per
week but did not clear the 0.05 threshold once corrected. Total symptom
severity and stool consistency showed no difference between the programmes.

On this evidence the service should offer the structured low FODMAP advice
programme as the first-line option for adults with irritable bowel syndrome,
while being clear to commissioners that the demonstrated gains are in pain and
quality of life rather than in total symptom severity, and that the bloating
result is suggestive only. A larger evaluation would be needed to settle the
bloating and overall severity questions.
