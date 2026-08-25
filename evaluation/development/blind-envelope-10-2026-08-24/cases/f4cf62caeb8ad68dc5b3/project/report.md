# Ski-piste disturbance and alpine marmot condition and behaviour

## Data

The dataset is `marmots.csv`. One row is one adult alpine marmot, trapped, measured and released once
during a single summer season. Each animal appears exactly once, and every cell is filled. There are
58 rows: 29 marmots from colonies whose burrow systems sit within 100 m of a groomed piste, and 29
from undisturbed alpine meadow colonies at similar elevation and aspect.

| Column | Units | Meaning |
| --- | --- | --- |
| `marmot_id` | none | Unique animal identifier, `MAR-001` through `MAR-058`, in trapping order. |
| `disturbance_group` | none | Colony type, either `piste_adjacent` or `undisturbed`. 29 rows each. |
| `body_mass_kg` | kilograms | Pre-hibernation body mass at capture. |
| `fgm_ng_per_g` | nanograms per gram dry faeces | Faecal glucocorticoid metabolite concentration from the sample taken at handling. |
| `emergence_doy` | day of year | Day the animal was first seen above ground after hibernation, where 1 is 1 January. |
| `vigilance_pct` | percent | Share of a standardised focal observation period spent in an upright vigilance posture. |
| `ectoparasite_count` | count | Ectoparasites found in a standardised body search at handling. |

## Methods

Each of the five declared outcomes was compared between the two colony types with a Welch two-sample
t-test for independent samples, run in `analysis.py`. Group means and standard deviations (sample SD)
are reported for every outcome.

For the three headline outcomes (body mass, faecal glucocorticoid metabolites, emergence date) the
raw p-value was multiplied by five, the number of comparisons in the declared family, capped at one,
and the corrected value judged against 0.05. Vigilance and ectoparasite load were declared as
separate questions in their own right, so each was judged on its own raw p-value against 0.05.

## Group summaries

| Outcome | Piste-adjacent (n = 29) | Undisturbed (n = 29) | Difference |
| --- | --- | --- | --- |
| Body mass (kg) | 3.98 +/- 0.47 | 4.37 +/- 0.50 | -0.40 |
| Faecal glucocorticoid metabolites (ng/g) | 191.5 +/- 79.6 | 156.8 +/- 42.2 | +34.7 |
| Emergence date (day of year) | 117.6 +/- 7.4 | 112.8 +/- 7.4 | +4.7 |
| Vigilance (% of observation period) | 14.3 +/- 6.5 | 11.3 +/- 5.0 | +2.9 |
| Ectoparasite count | 9.0 +/- 5.8 | 7.4 +/- 3.7 | +1.6 |

Values are mean +/- standard deviation. The difference column is piste-adjacent minus undisturbed.

## Headline outcomes

| Outcome | t | Raw p | Corrected p | Verdict at 0.05 |
| --- | --- | --- | --- | --- |
| Body mass | -3.120 | 0.0029 | 0.0143 | Significant |
| Faecal glucocorticoid metabolites | 2.074 | 0.0441 | 0.2207 | Not significant |
| Emergence date | 2.446 | 0.0176 | 0.0881 | Not significant |

Marmots from piste-adjacent colonies went into hibernation 0.40 kg lighter on average, and that gap
survives the correction. The stress-metabolite gap of 34.7 ng/g and the 4.7-day later emergence both
point the same way but do not clear 0.05 once corrected.

## Vigilance and ectoparasite load

| Outcome | t | p | Verdict at 0.05 |
| --- | --- | --- | --- |
| Vigilance | 1.924 | 0.0597 | Not significant |
| Ectoparasite count | 1.240 | 0.2209 | Not significant |

Piste-adjacent animals spent 2.9 percentage points more of the observation period upright and
watching, and carried 1.6 more ectoparasites on average. Neither difference reaches 0.05.

## Conclusion

Body condition is where piste disturbance shows up in this sample. Marmots living within 100 m of a
groomed piste entered hibernation lighter than meadow animals by 0.40 kg, about 9 percent of the
undisturbed mean, and that difference holds after correcting the headline family. The physiological
and phenological outcomes move in the direction a disturbance effect would predict, with higher
faecal glucocorticoid metabolites and later spring emergence in the piste-adjacent group, but neither
clears the corrected threshold in 29 animals per group. Behaviourally, vigilance was higher near
pistes and fell just short of 0.05, and ectoparasite burden did not differ. On this season of data
the clear signal is a mass cost near pistes, with the stress and timing outcomes worth revisiting
with a larger sample.
