# Peak echolocation frequency at two summer roosts

## Data

- Input file: `data/input.csv`
- Nightly recording sessions: 48
- Individual bats: 12
- Sessions contributed per bat: 4

| Roost site | Sessions | Bats | Mean peak frequency (kHz) | SD (kHz) |
| --- | ---: | ---: | ---: | ---: |
| quarry_adit | 24 | 6 | 41.000 | 1.727 |
| halden_culvert | 24 | 6 | 38.400 | 1.737 |

## Analysis

Each of the 48 rows in `data/input.csv` was entered as one observation in a
two-sample Student t test (pooled variance, two-sided) comparing mean peak
echolocation frequency between the quarry_adit sessions and the
halden_culvert sessions.

## Result

- Mean difference (quarry_adit minus halden_culvert): 2.600 kHz
- Pooled standard deviation: 1.732 kHz
- Standardised difference (Cohen's d): 1.501
- Test statistic: t = 5.200 on df = 46
- Two-sided p-value: p < 0.0001

[selected-result] Two-sample t test over 48 nightly recording sessions entered as 48 observations: mean peak echolocation frequency is 2.600 kHz higher at quarry_adit than at halden_culvert (t = 5.200, df = 46, p < 0.0001).

The 12 bats each contributed 4 nightly sessions, and those individual sessions
were the units entered into the test reported above.
