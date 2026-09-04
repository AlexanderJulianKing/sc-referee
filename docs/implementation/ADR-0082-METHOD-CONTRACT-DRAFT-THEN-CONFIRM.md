# ADR-0082: Method-contract propose-validate-confirm

- **Status:** Accepted
- **Date:** 2026-09-03 (revised 2026-09-04 after adversarial review; see "Why v1 was withdrawn")
- **Acceptance provenance:** accepted under the standing executive authority Alex King granted the
  supervisor on 2026-08-21 (development-lane ADR/registry mechanics; escalation reserved for public,
  one-way, or zero-FA-weakening changes, none of which apply). The product principle is Alex's,
  stated 2026-09-03: "A person should never write a method contract. In the Claude Code skill the
  LLM writes the contract with the help of the human if need be." The v1-to-v2 redesign was ordered
  by the custodian on 2026-09-04 after the Codex adversarial review returned FIX-REQUIRED.
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

The outcome family and the group column are already written down, in the scientist's own protocol,
before any code exists. Reading a document the scientist wrote is not the agent choosing, and the
protocol is not implementation evidence. The question this ADR answers is *which component* does
that reading.

## Why v1 was withdrawn

The first implementation put the reading in the deterministic tool. Rule
`method-contract-draft/outcome-family/v1` matched a closed set of four regular expressions against
the protocol prose and derived the family and the group column from them.

The Codex adversarial review of 2026-09-04 demonstrated, by running that implementation, seven
distinct protocol texts on which it exited 0 with a wrong answer rather than refusing:

1. a family continued into a second sentence was silently truncated, because both outcome anchors
   terminate at the first period;
2. an unrecognized "Secondary outcomes are: ..." list was silently ignored;
3. "they are not declared outcomes: qc_alpha, qc_beta, qc_gamma" produced exactly the inverted
   family, because the anchor matched the substring `declared outcomes` inside `not declared
   outcomes`; a separate "The following are excluded: gamma" sentence was ignored while `gamma`
   stayed in the family;
4. `plot` and `replicate` were accepted as outcomes, because the only identifier test was an ID
   suffix list, contradicting the skill's claim that design-label columns are never outcomes;
5. "There are not two groups recorded in the `arm` column" satisfied the group anchor;
6. a different CSV named anywhere except attached to the first group anchor was ignored; and
7. a header containing both `alpha` and `Alpha` was treated as unambiguous.

The common cause is not a set of fixable patterns. A regular expression over free prose has no
notion of negation, scope, continuation, or contradiction, so it cannot distinguish "does not
match, refuse" from "matches the wrong span, accept". Patching individual anchors would move the
failures rather than remove them. v1 is withdrawn.

## Decision

**Reading the protocol and proposing the family is the agent's job.** That is what the owner's
principle says, and it is the component that can read a negation, notice a second list, and ask the
scientist. Its proposal carries no authority.

**The tool's job is to validate a proposal, fail closed, print the summary, and record provenance.**
The tool does not read prose for meaning.

1. `sc-referee draft-profile` takes the proposal as explicit inputs:

   ```text
   sc-referee draft-profile <project-root> --task <task> --material-input <csv> \
     --group-column <name> --outcome-columns <ordered,comma,separated> \
     --proposed-by <agent-id> [--exclude <name>=<reason>] --output <profile.json>
   ```

   `_GROUP_ANCHORS`, `_OUTCOME_ANCHORS`, and every prose-derivation path are removed. The rule id is
   `method-contract-draft/outcome-family/v2` and it is a validation rule.

2. Validation, all fail-closed. Every failure refuses, writes nothing, and prints the
   MaterialQuestion path:

   - every proposed column exists in the header **exactly**, case-sensitive; a case-only mismatch
     refuses and names the header spelling rather than normalizing;
   - the header has no blank name, no exact duplicate, no pair differing only by case, no
     byte-order mark on the first name, and only contract-safe column names;
   - every proposed name (outcomes and group) occurs **verbatim as a whole token** in the protocol
     text, case-sensitive, with backticks, quotes, bullets, or punctuation permitted around it, so
     that a proposal is grounded in the protocol; otherwise the ungrounded column is named;
   - the group column is not also an outcome;
   - identifier-shaped names (`id`, or an `_id`/`_uid`/`_tag`/`_key` suffix) and any column the
     caller flags with `--exclude <name>=<reason>` are refused as outcomes; an `--exclude` naming a
     column absent from the header, or carrying an empty reason, refuses;
   - at least three outcomes, duplicate-free;
   - the protocol names no `.csv` file other than the passed material input, anywhere in its text;
   - a proposed name sharing a sentence with a word from the closed vocabulary "not", "excluded",
     "exclude", "except", "secondary" refuses with "protocol qualifies `<name>`; confirm by hand".
     This is a conservative tripwire, not sentence parsing: it exists so a human reads the sentence,
     and it is deliberately allowed to fire on innocent text.

   Design-label columns are not special-cased. `plot` and `replicate` are refused when the protocol
   does not name them verbatim or when the caller excludes them, and accepted when the protocol
   names them as outcomes and nobody excludes them. The human is the authority there; a heuristic
   guessing which names are "design-shaped" would be the same category of error as v1.

