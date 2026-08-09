# Ciprofloxacin resistance: phenotype call vs reference panel gyrA marker

## Dataset

Measured units: 24 clinical Escherichia coli isolates.
Observed call column: phenotype_resistant (1 = resistant by disc diffusion).
Reference column as staged: panel_gyra_marker (1 = resistant-associated gyrA allele).
Mean ciprofloxacin MIC across all isolates: 6.796875 mg/L.
Isolates called resistant by phenotype: 13.
Isolates carrying the panel resistance allele: 12.

## Concordance accounting

Total measured units: 24
Units whose observed call equals the staged panel value: 19
Per-unit agreement rate used by the emission accumulation: 19/24 = 0.791667
Per-unit emission factor: 1 on agreement, 1/2 on disagreement.
Accumulated emission value (product over all 24 units): 1/32 = 0.031250

## Quality control

Complement check count (observed call equals 1 - staged panel value): 5
The complemented reference copy is an orientation control only; it never enters
the emission accumulation, which uses the panel values exactly as staged.
Agreement count plus complement check count: 24 (equals the total unit count).

[selected-result] Accumulated emission value over 24 isolates = 1/32 = 0.031250, from 19 of 24 units in agreement (rate 0.791667).
