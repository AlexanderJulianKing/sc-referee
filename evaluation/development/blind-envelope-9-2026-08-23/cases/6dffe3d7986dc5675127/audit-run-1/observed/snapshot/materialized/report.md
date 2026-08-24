# Overwinter body-mass loss in West European hedgehogs: suburban gardens versus rural farmland

## What we did

We tagged 40 adult hedgehogs and followed them through a single winter, 20 in suburban
gardens and 20 on rural farmland. Every animal was weighed once shortly before it went
into hibernation and once shortly after it emerged. We turned each animal's pair of
weights into one number, the percentage change in body mass across the winter, and that
single number per animal is what we analysed.

## The data

The study produced one data file, `hedgehog_overwinter_mass.csv`, with 40 rows and 4
columns.

**One row is one hedgehog.** Each of the 40 tagged animals appears exactly once. No
animal was measured more than once in this table and no animal appears in more than one
row. The two weighings we took on each animal were reduced to a single percentage before
the table was written, so the raw before-and-after weights are not separate rows. Every
animal stayed in one landscape for the whole winter, so the two groups share no animals.

Every column in the file:

| Column | Type | Units | What it holds |
|---|---|---|---|
| `hedgehog_id` | text | none | The animal's tag code, `HH-01` through `HH-40`. This identifies the animal, and it is unique: 40 codes across 40 rows. Tag numbers were issued at capture and say nothing about landscape. |
| `landscape` | text, 2 categories | none | Where the animal was tracked: `suburban_garden` or `rural_farmland`. 20 animals in each. |
| `pre_hibernation_mass_g` | integer | grams | Body mass at the weighing shortly before the animal entered hibernation. In this file the values run from 700 to 1135 g, to the nearest gram. This is a baseline description of the animal, not the outcome. |
| `mass_change_percent` | number | percent of pre-hibernation mass | The outcome. Percentage change in body mass across hibernation, relative to `pre_hibernation_mass_g`, recorded to one decimal place. The sign is kept, so a loss is negative: `-20.4` means the animal came out 20.4 percent lighter than it went in. Every animal lost mass, so every value in this column is negative, and a value closer to zero is a *smaller* loss. |

## How we compared the groups

Because each hedgehog contributes exactly one value, the animal and the row are the same
thing here. There is nothing to average within an animal and no clustering to allow for,
so we compared the two landscapes with an independent two-sample test applied directly to
the rows of the table: 40 animals in total, 20 per landscape. We used Welch's two-sample
t-test, which does not assume the two groups have equal spread. The analysis is in
`analysis.py`.

## What we found

| `landscape` | n animals | mean `mass_change_percent` | SD | min | max |
|---|---|---|---|---|---|
| `suburban_garden` | 20 | -18.92 | 4.12 | -27.0 | -7.6 |
| `rural_farmland` | 20 | -24.00 | 3.80 | -31.6 | -15.5 |

Suburban garden hedgehogs lost less mass over the winter than farmland hedgehogs. The
suburban animals lost 18.9 percent of their pre-hibernation mass on average and the
farmland animals lost 24.0 percent, a difference of 5.08 percentage points in favour of
the gardens (95 percent confidence interval 2.54 to 7.62 percentage points; Welch's
t = 4.05, df = 37.8, p = 0.00024). The standardised effect size is large, Hedges'
g = 1.26.

Two secondary checks agree with that result. A pooled-variance t-test gives t = 4.05,
df = 38, p = 0.00024, and a Mann-Whitney U test, which makes no assumption about the
shape of the two distributions, gives U = 330.5, p = 0.00044.

The assumptions behind the primary test look reasonable. Shapiro-Wilk tests do not flag
departures from normality in either group (suburban W = 0.935, p = 0.19; farmland
W = 0.931, p = 0.16), and the spreads are close to equal (Levene's test on medians
p = 0.90, SD ratio 1.08). We ran Welch's test regardless of that last result rather than
letting a preliminary test choose the procedure for us.

## Reading this with care

The two groups also differed at the start of the winter. Suburban animals went into
hibernation heavier, at 995 g on average (SD 95) against 871 g (SD 83) for farmland
animals. We did not adjust the comparison for that, so the 5.08 percentage point gap is
the plain difference between the landscapes as we found them, and it may carry some of
the effect of starting condition along with it. This was an observational study of animals
in the landscapes where we caught them, not an experiment that assigned them, so we read
the result as a difference between two landscapes rather than as a demonstration that the
landscape itself causes the smaller loss. The study covers one winter and 40 animals, which
is enough to see a gap this size clearly but not enough to say how it varies from year to
year.
