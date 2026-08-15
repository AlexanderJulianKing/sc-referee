# Seagrass meadow extent change under two anchoring regimes

## Data

Each row of `data/input.csv` is one seagrass meadow surveyed once, so the
meadow is the independent unit and contributes exactly one extent-change value.

- Meadows analysed: 10
- No-anchoring zones: 5 (median extent change 7.60 %)
- Open-access meadows: 5 (median extent change -6.80 %)

## Analysis

Two-sided Mann-Whitney U test comparing the 2015-2025 change in mapped meadow
area between no-anchoring zones and open-access meadows. The exact null
distribution is used (5 and 5 meadows per regime, all values distinct), so
no normal approximation or tie correction enters the calculation.

## Result

- U statistic (no-anchoring zones) = 23.0
- Exact two-sided p-value = 0.0317
- Rank-biserial correlation = 0.840

[selected-result] Meadow extent change differed between anchoring regimes (exact two-sided Mann-Whitney U = 23.0, 5 vs 5 meadows, p = 0.0317, rank-biserial 0.840): no-anchoring meadows gained area (median +7.60 %) while open-access meadows lost area (median -6.80 %).
