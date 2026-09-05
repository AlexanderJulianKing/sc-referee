# Data description: `hand_skin_study.csv`

Twelve-week hand-skin study in apprentice hairdressers at a salon chain. Fifty-four apprentices took
part, 27 in each of two glove protocols. Each apprentice was measured once, at the end of week 12.

**One row is one apprentice**, holding that apprentice's glove protocol and their seven week-12
outcome measurements. The file has 54 data rows plus a header row. Every cell is filled; there are
no blanks.

## Columns, in file order

| Column | Meaning | Unit / scale |
| --- | --- | --- |
| `participant_id` | Anonymous apprentice identifier, `AP001` through `AP054`, unique per row | none (text label) |
| `glove_protocol` | Which glove protocol the apprentice was assigned to. Exactly two values: `liner_under_nitrile` (thin cotton liners worn under disposable nitrile gloves) and `nitrile_only` (disposable nitrile gloves alone) | none (group label) |
| `transepidermal_water_loss_g_m2_h` | Transepidermal water loss on the back of the dominant hand. Declared **primary** barrier-function outcome 1. Higher means a leakier skin barrier | grams per square metre per hour (g/m²/h) |
| `stratum_corneum_hydration_au` | Stratum corneum hydration of the dominant hand. Declared **primary** barrier-function outcome 2. Higher means better hydrated skin | arbitrary capacitance units (a.u.) |
| `hand_eczema_severity_score_points` | Clinical hand eczema severity score, whole numbers. Declared secondary outcome. Higher means more severe | points on a 0 to 30 scale |
| `self_reported_itch_score_points` | Apprentice's own rating of hand itch, whole numbers. Declared secondary outcome. Higher means more itch | points on a 0 to 10 scale |
| `skin_surface_ph` | Skin surface pH of the dominant hand. Declared secondary outcome. Higher means a more alkaline, less protective surface | pH (dimensionless) |
| `erythema_index_au` | Erythema (skin redness) index. Declared secondary outcome. Higher means more redness | arbitrary units (a.u.) |
| `hand_symptom_days_last_4_weeks_days` | Number of days with hand symptoms reported over the previous four weeks, whole numbers. Declared secondary outcome | days (0 to 28) |

## Declared outcome order

The seven outcomes appear in the columns in the order declared in the study protocol before
recruitment: water loss, hydration, eczema severity, itch, pH, erythema, symptom days. The first
two are the protocol's primary barrier-function outcomes; the remaining five are secondary.

## Provenance

The measurements are invented for this exercise, not collected from real apprentices. They were
produced by `generate_data.py` in this directory, which draws each outcome from a normal
distribution per protocol group with a fixed random seed (20260826) and clips values to the
physiologically plausible range for each measure. Scores and day counts are rounded to whole
numbers. Row order is shuffled so participant IDs are not blocked by group.
