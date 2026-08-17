# Entrance-reducer design and honey bee overwintering survival

## Design

24 queenright colonies in one research apiary were assigned by
coin toss to one of two winter entrance-reducer designs. Each colony was
opened once, at the spring inspection, and scored survived or died. A colony
contributes exactly one row, so the survival calls are one per independent
unit and the design-by-outcome table below counts colonies, not visits.

## Colony counts

| Entrance design | Survived | Died | Colonies | Survival |
| --- | --- | --- | --- | --- |
| notched | 9 | 3 | 12 | 0.750 |
| open | 3 | 9 | 12 | 0.250 |

Autumn strength was balanced at assignment: 8.50 bee-covered
frames on average for notched colonies against 8.50 for
open colonies, with mean autumn mite loads of 2.07 and
2.28 mites per 100 bees.

## Test

Fisher's exact test, two-sided, on the 2 x 2 table of entrance design by
overwinter outcome: [[9, 3], [3, 9]].

- Survival difference (notched minus open): 0.500
- Sample odds ratio: 9.000
- Two-sided p-value: 0.0391

[selected-result] Fisher's exact test on 24 independent colonies (one row per colony) returns a two-sided p-value of 0.0391: 9/12 (0.750) of notched colonies overwintered against 3/12 (0.250) of open colonies.

## Reading

Because each colony is observed once, there is no within-colony replication
to absorb and the row count equals the number of independent units. The
exact conditional test is used in preference to a chi-square approximation
at these cell counts, and no odds-ratio interval is quoted because the
conditional estimate is poorly determined with single-digit cells.
