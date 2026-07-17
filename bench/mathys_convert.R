#!/usr/bin/env Rscript
# Convert the Murphy-et-al reprocessed Mathys-2019 SingleCellExperiment (sce.qs, from
# AD Knowledge Portal syn51758062 / figshare) into language-neutral files sc-referee can ingest:
#   counts.mtx.gz   genes x cells raw counts (MatrixMarket)
#   var.csv         one row per gene  (gene_id + any rowData)
#   obs.csv         one row per cell  (ALL colData columns, verbatim)
#
# Deliberately schema-AGNOSTIC: it dumps every colData column so we can see the real
# donor / diagnosis / cell-type column names rather than guessing. Minimal deps.
#
#   Rscript bench/mathys_convert.R /path/to/sce.qs data/mathys_export [assay=counts]
#
suppressPackageStartupMessages({
  library(Matrix)
  library(SingleCellExperiment)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("usage: mathys_convert.R <sce.{qs,rds}> [out_dir=data/mathys_export] [assay=counts]")
}
in_path <- args[[1]]
out_dir <- if (length(args) >= 2) args[[2]] else "data/mathys_export"
assay_name <- if (length(args) >= 3) args[[3]] else "counts"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# Read the serialized object by extension: .rds -> base R (no extra deps); .qs -> the qs package.
cat("Reading", in_path, "...\n")
ext <- tolower(tools::file_ext(in_path))
if (ext == "rds") {
  sce <- readRDS(in_path)
} else if (ext == "qs") {
  if (!requireNamespace("qs", quietly = TRUE))
    stop("file is .qs but the 'qs' package is not installed; install qs or obtain the .rds/.h5ad form")
  sce <- qs::qread(in_path)
} else {
  stop(paste0("unsupported extension '", ext, "'; expected .rds or .qs (use anndata directly for .h5ad)"))
}
cat("class:", class(sce), "\n")
stopifnot(is(sce, "SummarizedExperiment"))

# Require the caller to identify a raw-count assay. Falling back to the first assay is unsafe: many
# SingleCellExperiment objects put logcounts or another transformed assay first.
an <- assayNames(sce)
cat("assays:", paste(an, collapse = ", "), "\n")
if (!(assay_name %in% an)) {
  stop(paste0("raw-count assay '", assay_name, "' is absent; available assays: ",
              paste(an, collapse = ", "),
              ". Pass the explicit raw-count assay as the third argument; transformed assays are refused."))
}
cat("using assay:", assay_name, "\n")
m <- assay(sce, assay_name)
m <- as(m, "CsparseMatrix")                     # genes x cells
if (!all(is.finite(m@x))) stop("raw-count assay contains non-finite values")
if (!all(m@x >= 0)) stop("raw-count assay contains negative values")
if (!all(m@x == floor(m@x))) stop("raw-count assay contains non-integer values")
cat("dims (genes x cells):", nrow(m), "x", ncol(m), "\n")

Matrix::writeMM(m, file = file.path(out_dir, "counts.mtx"))
system2("gzip", c("-f", shQuote(file.path(out_dir, "counts.mtx"))))
meta <- data.frame(
  assay = assay_name,
  n_genes = nrow(m),
  n_cells = ncol(m),
  counts_mtx_gz_md5 = unname(tools::md5sum(file.path(out_dir, "counts.mtx.gz"))),
  stringsAsFactors = FALSE
)
write.table(meta, file.path(out_dir, "counts.meta.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)

# var: gene ids + any rowData columns.
var <- data.frame(gene_id = rownames(sce), row.names = NULL, check.names = FALSE,
                  stringsAsFactors = FALSE)
rd <- as.data.frame(rowData(sce), check.names = FALSE, stringsAsFactors = FALSE)
if (ncol(rd) > 0) var <- cbind(var, rd)
write.csv(var, file.path(out_dir, "var.csv"), row.names = FALSE)

# obs: EVERY colData column, verbatim — this is what tells us the real schema.
obs <- as.data.frame(colData(sce), check.names = FALSE, stringsAsFactors = FALSE)
obs <- cbind(cell_id = colnames(sce), obs)
write.csv(obs, file.path(out_dir, "obs.csv"), row.names = FALSE)

cat("\ncolData columns (the schema we map from):\n")
cat(paste0("  - ", colnames(colData(sce))), sep = "\n")
cat("\nWrote:", out_dir, "/{counts.mtx.gz, counts.meta.tsv, var.csv, obs.csv}\n")
