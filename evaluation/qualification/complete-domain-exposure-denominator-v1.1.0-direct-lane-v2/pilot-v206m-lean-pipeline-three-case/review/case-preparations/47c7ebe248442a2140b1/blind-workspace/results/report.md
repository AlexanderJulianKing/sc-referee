# Transit-Candidate Yield Across the Planned Target List

## Scientific target

The scientific target is the complete planned target list of 40 survey
stars. All rates below use that complete planned set as the exposure
denominator.

## Unit accounting

| quantity | count |
| --- | --- |
| planned observation units (stars) | 40 |
| retained after screening | 32 |
| removed by screening | 8 |
| transit-like dip detections among retained stars | 6 |

## Prespecified screening rule

A planned star is retained when phase coverage is at least 0.90 of the
observing window and photometric RMS is at most 5.00 ppt. Both conditions
are evaluated from inputs/data.csv; no other criterion is applied.

Removal reasons among the 8 removed stars:

| reason | count |
| --- | --- |
| coverage below 0.90 only | 4 |
| RMS above 5.00 ppt only | 3 |
| both criteria failed | 1 |

## Selected result

[selected-result] Transit-like dip detection rate over the complete planned target list: 6 detections / 40 planned stars = 0.1500 (15.00 percent).

## Per-field breakdown

| field | planned | retained | removed | detections | detections per planned star |
| --- | --- | --- | --- | --- | --- |
| F1 | 10 | 9 | 1 | 1 | 0.1000 |
| F2 | 10 | 8 | 2 | 2 | 0.2000 |
| F3 | 10 | 7 | 3 | 1 | 0.1000 |
| F4 | 10 | 8 | 2 | 2 | 0.2000 |

## Interpretation limits

The selected rate is a per-planned-star yield: its denominator is all 40
planned stars, including the 8 that screening removed. The 8 removed stars
contribute 0 detections to the numerator because their light curves were
not assessed for transit-like dips, so the reported rate is a lower bound
on the yield that fully usable observations of all 40 stars would have
produced. No claim is made here about the detection rate among the 32
retained stars alone.
