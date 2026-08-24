# Whole-body vibration at the tractor seat pan: air-suspension seat versus standard mechanical seat

## What we did

We compared whole-body vibration exposure between two tractor seat types on a large arable
estate. Twenty of our operators took part. Ten drove machines fitted with an air-suspension
seat and ten drove machines fitted with the standard mechanical seat. Seat type was fixed for
an operator: nobody swapped seats part-way through.

We instrumented each operator during six separate field runs, carried out on different days
over the same cultivated ground. The outcome is the vibration total value measured at the seat
pan, in metres per second squared. That gives 120 measured runs in the file, but only 20
independent people. The six runs belonging to one operator are repeat measurements on the same
person on the same machine, so they are not independent of each other, and we treated the
operator as the unit of analysis throughout.

## The data

The study uses a single data file, `vibration_runs.csv`, with a header row and 120 data rows.

**One row is one instrumented field run by one operator**: the vibration measurement recorded at
the seat pan during a single day's run over the cultivated ground. A row is not an operator.
Each operator contributes six rows.

The file has four columns, in this order.

| Column | Type | Values | What it holds |
| --- | --- | --- | --- |
| `operator_code` | text | `OP-01` to `OP-20` | The staff code of the tractor operator. This is our unit of analysis and our clustering variable: the six rows sharing a code are repeat measurements on the same person. |
| `seat_type` | text | `air_suspension` or `mechanical` | The seat fitted to the machine that operator drove. `air_suspension` is the air-suspension seat, `mechanical` the standard mechanical seat. Constant within an operator. |
| `run_number` | integer | 1 to 6 | Numbers the field run within that operator, in the order the runs were carried out on different days. It restarts at 1 for each operator, so it only means anything alongside `operator_code`. It is not a date, and it is not unique across the file. |
| `vibration_total_value_ms2` | number, 2 decimal places | 0.41 to 1.43 in this file | The outcome: the vibration total value at the seat pan for that run, in metres per second squared. The units are in the column name. Our field instruments report to two decimal places. |

There are no missing values, no duplicated operator-and-run pairs, and the design is balanced:
every operator has all six runs, and there are 10 operators (60 rows) in each seat group.

## What the measurements look like

| | Air-suspension | Mechanical |
| --- | --- | --- |
| Operators | 10 | 10 |
| Runs | 60 | 60 |
| Mean over runs (m/s²) | 0.792 | 1.099 |
| Standard deviation over runs (m/s²) | 0.175 | 0.175 |
| Range over runs (m/s²) | 0.41 to 1.11 | 0.61 to 1.43 |
| Spread of the 10 operator means (m/s²) | 0.156 | 0.161 |

The average spread of runs *within* one operator is 0.091 m/s², against a spread *between*
operators of about 0.16 m/s². Most of the variation in the file therefore sits between people,
not between one day's run and the next. That is the whole reason the analysis has to be done on
operators: the extra runs tell us a lot about where an individual operator sits, and rather
little that is new about how the two seats compare.

## How we analysed it

Our primary inference is a resampling procedure we wrote out ourselves rather than taking from a
package, and it resamples **whole operators**. When an operator is drawn, all six of that
operator's runs come with them, so the family resemblance among one person's runs is carried into
every resampled dataset. Think of it as drawing people out of a hat rather than drawing loose
measurements out of a hat. We drew 20,000 operator-level resamples, stratified by seat type so
that the ten-and-ten design is held fixed, and took the 2.5th and 97.5th percentiles of the
resampled differences as the confidence interval.

For the p-value we used a second operator-level resampling procedure: reassigning the seat labels
to whole operators. Under the idea that the seat makes no difference, an operator's whole six-run
record would have looked the same whichever seat had been fitted, so the labels can be shuffled
over operators. There are only 184,756 ways of choosing which ten of the twenty operators carry
the mechanical label, so we enumerated all of them rather than sampling. The p-value is exact.

Both procedures are in `analysis.py`, the only analysis script in the project. It reads the CSV
and prints everything reported here.

## Results

**The primary, dependence-aware result. n = 20 operators, 10 per seat group.**

The mechanical seat gave a higher vibration total value than the air-suspension seat by
**0.307 m/s²** (95% confidence interval 0.177 to 0.439 m/s², from 20,000 operator-level
resamples; bootstrap standard error 0.067 m/s²). The exact operator-level permutation test gives
a two-sided p-value of **0.00048** (88 of 184,756 label assignments were as extreme as, or more
extreme than, the one we observed).

So the air-suspension seat cut exposure by roughly a quarter to a third of a metre per second
squared, on a mechanical-seat baseline of about 1.10 m/s². Our sample size for this comparison is
20 operators, not 120 runs.

**An illustrative contrast, which is not valid inference here.**

If we ignore the clustering and run a plain two-sample Welch t-test across all 120 individual
runs, we get the same point estimate of 0.307 m/s², but a standard error of 0.032 m/s², a 95%
interval of 0.243 to 0.370 m/s², and t = 9.61 on 118 degrees of freedom, p = 1.7 × 10⁻¹⁶.

**This row-level comparison is not valid for inference in this study.** It treats six repeated
runs on one operator as six independent observations, which they are not: the runs are repeat
measurements on the same person and the same machine, and seat type does not vary within an
operator. Counting them as independent inflates the apparent sample size from 20 to 120 and
understates the uncertainty. The standard error it reports is less than half the honest one
(0.032 against 0.067 m/s²), the interval is half as wide, and the p-value is smaller by about
twelve orders of magnitude. We show it only so the size of that distortion is visible. It is not
the basis of any conclusion below.

## What we conclude

Fitting the air-suspension seat lowered whole-body vibration at the seat pan by about
0.31 m/s² compared with the standard mechanical seat, with a 95% confidence interval of roughly
0.18 to 0.44 m/s² (exact operator-level permutation p = 0.00048). This rests on the
dependence-aware analysis of **20 operators, ten per seat type**.

The interval is wide because twenty people is a small study, and because operators differ from
one another more than one operator's days differ among themselves. Running more days per operator
would not narrow it much. Recruiting more operators would.

Two limits are worth stating plainly. Seat type was not randomised within an operator, so an
operator's driving style, machine, and usual ground are bound up with the seat they had, and we
cannot separate those from the seat itself. And all runs were over the same cultivated ground on
one estate, so the size of the benefit on other surfaces or other machines is not something this
study can speak to.
