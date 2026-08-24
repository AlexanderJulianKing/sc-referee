# Polychaete abundance inside and outside the dredge spoil disposal footprint

## Background

The port authority asked whether seabed invertebrate life differs inside the dredge spoil disposal
footprint. We visited sixteen fixed sampling stations by boat: eight inside the footprint and eight
at matched reference positions of the same depth and sediment type. At each station the crew took
five separate grab samples from slightly different points within a twenty-metre radius. Each grab
covers 0.1 square metres. Every grab was sorted in the laboratory and its polychaete worms counted.

## The data

The survey produced one CSV file, `benthic_grabs.csv`, with 80 rows.

**One row is one grab sample:** a single 0.1 square metre grab of seabed sediment, taken at one
station and sorted in the laboratory, with the polychaete worms in that grab counted.

| Column | Description |
|--------|-------------|
| `station_ref` | Survey station reference, `ST-01` through `ST-16`. Identifies the sampling station the grab came from. |
| `station_group` | Whether the station lies inside the disposal footprint (`footprint`) or is a matched reference position (`reference`). |
| `grab_number` | Which grab this is within its station, numbered 1 to 5, in the order the crew collected them. |
| `polychaete_count` | Number of polychaete worms counted in this grab, over its 0.1 square metre area. A whole count. |

Forty rows carry `footprint` and forty carry `reference`.

## Method

We compared `polychaete_count` between the two levels of `station_group` with an independent
two-sample t-test assuming equal variances. Each of the 80 measured grabs entered the comparison as
its own observation, so the test ran on n = 80. The analysis is in `analysis.py`.

## Results

| Group | n | Mean worms per grab | SD | Range |
|-------|---|---------------------|----|-------|
| `footprint` | 40 | 53.77 | 16.09 | 24 to 82 |
| `reference` | 40 | 100.42 | 24.11 | 56 to 142 |

Reference grabs held 46.65 more worms per 0.1 square metre than footprint grabs on average
(95% CI 37.53 to 55.77). The difference is highly significant: t(78) = 10.179, p = 5.7e-16,
Cohen's d = 2.28.

## Conclusion

Polychaete abundance inside the dredge spoil disposal footprint is well under half that at the
matched reference positions: about 54 worms per 0.1 square metre against about 100. The gap is
large, consistent across the observed range, and comfortably outside what the grab-to-grab spread
in these data would produce by chance. On this evidence the disposal footprint supports a
substantially poorer polychaete fauna than comparable seabed nearby.
