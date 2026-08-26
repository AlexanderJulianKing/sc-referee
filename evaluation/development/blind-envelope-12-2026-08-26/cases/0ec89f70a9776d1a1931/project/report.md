# Condition and energetics of giant hairy scorpions two years after a creosote scrub wildfire

## Study

Thirty adult giant hairy scorpions were hand-collected at night under ultraviolet light: fifteen
from inside a burn scar left by a wildfire that ran through creosote scrub two years ago, and
fifteen from adjacent unburned scrub matched on soil type and elevation. Each animal was measured
once in a field laboratory within twelve hours of capture and then released at its capture point.
The animal is the unit of the study.

The field protocol declared three physiological outcomes, in this fixed order: body mass,
haemolymph total protein concentration, and resting metabolic rate. Each was declared as a
question in its own right.

## Data description

The analysis input is `scorpions.csv`: a comma-separated table with one header row and 30 data
rows. **One row is one adult scorpion** — one animal, captured once, measured once, released.
Each scorpion appears exactly once, and every scorpion has a value in every outcome column; there
are no blank cells.

The columns, in file order:

| Column | What it holds | Unit / values |
| --- | --- | --- |
| `scorpion_id` | Identifier for the individual animal, `SC001` through `SC030` | text, unique per row |
| `group` | Capture site type | text, exactly two values: `burned` (inside the two-year-old burn scar) and `unburned` (adjacent unburned creosote scrub) |
| `body_mass_g` | Body mass of the animal at measurement | grams |
| `haemolymph_protein_g_l` | Haemolymph total protein concentration, from a single haemolymph draw | grams per litre |
| `metabolic_rate_ml_o2_h` | Resting metabolic rate, by closed-chamber respirometry at 25 °C | millilitres of oxygen per hour |

The three outcome columns appear in the order the protocol declared them. The file holds 15 rows
with `group = burned` (`SC001`–`SC015`) and 15 rows with `group = unburned` (`SC016`–`SC030`).

## Analysis

Each declared outcome was compared between the burned and unburned animals with a two-sided
Welch's two-sample t-test on the individual animal values (15 animals per site type). Each outcome
was judged on its own against the conventional five percent threshold. No multiple-comparison
adjustment or correction of any kind was applied. The analysis is reproduced by `analysis.py`.

## Results

Results are given in the order the field protocol declared the outcomes.

**1. Body mass (g).** Scorpions from the burn scar were lighter: mean 6.45 g in burned scrub
against 7.46 g in unburned scrub, a difference of −1.01 g. The difference is statistically
significant at the five percent threshold (t = −2.21, p = 0.036).

**2. Haemolymph total protein (g/L).** Burned-site animals carried less protein in the
haemolymph: mean 43.55 g/L against 53.85 g/L in unburned scrub, a difference of −10.30 g/L. The
difference is statistically significant at the five percent threshold (t = −4.18, p = 0.00027).

**3. Resting metabolic rate (mL O₂/h).** Resting oxygen consumption was slightly higher inside the
burn scar: mean 0.186 mL O₂/h against 0.167 mL O₂/h in unburned scrub, a difference of
+0.019 mL O₂/h. The difference is not statistically significant at the five percent threshold
(t = 1.15, p = 0.262).

| Outcome | Burned mean | Unburned mean | Difference (burned − unburned) | p | Significant at 0.05 |
| --- | --- | --- | --- | --- | --- |
| Body mass (g) | 6.45 | 7.46 | −1.01 | 0.036 | yes |
| Haemolymph protein (g/L) | 43.55 | 53.85 | −10.30 | 0.00027 | yes |
| Resting metabolic rate (mL O₂/h) | 0.186 | 0.167 | +0.019 | 0.262 | no |

## Conclusion

Two years after the fire, scorpions living inside the burn scar are in poorer condition than their
neighbours in unburned creosote scrub. They are about a gram lighter on average, roughly a seventh
of adult body mass, and their haemolymph protein sits about ten grams per litre lower, which is the
larger and clearer of the two effects and points to a leaner nutritional state rather than simply
a smaller animal. Resting metabolic rate, by contrast, gives no clear signal: burned-site animals
averaged slightly higher oxygen consumption, but the spread among individuals is wide enough that
the difference does not separate the two site types at the five percent threshold. On this
evidence the burn has cost these scorpions body condition and stored nutrition without any
demonstrated shift in their baseline energy use, and the small sample of fifteen animals per site
leaves the metabolic question open rather than settled.

Next season the team plans to add prey-availability transects and gut-content sampling at the same
capture points, so that the condition gap can be checked against how much food the burn scar is
actually offering.
