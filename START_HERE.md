# Start here: coding-agent brief

Your assignment is to turn the walking skeleton in this repository into the first production-quality vertical slice of sc-referee without broadening scope prematurely.

## First actions

1. Run `pytest` before changing code.
2. Run the demo and inspect `.demo-audit/report.html`.
3. Read `docs/implementation/MILESTONE_0_BUILD_SPEC.md`.
4. Work through `docs/implementation/TASK_BOARD.md` in dependency order.
5. Treat accepted ADRs, including ADR-0017's evidence-first `0.6.0` MPP boundary and ADR-0018's
   closed method-contract compatibility boundary, as the highest
   product authority over the immutable `reference/specification-v0.5.0-draft/` baseline.
6. Treat `reference/schemas-v0.18.0/` as the authority for the current public record contract;
   accepted earlier schema releases remain immutable migration baselines.
7. Treat `docs/implementation/` as the authority for implementation order and experimental
   interfaces.

## Do not do these things

- Do not add an open-ended LLM search for scientific mistakes.
- Do not let model confidence establish a Finding premise.
- Do not call every warning a Finding.
- Do not execute repository-authored code in the production MPP. The disabled synthetic v0.14
  executor is post-MPP work and does not establish a supported capability.
- Do not silently invent missing scientific semantics.
- Do not make SQLite canonical.
- Do not broaden to all listed scientific domains before the walking skeleton is stable.
- Do not promote experimental schemas into the public W3ID namespace without an accepted schema
  ADR, exact version, migration note, examples, and invariant tests.
- Do not modify the architecture baseline merely to make an implementation shortcut look compliant.

## Definition of useful progress

Useful progress is an end-to-end improvement that preserves deterministic replay, conservative admission, exact evidence locations, explicit coverage, and a passing hard-negative test. A new detector without those properties is not useful progress.
