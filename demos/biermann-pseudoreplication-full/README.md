# Biermann et al. — full public-data reproducibility proof

**Status:** full-provenance build; downloads approximately 1.2 GB and materializes a large sparse
AnnData file locally.

This is the credibility counterpart to the instant
[`biermann-pseudoreplication`](../biermann-pseudoreplication/) demo. It starts from the authors'
official GSE200218 processed count matrix and cell metadata, reconstructs the same single-nucleus
tumor-cell population reviewed by their published code, and runs Referee on those **82,783 cells**.
Referee itself aggregates those cells into the 27 biological samples before its PyDESeq2
recomputation.

The raw sequencing reads are privacy-restricted in dbGaP. This proof begins at the public processed
count matrix, which is the input needed to audit the paper's differential-expression inference. It
does not claim to validate alignment or upstream read processing.

## Build and run

From the repository root:

```bash
.venv/bin/python demos/biermann-pseudoreplication-full/build_full.py
.venv/bin/sc-referee audit demos/biermann-pseudoreplication-full \
  --json demos/biermann-pseudoreplication-full/full-audit.json
```

For the browser presentation used in the interactive demo, the second command can instead be
`.venv/bin/referee demos/biermann-pseudoreplication-full`.

The first command:

1. downloads the official GEO count matrix, gene names, and metadata;
2. records SHA-256 digests for every source artifact;
3. selects `sequencing == "Single nuclei"` and `cell_type_main == "Tumor cells"`, matching the
   authors' published analysis code;
4. preserves the selected cell-by-gene matrix as sparse counts;
5. reconciles the two duplicated gene labels in the GEO gene-name file by summing their columns;
6. verifies that aggregating this full matrix exactly reproduces the committed 27-patient demo
   capsule; and
7. writes `provenance.json` with dimensions, filters, digests, and the equality result.

Expected audit result: **16,289 published cell-level discoveries → 770 patient-level survivors**
(**95.3% lose significance**). Referee still withholds a hard blocker because the corrected analysis
is underpowered.

Downloaded and generated large files are intentionally gitignored. The compact demo is committed so
reviewers can reproduce the statistical result immediately; this folder proves where that compact
artifact came from and that the production ingestion/reduction path accepts the full public matrix.
The checked-in [`VERIFIED_RUN.json`](VERIFIED_RUN.json) freezes the source digest, full-matrix
dimensions, exact compact-capsule equality, generated H5AD digest, and measured audit result from the
successful end-to-end run on 2026-07-12.

Official source: [NCBI GEO GSE200218](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE200218).
