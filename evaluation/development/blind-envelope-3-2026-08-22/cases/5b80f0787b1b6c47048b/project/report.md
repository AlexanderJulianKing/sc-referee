# Pre-lambing mineral drench and total weaned lamb weight in hill ewes

## 1. Data description

The project contains one data file, `ewe_weaning_weights.csv`. It has a header row and 44 data
rows. The values are invented for this exercise.

**What one row represents.** One row is one ewe, recorded once at weaning. Each of the 44 ewes
appears in the file exactly once, so the 44 rows are 44 different animals and all 44 `ewe_id`
values are distinct. There are no repeated measurements, no lamb-level rows and no
before-and-after records. The row is the ewe, and the ewe is the experimental unit, because the
drench was given to the individual ewe.

**Columns.** All six columns are filled for all 44 rows; there are no missing values.

| Column | Type | Values in the file | Meaning |
| --- | --- | --- | --- |
| `ewe_id` | text | `E001`-`E022` (drenched), `E101`-`E122` (undrenched) | Unique identifier for the ewe. Appears once and only once. |
| `treatment` | text | `drenched`, `undrenched` | Whether the ewe received the pre-lambing mineral drench. |
| `lambs_weaned` | integer | 1 or 2 | Number of lambs that ewe weaned. |
| `ewe_age_years` | integer | 2 to 6 | Age of the ewe in years at lambing. |
| `body_condition_score` | number | 1.5 to 4.5 in half-point steps | Body condition score at mating, on the usual five-point scale. |
| `total_weaned_lamb_weight_kg` | number, one decimal | 25.1 to 56.0 | Outcome. Combined weight in kilograms of all lambs that ewe weaned. For a twin-rearing ewe this is the sum of both lambs. |

## 2. Flock and treatment

Forty-four ewes on a single hill farm were studied in one lambing season. Twenty-two ewes
received a mineral drench six weeks before lambing, and twenty-two received no drench. Each ewe
was in one group only, and group membership did not change during the trial, so the two groups
are independent sets of animals.

The two groups were similar in the background characteristics recorded. The drenched group had 15
twin-rearing ewes and 7 single-rearing ewes, a mean age of 4.0 years and a mean body condition
score at mating of 2.98. The undrenched group had 14 twin-rearing and 8 single-rearing ewes, a
mean age of 4.2 years and a mean body condition score of 3.07.

Every ewe was recorded once, at weaning. The single outcome recorded was the total weight of that
ewe's lambs at weaning, in kilograms.

## 3. Methods

The outcome was total weaned lamb weight per ewe, in kilograms. Because each ewe contributes
exactly one row and the drench was assigned to the individual ewe, the row and the experimental
unit are the same thing, and the two treatment groups were compared with an independent
two-sample t-test on the 44 ewe records. Welch's version of the test was used as the primary
analysis, since it does not assume the two groups share a variance. The equal-variance version was
run alongside it as a check.

Group means, standard deviations and ranges are reported, together with the difference in means, a
95 per cent confidence interval for that difference, and Cohen's d using the pooled standard
deviation. No covariate was adjusted for; the comparison reported here is the unadjusted
two-group comparison set out in the protocol, and the background characteristics in section 2 are
descriptive only.

Normality within each group was checked with the Shapiro-Wilk test, equality of variances with
Levene's test on medians, and the result was cross-checked with a Mann-Whitney U test. The
analysis is in `analysis.py` at the root of the project and was run with Python 3, pandas, numpy
and scipy.

## 4. Results

Twenty-two ewes were analysed in each group, 44 in total, with no exclusions and no missing
values.

| Group | Ewes | Mean total weaned lamb weight (kg) | SD (kg) | Range (kg) |
| --- | --- | --- | --- | --- |
| Drenched | 22 | 41.51 | 6.56 | 28.9-56.0 |
| Undrenched | 22 | 37.80 | 6.40 | 25.1-50.0 |

Drenched ewes weaned 3.70 kg more lamb than undrenched ewes on average. The standard error of that
difference was 1.95 kg and the 95 per cent confidence interval ran from -0.24 kg to 7.65 kg.
Welch's independent two-sample t-test gave t = 1.897 on 42.0 degrees of freedom, **p = 0.065**.
The equal-variance t-test gave the same result to three decimal places (t = 1.897 on 42 degrees of
freedom, p = 0.065), which is expected with equal group sizes and near-equal spreads. The
standardised effect size was Cohen's d = 0.57.

The assumptions held. Shapiro-Wilk gave p = 0.90 in the drenched group and p = 0.91 in the
undrenched group, so there is no sign of departure from normality. Levene's test gave p = 0.95, so
the two spreads are close, as the standard deviations of 6.56 and 6.40 kg already suggest. The
Mann-Whitney U test agreed with the t-test (U = 317.0, p = 0.080).

## 5. Conclusion

This trial did not show that the pre-lambing mineral drench increased total weaned lamb weight.
The drenched ewes weaned 3.70 kg more lamb on average, which would be worth having on a hill farm,
but the difference was not statistically significant at the 5 per cent level (p = 0.065) and the
95 per cent confidence interval includes zero.

The result should be read as inconclusive rather than as evidence of no effect. The interval runs
from a loss of 0.24 kg to a gain of 7.65 kg per ewe, so a commercially useful benefit is still
consistent with these data, and so is no benefit at all. With 22 ewes per group the trial has
limited power to settle a difference of this size: at the observed spread of about 6.5 kg, a
difference of 3.7 kg is close to the edge of what 44 ewes can detect. A larger trial, ideally
across more than one farm and more than one season, would be needed to decide whether the drench
is worth using. On the present evidence the drench cannot be recommended on the basis of weaned
lamb weight.
