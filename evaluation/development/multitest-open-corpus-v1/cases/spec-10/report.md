# Neonicotinoid seed treatment and bumblebee colony performance

Forty-four commercial bumblebee colonies were placed beside oilseed rape plots grown from
either neonicotinoid-treated or untreated seed, 22 colonies per treatment, and assessed at
the end of the flowering period. Five colony outcomes make up the family: final colony
mass, new queens produced, worker count, foraging trips per hour, and mean pollen load per
returning forager.

The primary analysis compared treatments with Welch two-sample t-tests and corrected all
five p-values together using Holm's step-down procedure from statsmodels, holding the
family-wide error rate at 5%.

| Outcome | Untreated | Treated | Raw p | Holm p | Decision |
|---|---|---|---|---|---|
| Colony mass (g) | 620.1 | 547.1 | 0.0570 | 0.1812 | not significant |
| New queens | 7.64 | 5.64 | 0.0908 | 0.1816 | not significant |
| Workers | 173.4 | 145.5 | 0.0261 | 0.1304 | not significant |
| Foraging trips per hour | 11.15 | 9.70 | 0.1226 | 0.1816 | not significant |
| Pollen load (mg) | 18.74 | 16.07 | 0.0453 | 0.1812 | not significant |

No outcome survives the correction. Every point estimate runs in the same direction,
colonies beside treated plots being smaller, less productive and slower to forage, and
worker count and pollen load would have been called significant if each outcome had been
judged on its own at 5%. With five outcomes tested together and 22 colonies per arm, the
study does not have the resolution to separate that consistent pattern from ordinary
between-colony variation, so it demonstrates no effect on any single outcome.

## Sensitivity analysis

The same five comparisons were repeated with the Mann-Whitney U test, a rank-based
alternative that does not lean on the mean or on approximate normality, and that second
set of five p-values was corrected with the same Holm procedure at the same 5% level. Raw
values were 0.0979 for colony mass, 0.1116 for new queens, 0.0326 for workers, 0.1270 for
foraging trips and 0.0366 for pollen load; after Holm the smallest was 0.1631, and again
nothing is significant. The rank-based re-run therefore agrees with the primary analysis on
all five outcomes.

Both passes corrected the same family of five outcomes, and the conclusions above come
from the corrected primary t-test results; the rank-based pass is reported only as a check
that the picture holds.
