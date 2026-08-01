# Practical parity matrix

This matrix compares useful behavior, not internal compatibility with the public repository. “Full”
means the behavior is available through the overhaul's stricter evidence boundary. “Partial” means a
useful bounded subset exists and the missing scope is named. A Disclosure is not a Finding or a global
pass.

| Public feature family | Overhaul status | Current evidence and limit |
|---|---|---|
| Cells treated as replicates | Full for the compact declared profile | Biermann was independently recomputed at replicate level: 770 of 16,289 discoveries survived; underpowering and unresolved producer/dependence semantics remain explicit. |
| Benjamini–Hochberg multiplicity | Full for a declared complete family | Exact-decimal recomputation over bounded CSV/TSV; incomplete families ask or abstain. |
| Effect-size relevance | Full for a declared log2-fold-change family | Exact table summary against the report's declared relevance floor; significance-only claims are not applicable. |
| Treatment/batch confounding | Full for declared categorical main effects | Exact column-space aliasing is calculated from a bounded metadata table; continuous covariates, interactions, and arbitrary formulas abstain. |
| Latent contamination adjustment | Full when the variable is explicitly required | Exact required-versus-fitted adjustment presence is checked; discovering or deciding that a latent variable is a confounder remains intentionally outside the module. |
| Pairing | Full for a declared two-arm metadata profile | Complete and incomplete pairing levels are counted and compared with the exact paired/unpaired binding; arbitrary repeated-measures models abstain. |
| Pseudobulk construction integrity | Full for a declared aggregation key | Groups containing both contrast arms and rows with missing grouping identities are counted exactly; assay-layer dataflow remains unsupported. |
| Count-model compatibility | Full for the initial namespaced R registry | One exact DESeq2, edgeR, limma, or stats producer call is compared with the declared response scale and required family; arbitrary wrappers and dataflow abstain. |
| Circular selection and testing | Full for the initial Scanpy shape | Unique neighbors, Leiden, and calibrated marker-test calls are checked for same-object reuse; arbitrary aliases, wrappers, Seurat, and safeguard verification abstain. |
| eQTL orientation and support | Full for the public unadjusted donor-OLS profile | Exact allele orientation, donor/genotype support, and reported-versus-recomputed sign are checked; adjusted, mixed, nonlinear, and count-likelihood eQTL models abstain. |
| Hi-C estimator fidelity | Full for the public arithmetic-background profile | The reported delta is independently recomputed from exact dense contacts and bins under the fixed resolution, mask, target-exclusion, zero, replicate, and tolerance rules; other estimators abstain. |

Cross-cutting architecture, schema validation, immutable snapshots, semantic lock, no-post-lock model
access, storage integrity, and deterministic replay exceed the public implementation's guarantees.
That architectural superiority does not convert partial scientific feature rows into full coverage.
