# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (NumPy, seed `20260146`). Running it rewrites `antenatal_iron_study.csv` byte-for-byte. |
| `antenatal_iron_study.csv` | The study data set. 96 data rows plus one header row. |

## `antenatal_iron_study.csv`

One row is one pregnant woman assessed at 28 weeks of gestation in the hospital
antenatal clinic, holding her participant identifier, the four laboratory results
from her single blood draw at that visit, and the supplement regimen she had been
taking since her first trimester. Each woman appears exactly once; there is one
blood draw per woman and no repeated measurements. Every cell is filled, so there
are no missing values anywhere in the file.

96 women in total: 48 on iron plus folic acid, 48 on folic acid alone.

### Columns, in file order

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `participant_id` | text | none | Clinic identifier for the woman, `ANC-001` through `ANC-096`, assigned in enrolment order. Unique across the file. |
| `haemoglobin_g_dl` | number | grams per decilitre | Haemoglobin concentration in whole blood at the 28-week draw. One decimal place. Observed range 9.3 to 13.9. |
| `ferritin_ug_l` | number | micrograms per litre | Serum ferritin at the 28-week draw. One decimal place. Right-skewed, as ferritin results usually are. Observed range 5.8 to 64.1. |
| `transferrin_saturation_pct` | number | percent | Transferrin saturation at the 28-week draw. One decimal place. Observed range 6.6 to 37.5. |
| `hepcidin_ng_ml` | number | nanograms per millilitre | Serum hepcidin at the 28-week draw. One decimal place. Right-skewed. Observed range 3.9 to 24.9. |
| `supplement_regimen` | text | none | The woman's supplement regimen, exactly two distinct values: `iron_plus_folic_acid` (48 women) or `folic_acid_only` (48 women). |

The four outcome columns appear in the order the study protocol declares them:
haemoglobin, ferritin, transferrin saturation, hepcidin.

### How the values were produced

`make_data.py` draws each woman a single latent iron-status score, then draws the
four markers from that score plus marker-specific noise, so the four results move
together within a woman the way real iron markers do. Haemoglobin and transferrin
saturation are drawn on the natural scale; ferritin and hepcidin are drawn on a log
scale to give the right-hand tail that laboratory reports for those two markers
show. Values are clipped to physiologically possible limits and rounded to one
decimal place before being written.
