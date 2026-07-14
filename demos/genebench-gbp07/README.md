# GB-P07 — latent ambient-RNA contamination (CXCL10 eQTL)

A runnable demonstration of sc-referee reviewing a *compiled* analysis: a donor-level eQTL for
`CXCL10 ~ genotype`, on the public **GeneBench-Pro GB-P07** benchmark. sc-referee independently flags that
the ratified ambient-RNA contamination basis is absent from the submitted fitted design.

## Data (not redistributed)

The benchmark's released bytes are **not** committed to this repository (see `ATTRIBUTION.md`). Supply your
own copy of `GB-P07-data.zip` and materialize the analysis inputs once, locally:

```bash
GBP07_ZIP="/path/to/GB-P07-data.zip" python -c \
  "from sc_referee.derivations.gbp07_capsule import prepare_gbp07_capsule; prepare_gbp07_capsule('demos/genebench-gbp07')"
```

This writes the compiler inputs into the gitignored `raw_compile_input/` and verifies them against the
provenance digests recorded in `sc-referee-capsule.yaml`. If the bytes are missing or altered, sc-referee
abstains honestly rather than auditing the wrong data.

## Review it

Then review the folder like any other analysis — through the browser or the CLI:

```bash
referee demos/genebench-gbp07
# or:  referee  ->  Choose analysis folder  ->  demos/genebench-gbp07
```

sc-referee reconstructs the eQTL design, asks the scientific premises it needs to evaluate ambient-RNA
confounding, and reports three findings:

- **contamination confound — flagged:** the ratified contamination basis is absent from the fitted design;
- **allele orientation — needs review:** genotype coding / effect-allele orientation is not established
  from the supplied inputs;
- **eQTL design support — clear.**

## Scientific boundary

This is a **structural-containment** result. It establishes only that the confirmed contamination basis is
absent from the fitted design; it does **not** establish how that omission affected the reported
coefficient, and it makes no causal claim.
