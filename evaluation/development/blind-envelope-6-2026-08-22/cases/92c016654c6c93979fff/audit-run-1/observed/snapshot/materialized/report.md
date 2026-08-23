# Larval crowding reduces adult female body size in *Anopheles*

## Aim

Adult female body size matters for malaria transmission: larger females survive longer and take
more blood meals, so anything that shrinks the emerging adults shrinks their vectorial capacity.
Larval habitats in the field are often crowded, and crowding means competition for food during the
larval instars. This study asks a single question: does rearing *Anopheles* larvae at high density
produce smaller adult females than rearing them at low density, measured by right wing length, the
standard index of mosquito body size?

## Rearing and measuring protocol

Sixteen rearing trays were set up in the insectary. Eight trays were seeded at low larval density
and eight at high larval density. Each tray received its own water, its own food ration and its own
position on the rack; the two density treatments were interleaved across the rack rather than
blocked at one end of it (low: TRAY-01, 04, 06, 08, 10, 12, 14, 15; high: TRAY-02, 03, 05, 07, 09,
11, 13, 16).

Trays were checked daily for emergence. Emergence was scored in days after the larval trays were
seeded and ran from day 9 to day 14. Ten emerged adult females per tray were killed, and the right
wing of each was removed and slide-mounted. Wing length was measured under a microscope from the
alular notch to the wing tip, excluding the fringe scales, and recorded to two decimal places in
millimetres. This gave 160 measured adult females in total, 80 per density treatment.

## Data description

The project holds one data file, `wing_lengths.csv`.

**What one row represents.** One row is one measured adult female mosquito: a single emerged
female that was killed, mounted, and had her right wing measured under the microscope. The wing
value on that row is that female's body size index.

**Columns.**

| Column | Type | Description |
|---|---|---|
| `tray.ref` | text | Label of the rearing tray the female emerged from, `TRAY-01` to `TRAY-16`. |
| `density.treatment` | text | Larval density the tray was reared at: `low` or `high`. |
| `emergence.day` | integer | Day the female emerged as an adult, counted in days after the larval tray was seeded (9-14). |
| `mosquito.no` | integer | Number of the female within her tray, 1-10, in the order the females were mounted. |
| `wing.length.mm` | number | Length of the right wing in millimetres, measured under a microscope and recorded to two decimal places. |

The file has 160 rows, one per measured female. No values are missing; every row has all five
fields filled in.

## Method

All analysis is in a single script, `analysis.py`, run with Python 3 (pandas, scipy). The script
reads `wing_lengths.csv`, summarises `wing.length.mm` within each level of `density.treatment`
(count, mean, standard deviation, standard error, minimum, maximum, median), and compares the two
treatments.

The comparison is an independent two-sample *t* test of `wing.length.mm` between the low and high
density treatments, using the Welch form so that the two treatments are not required to share a
variance. Each measured adult female contributes one wing measurement to the test, so the sample
size entering the test is the total number of measured females per treatment: 80 at low density and
80 at high density. Alongside the test the script reports the mean difference with its 95%
confidence interval, and the standardised effect size as Cohen's *d* and Hedges' *g*. Tests are
two-sided, with significance read at the conventional 5% level.

## Results

Wing measurements were obtained from all 160 adult females, 80 per treatment, with emergence
spanning days 9 to 14.

| Larval density | n measured females | Mean wing length (mm) | SD (mm) | SEM (mm) | Median (mm) | Min (mm) | Max (mm) |
|---|---|---|---|---|---|---|---|
| low | 80 | 2.973 | 0.137 | 0.015 | 3.00 | 2.61 | 3.29 |
| high | 80 | 2.781 | 0.123 | 0.014 | 2.77 | 2.53 | 3.04 |

Females reared at high larval density had shorter wings than females reared at low larval density.
The mean difference was 0.1916 mm (low minus high), 95% CI 0.1511 to 0.2322 mm, which is a 6.45%
reduction in wing length relative to the low density mean.

The independent two-sample *t* test gave *t* = 9.34 on 156.15 degrees of freedom and
*p* = 9.6 x 10^-17, with n = 80 measured females at low density and n = 80 at high density. The
standardised effect size was Cohen's *d* = 1.476 (Hedges' *g* = 1.469), a large effect by
conventional benchmarks.

The two distributions are shifted rather than separated. They overlap over most of their range: 78
of the 80 high-density females fall below the low-density median of 3.00 mm, and 57 of them fall
below the low-density lower quartile of 2.86 mm, while 31 of the 80 low-density females exceed the
largest high-density female at 3.04 mm.

## Conclusion

Rearing *Anopheles* larvae at high density produced adult females that were about 0.19 mm shorter
in the wing than females reared at low density, a reduction of roughly 6.5% in the standard body
size index. The shift is about 1.5 within-treatment standard deviations, so it is large relative to
the spread of wing lengths among the measured females, and it is statistically significant at the
5% level.

Larval crowding therefore reduces adult body size in this colony. Because wing length tracks
longevity and biting rate in *Anopheles* females, crowded larval habitats should be expected to
yield adults with lower per-female transmission potential than uncrowded habitats. For insectary
work, the practical implication is that larval density has to be held constant across treatments
whenever adult body size, or any trait that scales with it, is part of the readout: the density
contrast used here moved mean wing length by nearly as much as the whole interquartile spread of a
single density treatment (0.22 mm at low density, 0.18 mm at high density). Follow-up work could
measure whether the same crowding effect carries through to female longevity and blood-feeding
frequency directly, and whether it is driven by the food ration per larva rather than by larval
density as such.
