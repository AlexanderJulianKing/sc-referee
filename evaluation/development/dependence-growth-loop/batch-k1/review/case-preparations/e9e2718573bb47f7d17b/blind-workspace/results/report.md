# Endosymbiont density in lagoon and forereef colonies of Porites lobata

## Analysis

Endosymbiont density (millions of cells per cm^2) was compared between the two
reef zones with Welch's two-sample t-test (scipy.stats.ttest_ind with
equal_var=False). Every nubbin record in data/input.csv contributed one
observation to the test.

## Result

| zone | n | mean | sd |
| --- | --- | --- | --- |
| lagoon | 24 | 1.833 | 0.382 |
| forereef | 24 | 1.528 | 0.353 |

Mean difference (lagoon minus forereef): 0.305 million cells per cm^2.
Welch t = 2.874, df = 45.7, p < 0.01 (two-sided, alpha = 0.05).

[selected-result] Lagoon nubbins carry a higher endosymbiont density than forereef nubbins: mean difference 0.305 million cells per cm^2 (1.833 vs 1.528), Welch t = 2.874, df = 45.7, p < 0.01, so the zone difference is significant at alpha = 0.05.
