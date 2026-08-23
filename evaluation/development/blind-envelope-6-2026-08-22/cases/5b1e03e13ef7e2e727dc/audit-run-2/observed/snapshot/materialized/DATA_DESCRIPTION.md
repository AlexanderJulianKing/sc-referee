# Data description

## File

`bifidobacterium_samples.csv` — the sequenced stool samples from the infant feeding
cohort. It is the only data file in the project. It is produced by `make_data.py`,
which uses a fixed random seed, so rerunning the script reproduces the file exactly.

## What one row represents

One row is **one sequenced stool sample**: a single stool specimen collected from one
infant at one study visit, and the relative abundance of the genus *Bifidobacterium*
measured in that specimen.

## Units and counts

- **Infants enrolled:** 18
- **Feeding groups:** 2, with 9 infants in each
- **Scheduled visits per infant:** 5, at roughly 2, 6, 10, 14 and 18 weeks of age
- **Rows (stool samples) in the file:** 87
  - `breastfed`: 44 samples from 9 infants
  - `formula`: 43 samples from 9 infants

The table is unbalanced: 3 infants missed one scheduled visit each (one breastfed
infant at 10 weeks, one formula infant at 6 weeks, one formula infant at 18 weeks),
so 87 samples were collected out of 90 scheduled.

## The two groups

The `feeding_group` column takes exactly two values:

| Value | Meaning |
| --- | --- |
| `breastfed` | Exclusive breastfeeding regimen |
| `formula` | Standard infant formula regimen |

Feeding group is fixed for an infant for the whole study; every sample from a given
infant carries the same group label.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `infant_id` | text | Study identifier of the infant the sample came from. `BF-01` … `BF-09` for the breastfed group and `FF-01` … `FF-09` for the formula group. 18 distinct values. |
| `feeding_group` | text | The infant's feeding regimen: `breastfed` or `formula`. |
| `age_weeks` | integer | Age of the infant in weeks at the study visit when the sample was collected. One of 2, 6, 10, 14, 18. |
| `sample_id` | text | Unique identifier of the stool sample, `S001` through `S087`. One value per row; no repeats. |
| `bifidobacterium_pct` | number | Relative abundance of the genus *Bifidobacterium* in that sample, as a percentage of sequencing reads. Recorded to two decimal places. Range in this file: 14.34 to 61.04. Values are bounded to lie between 0 and 100. |

There are no missing cells: a missed visit is absent as a row rather than present with
a blank value.

## How the values were generated

`make_data.py` builds each measurement from three parts: a group-level trajectory that
declines with age, a per-infant offset that shifts all of that infant's samples up or
down, and a per-sample deviation. The group trajectories run from about 55 percent at
2 weeks down to about 40 percent at 18 weeks for the breastfed group, and from about
34 percent down to about 26 percent for the formula group. The resulting file has group
means of 45.31 percent (breastfed) and 28.86 percent (formula).
