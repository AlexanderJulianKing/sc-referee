# ADR-0082: Method-contract draft-then-confirm

- **Status:** Accepted
- **Date:** 2026-09-03
- **Acceptance provenance:** accepted under the standing executive authority Alex King granted the
  supervisor on 2026-08-21 (development-lane ADR/registry mechanics; escalation reserved for public,
  one-way, or zero-FA-weakening changes, none of which apply). The product principle is Alex's,
  stated 2026-09-03: "A person should never write a method contract. In the Claude Code skill the
  LLM writes the contract with the help of the human if need be."
- **Decision owners:** Alex / sc-referee maintainers
- **Scope:** The pre-analysis method-contract flow and the `method-contract` Agent Skill. No
  detector, check, adapter, schema, or authority semantics change.
- **Execution impact:** None; project-authored code remains unexecuted
- **Production impact:** None; no qualification, grant, GrantPin, or Finding authority is installed

## Context

Until now the method-contract flow assumed the scientist arrived holding a complete
`scientific_check_requirement_v1` JSON object. In practice that is the step that does not happen. A
scientist who must hand-author a closed profile, with an exact ordered outcome family and the exact
group column spelled as they appear in a CSV header, will either skip the contract or delegate the
authoring to the agent informally, which is the failure the contract exists to prevent.

Two prohibitions are load-bearing and must survive any usability change. The agent must not choose
the scientific content of the requirement, and no scientific value may be inferred from
project-authored code or from data values. The existing skill enforced both by refusing to author
anything at all.

The gap between those two positions is narrow but real: the outcome family and the group column are
already written down, in the scientist's own protocol, before any code exists. Reading a document
the scientist wrote is not the agent choosing, and the protocol is not implementation evidence.

## Decision

1. Add a deterministic `sc-referee draft-profile` subcommand. It reads exactly two inputs: the
   governing task or protocol file, and the first row of the named material-input CSV. It never
   opens project-authored code and never reads a data value below the header row.

2. The draft rule is closed and is identified as `method-contract-draft/outcome-family/v1`:

   - **Outcome columns** are the columns the protocol names as outcomes, matched to the header.
     They are captured by a closed anchor set over the protocol text; each anchor requires the
     protocol to name a comma-separated list explicitly. Every anchor match must yield the identical
     list. The list is used in protocol order.
   - **Group column** is the column the protocol names as the two-group contrast, matched to the
     header, captured by a second closed anchor set. Exactly one distinct column may match.
   - If the protocol names no outcome family, or no group column, the command refuses. It writes no
     file and prints the unresolved-contract MaterialQuestion path instead. Refusal is a normal
     outcome, not an error condition to work around.
   - Identifier, design-label, and group columns are never outcomes. A header column that the
     protocol does not name as an outcome is excluded, and the reason is printed. If the protocol
     names the group column or an identifier-shaped column (`id`, or a `_id`/`_uid`/`_tag`/`_key`
     suffix) as an outcome, the command refuses rather than silently dropping it.
   - Every named column must appear in the header, the family must be duplicate-free and hold at
     least three columns, and the drafted object must resolve through the installed registry. Any
     failure refuses.
   - If the protocol names a CSV file in the group anchor and it is not the `--material-input`
     path, the command refuses. This is what keeps a drafted contract pointed at the raw material
     input rather than a derived results table.
   - Where the protocol order and the header order of the same columns disagree, the protocol order
     is used and the summary says so, because the protocol is the human-authored source and the
     scientist confirms the result.

3. `draft-profile` prints a plain-language summary for a human to read: the outcome family with its
   size and order, the group column, every excluded column with its reason, and an explicit
   statement that no analysis code and no data value was read.

4. The existing `method-contract --profile <profile.json> --actor-id <human>` freeze is the
   confirmation step. A new optional `--draft-provenance <sidecar>` marks the freeze as confirming a
   drafted profile.

5. Provenance is recorded in two places, and deliberately not in a third:

   - **Not in the profile.** Both levels of the `scientific_check_requirement_v1` 1.2.0 object have
     a closed exact field set enforced in `scientific_requirement_contract.py`. Adding a provenance
     key would require loosening that validation, would change the frozen manifest digest, and would
     break byte-identity with every sealed envelope profile. The profile stays closed.
   - **In a sidecar** written next to the drafted profile as `<profile>.provenance.json`, carrying
     `drafted_by` (tool and version), the draft rule id, the draft sources (task path plus content
     digest, material-input path plus header and header digest), the drafted profile digest, and
     `confirmed_by: null`.
   - **In the frozen contract's extension surface** as `x-method-profile-draft-provenance`. The
     accepted public `scientific-contract` schema already admits arbitrary `x-`-prefixed extension
     keys, so this needs no schema change. The recorded value adds the confirmed profile digest,
     `human_edited_after_draft` (true when the scientist changed the drafted values before freezing),
     and `confirmed_by` naming the human actor.

6. The CLI stdout summary states the confirmation and whether the draft was edited.

7. The `method-contract` skill and its packaged plugin copy are rewritten to the draft-then-confirm
   flow: draft, present the summary, take edits, freeze under the scientist's actor id, verify. The
   framing that the scientist arrives with a JSON profile in hand is dropped. Every existing
   prohibition is kept. The instruction "never infer the family from the implementation" is narrowed
   to "never infer it from code or data values; derive it only from the protocol and the header, and
   only through `draft-profile`".

## What does not change

The detector core, the check registry, the adapters, the comparison forms, the bind rules, and the
authority semantics are untouched. The confirmed family in the frozen profile is still the only
authority. Draft provenance is a record of how a proposal was produced. It is not evidence, not
corroboration, not a second authority, and never a Finding, a clearance, or a reason to relax any
abstention. A contract frozen without `--draft-provenance` is byte-identical to one frozen before
this change, so every sealed envelope lock remains valid.

## Validation

- Unit tests for the closed draft rule: exact profile when the protocol names outcomes; refusal when
  the protocol names none; refusal when the protocol names no group column; refusal on header
  mismatch for an outcome or the group column; refusal when the protocol names an identifier or the
  group column as an outcome; refusal below three outcomes; refusal on a mismatched material input;
  refusal on conflicting named families; refusal outside the repository root; identifier and
  design-label exclusion with printed reasons.
- A reproduction test asserts that `draft-profile` reproduces the sealed `profile_1_2_0.json` of
  every envelope-17 and envelope-18 case byte-for-byte. All 30 reproduce. Those profiles were
  hand-authored under the envelope custody rule, months of authoring apart from this code, which is
  what makes the agreement evidence about the rule rather than about the test.
- Provenance validation is closed and rejects a confirmed-looking sidecar, a drifted header digest,
  an unknown rule id, and any extra field.
- The skill byte-identity test between `.agents/skills/` and `plugins/sc-referee/skills/` stays
  green.

## Consequences

- A protocol written in a form the closed anchor set does not recognize refuses rather than drafts.
  That is the intended direction of failure: the human then answers the MaterialQuestion explicitly.
  Widening the anchor set is a candidate-surface change and needs its own review.
- The draft step gives the agent a legitimate, bounded reason to read the protocol. It gives it no
  new reason to read anything else, and the refusal path must never be resolved by reading code, the
  report, or data values.
