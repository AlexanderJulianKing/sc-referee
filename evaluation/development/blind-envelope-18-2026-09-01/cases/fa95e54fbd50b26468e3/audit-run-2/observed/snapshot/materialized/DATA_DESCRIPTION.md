# Data description: data.csv

Noise exposure survey of dwellings after the opening of a new tram line. Forty-six dwellings were
surveyed: twenty-three fronting the tram corridor and twenty-three on comparable control streets two
blocks away, matched on building type and road traffic. Each dwelling was measured over the same
one-week period, and one resident per dwelling completed the questionnaire.

## What one row represents

One row is one surveyed dwelling. It holds that dwelling's identifier, its street type, its two
measured sound levels for the survey week, and the two questionnaire answers given by its resident.
Each dwelling appears exactly once, so there are 46 data rows plus a header row. There are no blank
cells; every dwelling has a value for every outcome.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `dwelling_id` | text | Unique survey identifier for the dwelling, formatted `DW-001` through `DW-046`. Ordered by survey sequence, not by group. |
| `street_type` | text | Which street the dwelling fronts. Exactly two values: `tram_corridor` (fronting the new tram line) and `control` (comparable street two blocks away). 23 dwellings in each. |
| `indoor_night_level_db` | number, one decimal | Declared outcome 1. Indoor night-time equivalent continuous sound level over the survey week, A-weighted decibels (dB). |
| `facade_lden_db` | number, one decimal | Declared outcome 2. Facade day-evening-night sound level over the survey week, A-weighted decibels (dB). |
| `sleep_disturbance_score` | integer | Declared outcome 3. Resident's self-reported sleep disturbance on a 0 to 10 questionnaire scale, where 0 is no disturbance. Unitless. |
| `awakenings_per_night` | integer | Declared outcome 4. Resident's reported count of noise-related awakenings on a typical night during the survey week. A count, so unitless. |

The four outcome columns appear in the order the survey plan declared them.

## Data collection note

Dwelling `DW-019`, on the tram corridor, was measured while unrelated building work was under way in
the same building. Its indoor night-time level of 57.8 dB is far above what is plausible for a
dwelling of this type and reflects that work rather than tram noise. The value in the file is the
real measured value and has not been altered or removed.
