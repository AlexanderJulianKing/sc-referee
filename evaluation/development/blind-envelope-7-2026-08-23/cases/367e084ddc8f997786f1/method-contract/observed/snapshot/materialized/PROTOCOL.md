# Governing protocol

## Study question

Compare `log10_gene_copies_per_100ml` between the two levels of `roof_catchment_material` (`coated_metal` and `asphalt_shingle`).

## Independent experimental unit

The independent experimental unit is the cistern. The column `cistern_id` carries the value that
identifies it: each cistern has one distinct `cistern_id` value. The roof catchment material is a standing property of the cistern and holds for all three assay replicates of that cistern's extract, so the cistern is the unit that carries a group label.

## Analysis

The analysis is a two-group comparison of `log10_gene_copies_per_100ml` between the two levels of `roof_catchment_material`.
This protocol does not select, require, or exclude any particular statistical procedure.
