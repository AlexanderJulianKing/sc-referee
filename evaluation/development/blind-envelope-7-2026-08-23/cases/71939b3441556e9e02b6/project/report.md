# Regulated deficit irrigation and olive oil content

Research agronomist's report on the grove irrigation trial.

## Design

Sixteen mature olive trees were selected across the grove. Eight trees were kept under
full-season irrigation. The other eight received regulated deficit irrigation through pit
hardening and were returned to normal watering afterwards. At harvest, fruit was picked
separately from the four cardinal quadrants of each tree's canopy, giving four samples per tree.
Each sample was pressed on its own and assayed for oil content as a percentage of fruit fresh
weight. That gives 64 assayed samples in total, 32 under each regime.

## Data description

The trial data sit in one table, `olive_oil_content.csv`, with a header row and 64 data rows.
**One row is one canopy-position fruit sample from one tree**: the fruit picked from a single
cardinal quadrant of a single tree's canopy at harvest, pressed and assayed.

| Column | What it holds |
| --- | --- |
| `tree_id` | Identifier of the olive tree the sample was picked from, `T01` through `T16`. |
| `irrigation_regime` | The tree's irrigation treatment: `full` (full-season irrigation) or `deficit` (regulated deficit irrigation during pit hardening). |
| `canopy_position` | Cardinal quadrant of the canopy the fruit came from: `north`, `east`, `south`, or `west`. |
| `oil_content_pct` | Oil content of the pressed sample, as a percentage of fruit fresh weight, to two decimal places. |

There are no missing values.

## Method

The analysis is in `analysis.py`. It reads the committed CSV and compares mean oil content
between the two irrigation regimes with a standard independent two-sample t-test, taking each
canopy-position sample in the table as one observation. Group means and standard deviations are
reported alongside the test. Analysis was run in Python with pandas and SciPy
(`scipy.stats.ttest_ind`).

## Results

| Regime | Samples | Mean oil content (%) | SD (%) | Range (%) |
| --- | --- | --- | --- | --- |
| Full-season irrigation | 32 | 18.53 | 1.87 | 14.34 to 21.73 |
| Regulated deficit irrigation | 32 | 21.13 | 1.58 | 17.89 to 24.50 |

Deficit-irrigated fruit averaged 2.60 percentage points more oil than fully irrigated fruit.
The independent two-sample t-test on the 64 assayed samples gives **t = 6.01 on 62 degrees of
freedom, p = 1.1 x 10^-7**. The sample size for the test is 32 samples under full irrigation and
32 under deficit irrigation.

## Interpretation

Regulated deficit irrigation during pit hardening raised oil content in this grove, and the
increase is large enough to matter in the mill as well as on paper. Moving from 18.53 percent to
21.13 percent oil on a fresh-weight basis is a gain of about 2.6 points, roughly a 14 percent
relative lift in oil recovered per tonne of fruit delivered. The spread within each regime is
modest, a little under 2 percentage points, and the two ranges overlap only in their tails, so
the separation is not being carried by a handful of unusual samples. The p-value is far below any
conventional threshold, so a difference this size is very unlikely to have arisen by chance
alone. On the strength of this season's harvest I would recommend holding water back through pit
hardening as standard practice in the grove, and tracking oil content again next season to
confirm the response repeats.

*Analysis: `analysis.py`. Data: `olive_oil_content.csv` (see also `DATA_DESCRIPTION.md`).*
