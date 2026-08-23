# Amenity footpath lighting and foraging activity of lesser horseshoe bats

A survey of twelve river valley maternity roosts, summer season.

## Aim

New amenity lighting has been installed along footpaths in several of our river
valleys. Lesser horseshoe bats (*Rhinolophus hipposideros*) are a light-shy
species and the concern raised by the conservation team is that a lit path
running past a roost exit suppresses foraging activity in the valley. This
survey asks a single question: do detectors record fewer bat passes per night in
lit valleys than in dark ones?

## Survey design

Twelve maternity roosts were surveyed. Six sit in valleys where a newly lit
amenity footpath now runs past the roost exit. The other six sit in valleys that
remain dark. One static ultrasonic detector was deployed at each roost and left
in position for eight consecutive suitable nights, so each detector returned
eight nightly activity totals. Nightly minimum temperature was logged alongside
each total.

Twelve detectors times eight nights gives 96 detector-nights of survey effort:
48 detector-nights in dark valleys and 48 in lit valleys.

## Method

The analysis is in `analysis.py` at the project root. It reads
`bat_activity.csv`, checks the file for missing values and unexpected lighting
labels, and summarises nightly bat passes in each lighting condition.

Nightly bat passes were then compared between the two lighting conditions with
an independent two-sample t-test, using Welch's correction so the two groups are
not required to share a variance. The test was applied to every detector-night
row in the file, and the sample size is the total number of detector-nights in
each condition: 48 dark and 48 lit.

Nightly minimum temperature was checked in the same way, as a descriptive
comparison of survey conditions between the two groups, and its association with
nightly activity was summarised with a Pearson correlation.

## Results

Nightly bat passes by lighting condition:

| Lighting | Detector-nights | Mean | SD | SE | Median | Min | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dark | 48 | 206.2 | 80.0 | 11.5 | 176.5 | 122 | 453 |
| lit | 48 | 133.3 | 33.3 | 4.8 | 122.0 | 91 | 222 |

Survey conditions were closely matched between the two groups. Nightly minimum
temperature averaged 9.60 degrees C in dark valleys (SD 2.26, range 5.1 to 13.0)
and 9.66 degrees C in lit valleys (SD 2.34, range 4.8 to 12.6). Across all 96
detector-nights, warmer nights carried more passes than colder ones
(r = 0.296, p = 0.0034), which is the expected weather signal for this species.

Independent two-sample t-test (Welch), 96 detector-nights:

| Quantity | Value |
| --- | --- |
| n, dark detector-nights | 48 |
| n, lit detector-nights | 48 |
| Mean difference, dark minus lit | 72.9 passes per night |
| 95% confidence interval | 47.9 to 97.9 passes per night |
| t | 5.833 |
| Degrees of freedom | 62.81 |
| p | 0.000000205 |
| Cohen's d | 1.19 |

Detectors in lit valleys logged 35.4 per cent fewer bat passes per night than
detectors in dark valleys. The difference is significant at the 5 per cent level
and the effect is large.

## Conservation recommendation

The survey shows a substantial shortfall in nightly foraging activity at roosts
in lit valleys, on the order of 73 passes per night, or about a third of the
activity recorded in dark valleys. For a light-shy species using maternity
roosts, activity lost around the roost exit during the maternity period is a
real cost to the colony.

We recommend the following:

1. Do not install further amenity lighting along river valley footpaths that
   pass within sight of a known lesser horseshoe roost exit. Treat the roost
   exit and its first stretch of commuting route as a dark corridor.
2. Where lighting is already installed, retrofit the units nearest the roost
   exits. The measures to apply are full downward shielding to cut spill toward
   the exit and flight line, a reduction in output, and a part-night switch-off
   covering the hours around dusk emergence and pre-dawn return through the
   maternity period.
3. Repeat detector deployments at the same roosts after any retrofit, using the
   same eight-night protocol, so the change in nightly activity can be measured
   against the totals reported here.
4. Consult the survey results at the planning stage for any new footpath
   lighting scheme in these valleys.

## Data description

Two CSV files accompany this report. `bat_activity.csv` is the analysis file.
`roost_summary.csv` is a convenience summary derived from it.

### `bat_activity.csv`

One row is one detector-night: the activity logged by one detector, at one
roost, on one night. The file has 96 rows.

| Column | Type | Units or values | Meaning |
| --- | --- | --- | --- |
| `roost_code` | text | `R01` to `R12` | Anonymised code of the maternity roost where the detector stood. Twelve codes, each on eight rows. |
| `lighting_condition` | text | `dark` or `lit` | Lighting group of the valley. `lit` means a newly lit amenity footpath runs past the roost exit; `dark` means the valley has no such lighting. 48 rows in each group. |
| `night_index` | integer | 1 to 8 | Position of the night within that detector's eight consecutive survey nights. 1 is the first night of deployment, 8 the last. |
| `min_temp_c` | decimal | degrees Celsius, one decimal place | Minimum air temperature over that night at that roost. Values run from 4.8 to 13.0. |
| `bat_passes` | integer | whole counts | Number of lesser horseshoe bat passes logged by the detector over that night. Values run from 91 to 453. |

### `roost_summary.csv`

One row is one roost, summarising that roost's eight detector-nights. The file
has 12 rows and holds no information beyond `bat_activity.csv`.

| Column | Type | Units or values | Meaning |
| --- | --- | --- | --- |
| `roost_code` | text | `R01` to `R12` | Roost identifier, matching `bat_activity.csv`. |
| `lighting_condition` | text | `dark` or `lit` | Lighting group of that roost's valley. |
| `nights_surveyed` | integer | nights | Number of detector-nights contributed by the roost. Eight for every roost. |
| `total_passes` | integer | whole counts | Sum of `bat_passes` over the roost's eight nights. |
| `mean_passes_per_night` | decimal | passes per night, one decimal place | Mean of `bat_passes` over the roost's eight nights. |
| `min_passes` | integer | whole counts | Lowest nightly total at that roost. |
| `max_passes` | integer | whole counts | Highest nightly total at that roost. |
| `mean_min_temp_c` | decimal | degrees Celsius, one decimal place | Mean of `min_temp_c` over the roost's eight nights. |

All figures quoted in this report are produced by `analysis.py` from
`bat_activity.csv`.
