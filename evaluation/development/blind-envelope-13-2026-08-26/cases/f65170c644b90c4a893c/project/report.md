# Back-slopped versus spontaneous fermentation of gari

## Data

The data file is `gari_fermentation_batches.csv`. It holds 40 data rows plus a header row.

One row is one fermentation batch: a single 20 kg unit of grated cassava mash fermented in its own
press bag and sampled once, 72 hours after fermentation started. Each batch is measured once, so
there are no repeated measures. Twenty batches were fermented with a back-slopped inoculum carried
over from a previous successful batch, and twenty were left to ferment spontaneously with no added
inoculum.

| Column | Meaning | Unit |
| --- | --- | --- |
| `batch_id` | Batch identifier, unique across the study. `BS-01` to `BS-20` are the back-slopped batches, `SP-01` to `SP-20` the spontaneous ones. | none (text label) |
| `fermentation_treatment` | Group assignment. Exactly two values: `back_slopped` and `spontaneous`. | none (category) |
| `total_cyanogenic_potential_mg_hcn_eq_per_kg_dw` | Declared outcome 1. Total cyanogenic potential of the finished gari. | milligrams hydrogen cyanide equivalent per kilogram dry weight |
| `ph_72h_ph_units` | Declared outcome 2. pH of the mash measured at 72 hours. | pH units |
| `titratable_acidity_percent_lactic_acid` | Declared outcome 3. Titratable acidity of the mash at 72 hours, expressed as lactic acid. | percent lactic acid (g lactic acid per 100 g) |
| `moisture_content_percent` | Declared outcome 4. Moisture content of the finished gari. | percent by mass |

The outcome columns appear in the order the four outcomes were declared in the study plan. Every
batch has a value in every outcome column, and there are no blank cells. The measurements are
invented for this project, not collected from a real processing run.

## Method

Each group holds 20 batches. Every outcome is compared between the two groups with the same test, a
two-sided Welch two-sample t-test.

The four declared outcomes form one family, so the family-wise error rate is controlled. The family
size is 4 and the family-wise level is 0.05. The Sidak per-comparison threshold is

    1 - (1 - 0.05) ** (1 / 4) = 0.012741

Every verdict below compares that outcome's p-value with 0.012741, not with 0.05.

## Results

Group sizes are 20 back-slopped and 20 spontaneous for all four outcomes.

### Outcome 1: total cyanogenic potential (mg HCN eq / kg dry weight)

Mean 9.4500 for back-slopped, 12.0500 for spontaneous. The back-slopped batches are 2.6000 lower.
t = -3.4973, p = 0.00131933. This is below the 0.012741 threshold, so the difference is significant.

### Outcome 2: pH at 72 hours (pH units)

Mean 4.0245 for back-slopped, 4.2790 for spontaneous. The back-slopped batches are 0.2545 lower.
t = -6.3043, p = 3.07609e-07. This is below the 0.012741 threshold, so the difference is
significant.

### Outcome 3: titratable acidity (percent lactic acid)

Mean 0.9150 for back-slopped, 0.7975 for spontaneous. The back-slopped batches are 0.1175 higher.
t = 3.0844, p = 0.00402361. This is below the 0.012741 threshold, so the difference is significant.

### Outcome 4: moisture content (percent by mass)

Mean 9.5150 for back-slopped, 9.5700 for spontaneous. The back-slopped batches are 0.0550 lower.
t = -0.2354, p = 0.815186. This is above the 0.012741 threshold, so the difference is not
significant.

## Conclusion

On this data, processors should use the back-slopped inoculum. Back-slopped batches finished with a
lower total cyanogenic potential, a lower pH and a higher titratable acidity than spontaneous
batches, and all three of those differences hold up against the Sidak threshold of 0.012741.
Moisture content came out about the same in both groups, so the choice of treatment does not appear
to change how dry the finished gari is.

Two limits are worth stating. The measurements are invented rather than collected, so the numbers
above describe this synthetic data set and not real processing lines. The study also sampled each
batch once at 72 hours, so it says nothing about how the two treatments differ earlier or later in
fermentation.
