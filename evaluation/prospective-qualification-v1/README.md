# Prospective qualification protocol v1

This evaluation-private protocol freezes a generic relation-envelope qualification study before
scientific labels or detector outcomes are available. It does not contain benchmark identities,
create independent cases, authenticate reviewers, qualify a detector, or authorize a Finding.

For every declared relation envelope, both the threshold-pilot and final held-out blocks contain
exactly one preassigned case in each required cell:

- error-bearing;
- corrected twin;
- valid alternative;
- hard negative;
- ambiguous;
- unsupported; and
- renamed implementation.

The protocol binds detector bytes, atomic relation bindings, opaque participants, distinct author
and reviewer contexts, authoring-brief digests, and fixed no-replacement assignments. The outcome
ledger must retain exactly one outcome for every assignment, including contamination, technical
failure, withdrawal, and disagreement with the intended cell. Public-benchmark and internal
development cases may be retained in a development block but are always metric-ineligible.

The three JSON Schemas describe the canonical protocol, block outcome ledger, and pilot threshold
decision. Semantic and chronological constraints that JSON Schema cannot express are enforced by
`sc_referee_evaluation.prospective_qualification` and the corresponding CLI commands.
