# ADR-0046: Recover practical parity as bounded modular observations

- **Status:** Accepted under the standing authorization for non-material ADRs
- **Date:** 2026-07-31
- **Schema impact:** None; schema remains `0.18.0`
- **Finding impact:** None; the initial parity modules are Disclosure-only

## Context

The public implementation advertises useful checks for experimental unit, multiple testing,
effect-size relevance, confounding, contamination adjustment, pairing, pseudobulk construction,
count-model compatibility, circular analysis, eQTL support, and Hi-C estimator fidelity. The
overhaul already has stronger evidence, locking, replay, question, and epistemic boundaries, but it
does not yet expose every useful public check through those boundaries.

Copying the old controller would also copy its weaker assumptions. Conversely, treating one
successful Biermann calculation as broad parity would overstate coverage.

## Decision

Recover practical parity as independently removable deterministic modules. Each module must:

1. recognize one closed, versioned declaration rather than infer scientific intent from arbitrary
   prose;
2. bind every evaluated table or metadata surface through an explicitly selected, fully digested
   material input;
3. apply finite byte, row, column, and vocabulary ceilings;
4. retain exact typed operands, source spans, completeness receipts, and limitations;
5. treat unresolved claim semantics, producer identity, model identity, missing values, and
   unsupported shapes as unknown rather than adverse evidence;
6. execute no project-authored code and make no model calls;
7. remain Disclosure-only until separately qualified for Finding authority; and
8. have positive, corrected, hard-negative, ambiguity, mutation, and module-removal controls.

The first module summarizes a complete reported discovery family against an explicitly declared
effect-size relevance floor. It is not applicable when the report claims statistical significance
only. A conventional display threshold cannot silently become a scientific requirement.

The next module evaluates exact tabular design structure: required categorical adjustment presence,
perfect treatment/adjustment aliasing, pairing availability versus the bound comparison mode,
aggregation groups that merge contrast arms, and missing grouping identities. It consumes a compact
metadata table rather than requiring a full single-cell matrix, so large workflows can provide a
bounded audit surface without rerunning or loading the assay.

## Consequences

- Practical parity is measured feature by feature, with coverage and authority reported separately.
- A public feature may be recovered at a more conservative output ceiling than the old release.
- Large datasets can be audited through small, exact metadata and result surfaces.
- Arbitrary formulas, continuous-covariate rank tests, hidden producer lineage, dynamic selection
  semantics, and unselected large matrices remain unsupported until their own contracts exist.

## Acceptance criteria

- Removing a module removes only its observations.
- A corrected twin is conformant and a scientific hard negative is not applicable.
- Missing or unresolved premises never create a nonconformant observation.
- Every nonconformant result has complete finite counterevidence checks and zero Findings.
- Audit and replay preserve the exact observation projection.
