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
  this excerpt is what sc-referee reads to recognize the inferential unit. The source code is
  Copyright © 2021 Izar Lab and used under the MIT License reproduced below.

sc-referee's patient-level recompute collapses the reported family
**16,289 → 770 (95.3%)** and responsibly **withholds** a hard blocker because the corrected
patient-level analysis is underpowered — a later peer-reviewed reanalysis independently reports the
same cell-as-replicate error.

**Source:** GEO accession **GSE200218**. Please cite Biermann et al. 2022 and GSE200218. Public
data, redistributed here (as a de-identified aggregate + the published supplementary table) for
research and demonstration.

**Original analysis repository:** https://github.com/IzarLab/Melanoma_Brain_Metastasis

## License for the original analysis-code excerpt

MIT License

Copyright (c) 2021 Izar Lab

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
