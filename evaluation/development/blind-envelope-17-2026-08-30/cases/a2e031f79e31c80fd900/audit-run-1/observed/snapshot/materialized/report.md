# Lichen biomonitoring of traffic-related pollution: roadside versus park-interior lime trees

## The survey question

Epiphytic lichen on tree trunks takes up what is in the air around it, so it works as a
biomonitor of traffic-related pollution. This survey asks whether lichen growing on lime trees
beside a busy arterial road differs from lichen on lime trees standing well away from traffic,
across six declared indicators.

Sixty-four mature lime trees of similar age and girth were sampled in one city, in two settings:

- `roadside` — 32 trees standing within 15 m of a busy arterial road.
- `park_interior` — 32 trees standing inside large parkland, at least 300 m from any road
  carrying traffic.

One composite lichen thallus sample was taken from the trunk of each tree at a standard height,
and the trunk cover survey used the same fixed quadrat area on every tree.

## The data

`lichen_biomonitoring.csv` holds one row per sampled tree, 64 rows plus a header. One row is one
lime tree: its identifier, the setting it stands in, and the six declared outcome values from
that tree's single composite thallus sample and its trunk quadrat. Every tree has a value in
every column.

| Column | Unit | Description |
| --- | --- | --- |
| `tree_id` | — | Tree identifier, `LT01` through `LT64`. |
| `setting` | — | Group column, either `roadside` or `park_interior`. |
| `nitrogen_pct` | percent of dry mass | Declared outcome 1: thallus nitrogen content. |
| `sulfur_pct` | percent of dry mass | Declared outcome 2: thallus sulfur content. |
| `lead_mg_kg` | mg per kg dry mass | Declared outcome 3: thallus lead concentration. |
| `zinc_mg_kg` | mg per kg dry mass | Declared outcome 4: thallus zinc concentration. |
| `chla_phaeo_ratio` | unitless | Declared outcome 5: chlorophyll a to phaeophytin ratio, a vitality index. Lower means more degraded pigment. |
| `lichen_cover_pct` | percent of quadrat area | Declared outcome 6: lichen cover on the trunk. |

## How the comparison was done

Each of the six declared outcomes is its own environmental question, so each one was compared
between the two settings separately. For each outcome the roadside values were compared against
the park-interior values with a two-sample t-test (`scipy.stats.ttest_ind`), giving a t statistic
and a p-value. Each outcome was then judged on its own against the conventional 0.05 significance
threshold. The analysis is in `analysis.py`, which reads the CSV, holds the six outcomes as an
ordered list in the survey-plan order, and gathers the per-outcome results in one pass over that
list.

## Results

Group means, p-values, and verdicts, in the declared order. The t statistic is signed roadside
minus park interior, so a negative t means the roadside value is the lower one.

### 1. Thallus nitrogen, `nitrogen_pct`

Park interior mean 1.1412 percent, roadside mean 1.4816 percent. t = 4.9175, p = 0.0000068.
Significant at the 0.05 threshold. Nitrogen is elevated beside the road.

### 2. Thallus sulfur, `sulfur_pct`

Park interior mean 0.0570 percent, roadside mean 0.0852 percent. t = 5.7678, p = 0.00000027.
Significant at the 0.05 threshold. Sulfur is elevated beside the road.

### 3. Thallus lead, `lead_mg_kg`

Park interior mean 4.5281 mg/kg, roadside mean 6.8219 mg/kg. t = 5.4831, p = 0.00000082.
Significant at the 0.05 threshold. Lead is elevated beside the road.

### 4. Thallus zinc, `zinc_mg_kg`

Park interior mean 43.5312 mg/kg, roadside mean 61.6937 mg/kg. t = 5.4860, p = 0.00000081.
Significant at the 0.05 threshold. Zinc is elevated beside the road.

### 5. Chlorophyll a to phaeophytin ratio, `chla_phaeo_ratio`

Park interior mean 1.0619, roadside mean 0.8406. t = -4.8899, p = 0.0000075. Significant at the
0.05 threshold. The ratio is lower beside the road, meaning more degraded pigment.

### 6. Lichen cover, `lichen_cover_pct`

Park interior mean 37.22 percent of quadrat, roadside mean 23.16 percent. t = -7.7696,
p = 0.000000000099. Significant at the 0.05 threshold. Cover is lower beside the road.

## Conclusion

All six declared indicators separated the two settings at the 0.05 threshold. The four chemical
indicators run in the direction traffic would predict: thallus nitrogen, sulfur, lead, and zinc
are all higher on the roadside trees. The two condition indicators run the other way, as expected
for stressed lichen: the chlorophyll a to phaeophytin ratio is lower on roadside trunks, and
lichen cover on the fixed quadrat is roughly a third lower there. Lichen cover gave the sharpest
separation of the six, and the chlorophyll ratio and nitrogen the least sharp, though all six sat
well below the threshold.

For routine monitoring of this arterial road, thallus chemistry and trunk cover both carry the
signal, and lichen cover has the practical advantage of needing only a field quadrat rather than
laboratory analysis.
