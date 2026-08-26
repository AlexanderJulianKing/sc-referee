# Data description

File: `groundnut_drying_quality.csv`

## What one row is

One row is one groundnut lot. A lot is a single farmer delivery of roughly 50 kg of freshly
lifted groundnuts brought to the collection centre. Each lot was dried as a unit by one drying
method, then sampled once for laboratory analysis. The file holds 40 lots (40 data rows plus a
header row): 20 dried in a simple solar dryer and 20 dried in the traditional way on open mats.
Every lot has a value in every outcome column, so there are no blank cells.

## Columns

| Column | Meaning | Unit / values |
| --- | --- | --- |
| `lot_id` | Identifier for the farmer delivery, in delivery order down the file | Text, `LOT-001` through `LOT-040` |
| `drying_method` | How the lot was dried | Text, exactly two values: `solar_dryer` (simple solar dryer) and `open_mat` (traditional open-mat drying) |
| `moisture_content_percent_wb` | Moisture content of the dried kernels, measured on a wet basis | Percent, wet basis |
| `aflatoxin_b1_ug_per_kg` | Aflatoxin B1 concentration in the dried kernels | Micrograms per kilogram |
| `free_fatty_acids_percent_oleic` | Free fatty acid content of the extracted oil, expressed as oleic acid | Percent, as oleic acid |

The three outcome columns appear in the order the outcomes were declared in the study plan:
moisture content first, aflatoxin B1 second, free fatty acids third.

## Notes on the values

The measurements are invented but chosen to be plausible for a humid tropical harvest season.
Moisture content sits in the high single digits in percent. Aflatoxin B1 is right-skewed, so most
lots sit low and a few run much higher, which is how the contaminant behaves in real deliveries.
Free fatty acids sit near one percent. Numbers are rounded the way a laboratory sheet would report
them: moisture and free fatty acids to two decimals, aflatoxin B1 to one decimal.
