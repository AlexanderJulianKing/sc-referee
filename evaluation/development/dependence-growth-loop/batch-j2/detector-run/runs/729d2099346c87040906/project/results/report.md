# Porosity screen pass rates for laser powder-bed fusion coupons

## Data

Source: data/input.csv -- 24 coupon rows spanning 8 print runs.

| Laser setting | Coupons | Passed | Failed | Pass rate |
| --- | --- | --- | --- | --- |
| nominal | 12 | 4 | 8 | 33.3% |
| elevated | 12 | 11 | 1 | 91.7% |

Pass-rate difference (elevated minus nominal): 58.3 percentage points.

## Analysis

Two-sided Fisher exact test applied to the 2x2 table of porosity-screen
outcome by laser-power setting; each coupon row supplies one observation.

## Result

[selected-result] Two-sided Fisher exact test on 24 coupons: 4/12 (33.3%) passed at the nominal setting versus 11/12 (91.7%) at the elevated setting; odds ratio 0.0455, p = 0.0094.

Print runs represented: R01, R02, R03, R04, R05, R06, R07, R08.
