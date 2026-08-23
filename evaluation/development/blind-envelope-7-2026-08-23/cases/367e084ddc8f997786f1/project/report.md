# Faecal indicator contamination in harvested rainwater cisterns, by roof catchment material

District wet-season survey. Environmental health investigation.

## Background and design

Harvested rainwater is a primary domestic supply in this district, and the roof catchment is the
first surface the water touches. We surveyed twelve household rainwater storage cisterns, each
sampled once during the wet season. Six cisterns are fed by coated-metal roof catchments and six
by asphalt-shingle roof catchments. Each water sample was split in the laboratory, and the same
molecular assay for a faecal indicator gene was run three times on the same extract as instrument
triplicates. That gives 36 assay measurements in total, 18 per roof-material group.

## Data description

The analysis reads one committed data file, `cistern_faecal_indicator.csv`, which has a header row
and 36 data rows. **One row is one assay replicate: a single run of the faecal indicator gene assay
on one laboratory extract.**

| Column | Description |
| --- | --- |
| `cistern_id` | Identifier of the household cistern the sample came from, `CIS-01` through `CIS-12`. Each identifier appears on three rows. |
| `roof_catchment_material` | Material of the roof catchment feeding that cistern, either `coated_metal` or `asphalt_shingle`. |
| `assay_replicate` | Which of the three instrument replicates on that extract the row reports, 1, 2 or 3. |
| `log10_gene_copies_per_100ml` | Faecal indicator gene concentration for that assay replicate, as the base-ten logarithm of gene copies per 100 mL of water. |

## Method

We compared `log10_gene_copies_per_100ml` between the two roof materials with a standard
independent two-sample t-test. Every assay replicate in the table entered the test as one
observation, so the sample size is 18 assay measurements per roof-material group. Concentrations
were analysed on the log scale, which is the usual scale for gene copy data. The analysis script is
`analysis.py`; it reads the committed CSV and does not regenerate it.

## Results

| Roof catchment material | n (assay measurements) | Mean log10 copies/100 mL | SD |
| --- | --- | --- | --- |
| `coated_metal` | 18 | 2.823 | 0.284 |
| `asphalt_shingle` | 18 | 3.626 | 0.246 |

Cisterns fed by asphalt-shingle catchments carried a mean faecal indicator concentration 0.803
log10 units higher than cisterns fed by coated-metal catchments, which is about a 6.4-fold
difference on the original copies-per-100 mL scale. The independent two-sample t-test gave
t(34) = 9.07, p = 1.3e-10. Values ranged from 2.41 to 3.29 log10 copies/100 mL in the coated-metal
group and from 3.28 to 4.05 in the asphalt-shingle group.

## Interpretation

Roof catchment material is associated with a large and clearly measurable difference in faecal
indicator contamination of stored rainwater in this district. Asphalt-shingle catchments feed
cisterns with roughly six times the faecal indicator gene concentration of coated-metal catchments,
and the separation between the two groups is wide relative to the spread within either group: the
highest coated-metal measurement, 3.29, sits at the very bottom of the asphalt-shingle range. The plausible mechanism is surface texture: a rough granular shingle surface holds deposited
bird and animal faecal material and stays damp between rain events, while smooth coated metal
sheds debris and dries quickly. For district practice, households drawing domestic water from
shingle-fed cisterns carry the higher contamination risk and should be the first priority for
first-flush diverters, roof and gutter cleaning, and point-of-use treatment. Where a roof serving
a domestic cistern is replaced or newly built, coated metal is the better catchment surface on
water-quality grounds. These results come from one district in one wet season, so confirmation
elsewhere would strengthen a general recommendation.
