# Ventilation upgrade in primary schools: classroom carbon dioxide

Prepared for the schools estates board by the city public-health environmental health team.

## Data

The analysis uses one comma-separated data file, `classroom_co2.csv`, with a header line and 80 data
rows.

**One row is one logged classroom.** Each row records a single carbon dioxide logger sitting in one
occupied classroom, in one school building, on one cold weekday. A row is not a building and not a
pupil.

| Column | Type | What it holds |
|---|---|---|
| `building_ref` | text | Estate-management reference for the school building, in the form `EDU/<district code>/<asset number>`, for example `EDU/CE/0865`. There are 16 distinct references, each on 5 rows. |
| `ventilation_status` | text | Whether that building has the upgraded ventilation. Either `upgraded` or `unupgraded`. The upgrade was installed building-wide, so this value is the same for every room in a building. |
| `room_label` | text | The classroom's name as the school uses it, for example `Y4 Willow` or `Room 3A`. |
| `pupils_present` | integer | Number of pupils in that room while the logger was recording. Values run from 18 to 32. |
| `mean_co2_ppm` | integer | The outcome. Mean mid-lesson carbon dioxide concentration in that room, in parts per million, rounded to whole ppm. |

Sixteen school buildings took part. Eight received the ventilation upgrade and eight comparable
buildings kept their original ventilation. Five occupied classrooms were logged in each building,
spread across floors and wings, giving 80 classroom records.

## Methods

Every logged classroom in the table entered the comparison as a separate observation. Classroom
carbon dioxide was compared between the upgraded and unupgraded groups with an independent
two-sample t-test of the difference in means, using the Welch form so that the two groups are not
required to share a variance. The analysis is implemented in `analysis.py` (Python, pandas and
SciPy) and reproduces every number below.

## Results

Number of classroom records analysed: **80** (40 upgraded, 40 unupgraded).

| Group | Records | Mean CO2 (ppm) | SD (ppm) | SE (ppm) | Range (ppm) |
|---|---|---|---|---|---|
| Unupgraded | 40 | 1672.3 | 200.6 | 31.7 | 1271 to 2079 |
| Upgraded | 40 | 1049.8 | 142.5 | 22.5 | 809 to 1311 |

Upgraded classrooms sat **622.5 ppm lower** than unupgraded classrooms, a reduction of 37.2 per
cent. The 95 per cent confidence interval for the difference runs from 544.9 to 700.1 ppm.

Welch two-sample t-test: t = 16.001, df = 70.39, **p = 3.8e-25**.

The difference is significant well beyond the conventional 5 per cent level. Classroom carbon
dioxide is lower where the ventilation upgrade was installed.

## Recommendation

The upgrade works. It cut mid-lesson carbon dioxide by roughly 620 ppm, moving typical classrooms
out of the 1500 to 2100 ppm band, where stuffiness and drowsiness complaints concentrate, and into
the range around 1000 ppm that ordinary school guidance treats as acceptable on a cold day when
windows stay shut.

The estates board should extend the same ventilation upgrade to the remaining eight buildings in the
programme, and should treat it as the standard specification for the rest of the primary estate.
Loggers should stay in place through the following heating season so the board can confirm that the
improvement holds year on year.
