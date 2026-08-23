# Data description

## File

`milk_yield.csv` — 120 data rows plus one header row, 6 columns, comma separated, UTF-8.

There is only one data file in this project. No summary CSV is produced.

## What one row represents

One row is **one cow on one weekly test day**: a single animal's recorded daily milk yield for a
single test day, together with that animal's identity, her ration, the test week, her days in milk
on that day, and her parity.

A row is therefore not a cow. Each of the 20 cows contributes 6 rows, one per test week.

## Units and counts

| Quantity | Count |
| --- | --- |
| Cows (experimental units) | 20 |
| Cows per ration group | 10 |
| Weekly test days per cow | 6 |
| Rows per cow | 6 |
| Total data rows | 120 |
| Test-day records per ration group | 60 |

Each cow received one ration for the entire trial and never switched, so all 6 rows belonging to a
given `cow_tag` carry the same value of `ration`. The 6 rows for a cow are repeated measurements on
that one animal.

## The two groups

The `ration` column has exactly two values:

- `conventional_soybean_meal` — the control total mixed ration, with soybean meal as the source of
  rumen-undegradable protein. 10 cows: HO-2101, HO-2103, HO-2105, HO-2107, HO-2109, HO-2111,
  HO-2113, HO-2115, HO-2117, HO-2119. 60 test-day records.
- `treated_canola` — the test total mixed ration, with treated canola meal as the source of
  rumen-undegradable protein. 10 cows: HO-2102, HO-2104, HO-2106, HO-2108, HO-2110, HO-2112,
  HO-2114, HO-2116, HO-2118, HO-2120. 60 test-day records.

Odd-numbered tags fall in the control group and even-numbered tags in the treated-canola group, so
neither group is a contiguous block of tag numbers.

## Columns

| Column | Type | Values in this file | Meaning |
| --- | --- | --- | --- |
| `cow_tag` | text | `HO-2101` … `HO-2120`, 20 distinct values, each appearing 6 times | Ear-tag identifier of the individual lactating Holstein cow. Identifies the experimental unit and links a cow's 6 test-day rows together. |
| `ration` | text | `conventional_soybean_meal` or `treated_canola` | The total mixed ration formulation the cow was assigned to. Constant within a cow for the whole trial. |
| `test_week` | integer | 1–6 | Which of the six consecutive weekly test days the row records. Week 1 is the first test day after enrolment. |
| `days_in_milk` | integer | 90–183 | Days since the cow's calving, as of that test day. Range at week 1 is 90–148 days, matching the enrolment criterion; it increases by 7 for each later test week within a cow. |
| `parity` | integer | 1–4 (10 cows parity 1, 7 parity 2, 2 parity 3, 1 parity 4) | Number of times the cow has calved. A cow-level trait, constant across her 6 rows. |
| `milk_yield_kg` | decimal, 1 place | 23.8–42.9 | The outcome: the cow's daily milk yield in kilograms on that test day. |

## Structure built into the values

The numbers were generated so the intended structure is visible:

- Group level: control mean 30.60 kg/d (SD 3.11 across its 60 records), treated-canola mean
  32.73 kg/d (SD 4.08 across its 60 records).
- Between cows: each cow has her own persistent level; the standard deviation of the 20 cow means
  is 3.49 kg.
- Within a cow: her 6 weekly test days scatter around her own level with an average within-cow
  standard deviation of 1.64 kg.

Because a cow's repeated test days are drawn around that cow's own level, the 6 records from one
animal are correlated with each other rather than independent.

## How the file was produced

`make_data.py` in this directory generates `milk_yield.csv` using only the Python standard library,
with a fixed random seed (`SEED = 20260814`). Re-running it reproduces the file byte for byte:

```
/usr/local/bin/python3 make_data.py
```
