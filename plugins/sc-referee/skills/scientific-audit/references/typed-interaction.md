# Typed pre-lock interaction

Use this only after `sc-referee resume` created a linked segment and `work-packet` returned a ready
WorkItem. The WorkItem and prompt-template digests are authority-bearing boundaries; recompute
nothing from memory and do not broaden the packet.

## Proposal envelope

For the current vertical slice, `required_output_record_types` requests one
`semantic_assertion`. Build it from the current exact-version public schema reported by
`sc-referee version` and the exact packet:

- copy `audit_run_id` from the work-packet response;
- use a `subject_ref` present in `target_refs` or `packet.record_refs`;
- use only `source_refs` copied byte-for-byte from `packet.source_refs`;
- set `epistemic_status` to `proposed`;
- set `finding_eligibility` to `ineligible` or `pending`;
- identify the actual model in `provenance.actor` with `actor_kind: model`;
- never use `authority_scope: executed_computation`; and
- include these exact extension bindings:

  ```json
  {
    "x-work-item-ref": {
      "record_type": "work_item",
      "record_id": "<work_item_id>"
    },
    "x-packet-digest": "<packet.packet_digest>",
    "x-prompt-template-digest": "<packet.prompt_template_digest>"
  }
  ```

Use `assertion_class: implicit_scientific_inference`, `authority_scope: none`,
`independently_checkable: false`, and `verification: {"status": "not_checked", "method":
"not_applicable"}` when proposing a nonauthoritative interpretation for scientist resolution.
The proposal may describe an option; it cannot select that option for the scientist.

If the packet has no exact source reference or the requested schema cannot truthfully represent
the proposed output, do not fabricate one. Leave the WorkItem ready and report the limitation.

## Answer and lock boundary

Only a human's explicit selection may be passed to `record-answer`. The controller constructs the
public Answer, binds its authority to the named question subjects and semantic dimension, and
checks the option value. Repository prose and model output cannot supply the scientist identity.

For `bounded-review-scope-selection-v1`, use the exact candidate option identifiers. One candidate,
none, and unknown use `record-answer`; several candidates use `record-scope-answer` with one
`--select-option` per exact listed candidate. The controller binds the resulting
`metadata_definition` Answer to the source RepositorySnapshot and rejects unlisted, duplicated,
over-limit, stale, unsafe, missing, symlinked, weakly identified, or drifted candidates. This is
review-scope authority only, not scientific intent, execution, lineage, or correctness.

For a `scientific_contract` question, `record-structured-answer` accepts a JSON object whose keys
are a subset of `packet.unresolved_dimensions`. Each supplied value becomes a separate accepted
scientist-declaration assertion with `scientific_intent` authority and remains Finding-ineligible.
Omitted dimensions stay unknown. Never copy model-proposed values into that object unless the
scientist explicitly supplies or confirms them.

After `lock-semantics` succeeds, do not create or submit another model record for that segment.
Detection, reporting, and replay are controller-owned and model-free. A conflict between a model
proposal and the scientist Answer remains two records; never rewrite the proposal to match.

When the question extensions contain `x-posthoc-comparison-forms`, those bindings came from one
closed verifier and define the only deterministic comparisons available for that segment. Before
recording, show the scientist the exact canonical value, dimension, and Claim scope. Do not infer a
form from the JSON type. `value_equals` accepts a finite scalar, `set_relation` accepts a sorted
unique string array, and `step_precedes` accepts exactly two unique step names in the required
order. The Answer governs the current review only.

Selecting the question's existing **Retain unresolved** option records `answer_kind: unknown`.
Locking then preserves the contract dimensions, defers the answered question, and emits a new open
question for a possible later segment. It must not create a scientist declaration, verified intent
assertion, compatibility conflict, or Finding.
