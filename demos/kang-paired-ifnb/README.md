# Kang et al. 2018 — paired IFN-β response

**Status:** runnable published-human-data calibration anchor after one local build step.

Eight patients each contribute control and IFN-β-stimulated PBMCs. A per-cell Wilcoxon analysis
claims thousands of genes; Referee recomputes the contrast with donors as the paired independent
units. Unlike Biermann, the biology is deliberately strong: many effects should survive. The value
of the example is calibration—Referee neither rubber-stamps all cell-level calls nor declares the
real IFN-β response false.

```bash
# data/kang.h5ad is already present in this workspace. For a fresh clone, use the URL documented
# in bench/kang_anchor.py first.
.venv/bin/python demos/kang-paired-ifnb/build_demo.py
.venv/bin/referee demos/kang-paired-ifnb
```

The builder hard-links the local H5AD when possible and regenerates the reported per-cell table. It
does not duplicate or modify the source dataset.

Source: Kang et al. 2018, GEO GSE96583; public scverse example-data conversion.

