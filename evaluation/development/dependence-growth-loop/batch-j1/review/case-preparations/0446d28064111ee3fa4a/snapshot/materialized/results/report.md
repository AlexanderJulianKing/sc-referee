# Structural damping of machine-tool bases: gray cast iron vs. polymer concrete

## Data

Modal impact tests on machine-tool bases. Each row of the input table is one
instrumented hammer strike, and the response variable is the first-mode damping
ratio expressed as a percentage of critical damping. The table holds 60 strikes:
6 gray cast iron bases and 6 polymer concrete bases, with 5 strikes recorded on
each base.

## Analysis

Welch's two-sample t-test (scipy.stats.ttest_ind with equal_var=False) compares
the damping ratio of polymer concrete strikes against gray cast iron strikes.
Every recorded strike is entered into the test as one observation, so each
material group contributes 30 observations.

## Result

| material         | strikes | mean damping ratio (%) |
| ---------------- | ------- | ---------------------- |
| gray_cast_iron   | 30      | 1.190                  |
| polymer_concrete | 30      | 2.510                  |

Mean difference (polymer concrete minus gray cast iron): 1.320 percentage
points. Welch t = 17.11, df = 40.2, p < 1e-15.

[selected-result] Polymer concrete machine-tool bases damp the first bending mode more strongly than gray cast iron bases: mean damping ratio 2.510% versus 1.190%, a difference of 1.320 percentage points (Welch two-sample t-test over 30 strikes per material, t = 17.11, df = 40.2, p < 1e-15).
