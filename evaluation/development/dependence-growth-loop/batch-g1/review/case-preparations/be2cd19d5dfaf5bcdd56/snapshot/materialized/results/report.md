# Cryobank germination trial: paired comparison of two storage regimes

## Data

- Source file: data/input.csv
- Independent units (fern spore accessions): 16
- Rows analysed: 16 (exactly one row per accession)
- Spores scored per aliquot: 100

## Design and analysis

Each accession is a spore lot harvested from one maternal sporophyte at its
own site. Every lot was split into two aliquots: one held at -20 C and one
held at -196 C. After 18 months a single plate per aliquot was sown and
scored, so an accession yields exactly one matched pair and exactly one
analysed difference (cryo minus freezer, in percentage points).

The primary test is a two-sided paired t-test on the 16 accession-level
differences (df = 15). A Wilcoxon signed-rank test on the same differences
is reported as a distribution-free check.

## Results

| quantity | value |
| --- | --- |
| mean germination at -20 C (%) | 48.25 |
| mean germination at -196 C (%) | 56.25 |
| mean paired difference (pp) | 8.00 |
| SD of paired differences (pp) | 6.00 |
| standard error of the mean difference (pp) | 1.50 |
| 95% CI for the mean difference (pp) | 4.80 to 11.20 |
| Cohen's dz | 1.33 |

Paired t-test: t(15) = 5.333, p < 0.0001 (two-sided).
Wilcoxon signed-rank test: W = 0.0, p < 0.0001 (two-sided).

[selected-result] Paired t-test on 16 accession-level differences (one difference per accession): cryogenic storage at -196 C raised 18-month spore germination by 8.00 percentage points relative to -20 C storage (95% CI 4.80 to 11.20 pp; t(15) = 5.333, p < 0.0001, two-sided).

## Reading the numbers

All 16 of the 16 accessions germinated at least as well after cryogenic
storage; the smallest single-accession gain was 1 pp and the largest
was 19 pp. The accession is the unit of replication: no accession
contributes more than one row, nothing is pooled across accessions before
testing, and the 16 differences entering the test are the 16 independent
observations the design provides. The interval describes a within-accession
contrast, not the spread of absolute germination between accessions, which
runs from 29 to 66 percent under freezer storage.
