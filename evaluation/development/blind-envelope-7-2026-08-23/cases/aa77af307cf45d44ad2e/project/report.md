# Noise rearing raises response thresholds in gerbil primary auditory cortex

## Design

We reared Mongolian gerbils from weaning under one of two acoustic conditions.
Seven animals were housed in the quiet colony room. Seven were housed in
continuous moderate-level broadband noise. In adulthood each animal was
anaesthetised and single neurons were recorded from primary auditory cortex
with a fine electrode. For every well-isolated unit we measured the response
threshold at that unit's characteristic frequency, read off the rate-level
function in decibels sound pressure level (dB SPL). Recording yielded 175 units
in total from 14 animals.

## Data description

All measurements are in the single file `unit_thresholds.csv`, a plain
comma-separated text file with one header line and 175 data lines.

**One row is one well-isolated single unit** recorded from primary auditory
cortex, carrying that unit's threshold at its own characteristic frequency.
Each unit appears exactly once.

The file has four columns:

| column | type | what it holds |
|---|---|---|
| `animal_id` | text | Identifier of the gerbil the unit came from, `G01`-`G14`. |
| `rearing_condition` | text | Acoustic rearing condition of that animal, `quiet` or `noise`. |
| `unit_id` | text | Identifier of the unit, formatted `<animal_id>-uNN` and numbered in recording order from `u01`. Unique across the file. |
| `cf_threshold_db_spl` | number | Response threshold of the unit at its characteristic frequency, in dB SPL, to one decimal place. |

There are no missing values in any column.

## Method

The analysis script `analysis.py` loads the CSV and compares
`cf_threshold_db_spl` between the two levels of `rearing_condition` with a
standard independent two-sample t-test assuming equal variances. Every recorded
unit contributes one observation to the test. The script also reports the
number of units per group with the group mean, standard deviation, and observed
range.

## Result

Sample size was 175 units: 89 recorded under quiet rearing and 86 under noise
rearing.

| group | n units | mean threshold (dB SPL) | SD (dB) | range (dB SPL) |
|---|---|---|---|---|
| quiet | 89 | 23.93 | 6.76 | 7.6 - 41.6 |
| noise | 86 | 33.22 | 7.11 | 14.2 - 50.4 |

Mean threshold was 9.29 dB SPL higher in the noise-reared group. The
independent two-sample t-test gave t(173) = 8.855, p = 9.71e-16.

## Interpretation

Rearing in continuous moderate-level broadband noise leaves adult cortical
neurons markedly less sensitive at their characteristic frequency. The shift is
close to 9 dB, which is large next to the roughly 7 dB spread of thresholds
within either group, and the difference is highly reliable. Because the two
groups differed only in the acoustic environment they experienced from weaning
onward, the elevation is attributable to that rearing environment rather than
to any difference in recording procedure, which was identical for both groups.
The size of the shift is consistent with a real loss of sensitivity in primary
auditory cortex rather than a small change in tuning: a unit that would once
have responded to a moderate tone now needs an appreciably louder one to fire.
The full range of thresholds still overlaps between the groups, so noise
rearing does not silence the cortex, it moves the whole distribution upward. We
conclude that prolonged developmental exposure to moderate broadband noise
raises response thresholds in gerbil primary auditory cortex by roughly 9 dB
SPL in adulthood.
