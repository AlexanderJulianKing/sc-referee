# ADR-0045: Add an authorized material-input boundary for single-cell parity

- **Status:** Accepted under the owner's standing parity authorization on 2026-08-01
- **Date:** 2026-08-01
- **Coordinated schema release:** None initially; reuse schema `0.18.0`
- **Related decisions:** ADR-0017, ADR-0020, ADR-0042, and ADR-0044
- **Finding impact:** None; initial single-cell modules are question/Disclosure-only
- **Execution impact:** Auditor-owned bounded readers and calculations only; project-authored code
  remains unexecuted

## Context

The current public sc-referee release has a useful single-cell vertical that the overhaul does not
yet reproduce. Its compact Biermann capsule contains a 27-by-35,650 patient-level H5AD, the
35,650-row reported differential-expression family, one R excerpt, and a repository-declared
analysis contract. The public implementation reports 16,289 testable reported discoveries and
approximately 770 patient-level survivors, while withholding its strongest adverse verdict because
the corrected analysis is underpowered.

A schema-v0.18 baseline audit of the exact local capsule is integrity-verified but emits no
scientific observation. It asks which Markdown file is the publication surface, inventories only
the R syntax, and weakly fingerprints the 2.6 MB result table after the generic five-megabyte full-
digest budget is consumed. It cannot bind the selected scientific surface, H5AD, result family,
unit-of-analysis contract, and calculation into one target.

Simply porting the public engine would violate the overhaul's architecture. Repository YAML cannot
authenticate its own `confirmed_by_human` assertion, a project R script cannot be executed to prove
what ran, and large single-cell matrices cannot become mandatory full-recomputation inputs.

## Decision

Add a bounded, explicit material-input boundary and implement single-cell parity as modular
evidence layers:

1. The caller may identify exact repository-relative material inputs before snapshot capture.
   These paths receive a separate finite full-digest budget and are recorded as caller-selected,
   not scientifically validated.
2. The selected publication surface remains separately explicit. Selecting a file does not accept
   its scientific claims or the repository's assertions of human confirmation.
3. A non-executing H5AD adapter may inspect only allowlisted structural fields and bounded matrix
   bytes through an auditor-owned library. It records exact shapes, axes, observation columns,
   matrix kind, integer/nonnegative checks, and finite ceilings. It never imports the audited
   project or interprets arbitrary HDF5 objects.
4. A result-table adapter binds exact identifier, adjusted-p-value, effect, and call columns under
   finite row/column/byte ceilings. Ambiguous bindings abstain.
5. Unit-of-analysis, biological-replicate, contrast, dependence, and reported-producer semantics
   remain scientist-governed. Repository declarations may populate question candidates but cannot
   answer those questions.
6. Auditor-owned sensitivity calculations use ADR-0044's content-addressed calculation registry and
   typed `DeterministicCheckObservation`. They cannot branch the controller or emit assessments
   directly.
7. Full recomputation is optional. A compact input within the declared ceiling may be recomputed;
   a large, missing, externally computed, or over-budget input remains an explicit unknown or may
   use separately identified external evidence. No ordinary audit must process a full million-cell
   matrix.
8. The initial Biermann result is capped at Disclosure and may state only the exact observed
   reported-versus-patient-level discrepancy and its power limitation. It cannot prove that the R
   excerpt ran, that it generated the supplied table, that the paper is invalid, or that the same
   result generalizes to another workflow.

The implementation must keep data adapters, scientific-contract questions, calculation modules,
and any later detector separate. New input layouts or checks register independently.

## Initial limits

- At most eight explicitly selected material inputs.
- At most 16 MiB of additional exact material-input reads in one audit.
- H5AD support initially covers a single dense integer `X`, string/categorical observation fields,
  and a unique feature index. Sparse matrices, layers, raw slots, backed remote arrays, arbitrary
  encodings, and multi-file assembly abstain until separately controlled.
- The initial result-family profile covers one explicit CSV contract and no column guessing.
- The first numerical parity target is the compact local Biermann aggregate, not the original
  145,555-cell matrix.

## Acceptance criteria

- Freeze exact Biermann input digests, the public-release reference metrics, and positive,
  corrected/covered, ambiguous, hard-negative, removal, mutation, and over-budget roles before the
  production module is finalized.
- Prove that caller-selected material paths are fully identified without increasing generic reads
  for unselected large files.
- Reproduce the compact Biermann reference discrepancy within its documented platform tolerance.
- Run the ordinary `scientific-audit` skill path and replay with no project execution, no model
  calls after lock, and zero production Findings.
- Removing each new adapter or check removes only its own records and coverage.
- Preserve the pre-parity audit as the negative baseline.

## Remaining limitation

This decision targets practical parity for one flagship single-cell failure family. It does not
establish representative recognition rates, general H5AD compatibility, single-cell correctness,
or parity with every public-release check. Confounding, pairing, count-model, effect-size,
pseudobulk-integrity, and circular-inference parity remain separate subsequent modules.
