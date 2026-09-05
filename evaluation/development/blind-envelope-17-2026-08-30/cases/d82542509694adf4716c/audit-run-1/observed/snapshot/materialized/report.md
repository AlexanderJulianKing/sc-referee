# Pelleted versus seed-based maintenance diet in adult African grey parrots

## The question

Forty-eight adult African grey parrots at the rescue and rehoming centre, all individually
housed in identical aviaries and all previously maintained on a seed-based diet, were put on
one of two maintenance diets for twelve weeks: a complete extruded pelleted diet (24 birds)
or a continued seed-based diet with fresh produce (24 birds). The two diets are the only
comparison here. At the end of the twelve weeks each bird was sampled and scored by the
attending veterinarian. The question for each declared outcome is simply whether the diet
changed it: vitamin A status, body mass, calcium, plumage.

## The data

File: `parrot_diet_data.csv`. One row is one bird, sampled and scored once at week twelve.
There are 48 rows, 24 birds on each diet, and every bird has a value in every column.

| Column | Description |
| --- | --- |
| `bird_id` | Bird identifier, `AGP01` through `AGP48`. |
| `diet` | Group column, either `pellet` or `seed`. |
| `plasma_retinol_ug_dl` | Plasma retinol (vitamin A) at week twelve, micrograms per decilitre. |
| `body_mass_g` | Body mass at week twelve, grams. |
| `plasma_calcium_mmol_l` | Plasma total calcium at week twelve, millimoles per litre. |
| `feather_condition_score` | Feather condition score at week twelve, 0 to 20, higher is better. |

The four outcome columns appear in the declared order fixed in the study protocol before the
diets began: retinol, body mass, calcium, feather condition score.

## How the comparison was done

Each declared outcome was compared between the two diet groups with an independent-samples
t-test, the standard two-group comparison for continuous data, run on the 24 pellet-fed and
24 seed-fed birds. Each outcome was judged on its own against the conventional 0.05
significance threshold.

## Results

**Plasma retinol (vitamin A).** Pellet-fed mean 38.72 ug/dl, seed-fed mean 25.31 ug/dl;
t = 4.600, p = 0.00003. Significant at the 0.05 threshold.

**Body mass.** Pellet-fed mean 452.5 g, seed-fed mean 459.1 g; t = -0.764, p = 0.449. Not
significant at the 0.05 threshold.

**Plasma total calcium.** Pellet-fed mean 2.245 mmol/l, seed-fed mean 2.037 mmol/l;
t = 3.361, p = 0.0016. Significant at the 0.05 threshold.

**Feather condition score.** Pellet-fed mean 15.71, seed-fed mean 14.04; t = 2.357,
p = 0.023. Significant at the 0.05 threshold.

## Conclusion

Over twelve weeks the pelleted diet affected three of the four declared aspects of health.
Vitamin A status was the largest change: retinol was about 13 ug/dl higher in the pellet-fed
birds. Plasma calcium was higher on pellets by about 0.21 mmol/l, and feather condition
scored about 1.7 points better on the 0 to 20 scale. Body mass did not differ; the birds on
pellets weighed about 7 g less on average, well within the scatter seen in both groups. In
short, the pelleted diet improved vitamin A status, calcium and plumage in these birds
without moving body mass in either direction.
