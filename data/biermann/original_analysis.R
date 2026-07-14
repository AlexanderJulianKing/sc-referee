# Differential expression as run in the original study (excerpt).
# Biermann et al. 2022, GSE200218 — tumor cells, brain vs. extracranial metastasis.
# Full analysis: the authors' own repository; this excerpt is the DE step sc-referee reviews.
#
# Note the inferential unit: FindMarkers tests each CELL as an independent observation
# (Seurat's default), with no patient-level aggregation and no covariate adjustment.

library(Seurat)

seu <- readRDS("data_MBPM_scn.rds")
seu <- subset(seu, sequencing == "Single nuclei" & cell_type_main == "Tumor cells")
Idents(seu) <- seu$organ

# Cell-level differential expression (MAST), Brain vs Peripheral, no adjustment covariates.
markers <- FindMarkers(
  seu,
  ident.1 = "Brain",
  ident.2 = "Peripheral",
  test.use = "MAST",
  assay = "RNA",
  min.pct = 0,
  logfc.threshold = 0,
  max.cells.per.ident = min(table(seu$organ))
)

markers$gene <- rownames(markers)
write.csv(markers, "results/original_table_s3_snrna.csv", row.names = FALSE)
