# Reduced nitrogen top-dressing and hop cone alpha-acid content

## What we did

We wanted to know whether cutting the nitrogen top-dressing changes the alpha-acid content of the
cone. We followed twenty mature bines on the trellis through the season: ten kept on the farm's
standard nitrogen rate, ten on the reduced rate. At harvest the technician picked six cones from
each bine and sent every cone to the bench on its own, so each cone carries its own alpha-acid
assay. That gives us 120 cone measurements to work with.

## The data

The measurements are in `hop_cone_alpha_acids.csv`. One row is one hop cone: a single cone picked
from a single bine and assayed on its own for alpha-acid content. The file has 120 rows plus a
header.

| Column | Type | What it holds |
| --- | --- | --- |
| `bine_tag` | text | The numbered aluminium tag fixed to the bine the cone came from, `BINE-01` through `BINE-20`. |
| `nitrogen_rate` | text | The nitrogen top-dressing rate that bine was grown at: `standard` or `reduced`. |
| `cone_number` | integer | Which of the six cones picked from that bine this row is, 1 to 6. It is a label for the cone, not a time point and not a dose. |
| `alpha_acid_percent` | number | Alpha-acid content of that cone, as a percentage of dry cone weight, to two decimal places. This is the outcome we measured. |

The table is balanced: 20 bines, six cones assayed from each, 60 cones on the standard rate and 60
on the reduced rate. There are no missing cones. Rates alternate down the tag order, odd tags
standard and even tags reduced, so neither treatment sits at one end of the trellis row.

## How we analysed it

We compared alpha-acid percentage between the two nitrogen rates with an independent two-sample
t-test assuming equal variances, run over every row of the table. Each assayed cone enters the
comparison as its own observation, giving a total sample size of n = 120. The analysis is in
`analysis.py`.

## Results

| Group | n | Mean alpha-acid (%) | SD | Range (%) |
| --- | --- | --- | --- | --- |
| Standard nitrogen | 60 | 11.46 | 1.24 | 9.32 to 13.69 |
| Reduced nitrogen | 60 | 10.66 | 1.26 | 8.51 to 13.19 |

Cones from the reduced-nitrogen bines came in 0.80 percentage points lower in alpha acids than
cones from the standard-rate bines (95% CI 0.35 to 1.25 percentage points; SE 0.228).

Independent two-sample t-test: t(118) = 3.52, p = 0.00062, Cohen's d = 0.64.

## What this means

Cutting the nitrogen top-dressing lowered cone alpha-acid content. The drop is 0.80 percentage
points, about seven percent of the standard-rate mean of 11.46 percent, and it is clearly
distinguishable from zero at the 120-cone sample size (p = 0.00062). The effect is a moderate one
by the usual standard, d = 0.64, and the confidence interval keeps the true difference somewhere
between roughly a third of a point and a point and a quarter.

For the brewhouse that matters. Alpha acids are what the buyer pays for, so a drop of 0.80
percentage points off an 11.5 percent baseline is a real haircut on the bittering value of the
crop. We would not recommend the reduced rate on bines destined for high-alpha contracts on the
strength of these numbers. If the reduced rate is worth pursuing for input cost or nitrate-runoff
reasons, the trade-off should be priced against that loss in cone quality rather than assumed
away.

The spread within each group is much the same at the two rates, 1.24 against 1.26 percentage
points, so the reduced rate shifted the whole distribution down rather than making the crop more
erratic. Every value in the table falls in the eight to fourteen percent band we expect from this
variety, and the lowest cone we measured, 8.51 percent, came off a reduced-nitrogen bine.
