# Station trial note: biostimulant seed coating in sunflower

## Aim and treatments

This trial asks whether coating sunflower seed with a microbial biostimulant before sowing improves
crop performance. Seventy-two individually tagged plants were grown in a single uniform field under
one management regime. Thirty-six plants came from biostimulant-coated seed (`coated`) and
thirty-six from untreated seed of the same cultivar and seed lot (`untreated`). These two seed
treatments are the only comparison in the study. Each plant was measured individually at flowering
and at harvest.

## Data

File: `sunflower_trial.csv`. One row is one tagged sunflower plant, carrying its seed treatment and
its value for each of the five declared outcomes. There are 72 data rows, 36 per seed treatment, and
no missing cells.

| Column | Description |
| --- | --- |
| `plant_id` | Plant tag, prefix `SF-` plus a zero-padded serial number (`SF-001` to `SF-072`). |
| `seed_treatment` | Seed treatment group, either `untreated` or `coated`. |
| `plant_height_cm` | Outcome 1. Plant height at flowering, nearest centimetre. |
| `head_diameter_cm` | Outcome 2. Capitulum (seed head) diameter at harvest, to 0.1 cm. |
| `filled_seed_number` | Outcome 3. Filled seeds counted in the head at harvest. |
| `thousand_seed_mass_g` | Outcome 4. Mass of one thousand seeds from that plant, to 0.1 g. |
| `seed_oil_content_pct` | Outcome 5. Seed oil content as a percentage of seed dry mass, to 0.1 percent. |

The five outcomes appear in the declared order fixed before the season began: plant height, head
diameter, filled seed number, thousand-seed mass, seed oil content.

## How the comparison was done

Each declared outcome is its own agronomic question, so each was compared between the two seed
treatments on its own with a two-sample t-test (`scipy.stats.ttest_ind`, coated versus untreated,
36 plants per group). Each outcome was judged separately against the conventional 0.05 significance
threshold. All of the analysis code is in `analysis.py`, which reads the CSV and works through the
five outcomes in the declared order.

## Results

**Outcome 1: plant height at flowering (cm).** Untreated mean 166.53 cm, coated mean 172.81 cm.
t = 2.065, p = 0.0427. Significant at 0.05.

**Outcome 2: head diameter at harvest (cm).** Untreated mean 17.47 cm, coated mean 18.35 cm.
t = 2.076, p = 0.0416. Significant at 0.05.

**Outcome 3: filled seed number per head.** Untreated mean 1154.61 seeds, coated mean 1212.64 seeds.
t = 1.862, p = 0.0668. Not significant at 0.05.

**Outcome 4: thousand-seed mass (g).** Untreated mean 57.65 g, coated mean 60.83 g. t = 3.025,
p = 0.0035. Significant at 0.05.

**Outcome 5: seed oil content (percent of seed dry mass).** Untreated mean 43.42 percent, coated
mean 44.24 percent. t = 2.367, p = 0.0207. Significant at 0.05.

## Conclusion

Coated seed gave taller plants at flowering, wider heads at harvest, heavier seed, and higher seed
oil content, with each of those four outcomes separating at the 0.05 threshold. Thousand-seed mass
showed the largest and clearest difference of the five, about 3.2 g heavier per thousand seeds.
Filled seed number per head ran about 58 seeds higher under the coating but did not reach the 0.05
threshold, so on this trial the coating's effect on seed set is not established. Taken together, the
biostimulant seed coating affected plant size, seed size, and seed quality in this field, while its
effect on the number of filled seeds per head remains open.
