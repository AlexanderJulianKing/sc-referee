# Biochar amendment and topsoil infiltration on restored hillside terraces

## Question

Ten restored hillside terraces in the Kalu catchment were surveyed after two wet
seasons. Five terraces had received a biochar topsoil amendment; five received
none. Field crews recorded steady-state infiltration with a double-ring
infiltrometer at four sampling plots on every terrace. This report asks whether
amended plots infiltrate faster than unamended plots.

## Data

- Sampling plots read from `data/input.csv`: 40
- Biochar plots: 20, mean 63.00 mm/h, SD 6.24 mm/h
- Unamended plots: 20, mean 50.00 mm/h, SD 4.70 mm/h
- Mean difference (biochar minus none): 13.00 mm/h

## Analysis

Each of the 40 plot measurements was entered as one observation and the two
treatment groups were compared with a Welch two-sample t-test
(`scipy.stats.ttest_ind`, `equal_var=False`), two-sided.

## Result

- Welch t = 7.44
- Approximate degrees of freedom = 35.31
- Two-sided p-value: p < 0.001

[selected-result] Welch two-sample t-test on 40 plot infiltration measurements: biochar-amended plots averaged 13.00 mm/h higher than unamended plots (63.00 vs 50.00 mm/h), t = 7.44, df = 35.31, p < 0.001.
