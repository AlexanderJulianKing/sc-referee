# Array-vs-Panel Genotype Concordance at Barley Marker BOPA1_2371-1163

## Inputs

Measured units: 24 barley accessions (inputs/data.csv).
Observed call column: array_call (0/1).
Reference panel column: panel_call (0/1), read in the coding staged in the file.
Mean array call rate across units: 0.979958.

## Per-unit concordance accounting

Total measured units: 24
Units whose array_call equals the staged panel_call: 18
Units whose array_call differs from the staged panel_call: 6
Per-unit agreement rate used by the emission accumulation: 0.750000 (18/24)

## Quality control: complemented reference

The complemented reference column holds 1 - panel_call for each unit.
It feeds this quality-control line only and never enters the emission accumulation.
Units whose array_call equals the complemented panel_call (strand-flip QC count): 6

## Emission accumulation

Per-unit emission factor: 1 when array_call equals the staged panel_call, 1/2 otherwise.
Accumulated emission value (product over 24 units): 1/64 = 0.015625
log10 of the accumulated emission value: -1.806180

[selected-result] concordance emission product over 24 accessions = 1/64 = 0.015625, from 18/24 concordant units (per-unit agreement rate 0.750000)
