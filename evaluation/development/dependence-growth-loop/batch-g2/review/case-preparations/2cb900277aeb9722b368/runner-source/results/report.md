# Biofilm accumulation on moored sensor housings under two hull coatings

## Study and data

The array holds 18 oceanographic sensor housings moored independently on the Kelso
Bank shelf: 9 finished with the yard-standard epoxy (epoxy_control) and 9 with an
experimental silicone-hydrogel topcoat (silicone_hydrogel). Each housing was
photographed by a diver at four monthly inspections (month 0 to month 3) and the
fraction of the housing shoulder covered by biofilm was scored from each image.
The file therefore holds 72 session records, 4 per housing.

## Statistical approach

The four inspections of a given housing are repeated measurements of the same
mooring and are not independent of one another, so they were not entered into the
group comparison as separate observations. Each housing was first summarised by
the ordinary least-squares slope of biofilm cover on month index, that is, its
fouling accumulation rate in percentage points per month. That reduction yields
exactly one analysed value per independently moored housing, and the 18 rates were
compared between coatings with Welch's two-sample t-test for unequal variances
(two-sided).

## Per-housing fouling accumulation rate

| housing | coating           | rate |
|---------|-------------------|------|
| H01     | epoxy_control     | 7.64 |
| H02     | silicone_hydrogel | 4.04 |
| H03     | epoxy_control     | 7.99 |
| H04     | silicone_hydrogel | 3.40 |
| H05     | epoxy_control     | 7.40 |
| H06     | silicone_hydrogel | 4.24 |
| H07     | epoxy_control     | 8.58 |
| H08     | silicone_hydrogel | 3.19 |
| H09     | epoxy_control     | 6.80 |
| H10     | silicone_hydrogel | 4.16 |
| H11     | epoxy_control     | 8.82 |
| H12     | silicone_hydrogel | 3.58 |
| H13     | epoxy_control     | 7.54 |
| H14     | silicone_hydrogel | 4.59 |
| H15     | epoxy_control     | 8.33 |
| H16     | silicone_hydrogel | 3.30 |
| H17     | epoxy_control     | 7.00 |
| H18     | silicone_hydrogel | 4.04 |

Rate is in percentage points of cover per month; 18 housings, one rate each.

## Result

Epoxy control: mean rate 7.79 pp/month (SD 0.69, n = 9 housings).
Silicone-hydrogel topcoat: mean rate 3.84 pp/month (SD 0.48, n = 9 housings).
Difference (control minus topcoat): 3.95 pp/month, 95% CI [3.35, 4.56].

[selected-result] Welch's two-sample t-test on 18 independent per-housing fouling accumulation rates (9 epoxy_control vs 9 silicone_hydrogel, one OLS slope per housing over its 4 monthly inspections): t = 14.00, df = 14.3, p < 0.0001; the silicone-hydrogel topcoat accumulates biofilm 3.95 pp/month more slowly (95% CI [3.35, 4.56]).

The 72 session-level records were used only to estimate the within-housing slopes;
no inference was drawn from them as if they were 72 independent observations.
