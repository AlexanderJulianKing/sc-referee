# Neonicotinoid microdosing and gyne production in caged bumblebee colonies

## Design

Twenty-eight queenright Bombus terrestris colonies were reared, each in its own sealed
flight arena, and each colony was held on a single diet for the whole colony cycle:
14 colonies received untreated sugar syrup (control) and 14 received syrup dosed at
2 ppb thiamethoxam (exposed). The response is the lifetime gyne count, a single
whole-colony census taken at nest teardown. Each colony is censused once and appears
once, so every analysed row is one independent unit.

Independence check: 28 data rows, 28 distinct colony identifiers, 28 distinct arena
identifiers, at most 1 row per colony.

## Baseline balance

| treatment | colonies | mean founding workers |
| --- | --- | --- |
| control | 14 | 41.43 |
| exposed | 14 | 40.57 |

## Gyne production

| treatment | colonies | mean gynes | SD |
| --- | --- | --- | --- |
| control | 14 | 13.86 | 4.99 |
| exposed | 14 | 6.00 | 3.88 |

Welch's two-sample t-test (two-sided) on lifetime gyne count: t = 4.65, df = 24.5,
p < 0.001. The control minus exposed difference in means is 7.86 gynes.

Mann-Whitney U test (two-sided, normal approximation) as a distribution-free check:
U = 176.0, p < 0.001.

[selected-result] Welch's two-sided two-sample t-test on lifetime gyne count with one colony per row: control colonies produced 13.86 gynes on average against 6.00 for thiamethoxam-exposed colonies, a difference of 7.86 gynes (t = 4.65, df = 24.5, p < 0.001), so 2 ppb dietary thiamethoxam is associated with markedly reduced gyne output.

## Notes

The gyne count is a whole-colony lifetime total, so there are no repeated measures to
pool and no within-colony correlation for the test to absorb. The degrees of freedom
in the Welch approximation count colonies, not observations. The two arms are close on
founding worker number (41.43 against 40.57), so the contrast is not driven by
an obvious size imbalance.
