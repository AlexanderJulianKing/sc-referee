# Example capability matrix

This example illustrates the public shape; it does not claim that these capabilities have been implemented.

| Domain | Language/package | Tested versions | Operation scope | Syntax | Operation extraction | Semantic modeling | Detector | Maturity and review basis | Strongest output | Known gaps |
|---|---|---|---|---|---|---|---|---|---|---|
| General statistics | Python / statsmodels | none yet | formula fit, coefficient table, confidence interval | planned | planned | draft | claim/result agreement | experimental / not qualified | ConditionalConcern | dynamic formula generation |
| Bulk RNA-seq | R / DESeq2 | planned: 1.40, 1.42 | `DESeqDataSetFromMatrix`, `DESeq`, `results` | planned | planned | draft | report contrast vs fitted contrast | experimental / not qualified | ConditionalConcern | dynamic contrasts, unsupported versions |
| Bulk RNA-seq | R / edgeR | none yet | `DGEList`, `filterByExpr`, `glmQLFit`, `glmQLFTest` | planned | planned | not started | tested-gene universe vs enrichment background | experimental / not qualified | Disclosure | custom wrappers |

A real entry is generated from versioned manifests and includes qualification references, exact abstention conditions, inferred compatibility, and applicable fixture evidence. The matrix never converts one validated detector into a domain-wide “supported” claim.
