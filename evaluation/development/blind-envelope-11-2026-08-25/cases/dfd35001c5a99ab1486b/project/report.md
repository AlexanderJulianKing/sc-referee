# Badgers in pasture and arable landscapes: five declared outcomes

## Question and design

We asked whether European badgers living in a pasture-dominated landscape differ from
badgers living in an arable-dominated landscape. Fifty adult badgers were live-trapped,
measured, fitted with GPS collars and tracked for six weeks in late summer: 25 animals in
pasture country and 25 in arable country. Landscape type is the two-level grouping factor.
Each animal contributes one summary value per outcome for its whole tracking period, so
the design is a simple between-animal comparison with no repeated measures.

Five outcomes were written into the study plan before the collars went on, and they are
examined here in that declared order: mean nightly distance travelled, 95 percent kernel
home range area, body condition index, mean time active per night, and faecal cortisol
metabolite concentration. Each of these is a distinct ecological question about how
landscape shapes badger biology, and each is answered on its own terms. Every outcome was
compared between the two landscapes with a two-sample t-test and judged against the
conventional 0.05 threshold.

## Data description

The study data live in `badger_landscape_data.csv`: one header row and 50 data rows,
seven comma-separated columns, UTF-8.

**One row is one collared adult badger.** The row holds that animal's identifier, its
landscape group, and one summary value for each of the five declared outcomes covering its
whole six-week tracking period. Each animal appears exactly once, and every cell is filled.

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `animal_id` | text | none | Unique animal identifier (`BDG-P01`...`BDG-P25` pasture, `BDG-A01`...`BDG-A25` arable). |
| `mean_nightly_distance_km` | number | kilometres | Declared outcome 1: mean distance travelled per night. |
| `home_range_95_kernel_ha` | number | hectares | Declared outcome 2: home range area from a 95 percent kernel estimate. |
| `body_condition_index` | number | unitless | Declared outcome 3: body condition index at capture. |
| `mean_time_active_hours` | number | hours | Declared outcome 4: mean time active per night. |
| `faecal_cortisol_ng_per_g` | integer | nanograms per gram | Declared outcome 5: faecal cortisol metabolite concentration. |
| `landscape_type` | text | none | Grouping factor with exactly two values, `pasture` and `arable`. |

Rows are interleaved rather than blocked by group, so row order carries no information.

## Per-group summaries

Spread is the sample standard deviation.

| Declared outcome | Pasture n | Pasture mean | Pasture SD | Arable n | Arable mean | Arable SD |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Mean nightly distance (km) | 25 | 4.809 | 1.166 | 25 | 6.225 | 1.464 |
| 2. Home range, 95% kernel (ha) | 25 | 64.312 | 20.566 | 25 | 84.368 | 24.023 |
| 3. Body condition index | 25 | 1.126 | 0.128 | 25 | 1.016 | 0.128 |
| 4. Mean time active per night (h) | 25 | 6.972 | 1.284 | 25 | 7.534 | 1.159 |
| 5. Faecal cortisol (ng/g) | 25 | 211.560 | 59.553 | 25 | 253.640 | 57.111 |

## Test results

| Declared outcome | t | p | Verdict at 0.05 |
| --- | --- | --- | --- |
| 1. Mean nightly distance (km) | -3.784 | 0.0004 | Significant |
| 2. Home range, 95% kernel (ha) | -3.171 | 0.0026 | Significant |
| 3. Body condition index | 3.036 | 0.0039 | Significant |
| 4. Mean time active per night (h) | -1.623 | 0.1111 | Not significant |
| 5. Faecal cortisol (ng/g) | -2.550 | 0.0140 | Significant |

## Conclusions, in the declared order

**1. Mean nightly distance travelled.** The two landscapes differ significantly
(p = 0.0004). Arable badgers covered about 6.23 km a night against 4.81 km for pasture
badgers, roughly 1.4 km further. Arable ground offers food in scattered, seasonal patches,
and the collars show animals walking further to string those patches together.

**2. Home range area.** The two landscapes differ significantly (p = 0.0026). Arable
ranges averaged 84.4 ha, pasture ranges 64.3 ha, about 20 ha larger. This is the same
story as the nightly distance seen at the scale of the whole tracking period: badgers in
arable country hold more ground.

**3. Body condition index.** The two landscapes differ significantly (p = 0.0039), and
here pasture animals come out ahead: 1.13 against 1.02. Permanent grass supplies
earthworms steadily through late summer, and the extra walking arable badgers do does not
buy them the same condition.

**4. Mean time active per night.** The two landscapes do not differ significantly
(p = 0.1111). Arable animals were out 7.53 hours a night and pasture animals 6.97 hours, a
gap of about 34 minutes that sits well inside the animal-to-animal spread. Nightly activity
time looks set by daylight and by badger habit rather than by the surrounding farmland, so
arable animals appear to fit their longer journeys into a similar working night.

**5. Faecal cortisol metabolite concentration.** The two landscapes differ significantly
(p = 0.0140). Arable badgers averaged 254 ng/g against 212 ng/g in pasture, about 42 ng/g
higher, consistent with the greater effort and more disturbed surroundings that the
movement results describe.

Taken outcome by outcome, badgers in arable country range further over a larger area, carry
poorer condition, and show higher cortisol, while the length of their active night matches
that of pasture badgers.
