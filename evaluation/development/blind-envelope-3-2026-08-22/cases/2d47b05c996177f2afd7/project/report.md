# Rootstock and powdery mildew susceptibility in a single-block vineyard trial

## Data description

The trial produced one comma-separated data file, `mildew_leaf_data.csv`, with a header line and
128 data rows.

**One row is one grapevine leaf.** Each row records the leaf's lesion measurement together with the
vine it came from, that vine's rootstock, the canopy position it was picked from, and its own
identifier.

| Column | Type | Units | Description |
| --- | --- | --- | --- |
| `Vine` | text | — | Vine identifier, `V01` through `V16`. |
| `Rootstock` | text | — | Rootstock the vine is grafted onto: `Standard` or `DroughtTolerant`. |
| `CanopyPosition` | text | — | Canopy zone the leaf was collected from: `Upper` or `Lower`. |
| `Leaf` | text | — | Leaf identifier, written `<Vine>-L<n>`, unique across the file. |
| `LesionArea` | number | cm² | Area of powdery mildew lesions measured on that leaf. |
| `TotalLeafArea` | number | cm² | Total one-sided area of that leaf. |

There are no missing values, and each of the 128 leaf identifiers occurs exactly once.

The analysis script is `analysis.py` at the root of the project. It reads the data file and prints
every number quoted below.

## Vineyard layout

Sixteen grapevines of a single scion variety were planted in one block. Eight were grafted onto the
estate's standard rootstock (`V01`–`V08`) and eight onto a drought-tolerant rootstock
(`V09`–`V16`). Keeping all sixteen vines in the same block holds soil type, aspect, irrigation, row
orientation, and spray history common across the two rootstock groups, so the rootstock is the
feature that separates them. Canopy management and trellising were the same throughout the block.

## Sampling and measurement

Leaves were collected at veraison, the stage at which berries begin to colour and soften and at
which powdery mildew pressure on the canopy is at its most informative. Eight leaves were taken from
each vine, four from the upper canopy and four from the lower canopy, so that the sample spans the
light and humidity gradient down the canopy rather than sitting in one zone. That gives 64 leaves per
canopy position and 128 leaves in total.

Each collected leaf was flattened and imaged. Image analysis returned two areas per leaf: the area
covered by powdery mildew lesions (`LesionArea`, cm²) and the total one-sided area of the leaf
(`TotalLeafArea`, cm²). Total leaf area averaged 94.8 cm² (SD 11.1 cm², range 68.3–123.8 cm²) and
was comparable across the two rootstock groups, so lesion area is being compared on leaves of
similar size.

## Analysis

Lesion area on each measured leaf is the response. The two rootstock groups were compared with an
independent two-sample t-test on `LesionArea`, with every leaf in the table entered as its own
observation. Sample size is therefore the total number of leaves measured, n = 128, 64 leaves per
rootstock group. The test was two-sided at the 5% level.

## Results

| Rootstock | Leaves (n) | Mean lesion area (cm²) | SD (cm²) | SE (cm²) | Range (cm²) |
| --- | --- | --- | --- | --- | --- |
| Standard | 64 | 3.90 | 1.82 | 0.23 | 0.85 – 7.80 |
| DroughtTolerant | 64 | 2.45 | 1.83 | 0.23 | 0.02 – 8.61 |

Total sample size: **n = 128 leaves**.

Leaves from vines on the drought-tolerant rootstock carried 1.45 cm² less mildew lesion area than
leaves from vines on the standard rootstock (95% CI 0.81 to 2.09 cm²), a reduction of 37.2%.

Independent two-sample t-test: **t = 4.50, df = 126, p = 1.53 × 10⁻⁵**.

Spread was almost identical in the two groups (SD 1.82 and 1.83 cm²). Both groups included lightly
affected leaves and a few heavily affected ones, which is the usual pattern for powdery mildew on a
canopy: infection starts in patches, so some leaves escape while others carry most of the damage.

Mean lesion area per vine ranged from 2.42 to 4.78 cm² on the standard rootstock and from 1.06 to
4.36 cm² on the drought-tolerant rootstock.

## Conclusion

Rootstock choice reduced mildew damage in this block. Vines grafted onto the drought-tolerant
rootstock carried mildew lesions covering an average of 2.45 cm² per leaf, against 3.90 cm² per leaf
on the estate's standard rootstock, a drop of 1.45 cm² per leaf, or 37.2%, with p = 1.53 × 10⁻⁵
across the 128 leaves measured.

For a block managed under one spray programme, a reduction of that size on the drought-tolerant
rootstock is worth acting on. The practical reading is that the drought-tolerant rootstock delivers a
second benefit alongside its water-stress tolerance: less powdery mildew on the leaf. Growers
choosing this rootstock for dry sites can expect lower mildew damage on the canopy as well.

Two limits are worth stating. The trial covers one block in one season, so the result describes this
site and this year rather than every site the rootstock might go into. And the comparison is made at
veraison only, so it says nothing about how the two rootstocks compare earlier in the season, when
the mildew epidemic is still building. Repeating the sampling across seasons and across blocks would
show whether the gap holds.
