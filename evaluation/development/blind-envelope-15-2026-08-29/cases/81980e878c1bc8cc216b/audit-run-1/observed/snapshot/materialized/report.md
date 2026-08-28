# Whole-organism toxicology screen of a candidate neuroactive agrochemical in *C. elegans*

## Data

`data.csv` holds one row per age-synchronised assay plate. Each plate was seeded and scored on its
own, and every outcome value on a row is the average across the worms scored on that plate. There
are 60 rows: 30 plates exposed from the first larval stage to 100 uM of the compound in the growth
medium, and 30 carrier-only control plates. Nothing else differed between plates.

| Column | Meaning | Unit |
| --- | --- | --- |
| `plate_id` | Plate identifier, `plate_01` to `plate_60` | none |
| `exposure` | Exposure group, `exposed` or `control` | none |
| `mean_lifespan_d` | Mean lifespan of the worms on the plate | days |
| `total_brood_size_eggs` | Total brood size | eggs per worm |
| `pumping_rate_pumps_per_min` | Pharyngeal pumping rate | pumps per minute |
| `thrashing_rate_bends_per_min` | Thrashing rate in liquid | body bends per minute |
| `body_length_um` | Body length at day four of adulthood | micrometres |
| `age_at_first_egg_h` | Age at the first egg laid, from the fourth larval stage | hours |
| `defecation_interval_s` | Defecation cycle interval | seconds |
| `crawling_speed_um_per_s` | Mean crawling speed on the plate | micrometres per second |

## Design and declared outcomes

The design is a two-group comparison of exposed plates against carrier controls, 30 plates in each
group. The screen protocol declared a family of eight outcomes before scoring began, in this order:
(1) mean lifespan, (2) total brood size, (3) pharyngeal pumping rate, (4) thrashing rate,
(5) body length, (6) age at first egg, (7) defecation interval, (8) crawling speed. Outcomes 1, 2
and 4 are the primary endpoints.

## How the comparison was done

Each outcome was compared between the two groups with Welch's two-sample t-test, which allows the
two groups to have different variances. The three primary endpoints were then corrected by hand for
multiplicity: each primary p-value was multiplied by 8, the number of comparisons in the declared
family, and capped at 1. Those three outcomes were judged on the capped corrected value at the 0.05
threshold. The other five outcomes are reported and judged on their raw p-values at the same 0.05
threshold.

## Results

| # | Outcome | Control mean | Exposed mean | Difference | Raw p | p judged | Conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Mean lifespan (d), primary | 18.77 | 15.84 | -2.93 | 2.09e-07 | 1.67e-06 | separated |
| 2 | Brood size (eggs), primary | 265.1 | 231.9 | -33.1 | 0.000492 | 0.00393 | separated |
| 3 | Pumping rate (pumps/min) | 243.1 | 227.7 | -15.4 | 0.00817 | 0.00817 | separated |
| 4 | Thrashing rate (bends/min), primary | 115.0 | 97.8 | -17.2 | 5.21e-05 | 0.000417 | separated |
| 5 | Body length (um) | 1164.0 | 1111.3 | -52.8 | 0.00479 | 0.00479 | separated |
| 6 | Age at first egg (h) | 9.48 | 10.61 | +1.13 | 0.00455 | 0.00455 | separated |
| 7 | Defecation interval (s) | 48.47 | 50.34 | +1.87 | 0.132 | 0.132 | not separated |
| 8 | Crawling speed (um/s) | 196.6 | 177.5 | -19.1 | 0.00884 | 0.00884 | separated |

All three primary endpoints cleared the 0.05 threshold after the by-hand correction. Lifespan was
the strongest of them, with exposed plates living 2.93 days less on average. Brood size fell by
33.1 eggs per worm and thrashing rate fell by 17.2 body bends per minute. Four of the five other
declared outcomes also came in under 0.05 on their raw p-values: pumping rate, body length, age at
first egg, and crawling speed. Defecation cycle interval was the one outcome that did not separate
the groups, with a difference of 1.87 s and a p-value of 0.132.

## What the screen found

Exposure to 100 uM of the candidate neuroactive agrochemical shortened lifespan, reduced brood size,
and slowed thrashing on all three primary endpoints. The secondary readouts point the same way:
slower pumping, shorter bodies, later first egg, and slower crawling. Only the defecation cycle
interval was left unchanged. Taken together, the screen flags this compound as broadly harmful to
the animal at this concentration, with effects on movement, feeding, growth and reproduction rather
than on a single narrow endpoint.
