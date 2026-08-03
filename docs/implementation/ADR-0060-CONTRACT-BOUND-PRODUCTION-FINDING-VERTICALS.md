# ADR-0060: Build contract-bound generic production-Finding verticals

- **Status:** Accepted under the repository owner's explicit Finding-level product request
- **Date:** 2026-08-03
- **Related decisions:** ADR-0018, ADR-0020, ADR-0040, ADR-0042, ADR-0059
- **Schema impact:** None initially; stop and register a schema gap if existing typed records cannot
  preserve the meanings below
- **Finding impact:** Authorizes implementation and qualification work, not detector promotion;
  each production Finding envelope still requires its own completed qualification and promotion
- **Execution impact:** None; production remains non-executing

## Context

The ten-case cold-recognition loop established that the current registry can localize relevant
method choices, but question localization and evaluation-only incompatibility Disclosures do not
satisfy the product objective. The required behavior is an automatic, demonstrated Finding on an
erroneous unseen workflow and no Finding on corrected or valid-alternative controls.

Many scientific methods are wrong only relative to a governing task, protocol, preregistration, or
analysis plan. Inferring that requirement after inspecting a benchmark answer would overfit and
would not provide legitimate authority. Conversely, requiring a scientist to answer every method
question after an audit makes the system an interactive comparison tool rather than the requested
automatic referee.

## Decision

1. The target acceptance unit is one independently adjudicated atomic root cause, not one question
   or one arbitrary warning per workflow.
2. An automatic method-conflict Finding must consume either a human-authorized requirement frozen
   before workflow implementation or a separately qualified scientific invariant. Missing
   authority remains a question or abstention.
3. Generalize the claimless method-contract lifecycle to registered scientific-check requirements.
   A requirement binds one check, semantic dimension, comparison form, canonical operand, exact
   task/protocol identity, analysis scope, human actor, and immutable semantic lock.
4. A later audit verifies the parent lock and unchanged task identity, then binds the requirement
   automatically to the exact selected analysis. No post-audit Answer may be a premise for the
   target automatic-Finding acceptance tests.
5. Compile requirement and workflow evidence into an internal domain-neutral `ReviewCase`.
   Removable adapters own language, file-format, and domain representations; the deterministic core
   owns only closed relations and finite counterevidence.
6. Static source, report text, material inputs, and execution remain distinct evidence planes. A
   Finding states only the exact bounded conflict established by the available planes and does not
   infer execution, numerical causality, bias direction, biological truth, or global invalidity.
7. Finding authority is envelope-specific. Reusable engine code does not share maturity: each
   scientific-check binding and supported adapter envelope requires its own frozen detector
   identity, independent qualification evidence, threshold decision, maintainer promotion, and
   emergency-demotion path.
8. Public GeneBench cases remain development-only. Production code and manifests must not contain
   benchmark identities, repository names, fixture paths, hashes, answer values, grading
   tolerances, or expected outputs.
9. The first complete vertical is founder orientation. It must emit a real production Finding on
   an unseen renamed error and remain Finding-clean on corrected, ambiguous, unsupported, and
   unrelated controls before other families are scaled.
10. The installed scientific-audit skill and CLI are coequal product surfaces. Final acceptance
    runs through the installed skill, integrity verification, and model-free replay rather than an
    internal detector unit test alone.

## Consequences

The current scientific-check modules become evidence adapters and unresolved-intent fallbacks,
not the final success measure. Pre-analysis contracting becomes the normal authority path for
agent-built workflows. Post-hoc audits without a governing contract remain useful but cannot
manufacture contextual scientific requirements.

The program may reach high precision more slowly because each Finding envelope requires real
qualification. That cost is necessary: changing an experimental candidate's string to `Finding`
would violate the repository's accepted admission semantics and would not deliver a trustworthy
referee.

## Mandatory stop conditions

- If a required value cannot be represented without overloading an accepted record, record the gap
  and adopt a forward-only schema ADR before implementation.
- If a detector needs a benchmark identifier or answer value, reject the detector design.
- If a decisive applicability or counterevidence check is unavailable, block the Finding.
- If qualification labels are visible before detector and case-selection freeze, exclude the case.
- If an implementation change follows qualification-label access, mint a new detector version and
  restart qualification.
