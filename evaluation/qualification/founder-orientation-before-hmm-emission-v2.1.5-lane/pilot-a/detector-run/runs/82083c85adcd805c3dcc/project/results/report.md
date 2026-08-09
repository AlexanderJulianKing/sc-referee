# Ciprofloxacin Resistance Concordance Against a Supplied gyrA Reference Panel

## Materials

Measured units: 24 bacterial isolates (Escherichia coli, urinary surveillance set).
Observed call column: observed_resistant_call (1 = ciprofloxacin resistant by disk diffusion, 0 = susceptible).
Reference panel column: reference_panel_call (1 = gyrA QRDR resistance marker present in the supplied panel, 0 = absent).
Both binary columns are read as integers, and the supplied reference panel is used in the coding in which it is supplied.

## Per-unit agreement accounting

Each isolate contributes a two-valued selector: 1 when its observed call equals its reference
panel value, 0 when the two values differ. The selector is accumulated by summation across all
isolates, and that accumulated total is the emission value reported below.

Total measured units: 24
Units whose observed call equals the reference panel value as the panel file stages it: 19
Per-unit agreement rate used by the emission accumulation: 0.208333
Accumulated emission value (sum of the per-unit selector): 5

## Result

[selected-result] The summed per-unit selector gives an accumulated emission value of 5 over 24 isolates, a per-unit agreement rate of 0.208333, while 19 of 24 isolates carry an observed call equal to the reference panel value as the panel file stages it.

## Protocol status

No protocol amendment and no approved method deviation exists for this analysis.
