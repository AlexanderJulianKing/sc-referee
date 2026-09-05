# Ultraviolet B lamp type in captive bred juvenile bearded dragons

## Design

Forty captive bred juvenile bearded dragons from a single hatch cohort were each
housed alone in a vivarium of identical size, diet and temperature gradient for
twelve weeks. Twenty animals were kept under a compact fluorescent ultraviolet B
lamp (`cfl`) and twenty under a linear T5 high output ultraviolet B lamp
(`t5_ho`). Lamps were mounted at the manufacturer's stated distance and replaced
on schedule. Every animal was measured once, at the end of week twelve.

Five outcomes were declared in the trial protocol, in this fixed order, before
the animals were allocated:

1. Plasma 25-hydroxyvitamin D3 (nmol/L)
2. Plasma ionised calcium (mmol/L)
3. Body mass gain over twelve weeks (g)
4. Snout to vent length gain over twelve weeks (mm)
5. Radiographic humeral cortical thickness ratio (unitless)

## Data

`data.csv` holds one row per animal: 40 rows plus a header. A single row is one
juvenile dragon, with its lamp group and its five end of week twelve outcome
values. There are no repeated rows, no summary rows and no blank cells. Every
animal has a value for every outcome, and the group labels split exactly twenty
and twenty.

| Column | Meaning | Unit |
| --- | --- | --- |
| `dragon_id` | Animal identifier, `bd_01` through `bd_40`, unique per row | none |
| `lamp_type` | Lamp the animal was housed under, `cfl` or `t5_ho` | none |
| `plasma_25ohd3_nmol_l` | Plasma 25-hydroxyvitamin D3 at week twelve | nmol/L |
| `plasma_ionised_calcium_mmol_l` | Plasma ionised calcium at week twelve | mmol/L |
| `body_mass_gain_g` | Body mass gained over the twelve weeks | g |
| `snout_vent_length_gain_mm` | Snout to vent length gained over the twelve weeks | mm |
| `humeral_cortical_thickness_ratio` | Cortical width divided by total humeral bone width | none (ratio) |

## Multiplicity position

Five outcomes were declared as one family, so five tests are run on the same
trial. Holding the family-wise error rate for the whole family at 0.05 with a
Bonferroni correction gives a per-outcome level of 0.05 / 5 = 0.01. The protocol
fixed the per-outcome significance threshold at 0.01 in advance for exactly that
reason. Every verdict in this report is judged against 0.01, and no verdict here
is taken against any other level.

## Results

Each outcome was compared between the two lamp groups with a two sided Welch
two-sample t-test (twenty animals per group throughout).

| Outcome | Mean `t5_ho` | Mean `cfl` | Difference | Welch t | p | Verdict vs 0.01 |
| --- | --- | --- | --- | --- | --- | --- |
| Plasma 25-hydroxyvitamin D3 (nmol/L) | 158.1 | 101.8 | 56.3 | 4.151 | 0.00020 | significant |
| Plasma ionised calcium (mmol/L) | 1.506 | 1.437 | 0.069 | 2.632 | 0.01220 | not significant |
| Body mass gain (g) | 61.9 | 60.9 | 1.1 | 0.244 | 0.80887 | not significant |
| Snout to vent length gain (mm) | 41.4 | 36.6 | 4.8 | 1.958 | 0.05784 | not significant |
| Humeral cortical thickness ratio | 0.355 | 0.290 | 0.065 | 3.922 | 0.00036 | significant |

Differences are the T5 high output mean minus the compact fluorescent mean, so a
positive difference favours the T5 lamp.

Outcome by outcome: plasma 25-hydroxyvitamin D3 is higher under the T5 lamp by
56.3 nmol/L, and at p = 0.00020 that separation clears the 0.01 threshold.
Plasma ionised calcium is higher under the T5 lamp by 0.069 mmol/L, but at
p = 0.01220 it does not clear 0.01, so it is not called significant here. It
would have cleared an uncorrected 0.05, and holding back that call is the point
of fixing the per-outcome level in advance. Body mass gain differs by 1.1 g with
p = 0.80887 and shows no separation. Snout to vent length gain is 4.8 mm greater
under the T5 lamp with p = 0.05784, which does not clear 0.01. The humeral
cortical thickness ratio is 0.065 higher under the T5 lamp, and at p = 0.00036
it clears 0.01.

## What the trial found

Over twelve weeks, juvenile bearded dragons housed under the linear T5 high
output ultraviolet B lamp reached substantially higher plasma 25-hydroxyvitamin
D3 and a thicker humeral cortex than those housed under the compact fluorescent
lamp. Those are the two outcomes that met the pre-declared 0.01 threshold. The
remaining three declared outcomes, ionised calcium, body mass gain and snout to
vent length gain, all pointed in the same direction but did not meet that
threshold in a cohort of this size, and this trial does not establish a
difference in them. The evidence supports the T5 high output lamp over the
compact fluorescent lamp on vitamin D3 status and on bone cortical thickness,
while the growth measures over twelve weeks remain undecided.
