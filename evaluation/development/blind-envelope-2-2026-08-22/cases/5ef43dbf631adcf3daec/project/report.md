# Mycorrhizal inoculation and marketable tomato yield: a greenhouse trial

## Background

Phosphorus is the nutrient a tomato root is least able to chase down. Phosphate ions bind tightly to
substrate particles and diffuse very slowly, so a root strips the phosphorus out of the few
millimetres around itself within days and then sits inside a depletion zone it cannot cross by
growing alone. Arbuscular mycorrhizal fungi solve that geometry problem. The fungus colonises the
root cortex, forms arbuscules that trade nutrients with the plant cell, and pushes extraradical
hyphae out into substrate the root will never reach. Those hyphae are far thinner than root hairs,
so they explore a much larger volume per unit of carbon spent, and they carry phosphate back to the
host in exchange for photosynthate. Colonised plants also tend to take up more zinc and copper, hold
water status better under transient drought, and in several crops shift dry matter toward
reproductive sinks. In tomato, better phosphorus status early in development supports flower
initiation and fruit set, so the expected agronomic outcome is more marketable fruit and a heavier
cumulative harvest per plant. This trial tests that expectation directly, by comparing cumulative
marketable fruit fresh mass between inoculated and uninoculated plants.

## Data description

The analysis uses a single data file, `greenhouse_tomato_yield.csv`. It has one header row and 48
data rows.

**One row is one whole tomato plant.** Each plant grew alone in its own pot, in its own substrate,
watered and fertilised on its own schedule, and was harvested once at the end of the season. Every
plant contributes exactly one row, and every plant appears exactly once. No plant was measured
twice, and no plant shared a pot, tray, or block with another plant.

Inoculation was applied to the individual plant at transplanting, and cumulative yield was measured
on that same individual plant. The plant is therefore both the treated unit and the measured unit.
The number of rows, the number of measurements, and the number of experimental units are all the
same number: 48.

### Columns

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `plant_id` | text | none | Unique label for the plant, `P01` through `P48`. Each label appears exactly once. |
| `treatment` | text | none | Inoculation group, either `inoculated` or `control`. |
| `bench_position` | text | none | Final position of the pot, written as bench and slot, for example `B3-08`. Benches `B1` to `B4`, slots `01` to `12`, one plant per slot, 48 slots for 48 plants. |
| `height_cm_at_first_flower` | number | centimetres | Height of the plant, measured once on the day its first flower opened. |
| `marketable_fruit_count` | whole number | fruits | Number of marketable fruits that plant produced over the whole harvest period. |
| `marketable_yield_g` | whole number | grams | The outcome. Cumulative fresh mass of marketable fruit from that plant, summed over the whole harvest period and recorded at the end of the season, rounded to the nearest gram. |

### Design and groups

Plants were assigned to a group at random at transplanting: 24 inoculated and 24 uninoculated
controls. Pot positions on the benches were randomised at the start and re-randomised weekly, and
`bench_position` records the final slot each pot occupied. All 48 slots are distinct.

The values in the file are simulated rather than measured, generated once with a fixed random seed
so the file is reproducible.

## Statistical approach

Because each plant was randomised on its own and yields exactly one number, the 48 yield values are
48 independent observations. The comparison is an independent two-sample t-test on
`marketable_yield_g` between the two levels of `treatment`, one value per plant. Welch's form is
reported as the primary test, since it does not assume the two groups share a variance. No averaging
within groups of plants and no random effect for a shared container are needed, because nothing sits
below the plant to average over and nothing above the plant is shared between plants.

The analysis script `analysis.py` includes an explicit check that every `plant_id` appears exactly
once. That check passed: 48 rows, 48 distinct identifiers, no identifier repeated. This confirms
that a row and an experimental unit are the same thing in this file, which is the condition an
independent two-sample test requires.

## Results

Sample size, counted as plants:

