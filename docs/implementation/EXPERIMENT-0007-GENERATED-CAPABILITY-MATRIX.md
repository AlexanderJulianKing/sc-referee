# Experiment 0007: Fail-closed generated capability matrix

- **Status:** Active local implementation profile; not a detector-qualification claim
- **Date:** 2026-07-28
- **Authority:** Specification ADR-0040, SA-FR-100, SA-FR-103, AC-60, and accepted public schema v0.12.0
- **Scope:** Deterministic projection of one closed release-manifest set into one public `CapabilityMatrix`

## Purpose

Implement the already-specified capability matrix without turning implementation presence, parser
support, development fixtures, or inferred compatibility into a public detector or domain claim.

## Exact source profile

The generator consumes a closed, canonical manifest set containing exactly five independently
digested collections:

- public `ParserManifest` records;
- private semantic-profile manifests that join exact parser and detector references to one narrow
  language/package/operation envelope;
- public `DetectorManifest` records;
- public `DetectorQualification` records; and
- private version manifests that keep tested versions distinct from inferred compatibility.

The set manifest binds the collection paths and byte digests, release version, and generation
timestamp. Every public source record is validated against schema v0.12.0. All references must
resolve exactly, IDs must be unique, and collection bytes must be canonical JSON. The generated
matrix records the set and collection digests in `x-` extensions and is itself canonical and
schema-valid.

## Conservative projection rules

- Parser `supported_versions` never become matrix `tested_versions`.
- Tested versions and inferred compatibility come only from the applicable version manifest and
  remain separate arrays.
- A profile with no detector references emits an empty detector list plus explicit known-gap and
  abstention text. It cannot imply that a scientific issue was checked.
- Experimental detectors are always `not_qualified`, have no qualification reference, and cannot
  expose `finding` as their strongest output.
- A validated or publication-grade entry requires an exact promoted qualification with matching
  detector identity, version, effective maturity, review basis, and qualification reference. Any
  mismatch fails closed.
- Known gaps and abstention conditions are the sorted union of the profile, parser, version, and
  detector declarations. Empty information is not replaced with guessed support.
- Every entry and the matrix set both retain `domain_wide_*_claim_allowed:false`.

The bundled v1 manifest set initially contained no detector or qualification records. Experiments
0009 and 0010 added narrow delimited-header and default Nextflow-trace component profiles;
Experiment 0011 and accepted ADR-0018 now add two exact cross-profile detector manifests. Both
remain experimental, unqualified, and Finding-ineligible. Synthetic walking-skeleton detector
test doubles remain excluded.

## Safety boundaries

- The generator imports or executes no project-authored code and makes no model calls.
- The matrix does not establish scientific validity, parser completeness, detector qualification,
  package compatibility, or a correctness conclusion.
- Source implementation digests are published for traceability, but source presence alone does
  not increase a capability state.
- Private profile and version manifests are generator inputs, not new public record types; their
  full digests are retained in the public matrix extension.

## Exit evidence

- deterministic generation from the same manifest set is byte-identical;
- source digest, canonicalization, duplicate ID, unresolved reference, and qualification-envelope
  mutations fail closed;
- parser supported versions cannot leak into tested or inferred versions;
- the default five-profile matrix has only one experimental unqualified detector and no
  domain-wide claim; and
- generation and validation pass from an isolated production wheel.
