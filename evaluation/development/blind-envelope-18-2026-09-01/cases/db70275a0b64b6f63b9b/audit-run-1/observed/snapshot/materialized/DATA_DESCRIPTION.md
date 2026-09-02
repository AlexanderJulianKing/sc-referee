# Data description

Two authored, fixed CSV files support this project: `data.csv` (the raw batch
measurements) and `adjusted_pvalues.csv` (the inferential export received from an
upstream pipeline stage that runs outside this project).

## data.csv

One row is one production batch of cold-pressed rapeseed oil. Seventy-two batches
were sampled over one season from two growing regions supplying the same mill, and
each batch was analysed once, in a single laboratory run order. The file holds 72
data rows plus a header. There are 36 lowland batches and 36 upland batches. Every
batch has a value for every declared outcome; there are no blank cells.

| Column | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `batch_id` | text | none | Batch identifier, `B001` through `B072`, unique, in laboratory run order. |
| `region` | text | none | Growing region of the farms that supplied the batch. Exactly two values: `lowland`, `upland`. |
| `peroxide_value_meq_o2_kg` | number | milliequivalents of oxygen per kilogram | Declared outcome 1: peroxide value. Two decimal places. |
| `free_fatty_acids_pct` | number | percent oleic acid | Declared outcome 2: free fatty acid content. Two decimal places. |
| `total_tocopherols_mg_kg` | number | milligrams per kilogram | Declared outcome 3: total tocopherols. Whole numbers. |
| `oxidative_stability_index_h` | number | hours | Declared outcome 4: oxidative stability index. One decimal place. |
| `chlorophyll_pigments_mg_kg` | number | milligrams per kilogram | Declared outcome 5: chlorophyll pigments. One decimal place. |
| `erucic_acid_pct` | number | percent of total fatty acids | Declared outcome 6: erucic acid content. Three decimal places. |

The six outcome columns appear in the order the quality plan declared them, after
`batch_id` and `region`. Observed value spans in the file are: peroxide value 1.22
to 3.63; free fatty acids 0.18 to 0.92; total tocopherols 398 to 722; oxidative
stability index 4.1 to 12.2; chlorophyll pigments 4.3 to 24.6; erucic acid 0.064
to 0.607. Each span sits inside the plausible range the quality plan states for
that outcome.

## adjusted_pvalues.csv

One row is one declared outcome, in the declared order, so the file holds 6 data
rows plus a header.

| Column | Type | Meaning |
| --- | --- | --- |
| `outcome` | text | The outcome name, written exactly as the matching column name in `data.csv`. |
| `adjusted_p_value` | number | The adjusted p-value the upstream stage exported for that outcome. |

This file is an import, not a result of this project. A standing laboratory
pipeline stage upstream of this project tested the whole declared family of six
outcomes and applied a Holm-Bonferroni multiple-comparison adjustment across all
six together, then exported the adjusted values. The numbers are written to six
significant figures, in plain or scientific notation depending on size. Because
Holm-Bonferroni is a step-down procedure, several outcomes can carry the same
adjusted value.

## Provenance

Both CSV files are fixed authored files. `generate_data.py` in this staging
directory produced them once; it is not part of the project's analysis and is not
re-run by anything in the project.
