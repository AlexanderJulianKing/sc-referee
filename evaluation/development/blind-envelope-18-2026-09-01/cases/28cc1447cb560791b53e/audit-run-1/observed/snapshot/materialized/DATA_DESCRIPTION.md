# data.csv

## What one row represents

One row is one adult female orb-weaving spider, together with the single web that
spider occupied at the time of measurement. Each spider and its web were measured once,
at dawn, before the spider was collected. Sixty spiders were collected on consecutive
still nights across the city park system: thirty at sites under streetlights and thirty
at unlit sites at least two hundred metres away.

The file has a header row plus 60 data rows. Each spider appears exactly once. There are
no blank cells; every spider has a value for every column.

## Columns

| Column | Type | Unit | Description |
| --- | --- | --- | --- |
| `spider_id` | text | none | Identifier for the individual spider, `SP01` through `SP60`. Unique across the file. |
| `site_lighting` | text | none | The lighting condition of the site where the spider was collected. Exactly two possible values: `lit` (site under a streetlight) and `unlit` (site with no artificial light nearby). Thirty rows carry each value. |
| `body_mass_mg` | number | milligrams (mg) | Body mass of the spider, recorded to one decimal place. |
| `cephalothorax_width_mm` | number | millimetres (mm) | Width of the cephalothorax at its widest point, recorded to two decimal places. |
| `web_capture_area_cm2` | number | square centimetres (cm2) | Area of the capture spiral of the web, recorded to one decimal place. |
| `mesh_width_mm` | number | millimetres (mm) | Mesh width, meaning the spacing between neighbouring capture threads, recorded to two decimal places. |
| `prey_items` | integer | none (a count) | Number of prey items present in the web at dawn. A count, so whole numbers only, and zero is a valid recorded value. |

The five outcome columns appear in the order the field plan declared them in advance:
body mass, cephalothorax width, web capture area, mesh width, prey items.

## Value ranges present in the file

These are the ranges the recorded values actually span, given for orientation only.

| Column | Minimum | Maximum |
| --- | --- | --- |
| `body_mass_mg` | 69.0 | 192.0 |
| `cephalothorax_width_mm` | 2.43 | 4.54 |
| `web_capture_area_cm2` | 221.1 | 714.1 |
| `mesh_width_mm` | 2.74 | 5.95 |
| `prey_items` | 0 | 15 |

## Format notes

Comma-separated, UTF-8, one header line, no quoting needed anywhere in the file, no index
column, no missing-value markers.
