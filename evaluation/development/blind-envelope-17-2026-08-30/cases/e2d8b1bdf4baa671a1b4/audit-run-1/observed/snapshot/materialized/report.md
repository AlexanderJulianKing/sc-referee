# Rearing temperature and life history in *Daphnia magna*

## Question

Does rearing temperature shift life-history traits in *Daphnia magna*? Eighty animals from a single
clonal line were reared individually from birth, forty in vessels held at 18 degrees Celsius and
forty in vessels held at 24 degrees Celsius, on the same algal feeding regime and the same water
renewal schedule. Rearing temperature is the only condition that differs between the two sets of
vessels, and the two temperatures are the only comparison in the experiment.

## Data

File: `daphnia_temperature.csv`. One row is one animal: a single individually reared *Daphnia
magna*, followed from birth, with its rearing temperature and its four declared outcomes. There are
80 data rows, 40 per temperature, with a value in every cell.

Columns, in file order:

- `animal_id` - identifier for the animal, the prefix `dm` plus a zero-padded two-digit serial
  number, `dm01` through `dm80`.
- `temperature_c` - group column, the rearing temperature of the vessel in degrees Celsius, with
  exactly two distinct values, 18 and 24.
- `age_first_brood_days` - declared outcome 1, age at first brood release in days, counted from
  birth, recorded on a 0.5-day grid because vessels were inspected twice a day.
- `body_length_day14_mm` - declared outcome 2, body length on day fourteen in millimetres, read with
  an ocular micrometer on a stereomicroscope to 0.01 mm.
- `offspring_day21` - declared outcome 3, cumulative count of neonates released by day twenty-one.
- `heart_rate_day10_bpm` - declared outcome 4, heart rate on day ten in beats per minute, from beats
  counted over a timed window under the stereomicroscope.

Columns three through six are the four outcomes of the declared outcome family, in the order fixed
in the experimental plan before the animals were set up.

## How the comparison was done

The four outcomes were declared in advance as one family. Each outcome was compared between the 18
degree and 24 degree groups with a standard two-group comparison test for continuous data, and the
four resulting p-values were kept together in the declared order. All four p-values were then passed
in a single call, covering the complete family, to the standard multiple-comparison adjustment
routine of a widely used general-purpose Python statistics library. No correction method was chosen,
named or configured: the routine was called without a method argument and whatever adjustment it
applies by default was accepted. Every verdict below is read from the adjusted p-value returned by
that routine, at the conventional 0.05 threshold. No outcome is given a verdict from an unadjusted
p-value.

The analysis is in `analysis.py`, which reads the committed CSV and prints, for each outcome in the
declared order, the two group means, the unadjusted p-value for reference, the adjusted p-value and
the verdict.

## Results

The values below are the numbers printed by `analysis.py`.

**1. Age at first brood release (days).** Mean 9.14 days at 18 degrees and 7.54 days at 24 degrees.
Adjusted p = 7.41e-10. Significant. Warm-reared animals released their first brood about 1.6 days
earlier.

**2. Body length at day fourteen (mm).** Mean 3.32 mm at 18 degrees and 3.02 mm at 24 degrees.
Adjusted p = 9.26e-08. Significant. Warm-reared animals were about 0.30 mm shorter at day fourteen.

**3. Cumulative offspring by day twenty-one (count).** Mean 42.98 neonates at 18 degrees and 54.08
at 24 degrees. Adjusted p = 1.68e-05. Significant. Warm-reared animals produced about 11 more
offspring over the first three weeks.

**4. Heart rate at day ten (bpm).** Mean 272.10 bpm at 18 degrees and 337.58 bpm at 24 degrees.
Adjusted p = 2.36e-11. Significant. Warm-reared animals ran about 65 bpm faster.

All four declared outcomes were significant after the family-wide adjustment.

## Conclusion

Rearing at 24 degrees rather than 18 degrees shifts *Daphnia magna* toward a faster life history.
Animals held warm matured sooner, ran a faster heart rate and produced more offspring by day
twenty-one, but were smaller at day fourteen. That is the usual temperature trade-off in this
species: faster development and higher early reproductive output, paid for in body size.
