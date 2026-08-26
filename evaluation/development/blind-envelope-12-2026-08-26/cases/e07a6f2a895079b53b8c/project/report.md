# Cloudy pear juice: thermal pasteurisation versus high-pressure processing

Report to the product development team, 28-day storage trial.

## What we did

One batch of pressed cloudy pear juice was filled into forty-four identical bottles. Twenty-two
bottles went through our usual thermal pasteurisation. The other twenty-two were treated by
high-pressure processing. All forty-four bottles were then stored together in the dark at four
degrees Celsius for twenty-eight days. At the end of storage every bottle was opened once and
analysed. No bottle was sampled twice, so a bottle is the unit of the trial.

The trial declared four quality outcomes, and each one is a separate acceptance question for the
new process. So each outcome is compared on its own terms: a standard two-group comparison
(two-sample t-test) of the bottle values between the two treatments, judged against the
conventional five percent threshold. No multiple-comparison adjustment of any kind is applied.
Every outcome carries its own verdict at that threshold.

## Data description

The analysis reads `juice_quality.csv`. The file has one header row and 44 data rows, comma
separated.

**What one row represents:** one bottle of cloudy pear juice from the trial batch, opened once
after 28 days of dark storage at 4 degrees Celsius and measured on all four quality attributes.
Each bottle appears in exactly one row, and each row belongs to exactly one treatment. Twenty-two
rows are thermal pasteurisation and twenty-two are high-pressure processing. Every row has a value
in every column; there are no blanks.

Columns, in file order:

| Column | What it holds | Unit or values |
| --- | --- | --- |
| `bottle_id` | Bottle label, unique across the trial | Text, `B001` through `B044` |
| `group` | The process the bottle received | Text, exactly two entries: `thermal_pasteurisation` or `high_pressure_processing` |
| `ascorbic_acid_mg_100ml` | Ascorbic acid (vitamin C) content of the juice after storage | Milligrams per 100 millilitres |
| `cloud_stability_pct` | Share of the initial turbidity still suspended after the fixed centrifugation step | Percent |
| `browning_index` | Absorbance of the clarified juice at 420 nanometres | Unitless optical reading |
| `plate_count_log_cfu` | Total aerobic plate count of the bottle contents | Base-ten logarithm of colony forming units per millilitre |

The four outcome columns sit in the order the trial declared them: ascorbic acid, cloud stability,
browning index, plate count.

## Results

Each declared outcome in the declared order. Means are bottle means within a treatment, n = 22 per
treatment. The difference is high-pressure processing minus thermal pasteurisation.

### 1. Ascorbic acid (mg/100 mL)

| Treatment | Mean |
| --- | --- |
| Thermal pasteurisation | 17.38 |
| High-pressure processing | 27.42 |

Difference +10.03 mg/100 mL, p = 1.8e-19. Significant at the five percent threshold.

High-pressure bottles kept far more vitamin C through storage. The gap is large next to the
bottle-to-bottle spread inside each treatment (SD 2.48 thermal, 1.59 high pressure).

### 2. Cloud stability (percent of initial turbidity)

| Treatment | Mean |
| --- | --- |
| Thermal pasteurisation | 69.93 |
| High-pressure processing | 88.96 |

Difference +19.03 percentage points, p = 6.8e-17. Significant at the five percent threshold.

The high-pressure bottles held their cloud much better. Thermally pasteurised bottles had lost
roughly thirty percent of their suspended turbidity by day 28, against about eleven percent for
high pressure.

### 3. Browning index (absorbance at 420 nm)

| Treatment | Mean |
| --- | --- |
| Thermal pasteurisation | 0.332 |
| High-pressure processing | 0.118 |

Difference -0.214 absorbance units, p = 9.4e-22. Significant at the five percent threshold.

Lower is better here, and high pressure is lower. The thermally pasteurised bottles browned
noticeably more over storage.

### 4. Total aerobic plate count (log10 CFU/mL)

| Treatment | Mean |
| --- | --- |
| Thermal pasteurisation | 1.58 |
| High-pressure processing | 1.78 |

Difference +0.21 log10 CFU/mL, p = 0.21. Not significant at the five percent threshold.

Counts after 28 days were low and similar in both treatments. The small numerical edge for thermal
pasteurisation is within the spread we see between bottles of the same treatment (SD 0.55 thermal,
0.52 high pressure).

## Conclusion

Three of the four declared quality attributes differ between the two processes, and all three
favour high-pressure processing. High-pressure bottles finished storage with about 10 mg/100 mL
more ascorbic acid, about 19 percentage points more cloud held in suspension, and a browning index
about 0.21 absorbance units lower. Those are sensory and label-relevant differences, not marginal
ones: a cloudy pear juice that stays cloudy and stays pale is closer to what the product is
supposed to be at the end of its chilled life.

The fourth attribute, total aerobic plate count, did not separate the two processes at the five
percent threshold. On this trial the microbiological picture after 28 days at 4 degrees looks
comparable either way, with both treatments sitting well under 2 log CFU/mL on average.

For the changeover decision, this trial supports high-pressure processing on quality grounds while
giving no evidence that it costs us on aerobic plate count at the end of the declared storage
period. Two limits are worth stating before the team treats that as settled. First, this was a
single pressed batch split across forty-four bottles, so it speaks to this juice on this day, not
to batch-to-batch behaviour across a season of fruit. Second, plate count was read only at day 28,
and a non-significant result at one time point is not a shelf-life or a safety clearance. A
multi-batch repeat, with counts read at several points across storage and pathogen work handled
under the food safety plan, is the sensible next step before we commit capital.
