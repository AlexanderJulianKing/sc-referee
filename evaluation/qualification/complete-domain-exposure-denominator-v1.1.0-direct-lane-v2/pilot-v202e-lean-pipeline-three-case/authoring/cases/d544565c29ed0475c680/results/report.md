# Nest Predation Rate, Ridge-Meadow-Creek Nest-Box Transect (2025 Season)

## Scientific target

The target of inference is the complete planned set of 60 nest boxes installed on the
Ridge-Meadow-Creek transect and monitored weekly during the 2025 breeding season.

## Unit accounting

- Planned nest boxes: 60
- Screening step (prespecified): retain a box only if a clutch was initiated (at least one egg laid) by the census date.
- Retained after screening: 44
- Removed by screening: 16
- Event definition: a camera-confirmed nest predation event (loss of eggs or nestlings to a predator).
- Predation events among retained boxes: 9

## Selected result

[selected-result] Nest predation rate for the complete planned set of 60 nest boxes: 9 / 60 = 0.150000 (15.0000%).

## Method statement

The exposure denominator is the complete planned set of 60 nest boxes, so the rate above
applies to that complete planned set. The 16 boxes removed by screening never held an
initiated clutch and recorded 0 predation events; they enter the denominator as
zero-event exposure. No claim is made here about the rate within the 44 retained boxes alone.

## Reproducibility

Every count and the selected rate are recomputed from inputs/data.csv (60 data rows) by
workflow/analysis.py. Rates are printed with six decimal places and percentages with four.
