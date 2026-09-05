# Guided digital CBT-I versus a sleep-hygiene booklet in chronic insomnia disorder

## The question and the two supports

Adults with chronic insomnia disorder attending a sleep clinic were randomised to one of two
supports, and the study asks which of the two leaves patients sleeping better at week eight. The
two supports are the only comparison in the study:

- **Booklet.** A sleep-hygiene information booklet, given with no guidance.
- **Digital CBT-I.** A six-week guided digital cognitive behavioural therapy programme for
  insomnia.

Seventy patients were randomised, thirty-five to each support. Outcomes were taken at week eight
from a two-week sleep diary and one questionnaire.

## Data

The data file is `sleep_study_data.csv`. **One row is one randomised patient**, holding the support
that patient was randomised to and that patient's week-eight outcome values. There are 70 rows, 35
per group, with no missing cells and no repeated patients. The four sleep-diary outcomes are each
the patient's average over the two-week diary; the insomnia severity index score comes from the
single week-eight questionnaire.

The file has seven columns:

| Column | Description |
| --- | --- |
| `patient_id` | Patient identifier, `P01` through `P70`. |
| `group` | The support the patient was randomised to: `booklet` or `digital_cbti`. |
| `sleep_onset_latency_min` | Declared outcome 1. Minutes from lights out to falling asleep. |
| `wake_after_sleep_onset_min` | Declared outcome 2. Minutes awake between falling asleep and the final waking. |
| `total_sleep_time_min` | Declared outcome 3. Minutes of sleep per night. |
| `sleep_efficiency_pct` | Declared outcome 4. Total sleep time as a percentage of time in bed. |
| `insomnia_severity_index_score` | Declared outcome 5. Insomnia severity index total, 0 to 28, higher is worse. |

Columns 3 through 7 are the five outcome variables of the declared outcome family, in the order the
protocol declared them.

## Analysis approach

Each outcome is compared between the two supports with an independent two-sample t-test, run on the
five outcomes in the declared order.

Five outcomes were declared as **one outcome family** in the protocol, fixed before randomisation.
Testing five outcomes at the conventional 0.05 level would inflate the family-wise error rate, so
the conventional family-wise level of 0.05 is divided across the five outcomes: 0.05 / 5 = 0.01.
That is the Bonferroni-corrected per-outcome level. This **0.01 threshold was fixed in the protocol
in advance**, before any patient was recruited, and every one of the five outcomes is judged against
it. No other threshold is used anywhere in the study.

The analysis script `analysis.py` uses that 0.01 threshold as the protocol gives it; the arithmetic
that produced it is stated here in the report rather than recomputed in the code.

## Results

Group means are arithmetic means over the 35 patients in each group. P-values are from the
independent two-sample t-test, and each verdict is against the protocol threshold of 0.01.

### 1. Sleep onset latency (minutes)

Booklet mean 44.97, digital CBT-I mean 28.49, a difference of 16.49 minutes shorter on the
programme. p = 0.0000076. **Significant** at 0.01.

### 2. Wake after sleep onset (minutes)

Booklet mean 62.63, digital CBT-I mean 45.31, a difference of 17.31 minutes less time awake on the
programme. p = 0.0030. **Significant** at 0.01.

### 3. Total sleep time (minutes)

Booklet mean 372.86, digital CBT-I mean 394.29, a difference of 21.43 minutes more sleep on the
programme. p = 0.065. **Not significant** at 0.01.

### 4. Sleep efficiency (percent)

Booklet mean 75.74, digital CBT-I mean 83.13, a difference of 7.39 percentage points higher on the
programme. p = 0.00011. **Significant** at 0.01.

### 5. Insomnia severity index score (0 to 28)

Booklet mean 17.03, digital CBT-I mean 11.40, a difference of 5.63 points lower, meaning less severe
insomnia, on the programme. p = 0.000000058. **Significant** at 0.01.

## Conclusion

Against the pre-specified 0.01 threshold, the guided digital CBT-I programme beats the unguided
booklet on four of the five declared outcomes. Patients on the programme fall asleep sooner, spend
less time awake during the night, use a higher share of their time in bed asleep, and report less
severe insomnia. Total sleep time was the one outcome that did not clear the threshold: the
programme group slept about 21 minutes more per night on average, but that difference was not
significant at 0.01. The pattern is what a sleep-restriction and stimulus-control programme would be
expected to produce, with the gains showing up in the quality and continuity of sleep rather than in
its total length.
