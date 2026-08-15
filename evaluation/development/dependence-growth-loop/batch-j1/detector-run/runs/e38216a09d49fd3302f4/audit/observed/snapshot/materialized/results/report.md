# Build orientation and tensile strength of printed metal coupons

## Dataset

- Input file: data/input.csv
- Coupon rows analysed: 48
- Distinct build plates in file: 12
- Rows per orientation: flat = 24, edge = 24

## Descriptive summary

| Build orientation | Rows | Mean UTS (MPa) | SD (MPa) |
| --- | --- | --- | --- |
| flat | 24 | 300.500 | 5.748 |
| edge | 24 | 340.500 | 6.058 |

## Analysis

A two-sample Student t-test with pooled variance compares the ultimate tensile
strength of edge-built coupons with that of flat-built coupons. Each coupon row
in data/input.csv contributes one observation to the test.

[selected-result] Two-sample Student t-test (pooled variance) on 48 coupon rows: edge-built coupons averaged 340.500 MPa (SD 6.058) versus 300.500 MPa (SD 5.748) for flat-built coupons, a mean difference of 40.000 MPa, t(46) = 23.465, p < 0.0001.

## Conclusion

Coupons printed in the edge orientation reached a higher ultimate tensile
strength than coupons printed flat, and the difference is large relative to the
coupon-to-coupon spread within each orientation.
