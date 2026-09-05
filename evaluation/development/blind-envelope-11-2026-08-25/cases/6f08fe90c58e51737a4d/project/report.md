# Black soldier fly substrate trial: brewery spent grain versus supermarket vegetable waste

## Question and design

Our production unit needs to know which of our two available feed substrates gives the better
rearing result. We ran the comparison in the unit itself. Forty-eight identical rearing crates were
seeded with the same number of neonate larvae on the same day. Twenty-four crates were fed brewery
spent grain and twenty-four were fed sorted supermarket vegetable waste. Substrate is the only
thing we varied; it is a two-level grouping factor, and the crate is the experimental unit. Each
crate was harvested when the first prepupae appeared in it.

Before harvest we declared six outcomes in the trial plan: mean individual larval fresh mass,
harvested fresh larval yield per crate, larval crude protein, larval crude fat, substrate
reduction, and development time to first prepupae. Each of these is a separate production question
that we care about on its own merits. Protein content matters to the feed customer; yield matters
to the throughput plan; development time matters to the crate turnaround schedule. So each declared
outcome gets its own comparison of spent grain against vegetable waste, and each one is judged
against the conventional 0.05 threshold. The comparison is a standard two-sample t-test on the 24
crates in each group.

The analysis is in `analysis.py` and runs against `bsf_substrate_trial.csv`.

## Data description

**One row is one rearing crate.** There are 48 data rows, one per crate, plus a header row. Each
row carries the crate's label, the substrate it was fed, and the six declared outcome measurements
taken from that same crate at harvest. There are no missing cells.

| Column | Type | Unit | What it holds |
| --- | --- | --- | --- |
| `crate_id` | text | none | Crate label, `CR01` through `CR48`, unique in the file |
| `substrate` | text | none | Feed substrate for that crate, exactly two values: `spent_grain` or `vegetable_waste` |
| `mean_larval_fresh_mass_mg` | number | mg | Declared outcome 1: mean fresh mass of an individual larva at harvest in that crate |
| `fresh_larval_yield_g` | integer | g | Declared outcome 2: total harvested fresh larval mass from that crate |
| `crude_protein_pct_dm` | number | % of dry matter | Declared outcome 3: crude protein content of the larvae from that crate |
| `crude_fat_pct_dm` | number | % of dry matter | Declared outcome 4: crude fat content of the larvae from that crate |
| `substrate_reduction_pct` | number | % | Declared outcome 5: share of the crate's starting substrate mass consumed by harvest |
| `development_time_days` | number | days | Declared outcome 6: days from seeding to the first prepupae in that crate |

The six outcome columns sit in the fixed order the trial plan declared them.

## Per-group summary

Spread is the standard deviation across crates within the group.

| Declared outcome | Spent grain (n, mean, SD) | Vegetable waste (n, mean, SD) |
| --- | --- | --- |
| 1. Mean larval fresh mass (mg) | 24, 178.06, 18.20 | 24, 154.05, 17.13 |
| 2. Fresh larval yield (g) | 24, 956.79, 89.84 | 24, 849.33, 66.75 |
| 3. Crude protein (% DM) | 24, 39.10, 2.43 | 24, 38.45, 2.94 |
| 4. Crude fat (% DM) | 24, 28.08, 3.29 | 24, 31.15, 2.93 |
| 5. Substrate reduction (%) | 24, 52.28, 4.52 | 24, 46.33, 6.11 |
| 6. Development time (days) | 24, 14.71, 1.52 | 24, 15.29, 1.28 |

## Results, one declared outcome at a time

**1. Mean individual larval fresh mass (mg).** Spent grain 178.06, vegetable waste 154.05, a
difference of 24.0 mg in favour of spent grain. t = 4.704, p = 0.000024. The two substrates differ
significantly. Larvae reared on spent grain finish about 16 percent heavier per individual.

**2. Harvested fresh larval yield per crate (g).** Spent grain 956.79, vegetable waste 849.33, a
difference of 107.5 g per crate. t = 4.704, p = 0.000024. The two substrates differ significantly.
This tracks the mass result, as it should, and it is the number the throughput plan uses.

**3. Larval crude protein (% of dry matter).** Spent grain 39.10, vegetable waste 38.45, a
difference of 0.65 points. t = 0.839, p = 0.406. The two substrates do not differ significantly.
The crate-to-crate spread on this measurement, around 2.5 to 3 points in both groups, is several
times larger than the gap between the group means. For the feed customer, larvae from either
substrate are the same product on protein.

**4. Larval crude fat (% of dry matter).** Spent grain 28.08, vegetable waste 31.15, a difference
of 3.07 points in favour of vegetable waste. t = -3.416, p = 0.0013. The two substrates differ
significantly. Vegetable waste gives the fattier larva.

**5. Substrate reduction (%).** Spent grain 52.28, vegetable waste 46.33, a difference of 5.9
points. t = 3.834, p = 0.00038. The two substrates differ significantly. Crates on spent grain
consumed a larger share of what they were given, which means less residue to handle per crate.

**6. Development time to first prepupae (days).** Spent grain 14.71, vegetable waste 15.29, a
difference of 0.58 days. t = -1.431, p = 0.159. The two substrates do not differ significantly.
Crate turnaround is the same on either substrate as far as this trial can tell, and the scheduling
assumption of roughly fifteen days holds for both.

## What this means for the unit

Four of the six declared outcomes separate the two substrates and two do not. Spent grain wins on
the three production outcomes: heavier individual larvae, more harvested mass per crate, and more
of the substrate consumed. Vegetable waste wins on crude fat. Protein content and development time
came out the same on both feeds, so neither the protein spec nor the crate schedule gives us a
reason to prefer one substrate over the other.

If the unit is buying on yield, spent grain is the better substrate. If a customer is buying larvae
for the fat fraction, vegetable waste is worth keeping in the mix.

## Reproducing the analysis

From the project root:

```
python analysis.py
```

The script reads `bsf_substrate_trial.csv`, prints the crate counts per group, prints the mean and
standard deviation of every declared outcome in each group, and then works through the declared
outcome list in order, printing each outcome's t statistic, p-value, and verdict at the 0.05
threshold. It requires `pandas` and `scipy`.
