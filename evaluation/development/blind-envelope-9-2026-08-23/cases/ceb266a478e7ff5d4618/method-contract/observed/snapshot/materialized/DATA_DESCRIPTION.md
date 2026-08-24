# Data description

## The study

A nursery tested whether a mycorrhizal inoculant changes fruit sweetness in potted highbush
blueberry bushes. Twenty-four bushes were grown in identical pots under one polytunnel. Twelve
bushes were inoculated at planting and twelve were left uninoculated. At harvest the technician
picked five separate berry clusters from each bush and read the juice of each cluster on a
refractometer.

## Files

There is one data file: `blueberry_brix_clusters.csv`. It holds every individual cluster
measurement, with no averaging or other processing applied. There is no second summary file; the
per-bush averages are computed in the analysis, not stored here.

## What one row is

**One row is one berry cluster from one bush: a single refractometer reading.** A row is not a
bush. Each bush contributes five rows, one per cluster.

## Size

- 120 data rows, plus one header row.
- 24 bushes (the experimental units), 5 clusters measured on each.
- 12 bushes inoculated, 12 uninoculated. Treatment is fixed for a bush, so all five rows for a
  given bush carry the same treatment label.

## Groups

| Treatment      | Bushes | Cluster rows | Bush labels |
| -------------- | ------ | ------------ | ----------- |
| `inoculated`   | 12     | 60           | BB-01, BB-04, BB-06, BB-08, BB-12, BB-13, BB-14, BB-15, BB-18, BB-20, BB-22, BB-23 |
| `uninoculated` | 12     | 60           | BB-02, BB-03, BB-05, BB-07, BB-09, BB-10, BB-11, BB-16, BB-17, BB-19, BB-21, BB-24 |

## Columns

| Column | Type | Description |
| ------ | ---- | ----------- |
| `bush_label` | text | Pot label identifying the bush the cluster came from, `BB-01` through `BB-24`. This is the experimental unit. Each label appears in exactly 5 rows. |
| `treatment` | text | Inoculation treatment applied to that bush at planting. Two values: `inoculated` (mycorrhizal inoculant applied) and `uninoculated` (no inoculant). Constant within a bush. |
| `cluster_number` | integer | Which of the bush's five picked clusters this reading came from, numbered 1 to 5 within each bush. It is a within-bush label only; cluster 3 on BB-07 has nothing to do with cluster 3 on BB-08. |
| `soluble_solids_brix` | number | The refractometer reading on that cluster's juice: soluble solids in degrees Brix, recorded to one decimal place. This is the outcome measured. |

## Notes on the values

- Readings run from 10.1 to 15.1 degrees Brix, with about 96 percent falling between 10.0 and 14.5.
- Clusters picked from the same bush resemble each other more closely than clusters from different
  bushes, which is why the five clusters per bush are subsamples of the bush rather than
  independent observations.
- The file has no missing values: every one of the 24 bushes has all five cluster readings.

## How the file was made

`make_data.py` in this directory generates `blueberry_brix_clusters.csv`. It uses only the Python
standard library and a fixed random seed (20260823), so rerunning it reproduces the identical file.
