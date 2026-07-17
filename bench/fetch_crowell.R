#!/usr/bin/env Rscript
# Load the muscat paper's OWN mouse data (Crowell19_4vs4: 8 CD-1 mice, 4 vehicle vs 4 LPS,
# cortex snRNA-seq) from Bioconductor's muscData/ExperimentHub and save it as an .rds that
# bench/mathys_convert.R turns into an h5ad. Mouse data -> no human-subjects access restrictions.
#
#   Rscript bench/fetch_crowell.R [out=data/crowell.rds]
#
# Then (reusing the general pipeline):
#   Rscript bench/mathys_convert.R data/crowell.rds data/crowell_export
#   .venv/bin/python bench/mathys_build_h5ad.py data/crowell_export data/crowell.h5ad
#   MATHYS_DONOR=sample_id MATHYS_CONDITION=group_id MATHYS_CELLTYPE=cluster_id \
#     MATHYS_REF=Vehicle MATHYS_TEST=LPS PYTHONPATH=src:. .venv/bin/python bench/mathys_anchor.py
suppressPackageStartupMessages({library(muscData); library(SingleCellExperiment)})
args <- commandArgs(trailingOnly = TRUE)
out <- if (length(args) >= 1) args[[1]] else "data/crowell.rds"
dir.create(dirname(out), showWarnings = FALSE, recursive = TRUE)

sce <- Crowell19_4vs4()
cat("class:", class(sce), "| dims (genes x cells):", nrow(sce), "x", ncol(sce), "\n")
cat("assays:", paste(assayNames(sce), collapse = ", "), "\n")
cat("colData columns:", paste(colnames(colData(sce)), collapse = ", "), "\n")
for (col in colnames(colData(sce))) {
  v <- colData(sce)[[col]]
  if (length(unique(v)) <= 12)
    cat(sprintf("  %s: %d unique -> %s\n", col, length(unique(v)),
                paste(head(unique(as.character(v)), 12), collapse = ", ")))
}
saveRDS(sce, out)
cat("saved:", out, "\n")
