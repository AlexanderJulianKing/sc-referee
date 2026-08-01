# Experiment 0030: Biermann parity baseline and freeze

- **Status:** Disclosure-only parity slice reproduced and replayed; broader bounded parity closed by Experiment 0031
- **Date:** 2026-08-01
- **Project execution:** Disabled in the production audit
- **Finding authority:** None
- **Governing decision:** ADR-0045

## Local source capsule

The authorized local source is
`/Users/alexanderking/Desktop/random_stuff/sc-referee-public/data/biermann`. Repository text is
evidence only. The source capsule contains:

| Path | SHA-256 | Role |
|---|---|---|
| `patient_pseudobulk_counts.h5ad` | `03a7b88b1851f3ded111a5d7de28c85ccd5ba302cb57adcd73a08ee813a42e7e` | 27-by-35,650 patient aggregate |
| `results/original_table_s3_snrna.csv` | `c967f3ddb76f90924ccf24a8dac5e057a15cac33e03d932dbd8a5a59445b889d` | 35,650-row reported family |
| `sc-referee.yaml` | `e92780463d0da4c33dbed6ad5b286858a80ce8e5a7b98c83b6ee99d2d7ee1422` | repository-declared contract candidate |
| `original_analysis.R` | `51138aa100d2ff81997efb3b2c0fef6cff031b5bdd9d0093aa4a12e1b913e5ec` | static reported-method evidence |
| `ATTRIBUTION.md` | `9458b46d18725286a22943161d8cb48d6a5e47436a9e2c943cbfc705e27b3a8a` | provenance and result narrative candidate |

The H5AD has dense `X` shape 27-by-35,650; observation fields `cell_id`, `organ`, and `patient`;
and one 35,650-element feature index. The reported CSV columns are `p_val`, `avg_log2FC`, `pct.1`,
`pct.2`, `p_val_adj`, `gene`, and `diffexpressed`.

## Public-release parity target

The old public implementation's frozen target is:

- 16,289 testable reported significant genes;
- 770 patient-level survivors, with a documented platform tolerance of one;
- survival rate approximately 0.0473, or a 95.3% collapse;
- powered fraction 0.3817; and
- an underpowered/needs-evidence disposition rather than its strongest blocker.

These values are a compatibility target for the auditor-owned calculation, not independent proof
that the original paper is wrong. The original report-to-code execution link and the scientific
authority of the repository YAML remain unestablished.

## Pre-implementation baseline

The schema-v0.18 `scientific-audit` skill was run over an exact staged copy in standard mode. The
auditor opened regular files only for tiered identity, executed no project code, made zero model
calls, and produced an integrity-verified `partial_evidence_unavailable` audit with:

- zero Findings;
- zero ConditionalConcerns;
- one MaterialQuestion asking which candidate is the final publication surface; and
- one Disclosure explaining the coverage limitation.

The result table received only a weak fingerprint because the H5AD and table together exceed the
generic five-megabyte exact-read budget. No H5AD structure, unit-of-analysis contract, reported
family, or patient-level comparison entered the semantic lock. This is the exact negative baseline
the parity implementation must improve without broadening unselected large-file reads.

## Implemented parity slice

The accepted ADR-0045 boundary now provides:

- a separate 16 MiB exact-read budget for at most eight caller-selected material inputs;
- a bounded non-executing dense-H5AD inventory that is active only for selected material paths;
- an immutable calculation context that exposes only exactly digested selected artifacts;
- a closed `sc-referee-single-cell-sensitivity-v1` declaration with explicit paths, columns,
  H5AD axes, contrast, one-factor model, unit, producer/dependence status, alpha, reference effect,
  target power, and minimum powered fraction; and
- a lazy one-CPU PyDESeq2 negative-binomial Wald engine in the optional
  `single-cell-recompute` dependency extra.

The exact capsule was audited through the ordinary controller with `BIERMANN_AUDIT.md` as an
evaluator-owned selected surface. No repository-authored code was executed. The integrity-verified
bundle records:

| Metric | Observed |
|---|---:|
| Reported family rows | 35,650 |
| Reported significant, matched, and testable | 16,289 |
| Replicate-level survivors | 770 |
| Survival rate | 0.047271164589600345 |
| Powered fraction | 0.38166861071889 |
| Reference/test replicate rows | 10 / 17 |
| Recompute engine | PyDESeq2 0.5.4 |

This exactly reproduces the frozen public target. The audit emitted one non-accusatory Disclosure,
zero Findings, zero ConditionalConcerns, zero model calls, and no model access after semantic lock.
It explicitly records that the recomputation is underpowered, the report producer is unresolved,
and the original covariance behavior was not established. Model-free replay reproduced the exact
`DeterministicCheckObservation` and semantic-lock digest.

The prior public demo environment was also rerun twice. It failed before auditing because its
SciPy import timed out while reading the installed module. That environmental failure was not used
as scientific evidence or as an implementation template.

## Frozen controls

Before any Finding-capable detector is considered, the following roles are frozen:

1. the exact Biermann compatibility case;
2. a corrected or covered comparison using the same input family;
3. a patient-level-reported hard negative;
4. an unresolved replicate/dependence case;
5. one mutation for every finite identity, shape, column, and contract check;
6. an over-budget H5AD/table case; and
7. independent removal tests for material-input selection, H5AD adapter, table adapter, calculation
   module, and any later detector.

The current automated family covers a reported-observation-level discrepancy, an all-survive
corrected twin, a biological-replicate hard negative, an unresolved-unit abstention, a missing-
column mutation, unselected and unsupported H5AD layouts, duplicate feature IDs, exact-material
selection, and calculation-module removal. Snapshot tests separately cover missing and over-budget
material paths. The exact Biermann run supplies the natural positive and replay control.

Still pending before any qualification proposal are a scientist-answer round trip for the
unresolved-unit case, additional identity/shape mutations, a live-workspace drift control for the
new module, and independent natural-workflow evidence outside this capsule.

## Current limitations

The old reference rerun is an authorized evaluation activity outside the production auditor. It
does not permit the new production path to execute `original_analysis.R` or import the old engine.
Natural workflows, sparse H5AD layouts, alternate DE tools, additional covariates, paired designs,
and very large matrices remain outside this first control family.
