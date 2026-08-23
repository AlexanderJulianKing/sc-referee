# Sugar kelp seeding density and blade length

## Aim

The farm wants to know whether seeding dropper lines at a reduced density, which gives each
plant more light, grows longer sugar kelp blades than the farm's standard seeding density.
The response is blade length in centimetres at harvest, five months after deployment.

## Farm layout and sampling

All work happened on one longline. Fourteen dropper lines hang from that longline. Seven lines
were seeded at the **standard** density (`L01`-`L07`) and seven at the **reduced** density
(`L08`-`L14`). The seeding density was applied to a whole dropper line, so every plant on a
line shares one treatment.

After five months in the water, ten blades were haphazardly selected and measured on each
dropper line. That is 14 x 10 = **140 measured blades**. Each blade contributes one row to the
raw file, and its length and wet mass were recorded.

## The averaging step, and why the line is the unit of replication

The dropper line, not the blade, is the thing that was assigned a seeding density. Ten blades
from the same line share that line's depth, current, light, and seeding, so they resemble each
other more than they resemble blades from a different line. Treating the 140 blades as 140
independent observations would count the same line seven or eight times over and shrink the
standard error to something the design does not support. This is pseudoreplication.

The fix is a single averaging step. `analysis.py` collapses each dropper line's ten blade
lengths into one number, the line's mean blade length. That leaves **14 values, one per dropper
line, seven per seeding density**, and those fourteen values are the only data the test sees.
The 140 blades still matter, because averaging ten blades measures each line more precisely
than measuring one blade would, but they describe sampling effort rather than sample size.

Per-line mean blade length (cm):

| Dropper line | Seeding density | Mean blade length (cm) | Blades averaged |
| --- | --- | --- | --- |
| L01 | standard | 95.28 | 10 |
| L02 | standard | 97.65 | 10 |
| L03 | standard | 99.45 | 10 |
| L04 | standard | 78.37 | 10 |
| L05 | standard | 80.34 | 10 |
| L06 | standard | 93.03 | 10 |
| L07 | standard | 104.90 | 10 |
| L08 | reduced | 127.35 | 10 |
| L09 | reduced | 129.56 | 10 |
| L10 | reduced | 111.57 | 10 |
| L11 | reduced | 127.72 | 10 |
| L12 | reduced | 126.48 | 10 |
| L13 | reduced | 128.44 | 10 |
| L14 | reduced | 120.81 | 10 |

## Method

One inferential test was run: an independent two-sample **Welch t-test** on the fourteen
per-line mean blade lengths, comparing the seven reduced-density lines with the seven
standard-density lines. Welch's version was used because it does not assume the two groups
have equal variance, and the two groups here do differ in spread. The test is two-sided at the
5% level. No test of any kind was run on individual blades, and blade wet mass was not tested;
wet mass tracks blade length closely, so it is not independent evidence.

Reported alongside the test: the difference in group means, its 95% confidence interval, and
Hedges' g, a standardised effect size that expresses the difference in units of the pooled
between-line standard deviation and applies a small-sample correction.

## Results

Sample size: **14 dropper lines**, 7 per seeding density. (140 blades were measured, 10 per
line, to produce those 14 values.)

Group summaries of the per-line averages:

| Seeding density | n (dropper lines) | Mean (cm) | SD (cm) | SEM (cm) | Min (cm) | Max (cm) |
| --- | --- | --- | --- | --- | --- | --- |
| standard | 7 | 92.72 | 9.86 | 3.73 | 78.37 | 104.90 |
| reduced | 7 | 124.56 | 6.38 | 2.41 | 111.57 | 129.56 |

Welch independent two-sample t-test on those 14 per-line averages:

| Quantity | Value |
| --- | --- |
| Mean difference (reduced minus standard) | +31.84 cm |
| 95% CI of the difference | +21.99 to +41.70 cm |
| Standard error of the difference | 4.44 cm |
| t | 7.172 |
| df (Welch) | 10.27 |
| p | 2.623e-05 |
| Hedges' g | 3.589 |

## Conclusion

Reduced seeding density produced longer blades. Averaged over its ten measured blades, a
reduced-density dropper line grew blades 31.84 cm longer than a standard-density line, and the
95% confidence interval for that difference runs from about 22 cm to about 42 cm, so the whole
interval sits well above zero. The p-value is 2.6e-05, and the effect is large relative to the
line-to-line spread (Hedges' g = 3.6). Every one of the seven reduced-density lines averaged
longer than every one of the seven standard-density lines.

Limits worth stating. This is a comparison of 7 dropper lines against 7 dropper lines on a
single longline in a single season, so the confidence interval is wide and the result speaks to
this longline and this season, not to the farm's other sites or to other years. Blades were
selected haphazardly rather than by a random rule, which can bias which blades get measured,
though averaging ten per line limits how much any one choice moves a line's value. The trial
measured blade length; it did not measure yield per metre of dropper line, and longer blades at
a lower seeding density need not mean more total biomass, because there are fewer plants on the
line. A yield comparison would answer the farm's economic question and this one does not.

Finally, the values analysed here are simulated for a self-contained example project. They are
not measurements from a real seaweed farm and should not be read as evidence about any real
cultivar, site, or season.

## Data description

The raw file is `kelp_blades.csv`: 140 data rows plus one header row.

**One row is one measured blade of sugar kelp on one dropper line.** A row is not a dropper
line and not a farm. Ten rows share a dropper line, because ten blades were measured on each
line.

Every column of `kelp_blades.csv`:

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `dropper_line` | text | none | Identifier of the dropper line the blade grew on. 14 distinct values, `L01` through `L14`, each repeated 10 times. |
| `seeding_density` | text | none | Seeding-density treatment applied to the whole dropper line. Two values, `standard` and `reduced`. Constant within a dropper line. |
| `blade_number` | integer | none | Index of the blade within its dropper line, 1 through 10, in measurement order. A within-line label only; it carries no meaning across lines. |
| `blade_length_cm` | number, 1 decimal | centimetres | Length of the measured blade at harvest, five months after deployment. This is the response variable analysed. |
| `blade_wet_mass_g` | number, 1 decimal | grams | Wet mass of the same blade, measured immediately after it came out of the water. Wet mass tracks blade length, so the two columns are not independent evidence. Not analysed here. |

There are no missing values. The per-dropper-line averages are not stored on disk;
`analysis.py` computes them from this raw file at run time.

## Files

| File | Contents |
| --- | --- |
| `kelp_blades.csv` | Raw blade measurements, one row per measured blade (140 data rows). |
| `analysis.py` | The single analysis script: averages blades to lines, then runs the one test. |
| `make_data.py` | Generator that produced the CSV (standard library only, fixed seed `20260822`). |
| `DATA_DESCRIPTION.md` | Longer description of the raw file and how its values were generated. |
| `PROTOCOL.md` | The governing protocol for the study question and the experimental unit. |
| `report.md` | This report. |

Reproduce the numbers with `python3 analysis.py` from the project root.
