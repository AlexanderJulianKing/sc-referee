# Data description

## Files

| File | What it is |
| --- | --- |
| `make_data.py` | Deterministic seeded generator (`SEED = 20260824`, NumPy). Running it rewrites `marmots.csv` identically. |
| `marmots.csv` | The field dataset: 58 data rows plus one header row. |

## `marmots.csv`

One row is one adult alpine marmot, trapped, measured and released once during a single summer
season. Each animal appears exactly once. There are 58 rows: 29 marmots from colonies whose burrow
systems sit within 100 m of a groomed piste, and 29 from undisturbed alpine meadow colonies at
similar elevation and aspect. Every cell is filled; there are no missing values.

| Column | Type | Units | Meaning |
| --- | --- | --- | --- |
| `marmot_id` | text | none | Unique animal identifier, `MAR-001` through `MAR-058`, numbered in trapping order. |
| `disturbance_group` | text | none | Colony type. Exactly two values: `piste_adjacent` (burrow system within 100 m of a groomed piste) and `undisturbed` (alpine meadow colony away from pistes). 29 rows each. |
| `body_mass_kg` | number, 2 decimals | kilograms | Pre-hibernation body mass at capture. Recorded range in this file: 2.83 to 5.53. |
| `fgm_ng_per_g` | number, 1 decimal | nanograms per gram of dry faeces | Faecal glucocorticoid metabolite concentration from the sample collected at handling. Recorded range: 85.7 to 399.8. |
| `emergence_doy` | integer | day of year | Date the animal was first seen above ground after hibernation, as a day number where 1 is 1 January. Recorded range: 97 to 135. |
| `vigilance_pct` | number, 1 decimal | percent | Share of a standardised focal observation period the animal spent in an upright vigilance posture. Recorded range: 4.6 to 28.5. |
| `ectoparasite_count` | integer | count | Number of ectoparasites found during a standardised body search at handling. Recorded range: 0 to 25. |

## How the values were produced

`make_data.py` draws each colony type's five outcomes from fixed distributions with a fixed seed:
body mass and emergence day from normal distributions, glucocorticoid metabolites from a lognormal
distribution (faecal assay values are right-skewed), vigilance from a gamma distribution, and
ectoparasite counts from a negative binomial (Poisson counts with gamma-distributed individual
susceptibility, which spreads burdens more widely than a plain Poisson would). Draws are clipped to
the protocol's plausible field limits: mass 2.8-5.6 kg, metabolites 50-400 ng/g, emergence day
95-135, vigilance 3-30 percent, ectoparasite count 0-25. Row order is then shuffled with the same
seed, so the two colony types are interleaved rather than blocked.
