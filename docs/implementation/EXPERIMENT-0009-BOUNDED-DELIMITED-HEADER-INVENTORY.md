# Experiment 0009: Bounded delimited-table header inventory

- **Status:** Active local implementation profile; not row or scientific-semantic inspection
- **Date:** 2026-07-29
- **Authority:** SA-FR-013, SA-FR-016, SA-FR-029, SA-FR-050, specification sections 3.8, 4.5, and 6.11, and accepted implementation ADR-0017
- **Scope:** Exact header inventory for fully captured repository CSV and TSV files

## Purpose

Expose a useful, domain-neutral summary of existing tabular inputs and outputs without executing
project code, reading an enormous table body outside the snapshot budget, inferring values from
samples, or assigning scientific meaning from column names.

## Exact profile

The inspector considers inventoried regular files with a case-insensitive `.csv` or `.tsv` suffix.
It operates only on a complete immutable payload already admitted under `full_digest` identity and
rehashes that materialized payload before inspection. A weak, manifest, unidentified, missing,
changed, symlinked, or otherwise nonmaterialized table remains structurally unavailable.

The active Python standard-library `csv` reader parses only the first logical record, using comma
for CSV and tab for TSV. Strict UTF-8 is required. A header is admitted only when every name is
nonempty and unique. At most 1,024 variables are emitted. Decode errors, parse errors, missing or
duplicate names, over-limit headers, and ambiguous existing Artifact linkage fail locally and are
retained as partial, opaque, unavailable, or uninspected coverage as applicable.

An unlinked valid table receives an Artifact whose role remains unknown. When exactly one existing
static Artifact resolves to the same path, its observed producer and consumer edges may classify
the DataAsset as input, intermediate, or output. Those static edges do not establish that the
project ran or used the snapshotted bytes.

## Evidence meaning

An emitted Variable establishes only the exact header string. Its storage type is `unknown`, its
scientific meaning is unresolved, and it has no observed-level count. Row shape, row count, cells,
types, missingness, units, scales, roles, statistical meaning, and result correctness remain
unknown. Row values are not copied into the DataAsset or Variable records.

The DataAsset is therefore `partial`, even when the complete file was safely captured. Malformed
tables may emit an `opaque` or `unavailable` DataAsset with no Variables. These states are coverage
evidence, not Findings.

## Exit evidence

- an existing CSV output with an exact static writer edge is recorded as an output DataAsset while
  project code remains unexecuted;
- exact column names replay, while values, storage types, scientific meanings, and row counts do
  not appear in the promoted records;
- unlinked tables retain unknown role;
- duplicate headers become opaque and over-budget tables remain structurally unavailable;
- all emitted Artifact, AssetIdentity, DataAsset, and Variable records validate under public
  schema v0.14.0; and
- the generated capability matrix discloses only this header-level envelope, no detector, no
  tested-version claim, and no domain-wide validation.
