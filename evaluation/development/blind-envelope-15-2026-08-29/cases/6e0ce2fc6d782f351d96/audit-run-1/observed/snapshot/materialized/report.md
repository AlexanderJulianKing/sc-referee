# Week six comparison of a nicotine vaping device and nicotine patches

## Data

`data.csv` holds the week six visit records of 72 adult daily smokers who asked a stop smoking
service for help quitting. One row is one participant. The columns are:

- `participant_id`: the participant's identifier, text of the form `qs_001` through `qs_072`.
- `nicotine_product`: the product the participant was allocated to, either `vape` (a refillable
  nicotine vaping device at a standardised liquid strength) or `patch` (a transdermal nicotine
  patch at a standard starting dose).
- `exhaled_co_ppm`: exhaled carbon monoxide at the week six visit, in parts per million, recorded
  to one decimal place.
- `cigarettes_smoked_cpd`: cigarettes smoked per day at week six, self-reported over the previous
  seven days, in whole cigarettes per day.
- `urge_to_smoke_vas_0_100`: strongest urge to smoke in the past week, marked on a visual
  analogue scale from 0 (no urge at all) to 100 (strongest possible urge), in whole points.

## Design

Thirty-six participants were allocated to the vaping device and thirty-six to the patch, and both
groups received the same brief behavioural support. All 72 attended the week six visit, so no
values are missing. Three outcomes were declared in the study protocol before recruitment started,
in this order: exhaled carbon monoxide, cigarettes smoked per day, then strongest urge to smoke.

## Method

`analysis.py` reads `data.csv`, summarises each group with its size, mean and standard deviation,
and compares the two product groups on each declared outcome in the declared order. Each
comparison is a Welch two-sample t-test, which suits two independent groups and does not assume
the two groups have equal variances. Each outcome answers its own clinical question, so each one
carries its own verdict, read directly from its own p-value against the conventional 0.05
threshold. Differences below are the vaping group mean minus the patch group mean.

## Results

**Exhaled carbon monoxide.** Vaping group mean 7.74 ppm (SD 4.06), patch group mean 10.60 ppm
(SD 4.50), a difference of -2.86 ppm; t = -2.829, df = 69.3, p = 0.0061. Significant at 0.05: the
vaping group had lower exhaled carbon monoxide at week six.

**Cigarettes smoked per day.** Vaping group mean 3.47 cpd (SD 2.86), patch group mean 5.81 cpd
(SD 2.97), a difference of -2.33 cpd; t = -3.391, df = 69.9, p = 0.0011. Significant at 0.05: the
vaping group smoked fewer cigarettes per day at week six.

**Strongest urge to smoke.** Vaping group mean 32.92 points (SD 15.97), patch group mean 39.92
points (SD 16.08), a difference of -7.00 points; t = -1.853, df = 70.0, p = 0.0681. Not
significant at 0.05: the urge scores were somewhat lower in the vaping group, but not by enough to
separate the products.

## Conclusion

At the week six visit, participants using the refillable vaping device had lower exhaled carbon
monoxide and smoked fewer cigarettes per day than participants using the nicotine patch, while
their strongest reported urge to smoke was lower by about seven points but not distinguishable
from the patch group at the 0.05 threshold. The two biochemical and behavioural measures of
smoking favoured the vaping device; the urge measure did not settle the comparison either way.
