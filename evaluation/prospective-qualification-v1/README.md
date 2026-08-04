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

`scripts/build_prospective_study_scaffold.py` compiles the coordinator template and the separately
self-digested benchmark-blind authoring template into a write-once role-separated assignment
package. It requires explicit detector, participant, context, deadline, and timestamp inputs. The
generated author queues omit block roles, relation ordinals, check and candidate identifiers,
binding digests, detector mechanics, expected answers, labels, and outcomes. The coordinator keeps
the content-addressed relation map needed to bind each blind premise back to the frozen protocol.

The scaffold contains assignments and instructions only. It does not contain authored cases,
authenticate participants, open held-out material, create scientific labels, calculate metrics, or
grant qualification or Finding authority.

`scripts/build_prospective_method_contract_inputs.py` consumes only the frozen coordinator
protocol, relation-binding map, and authoring briefs. For one named block it emits 70 create-once
coordinator project shells containing a read-only `TASK.md` and the exact four-field
`scientific_check_requirement_v1` profile selected by the scientist. The held-out block is refused
unless the coordinator supplies the explicit `--allow-heldout` gate. The builder creates no case
implementation, report, label, detector observation, or method-contract lock, and does not execute
project-authored code.
