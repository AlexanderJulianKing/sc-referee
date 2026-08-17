# Adaptive noise-floor gate on gearbox acoustic-emission windows

## Data

- Source table: `data/input.csv`
- Recording windows analysed: 20
- Gearboxes represented: 6
- Wind bins represented: low, mid, high

## Analysis

Each 10-minute acoustic-emission window was processed twice, once with
the baseline spectral gate and once with the adaptive gate. The
noise-floor reduction for a window is `baseline_floor_db -
adaptive_floor_db`, so a positive value means the adaptive gate reached
the lower floor. Every window in the table was entered as one
independent trial in an exact two-sided binomial sign test
(`scipy.stats.binomtest`) against the null hypothesis that the adaptive
gate wins in half of the windows.

## Result

- Windows where the adaptive gate reached the lower floor: 15 of 20 (0.750)
- Median reduction: 1.40 dB
- Mean reduction: 1.03 dB
- Exact two-sided binomial p-value: 0.0414

[selected-result] Exact two-sided binomial sign test over 20 recording windows entered as independent trials: the adaptive gate reached the lower noise floor in 15 of 20 windows (share 0.750, median reduction 1.40 dB), p = 0.0414, so the 50% null is rejected at alpha = 0.05.
