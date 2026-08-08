# Transit Yield Over the Complete Planned Pointing Set

## Subject area and scientific target

Subject area: ground-based time-series photometry of candidate transiting
exoplanet host stars. The scientific target of this analysis is the complete
planned set of scheduled pointings: all 48 pointings on the observing plan.

## Planned unit accounting

- Planned pointings (observation units): 48
- Retained after prespecified screening: 36
- Removed by prespecified screening: 12
- Transit-like dip detections among retained pointings: 9

## Prespecified screening step

A pointing is eligible when its photometric scatter is at most 1.50 ppt and its
time-series coverage fraction is at least 0.90. Pointings failing either
criterion were removed before the dip search was run. The 12 removed pointings
were never searched, so their event status is recorded as NA in inputs/data.csv
rather than as a confirmed zero.

## Selected result

The declared scientific target is the complete planned set, so the exposure
denominator is all 48 planned pointings. The numerator is the 9 dip detections
actually made. The 12 removed pointings stay in the denominator as planned
exposure that yielded no detection.

[selected-result] Transit-like dip yield over the complete planned set: 9 detections / 48 planned pointings = 0.187500 (18.75 per 100 planned pointings).

## Scope of claims

This rate is a yield per planned pointing for this observing plan as executed.
It is not a per-retained-pointing detection probability, and it is not an
estimate of the fraction of the 48 target stars that host transiting planets.
Because the 12 removed pointings were never searched, the reported yield is a
lower bound on the number of detectable dips per planned pointing: any dip
present in a removed pointing is counted as absent here. No claim is made about
the 12 removed pointings individually.

## Reproducibility

All counts and the reported rate are computed from inputs/data.csv by
workflow/analysis.py; no result value is hard-coded.
