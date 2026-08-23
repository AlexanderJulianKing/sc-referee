# Post-treatment faecal egg counts after two anthelmintic drenches in yearling dairy goats

## Data description

The analysis uses one comma-separated file, `faecal_egg_counts.csv`, with a header row and 60 data
rows.

**What one row represents.** One row is one counting slide: a single McMaster egg count read from one
goat's faecal sample. Each of the 20 goats gave one faecal sample 14 days after treatment, and the
same technician counted that one sample three separate times on three slides. Each goat therefore
appears on three rows that differ only in the slide number and in the slide-to-slide counting
variation of the post-treatment count.

**Columns, in file order.**

| Column | Type | What it holds |
|---|---|---|
| `goat_tag` | text | Ear-tag identifier of the goat, given as year of birth plus animal number (for example `25-037`). There are 20 distinct tags and each appears on exactly 3 rows. |
| `drench_group` | text | The drench the goat was randomised to: `benzimidazole` or `macrocyclic_lactone`. It is the same on all three of a goat's rows. |
| `slide_replicate` | integer | Which of the three counting slides this row is: 1, 2 or 3. It labels a laboratory repeat of the same faecal sample. |
| `pre_treatment_epg` | integer | The goat's pre-treatment faecal egg count in eggs per gram, taken before drenching. One value per goat, repeated identically on that goat's three rows. Values run from 850 to 2200. |
| `post_treatment_epg` | integer | The egg count in eggs per gram read from this particular slide, 14 days after treatment. This is the outcome. Values run from 50 to 700. |

Counts come from the McMaster technique with a counting factor of 25 eggs per gram, so every egg
count in the file is a whole number and a multiple of 25.

## Methods

Twenty yearling dairy goats from one herd were randomised individually to one of two drenches, ten
per drench. The outcome is `post_treatment_epg`, the faecal egg count 14 days after treatment.

The two drenches were compared with an independent two-sample test of the difference in means
(Welch's t-test, which does not assume the two groups share a variance). Every counting slide in the
table was entered into the comparison as a separate observation, giving 60 counts analysed, 30 per
drench. Each group is summarised by its mean, standard deviation and standard error, together with
the range of counts. The difference in means is reported with a 95% confidence interval. The
significance level is 0.05. The analysis was run in Python with pandas and SciPy; `analysis.py`
reproduces every number below.

## Results

Sixty counts were analysed, 30 per drench.

| Group | Counts | Mean epg | SD | SEM | Min | Max |
|---|---|---|---|---|---|---|
| `benzimidazole` | 30 | 494.2 | 140.1 | 25.6 | 275 | 700 |
| `macrocyclic_lactone` | 30 | 154.2 | 57.3 | 10.5 | 50 | 250 |

Mean pre-treatment counts were 1535.0 epg in the benzimidazole arm and 1342.5 epg in the macrocyclic
lactone arm. Against those pre-treatment means, the faecal egg count reduction was 67.8% for the
benzimidazole drench and 88.5% for the macrocyclic lactone drench.

The macrocyclic lactone arm left post-treatment counts 340.0 epg lower than the benzimidazole arm
(95% CI 284.1 to 395.9 epg). Welch's independent two-sample t-test gives t = 12.301 on 38.4 degrees
of freedom, p = 6.76e-15. The difference between the two drenches is significant at the 0.05 level.

## Efficacy conclusion and recommendation

The macrocyclic lactone drench is the more efficacious of the two products in this herd. It cut the
faecal egg count by 88.5% and left a mean of 154.2 epg at day 14, while the benzimidazole cut counts
by only 67.8% and left a mean of 494.2 epg.

Both figures sit below the 95% reduction expected of a fully effective drench, and the benzimidazole
result is far below it. The practical reading is that the herd's nematode population carries
substantial benzimidazole resistance, with reduced macrocyclic lactone efficacy alongside it.

Recommendations for the herd:

1. Stop using the benzimidazole drench as a standalone treatment in this age group. At a 67.8%
   reduction it is not clearing the burden and it will keep selecting for resistance.
2. Use the macrocyclic lactone as the working product for the yearlings for now, dosing to accurate
   individual bodyweight and checking the drench gun's delivered volume before each round.
3. Repeat a faecal egg count reduction test on the macrocyclic lactone at the next treatment, and
   consider a combination or a different drench class if the reduction stays below 95%.
4. Keep a proportion of the group untreated as refugia, and quarantine-drench and test all incoming
   stock so no further resistant worms enter the herd.
