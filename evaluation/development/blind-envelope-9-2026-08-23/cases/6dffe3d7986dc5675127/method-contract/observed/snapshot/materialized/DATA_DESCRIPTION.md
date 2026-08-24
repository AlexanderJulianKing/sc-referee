# Data description: hedgehog overwintering study

## Files

One data file: `hedgehog_overwinter_mass.csv`.

There is no second summary file. The study produced a single value per animal, so the
one table already holds one number per animal and nothing needs to be pre-aggregated.

The file is produced by `make_data.py` (Python standard library only, fixed random seed
`20260823`), so re-running the generator reproduces the same CSV.

## What one row is

**One row is one hedgehog.** Each of the 40 tagged animals appears exactly once.

Each animal was weighed twice over the winter, once shortly before it entered
hibernation and once shortly after it emerged. Those two weighings were reduced to a
single percentage mass change before the table was written, so the two raw weights are
not separate rows and the post-emergence weight is not a column of its own. **No animal
is measured more than once in this table, and no animal appears in more than one row.**
The animal and the row are therefore the same unit, and the 40 rows are 40 independent
animals rather than repeated observations on a smaller set of animals.

## Size

- 40 rows of data, plus one header row (41 lines in the file).
- 40 hedgehogs, all distinct tag codes.
- 4 columns.

## Groups

The grouping variable is `landscape`, with two levels and 20 animals each:

| `landscape` value | Meaning | Animals |
|---|---|---|
| `suburban_garden` | Tracked in suburban gardens | 20 |
| `rural_farmland` | Tracked on rural farmland | 20 |

Landscape is a between-animal grouping. Every animal belongs to exactly one landscape
for the whole winter, so the two groups share no animals.

## Columns

| Column | Type | Units | Description |
|---|---|---|---|
| `hedgehog_id` | text | — | Tag code of the animal, `HH-01` through `HH-40`. The unit identifier. Unique across the file: 40 codes for 40 rows. Tag numbers were issued at capture and do not encode landscape. |
| `landscape` | text (2 categories) | — | Landscape the animal was tracked in: `suburban_garden` or `rural_farmland`. 20 animals in each. |
| `pre_hibernation_mass_g` | integer | grams | Body mass at the weighing shortly before the animal entered hibernation. Range in this file 700 to 1135 g, rounded to the nearest gram. This is a baseline covariate, not the outcome. |
| `mass_change_percent` | number | percent of pre-hibernation mass | The outcome. Percentage change in body mass across hibernation, relative to `pre_hibernation_mass_g`. **Signed, so a loss is negative**: `-20.4` means the animal came out of hibernation 20.4 percent lighter than it went in. Every animal lost mass, so every value is negative. Recorded to one decimal place. |

### Reading the outcome column

`mass_change_percent` is a change, so the sign carries meaning and the values are
negative. When a result is described in words as a "loss of 24 percent", that is the
size of the number without its minus sign. Anything comparing the two landscapes should
keep the sign convention straight: a value closer to zero is a *smaller* loss, so a
group whose mean is `-19` lost less mass than a group whose mean is `-24`.

## What the numbers look like

Summary statistics of the delivered file, for orientation only:

| `landscape` | n animals | mean `mass_change_percent` | SD | min | max |
|---|---|---|---|---|---|
| `suburban_garden` | 20 | -18.9 | 4.1 | -27.0 | -7.6 |
| `rural_farmland` | 20 | -24.0 | 3.8 | -31.6 | -15.5 |

Most animals lost between 12 and 32 percent of their pre-hibernation mass. One suburban
animal lost only 7.6 percent.

## Implication for analysis

Because each hedgehog contributes exactly one value and no animal is repeated, the rows
of this table are the analysis units. A comparison of the two landscapes is an
independent two-sample comparison applied directly to the rows, with 40 animals in
total and 20 per landscape. No clustering, repeated-measures, or averaging step is
needed before the groups are compared, because there is nothing to average within an
animal.
