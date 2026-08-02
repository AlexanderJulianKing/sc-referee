# Experiment 0043: Portable calculation-layout adapters

- **Status:** Completed locally
- **Date:** 2026-08-02
- **Decision:** Accepted ADR-0052 under the owner's standing authorization
- **Schema:** Unchanged at `0.18.0`
- **Backlog item:** L09

## Question

Can all eight bounded calculation families operate outside their original report capsules without
duplicating calculation logic, inferring scientific premises from filenames, or increasing their
authority?

## Design

Each family now exposes one normalized internal contract consumed by its existing evaluator. The
original report adapter and a new selected-sidecar adapter independently normalize into that same
contract. The second layout is a strict YAML document with:

- the exact root marker `sc_referee_calculation_contracts: 1`;
- a bounded list of unique calculation-check IDs and mapping-valued contracts;
- no semantic filename requirement; and
- an existing exact scientist-selected material-input scope path.

The shared parser accepts at most 256 KiB and 32 contracts, uses safe YAML loading, requires exact
keys, and ignores unmarked YAML. Every family retains its own closed scientific vocabulary and
input ceilings. If report and sidecar adapters both produce an observation, the existing registry
marks the module as failed because two evidence layouts compete.

## Result

All eight calculation families now have two content-addressed layout adapters:

1. complete-family Benjamini–Hochberg conformance;
2. replicate-level single-cell sensitivity;
3. effect-size relevance;
4. tabular design integrity;
5. R method/response-scale compatibility;
6. Scanpy selection/test reuse;
7. donor-level eQTL sign; and
8. Hi-C loop strength.

The embedded-report adapters and sidecar adapters call the same per-family `inspect_normalized`
path. Cross-layout tests retain the expected operands and outcomes. The BH control additionally
uses a different directory tree, TSV layout, column order, extra column, and identifier-column
name; exact raw and recomputed arrays remain equal to the original CSV capsule.

## Acceptance evidence

The added or extended tests cover:

- one selected-sidecar positive for every family;
- BH cross-adapter operand equivalence and semantic-lock replay;
- alternate safe BH paths, identifiers, delimiter, column order, and extra columns;
- simultaneous embedded and sidecar declarations failing closed;
- an unselected sidecar contributing no authority;
- duplicate sidecar check IDs and an over-budget marked sidecar producing no observation;
- duplicate table identifiers and `NA` remaining unsupported without numerical accusation; and
- all pre-existing family positives, corrected twins, hard negatives, ambiguity, unsupported,
  removal, no-execution, and replay controls.

Calculation-manifest v10 freezes the generalized registry. Earlier family manifest files are
resynchronized with their behavior-preserving source refactors. Public observation schema,
comparison relations, output ceilings, and `production_finding_permitted: false` are unchanged.
The completed checkpoint passes 1,370 tests and retains 121 regression cases across 12 sources;
all 26 active module baselines remain complete and qualification use remains forbidden.

## Remaining limitation

Portability is not automatic scientific interpretation. A selected sidecar is a scoped declaration,
not proof that its premises are true or that the declared workflow executed. Unsupported table
formats, hidden preprocessing, dynamic producer lineage, implicit units, unknown thresholds,
unselected inputs, and calculations outside the eight closed families continue to abstain.
