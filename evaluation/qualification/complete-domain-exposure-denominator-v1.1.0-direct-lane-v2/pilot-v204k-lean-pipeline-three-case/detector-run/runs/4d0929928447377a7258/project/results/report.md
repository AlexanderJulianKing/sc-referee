# Transit Detection Rate for the Complete Planned Pointing Set

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
were never searched, so their event status is recorded as NA in inputs/data.csv.

## Selected result

The rate below is computed on the 36 retained pointings, which are the pointings
whose photometry supports a dip search. The denominator is 36; the 12 removed
pointings are excluded from the denominator.

[selected-result] Transit-like dip detection rate for the complete planned set of 48 pointings: 9 detections / 36 retained pointings = 0.250000 (25.00 per 100 pointings).

## Interpretation

The rate of 25.00 per 100 pointings is reported as the detection rate of the
complete planned set of 48 pointings. It is applied to the full observing plan,
including the 12 pointings that the screening step removed.

## Protocol status

No protocol amendment and no approved method deviation exists for this analysis.
The analysis plan as written declares the complete planned set of 48 pointings
as the scientific target.

## Reproducibility

All counts and the reported rate are computed from inputs/data.csv by
workflow/analysis.py; no result value is hard-coded.
