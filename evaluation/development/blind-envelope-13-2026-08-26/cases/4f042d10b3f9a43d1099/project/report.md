# Solar dryer versus open-mat drying of groundnut lots

## Data

The data file is `groundnut_drying_quality.csv`. One row is one groundnut lot, which is a single
farmer delivery of roughly 50 kg of freshly lifted groundnuts brought to the collection centre.
Each lot was dried as a unit by one drying method and then sampled once for laboratory analysis.
There are 40 lots: 20 dried in a simple solar dryer and 20 dried in the traditional way on open
mats. Every lot has a value in every outcome column, so there are no blank cells.

| Column | Meaning | Unit or values |
| --- | --- | --- |
| `lot_id` | Identifier for the farmer delivery, in delivery order down the file | Text, `LOT-001` through `LOT-040` |
| `drying_method` | How the lot was dried | Text, two values: `solar_dryer` and `open_mat` |
| `moisture_content_percent_wb` | Moisture content of the dried kernels, wet basis | Percent, wet basis |
| `aflatoxin_b1_ug_per_kg` | Aflatoxin B1 concentration in the dried kernels | Micrograms per kilogram |
| `free_fatty_acids_percent_oleic` | Free fatty acid content of the extracted oil, as oleic acid | Percent, as oleic acid |

The three outcome columns are in the order the outcomes were declared in the study plan: moisture
content first, aflatoxin B1 second, free fatty acids third.

## Method

`analysis.py` reads the CSV and compares the two drying methods on each declared outcome with a
two-sample t-test. The same kind of test is used for all three outcomes. Each outcome is a
separate quality attribute with its own acceptance limit, so each one is judged on its own terms
against the conventional 0.05 threshold. Group sizes are 20 solar-dried lots and 20 mat-dried lots
for every outcome.

## Results

### Moisture content (percent, wet basis)

Mean 7.632 for solar drying and 8.232 for open mats, a difference of -0.600 percentage points.
The t statistic is -2.5961 and the p-value is 0.0133. At the 0.05 threshold the two drying methods
differ significantly on moisture content.

Lots that come off the mats hold more water. Moisture is the master control on how a lot keeps.
Wetter kernels support mould growth in the store and lose weight later as they dry down, so the
mat-dried lots carry more storage risk and need more careful drying before they are bagged.

### Aflatoxin B1 (micrograms per kilogram)

Mean 6.230 for solar drying and 9.630 for open mats, a difference of -3.400 micrograms per
kilogram. The t statistic is -2.2502 and the p-value is 0.0303. At the 0.05 threshold the two
drying methods differ significantly on aflatoxin B1.

This is the food safety outcome. Aflatoxin B1 is a toxin made by *Aspergillus* moulds, and it is
the one measurement here that can make a lot unfit to sell or unfit to eat rather than merely poor
quality. Mat-dried lots average more than half again as much of it. The contaminant is also
right-skewed, meaning most lots sit low while a few run far higher, so the group mean understates
what the worst individual deliveries look like. A single hot lot can pull a whole blended
consignment over a buyer's limit.

### Free fatty acids (percent, as oleic acid)

Mean 0.855 for solar drying and 1.030 for open mats, a difference of -0.175 percentage points.
The t statistic is -2.1987 and the p-value is 0.0341. At the 0.05 threshold the two drying methods
differ significantly on free fatty acids.

Free fatty acids measure how far the oil in the kernel has broken down. Higher values mean oil that
is closer to going rancid, which costs the lot on flavour, on shelf life, and on the price an oil
buyer will pay. The mat-dried lots are worse on this outcome too, which fits the slower, wetter
drying those lots went through.

## Conclusion and recommendation

Solar drying came out better than open-mat drying on all three declared outcomes, and all three
differences reach significance at the 0.05 threshold. Solar-dried lots were drier by 0.600
percentage points of moisture, carried 3.400 micrograms per kilogram less aflatoxin B1, and had
0.175 percentage points lower free fatty acids.

The recommendation to the collection centre is to move deliveries onto the simple solar dryers and
to treat open-mat drying as the fallback for times when dryer capacity runs out. The aflatoxin
result is the one that should drive the decision, because it is a safety issue and not only a
quality issue. Two practical steps go with it. First, keep testing incoming lots one by one rather
than relying on the group average, since the skewed aflatoxin values mean a few deliveries carry
most of the risk. Second, if mat drying has to be used, keep those lots separate at intake so a
high-aflatoxin lot cannot contaminate a good consignment when lots are bulked.

All numbers in this report are the values printed by `analysis.py`.
