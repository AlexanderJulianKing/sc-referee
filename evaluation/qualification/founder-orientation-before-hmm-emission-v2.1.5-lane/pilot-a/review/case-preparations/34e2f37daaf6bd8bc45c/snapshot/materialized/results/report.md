# Ciprofloxacin Resistance Concordance Against a Supplied gyrA Reference Panel

## Materials

Measured units: 24 bacterial isolates (Escherichia coli, urinary surveillance set).
Observed call column: observed_resistant_call (1 = ciprofloxacin resistant by disk diffusion, 0 = susceptible).
Reference panel column: reference_panel_call (1 = gyrA QRDR resistance marker present in the supplied panel, 0 = absent).
The comparison uses the reference panel exactly as the panel file stages it.

## Per-unit agreement accounting

Each isolate contributes a two-valued selector: 1 when its observed call equals its staged
reference panel value, 0 when the two values differ. The selector is accumulated by summation
across all isolates, and that accumulated total is the emission value reported below.

Total measured units: 24
Units whose observed call equals the staged reference panel value: 19
Units whose observed call differs from the staged reference panel value: 5
Per-unit agreement rate used by the emission accumulation: 0.791667
Accumulated emission value (sum of the per-unit selector): 19

## Result

[selected-result] Observed ciprofloxacin resistance calls agree with the supplied gyrA reference panel on 19 of 24 isolates, a per-unit agreement rate of 0.791667, and the summed per-unit selector gives an accumulated emission value of 19.

## Scope

Every claim above rests on the single staged-coding equality comparison of
observed_resistant_call against reference_panel_call; the workflow performs no other
comparison of those two columns and reports no quantity beyond this accounting.
