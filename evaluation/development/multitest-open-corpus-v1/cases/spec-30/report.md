# Fermented versus fresh vegetable snack in adults

Seventy-six healthy adults ate a daily portion of either lacto-fermented vegetables or
the same vegetables fresh for four weeks, 38 per arm. Six gut and inflammatory markers
were measured at the end and compared between arms with Welch two-sample t-tests.

## Multiplicity

All six markers are pre-specified outcomes of the same study and are treated as one
family. The family-wise error rate was held at five percent across all six with the
`multipy` package (version 0.16), using `multipy.fwer.sidak`. That routine tests each
raw p-value against 1 - (1 - 0.05)^(1/6) = 0.0085 and returns the decisions used below.
The adjusted p-values printed beside the raw values are the matching Sidak values,
1 - (1 - p)^6. `multipy` and its version are pinned in `requirements.txt`.

## Results

| Marker | Fresh | Fermented | Raw p | Adjusted p | Decision |
| --- | --- | --- | --- | --- | --- |
| Stool frequency (per week) | 8.21 | 9.64 | 0.011 | 0.063 | not significant |
| Faecal pH | 6.84 | 6.55 | 0.0015 | 0.0090 | significant |
| Interleukin-6 (pg/mL) | 1.55 | 1.28 | 0.070 | 0.35 | not significant |
| C-reactive protein (mg/L) | 1.35 | 1.27 | 0.74 | 1.00 | not significant |
| Faecal lactobacilli (log10 CFU/g) | 6.95 | 7.83 | 2.6e-05 | 0.00015 | significant |
| Bloating score (0-10) | 3.38 | 3.62 | 0.61 | 1.00 | not significant |

## Interpretation

Two markers are findings after correction, and they are the two closest to the food
itself. Faecal lactobacilli were 0.88 log10 CFU/g higher after four weeks of fermented
vegetables, close to an eight-fold increase in counts, and faecal pH was 0.29 units
lower. Those results fit together: more lactobacilli means more lactic acid in the
colon, and more acid means lower pH. Both survive with room to spare, so the fermented
product does reach the gut and does shift the environment there.

Nothing else is established. Stool frequency was 1.4 movements per week higher in the
fermented arm, which would have been called significant on its raw p-value of 0.011, but
it does not clear the family-wise threshold and should not be reported as an effect of
the intervention. The same applies to interleukin-6, lower by 0.27 pg/mL with a raw p of
0.070. Both are consistent with the direction people expect from fermented foods, and
neither is supported by this study. C-reactive protein and bloating show essentially no
difference.

The cautious summary is that four weeks of a daily fermented vegetable portion changes
the gut environment in a way that is easy to measure, and that this study does not
demonstrate any change in inflammation or in symptoms. The inflammatory markers were
low and healthy in both arms at the end, which is what you expect in healthy adults and
which leaves little room for an anti-inflammatory effect to show. A trial designed to
test inflammation would need participants with raised baseline markers, a longer
exposure, and a larger sample. Nothing here says the fermented snack is better for
health; it says the snack does what a live-culture food is supposed to do to the colon.
