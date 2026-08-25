# In-vessel composting versus static aerated pile

## Setting

The authority ran an in-vessel composting system and a static aerated pile side by side
on the same feedstock stream for one year, sampling 30 batches from each system. The
evaluation protocol (MWA-COMPOST-2024-03) was registered before sampling began.

## The registered decision rule

The protocol states: *"The outcome family consists of five outcomes: days to maturity,
final carbon to nitrogen ratio, germination index, E. coli count, and ammonia emission.
The family-wide significance level is five percent, shared equally across the five
outcomes. Each outcome is judged significant when its p-value falls below 0.010."*

The threshold is that five percent divided equally among the five outcomes in the family:

    0.05 / 5 = 0.010

The family and the threshold were both fixed before the first batch was sampled, so the
analysis script carries only the number 0.010 and does no correction arithmetic of its
own. If the family had been a different size the registered threshold would have been a
different number, and re-deriving it after the fact is exactly what registration is meant
to prevent.

## Results

Each outcome was compared between systems with a two-sample t-test for a difference in
means, and each p-value was read against 0.010.

| Outcome | Static pile | In-vessel | p | Decision |
|---|---|---|---|---|
| Days to maturity | 93.90 | 62.70 | <0.0001 | difference |
| Final C:N ratio | 17.16 | 15.24 | 0.0015 | difference |
| Germination index (%) | 82.83 | 89.63 | 0.0099 | difference |
| E. coli (log10 CFU/g) | 2.50 | 1.57 | <0.0001 | difference |
| Ammonia (g/tonne feedstock) | 387.50 | 236.17 | <0.0001 | difference |

All five outcomes clear the registered threshold. The germination index is the marginal
one at p = 0.0099, which sits just inside 0.010; it would have been called a difference at
an unadjusted five percent level with room to spare, so it is worth flagging as the result
most sensitive to the pre-registered rule.

## Conclusion

The in-vessel system reaches maturity about 31 days sooner, produces compost with a lower
C:N ratio and a higher germination index, achieves close to one log more E. coli
reduction, and emits about 150 g less ammonia per tonne of feedstock. Every one of the
five registered outcomes favours in-vessel composting at the protocol's 0.010 threshold.
