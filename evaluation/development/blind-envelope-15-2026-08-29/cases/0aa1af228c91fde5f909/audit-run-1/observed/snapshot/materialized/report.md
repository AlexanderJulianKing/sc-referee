# Winter food supplementation in bank voles

## Data

`data.csv` has 48 rows and a header. **One row is one vole**, measured once at the end of
the four-week study. The columns are:

- `vole_id` — animal identifier, `vole_01` to `vole_48` (text label, no unit).
- `supplement_group` — the feeding treatment the vole's pen received, either
  `supplemented` or `unsupplemented`.
- `mass_change_g` — change in body mass over the four weeks, end minus start, in grams
  (g); negative values are animals that lost mass.
- `resting_metabolic_rate_ml_o2_per_h` — resting metabolic rate, in millilitres of oxygen
  per hour (ml O2/h).
- `faecal_corticosterone_ng_per_g` — faecal corticosterone metabolites, in nanograms per
  gram of dry faeces (ng/g).
- `distance_moved_per_night_m` — distance moved per night inside the pen from radio
  tracking, in metres (m).

## Design

Forty-eight wild-caught bank voles were each held singly in an outdoor pen of identical
construction on one site for four weeks. Twenty-four pens received a daily supplement of
seed and grain and twenty-four received none; pens were otherwise identical in shelter and
natural vegetation. Every animal was measured at the end of the four weeks and released.
The outcome family was declared in the licence application and study protocol before the
animals were caught, in this fixed order: body mass change, resting metabolic rate, faecal
corticosterone metabolites, distance moved per night.

## Group summaries

| Outcome | Supplemented (mean ± SD) | Unsupplemented (mean ± SD) | Difference |
| --- | --- | --- | --- |
| Mass change (g) | 3.09 ± 2.06 | 0.80 ± 2.13 | +2.29 |
| Resting metabolic rate (ml O2/h) | 67.48 ± 8.56 | 73.72 ± 8.83 | −6.23 |
| Faecal corticosterone (ng/g) | 140.42 ± 55.65 | 195.04 ± 48.65 | −54.62 |
| Distance moved per night (m) | 233.08 ± 73.13 | 309.21 ± 74.45 | −76.12 |

Group sizes are 24 supplemented and 24 unsupplemented.

## How the family was tested

Each outcome was compared between the two groups with a two-sample Welch t statistic,
supplemented minus unsupplemented. Because all four outcomes were declared together as one
family, testing each one at 0.05 on its own would let the chance of at least one false
positive across the family rise well above 0.05. The correction used here is a
label-shuffling procedure written directly in the analysis script from basic array
operations.

The number of shuffles was fixed in advance by the protocol at **4000**. In each shuffle
the group labels were reassigned at random across all forty-eight voles while the two group
sizes were held fixed at 24 and 24, the same statistic was recomputed for all four declared
outcomes on the shuffled labels, and the single largest absolute statistic across the whole
family was recorded. Those 4000 values form one reference distribution: the distribution of
the family maximum expected when supplementation does nothing to any outcome.

Each outcome's family-wise p-value is the share of the 4000 shuffles whose family maximum is
at least as large as that outcome's observed absolute statistic. Judging every outcome
against the family maximum, rather than against its own separate reference distribution, is
what holds the family-wise error rate at 0.05 across all four outcomes at once: under the
null, the chance that any member of the family clears the bar is the chance the observed
family maximum is extreme, and that is capped at 0.05 by construction. No verdict here comes
from an unshuffled per-outcome p-value. The run uses the fixed random seed 20240117 and is
reproducible.

## Results

| Outcome | Observed t | Family-wise p | Conclusion |
| --- | --- | --- | --- |
| Mass change (g) | 3.777 | 0.0015 | Significant at FWER 0.05 |
| Resting metabolic rate (ml O2/h) | −2.482 | 0.0698 | Not significant at FWER 0.05 |
| Faecal corticosterone (ng/g) | −3.620 | 0.0035 | Significant at FWER 0.05 |
| Distance moved per night (m) | −3.574 | 0.0043 | Significant at FWER 0.05 |

For reference, the 4000 shuffled family maxima had a mean of 1.493 and a 95th percentile of
2.619, so an observed absolute statistic above about 2.62 is what it takes to clear the 0.05
family-wise bar here.

## What the experiment found

Three of the four declared outcomes separate the groups after correction across the whole
family. Supplemented voles gained about 2.3 g more body mass over the four weeks, had faecal
corticosterone metabolite concentrations about 55 ng/g lower, and moved about 76 m less per
night than unsupplemented voles. Resting metabolic rate was about 6.2 ml O2/h lower in the
supplemented group, but that difference did not clear the family-wise 0.05 bar
(p = 0.0698) and is not claimed as a finding. Taken together, winter food supplementation
left bank voles heavier, less stressed by the corticosterone measure, and less active at
night, with no supported difference in resting metabolic rate.
