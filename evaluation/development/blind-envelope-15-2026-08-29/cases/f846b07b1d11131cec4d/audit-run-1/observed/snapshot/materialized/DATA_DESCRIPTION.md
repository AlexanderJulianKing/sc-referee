# data.csv

Saffron planting-depth trial. Sixty-four corms of the same size grade, each planted singly in its
own bed position, tracked through one flowering season and the following lift. Thirty-two corms
were planted shallow (10 cm) and thirty-two deep (20 cm); soil, spacing, irrigation and lifting
date were the same for all.

One row is one corm: its bed identifier, its planting depth, and its four protocol outcome
measurements. There are 64 data rows plus one header row. No repeated rows, no summary rows, no
blank cells.

## Columns

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `corm_id` | text | none | Corm identifier, `corm_` followed by a zero-padded bed position number from `corm_01` to `corm_64`. Unique across rows. |
| `planting_depth` | text | none | Planting depth group. Exactly two labels: `shallow` (10 cm) and `deep` (20 cm), 32 corms each. |
| `flower_count` | integer | flowers | Number of flowers the corm produced in the first season. |
| `stigma_yield_mg` | number | mg | Dry stigma yield harvested from that corm, recorded to 0.1 mg. |
| `daughter_corm_mass_g` | number | g | Total mass of the daughter corms attached to that corm at lifting, recorded to 0.1 g. |
| `time_to_first_flower_d` | integer | d (days) | Days from planting to the corm's first flower. |

Column order in the file is the order shown above: identifier, group, then the four outcomes in the
order they were declared in the trial protocol (flower count, stigma yield, daughter corm mass,
time to first flower).

Every corm has a value for every outcome. Flower counts and day counts are whole numbers; the two
mass measurements carry one decimal place, as a field horticulture team would record them.
