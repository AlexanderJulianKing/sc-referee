# Hand-hygiene prompts and nurses' skin condition

## What we did

Automated hand-hygiene prompts (motion-triggered units at bay entrances and at each
gel dispenser) were installed on half the wards of the hospital for eight weeks. The
remaining wards carried on with the existing signage. At the end of the eight weeks an
infection-control nurse assessed 80 nurses, 40 on prompt wards and 40 on unchanged
wards, for hygiene behaviour and skin condition. Each nurse contributes one row to
`data.csv`. Every outcome was compared between ward types with Welch's two-sample
t-test at the conventional five-percent level (`SIGNIFICANCE_LEVEL = 0.05` in
`analysis.py`, applied unchanged to all five outcomes).

## Results

| Outcome | Control | Prompt | p | Verdict |
| --- | --- | --- | --- | --- |
| Hand-hygiene events per hour | 4.38 | 6.65 | 2.5e-08 | significant |
| Clinician dryness score (0-12) | 3.44 | 4.69 | 0.0081 | significant |
| Transepidermal water loss (g/m2/h) | 12.07 | 14.91 | 0.0008 | significant |
| Moisturiser applications per day | 1.80 | 2.77 | 6.8e-05 | significant |
| Glove hours per shift | 4.23 | 4.06 | 0.60 | not significant |

The prompts did what they were installed to do: hygiene events rose by about 2.3 per
hour, a little over half again the control rate. The skin cost is visible in the same
data. Dryness scores were 1.25 points higher on prompt wards, water loss was 2.8
g/m2/h higher, and nurses on those wards were applying moisturiser about one extra
time per day, which is consistent with them noticing the dryness themselves. Glove
hours were essentially the same on both ward types (4.23 vs 4.06 hours), so the skin
differences are unlikely to be a glove-occlusion effect.

## Should the prompts be rolled out hospital-wide?

The behavioural gain is large and the skin effects, while real, are modest in absolute
terms: a dryness score still under 5 on a 0-12 scale, and a water-loss figure within
the range normally seen in ward nurses in winter. Our reading is that a hospital-wide
rollout is justified, but it should go out together with a skin-care package, at
minimum dispenser-side emollient on every bay and a low threshold for occupational
health review of nurses reporting cracking or dermatitis. Two practical caveats. All
five outcomes were assessed at a single time point at the end of the eight weeks, so
we cannot say whether the dryness plateaus, worsens, or settles once the novelty of
the prompts wears off. And wards, not nurses, were assigned to the prompt condition,
so nurses on the same ward share whatever else is true of that ward; a repeat with
more wards would let us separate the prompt effect from the ward effect properly.
