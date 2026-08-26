# Hay rack or forage block? What eight weeks in 34 pet guinea pigs told us

*From the practice feeding-study group. Methods appendix at the end.*

Hay is the whole diet argument in guinea pig medicine. We keep telling owners it
has to be the bulk of the bowl, and owners keep telling us their pig ignores the
rack and scatters it across the hutch. Compressed forage blocks are marketed as
the tidy answer. We wanted to know whether the animal chewing that block is
doing the same dental work as the animal pulling long stems off a rack.

Thirty-four adult guinea pigs, each from a different household, took part for
eight weeks. Seventeen were fed long-stem hay from an open rack, seventeen were
fed the same hay compressed into forage blocks. Nothing else in the diet
differed. At the end of the eight weeks every animal was weighed, examined under
sedation, and had two days of intake and output recorded at home by its owner on
scales we supplied.

## What is in the data file

The analysis reads one file, `guinea_pig_hay_study.csv`. **One row is one guinea
pig**: a single adult animal from a single household, carrying its feeding
treatment and its six end-of-study measurements. Each animal appears exactly
once, and every animal has a value in every column, so there are no blanks. The
file holds 34 data rows plus a header row, and eight columns.

| Column | Unit | What it holds |
| --- | --- | --- |
| `animal_id` | none (text label) | Study identifier for the animal, `GP01` through `GP34`. Unique across rows. |
| `group` | none (text label) | Feeding treatment, with exactly two possible entries: `hay_rack` (long-stem hay from an open rack) and `forage_block` (the same hay compressed into blocks). 17 animals in each. |
| `hay_intake_g_day` | grams per day | Daily hay dry matter intake, averaged over the two recorded days. |
| `body_weight_g` | grams | Body weight at the end of the eight weeks, from the sedated examination. |
| `faecal_output_g_day` | grams per day | Daily faecal output, averaged over the two recorded days. |
| `faecal_particle_mm` | millimetres | Median faecal particle size, our marker of how finely the animal chewed its hay. |
| `chewing_min_day` | minutes per day | Time spent chewing, scored from video of one recorded day. |
| `occlusal_angle_deg` | degrees | Cheek tooth occlusal angle, measured on the intraoral photographs. |

The six outcome columns appear in the order the protocol declared them, and the
results below are reported in that same order.

## Results, outcome by outcome

Each of the six outcomes was declared as a question in its own right, so each
one gets its own answer at the conventional five percent threshold.

**1. Daily hay dry matter intake (g/day).** Hay rack 56.14, forage block 55.42,
a difference of 0.72 g/day. p = 0.84. The two groups ate essentially the same
amount of hay.

**2. End-of-study body weight (g).** Hay rack 960.18, forage block 1003.94, a
difference of -43.76 g. p = 0.39. No detectable weight difference between
presentations.

**3. Daily faecal output (g/day).** Hay rack 43.15, forage block 44.11, a
difference of -0.96 g/day. p = 0.74. What went in came out at the same rate in
both groups, which fits the matched intake above.

**4. Median faecal particle size (mm).** Hay rack 0.81, forage block 1.16, a
difference of -0.35 mm. p = 0.0000055. Block-fed animals passed noticeably
coarser particles, so they were breaking the hay down less finely.

**5. Time spent chewing per day (min/day).** Hay rack 205.65, forage block
160.76, a difference of 44.88 minutes. p = 0.00015. Rack-fed animals spent
roughly three quarters of an hour more per day with their jaws working.

**6. Cheek tooth occlusal angle (degrees).** Hay rack 30.01, forage block 32.38,
a difference of -2.37 degrees. p = 0.047. The block-fed animals sat at a steeper
occlusal angle, the direction we associate with less even wear.

## What it means for the consulting room

Hay presentation did not change how much the animals ate, what they weighed, or
how much they passed. Intake, weight and output came out flat across the two
groups. The differences were all in *how* the hay was processed and what that
did to the teeth: block-fed pigs chewed about 45 minutes less per day, passed
coarser faecal particles, and finished the eight weeks with a steeper cheek
tooth occlusal angle.

Practical advice for owners: forage blocks are a reasonable way to keep hay
intake up and the hutch tidy, but they are not a substitute for long-stem hay
when it comes to dental wear. Where an animal is on blocks, we suggest keeping a
rack of long-stem hay available alongside it, and we would not present blocks as
the only hay source in a pig with any existing cheek tooth abnormality. The
weight and output results are reassuring, so an owner switching for practical
reasons is not risking condition; the trade-off is chewing time, not nutrition.

Two honest limits. The occlusal angle result sits just under the threshold
(p = 0.047), so it is the weakest of the three findings and would want repeating
in a larger group before we lean on it hard. And eight weeks is short next to
the years over which cheek tooth problems actually develop.

---

## Methods appendix

**Design.** Thirty-four adult guinea pigs, one per household, allocated 17 to
long-stem hay from an open rack and 17 to compressed forage blocks, fed for
eight weeks. Six outcomes measured on every animal at the end of the study, in
the protocol's declared order: daily hay dry matter intake, end-of-study body
weight, daily faecal output, median faecal particle size, daily chewing time
from video scoring of one recorded day, and cheek tooth occlusal angle from
intraoral photographs. Intake and output are the mean of two owner-recorded
days.

**Analysis.** Each declared outcome was analysed separately. For every outcome
the two feeding treatments were compared with a two-sample (Welch) t-test on the
34 animal values, and the outcome was called significant at the conventional
five percent threshold (alpha = 0.05). The animal is the unit of analysis
throughout, and each animal contributes one value per outcome.

**No multiple-comparison adjustment was applied.** Each of the six outcomes was
declared in the protocol as a question in its own right and carries its own
conclusion at the conventional threshold, so the p-values above are unadjusted.

**Software.** The analysis is a single script, `analysis.py`, in the project
root. It reads `guinea_pig_hay_study.csv`, builds one collection of per-outcome
results in a single pass over the declared outcome list, and prints the two
treatment means, the difference and the p-value for each outcome in the declared
order. It uses pandas for the table and `scipy.stats.ttest_ind` (with
`equal_var=False`) for the comparison. Run it from the project root with
`python analysis.py`.

**Full result table as printed by the script:**

| Outcome | Unit | Mean rack | Mean block | Difference | p-value | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Daily hay dry matter intake | g/day | 56.14 | 55.42 | 0.72 | 0.8415 | not significant |
| End-of-study body weight | g | 960.18 | 1003.94 | -43.76 | 0.3876 | not significant |
| Daily faecal output | g/day | 43.15 | 44.11 | -0.96 | 0.7385 | not significant |
| Median faecal particle size | mm | 0.81 | 1.16 | -0.35 | 0.0000055 | significant |
| Time spent chewing per day | min/day | 205.65 | 160.76 | 44.88 | 0.00015 | significant |
| Cheek tooth occlusal angle | deg | 30.01 | 32.38 | -2.37 | 0.0470 | significant |

Difference is the hay rack mean minus the forage block mean.
