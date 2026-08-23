# Data description: organoid barrier function by tight-junction genotype

## File

`organoid_teer.csv` — 108 data rows plus one header row, 6 columns, comma separated.

## What one row is

One row is **one well of intestinal organoids, measured once on day 7 after seeding**. The row
carries the well's day-7 transepithelial electrical resistance (TEER) together with the properties
of the donor that well came from.

A well is not a person. Each donor's cell preparation was seeded into 6 wells on the same plate
layout, so **every donor appears on 6 rows**, and those 6 rows repeat the same `donor_id`,
`genotype`, `passage_number`, and `donor_age_years`. The 6 wells of a donor are technical
replicates of that one donor: they share the donor's genetic background and one common cell
preparation.

## Units and counts

| Level | Count |
|---|---|
| Donors (the experimental unit) | 18 |
| Non-carrier donors | 9 (D01–D09) |
| Carrier donors | 9 (D10–D18) |
| Wells per donor | 6 |
| Wells (rows) in the file | 108 (54 per genotype group) |

## The two groups

`genotype` is a fixed property of the person the cells came from, so it varies **between donors and
never between wells within a donor**.

- `non_carrier` — donor does not carry the barrier-risk variant of the tight-junction gene. 9
  donors, 54 wells.
- `carrier` — donor carries the barrier-risk variant. 9 donors, 54 wells.

The independent replicate for any comparison of these groups is the donor: 9 per group, 18 in
total. Counting the 108 wells as 108 independent observations would treat technical replicates as
separate people.

## Columns

| Column | Type | Varies at | Description |
|---|---|---|---|
| `donor_id` | text | donor | Donor label, `D01`–`D18`. Repeats on the 6 rows belonging to that donor. Identifies the experimental unit. |
| `genotype` | text | donor | Tight-junction genotype group of the donor. Exactly two values: `non_carrier` or `carrier`. Constant across a donor's 6 wells. |
| `well_position` | text | well | Position of the well on the culture plate: `A1`, `A2`, `A3`, `B1`, `B2`, `B3`. Every donor uses the same 6-position layout, so each donor contributes each position exactly once. |
| `passage_number` | integer | donor | Passage number of the organoid preparation that was seeded, 2–5. One preparation per donor, so this is constant across that donor's 6 wells. |
| `donor_age_years` | integer | donor | Age in whole years of the biopsy donor, 26–68. Constant across that donor's 6 wells. |
| `teer_day7_ohm_cm2` | number, 1 decimal place | well | The outcome: transepithelial electrical resistance measured on day 7 after seeding, in ohm·cm². One measurement per well. Higher means a tighter, stronger epithelial barrier. |

## Structure that is present in the values

The numbers were generated so that the nesting of wells inside donors is visible.

- Non-carrier wells average **410.1** ohm·cm²; carrier wells average **319.7** ohm·cm².
- Donors differ a lot from one another: the standard deviation of the 9 donor means is **45.6**
  (non-carriers) and **39.8** (carriers) ohm·cm².
- Wells within a donor vary less: the average within-donor standard deviation is **28.2**
  (non-carriers) and **30.2** (carriers) ohm·cm².
- Observed well values span **181.6** to **550.6** ohm·cm²; donor means span **267.9** to **478.5**.

Because the donor-to-donor spread is larger than the well-to-well spread, wells from the same donor
are correlated. That is the reason the donor has to stay intact as the unit of any resampling or
test.

## Provenance

The file is simulated, not measured. `make_data.py` in this directory produced it with the Python
standard library only and a fixed seed (`SEED = 20260132`), so re-running
`/usr/local/bin/python3 make_data.py` rewrites the identical CSV.

sha256 of `organoid_teer.csv`:
`71d094db7c3941b14bbf6bde839335d1fdc830cd6d23a8dc0f04897701ef0d4b`
