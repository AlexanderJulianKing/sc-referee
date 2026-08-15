# Midday stomatal conductance under deficit irrigation in potted olive saplings

## Data

Source: data/input.csv, 64 midday gas-exchange sessions recorded in
long format. The 16 potted olive saplings were each measured on 4 dates: two sessions
on the deficit schedule and two on the full schedule, in a counterbalanced crossover
order.

## Analysis

Sessions repeated on the same sapling are not independent observations, so the 4
sessions belonging to a sapling were first collapsed into one deficit mean and one
full mean for that sapling. The reported comparison is a two-sided paired t-test on
the 16 sapling-level regime means, giving exactly one analysed row per sapling.

## Result

- Sapling-level mean conductance, deficit schedule: 195.44 mmol m^-2 s^-1
- Sapling-level mean conductance, full schedule: 219.44 mmol m^-2 s^-1
- Mean within-sapling difference (deficit minus full): -24.00 mmol m^-2 s^-1 (SD 18.36)
- 95% CI for the mean difference: [-33.78, -14.22]
- Paired t-test: t(15) = -5.23, p < 0.001

[selected-result] Midday stomatal conductance was 24.00 mmol m^-2 s^-1 lower on the deficit schedule than on the full schedule (95% CI [-33.78, -14.22]; two-sided paired t-test on 16 sapling-level means, t(15) = -5.23, p < 0.001).
