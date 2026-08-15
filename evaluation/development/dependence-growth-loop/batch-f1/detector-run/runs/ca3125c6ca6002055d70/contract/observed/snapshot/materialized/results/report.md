# First-arm choice in the paired-array foraging assay

## Data

- Source table: `data/input.csv`
- Foraging bouts scored: 20
- Individually marked bees: 6
- Bouts choosing the UV-marked arm first: 5 (25.0%)
- Mean handling time across bouts: 8.47 s

### Bouts per bee

| bee_id | bouts | uv_marked first | share |
| --- | --- | --- | --- |
| B01 | 4 | 0 | 0.000 |
| B02 | 3 | 0 | 0.000 |
| B03 | 4 | 0 | 0.000 |
| B04 | 2 | 2 | 1.000 |
| B05 | 4 | 2 | 0.500 |
| B06 | 3 | 1 | 0.333 |

## Analysis

Every scored bout was entered as one Bernoulli trial, and the 20 trials were submitted
to an exact two-sided binomial test (`scipy.stats.binomtest`) against the
no-preference expectation of 0.5.

## Result

[selected-result] Exact two-sided binomial test on 20 scored bouts: 5 of 20 first choices went to the UV-marked arm (25.0%), p = 0.041389 against the null proportion of 0.5, indicating a statistically significant bias away from the UV-marked arm at the 5% level.
