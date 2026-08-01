# Experiment 0034: Public documentation usability follow-up

## Question

Can a fresh reader complete the documented direct-CLI interaction path and understand the exact
scope of the optional method-contract skill without relying on unstated repository context?

## Scope

This is a documentation and plugin-presentation correction prompted by an independent
fresh-context review. It changes no record meaning, schema, detector, Finding admission rule,
model authority, scientific coverage, or execution privilege.

The correction:

- updates the contributor authority pointer from schema v0.17.0 to accepted v0.18.0;
- completes the documented `resume` through `lock-semantics` CLI sequence;
- adds one concrete conservative interpretation of the bundled ordinary audit;
- narrows plugin copy from generic method contracting to the single supported
  expected-count/background profile; and
- makes the method-contract handoff distinguish namespaced plugin invocation from standalone
  skill invocation.

## Acceptance criteria

1. `AGENTS.md` names `reference/schemas-v0.18.0/` as the current accepted public schema.
2. The quickstart shows `work-packet`, `submit-proposals`, `questions`, `record-answer`,
   `record-structured-answer`, `lock-semantics`, and final `status` commands while preserving human
   Answer authority.
3. The quickstart gives a worked 0.3.0 interpretation that reports zero Findings, one question,
   twenty Disclosures, partial coverage, and the non-certification boundary.
4. Plugin metadata describes only the supported expected-count/background pre-analysis contract.
5. The method-contract skill names `$sc-referee:scientific-audit` for plugin installs and
   `$scientific-audit` only for standalone installs.
6. Authoritative and packaged skill bytes remain identical.

## Tests added or changed

- `tests/test_public_documentation.py` freezes the accepted-schema pointer, direct interaction
  commands, human-authority wording, and worked interpretation.
- `tests/test_codex_plugin.py` freezes the narrower profile name, description, capability, and
  starter prompt.
- `tests/test_agent_skill.py` freezes the provider-aware namespaced handoff and method-contract
  discovery prompt.

## Remaining limitations

- The direct CLI sequence cannot manufacture the schema-valid proposal file or scientist values;
  a user or bounded agent must still supply those exact inputs.
- The worked counts describe the bundled 0.3.0 fixture and are not a promise about arbitrary
  repositories or future fixtures.
- The method-contract skill still supports only `expected_count_background_v1`; the wording fix
  does not broaden it.

## Result

All acceptance checks pass. The focused public-documentation, agent-skill, and plugin tests pass;
the complete repository reports 1,220 passing tests. Ruff, format checking across 318 files, strict
mypy across 105 source files, all 79 public schema examples, plugin validation, and the full
handoff verifier pass. The verifier rebuilt and installed the 0.3.0 production and isolated
evaluation wheels and exercised the typed interaction lifecycle through deterministic replay.