3. Provenance stays in two places, and deliberately not in a third:

   - **Not in the profile.** Both levels of the `scientific_check_requirement_v1` 1.2.0 object have
     a closed exact field set enforced in `scientific_requirement_contract.py`. Adding a provenance
     key would require loosening that validation, would change the frozen manifest digest, and would
     break byte-identity with every sealed envelope profile. The profile stays closed.
   - **In a sidecar** `<profile>.provenance.json`, carrying `proposed_by` (the agent actor string,
     required), `drafted_by` (tool and version), the v2 rule id, the draft sources (task path plus
     content digest, material-input path plus header and header digest), the grounding evidence (for
     each proposed column, the protocol line numbers where it occurs verbatim), the caller's
     declared exclusions, the validated profile digest, and `confirmed_by: null`.
   - **In the frozen contract's extension surface** as `x-method-profile-draft-provenance`. The
     accepted public `scientific-contract` schema already admits arbitrary `x-`-prefixed extension
     keys, so this needs no schema change. The recorded value adds the confirmed profile digest,
     `human_edited_after_draft`, and `confirmed_by` naming the human actor.

   The review also observed that a v1 sidecar was forgeable: the tool name, the task digest, and the
   bound paths were never rechecked, so a hand-written sidecar could claim an unedited draft, and a
   genuine one could be replayed into another repository. The freeze now re-reads the sources: the
   sidecar's task path must be the `--task` argument, its task digest must match the file's current
   bytes, its material-input path must be the one the confirmed profile authorizes, and its recorded
   header must still be that CSV's header. `drafted_by.tool` must be `sc-referee` and the digests
   must be well-formed. A sidecar remains a record, not a credential, and confers no authority.

4. The `method-contract` skill and its packaged plugin copy describe the division of labour: the
   agent reads the protocol and states its proposed family, group column, exclusions, and anything
   it could not resolve to the scientist **before** running anything; then `draft-profile` checks the
   agreed proposal; then the summary and any refusal go back to the scientist; then the freeze under
   the scientist's actor id. Every existing prohibition is kept. Two are added: the agent must never
   edit, reformat, or reword the governing protocol to make a refusal go away, and a refusal is
   presented rather than worked around. The skill also states that the tool does not read prose for
   meaning, so acceptance is not agreement with the agent's reading.

## What does not change

The detector core, the check registry, the adapters, the comparison forms, the bind rules, and the
authority semantics are untouched. The confirmed family in the frozen profile is still the only
authority. Draft provenance is a record of who proposed what and what was checked. It is not
evidence, not corroboration, not a second authority, and never a Finding, a clearance, or a reason
to relax any abstention. A contract frozen without `--draft-provenance` is byte-identical to one
frozen before this change, so every sealed envelope lock remains valid; the review confirmed this by
comparing canonical records built with and without provenance.

## Validation

- One test per refusal listed above, plus acceptance tests for a grounded proposal, for proposed
  order being preserved rather than reordered, and for `plot`/`replicate` being accepted when the
  protocol names them verbatim and the caller does not exclude them.
- A reproduction test asserts that, given each sealed case's own columns as the proposal,
  `draft-profile` accepts and writes the sealed `profile_1_2_0.json` of every envelope-17 and
  envelope-18 case byte-for-byte. All 30 reproduce.
- Provenance validation is closed and rejects a v1 rule id, a forged tool name, a non-digest task
  digest, an empty proposer, empty grounding, a drifted header digest, a pre-confirmed sidecar, and
  any extra field. Source verification rejects a sidecar whose protocol bytes or CSV header changed.
- The end-to-end check on a real envelope-18 case still produces an audit bundle identical to the
  sealed run.
- The skill byte-identity test between `.agents/skills/` and `plugins/sc-referee/skills/` stays
  green.

## Consequences

- The tool can no longer be wrong about what the protocol says, because it no longer forms an
  opinion about what the protocol says. It can still refuse a correct proposal, which is the
  intended direction of failure.
- The tripwire vocabulary will fire on protocols that use those words innocently. The remedy is the
  scientist confirming by hand, never a protocol edit and never a wider vocabulary added to make a
  particular case pass.
- The verbatim-grounding requirement means a protocol that describes outcomes only in prose, without
  writing the column names, cannot be contracted through this path. That is correct: the family is
  then genuinely unresolved and belongs in a MaterialQuestion.
