# Cold therapy after impacted lower third molar removal

Randomised comparison of a continuous cold compress (worn for the first six hours after surgery,
29 patients) against an intermittent cold compress (twenty minutes on, twenty minutes off over the
same six hours, 29 patients).

## Data

File: `molar_cold_therapy.csv`. **One row is one patient**: the cold therapy schedule they were
allocated to and their six declared outcome measurements. 58 rows, 29 per arm, no missing values.

| Column | Unit | Meaning |
| --- | --- | --- |
| `patient_id` | none | Per-patient identifier, `P01` to `P58` |
| `cold_schedule` | none | Allocated schedule: `continuous` or `intermittent` |
| `swelling_d2_mm` | mm | Outcome 1 (primary). Facial swelling on day 2, increase over the pre-operative facial reference |
| `opening_d2_mm` | mm | Outcome 2 (primary). Maximum interincisal mouth opening on day 2 |
| `pain_d1_vas` | 0-100 VAS points | Outcome 3 (secondary). Worst pain on day 1 |
| `pain_d3_vas` | 0-100 VAS points | Outcome 4 (secondary). Worst pain on day 3 |
| `rescue_tabs_n` | count | Outcome 5 (secondary). Rescue analgesic tablets over the first three days |
| `diet_return_d` | days | Outcome 6 (secondary). Days until return to a normal diet |

Higher swelling, pain, tablet counts and diet-return days mean a worse recovery; higher mouth
opening means a better recovery.

## Methods

Each of the six pre-declared outcomes was compared between the two arms with a two-sided
two-sample t-test (`scipy.stats.ttest_ind`), reporting the group means, the t statistic and the
p-value.

The protocol named `swelling_d2_mm` and `opening_d2_mm` as the primary endpoints, so those are the
endpoints given multiplicity protection. Their two p-values were passed through the Holm procedure
(`statsmodels.stats.multitest.multipletests`, `method="holm"`), and their significance verdicts
were read from the Holm-adjusted p-values at the conventional 0.05 threshold.

The four secondary outcomes were each treated as their own separate pre-declared question, so each
secondary verdict comes from its raw p-value compared with the 0.05 threshold, exactly as measured.
No further adjustment was applied.

All numbers below are the output of `analysis.py` run on `molar_cold_therapy.csv`.

## Results

### Primary outcomes (Holm-adjusted across the two primaries)

| # | Outcome | Mean, continuous | Mean, intermittent | t | Raw p | Holm p | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `swelling_d2_mm` | 9.11 | 12.41 | -4.010 | 0.00018 | 0.00036 | **Significant** |
| 2 | `opening_d2_mm` | 34.00 | 30.00 | 2.576 | 0.0127 | 0.0127 | **Significant** |

Both primary endpoints favour the continuous compress and both stay significant after Holm
adjustment. Day 2 swelling was 3.30 mm lower with continuous cold, and day 2 mouth opening was
4.00 mm wider.

### Secondary outcomes (raw p-value, each judged on its own)

| # | Outcome | Mean, continuous | Mean, intermittent | t | p | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | `pain_d1_vas` | 46.97 | 51.07 | -1.113 | 0.2705 | Not significant |
| 4 | `pain_d3_vas` | 23.97 | 27.00 | -0.909 | 0.3672 | Not significant |
| 5 | `rescue_tabs_n` | 6.28 | 6.76 | -0.639 | 0.5262 | Not significant |
| 6 | `diet_return_d` | 3.34 | 3.66 | -1.007 | 0.3182 | Not significant |

All four secondary outcomes point in the same direction as the primaries, with the continuous arm
slightly better on each, but none reaches the 0.05 threshold: 4.10 fewer VAS points on day 1, 3.03
fewer on day 3, 0.48 fewer rescue tablets, and 0.31 fewer days to a normal diet.

## Clinical interpretation

In this trial, wearing the cold compress continuously through the first six postoperative hours
gave a measurably better day 2 recovery than the twenty-on/twenty-off schedule on both protected
endpoints. The swelling difference of about 3.3 mm and the mouth opening difference of about 4 mm
are the size of effect an oral surgeon would notice at the day 2 review, and both survive the
adjustment applied across the two primary endpoints.

The comfort and function measures tell a softer story. Pain scores on day 1 and day 3, rescue
tablet use, and time back to a normal diet all lean toward continuous cold, but each difference is
small relative to the patient-to-patient scatter and none is statistically significant on its own
pre-declared test. With 29 patients per arm, differences of this size would not be expected to
separate reliably, so these results are best read as consistent with the primary findings rather
than as evidence of an analgesic benefit.

Practically, the trial supports advising continuous cold application over the first six hours where
the patient can tolerate it, on the grounds of less day 2 swelling and better mouth opening, while
setting the expectation that early pain and analgesic use will be much the same either way.
