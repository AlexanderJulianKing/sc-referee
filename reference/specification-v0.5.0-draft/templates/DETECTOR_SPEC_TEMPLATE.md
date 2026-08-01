# Detector specification: `<detector_id>`

## Metadata

| Field | Value |
|---|---|
| Version | |
| Issue class | |
| Domain profile | |
| Maturity | `experimental` |
| Evidence ceiling | `review_only` |
| Owners | |

## Scientific concern

State the concern in scientific terms. Describe why it can affect interpretation, not only which package call is involved.

## Target and applicability

- Target record types:
- Recognized operations and versions:
- Required Scientific Contract dimensions:
- Required trust dimensions:
- Explicit non-applicability conditions:

## Premises

| Premise ID | Description | Required authority | Material? |
|---|---|---|---:|
| P-1 | | | yes |

## Detection logic

Describe the deterministic logic, including graph queries, comparisons, tolerances, and package-specific mappings. Pseudocode is encouraged.

## Counterevidence search

List all evidence sources that must be searched before admission and the rule for downgrading or suppressing the candidate.

## Result states

Explain the precise conditions for:

- finding candidate;
- no issue detected within coverage;
- not applicable;
- insufficient semantics;
- unsupported path;
- execution evidence unavailable; and
- detector error.

## Finding language

Provide approved templates for every evidence class the detector may emit. Include conditional wording and prohibited overstatements.

## Root-cause and descendants

Define the canonical causal node and how affected models, artifacts, and claims are discovered.

## Coverage limitations

Document known unsupported constructs, package versions, domains, and data conditions.

## Fixtures

| Fixture | Class | Expected state | Purpose |
|---|---|---|---|
| | positive | | |
| | negative | | |
| | ambiguous | | |
| | unsupported | | |

## Qualification evidence

Record benchmark sets, precision, false-accusation rate, confidence intervals, reviewer agreement, runtime, and known failure modes before maturity promotion.
