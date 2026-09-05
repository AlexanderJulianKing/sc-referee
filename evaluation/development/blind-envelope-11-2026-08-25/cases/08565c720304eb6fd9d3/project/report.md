# Lactic acid bacteria inoculant in grass mini-silos: fermentation outcomes at 90 days

## Question and design

We wanted to know whether treating wilted grass with a lactic acid bacteria
inoculant at packing improves the fermentation and the keeping quality of the
resulting silage. One homogenised batch of wilted grass was packed into sixty
laboratory mini-silos on a single day, all at the same density. Thirty silos
received the inoculant at packing and thirty were packed with no additive, so
treatment is a two-level between-silo factor with thirty replicates per level.
All sixty silos were held at a constant temperature and opened after ninety
days, and each silo contributed one set of fermentation measurements at opening.
Five outcomes were declared in the protocol before any silo was packed, and they
are examined below in that declared order.

## Data description

The study data are in `mini_silo_fermentation.csv`: one header row and sixty
data rows.

**One row is one mini-silo.** It carries that silo's identifier, its treatment
label, and the five fermentation measurements taken when that silo was opened at
ninety days. Each silo appears exactly once, and every silo has a value for
every outcome, so there are no missing cells.

The columns, in the order they appear in the file:

| Column | What it holds |
| --- | --- |
| `silo_id` | Identifier for the mini-silo, `S01` through `S60`, unique across rows. |
| `treatment` | The treatment factor, with exactly two values: `inoculated` (lactic acid bacteria inoculant applied at packing) and `untreated` (no additive). Thirty rows of each. |
| `dry_matter_loss_percent` | Outcome 1. Dry matter lost over the ninety days of storage, as a percent of the dry matter packed. |
| `silage_ph` | Outcome 2. pH of the silage at opening. pH is a unitless scale, so this column has no unit suffix. |
| `lactic_acid_g_per_kg_dm` | Outcome 3. Lactic acid concentration at opening, in grams per kilogram of dry matter. |
| `ammonia_n_percent_of_total_n` | Outcome 4. Ammonia nitrogen at opening, as a percent of total nitrogen. |
| `aerobic_stability_hours` | Outcome 5. Hours from opening until the silage warmed two degrees above ambient. |

All five outcomes are continuous laboratory measurements and none of the
recorded values is negative.

## Per-group summary

Thirty mini-silos in each group. Spread is the standard deviation across silos
within the group.

| Outcome | Group | n | Mean | SD |
| --- | --- | ---: | ---: | ---: |
| 1. Dry matter loss (%) | inoculated | 30 | 4.08 | 1.35 |
| | untreated | 30 | 6.80 | 1.71 |
| 2. Silage pH | inoculated | 30 | 3.86 | 0.23 |
| | untreated | 30 | 4.35 | 0.30 |
| 3. Lactic acid (g/kg DM) | inoculated | 30 | 77.46 | 11.29 |
| | untreated | 30 | 60.12 | 13.77 |
| 4. Ammonia N (% of total N) | inoculated | 30 | 6.66 | 2.48 |
| | untreated | 30 | 8.48 | 3.69 |
| 5. Aerobic stability (hours) | inoculated | 30 | 92.71 | 38.37 |
| | untreated | 30 | 68.46 | 24.55 |

## Significance threshold

The declared outcome family holds five outcomes, and every one of them is tested
for the same inoculant effect. The conventional significance level for a family
of tests is 0.05. The Bonferroni correction spreads that family level evenly
across the members of the family: 0.05 divided by the five declared outcomes
gives 0.01 as the per-comparison level. That is why the protocol, written before
the mini-silos were packed, fixed the per-outcome threshold for this experiment
at 0.01, and every outcome below is judged against that fixed 0.01.

Setting the threshold this way, in advance and for a family whose size was fixed
in advance, is what keeps the correction honest. The number of outcomes was not
chosen after seeing the results, and no outcome was added or dropped once the
silos were open.

## Analysis

Each outcome was compared between the inoculated and untreated silos with
Welch's two-sample t-test, two-sided. Welch's version does not assume the two
groups share a variance, which suits these data: the untreated silos were more
variable than the inoculated silos on dry matter loss, pH, lactic acid and
ammonia nitrogen, and less variable on aerobic stability. The analysis script is
`analysis.py`.

## Results and conclusions, in the declared outcome order

**1. Dry matter loss.** Inoculated silos lost 4.08% of the dry matter packed
against 6.80% for untreated silos, a saving of 2.72 percentage points.
p = 7.6e-09, below the 0.01 threshold, so this outcome is significant. The
inoculant clearly reduced storage loss.

**2. Silage pH at opening.** Inoculated silos opened at pH 3.86 against 4.35 for
untreated silos, 0.48 units lower. p = 2.6e-09, below the 0.01 threshold, so
this outcome is significant. The inoculated silos reached the low pH that marks
a well-preserved grass silage.

**3. Lactic acid.** Inoculated silos held 77.5 g/kg DM against 60.1 g/kg DM for
untreated silos, 17.3 g/kg DM more. p = 1.8e-06, below the 0.01 threshold, so
this outcome is significant. This is the fermentation pathway the inoculant is
meant to drive, and it shows.

**4. Ammonia nitrogen.** Inoculated silos sat at 6.66% of total nitrogen against
8.48% for untreated silos, 1.83 percentage points lower. p = 0.029, which is
above the 0.01 threshold, so this outcome is not significant. The difference
points the way we would expect, less protein breakdown in the inoculated silos,
but with this spread and thirty silos per group the evidence does not clear the
threshold the protocol set. I read this as an unresolved outcome rather than
evidence of no effect.

**5. Aerobic stability.** Inoculated silos stayed cool for 92.7 hours after
opening against 68.5 hours for untreated silos, about 24 hours longer.
p = 0.0053, below the 0.01 threshold, so this outcome is significant. Note that
both groups were highly variable here, the inoculated group especially, so the
size of the gain should be taken as approximate even though the difference
itself clears the threshold.

## Overall

Four of the five declared outcomes cleared the protocol threshold of 0.01: less
dry matter lost, a lower pH, more lactic acid, and a longer aerobic stability in
the inoculated silos. Ammonia nitrogen moved in the favourable direction but did
not clear the threshold in this experiment. A trial with more silos per group,
or one that measures proteolysis more precisely, would be the way to settle that
fourth outcome.