| Group | Plants |
| --- | --- |
| Control | 24 |
| Inoculated | 24 |
| Total | 48 |

Cumulative marketable fruit fresh mass per plant:

| Group | n (plants) | Mean (g) | SD (g) | Range (g) |
| --- | --- | --- | --- | --- |
| Control | 24 | 1783.7 | 419.2 | 993 to 2520 |
| Inoculated | 24 | 2146.6 | 380.8 | 1036 to 2767 |

Difference in means, inoculated minus control: **362.9 g per plant**, which is 20.3 percent above
the control mean.

Independent two-sample t-test (Welch): t = 3.139, df = 45.58, **p = 0.0030**. The 95 percent
confidence interval for the difference in means runs from 130.2 g to 595.7 g per plant. The
pooled-variance (Student) form of the same test gives t = 3.139 on 46 degrees of freedom and
p = 0.0030, so the conclusion does not depend on which variance assumption is used.

Two supporting measurements move in the same direction. Inoculated plants averaged 18.1 marketable
fruits per plant against 14.8 for controls, and were 66.4 cm tall at first flower against 60.8 cm
for controls. These were not the trial's primary endpoint and were not formally tested here, but
they are consistent with the yield result rather than pulling against it.

## Interpretation

Inoculating seedlings with the arbuscular mycorrhizal fungus raised cumulative marketable yield by
about 363 g per plant, a gain of roughly one fifth over uninoculated controls, and the difference is
unlikely to be sampling noise (p = 0.0030). The size of the response is agronomically meaningful. At
a typical protected-culture density of about 2.5 plants per square metre, a gain of 363 g per plant
scales to roughly 0.9 kg per square metre over the season, which is the kind of margin that can
carry the cost of an inoculum treatment applied once at transplanting.

The fruit count and height data suggest where the extra mass came from. Inoculated plants set and
carried more marketable fruits rather than simply producing larger ones, and they were already
taller at first flower, which points to an early vigour effect established before the harvest period
began. That pattern fits what improved phosphorus capture during establishment would predict: better
early phosphorus status supports flower initiation and fruit set, and the yield advantage then
accumulates across the harvest.

The confidence interval is wide, running from 130 g to 596 g per plant. With 24 plants per group and
a within-group standard deviation near 400 g, the trial establishes that the effect is positive and
non-trivial but does not pin down its size closely. Anyone budgeting on the low end of that interval
should treat roughly 130 g per plant as the conservative planning figure.

### Caveats

- **One cultivar.** All plants were the same cultivar. Mycorrhizal responsiveness varies a great
  deal between tomato genotypes, and a cultivar with a more efficient native root system may show a
  smaller gain or none at all.
- **Greenhouse conditions.** Pots, a controlled substrate, and an individual fertigation schedule
  are not field soil. Substrate phosphorus availability in particular sets how much room a
  mycorrhizal partner has to help. Under high phosphorus fertilisation the response commonly shrinks
  or disappears, and it can turn negative when the carbon cost to the host exceeds the nutritional
  return.
- **One growing season.** A single season at one site cannot separate the treatment effect from
  season-specific light, temperature, and pest pressure. Repeating the trial across seasons, and
  across substrate phosphorus levels, would be needed before recommending inoculation as routine
  practice.
- **No colonisation assay.** Root colonisation was not quantified, so the trial shows that the
  inoculation treatment raised yield without confirming the degree of colonisation actually
  achieved, and without ruling out non-mycorrhizal components of the inoculum as a contributing
  cause.
- **Simulated data.** The values analysed here were generated, not harvested. The numbers illustrate
  the analysis and its reporting; they are not evidence about any real tomato crop.

## Reproducing the analysis

Run `python3 analysis.py` from the project root. The script reads `greenhouse_tomato_yield.csv`,
runs the one-row-per-plant check, and prints the group sizes, means, standard deviations, difference
in means, and p-value reported above.
