# Seed potato storage: firmness under conventional air and low-oxygen controlled atmosphere

## Data

The analysis uses `storage_firmness.csv`, which holds 84 records. One row is one bin visit: a single
sealed storage bin opened and sampled on a single sampling date. A row is not a bin and not an
individual tuber.

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `bin_code` | text | none | The store's bin tag, e.g. `CS1-A01`. There are 14 distinct codes, one per storage bin, each appearing on 6 rows. |
| `atmosphere` | text | none | Storage treatment applied to the bin at loading: `conventional_air` or `low_oxygen_ca`. Constant across a bin's six rows. |
| `storage_week` | integer | weeks since loading | Sampling time, one of 4, 8, 12, 16, 20, 24. |
| `weight_loss_pct` | number | percent of loading weight | Cumulative weight lost by the bin's contents since loading. Two decimal places. Observed range 0.64 to 8.22 percent. |
| `firmness_newton` | number | newtons (N) | Penetrometer firmness of the sample drawn at that visit. The study outcome. One decimal place. |

Fourteen bins were filled from the same graded seed-potato lot: seven held under conventional cold
air, seven under a low-oxygen controlled atmosphere. Each bin was sampled six times at four-week
intervals, giving 42 records per atmosphere and 84 in total. There are no missing values.

## Methods

Tuber firmness in newtons was compared between the two storage atmospheres with an independent
two-sample t-test of the difference in means. Every firmness record in the table entered the
comparison as a separate observation, giving 84 firmness records analysed, 42 per group. Each
group is summarised by its mean and standard deviation. The test was two-sided and significance was
judged at the 0.05 level. The analysis was run with `analysis.py` using pandas 2.0.3 and
scipy 1.9.1.

## Results

Firmness records analysed: 84.

| Atmosphere | Records | Mean firmness (N) | SD (N) | Range (N) |
| --- | --- | --- | --- | --- |
| `conventional_air` | 42 | 54.97 | 7.65 | 41.9 to 68.8 |
| `low_oxygen_ca` | 42 | 58.97 | 4.59 | 50.4 to 66.8 |

Mean firmness was 4.00 N higher under the low-oxygen controlled atmosphere than under conventional
cold air (t = 2.903, df = 82, p = 0.0047). The difference is statistically significant at the 0.05
level, so the low-oxygen controlled atmosphere holds tuber firmness above conventional cold air
across the storage season.

The pattern is clearest at the end of the season. At week 24, mean firmness was 52.71 N under the
low-oxygen atmosphere and 44.24 N under conventional air. Firmness under conventional air also
spread more widely, with a standard deviation of 7.65 N against 4.59 N under low oxygen. Weight loss
rose from 0.64 percent at the earliest visits to 8.22 percent at the end of storage.

## Recommendation

Move the seed lot to low-oxygen controlled atmosphere storage for next season. It delivered firmer
tubers overall and an 8.5 N advantage in mean firmness by week 24, when seed is drawn for planting,
and it held firmness within a tighter band across bins, which makes the condition of any given bin
easier to predict at loading time. Keep the four-week sampling interval and the penetrometer
protocol unchanged so next season's readings compare directly with this one.
