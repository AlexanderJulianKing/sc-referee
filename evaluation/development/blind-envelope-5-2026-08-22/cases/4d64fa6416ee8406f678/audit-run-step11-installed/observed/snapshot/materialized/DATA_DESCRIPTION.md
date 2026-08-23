# Data description

## The file

`shelter_cat_fgm.csv` is the single data file for this project. It is plain comma-separated text with
one header line and 144 data lines.

`make_data.py` is the script that produced it. The data are **simulated**, not measured: no real cats
were sampled. The script uses a fixed random seed (20260822) and only the Python standard library, so
running `python3 make_data.py` rewrites exactly the same file.

## What one row is

**One row is one cat on one morning** (one faecal sample plus that morning's food record). It is not
one cat, and it is not one group.

Because every cat was sampled on six consecutive mornings, **each cat appears on six rows** of the
file. Rows are grouped by cat, and inside a cat they run from `sample_day` 1 to 6.

## Units and counts

| Quantity | Count |
| --- | --- |
| Cats (independent animals) | 24 |
| Cats per group | 12 enrichment, 12 usual husbandry |
| Mornings per cat | 6 |
| Rows in the file | 144 |
| Rows per group | 72 |

The 144 rows are **not** 144 independent observations. The independent units are the 24 cats; the six
rows belonging to a cat are repeated measures on that same animal and are correlated with each other.
Think of it like weighing the same 24 people on six mornings: you have 144 numbers, but only 24
people's worth of independent information about who is heavy and who is light.

## The two groups

`husbandry_group` splits the cats into the two arms of the study. Cats were assigned as whole animals,
so a cat's group is the same on all six of its rows.

- `enrichment` — the structured enrichment protocol: hiding boxes, predictable handling, scent items.
- `usual_husbandry` — the shelter's usual husbandry, the control condition.

## Columns

Columns appear in this order.

| # | Column | Type | Description |
| --- | --- | --- | --- |
| 1 | `cat_ref` | text | The cat's shelter intake code, in the form `A26-nnnn` (`A` for animal, `26` for the 2026 intake year, then the running case number). Unique per cat; repeats on the six rows belonging to that cat. 24 distinct values. |
| 2 | `husbandry_group` | text | Which arm the cat is in: `enrichment` or `usual_husbandry`. Constant within a cat. |
| 3 | `sample_day` | integer | Which of the six consecutive sampling mornings this row is, 1 through 6. Day 1 is the first morning of sampling for that cat. |
| 4 | `food_intake_pct` | number, 1 decimal | Food eaten that morning as a percentage of the ration offered, 0 to 100. Observed range in the file is 40.6 to 100.0. |
| 5 | `fgm_ng_per_g` | number, 1 decimal | The outcome: faecal glucocorticoid metabolite concentration, in nanograms per gram of dry faeces. FGM is a stress-hormone by-product that shows up in droppings, so a higher number means more stress load. Observed range in the file is 65.4 to 255.1. |

There are no missing values: every cat has all six mornings, and every row has all five fields filled
in.

## What the numbers look like

Summary statistics, for orientation only. The analysis is not in this file.

| Group | Cats | Rows | Mean FGM (ng/g) | FGM range (ng/g) | Range of the 12 per-cat mean FGMs | Mean food intake (%) |
| --- | --- | --- | --- | --- | --- | --- |
| `enrichment` | 12 | 72 | 111.2 | 65.4 – 189.5 | 77.0 – 160.8 | 77.0 |
| `usual_husbandry` | 12 | 72 | 174.4 | 124.6 – 255.1 | 129.7 – 228.9 | 67.8 |

Two features of the simulated data matter for choosing an analysis:

1. **Cats differ a lot from each other, and those differences persist.** Within the usual-husbandry
   group the per-cat mean FGM runs from about 130 to about 229 ng/g. A cat that is high on morning 1
   tends to still be high on morning 6.
2. **Day-to-day wobble inside one cat is much smaller than that.** The typical (median) standard
   deviation of a cat's own six values is about 11 ng/g.

Together these mean the six rows from one cat carry much less independent information than six rows
from six different cats.
