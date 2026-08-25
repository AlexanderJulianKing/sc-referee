# Larvicide versus nets alone in the coastal district

52 villages were surveyed through one wet season, 26 under the larvicide regime and 26
under distribution of insecticide-treated nets alone. Each village contributes one row
and five outcomes. All five outcomes were tested with a two-sample Welch t-test on the
difference in means.

## Correction

The five raw p-values were passed as one list in a single call to
`statsmodels.stats.multitest.multipletests` at a family-wide error rate of 5 percent.
The correction method was left at the routine's default, which is `hs`, the Holm-Sidak
step-down procedure. The family is all five outcomes in the table below, including the
cost outcome; nothing was tested outside it and nothing was corrected separately. The
reject decisions and adjusted p-values printed by the routine are the only basis for the
claims made here.

## Results

| Outcome | nets_only | larvicide | difference | raw p | adjusted p | decision |
|---|---|---|---|---|---|---|
| adults per trap night | 15.28 | 7.94 | 7.34 | 7.6e-06 | 2.3e-05 | difference |
| habitats positive (%) | 43.4 | 16.8 | 26.6 | 8.1e-11 | 4.1e-10 | difference |
| bites per person-night | 6.42 | 4.80 | 1.62 | 0.00559 | 0.01114 | difference |
| fever cases per 1000 | 61.7 | 47.4 | 14.3 | 0.01350 | 0.01350 | difference |
| cost per capita (USD) | 2.27 | 3.26 | -0.98 | 1.6e-07 | 6.2e-07 | difference |

All five outcomes survive the correction. The two entomological outcomes move the most:
adult catches roughly halve and the share of water bodies positive for larvae falls from
about 43 percent to about 17 percent. Reported biting and fever cases move less, and the
fever result is the weakest of the five, adjusted p = 0.0135. It is still inside the
family-wide 5 percent level, but it is the one claim that would fall first if the data
were noisier.

## Advice to the district

The larvicide regime costs about one dollar more per resident, 3.26 against 2.27, which
is roughly 43 percent more programme spend. Against that it is associated with about 14
fewer fever cases per 1000 residents. Taking those two group means together, the extra
spend works out near 70 US dollars per averted fever case, which is cheap by the standards
of most vector control budgets.

Our recommendation is to move the district to the larvicide regime where the budget can
absorb the extra dollar per head, and to keep net distribution running alongside it rather
than in place of it, since nets protect people during biting hours in a way that larval
source reduction does not. Two cautions. First, villages were not randomised by us; the
regimes were assigned by the programme, so any village-level difference in habitat or
housing that tracks the regime is still a possible explanation. Second, fever cases here
are surveillance counts, not confirmed malaria, so the health benefit is the least solid
number in the table even though it passed the corrected threshold.
