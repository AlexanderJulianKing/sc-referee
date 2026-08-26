# Supplemental lighting spectra for winter glasshouse sweet peppers

Short trial report for growers. Protected-cropping research station, winter production season.

## The trial

Thirty-six sweet pepper plants were grown in individual pots on a single bench under identical
nutrition, temperature and day length. Eighteen plants grew under a broad white LED module and
eighteen under a red and blue module. Each plant was picked repeatedly through the winter, and its
season totals and season averages were recorded once at the end of the trial. The plant is the unit
of the study, so all comparisons below are two-group comparisons of the 18 plant values per
spectrum.

## Data description

The data file is `pepper_lighting_trial.csv`. It has a header row and 36 data rows.

**One row is one pepper plant**: a single pot on the bench, written down once at the end of the
season. The numbers in a row are that plant's season totals or season averages, not the record of a
single picking day. Every plant has a value in every column, so there are no blanks.

Columns appear in this order: the plant identifier, the lighting treatment, then the seven
protocol outcomes in the order the protocol declared them.

| # | Column | What it holds | Unit |
|---|--------|---------------|------|
| 1 | `plant_id` | Label for the individual plant. `W01`-`W18` are broad white plants, `R01`-`R18` red and blue plants. Each label appears once. | none (text) |
| 2 | `group` | The supplemental lighting spectrum the plant grew under. Exactly two entries occur: `broad_white` and `red_blue`. | none (text) |
| 3 | `yield_kg` | Total marketable fruit yield harvested from the plant across the whole season. | kilograms per plant |
| 4 | `fruit_mass_g` | Mean fresh mass of one marketable fruit from that plant, over all its marketable fruit. | grams |
| 5 | `wall_thickness_mm` | Fruit wall (pericarp) thickness for the plant, averaged over three fruit taken from it. | millimetres |
| 6 | `brix` | Soluble solids content of the plant's fruit. | degrees Brix |
| 7 | `ascorbic_mg_100g` | Ascorbic acid (vitamin C) content of the plant's fruit. | milligrams per 100 grams fresh weight |
| 8 | `leaf_area_m2` | Total leaf area of the plant, measured at the final harvest. | square metres per plant |
| 9 | `days_to_harvest` | Time from transplanting to the plant's first marketable harvest, in whole days. | days |

Two plants in each group (`W04`, `W15`, `R07`, `R12`) established slowly and ran weak all season.
They carry lower yield, smaller leaf area and a later first harvest than their bench mates. They are
ordinary trial plants, not errors, and they are kept in the analysis and recorded the same way as
every other plant.

## How the outcomes were compared

Each declared outcome was compared between the two spectra with Welch's two-sample t-test on the
plant values, 18 plants per spectrum.

**Yield and mean fruit mass were the two outcomes designated primary in the protocol.** These are
the commercial numbers the station will act on, so their two p-values were put through a Holm
multiple-comparison adjustment together, and their verdicts use those adjusted p-values at the
conventional five percent threshold.

The five remaining declared outcomes were given plain unadjusted verdicts: the raw p-value compared
with the same five percent threshold.

## Results

Outcomes in the order the protocol declared them. Means are per-plant means for each spectrum.

| # | Outcome (unit) | Broad white | Red and blue | p-value used | Basis | Verdict at 5% |
|---|----------------|-------------|--------------|--------------|-------|---------------|
| 1 | **Total marketable yield (kg/plant)** - PRIMARY | 3.03 | 3.29 | 0.083 | Holm-adjusted (raw 0.083) | No difference detected |
| 2 | **Mean fruit mass (g)** - PRIMARY | 165.3 | 180.5 | 0.042 | Holm-adjusted (raw 0.021) | Differs |
| 3 | Fruit wall thickness (mm) | 6.28 | 7.05 | 0.009 | Unadjusted | Differs |
| 4 | Soluble solids (degrees Brix) | 6.64 | 7.40 | <0.001 | Unadjusted | Differs |
| 5 | Ascorbic acid (mg/100 g FW) | 124.2 | 135.9 | 0.027 | Unadjusted | Differs |
| 6 | Total leaf area (m2/plant) | 0.739 | 0.666 | 0.095 | Unadjusted | No difference detected |
| 7 | Days to first marketable harvest (days) | 75.3 | 72.7 | 0.097 | Unadjusted | No difference detected |

Outcome by outcome:

1. **Total marketable yield (primary).** Red and blue plants averaged 3.29 kg per plant against
   3.03 kg under broad white, a gain of 0.27 kg per plant, about 9 percent. After the Holm
   adjustment across the two primary outcomes the p-value is 0.083, so at the five percent
   threshold this trial does not establish a yield difference between the two spectra. The
   direction favours red and blue, but the plant-to-plant spread is wide enough that 18 plants per
   spectrum cannot separate the two on yield.

2. **Mean fruit mass (primary).** Fruit averaged 180.5 g under red and blue against 165.3 g under
   broad white, a gain of about 15 g per fruit, roughly 9 percent. The raw p-value is 0.021 and the
   Holm-adjusted p-value is 0.042, so mean fruit mass differs between the two spectra. This is the
   one primary commercial outcome that the trial resolves.

3. **Fruit wall thickness.** 7.05 mm under red and blue against 6.28 mm under broad white, a gain
   of 0.77 mm (p = 0.009). Thicker walls under red and blue.

4. **Soluble solids.** 7.40 degrees Brix under red and blue against 6.64 under broad white, a gain
   of 0.76 (p < 0.001). This is the clearest separation in the trial.

5. **Ascorbic acid.** 135.9 mg/100 g under red and blue against 124.2 mg/100 g under broad white, a
   gain of about 12 mg/100 g (p = 0.027). Higher vitamin C under red and blue.

6. **Total leaf area.** 0.666 m2 per plant under red and blue against 0.739 m2 under broad white
   (p = 0.095). No difference established. The direction is towards less leaf under red and blue,
   which would fit fruit rather than canopy taking the assimilate, but this trial does not
   demonstrate it.

7. **Days to first marketable harvest.** 72.7 days under red and blue against 75.3 days under broad
   white, about 2.7 days earlier (p = 0.097). No difference established at the five percent
   threshold.

## Conclusion

On the evidence of this trial, the station should recommend the **red and blue module** for winter
sweet pepper production.

The case rests on fruit quality and fruit size rather than on tonnage. Of the two primary commercial
outcomes, mean fruit mass is higher under red and blue (180.5 g against 165.3 g, adjusted
p = 0.042), while total yield per plant is not separated by this trial (3.29 kg against 3.03 kg,
adjusted p = 0.083). Bigger fruit at similar yield means fewer, larger fruit, which grades into
better-paying size classes in most winter pepper markets.

The quality outcomes point the same way: fruit under red and blue had thicker walls, higher soluble
solids and more ascorbic acid. Nothing measured favoured broad white. Leaf area and earliness were
not separated.

Two cautions for growers reading this. First, the quality and growth verdicts here are unadjusted
single-outcome comparisons, so they carry the usual risk that comes with reading five tests at once,
and they are supporting evidence rather than the trial's designated commercial endpoints. Second,
the yield question is open, not settled in favour of broad white: this trial is sized for 18 plants
per spectrum and a 9 percent yield gain of the size seen here would need a larger trial to confirm.
A grower deciding on tonnage alone should treat yield as untested. A grower selling on fruit size
and eating quality has a clear result to act on.
