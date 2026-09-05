# Pre-registered trial of a universal school breakfast programme

One set of primary schools ran a free universal breakfast programme for an academic year
while matched schools did not. Data are one row per child, 80 children per condition,
160 in total. The analysis plan was registered before any data were collected.

## The registered decision rule

The registered plan states:

> "The confirmatory family consists of four child outcomes: attendance, literacy,
> numeracy, and BMI z-score. Each outcome is compared between conditions with a
> two-sample test for a difference in means. An outcome is declared to show an effect
> only if its p-value is below 0.0125. No further outcomes enter the confirmatory
> family and no post-hoc adjustment is applied."

The family is fixed at those four outcomes, and 0.0125 is the five-percent family-wide
level shared equally across the four tests. The arithmetic, stated once here and nowhere
else:

    0.05 / 4 = 0.0125

Splitting the five-percent budget four ways is what keeps the chance of at least one
false positive across the whole family near five percent rather than near twenty. The
threshold was set before the data existed, which is what stops it from being negotiated
afterwards. `analysis.py` compares each p-value with the plain number 0.0125 and does no
arithmetic on it.

## Results against the registered threshold

| Outcome | No programme | Breakfast | Difference | p | Decision at 0.0125 |
|---|---|---|---|---|---|
| Attendance (%) | 91.02 | 93.02 | +2.01 | 0.0277 | retain null |
| Literacy score | 98.55 | 101.88 | +3.33 | 0.1374 | retain null |
| Numeracy score | 99.05 | 101.26 | +2.21 | 0.3317 | retain null |
| BMI z-score | 0.42 | 0.35 | -0.07 | 0.6706 | retain null |

None of the four outcomes met the registered threshold.

## Conclusion

The trial does not demonstrate an effect of the breakfast programme on any of its four
registered outcomes.

Attendance is the outcome worth discussing honestly. Breakfast schools ran two
percentage points higher, and at p = 0.0277 that would have been called significant
against an unadjusted five-percent threshold. It does not meet the threshold that was
registered. The whole point of fixing 0.0125 in advance was to remove the temptation to
argue this case after seeing it, so the registered decision stands: the null is retained
for attendance. What can fairly be said is that attendance is the outcome that moved
most, in the expected direction, and that it is the right primary outcome for a larger
confirmatory trial. Two percentage points of attendance is about four extra days in a
190-day school year, which would matter if it holds up.

Literacy and numeracy both leaned positive, by about a quarter and a seventh of a
standard deviation, but with p-values of 0.14 and 0.33 they are indistinguishable from
noise at this sample size. BMI z-score barely moved.

With 80 children per condition this trial was never going to detect small effects, and
the results should be read as a signal for where to point a bigger study rather than as
evidence that free breakfast does nothing.
