# Low-dose fluoxetine reduces exploratory swimming in adult zebrafish

## Data description

All results below come from a single file, `zebrafish_activity.csv`. The file has a
header line and 96 data rows. **One row is one fish**: it records that fish's identity,
the tank it was housed in, the water condition that tank received, its body size, and the
total distance it swam during its own 6-minute novel-tank trial. Each fish was filmed
individually and appears exactly once in the file. Rows are stored in collection order,
tank by tank, beginning with `TNK-01`. No values are missing.

The file has five columns:

- `aquarium_ref` (text) - the 3 L tank the fish was housed in, written `TNK-01` through
  `TNK-08`.
- `exposure` (text) - the water condition, either `control` or `fluoxetine`.
- `fish_label` (text) - the individual fish identifier, `F01` through `F12`. Labels repeat
  across tanks, so a fish is picked out by the pair (`aquarium_ref`, `fish_label`).
- `body_length_mm` (number) - standard length in millimetres, measured at the end of the
  exposure period; observed range 31.4 to 39.1 mm.
- `distance_cm` (number) - total distance moved during the 6-minute novel-tank trial, in
  centimetres; observed range 838.7 to 1693.8 cm. This is the outcome analysed here.

## Experiment

Adult zebrafish (*Danio rerio*) were held in eight 3 L tanks, 12 fish per tank. Four tanks
(`TNK-01` to `TNK-04`) were maintained on clean system water and served as controls. The
remaining four tanks (`TNK-05` to `TNK-08`) received waterborne fluoxetine at 5 micrograms
per litre. Dosing was into the tank water and continued for 14 days. At the end of the
exposure period every fish was measured for standard length and then filmed alone for six
minutes in a novel tank, and total distance moved was extracted from the video track. This
produced 96 individual activity records, 48 under each water condition.

## Analysis

The question was whether total distance moved differs between the two water conditions, so
I compared `distance_cm` between control and fluoxetine fish with Student's two-sample
t-test (`scipy.stats.ttest_ind`, equal variances assumed, two-sided).

The measurements entering the test were the individual `distance_cm` values, one per row of
the CSV, with no averaging or other aggregation applied first. Every row whose `exposure`
value was `control` contributed one value to the first sample, and every row whose
`exposure` value was `fluoxetine` contributed one value to the second sample. Each fish was
counted as one replicate, so **the sample sizes I used were N = 48 per group**, 96
measurements in total, giving 94 degrees of freedom.

## Results

Control fish moved 1281.5 cm on average during the six-minute trial (SD 217.4 cm, N = 48).
Fluoxetine-exposed fish moved 1180.6 cm on average (SD 161.2 cm, N = 48). The difference
between the conditions was 100.9 cm, a reduction of about 7.9 percent relative to controls.

The two-sample t-test on these 96 individual measurements gave t(94) = 2.582 with a
two-sided p-value of 0.0114. Distance moved was therefore significantly lower in the
fluoxetine condition than in the control condition at the conventional 5 percent level.

## Conclusion

Fourteen days of waterborne fluoxetine at 5 micrograms per litre lowered exploratory
swimming in the novel-tank test. Exposed fish covered roughly 100 cm less ground over six
minutes than controls, consistent with the sedative-like behavioural profile reported for
low-dose SSRI exposure in small fish.
