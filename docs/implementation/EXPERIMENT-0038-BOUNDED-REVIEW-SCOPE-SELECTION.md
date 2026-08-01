# Experiment 0038: Bounded review-scope selection

## Question

Can a scientist select the exact report, analysis source, material input, and analysis output for an
ordinary static audit through bounded typed interaction, while stale or unsafe choices fail closed
and all unrelated unknowns survive append-only linked segments?

## Scope

This experiment completes post-MPP backlog item L04 under accepted ADR-0047. It adds a closed
`bounded-review-scope-selection-v1` interaction profile and internal semantic-lock projection. It
changes no public schema, detector authority, Finding-admission rule, scientific-check output
ceiling, model privilege, or project-execution privilege.

Selectable candidates come only from existing FileRecord, Artifact, ParserResult, and full-digest
AssetIdentity evidence in the immutable repository snapshot. Symlinks, unsafe paths, weak
identities, unsnapshotted outputs, missing records, and candidate sets above the finite limit are
not silently selectable. Zero candidates remain unavailable, one remains unselected, and two
through 64 candidates produce a bounded scientist question. The scientist may select listed
candidates, select none, or retain the dimension as unknown.

Linked segments may target one exact question. For compatibility, an untargeted resume may queue
all open questions, but one segment records one scientist Answer. When an unrelated question is
answered, every still-open scope contract is deterministically refreshed against the recaptured
byte-identical snapshot. Stable record and content identities remain the same; segment-local
AssetIdentity references are rebound to the current segment. Answered selections and their public
Answers are preserved while their internal identity projection is similarly rebound. Snapshot or
content drift is rejected before work is scheduled.

## Acceptance criteria

1. Zero, one, many, and over-limit source/input/output inventories have explicit deterministic
   states, and symlinks or unsafe paths never become candidates.
2. Single, multiple, none, and unknown Answers bind only listed candidates and carry
   `metadata_definition` authority for the exact RepositorySnapshot.
3. Stale, conflicting, missing, weak-identity, path-traversing, and digest-drifted selections fail
   closed without mutating the parent audit.
4. Targeted and untargeted linked resumes retain prior Answers, unrelated open questions, exact
   material full-digest capture budgets, and answerable current-segment candidate bindings.
5. The semantic lock and model-disabled replay preserve scope-selection meaning exactly and add no
   Finding, execution claim, scientific-intent claim, or correctness claim.
6. The integrity-verified agent protocol and both authoritative and packaged skills expose the
   same bounded selection workflow as the CLI.

## Tests added or strengthened

`tests/test_scope_selection.py` covers zero/one/many/over-limit inventories; safe exact candidate
construction; symlink exclusion; typed question projection; single, multiple, none, and unknown
Answers; stale, conflicting, missing, unsafe, weak-identity, and digest-drift rejection; exact
large-material identity-budget reuse; two linked selection segments; rebinding an unanswered scope
question after an unrelated publication Answer; parent immutability; cancellation; lock; replay;
and the repeatable `record-scope-answer` CLI.

`tests/test_general_audit.py` locks the new question counts and scope projection in ordinary audit
paths. `tests/test_agent_skill.py` and the plugin parity checks require the typed interaction
instructions to remain synchronized with the CLI and packaged skill.

## Result

The focused scope-selection and general interaction suites pass. The complete handoff verifier
passes all 1,297 tests; Ruff and mypy; 79 public schema examples; the 103-case, 26-component
regression corpus; clean production and evaluation wheels; demo and model-free replay; linked
publication and scientific-contract interaction; every migration baseline through public schema
0.18.0; and the final handoff checks.

The handoff verifier found one boundary not represented in the initial focused pack: after a
publication Answer, a still-open source-selection question retained its prior segment-local
AssetIdentity references. The implementation now refreshes the open contract against the exact
recaptured snapshot and preserves the unresolved question with current identity bindings. The
exact untargeted multi-question resume is a permanent regression control.

## Remaining limitations

- Selection establishes review scope only. It does not prove that selected code ran, consumed an
  input, produced an output, governed a report, or used a scientifically correct method.
- L05 must consume these selections through reusable, independently supported static joins.
- One-candidate scope remains unselected rather than implicitly scientist-authorized.
- The model-proposal step remains part of the current WorkItem protocol until the broader L15
  scientist-interaction redesign.
- The finite candidate ceiling and current artifact classifiers may leave large or unfamiliar
  repositories explicitly over-limit or unsupported.
