# Data description

Two CSV files sit in this directory. Both describe the same study: a test of whether adding
live daphnia to a flake diet speeds larval growth in common frogs (*Rana temporaria*) at a
conservation breeding centre.

Both files are simulated. `make_data.py` in this directory created them, and re-running that
script with the Python standard library reproduces both files byte for byte.

## Experimental units and groups

The unit that received a treatment is the **rearing bin**. There are **16 bins**, stocked from
one pooled clutch, and each bin was assigned to one of two diets:

| Diet group (`diet_treatment` value) | What the bins were fed | Number of bins |
| --- | --- | --- |
| `standard_flake` | The centre's standard flake diet | 8 |
| `flake_plus_daphnia` | The same flake diet plus live daphnia | 8 |

Bins carry the labels `B01` through `B16`. Diets alternate along that sequence, which is how the
rack was filled: odd-numbered bins are `standard_flake`, even-numbered bins are
`flake_plus_daphnia`.

After six weeks, **12 tadpoles were netted from each bin**, photographed against a scale, and
measured for snout-vent length. That gives **192 measured tadpoles** in total. Every bin
contributed 12 tadpoles, so the counts are balanced and nothing is missing.

The two files hold the same measurements at two different levels. The raw file has one row per
tadpole. The summary file collapses each bin's 12 tadpoles into a single row, so it has one row
per bin, which is one row per treated unit.

---

## File 1: `tadpole_measurements.csv` (raw measurements)

**One row is one measured tadpole.** 192 data rows plus a header row. 12 rows per bin, 16 bins.

| Column | Type | Description |
| --- | --- | --- |
| `bin_label` | text | Identifier of the rearing bin the tadpole came from. One of `B01` ... `B16`. Appears on exactly 12 rows. |
| `diet_treatment` | text | The diet that bin received: `standard_flake` or `flake_plus_daphnia`. This is a property of the bin, so it is the same on all 12 rows of a bin. |
| `tadpole_no` | integer | Which of that bin's 12 netted tadpoles this row is, numbered 1 to 12 within each bin. It is a within-bin label only. `tadpole_no` 3 in bin `B01` and `tadpole_no` 3 in bin `B02` are different animals, and the number carries no meaning across bins. |
| `snout_vent_length_mm` | number | The measured snout-vent length of that tadpole, in millimetres, recorded to 0.01 mm. This is the response variable. Values run from 11.15 to 19.69 mm. |
| `water_temp_c` | number | Water temperature of the bin in degrees Celsius, recorded to 0.1 degrees, between 17.5 and 19.9. This was measured once per bin, not once per tadpole, so it repeats on all 12 rows of a bin. It is a bin-level covariate sitting in a tadpole-level file. |

Two of the five columns, `diet_treatment` and `water_temp_c`, are bin-level values repeated
down the rows. Only `tadpole_no` and `snout_vent_length_mm` vary from tadpole to tadpole within
a bin.

---

## File 2: `bin_summary.csv` (per-bin summary)

**One row is one rearing bin.** Exactly 16 data rows plus a header row, one for each of the 16
bins, 8 per diet.

| Column | Type | Description |
| --- | --- | --- |
| `bin_label` | text | Identifier of the bin, `B01` ... `B16`. Each label appears exactly once, so this column is the file's unique key. It matches `bin_label` in the raw file. |
| `diet_treatment` | text | The diet that bin received: `standard_flake` or `flake_plus_daphnia`. Matches the value the raw file carries for that bin. |
| `mean_snout_vent_length_mm` | number | The arithmetic mean of that bin's 12 `snout_vent_length_mm` values from the raw file, in millimetres, written to four decimal places. Values run from 13.0975 to 17.5142 mm. |
| `n_tadpoles_measured` | integer | How many tadpoles from that bin went into the mean. It is 12 for every bin in this study. |

### How the summary file relates to the raw file

The summary file is **derived from** the raw file and adds no new measurements. For each bin,
`mean_snout_vent_length_mm` is the mean of the 12 `snout_vent_length_mm` values that the raw
file records for that bin, and `n_tadpoles_measured` is the count of those rows. Averaging the
raw file by `bin_label` reproduces the summary file exactly.

Because the two files describe the same 192 measurements, they are not two independent sources
of evidence. The summary file has one row per bin, which is one row per unit that actually got
a diet. The raw file has 12 rows per bin, and those 12 rows are repeated measures from inside a
single bin rather than 12 separately treated units.

A note on the four decimal places: a mean of twelve 2-decimal values can land exactly on a
rounding boundary at three decimals, and three of these sixteen bin means do. Rounding those to
three decimals would depend on floating-point summation order, so the means are written to four
decimals instead, where no bin mean sits on a boundary. Recomputing any bin mean from the raw
file and rounding to four decimals reproduces the stored value exactly.

---

## How the values were generated

`make_data.py` uses a fixed seed (808) and only the Python standard library. Snout-vent length
was drawn as:

    length = diet mean + bin effect + tadpole noise

with a diet mean of 14.8 mm for `standard_flake` and 16.3 mm for `flake_plus_daphnia`, one bin
effect per bin drawn from a Normal distribution with standard deviation 0.9 mm (variation
between bins), and one noise term per tadpole drawn from a Normal distribution with standard
deviation 1.2 mm (variation between tadpoles inside a bin). Water temperature was drawn once per
bin, uniformly between 17.5 and 20.0 degrees Celsius, and does not feed into length.

The seed was picked from a small set of candidates so the realized group means land close to the
14.8 mm and 16.3 mm targets in the study specification. That choice looked only at how closely
the simulated data tracked those stated generating values. No test result or comparison between
the groups was computed or consulted when picking the seed.
