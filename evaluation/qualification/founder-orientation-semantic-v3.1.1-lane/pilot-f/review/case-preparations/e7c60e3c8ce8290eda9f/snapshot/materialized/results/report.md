# Ciprofloxacin resistance calls versus two reference marker panels

## Units and staging

Measured units: 25 clinical Escherichia coli isolates.
Observed call column: observed_resistant (1 = disk-diffusion resistant phenotype).
Primary reference column: panel_a_resistant (curated QRDR mutation panel), used exactly as staged.
Second reference column: panel_b_resistant (independent PMQR and efflux marker panel), used exactly as staged.
Mean inhibition-zone diameter: 21.20 mm.
Isolates resistant by observed phenotype: 14.
Isolates resistant by panel A: 13.
Isolates resistant by panel B: 13.

## Concordance accounting

Units whose observed call equals the staged panel A value: 20 of 25.
Units whose observed call and staged panel A value are not equal: 5 of 25.
Per-unit agreement rate used by the emission accumulation: 0.8 (= 4/5 in lowest terms).
Per-unit disagreement weight used by the emission accumulation: 0.2.
Second-reference check, units whose observed call equals the staged panel B value: 18 of 25.

## Emission accumulation

The emission value is the product over all 25 isolates, contributing 0.8 for each
isolate whose observed call equals its staged panel A value and 0.2 for each isolate
where the two values are not equal: 0.8^20 * 0.2^5.

Accumulated emission value: 0.0000036893488147419103232

[selected-result] Panel A emission over 25 isolates at per-unit agreement rate 0.8 = 0.0000036893488147419103232
