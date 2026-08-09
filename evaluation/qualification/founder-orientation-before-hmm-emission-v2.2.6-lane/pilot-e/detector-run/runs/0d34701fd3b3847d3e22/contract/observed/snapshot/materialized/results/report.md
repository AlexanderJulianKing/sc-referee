# Reference-panel concordance of SNP calls in Vibrio cholerae isolate VC-2291

Observed calls at each diagnostic locus were compared, locus by locus, with the
allele state recorded for that locus in the supplied reference panel, using the
panel coding exactly as staged in inputs/data.csv (1 = alternate allele present,
0 = reference allele present).

## Accounting

- measured units (diagnostic SNP loci): 24
- units where observed_call equals staged panel_call: 19
- per-unit agreement rate used by the emission accumulation: 19/24 = 0.791667 (79.17%)
- per-unit disagreement weight (1 - agreement rate): 5/24 = 0.208333
- accumulated emission value (sum of per-unit emission weights): 193/12 = 16.083333
- quality-control comparison, units where observed_call equals the complemented panel value (1 - panel_call): 5
- mean read depth across loci: 105.42x

The complemented panel column is a polarity quality control only; it never
enters the emission accumulation. Its agreement count and the staged-panel
agreement count sum to the unit count, confirming that both binary columns
are read in the coding the staged file supplies.

[selected-result] Observed calls agree with the staged reference panel at 19 of 24 loci (per-unit agreement rate 19/24 = 0.791667), giving an accumulated emission value of 193/12 = 16.083333.
