# Low-stress cattle handling and carcass quality

## What we did

84 finishing steers were moved to the abattoir either under the low-stress handling
protocol (42) or under the plant's standard handling (42). We measured plasma
cortisol at exsanguination and five carcass traits. All six outcomes were
pre-specified as one family, so `analysis.py` tests all six with Welch two-sample
t-tests and corrects them together by Holm-Bonferroni at a family-wide alpha of 0.05.
Transport time was recorded for each steer but is not an outcome.

## Primary results (all 84 steers, Holm-corrected family of 6)

| Outcome | Standard | Low-stress | p raw | p Holm | Verdict |
|---|---|---|---|---|---|
| Plasma cortisol (nmol/L) | 69.05 | 46.75 | 6.7e-07 | 4.0e-06 | significant |
| Loin pH at 24 h | 5.73 | 5.64 | 0.0097 | 0.029 | significant |
| Shear force (N) | 43.66 | 37.05 | 0.00029 | 0.0012 | significant |
| Drip loss (%) | 2.95 | 2.34 | 0.00017 | 0.00087 | significant |
| Bruise score (0-5) | 1.32 | 0.96 | 0.028 | 0.056 | not significant |
| Meat colour score (0-10) | 3.56 | 3.07 | 0.095 | 0.095 | not significant |

These corrected results are the findings of the study. Low-stress handling cut
cortisol by about a third, and carried through into a lower 24-hour pH, more tender
loin (about 6.6 N less shear force) and about 0.6 points less drip loss. Bruising and
colour both moved in the expected direction but do not survive the correction.

## Sensitivity analysis (longest tenth of transport dropped)

Long hauls are a plausible confounder, so we repeated the whole corrected family
after dropping the nine steers above the 90th percentile of transport time (cutoff
202.3 min), leaving 75 animals (35 standard, 40 low-stress). This is a stability
check on the results above, not a second set of findings.

| Outcome | Standard | Low-stress | p raw | p Holm | Verdict |
|---|---|---|---|---|---|
| Plasma cortisol (nmol/L) | 66.95 | 47.06 | 1.2e-05 | 7.5e-05 | significant |
| Loin pH at 24 h | 5.73 | 5.65 | 0.029 | 0.059 | not significant |
| Shear force (N) | 43.98 | 37.07 | 0.00075 | 0.0030 | significant |
| Drip loss (%) | 3.01 | 2.31 | 3.8e-05 | 0.00019 | significant |
| Bruise score (0-5) | 1.37 | 0.95 | 0.020 | 0.059 | not significant |
| Meat colour score (0-10) | 3.65 | 3.00 | 0.042 | 0.059 | not significant |

## Did any conclusion change?

One did. Loin pH at 24 h is significant in the primary family (Holm p = 0.029) and
falls just outside in the trimmed re-run (Holm p = 0.059). The raw difference barely
moves (0.086 to 0.081); what changes is the loss of nine animals and the resulting
power. Cortisol, shear force and drip loss hold up, and the two null outcomes stay
null. We would treat the pH result as the least secure of the four findings and worth
confirming in the next batch, without reopening the primary conclusion on the basis
of a sensitivity run.
