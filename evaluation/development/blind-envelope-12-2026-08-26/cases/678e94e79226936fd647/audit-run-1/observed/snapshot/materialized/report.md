# Manufactured pellet versus fresh macroalgae as a finishing feed for purple sea urchins

Ten-week finishing trial, 36 adult urchins, single raceway.

## Study

Thirty-six adult purple sea urchins were held individually, one animal per
flow-through basket, in a single raceway for ten weeks. Eighteen animals
received chopped fresh macroalgae and eighteen received the manufactured
pellet. Water temperature and flow were identical for all baskets. At the end
of the ten weeks each urchin was measured and dissected once. The urchin is the
unit of the study, so each animal contributes one independent set of
end-of-trial values.

The trial declared five outcomes in advance, in this fixed order: gonad index,
gonad colour, test diameter, whole body wet mass, gonad firmness.

## Data description

The data file is `urchin_feeding_trial.csv`. It holds one header row and 36
data rows.

**One row represents one adult purple sea urchin**, held in its own basket for
the ten weeks and measured and dissected once at the end of the trial. The
values in a row are that single animal's end-of-trial measurements. Eighteen
rows are macroalgae-fed animals and eighteen are pellet-fed animals. Every
urchin has a value in every column; there are no blanks.

| Column | What it holds | Unit |
| --- | --- | --- |
| `urchin_id` | Identifier of the individual urchin, `U01` through `U36`, one per basket and unique in the file. | none, text label |
| `group` | The finishing feed the urchin received. Exactly two entries occur: `macroalgae` for the chopped fresh macroalgal feed and `pellet` for the manufactured pellet. | none, text label |
| `gonad_index_pct` | Gonad index: gonad wet mass as a percentage of whole body wet mass. | percent |
| `gonad_colour_b` | Gonad colour, the b\* yellowness coordinate from a handheld colorimeter. Higher is more yellow. | unitless |
| `test_diameter_mm` | Test diameter, the widest across-the-shell measurement. | millimetres |
| `body_mass_g` | Whole body wet mass of the urchin. | grams |
| `gonad_firmness_n` | Gonad firmness, the peak force in a small probe compression test on the gonad. | newtons |

The five measurement columns appear in the order in which the trial declared
its outcomes. Values are stored as recorded: gonad index and firmness to two
decimal places, colour, diameter and mass to one decimal place.

## Statistical method

Each declared outcome was compared between the two feeds with a Welch
two-sample t-test on the individual urchin values, giving one raw p-value per
outcome.

All five declared outcomes were declared together as one family, so all five
raw p-values were adjusted together as one family rather than judged
separately. The adjustment is the Holm step-down procedure, which controls the
family-wise error rate, and it was carried out by the `multicomp` function of
the third-party statistics package **pingouin** (version 0.6.1), declared as a
project dependency. Every significance verdict below is read from the adjusted
p-values at a family-wise level of 5 percent. No verdict is taken from a raw
p-value.

## Results

Group means are the means of the 18 urchins in each feed group.

| # | Declared outcome | Macroalgae mean | Pellet mean | Raw p | Adjusted p | Verdict at family-wise 5% |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Gonad index (%) | 11.41 | 10.30 | 0.242 | 0.727 | Not significant |
| 2 | Gonad colour b\* (unitless) | 38.35 | 32.52 | 0.0000090 | 0.000045 | Significant |
| 3 | Test diameter (mm) | 57.83 | 56.81 | 0.582 | 1.000 | Not significant |
| 4 | Whole body wet mass (g) | 99.04 | 96.61 | 0.661 | 1.000 | Not significant |
| 5 | Gonad firmness (N) | 2.026 | 2.736 | 0.00037 | 0.0015 | Significant |

Taken outcome by outcome, in the declared order:

1. **Gonad index.** Macroalgae-fed animals averaged 11.41 percent and
   pellet-fed animals 10.30 percent, a difference of 1.11 percentage points in
   favour of macroalgae. Raw p = 0.242, adjusted p = 0.727. Not significant.
   The trial does not show a difference in roe yield between the two feeds.
2. **Gonad colour.** Macroalgae-fed animals averaged a b\* of 38.35 against
   32.52 for pellet-fed animals, so pellet roe was 5.83 b\* units less yellow.
   Raw p = 0.0000090, adjusted p = 0.000045. Significant.
3. **Test diameter.** 57.83 mm on macroalgae against 56.81 mm on pellet. Raw
   p = 0.582, adjusted p = 1.000. Not significant.
4. **Whole body wet mass.** 99.04 g on macroalgae against 96.61 g on pellet.
   Raw p = 0.661, adjusted p = 1.000. Not significant.
5. **Gonad firmness.** 2.026 N on macroalgae against 2.736 N on pellet, so
   pellet roe was 0.710 N firmer. Raw p = 0.00037, adjusted p = 0.0015.
   Significant.

Two of the five declared outcomes, gonad colour and gonad firmness, are
significant after the family-wise adjustment. The other three, gonad index,
test diameter and whole body wet mass, are not.

## Conclusion

Over ten weeks the manufactured pellet held its own on the quantity measures.
Roe yield, animal size and animal mass came out statistically indistinguishable
between the two feeds after adjustment, so the pellet did not cost the animals
growth or gonad bulk in this trial.

The two differences that the trial does demonstrate are both about roe quality,
and they point in opposite commercial directions. Pellet-fed roe was
noticeably paler, by about 5.8 b\* units, which matters because buyers pay for
colour. Pellet-fed roe was also firmer, by about 0.71 N, which is usually
welcome for handling and shelf presentation.

Our reading is that the pellet is a promising but not yet finished replacement.
It is viable on yield and on animal condition, and the firmness result is a
point in its favour. The colour shortfall is the blocker, and it is the kind of
shortfall that is usually addressed through the feed's pigment content rather
than through the feeding regime. We would recommend a follow-up trial of a
pigment-supplemented version of the pellet before the hatchery commits to it
for market-grade roe.

Two limits on how far these results should be read. The trial ran once, in one
raceway, on 36 animals, so it speaks to these conditions and this pellet
formulation only. Measurement was taken once per animal at the end of the ten
weeks, so the trial shows where the animals ended up and not how they got
there.
