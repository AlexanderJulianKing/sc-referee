# Two six-week training blocks and 500 m ergometer power

## What we did

Eighteen rowers from the club took part. Nine completed a six-week high-intensity
interval block and nine completed a six-week steady-state endurance block. After the
block finished, each rower performed four maximal 500 metre ergometer trials, each on a
separate day, on the same machine and under the same conditions. We recorded the mean
power output over each trial in watts. That gives 72 recorded trials in total.

## The data

The measurements are in `erg_trials.csv`. **One row is one 500 metre ergometer trial
performed by one rower on one day.** It is a single trial result, not an average and not
a summary of a training block.

| Column | Type | What it holds |
| --- | --- | --- |
| `rower_id` | text | Athlete code for the rower who did the trial, `R01` through `R18`. |
| `training_block` | text | The six-week block that rower completed: `interval` or `endurance`. |
| `trial_number` | integer | Which of the four test days this trial was for that rower, 1 to 4. |
| `mean_power_w` | number | Mean power output over the 500 metre trial, in watts, to one decimal place. |

The table has 72 rows and no missing values. Rows are ordered by rower, and within a
rower by trial number.

## How we analysed it

We compared mean power between the two training blocks with an independent two-sample
t-test with pooled variance. Every measured trial in the table entered the comparison as
its own observation, so the test ran on all 72 measurements: 36 from the interval block
and 36 from the endurance block. The analysis is in `analysis.py`.

## Results

| Block | n | Mean power (W) | SD (W) | Range (W) |
| --- | --- | --- | --- | --- |
| interval | 36 | 282.42 | 25.86 | 231.1 to 322.1 |
| endurance | 36 | 266.83 | 17.66 | 231.1 to 306.2 |

The interval block produced higher mean power. Across the 72 trials the difference was
**15.59 W** in favour of the interval block (95% CI 5.18 to 26.00 W), with a pooled
standard deviation of 22.15 W. The two-sample t-test gave t(70) = 2.99, p = 0.0039, and
Cohen's d = 0.70.

## Conclusion

Rowers who completed the six-week high-intensity interval block produced about 16 watts
more mean power over a maximal 500 metre ergometer piece than rowers who completed the
steady-state endurance block. The difference is statistically significant at the 5%
level and corresponds to a moderate effect size. On this evidence the interval block is
the better choice for club rowers preparing for short maximal efforts, and we intend to
use it in the pre-season programme.
