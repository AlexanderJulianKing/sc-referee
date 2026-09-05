# Sit-stand desks in an office population: three-month results

## What we did

Occupational health fitted sit-stand desks on two floors (52 staff) and left two
comparable floors on fixed desks (52 staff). At three months we collected self-
reported workplace sitting and standing hours, three symptom scores, and a
self-rated productivity score. `analysis.py` compares the two desk groups on each of
the six outcomes with a Welch two-sample t-test.

## Results

| Outcome | Fixed | Sit-stand | p | Below 0.05? |
|---|---|---|---|---|
| Sitting hours/day | 6.19 | 4.55 | 1.3e-09 | yes |
| Standing hours/day | 0.61 | 2.22 | 4.7e-17 | yes |
| Low back pain (0-10) | 3.36 | 3.35 | 0.99 | no |
| Neck/shoulder pain (0-10) | 3.02 | 3.11 | 0.80 | no |
| End-of-day fatigue (0-10) | 4.84 | 4.00 | 0.0027 | yes |
| Self-rated productivity (0-10) | 6.42 | 7.04 | 0.044 | yes |

The behaviour change is not in doubt. Staff with sit-stand desks sat about 1.6 hours
less and stood about 1.6 hours more per working day, and those two outcomes are
essentially the same fact measured twice. Beyond that, the picture is mixed: reported
end-of-day fatigue was about 0.8 points lower in the sit-stand group, self-rated
productivity about 0.6 points higher, and neither pain score moved at all.

## Recommendation

Offer sit-stand desks building-wide, on request rather than as a blanket replacement.
The desks reliably do the thing they are sold to do, which is get people out of their
chairs, and the two outcomes that shifted point in a favourable direction. That is
enough to justify meeting demand from staff who want one, especially where a desk can
be reallocated when someone leaves.

It is not enough to justify a full refit, and the report should not oversell it. Three
points of caution:

- Neither pain score improved. If the business case is musculoskeletal symptoms, these
  data do not support it at three months.
- Fatigue and productivity are self-reported by staff who know which desk they were
  given. Neither outcome is blind, and both are the kind of measure that responds to
  having been chosen for a pilot.
- Floors were not randomised, and six outcomes were each tested against the same
  0.05 cutoff. Productivity at p = 0.044 is the weakest result in the table and the
  one most likely to look different with another three months of data.

A twelve-month follow-up on the same staff, with the pain scores as the pre-specified
primary outcomes, would settle the part of this that matters for occupational health.
