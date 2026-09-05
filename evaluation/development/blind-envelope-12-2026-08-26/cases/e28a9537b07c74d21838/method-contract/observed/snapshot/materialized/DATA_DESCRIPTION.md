# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded Python generator. Running it writes `guinea_pig_hay_study.csv`. Same seed, same file every time. |
| `guinea_pig_hay_study.csv` | The analysis input. One row per guinea pig, 34 rows plus a header row. |

## `guinea_pig_hay_study.csv`

One row is one guinea pig: a single adult animal from a single household, with
its feeding treatment and its six end-of-study measurements after the eight
week feeding period. Each animal appears exactly once. There are no blank
cells; every animal has a value in every column.

The file has 8 columns: the animal identifier, the feeding treatment, and then
the six protocol outcomes in the order the protocol declared them.

| Column | Unit | What it holds |
| --- | --- | --- |
| `animal_id` | none (text label) | Study identifier for the animal, `GP01` through `GP34`. Unique across rows. |
| `group` | none (text label) | Feeding treatment. Exactly two possible entries: `hay_rack` for long-stem hay from an open rack, `forage_block` for the same hay compressed into forage blocks. 17 animals in each. |
| `hay_intake_g_day` | grams per day | Declared outcome 1. Daily hay dry matter intake, averaged over the two recorded days. |
| `body_weight_g` | grams | Declared outcome 2. Body weight at the end of the eight weeks, recorded at the sedated examination. |
| `faecal_output_g_day` | grams per day | Declared outcome 3. Daily faecal output, averaged over the two recorded days. |
| `faecal_particle_mm` | millimetres | Declared outcome 4. Median faecal particle size, a marker of how finely the animal chewed its hay. |
| `chewing_min_day` | minutes per day | Declared outcome 5. Time spent chewing, scored from video of one recorded day. |
| `occlusal_angle_deg` | degrees | Declared outcome 6. Cheek tooth occlusal angle, measured on the intraoral photographs. |

## Ranges in the file as generated

| Column | Minimum | Maximum |
| --- | --- | --- |
| `hay_intake_g_day` | 36.1 | 73.4 |
| `body_weight_g` | 710 | 1194 |
| `faecal_output_g_day` | 27.3 | 59.0 |
| `faecal_particle_mm` | 0.52 | 1.41 |
| `chewing_min_day` | 110 | 244 |
| `occlusal_angle_deg` | 23.5 | 37.9 |

The weight column deliberately includes animals at both the light and the heavy
end of the adult range, not only animals near the middle.

## How the numbers were produced

`make_data.py` draws each animal's values from a fixed seed (`SEED = 20260826`)
using the Python standard library `random` module, so the CSV is reproducible.
Treatment labels are shuffled across the 34 animal identifiers, 17 per group.
Within an animal, daily hay intake rises slightly with body weight, faecal
output tracks intake, and chewing time rises with the amount of hay worked
through, so the columns carry the correlations a real feeding record would
carry. Draws that fall outside the plausible range for a measurement are placed
a small random distance back inside the nearer limit.
