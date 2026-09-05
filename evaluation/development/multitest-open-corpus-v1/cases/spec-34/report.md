# Metabolomic markers of grass-fed beef

## Design

We looked for plasma markers that separate pasture-finished from grain-finished
cattle, using 128 archived samples from one year of slaughter records (64 pasture,
64 grain). Because the six-marker panel is exploratory, animals were assigned to a
discovery set and a held-out validation set before any marker was measured against
finishing system. The assignment is recorded in the `split` column of `data.csv` and
is used exactly as recorded: 32 grain and 32 pasture animals in discovery, and the
same in validation. `analysis.py` never reassigns it.

## Discovery: screening only

All six markers were tested in the discovery animals (Welch two-sample t-tests). This
stage picks what goes forward; it is not evidence about any marker.

| Marker | Grain | Pasture | p | Shortlisted |
|---|---|---|---|---|
| Alpha-linolenic acid (mg/L) | 12.02 | 22.01 | 3.4e-10 | yes |
| Beta-carotene (ug/L) | 139.38 | 312.62 | 3.8e-12 | yes |
| Vaccenic acid (mg/L) | 8.16 | 13.36 | 6.0e-07 | yes |
| Phytanic acid (umol/L) | 2.81 | 4.06 | 0.00030 | yes |
| Urea (mmol/L) | 4.35 | 5.26 | 0.0030 | yes |
| Creatinine (umol/L) | 109.56 | 112.88 | 0.43 | no |

Five of six markers cleared the 0.05 screening threshold. Creatinine did not, which is
what we expected of it: it tracks muscle mass rather than diet, and it was in the panel
as a negative control.

## Validation: the corrected family

Only the five shortlisted markers were tested in the held-out animals, so the
validation family covers **5 tests**, Holm-Bonferroni corrected together at a
family-wide alpha of 0.05. Creatinine was not retested and is not part of this family.

| Marker | Grain | Pasture | p | p Holm | Verdict |
|---|---|---|---|---|---|
| Alpha-linolenic acid (mg/L) | 12.09 | 21.93 | 3.2e-07 | 1.3e-06 | marker |
| Beta-carotene (ug/L) | 158.59 | 265.62 | 8.2e-08 | 4.1e-07 | marker |
| Vaccenic acid (mg/L) | 8.52 | 14.15 | 5.1e-06 | 1.5e-05 | marker |
| Phytanic acid (umol/L) | 2.78 | 4.12 | 0.00013 | 0.00027 | marker |
| Urea (mmol/L) | 4.68 | 5.09 | 0.14 | 0.14 | not supported |

## Markers that qualify

Four of the six screened metabolites qualify as authenticity indicators: alpha-
linolenic acid, beta-carotene, vaccenic acid and phytanic acid. All four are pasture-
elevated and all four survive correction across the validation family by a wide
margin, so the conclusion does not hinge on the choice of Holm over another
family-wide method.

Plasma urea is the instructive failure. It screened at p = 0.0030 in discovery and
then landed at p = 0.14 in the held-out animals, with the gap between groups shrinking
from 0.91 to 0.41 mmol/L. Urea reflects dietary protein supply, which varies with the
particular grain ration as much as with pasture, so it is a plausible marker that
simply does not hold up. Had we reported the discovery screen as a result, urea would
have gone into the panel on the strength of one look at one half of the data.

Practical note for the assay: the four confirmed markers are what a routine
authenticity screen should measure. All four have a similar relative spread within
each finishing group (coefficient of variation between about 0.32 and 0.39), and the
two group distributions overlap in every case, so a single animal cannot be called
from any one marker on its own. Use them together, and on batches rather than on
individual carcasses, until we have enough animals to set reference ranges.
