# Panel-concordance emission for a 24-site assayed haplotype

Subject: short-read genotype calls at 24 biallelic autosomal sites, compared
against the allele carried by the same sites in reference panel HG-PANEL-A.

## Input accounting

- measured units (assayed variant sites): 24
- mean read depth across sites: 28.50
- per-site emission weight when the observed call equals the staged panel allele: 1
- per-site emission weight when they differ: 1/10

## Concordance accounting

- sites whose observed call equals the staged panel allele: 19
- per-unit agreement rate used by the emission accumulation: 19/24 = 0.791667
- discordant sites (total minus concordant): 5

## Quality-control comparison (not used in the emission)

- sites whose observed call equals the strand-complemented panel value (1 - panel allele): 5
- control check, concordant + complement-matching sites = total: 19 + 5 = 24

## Emission

- accumulated emission value (product of the 24 per-site weights): 1/100000 = 0.000010000000

[selected-result] panel-concordance emission for HG-PANEL-A over 24 assayed sites = 1/100000 = 0.000010000000 at agreement rate 19/24 = 0.791667
