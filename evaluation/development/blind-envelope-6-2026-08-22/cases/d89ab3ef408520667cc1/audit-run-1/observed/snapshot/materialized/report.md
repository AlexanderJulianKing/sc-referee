# Salt-in-moisture of a semi-hard raw-milk cheese made with two starter cultures

## Aim

The laboratory's house starter culture has been used for this semi-hard raw-milk cheese
for many seasons. A defined commercial culture is being considered as a replacement.
Salt-in-moisture is one of the controlling parameters for this cheese type, because it
governs the rate of proteolysis during ripening and the safety margin of the raw-milk
make. The aim of this work was to establish whether changing the starter culture shifts
the salt-in-moisture content of the finished cheese at ninety days.

## Make and sampling protocol

Sixteen production vats were made over one season, from 8 April 2025 to 20 September
2025, at a spacing of roughly eleven days. Eight vats were made with the traditional
house culture and eight with the defined commercial culture. The two cultures were
alternated through the make calendar so that neither culture was confined to one part
of the season and so that neither was systematically favoured by seasonal milk
composition.

Wheels from each vat were brined and ripened under the standard schedule for this
cheese. At ninety days of ripening one composite sample was drawn from each vat's
wheel-set. The salt-in-moisture content of each composite sample was then determined by
the laboratory's titration method, and the titration was carried out three times on that
sample. This produced 48 titration measurements in total, 24 for each starter culture.

## Data description

The measurements are held in `salt_in_moisture.csv`. One row is a single titration
measurement: one reading of salt-in-moisture on the composite sample from one production
vat's wheel-set at ninety days. The file has 48 data rows and one header row.

| Column | Type | Description |
|---|---|---|
| `VatCode` | text | Identifier of the production vat, `V01` through `V16`. Each code appears in three rows, one per titration reading of that vat's composite sample. |
| `CultureType` | text | Starter culture used for the vat, either `Traditional` or `Commercial`. Constant within a vat. |
| `MakeDate` | date, `YYYY-MM-DD` | Date the vat was made. Constant within a vat. |
| `ReplicateNo` | integer | Which of the three titration readings on that vat's composite sample the row holds. Takes the values 1, 2 and 3. |
| `SaltInMoisturePct` | number, 2 decimal places | Measured salt-in-moisture content, in percent, from the laboratory's titration method. |

## Method

The analysis is carried out by `analysis.py` at the project root, using pandas 2.0.3 and
SciPy 1.9.1.

Each titration measurement is taken as one observation of salt-in-moisture, giving 24
measurements per starter culture. Salt-in-moisture was summarised for each culture as the
number of measurements, the mean, the standard deviation, the standard error of the mean,
and the observed range. The two cultures were then compared with an independent
two-sample t-test assuming equal variances, testing the null hypothesis of equal mean
salt-in-moisture. The test was two-sided at a significance level of 0.05. The difference
in means is reported as Commercial minus Traditional, with a 95 percent confidence
interval built from the pooled standard deviation, and the standardised effect size is
reported as Cohen's d.

## Results

Salt-in-moisture, percent, by starter culture:

| Culture | n measurements | Mean | SD | SEM | Min | Max |
|---|---|---|---|---|---|---|
| Traditional | 24 | 4.230 | 0.243 | 0.050 | 3.85 | 4.60 |
| Commercial | 24 | 4.702 | 0.283 | 0.058 | 4.10 | 5.09 |

Independent two-sample t-test, Commercial minus Traditional:

| Quantity | Value |
|---|---|
| Difference in means | +0.472 percentage points |
| Pooled SD | 0.264 percentage points |
| Standard error of the difference | 0.076 percentage points |
| 95 percent CI for the difference | +0.319 to +0.625 percentage points |
| t statistic | t(46) = 6.201 |
| p value | 1.447e-07 |
| Cohen's d | 1.790 |

The cheese made with the commercial culture measured 4.702 percent salt-in-moisture on
average, against 4.230 percent for the traditional house culture. The difference of 0.472
percentage points is well outside the confidence interval's distance from zero, and the
null hypothesis of equal mean salt-in-moisture is rejected at the 0.05 level.

## Conclusion

Changing from the traditional house culture to the defined commercial culture raises
salt-in-moisture in this semi-hard raw-milk cheese by about 0.47 percentage points at
ninety days, with a 95 percent confidence interval of roughly 0.32 to 0.63 percentage
points. The shift is statistically significant (p = 1.4e-07) and the standardised effect
size is large (d = 1.79).

A shift of this size is technologically meaningful for this cheese type. If the
commercial culture is adopted, the brining schedule should be re-targeted so that the
finished cheese lands back in the salt-in-moisture window the ripening programme was
built around, and the ripening plan should be re-checked against the new level before the
change is made across the full season's production.
