# Annealing and the tensile strength of printed PLA coupons

## Source

`data/input.csv` records 72 dogbone coupons cut from 12 filament spools, six
coupons per spool. Each spool went through one post-print condition and every
coupon was pulled to failure on the same screw-driven frame at 5 mm/min.

## Coupon summary

| Condition | Coupons | Mean UTS (MPa) | SD (MPa) |
| --- | --- | --- | --- |
| as_printed | 36 | 47.20 | 2.19 |
| annealed | 36 | 51.20 | 2.07 |

## Test

Two-sample Student t-test (equal variances assumed) on coupon ultimate
tensile strength, annealed against as-printed.

- Mean difference: +4.00 MPa
- Pooled SD: 2.13 MPa
- t(70) = 7.97, p < 0.0001

[selected-result] Annealed coupons failed at a higher ultimate tensile strength than as-printed coupons (51.20 vs 47.20 MPa, difference +4.00 MPa; two-sample t-test t(70) = 7.97, p < 0.0001).
