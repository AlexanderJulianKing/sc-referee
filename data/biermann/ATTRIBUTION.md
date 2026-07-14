# Biermann et al. 2022 — sc-referee demo capsule (GSE200218)

A small **derived aggregate** of the public GEO dataset **GSE200218** (Biermann et al. 2022,
treatment-naive human melanoma brain vs. extracranial metastases). This is **not** the raw data.

Contents:
- `patient_pseudobulk_counts.h5ad` — patient-level pseudobulk counts (27 patients), aggregated
  from the public single-cell counts. A de-identified aggregate; never the raw single-cell matrix.
- `results/original_table_s3_snrna.csv` — the study's originally reported tumor-cell differential
  expression family (Supplementary Table S3), used as the reported results sc-referee re-tests.
- `sc-referee.yaml` — the analysis contract (brain vs. peripheral metastasis; patient as the
  replicate unit).

- `original_analysis.R` — the differential-expression **step** of the original analysis (an
  excerpt: a Seurat `FindMarkers(..., test.use="MAST")` call that tests each cell as an
  independent observation). The full analysis + plotting lives in the authors' own repository;
  this excerpt is what sc-referee reads to recognize the inferential unit.

sc-referee's patient-level recompute collapses the reported family
**16,289 → 770 (95.3%)** and responsibly **withholds** a hard blocker because the corrected
patient-level analysis is underpowered — a later peer-reviewed reanalysis independently reports the
same cell-as-replicate error.

**Source:** GEO accession **GSE200218**. Please cite Biermann et al. 2022 and GSE200218. Public
data, redistributed here (as a de-identified aggregate + the published supplementary table) for
research and demonstration.
