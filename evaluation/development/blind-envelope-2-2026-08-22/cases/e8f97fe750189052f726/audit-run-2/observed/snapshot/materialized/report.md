# A high-sugar larval diet reduces adult wing size in *Drosophila melanogaster*

## Background and question

Adult body size in *Drosophila melanogaster* is set almost entirely during the larval feeding
period. Once a larva reaches critical weight and pupariates, no further growth occurs, so whatever
nutrients the animal accumulated as a larva fix the size of every adult structure. Wing size is the
standard readout of that process: the wing blade is a flat, two-dimensional epithelial sheet whose
final area reflects both cell number and cell size, it can be mounted and imaged without distortion,
and centroid size summarises it in a single repeatable millimetre value.

Diet composition, and not only diet quantity, feeds into this system. A larval medium enriched with
sucrose delivers abundant calories but shifts the carbohydrate-to-protein balance away from the
protein that drives growth signalling through the insulin and TOR pathways. High-sugar rearing is
also known to push larvae toward a hyperglycaemic, insulin-resistant physiology. Both effects
predict smaller, not larger, adults, despite the extra energy on offer.

We asked a direct version of that question: does rearing larvae on standard cornmeal-molasses medium
supplemented with sucrose change the wing centroid size of the adult females that emerge?

## Methods

Sixteen rearing vials were prepared, each with a fresh batch of medium and the same number of seeded
eggs. Eight vials received the standard cornmeal-molasses medium and eight received the same medium
with added sucrose. Vials were distributed across incubator shelves in alternating order. After
eclosion, 12 adult females were sampled from each vial, one wing per fly was mounted, and wing
centroid size was measured in millimetres. Measurements were taken three to five days after
eclosion. This yielded 192 measured flies.

### Data description

The project holds a single comma-separated data file, `wing_size.csv`, with a header row and 192
data rows. **One row is one measured adult female fly:** a single mounted wing from a single fly,
recorded together with the vial that fly developed in, the diet that vial received, and the day the
wing was measured.

| Column | Type | Values | Meaning |
|---|---|---|---|
| `vial_id` | text | `V01`–`V16` | The rearing vial the fly developed in. |
| `diet` | text | `standard` or `high_sugar` | The larval diet, standard cornmeal-molasses medium or the same medium with added sucrose. |
| `fly_id` | text | `F01`–`F12` | The fly's identifier within its own vial. `vial_id` together with `fly_id` names a fly uniquely. |
| `wing_centroid_size_mm` | number | 2.081–2.623 | Wing centroid size in millimetres for the one wing mounted from that fly, rounded to three decimal places. This is the outcome. |
| `day_after_eclosion` | integer | 3, 4, or 5 | How many days after emergence from the pupal case the wing was measured. |

### Statistical analysis

Wing centroid size was compared between the two diets with a single independent two-sample
*t*-test, using the Welch formulation so that the two groups are not required to share a variance.
Each measured fly contributes one observation to the comparison. The sample size is therefore 96
measured flies on the standard diet and 96 measured flies on the high-sugar diet, 192 measured flies
in total. The analysis is implemented in `analysis.py`, which reads the CSV, prints the group sizes,
means and standard deviations, the difference in means, and the *p*-value. It was run with Python 3
using pandas and SciPy.

## Results

| Diet | Measured flies | Mean wing centroid size (mm) | SD (mm) |
|---|---|---|---|
| standard | 96 | 2.422 | 0.078 |
| high_sugar | 96 | 2.305 | 0.080 |

Flies reared on the high-sugar medium had smaller wings than flies reared on the standard medium.
The difference in means was -0.118 mm (high-sugar minus standard), a reduction of 4.9 per cent
relative to the standard-diet mean. The independent two-sample *t*-test gave *t* = -10.31 with 189.8
degrees of freedom and *p* = 4.6 x 10^-20 (n = 96 measured flies per group, 192 in total). Observed
wing centroid sizes across the whole experiment ranged from 2.081 to 2.623 mm, and the two groups
had closely matched standard deviations.

## Interpretation

Adding sucrose to an otherwise standard larval medium produced adults with measurably smaller wings.
The direction of the effect is the informative part. The high-sugar medium is the more calorie-dense
of the two, so a simple energy-limitation account of growth would predict larger adults; we observed
the opposite. This fits the view that larval growth tracks the balance of nutrients rather than
their caloric total, and that a carbohydrate-heavy, protein-diluted medium restrains growth
signalling even when energy is plentiful. It is also consistent with the reduced insulin sensitivity
reported in high-sugar-reared larvae, which would blunt the same signalling axis that sets final
size.

The magnitude is biologically meaningful without being extreme. A 4.9 per cent reduction in centroid
size is comfortably within the range over which *Drosophila* wing size responds to nutritional
manipulation, and it is large enough to be visible against normal culture-to-culture variation. A
change of this size is the kind that carries downstream consequences for flight mechanics and for
fecundity, both of which scale with body size, and it is worth following up in those terms.

Several practical caveats deserve stating, as they would in any diet study of this design.

- **Females only.** We sampled and measured adult females. *Drosophila* wing size is sexually
  dimorphic and the sexes are known to differ in their nutritional responses, so these estimates
  should not be read as applying to males without direct measurement.
- **One wing per fly.** A single wing was mounted from each fly. Left and right wings differ
  slightly through fluctuating asymmetry, so the per-fly value carries a small amount of
  side-specific variation that a two-wing average would remove. It also means this experiment says
  nothing about whether the high-sugar diet affects asymmetry itself.
- **A single sucrose concentration.** Only one supplemented formulation was tested against one
  standard medium. The result establishes the direction of the effect at that concentration and does
  not describe the shape of the dose-response curve.
- **Centroid size as the only morphometric readout.** Centroid size collapses the wing into one
  number and does not distinguish a reduction in cell number from a reduction in cell size, nor does
  it capture changes in wing shape. Cell counts and landmark-based shape analysis would separate
  those.
- **Measurement window.** Wings were scored three to five days after eclosion. Cuticle is fully
  expanded and sclerotised well before day three, so the outcome is stable across that window, but
  the timing is recorded in `day_after_eclosion` for anyone wishing to check it.
- **One genetic background, one temperature.** All vials came from the same stock and the same
  incubator regime. Nutritional effects on size interact with genotype and with rearing temperature,
  so generalising beyond these conditions requires further work.

## Conclusion

Larvae reared on cornmeal-molasses medium supplemented with sucrose emerged as adult females with
wing centroid sizes 0.118 mm smaller on average than those reared on the standard medium, 2.305 mm
against 2.422 mm (*p* = 4.6 x 10^-20). Extra dietary sugar reduces adult wing size in this system.

## Files

- `wing_size.csv` — the measured-fly data, one row per fly.
- `analysis.py` — the analysis script; run `python3 analysis.py` from the project root.
- `report.md` — this report.
