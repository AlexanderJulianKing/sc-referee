# Fern spore cryobank germination trial

Sixteen fern spore accessions were collected between 2021 and 2024, each from a
single maternal sporophyte growing at its own site, and each spore lot was split
into two aliquots. One aliquot was kept in a conventional -20 C freezer and the
other in liquid-nitrogen vapour at -196 C. After 18 months, one plate of 100
spores per aliquot was sown and germination was scored once, giving every
accession a matched pair of germination percentages on a single line of the CSV.

One row is: one fern spore accession, carrying its matched freezer and cryogenic germination percentages after 18 months of storage
Independent unit column: accession_id

Columns:
- accession_id: unique code for the accession; it appears on exactly one row
- taxon: fern species the spores came from
- collection_site: place where the parent sporophyte was found
- collection_year: year the spores were harvested
- spores_scored: number of spores sown on each of the two plates (100)
- germ_pct_freezer_minus20c: percent germinated after storage at -20 C
- germ_pct_cryo_minus196c: percent germinated after storage at -196 C

Accessions came from different sites and were never subsampled or re-measured,
so no accession is represented twice and no two rows share a source lot. The two
percentages inside a row are matched measurements on the same lot, which is why
the analysis works with the within-row difference instead of treating the two
columns as independent samples.
