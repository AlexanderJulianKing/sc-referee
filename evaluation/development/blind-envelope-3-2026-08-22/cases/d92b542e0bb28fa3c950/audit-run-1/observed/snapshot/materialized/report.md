# Fibre supplementation and gut microbial diversity in weaned piglets

## Data description

All analyses use the single comma-separated file `piglet_shannon.csv`, which has a header row and
110 data rows.

**One row is one faecal sample:** a single weekly collection taken from a single piglet on a single
study week. Each of the 22 piglets contributes five rows, one for each of the five consecutive study
weeks.

| column | type | what it holds |
| --- | --- | --- |
| `piglet_id` | text | Identifier of the animal the sample came from, `P01` through `P22`. |
| `ration` | text | Diet group of that piglet, `control` (starter ration alone) or `supplement` (same ration plus the fibre supplement). |
| `week` | integer | Study week in which the sample was collected, 1 through 5. |
| `shannon_diversity` | number | Shannon diversity index of the gut microbial community in that faecal sample. |
| `body_weight_kg` | number | Body weight of the piglet in kilograms on the day of that sampling. |
| `read_depth` | integer | Number of sequencing reads obtained for that faecal sample. |

There are no missing values. Every piglet has a complete set of five weekly samples.

## Animals and sampling schedule

Twenty-two weaned piglets were housed in individual pens for the duration of the study. Eleven
animals (`P01`–`P11`) received a control starter ration and eleven animals (`P12`–`P22`) received the
same starter ration with a fibre supplement added. Rations were fed continuously from weaning.

One faecal sample was collected from each piglet once a week for five consecutive weeks, giving 110
faecal samples in total, 55 per ration group. Each sample was sequenced and the Shannon diversity
index of the gut community was computed for it. Body weight was recorded on each sampling day and
rose from a group mean of 7.17 kg in week 1 to 14.11 kg in week 5. Sequencing depth averaged 45,738
reads per sample and ranged from 27,101 to 62,697 reads.

## Methods

Shannon diversity was compared between the two rations with an independent two-sample t-test assuming
equal variances. Every faecal sample collected over the five study weeks entered the test as a
separate observation, so the analysis is based on 110 samples, 55 in the control group and 55 in the
supplemented group. Group means, standard deviations, standard errors, the mean difference with its
95% confidence interval, Cohen's d, and the t-test result were computed. Descriptive summaries of
diversity by week and by ration, plus body weight and read depth by week, were produced alongside the
test.

The analysis was carried out in Python 3.9 using pandas 2.0.3 for data handling and SciPy 1.9.1
(`scipy.stats.ttest_ind`) for the test. The full analysis is in `analysis.py` at the project root and
reproduces every number below from `piglet_shannon.csv`.

## Results

Sample size for the comparison was n = 110 faecal samples (55 control, 55 supplement).

| ration | samples | mean Shannon | SD | SEM | min | max |
| --- | --- | --- | --- | --- | --- | --- |
| control | 55 | 3.2138 | 0.2123 | 0.0286 | 2.744 | 3.856 |
| supplement | 55 | 3.5692 | 0.2931 | 0.0395 | 2.882 | 4.263 |

Mean Shannon diversity was 0.3554 units higher on the supplemented ration than on the control ration.
The independent two-sample t-test gave t(108) = 7.283 with p = 5.59e-11. The 95% confidence interval
for the difference was 0.2587 to 0.4521, and the standardised effect size was Cohen's d = 1.39 with a
pooled SD of 0.2559.

The separation between rations was present at every time point. Weekly mean Shannon diversity was:

| week | control | supplement |
| --- | --- | --- |
| 1 | 3.112 | 3.568 |
| 2 | 3.193 | 3.569 |
| 3 | 3.210 | 3.545 |
| 4 | 3.218 | 3.571 |
| 5 | 3.337 | 3.592 |

Diversity also drifted upward slightly over the study in both groups: the overall weekly mean rose
from 3.340 in week 1 to 3.465 in week 5.

## Conclusion

The fibre supplement increased gut microbial diversity in weaned piglets. Across 110 faecal samples,
Shannon diversity averaged 3.57 on the supplemented ration against 3.21 on the control ration, a
difference of 0.36 diversity units that was highly significant (p = 5.59e-11) and large in magnitude
(d = 1.39). The advantage held in every one of the five study weeks. Adding the fibre supplement to a
standard starter ration is an effective way to raise gut community diversity through the post-weaning
period.
