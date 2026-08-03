# ScienceAgentBench verified task 70

## Task

Train a VAE model on the given data and perform a 1-vs-all differential expression test for each
cell type. Extract top markers for each cell type using the results. Visualize them as a dotplot
with the cell types organized using a dendrogram. Save the figure to
`pred_results/hca_cell_type_de.png`.

## Author-visible domain knowledge

For single-cell RNA data, account for the contribution of mitochondrial and ribosomal genes in
the data. These quantities can indicate data-collection quality. Separate the effects of cell type
from effects of the donor's expression profile. With SCVI this can be done using
`categorical_covariate_keys` or `continuous_covariate_keys`.

Preprocess the data rather than skipping quality control. Filter invalid or low-quality cells and
filter genes to reduce dimensionality. Choose and document a minimum number of samples in which a
gene must be observed. Some SCVI and Scanpy analyses and visualizations expect normalized and
log-transformed data.

## Available input

```text
hca/
  hca_subsampled_20k.h5ad
```

The input is an H5AD single-cell heart-atlas subset. The benchmark preview shows a cell-by-gene
matrix. The task's gold program, evaluator, expected image, and prior solutions are deliberately
not available in the author workspace.

## Deliverable for this recurrence experiment

Create a small reviewable repository containing:

- `analysis.py`, implementing the requested workflow against `hca/hca_subsampled_20k.h5ad`;
- `REPORT.md`, stating the scientific question, preprocessing, covariates, differential-expression
  comparison, and output path; and
- `requirements.txt`, listing necessary third-party packages.

Do not execute the analysis. Do not use sc-referee while authoring. Do not consult external
solutions or benchmark answer-side material.

## Provenance and ceiling

The task text is adapted from the ScienceAgentBench verified split at dataset revision
`9c6e96c9e74572e979b0930ee735041cef528cb7` under CC BY 4.0. This retained packet is public,
benchmark-derived, answer-side excluded, and ineligible for detector qualification or promotion.
